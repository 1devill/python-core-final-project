"""Command-line interface: input parsing, handlers and error handling."""

from .command import Handler, Command
from .contact_commands import CONTACT_COMMANDS
from .note_commands import NOTE_COMMANDS
from .parser import parse_input
from .registry import COMMANDS
