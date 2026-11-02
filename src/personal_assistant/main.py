"""Main entry point and command loop of the Personal Assistant."""

from difflib import get_close_matches

from colorama import init

from personal_assistant.cli import ui
from personal_assistant.cli.parser import parse_input
from personal_assistant.cli.registry import COMMANDS


def unknown_command(command: str) -> str:
    """Return an error message, suggesting a similar command if any."""
    known = [*COMMANDS, "help", *ui.EXIT_COMMANDS]
    matches = get_close_matches(command, known, n=1)
    message = f"Unknown command '{command}'."
    if matches:
        message += f" Did you mean '{matches[0]}'?"
    return ui.error(message) + "\n" + ui.info("Type 'help' to see commands.")


def main() -> None:
    """Run the interactive command loop until the user exits."""
    init(autoreset=True)
    print(ui.banner())

    while True:
        try:
            user_input = input(ui.prompt())
        except (KeyboardInterrupt, EOFError):
            print()
            break

        command, args = parse_input(user_input)

        if not command:
            continue
        if command in ui.EXIT_COMMANDS:
            break
        if command == "help":
            print(ui.help_table(COMMANDS))
            continue

        entry = COMMANDS.get(command)
        if entry is None:
            print(unknown_command(command))
            continue
        print(entry.handler(args))

    print(ui.goodbye())
