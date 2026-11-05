"""Command wiring and user-facing behaviour of the handlers."""

import pytest

from conftest import plain
from personal_assistant.cli import COMMANDS, Command
from personal_assistant.main import unknown_command

LOOP_COMMANDS = {Command.HELP, Command.EXIT}
HANDLED = [command for command in Command if command not in LOOP_COMMANDS]


class TestWiring:
    def test_every_command_has_a_handler(self):
        assert set(Command) - set(COMMANDS) == LOOP_COMMANDS

    def test_keywords_and_aliases_are_unique(self):
        keywords = Command.keywords()
        assert len(keywords) == len(set(keywords))

    @pytest.mark.parametrize("command", list(Command), ids=lambda c: c.keyword)
    def test_usage_starts_with_the_keyword(self, command):
        assert command.usage.split()[0] == command.keyword

    @pytest.mark.parametrize(
        "typed, expected",
        [
            ("ADD", Command.ADD),
            ("Close", Command.EXIT),
            ("bye", Command.EXIT),
            ("QUIT", Command.EXIT),
            ("nope", None),
            ("", None),
        ],
    )
    def test_parse_keyword(self, typed, expected):
        assert Command.parse(typed) is expected

    def test_handlers_get_the_right_book(self, run):
        assert "added" in run("add-note shop home buy milk")
        assert "No contacts yet" in run("all")
        assert "Shop" in run("all-notes")

    def test_unknown_command_suggests_a_close_one(self):
        assert "find-contacts" in plain(unknown_command("find-contact"))


class TestBadInputNeverCrashes:
    """The app must answer with a message: nothing may escape a handler."""

    ARGS = [
        "",
        "x",
        "x y",
        "x y z",
        "x y z w v",
        "= = =",
        "name=",
        "[] [] []",
        ", , ,",
        "-1",
        "99999999999999999999",
        "кирилиця ім'я",
        "'; DROP TABLE contacts; --",
    ]

    @pytest.mark.parametrize("command", HANDLED, ids=lambda c: c.keyword)
    @pytest.mark.parametrize("args", ARGS)
    def test_on_an_empty_book(self, run, command, args):
        assert isinstance(run(f"{command.keyword} {args}"), str)

    @pytest.mark.parametrize("command", HANDLED, ids=lambda c: c.keyword)
    @pytest.mark.parametrize("args", ARGS)
    def test_on_a_filled_book(self, run, command, args):
        run("add x 0123456789")
        run("add-note x tag text")
        assert isinstance(run(f"{command.keyword} {args}"), str)


class TestContactCommands:
    def test_add_with_a_bad_phone_creates_nothing(self, run, book):
        assert "digits" in run("add anna abc")
        assert "Anna" not in book

    def test_add_twice_appends_a_phone_in_any_case(self, run, book):
        run("add anna 0123456789")
        assert "Phone added" in run("add ANNA 0987654321")
        assert len(book["Anna"].phones) == 2

    @pytest.mark.xfail(
        strict=True, reason="BUG: extra words after the phone are ignored"
    )
    def test_add_rejects_extra_arguments(self, run, book):
        run("add anna 0123456789 0987654321")
        assert len(book) == 0 or len(book["Anna"].phones) == 2

    @pytest.mark.parametrize(
        "line",
        [
            "phone ghost",
            "show-birthday ghost",
            "show-email ghost",
            "show-address ghost",
            "remove ghost",
            "add-email ghost a@b.co",
            "add-address ghost Kyiv",
            "add-birthday ghost 01.01.1990",
            "change-phone ghost 0123456789 0987654321",
        ],
    )
    def test_missing_contact(self, run, line):
        assert "does not exist" in run(line)

    @pytest.mark.parametrize(
        "line, expected",
        [
            ("show-birthday anna", "no birthday"),
            ("show-email anna", "no email"),
            ("show-address anna", "no address"),
        ],
    )
    def test_unset_fields_get_a_message(self, run, line, expected):
        run("add anna 0123456789")
        assert expected in run(line)

    def test_address_keeps_every_word(self, run, book):
        run("add anna 0123456789")
        run("add-address anna Kyiv   Main St 5")
        assert book["Anna"].address.value == "Kyiv Main St 5"

    def test_contact_without_phones_is_still_shown(self, run):
        run("add anna 0123456789")
        run("remove-phone anna 0123456789")
        assert "no phones" in run("phone anna")
        assert "Phones: -" in run("all")


