"""The AI parser and its place in the main loop. No test reaches the network."""

import json
from types import SimpleNamespace

import pytest

from conftest import plain
from personal_assistant import main
from personal_assistant.cli import Command, ai_parser
from personal_assistant.models import Contact, ContactBook, NoteBook
from personal_assistant.storage import Storage


class FakeError(Exception):
    def __init__(self, message: str = "boom") -> None:
        super().__init__(message)
        self.message = message


class FakeConnectionError(FakeError):
    pass


class FakeAuthError(FakeError):
    pass


class FakeRateLimitError(FakeError):
    pass


FAKE_SDK = SimpleNamespace(
    APIError=FakeError,
    APIConnectionError=FakeConnectionError,
    AuthenticationError=FakeAuthError,
    RateLimitError=FakeRateLimitError,
)


def tool_call(command: str | None = None, args=None, name: str = ai_parser.TOOL_NAME):
    tool_input = {} if command is None else {"command": command, "args": args or []}
    return SimpleNamespace(type="tool_use", name=name, input=tool_input)


def text_block(text: str = "No command fits."):
    return SimpleNamespace(type="text", text=text)


def thinking_block():
    return SimpleNamespace(type="thinking", thinking="")


def reply(*content, stop_reason: str = "tool_use"):
    return SimpleNamespace(content=list(content), stop_reason=stop_reason)


class FakeClient:
    """Stands in for anthropic.Anthropic: returns or raises what a test sets."""

    def __init__(self) -> None:
        self.result = reply()
        self.requests: list[dict] = []
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **request):
        self.requests.append(request)
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


@pytest.fixture
def client(monkeypatch) -> FakeClient:
    fake = FakeClient()
    monkeypatch.setattr(ai_parser, "anthropic", FAKE_SDK)
    monkeypatch.setattr(ai_parser, "_client", fake)
    return fake


