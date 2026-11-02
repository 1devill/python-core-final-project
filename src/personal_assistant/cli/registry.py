"""Registry that merges command dicts from all command modules."""

from personal_assistant.cli.command import Command, Handler
from personal_assistant.cli.contact_commands import CONTACT_COMMANDS
from personal_assistant.cli.general_commands import GENERAL_COMMANDS

COMMANDS: dict[Command, Handler] = {
    **GENERAL_COMMANDS,
    **CONTACT_COMMANDS,
}
