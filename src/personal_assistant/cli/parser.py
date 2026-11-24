"""Parse raw user input into a command name, its arguments, search filters and addresses."""

from personal_assistant.cli.command import Command
from personal_assistant.exceptions import ValidationError


def parse_input(user_input: str) -> tuple[str, list[str]]:
    """Split input into a lowercase command name and a list of arguments.

    Returns an empty command name for empty input.
    """
    parts = user_input.split()
    if not parts:
        return "", []
    command, *args = parts
    return command.lower(), args


def parse_filters(args: list[str], allowed_keys: tuple[str, ...]) -> dict[str, str]:
    """
    turn search command args into kwargs for a book search method:
    ["text=buy", "milk", "tag=home"] -> {"text": "buy milk", "tag": "home"};
    words without "=" belong to the previous key, so values may contain spaces
    :param args: command args: list[str]
    :param allowed_keys: filter names the command accepts: tuple[str, ...]
    :return: filters: dict[str, str]; raises ValueError if there are no args (handle_cmd_error shows the usage),
        ValidationError for an unknown or repeated key or a word before the first key (its text is shown)
    """
    filters: dict[str, list[str]] = {}
    key = None
    for word in args:
        candidate, sep, value = word.partition("=")
        if sep and candidate.lower() in allowed_keys:
            key = candidate.lower()
            if key in filters:
                raise ValidationError(f"Filter '{key}' is given twice")
            filters[key] = [value] if value else []
        elif key is None:
            raise ValidationError(
                f"Unexpected '{word}'. Filters: {', '.join(k + '=..' for k in allowed_keys)}"
            )
        else:
            filters[key].append(word)
    if not args:
        raise ValueError("At least one filter is required")
    return {key: " ".join(words) for key, words in filters.items()}


def split_address_args(args: list[str]) -> tuple[str, str]:
    """Return the name and the address made of all the words after it.

    Raises ValueError if no address is given, so the command usage is shown.
    """
    name, *address_parts = args
    if not address_parts:
        raise ValueError("Address is required")
    return name, " ".join(address_parts)


def require_no_args(command: Command, args: list[str]) -> None:
    """Raise ValidationError, naming the usage, if a command without arguments got some."""
    if args:
        raise ValidationError(
            f"{command.keyword} takes no arguments. Usage: {command.usage}"
        )
