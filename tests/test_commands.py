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

    def test_change_address_replaces_it(self, run, book):
        run("add anna 0123456789")
        run("add-address anna Kyiv")
        assert "Address changed" in run("change-address anna Lviv Market Sq 1")
        assert book["Anna"].address.value == "Lviv Market Sq 1"

    def test_change_address_needs_an_existing_address(self, run, book):
        run("add anna 0123456789")
        assert "add-address" in run("change-address anna Lviv")
        assert book["Anna"].address is None

    def test_change_address_without_address_shows_usage(self, run):
        run("add anna 0123456789")
        assert "Usage: change-address" in run("change-address anna")

    def test_contact_without_phones_is_still_shown(self, run):
        run("add anna 0123456789")
        run("remove-phone anna 0123456789")
        assert "no phones" in run("phone anna")
        assert "Phones: -" in run("all")


class TestContactEditRules:
    """add-* sets a missing value, change-* replaces an existing one.

    Each field is a (name, add line, change line, invalid change, attribute) case.
    """

    FIELDS = [
        pytest.param(
            "email",
            ("add-email anna a@b.co", "a@b.co"),
            ("change-email anna new@b.co", "new@b.co"),
            "change-email anna bad",
            id="email",
        ),
        pytest.param(
            "birthday",
            ("add-birthday anna 15.03.1990", "15.03.1990"),
            ("change-birthday anna 01.02.1991", "01.02.1991"),
            "change-birthday anna 32.13.2000",
            id="birthday",
        ),
        pytest.param(
            "address",
            ("add-address anna Kyiv Main St 5", "Kyiv Main St 5"),
            ("change-address anna Lviv Market Sq 1", "Lviv Market Sq 1"),
            "change-address anna " + "x" * 500,
            id="address",
        ),
    ]

    @staticmethod
    def value(book, field):
        """Return the stored value of a field as a plain string, or None."""
        stored = getattr(book["Anna"], field)
        return None if stored is None else stored.value

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_add_sets_a_missing_value(self, run, book, field, add, change, invalid):
        run("add anna 0123456789")
        assert "added" in run(add[0])
        assert self.value(book, field) == add[1]

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_add_again_points_to_change(self, run, book, field, add, change, invalid):
        run("add anna 0123456789")
        run(add[0])
        answer = run(add[0])
        assert f"change-{field}" in answer
        assert "added" not in answer
        assert self.value(book, field) == add[1]

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_change_replaces_the_value(self, run, book, field, add, change, invalid):
        run("add anna 0123456789")
        run(add[0])
        assert "changed" in run(change[0])
        assert self.value(book, field) == change[1]

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_change_needs_an_existing_value(
        self, run, book, field, add, change, invalid
    ):
        run("add anna 0123456789")
        answer = run(change[0])
        assert f"add-{field}" in answer
        assert "changed" not in answer
        assert self.value(book, field) is None

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_invalid_change_keeps_the_old_value(
        self, run, book, field, add, change, invalid
    ):
        run("add anna 0123456789")
        run(add[0])
        assert "changed" not in run(invalid)
        assert self.value(book, field) == add[1]

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_change_missing_contact(self, run, field, add, change, invalid):
        assert "does not exist" in run(change[0])

    @pytest.mark.parametrize("field", ["email", "birthday"])
    def test_change_without_value_shows_usage(self, run, field):
        run("add anna 0123456789")
        assert f"Usage: change-{field}" in run(f"change-{field} anna")

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_removed_value_can_be_added_again(
        self, run, book, field, add, change, invalid
    ):
        run("add anna 0123456789")
        run(add[0])
        run(f"remove-{field} anna")
        assert "added" in run(add[0])
        assert self.value(book, field) == add[1]

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_change_to_the_same_value_is_refused(
        self, run, book, field, add, change, invalid
    ):
        """Like change-phone with two identical phones: nothing to change."""
        run("add anna 0123456789")
        run(add[0])
        answer = run(f"change-{field} anna {add[1]}")
        assert "changed" not in answer
        assert self.value(book, field) == add[1]

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_name_is_case_insensitive(self, run, book, field, add, change, invalid):
        run("add anna 0123456789")
        run(add[0].replace("anna", "ANNA"))
        assert "changed" in run(change[0].replace("anna", "aNNa"))
        assert self.value(book, field) == change[1]

    @pytest.mark.parametrize("field, add, change, invalid", FIELDS)
    def test_failed_commands_do_not_touch_other_fields(
        self, run, book, field, add, change, invalid
    ):
        run("add anna 0123456789")
        run(add[0])
        before = str(book["Anna"])
        run(add[0])
        run(invalid)
        assert str(book["Anna"]) == before


