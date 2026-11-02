"""Decorators that turn handler exceptions into user-facing messages."""

from functools import wraps

from personal_assistant.cli import ui
from personal_assistant.cli.command import Command
from personal_assistant.exceptions import AssistantError


def handle_cmd_error(command: Command):
    """Return the error text, or the command usage when arguments are wrong."""

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AssistantError as error:
                return ui.error(str(error))
            except ValueError:
                return ui.error(f"Usage: {command.usage}")

        return inner

    return decorator
