"""All CLI commands with their keyword, usage hint and description."""

from collections.abc import Callable
from enum import Enum
from typing import TypeVar

BookT = TypeVar("BookT")

Handler = Callable[[list[str], BookT], str]
"""Template for every command handler: takes the arguments after the command
and a book, returns a message to show the user. Name the book it works with:

    Handler[ContactBook]
    Handler[NoteBook]
    Handler[ContactBook | NoteBook]  - works with either book
    Handler[Any]                     - the book depends on the command
"""


class Command(Enum):
    """All assistant commands. Each member keeps its keyword, usage and description.

    Command("add") -> Command.ADD
    Command("close") -> Command.EXIT (via aliases)
    """

    keyword: str
    usage: str
    description: str
    aliases: tuple[str, ...]

    HELLO = ("hello", "hello", "Greet the assistant")

    ADD = (
        "add",
        "add [name] [phone]",
        "Add a contact or a phone to an existing contact",
    )
    ADD_BIRTHDAY = (
        "add-birthday",
        "add-birthday [name] [DD.MM.YYYY]",
        "Add a birthday to a contact",
    )
    ADD_EMAIL = (
        "add-email",
        "add-email [name] [email]",
        "Add an email to a contact",
    )
    ADD_ADDRESS = (
        "add-address",
        "add-address [name] [address]",
        "Add an address to a contact",
    )

    ALL = ("all", "all", "Show all contacts")
    SHOW_PHONE = ("phone", "phone [name]", "Show a contact's phones")
    SHOW_BIRTHDAY = (
        "show-birthday",
        "show-birthday [name]",
        "Show a contact's birthday",
    )
    SHOW_EMAIL = (
        "show-email",
        "show-email [name]",
        "Show a contact's email",
    )
    SHOW_ADDRESS = (
        "show-address",
        "show-address [name]",
        "Show a contact's address",
    )
    SHOW_UPCOMING_BIRTHDAYS = (
        "show-upcoming-birthdays",
        "show-upcoming-birthdays [days]",
        "Show upcoming birthdays in next given days",
    )
    FIND_CONTACTS = (
        "find-contacts",
        "find-contacts [name=..] [phone=..] [email=..] [address=..]",
        "Find contacts matching all given filters",
    )

    CHANGE_NAME = (
        "change-name",
        "change-name [name] [new name]",
        "Rename a contact",
    )
    CHANGE_PHONE = (
        "change-phone",
        "change-phone [name] [old phone] [new phone]",
        "Change a contact's phone",
    )
    CHANGE_BIRTHDAY = (
        "change-birthday",
        "change-birthday [name] [DD.MM.YYYY]",
        "Change a contact's birthday",
    )
    CHANGE_EMAIL = (
        "change-email",
        "change-email [name] [email]",
        "Change a contact's email",
    )
    CHANGE_ADDRESS = (
        "change-address",
        "change-address [name] [new address]",
        "Change a contact's address",
    )

    REMOVE_CONTACT = (
        "remove",
        "remove [name]",
        "Remove a contact",
    )
    REMOVE_PHONE = (
        "remove-phone",
        "remove-phone [name] [phone]",
        "Remove a contact's phone",
    )
    REMOVE_BIRTHDAY = (
        "remove-birthday",
        "remove-birthday [name]",
        "Remove a contact's birthday",
    )
    REMOVE_EMAIL = (
        "remove-email",
        "remove-email [name]",
        "Remove an email of a contact",
    )
    REMOVE_ADDRESS = (
        "remove-address",
        "remove-address [name]",
        "Remove a contact's address",
    )

    ADD_NOTE = (
        "add-note",
        "add-note [name] [tag1,tag2] [text]",
        "Add a note with comma-separated tags",
    )
    ADD_NOTE_TAG = (
        "add-note-tag",
        "add-note-tag [name] [tag1,tag2]",
        "Add a tag to a note",
    )

    ALL_NOTES = ("all-notes", "all-notes", "Show all notes")
    FIND_NOTES = (
        "find-notes",
        "find-notes [name=..] [tag=..] [text=..]",
        "Find notes matching all given filters",
    )
    SORT_NOTES = (
        "sort-notes",
        "sort-notes [tag]",
        "Show all notes, the ones with [tag] first",
    )

    CHANGE_NOTE_NAME = (
        "change-note-name",
        "change-note-name [name] [new name]",
        "Rename a note",
    )
    CHANGE_NOTE_TEXT = (
        "change-note-text",
        "change-note-text [name] [text]",
        "Change note text",
    )
    CHANGE_NOTE_TAG = (
        "change-note-tag",
        "change-note-tag [name] [old tag] [new tag]",
        "Replace a note's tag",
    )

    REMOVE_NOTE = (
        "remove-note",
        "remove-note [name]",
        "Remove a note",
    )
    REMOVE_NOTE_TAG = (
        "remove-note-tag",
        "remove-note-tag [name] [tag]",
        "Remove a tag from a note",
    )

    HELP = ("help", "help", "Show this help message")
    EXIT = (
        "exit",
        "exit | close | bye | quit",
        "Save data and exit",
        ("close", "bye", "quit"),
    )

    def __new__(
        cls, keyword: str, usage: str, description: str, aliases: tuple[str, ...] = ()
    ):
        obj = object.__new__(cls)
        obj._value_ = keyword
        obj.keyword = keyword
        obj.usage = usage
        obj.description = description
        obj.aliases = aliases
        return obj

    @classmethod
    def _missing_(cls, value):
        """
        Called only when Command(value) finds no exact match.
        Handles any letter case ("ADD", "Add") and aliases ("Close").
        """
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower()
        for command in cls:
            if normalized == command.keyword or normalized in command.aliases:
                return command
        return None

    @property
    def action(self) -> str:
        """What the command does: add, view, change or remove (general for hello, help, exit)."""
        if self.group == "General":
            return "general"
        verb = self.keyword.split("-")[0]
        return verb if verb in ("add", "change", "remove") else "view"

    @property
    def group(self) -> str:
        """Section of the help: General, Notes or Contacts."""
        if self.keyword in ("hello", "help", "exit"):
            return "General"
        return "Notes" if "note" in self.keyword else "Contacts"

    @classmethod
    def parse(cls, keyword: str) -> "Command | None":
        """Return the command for a keyword or alias, or None if unknown."""
        try:
            # False alarm: the custom __new__ takes one value and looks the member up.
            return cls(keyword)  # type: ignore[call-arg]
        except ValueError:
            return None

    @classmethod
    def keywords(cls) -> list[str]:
        """Return every keyword and alias the user can type."""
        return [name for command in cls for name in (command.keyword, *command.aliases)]
