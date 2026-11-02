"""Command description shared by all command modules."""

from collections.abc import Callable
from typing import NamedTuple


class Command(NamedTuple):
    """A CLI command: its handler, usage hint and short description.

    Every handler takes the list of arguments typed after the command
    name and returns a message to show the user.
    """

    handler: Callable[[list[str]], str]
    usage: str
    description: str
