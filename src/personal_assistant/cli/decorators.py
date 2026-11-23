"""Decorators that turn handler exceptions into user-facing messages."""

from functools import wraps

from personal_assistant.exceptions import AssistantError, ValidationError

from . import ui
from .command import Command


def require_no_args(command: Command, args: list[str]) -> None:
    """Raise ValidationError, naming the usage, if a command without arguments got some."""
    if args:
        raise ValidationError(
            f"{command.keyword} takes no arguments. Usage: {command.usage}"
        )


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
