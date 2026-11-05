"""Registry that merges command dicts from all command modules."""

from typing import Any

from .contact_commands import CONTACT_COMMANDS
from .general_commands import GENERAL_COMMANDS
from .note_commands import NOTE_COMMANDS
from .command import Command, Handler

COMMANDS: dict[Command, Handler[Any]] = {
    **GENERAL_COMMANDS,
    **CONTACT_COMMANDS,
    **NOTE_COMMANDS,
}
