"""Parse raw user input into a command name, its arguments and search filters."""

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