class TestPhoneEditRules:
    """Phones follow the same rules: no silent overwrite, no no-op changes."""

    def test_adding_an_existing_phone_is_refused(self, run, book):
        run("add anna 0123456789")
        answer = run("add anna 0123456789")
        assert "already exists" in answer
        assert len(book["Anna"].phones) == 1

    def test_change_to_the_same_phone_is_refused(self, run, book):
        run("add anna 0123456789")
        assert "identical" in run("change-phone anna 0123456789 0123456789")

    def test_change_to_another_existing_phone_is_refused(self, run, book):
        run("add anna 0123456789")
        run("add anna 0987654321")
        assert "already exists" in run("change-phone anna 0123456789 0987654321")
        assert [p.value for p in book["Anna"].phones] == ["0123456789", "0987654321"]

    def test_invalid_new_phone_keeps_the_old_one(self, run, book):
        run("add anna 0123456789")
        assert "changed" not in run("change-phone anna 0123456789 12")
        assert [p.value for p in book["Anna"].phones] == ["0123456789"]

    def test_removing_a_missing_phone_is_refused(self, run):
        run("add anna 0123456789")
        assert "not found" in run("remove-phone anna 0987654321")


class TestNoteEditRules:
    """Notes follow the same rules as contacts."""

    @staticmethod
    def tags(notes):
        return [tag.value for tag in notes["Shop"].tags]

    def test_adding_an_existing_note_is_refused(self, run, notes):
        run("add-note shop home buy milk")
        assert "already exists" in run("add-note SHOP work other text")
        assert self.tags(notes) == ["home"]

    def test_adding_an_existing_tag_is_refused(self, run, notes):
        run("add-note shop home buy milk")
        answer = run("add-note-tag shop HOME")
        assert "already exists" in answer or "unique" in answer
        assert self.tags(notes) == ["home"]

    def test_change_tag_to_an_existing_tag_is_refused(self, run, notes):
        run("add-note shop home,work buy milk")
        assert "already exists" in run("change-note-tag shop home work")
        assert self.tags(notes) == ["home", "work"]

    def test_change_tag_to_the_same_tag_is_refused(self, run, notes):
        run("add-note shop home buy milk")
        assert "identical" in run("change-note-tag shop home home")

    def test_change_missing_tag_is_refused(self, run, notes):
        run("add-note shop home buy milk")
        assert "not found" in run("change-note-tag shop work office")
        assert self.tags(notes) == ["home"]

    def test_change_text_to_the_same_text_is_refused(self, run, notes):
        run("add-note shop home buy milk")
        assert "changed" not in run("change-note-text shop buy milk")

    def test_change_text_replaces_it(self, run, notes):
        run("add-note shop home buy milk")
        assert "changed" in run("change-note-text SHOP buy bread")
        assert notes["Shop"].text.value == "buy bread"

    @pytest.mark.parametrize(
        "line",
        [
            "change-note-text ghost text",
            "add-note-tag ghost home",
            "change-note-tag ghost home work",
            "remove-note-tag ghost home",
            "remove-note ghost",
        ],
    )
    def test_missing_note(self, run, line):
        assert "does not exist" in run(line)


class TestCommandFamilies:
    """Every contact field is managed with the same set of commands."""

    @pytest.mark.parametrize("field", ["email", "birthday", "address"])
    @pytest.mark.parametrize("verb", ["add", "change", "remove", "show"])
    def test_field_has_every_command(self, field, verb):
        assert Command.parse(f"{verb}-{field}") is not None

    @pytest.mark.parametrize(
        "keyword", ["add", "change-phone", "remove-phone", "phone"]
    )
    def test_phone_has_every_command(self, keyword):
        assert Command.parse(keyword) is not None

    @pytest.mark.parametrize("verb", ["add", "change", "remove"])
    def test_note_tag_has_every_command(self, verb):
        assert Command.parse(f"{verb}-note-tag") is not None

    def test_every_change_command_names_the_matching_add_command(self, run):
        """change-X on an empty field points the user to add-X."""
        run("add anna 0123456789")
        for field, value in [
            ("email", "a@b.co"),
            ("birthday", "15.03.1990"),
            ("address", "Kyiv"),
        ]:
            assert f"add-{field}" in run(f"change-{field} anna {value}")


class TestNoExtraArguments:
    @pytest.mark.parametrize("line", ["hello there", "all now", "all-notes now"])
    def test_commands_without_arguments_show_usage(self, run, line):
        keyword = line.split()[0]
        answer = run(line)
        assert f"{keyword} takes no arguments" in answer
        assert f"Usage: {keyword}" in answer

    @pytest.mark.parametrize("line", ["all", "all-notes", "hello"])
    def test_still_work_without_arguments(self, run, line):
        assert "Usage" not in run(line)


