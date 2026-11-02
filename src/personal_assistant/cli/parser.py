"""Parse raw user input into a command name and its arguments."""


def parse_input(user_input: str) -> tuple[str, list[str]]:
    """Split input into a lowercase command name and a list of arguments.

    Returns an empty command name for empty input.
    """
    parts = user_input.split()
    if not parts:
        return "", []
    command, *args = parts
    return command.lower(), args
