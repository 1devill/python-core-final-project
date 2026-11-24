"""General commands that are not tied to contacts or notes."""

from personal_assistant.cli.parser import require_no_args
from personal_assistant.models import ContactBook, NoteBook

from . import ui
from .command import Command, Handler
from .decorators import handle_cmd_error


@handle_cmd_error(Command.HELLO)
def hello(args: list[str], _: ContactBook | NoteBook) -> str:
    """Return a greeting message; extra arguments are refused (ValidationError)."""
    require_no_args(Command.HELLO, args)
    return ui.greeting()


GENERAL_COMMANDS: dict[Command, Handler[ContactBook | NoteBook]] = {
    Command.HELLO: hello,
}