@pytest.fixture
def enabled(client, monkeypatch) -> FakeClient:
    """Turn the AI parser on for the main loop."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-a-real-key")
    return client


@pytest.fixture
def storage(tmp_path) -> Storage:
    return Storage(tmp_path / "data.pkl")


@pytest.fixture
def type_lines(monkeypatch):
    """Answer input() with the given lines, then end the input."""

    def feed(*lines: str) -> None:
        answers = iter(lines)

        def fake_input(_prompt: str = "") -> str:
            try:
                return next(answers)
            except StopIteration:
                raise EOFError from None

        monkeypatch.setattr("builtins.input", fake_input)

    return feed


class TestIsEnabled:
    @pytest.fixture(autouse=True)
    def no_credentials(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.setattr(ai_parser, "anthropic", FAKE_SDK)

    def test_off_without_credentials(self):
        assert ai_parser.is_enabled() is False

    @pytest.mark.parametrize("name", ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"])
    def test_on_with_credentials(self, monkeypatch, name):
        monkeypatch.setenv(name, "not-a-real-key")
        assert ai_parser.is_enabled() is True

    def test_empty_key_is_off(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        assert ai_parser.is_enabled() is False

    def test_off_without_the_sdk(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "not-a-real-key")
        monkeypatch.setattr(ai_parser, "anthropic", None)
        assert ai_parser.is_enabled() is False


class TestPromptAndTool:
    def test_model_can_choose_every_command_except_loop_ones(self):
        allowed = ai_parser._tool()["input_schema"]["properties"]["command"]["enum"]
        expected = set(Command) - {Command.HELP, Command.EXIT}
        assert set(allowed) == {command.keyword for command in expected}

    def test_tool_schema_is_strict(self):
        tool = ai_parser._tool()
        assert tool["strict"] is True
        assert tool["input_schema"]["additionalProperties"] is False
        assert set(tool["input_schema"]["required"]) == {"command", "args"}

    def test_system_prompt_lists_commands(self):
        prompt = ai_parser._system_prompt()
        assert Command.FIND_CONTACTS.usage in prompt
        assert Command.SHOW_UPCOMING_BIRTHDAYS.usage in prompt
        assert f"- {Command.EXIT.usage}:" not in prompt

    def test_system_prompt_explains_find_contacts_filters(self):
        rules = ai_parser._system_prompt().split("Rules:")[1]
        assert "find-contacts" in rules

    def test_every_delete_command_needs_confirmation(self):
        deleting = {c for c in Command if c.keyword.startswith("remove")}
        assert deleting <= ai_parser.CONFIRM_COMMANDS

    @pytest.mark.parametrize(
        "command",
        [
            Command.CHANGE_PHONE,
            Command.CHANGE_NOTE_TEXT,
            Command.CHANGE_NOTE_TAG,
            Command.ADD_BIRTHDAY,
            Command.ADD_EMAIL,
            Command.ADD_ADDRESS,
        ],
        ids=lambda c: c.keyword,
    )
    def test_overwriting_commands_need_confirmation(self, command):
        assert command in ai_parser.CONFIRM_COMMANDS


class TestParse:
    def test_sends_the_user_text(self, client):
        client.result = reply(tool_call("hello"))
        ai_parser.parse("say hi")
        request = client.requests[0]
        assert request["messages"] == [{"role": "user", "content": "say hi"}]
        assert request["model"] == ai_parser.MODEL
        assert request["tools"] == [ai_parser._tool()]

    def test_asks_for_a_single_tool_call(self, client):
        client.result = reply(tool_call("hello"))
        ai_parser.parse("say hi")
        choice = client.requests[0].get("tool_choice", {})
        assert choice.get("disable_parallel_tool_use") is True

    @pytest.mark.parametrize(
        "error, expected",
        [
            (FakeAuthError(), "invalid API key"),
            (FakeRateLimitError(), "rate limited"),
            (FakeConnectionError(), "cannot reach the API"),
            (FakeError("bad model"), "AI parser failed"),
        ],
        ids=["auth", "rate-limit", "connection", "other"],
    )
    def test_api_errors_become_parser_errors(self, client, error, expected):
        client.result = error
        with pytest.raises(ai_parser.AIParserError, match=expected):
            ai_parser.parse("say hi")

    def test_client_is_built_once(self, monkeypatch):
        built = []

        def make_client(**settings):
            built.append(settings)
            return FakeClient()

        sdk = SimpleNamespace(**vars(FAKE_SDK), Anthropic=make_client)
        monkeypatch.setattr(ai_parser, "anthropic", sdk)
        monkeypatch.setattr(ai_parser, "_client", None)
        ai_parser.parse("one")
        ai_parser.parse("two")
        assert len(built) == 1


class TestExtract:
    def test_valid_command(self):
        response = reply(tool_call("add", ["anna", 123]))
        assert ai_parser._extract(response) == (Command.ADD, ["anna", "123"])

    def test_command_without_args(self):
        assert ai_parser._extract(reply(tool_call("all"))) == (Command.ALL, [])

    def test_skips_thinking_and_text_blocks(self):
        response = reply(thinking_block(), text_block(), tool_call("all"))
        assert ai_parser._extract(response) == (Command.ALL, [])

    def test_command_case_is_ignored(self):
        assert ai_parser._extract(reply(tool_call("ADD"))) == (Command.ADD, [])

    @pytest.mark.parametrize(
        "block",
        [
            tool_call("exit"),
            tool_call("close"),
            tool_call("help"),
            tool_call("nope"),
            tool_call(),
            tool_call("add", name="other_tool"),
            text_block(),
        ],
        ids=["exit", "exit-alias", "help", "unknown", "empty", "other-tool", "text"],
    )
    def test_nothing_to_run(self, block):
        assert ai_parser._extract(reply(block)) is None

    def test_empty_answer(self):
        assert ai_parser._extract(reply()) is None

    def test_refusal(self):
        assert (
            ai_parser._extract(reply(tool_call("all"), stop_reason="refusal")) is None
        )

    def test_answer_cut_off_by_max_tokens_is_not_run(self):
        response = reply(
            tool_call("add-note", ["a", "b", "c"]), stop_reason="max_tokens"
        )
        assert ai_parser._extract(response) is None

    def test_null_args_do_not_crash(self):
        block = SimpleNamespace(
            type="tool_use",
            name=ai_parser.TOOL_NAME,
            input={"command": "all", "args": None},
        )
        ai_parser._extract(reply(block))


class TestAiCommand:
    def test_shows_how_the_input_was_understood(self, client, capsys):
        client.result = reply(tool_call("add", ["anna", "0123456789"]))
        assert main.ai_command("new contact", "new") == (
            Command.ADD,
            ["anna", "0123456789"],
        )
        assert "Interpreted as: add anna 0123456789" in plain(capsys.readouterr().out)

    def test_error_is_shown_and_nothing_runs(self, client, capsys):
        client.result = FakeAuthError()
        assert main.ai_command("new contact", "new") is None
        assert "invalid API key" in plain(capsys.readouterr().out)

    def test_no_match_falls_back_to_unknown_command(self, client, capsys):
        client.result = reply(stop_reason="end_turn")
        assert main.ai_command("what is love", "what") is None
        assert "Unknown command 'what'" in plain(capsys.readouterr().out)

    def test_model_explanation_is_shown(self, client, capsys):
        client.result = reply(
            text_block("I can only manage contacts."), stop_reason="end_turn"
        )
        main.ai_command("what is love", "what")
        assert "I can only manage contacts." in plain(capsys.readouterr().out)

    @pytest.mark.parametrize("answer", ["y", "Y", "yes", " YES "])
    def test_confirmed_delete_runs(self, client, type_lines, answer):
        client.result = reply(tool_call("remove", ["anna"]))
        type_lines(answer)
        assert main.ai_command("delete anna", "delete") == (
            Command.REMOVE_CONTACT,
            ["anna"],
        )

    @pytest.mark.parametrize("answer", ["", "n", "no", "maybe", "yep"])
    def test_anything_else_cancels(self, client, type_lines, capsys, answer):
        client.result = reply(tool_call("remove", ["anna"]))
        type_lines(answer)
        assert main.ai_command("delete anna", "delete") is None
        assert "Cancelled." in plain(capsys.readouterr().out)

    def test_end_of_input_cancels(self, client, type_lines):
        client.result = reply(tool_call("remove", ["anna"]))
        type_lines()
        assert main.ai_command("delete anna", "delete") is None

    def test_ctrl_c_during_the_request_cancels(self, client):
        client.result = KeyboardInterrupt()
        try:
            assert main.ai_command("new contact", "new") is None
        except KeyboardInterrupt:
            pytest.fail("KeyboardInterrupt escaped ai_command")


class TestMainLoop:
    @pytest.fixture
    def book(self) -> ContactBook:
        book = ContactBook()
        contact = Contact("anna")
        contact.add_phone("0123456789")
        book.add_contact(contact)
        return book

    def test_known_commands_never_reach_the_api(
        self, storage, enabled, type_lines, book
    ):
        type_lines("all", "hello")
        main.run_loop(book, NoteBook(), storage)
        assert enabled.requests == []

    def test_unknown_input_is_stopped_while_off(
        self, client, type_lines, book, capsys, monkeypatch
    ):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        type_lines("nonsense words")
        main.run_loop(book, NoteBook(), storage)
        assert client.requests == []
        assert "Unknown command 'nonsense'" in plain(capsys.readouterr().out)

    def test_the_whole_line_goes_to_the_model(self, storage, enabled, type_lines, book):
        enabled.result = reply(tool_call("all"))
        type_lines("Please Show Everyone")
        main.run_loop(book, NoteBook(), storage)
        assert enabled.requests[0]["messages"][0]["content"] == "Please Show Everyone"

    def test_chosen_command_runs_on_the_right_book(
        self, storage, enabled, type_lines, book
    ):
        notes = NoteBook()
        enabled.result = reply(tool_call("add-note", ["shop", "home", "buy", "milk"]))
        type_lines("remember to buy milk")
        main.run_loop(book, notes, storage)
        assert "Shop" in notes
        assert len(book) == 1

    def test_invalid_values_are_still_validated(
        self, storage, enabled, type_lines, book, capsys
    ):
        enabled.result = reply(tool_call("add", ["bob", "123"]))
        type_lines("save bob")
        main.run_loop(book, NoteBook(), storage)
        assert "Bob" not in book
        assert "10 digits" in plain(capsys.readouterr().out)

    def test_wrong_args_from_the_model_show_usage(
        self, storage, enabled, type_lines, book, capsys
    ):
        enabled.result = reply(tool_call("add-email", ["anna"]))
        type_lines("mail for anna", "y")
        main.run_loop(book, NoteBook(), storage)
        assert "Usage: add-email" in plain(capsys.readouterr().out)

    def test_delete_runs_only_after_yes(self, storage, enabled, type_lines, book):
        enabled.result = reply(tool_call("remove", ["anna"]))
        type_lines("drop anna", "n")
        main.run_loop(book, NoteBook(), storage)
        assert "Anna" in book
        type_lines("drop anna", "y")
        main.run_loop(book, NoteBook(), storage)
        assert "Anna" not in book

    def test_loop_survives_an_api_error(
        self, storage, enabled, type_lines, book, capsys
    ):
        enabled.result = FakeConnectionError()
        type_lines("first try", "hello")
        main.run_loop(book, NoteBook(), storage)
        output = plain(capsys.readouterr().out)
        assert "cannot reach the API" in output
        assert "Hello!" in output

    def test_model_cannot_exit_the_app(
        self, storage, enabled, type_lines, book, capsys
    ):
        enabled.result = reply(tool_call("exit"))
        type_lines("leave now", "hello")
        main.run_loop(book, NoteBook(), storage)
        assert "Hello!" in plain(capsys.readouterr().out)


class TestRealSdk:
    """The real SDK over a mock transport: checks what the fakes above assume."""

    OK_BODY = {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": "test",
        "stop_reason": "tool_use",
        "stop_sequence": None,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "content": [
            {"type": "thinking", "thinking": "", "signature": "sig"},
            {
                "type": "tool_use",
                "id": "toolu_test",
                "name": ai_parser.TOOL_NAME,
                "input": {"command": "add", "args": ["anna", "0123456789"]},
            },
        ],
    }

    @pytest.fixture
    def sdk(self, monkeypatch):
        sdk = pytest.importorskip("anthropic")
        monkeypatch.setattr(ai_parser, "anthropic", sdk)
        return sdk

    @pytest.fixture
    def connect(self, sdk, monkeypatch):
        """Point the parser at a real client that uses the given request handler."""
        http_module = __import__(
            sdk.DefaultHttpxClient.__mro__[1].__module__.split(".")[0]
        )

        def attach(handler) -> None:
            transport = http_module.MockTransport(
                lambda request: handler(http_module, request)
            )
            client = sdk.Anthropic(
                api_key="not-a-real-key",
                max_retries=0,
                http_client=sdk.DefaultHttpxClient(transport=transport),
            )
            monkeypatch.setattr(ai_parser, "_client", client)

        return attach

    def test_sdk_has_every_name_the_parser_uses(self, sdk):
        for name in (
            "Anthropic",
            "APIError",
            "APIConnectionError",
            "AuthenticationError",
            "RateLimitError",
        ):
            assert hasattr(sdk, name)

    def test_request_and_response(self, connect):
        seen = {}

        def handler(http, request):
            seen.update(json.loads(request.content))
            return http.Response(200, json=self.OK_BODY)

        connect(handler)
        assert ai_parser.parse("save anna") == (Command.ADD, ["anna", "0123456789"])
        assert seen["model"] == ai_parser.MODEL
        assert seen["output_config"] == {"effort": "low"}
        assert seen["tools"][0]["strict"] is True
        assert seen.get("tool_choice", {}).get("type") not in ("any", "tool")

    @pytest.mark.parametrize(
        "status, expected",
        [
            (401, "invalid API key"),
            (429, "rate limited"),
            (400, "AI parser failed"),
            (404, "AI parser failed"),
            (500, "AI parser failed"),
        ],
    )
    def test_status_codes(self, connect, status, expected):
        body = {"type": "error", "error": {"type": "api_error", "message": "boom"}}
        connect(lambda http, request: http.Response(status, json=body))
        with pytest.raises(ai_parser.AIParserError, match=expected):
            ai_parser.parse("save anna")

    def test_lost_connection(self, connect):
        def handler(http, request):
            raise http.ConnectError("no network")

        connect(handler)
        with pytest.raises(ai_parser.AIParserError, match="cannot reach the API"):
            ai_parser.parse("save anna")

    def test_error_message_is_readable(self, connect):
        body = {"type": "error", "error": {"type": "api_error", "message": "boom"}}
        connect(lambda http, request: http.Response(500, json=body))
        with pytest.raises(ai_parser.AIParserError) as error:
            ai_parser.parse("save anna")
        assert "{" not in str(error.value)