class TestUpcomingBirthdaysCommand:
    @pytest.mark.parametrize(
        "line",
        [
            "show-upcoming-birthdays",
            "show-upcoming-birthdays abc",
            "show-upcoming-birthdays 1.5",
            "show-upcoming-birthdays 1 2",
        ],
    )
    def test_bad_days_show_usage(self, run, line):
        assert run(line).endswith(f"Usage: {Command.SHOW_UPCOMING_BIRTHDAYS.usage}")

    def test_negative_days(self, run):
        assert "Days must be 0 or more" in run("show-upcoming-birthdays -1")

    def test_nothing_found(self, run):
        assert "No upcoming birthdays" in run("show-upcoming-birthdays 7")

    def test_shows_next_birthday(self, run, freeze_today):
        freeze_today(2026, 12, 28)
        run("add anna 0123456789")
        run("add-birthday anna 02.01.1990")
        answer = run("show-upcoming-birthdays 7")
        assert "Upcoming birthdays (1)" in answer
        assert "Next birthday: 02.01.2027" in answer


class TestFindContactsCommand:
    def test_found(self, run):
        run("add anna 0123456789")
        run("add-address anna Kyiv Main St")
        assert "Found contacts (1)" in run("find-contacts address=kyiv main")

    def test_nothing_found(self, run):
        assert "No contacts found." in run("find-contacts name=zzz")

    def test_no_filters_shows_usage(self, run):
        assert "Usage: find-contacts" in run("find-contacts")

    @pytest.mark.parametrize(
        "line, expected",
        [
            ("find-contacts name=", "must not be empty"),
            ("find-contacts foo=bar", "Unexpected 'foo=bar'"),
            ("find-contacts name=a name=b", "given twice"),
        ],
    )
    def test_bad_filters(self, run, line, expected):
        assert expected in run(line)

    def test_all_title_is_unchanged(self, run):
        run("add anna 0123456789")
        assert "Contacts (1)" in run("all")


class TestNoteCommands:
    def test_tags_may_be_typed_with_brackets(self, run, notes):
        run("add-note shop [home,food] buy milk")
        assert [tag.value for tag in notes["Shop"].tags] == ["home", "food"]

    @pytest.mark.parametrize(
        "line",
        ["add-note shop home", "add-note shop ,home text", "add-note shop [] text"],
        ids=["no-text", "empty-tag", "empty-brackets"],
    )
    def test_invalid_note_is_not_added(self, run, notes, line):
        assert "must not be empty" in run(line)
        assert len(notes) == 0

    @pytest.mark.xfail(
        strict=True, reason="BUG: brackets are stripped only when adding a tag"
    )
    @pytest.mark.parametrize(
        "line",
        ["remove-note-tag shop [home]", "change-note-tag shop [home] office"],
        ids=["remove", "change"],
    )
    def test_brackets_work_when_naming_an_existing_tag(self, run, line):
        run("add-note shop home,food buy milk")
        assert "not found" not in run(line)

    @pytest.mark.xfail(
        strict=True, reason="BUG: brackets are stripped only when adding a tag"
    )
    def test_sort_notes_accepts_brackets(self, run):
        run("add-note alpha other text")
        run("add-note shop home text")
        answer = run("sort-notes [home]")
        assert answer.index("Shop") < answer.index("Alpha")

    @pytest.mark.xfail(strict=True, reason="BUG: add-note-tag keeps 'a,b' as one tag")
    def test_add_note_tag_splits_commas_like_add_note(self, run, notes):
        run("add-note shop home text")
        run("add-note-tag shop a,b")
        assert [tag.value for tag in notes["Shop"].tags] == ["home", "a", "b"]

    def test_change_text_without_text(self, run):
        run("add-note shop home text")
        assert "must not be empty" in run("change-note-text shop")

    def test_empty_notebook_messages(self, run):
        assert "No notes yet." in run("all-notes")
        assert "No notes yet." in run("sort-notes home")
