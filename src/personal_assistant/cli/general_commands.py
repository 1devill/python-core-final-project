"""General commands that are not tied to contacts or notes."""

from personal_assistant.cli import ui
from personal_assistant.cli.command import Command, Handler
from personal_assistant.models.contact_book import ContactBook


def hello(_: list[str], __: ContactBook) -> str:
    """Return a greeting message."""
    return ui.greeting()


GENERAL_COMMANDS: dict[Command, Handler] = {
    Command.HELLO: hello,
}
