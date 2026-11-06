"""Command-line interface: input parsing, handlers and error handling."""

from .command import Command, Handler
from .contact_commands import CONTACT_COMMANDS
from .note_commands import NOTE_COMMANDS
from .parser import parse_input
from .registry import COMMANDS

__all__ = [
    "Command",
    "Handler",
    "CONTACT_COMMANDS",
    "NOTE_COMMANDS",
    "parse_input",
    "COMMANDS",
]
