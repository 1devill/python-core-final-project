"""Decorators that turn handler exceptions into user-facing messages."""

from functools import wraps

from personal_assistant.exceptions import AssistantError

from .ui import error as err
from .command import Command


def handle_cmd_error(command: Command):
    """Return the error text, or the command usage when arguments are wrong."""

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AssistantError as error:
                return err(str(error))
            except ValueError:
                return err(f"Usage: {command.usage}")

        return inner

    return decorator
