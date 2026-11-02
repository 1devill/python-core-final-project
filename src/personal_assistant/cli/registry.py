"""Registry that merges command dicts from all command modules."""

from personal_assistant.cli.command import Command
from personal_assistant.cli.general_commands import GENERAL_COMMANDS

COMMANDS: dict[str, Command] = {
    **GENERAL_COMMANDS,
}
