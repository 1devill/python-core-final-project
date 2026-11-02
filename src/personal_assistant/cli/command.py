"""All CLI commands with their keyword, usage hint and description."""

from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from personal_assistant.models.contact_book import ContactBook

Handler = Callable[[list[str], "ContactBook"], str]
"""A command handler: takes the arguments after the command and the book,
returns a message to show the user."""


class Command(Enum):
    """All assistant commands. Each member keeps its keyword, usage and description.

    Command("add") -> Command.ADD
    Command("close") -> Command.EXIT (via aliases)
    """

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
    REMOVE_EMAIL = (
        "remove-email",
        "remove-email [name]",
        "Remove an email of a contact",
    )
    REMOVE_BIRTHDAY = (
        "remove-birthday",
        "remove-birthday [name]",
        "Remove a contact's birthday",
    )
    REMOVE_ADDRESS = (
        "remove-address",
        "remove-address [name]",
        "Remove a contact's address",
    )
    CHANGE_PHONE = (
        "change-phone",
        "change-phone [name] [old phone] [new phone]",
        "Change a contact's phone",
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
        obj.usage = usage
        obj.description = description
        obj.aliases = aliases
        return obj

    @classmethod
    def _missing_(cls, value):
        # Called only when Command(value) finds no exact match.
        # Handles any letter case ("ADD", "Add") and aliases ("Close").
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower()
        for command in cls:
            if normalized == command.value or normalized in command.aliases:
                return command
        return None

    @classmethod
    def parse(cls, keyword: str) -> "Command | None":
        """Return the command for a keyword or alias, or None if unknown."""
        try:
            return cls(keyword)
        except ValueError:
            return None

    @classmethod
    def keywords(cls) -> list[str]:
        """Return every keyword and alias the user can type."""
        return [name for command in cls for name in (command.value, *command.aliases)]
