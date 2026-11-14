"""Translate free-form user input into an assistant command with Claude.

The model never touches the data: it only picks one of the existing commands and
its arguments. The normal handlers and field validators still run afterwards.

The feature is optional. It is on only when the `anthropic` package is installed and
ANTHROPIC_API_KEY (or ANTHROPIC_AUTH_TOKEN) is set; otherwise the assistant behaves
exactly as before.
"""

import os
from datetime import date
from types import ModuleType

from personal_assistant.cli.command import Command
from personal_assistant.exceptions import AIParserError

anthropic: ModuleType | None
try:
    import anthropic
except ImportError:  # the AI parser is an optional extra
    anthropic = None

try:  # read ANTHROPIC_API_KEY / ASSISTANT_AI_MODEL from a .env file, if any
    from pathlib import Path

    from dotenv import find_dotenv, load_dotenv

    # load_dotenv does not override values already set, so the first source wins:
    # the environment, then a .env near the current folder, then the fixed location.
    load_dotenv(find_dotenv(usecwd=True))
    load_dotenv(Path.home() / ".personal_assistant" / ".env")
except ImportError:
    pass

MODEL = os.environ.get("ASSISTANT_AI_MODEL", "claude-opus-5-5")
TOOL_NAME = "run_command"

# Commands the model may not choose: the loop handles them itself.
EXCLUDED = {Command.HELP, Command.EXIT}

# Commands that delete data: the user must confirm them before they run.
CONFIRM_COMMANDS = {
    Command.REMOVE_CONTACT,
    Command.REMOVE_PHONE,
    Command.REMOVE_EMAIL,
    Command.REMOVE_BIRTHDAY,
    Command.REMOVE_ADDRESS,
    Command.REMOVE_NOTE,
    Command.REMOVE_NOTE_TAG,
    # They replace existing data based on the model's guess.
    Command.CHANGE_PHONE,
    Command.CHANGE_NOTE_TEXT,
    Command.CHANGE_NOTE_TAG,
    Command.ADD_BIRTHDAY,
    Command.ADD_EMAIL,
    Command.ADD_ADDRESS,
}

# Answers that are never run: declined, or cut off before the arguments were complete.
_NOT_RUN = ("refusal", "max_tokens")

_client = None


def is_enabled() -> bool:
    """Return True if the SDK is installed and credentials are configured."""
    return anthropic is not None and bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )


def _available_commands() -> list[Command]:
    return [command for command in Command if command not in EXCLUDED]


def _system_prompt() -> str:
    catalog = "\n".join(
        f"- {command.usage}: {command.description}" for command in _available_commands()
    )
    return (
        "You translate a user's request for a contacts and notes assistant into exactly "
        f"one assistant command. Always answer by calling the {TOOL_NAME} tool; if no "
        "command fits the request, answer in one short sentence without calling it.\n\n"
        f"Commands:\n{catalog}\n\n"
        "Rules:\n"
        "- Contact names and note names are a single word. Use only what the user wrote; "
        "never invent names, phones, emails or other values.\n"
        "- Pass phone numbers and emails exactly as the user wrote them.\n"
        "- Birthdays must be DD.MM.YYYY. Convert dates like 'March 5, 1990' to 05.03.1990.\n"
        "- Tags are one comma-separated argument without spaces, e.g. work,urgent.\n"
        "- Free text (an address, a note text) may be one argument or several words.\n"
        "- You can run only one command per request. If the request needs several "
        "commands, do not call the tool; answer in one short sentence asking the user "
        "to send them one at a time.\n"
        "- find-notes filters are arguments like name=..., tag=..., text=....\n"
        "- find-contacts filters are arguments like name=..., phone=..., email=..., "
        "address=...; give only the filters the user mentioned.\n"
        f"- Today is {date.today().strftime('%d.%m.%Y')}."
    )


def _tool() -> dict:
    return {
        "name": TOOL_NAME,
        "description": "Run one assistant command with its arguments.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": [command.value for command in _available_commands()],
                },
                "args": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["command", "args"],
            "additionalProperties": False,
        },
    }


def _get_client():
    global _client
    assert anthropic is not None  # parse() checks this before asking for a client
    if _client is None:
        _client = anthropic.Anthropic(timeout=30.0, max_retries=1)
    return _client


def parse(user_input: str) -> tuple[Command, list[str]] | str | None:
    """Return the command and arguments the user meant.

    If no command fits, return the model's explanation, or None if it gave none.

    :raises AIParserError: the request failed (network, auth, rate limit, API error).
    A refusal or a cut-off answer is not an error: it returns None.
    """
    if anthropic is None:
        raise AIParserError("The 'anthropic' package is not installed.")
    try:
        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=4096,
            output_config={"effort": "low"},
            system=_system_prompt(),
            tools=[_tool()],
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=[{"role": "user", "content": user_input}],
        )
    except anthropic.AuthenticationError:
        raise AIParserError("AI parser: invalid API key.") from None
    except anthropic.RateLimitError:
        raise AIParserError("AI parser: rate limited, try again later.") from None
    except anthropic.APIConnectionError:
        raise AIParserError("AI parser: cannot reach the API.") from None
    except anthropic.APIError as error:
        status = getattr(error, "status_code", None)
        suffix = f" (HTTP {status})" if status else ""
        raise AIParserError(f"AI parser failed{suffix}, try again later.") from None
    resolved = _extract(response)
    if resolved is None and response.stop_reason not in _NOT_RUN:
        return _explanation(response) or None
    return resolved


def _explanation(response) -> str:
    """The model's text reply, used when it chose no command."""
    texts = (b.text.strip() for b in response.content if b.type == "text")
    return " ".join(text for text in texts if text)


def _extract(response) -> tuple[Command, list[str]] | None:
    """Pull the command out of a response; None if the model chose no command."""
    if response.stop_reason in _NOT_RUN:
        return None
    for block in response.content:
        if block.type == "tool_use" and block.name == TOOL_NAME:
            command = Command.parse(str(block.input.get("command", "")))
            if command is None or command in EXCLUDED:
                return None
            args = [str(arg) for arg in block.input.get("args") or []]
            return command, args
    return None