class TestUniquePhones:
    def test_new_contact_cannot_take_a_used_phone(self, run, book):
        run("add anna 0123456789")
        answer = run("add bob 0123456789")
        assert "already belongs to 'Anna'" in answer
        assert "Bob" not in book

    def test_existing_contact_cannot_get_a_used_phone(self, run, book):
        run("add anna 0123456789")
        run("add bob 0987654321")
        assert "already belongs to 'Anna'" in run("add bob 0123456789")
        assert [p.value for p in book["Bob"].phones] == ["0987654321"]

    def test_change_phone_to_a_used_phone_is_refused(self, run, book):
        run("add anna 0123456789")
        run("add bob 0987654321")
        assert "already belongs to 'Anna'" in run(
            "change-phone bob 0987654321 0123456789"
        )
        assert [p.value for p in book["Bob"].phones] == ["0987654321"]

    def test_own_repeated_phone_keeps_its_own_message(self, run):
        run("add anna 0123456789")
        answer = run("add anna 0123456789")
        assert "already exists" in answer
        assert "belongs" not in answer

    def test_phone_is_free_after_removal(self, run):
        run("add anna 0123456789")
        run("remove anna")
        assert "added" in run("add bob 0123456789")

    def test_invalid_phone_is_still_reported_as_invalid(self, run):
        run("add anna 0123456789")
        assert "10 digits" in run("add bob 12345")


class TestEmailCase:
    def test_email_is_stored_in_lowercase(self, run, book):
        run("add anna 0123456789")
        run("add-email anna A@B.CO")
        assert book["Anna"].email.value == "a@b.co"

    def test_change_to_the_same_email_in_another_case_is_refused(self, run, book):
        run("add anna 0123456789")
        run("add-email anna a@b.co")
        assert "changed" not in run("change-email anna A@B.CO")


class TestNoteHints:
    @pytest.mark.parametrize("line", ["add-note", "add-note shop"])
    def test_add_note_without_tags_explains_the_syntax(self, run, notes, line):
        answer = run(line)
        assert "needs a name, tags and text" in answer
        assert "Example: add-note shop home,food buy milk" in answer
        assert "word after the name" in answer
        assert len(notes) == 0

    def test_add_note_without_text_keeps_its_own_message(self, run):
        assert "must not be empty" in run("add-note shop home")

    def test_sort_by_unknown_tag_says_so_and_lists_all_notes(self, run):
        run("add-note shop home buy milk")
        run("add-note work office report")
        answer = run("sort-notes zzz")
        assert "No note has the tag 'zzz'" in answer
        assert "Shop" in answer and "Work" in answer

    def test_sort_by_known_tag_has_no_warning(self, run):
        run("add-note shop home buy milk")
        run("add-note work office report")
        answer = run("sort-notes OFFICE")
        assert "No note has" not in answer
        assert answer.index("Work") < answer.index("Shop")

    def test_sort_with_brackets_around_the_tag(self, run):
        run("add-note shop home buy milk")
        assert "No note has" not in run("sort-notes [home]")

    def test_sort_on_an_empty_notebook_keeps_its_message(self, run):
        assert "No notes yet." in run("sort-notes home")
        assert "No note has" not in run("sort-notes home")

    def test_note_names_are_normalized_like_contact_names(self, run, notes):
        assert "Note 'N1' added" in run("add-note n1 home text")
        run("add-note McDonald home text")
        assert "McDonald" in notes


class TestDefaultOrder:
    """Lists are shown sorted by name, whatever order the items were added in."""

    @staticmethod
    def names(answer):
        return [
            line[2:].split()[0] for line in answer.splitlines() if line.startswith("● ")
        ]

    def test_all_lists_contacts_by_name(self, run):
        run("add zed 0501111111")
        run("add anna 0502222222")
        run("add Bob 0503333333")
        run("add mcDonald 0504444444")
        assert self.names(run("all")) == ["Anna", "Bob", "Mcdonald", "Zed"]

    def test_find_contacts_lists_matches_by_name(self, run):
        run("add zed 0501111111")
        run("add anna 0502222222")
        assert self.names(run("find-contacts phone=050")) == ["Anna", "Zed"]

    def test_all_notes_lists_notes_by_name(self, run):
        for name in ("zeta", "alpha", "Mid"):
            run(f"add-note {name} t text")
        assert self.names(run("all-notes")) == ["Alpha", "Mid", "Zeta"]

    def test_find_notes_lists_matches_by_name(self, run):
        run("add-note zeta t milk")
        run("add-note alpha t milk")
        assert self.names(run("find-notes text=milk")) == ["Alpha", "Zeta"]

    def test_sort_notes_still_puts_the_tag_first(self, run):
        run("add-note alpha a text")
        run("add-note zeta b text")
        assert self.names(run("sort-notes b")) == ["Zeta", "Alpha"]

    def test_order_does_not_depend_on_the_order_of_adding(self, run):
        run("add zed 0501111111")
        run("add anna 0502222222")
        first = self.names(run("all"))
        run("remove zed")
        run("add zed 0501111111")
        assert self.names(run("all")) == first


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

    @pytest.mark.parametrize(
        "line",
        ["remove-note-tag shop [home]", "change-note-tag shop [home] office"],
        ids=["remove", "change"],
    )
    def test_brackets_work_when_naming_an_existing_tag(self, run, line):
        run("add-note shop home,food buy milk")
        assert "not found" not in run(line)

    def test_sort_notes_accepts_brackets(self, run):
        run("add-note alpha other text")
        run("add-note shop home text")
        answer = run("sort-notes [home]")
        assert answer.index("Shop") < answer.index("Alpha")

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
