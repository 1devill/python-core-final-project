"""General commands that are not tied to contacts or notes."""

from personal_assistant.models import ContactBook, NoteBook

from .command import Command, Handler
from .ui import greeting


def hello(_: list[str], __: ContactBook | NoteBook) -> str:
    """Return a greeting message."""
    return greeting()


GENERAL_COMMANDS: dict[Command, Handler[ContactBook | NoteBook]] = {
    Command.HELLO: hello,
}
