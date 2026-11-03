"""Registry that merges command dicts from all command modules."""

from personal_assistant.cli.command import Command, Handler
from personal_assistant.cli.contact_commands import CONTACT_COMMANDS
from personal_assistant.cli.general_commands import GENERAL_COMMANDS
from personal_assistant.cli.note_commands import NOTE_COMMANDS

COMMANDS: dict[Command, Handler] = {
    **GENERAL_COMMANDS,
    **CONTACT_COMMANDS,
    **NOTE_COMMANDS,
}
