"""Main entry point and command loop of the Personal Assistant."""

from difflib import get_close_matches

from colorama import init

from personal_assistant.cli import ai_parser, ui
from personal_assistant.cli.command import Command
from personal_assistant.cli.parser import parse_input
from personal_assistant.cli.note_commands import NOTE_COMMANDS
from personal_assistant.cli.registry import COMMANDS
from personal_assistant.models.contact_book import ContactBook
from personal_assistant.models.note_book import NoteBook


def unknown_command(keyword: str) -> str:
    """Return an error message, suggesting a similar command if any."""
    matches = get_close_matches(keyword, Command.keywords(), n=1)
    message = f"Unknown command '{keyword}'."
    if matches:
        message += f" Did you mean '{matches[0]}'?"
    return ui.error(message) + "\n" + ui.info("Type 'help' to see commands.")


def ai_command(user_input: str, keyword: str) -> tuple[Command, list[str]] | None:
    """Ask the AI parser what the user meant; print the outcome and return None to skip."""
    try:
        resolved = ai_parser.parse(user_input)
    except ai_parser.AIParserError as error:
        print(ui.error(str(error)))
        return None
    if resolved is None:
        print(unknown_command(keyword))
        return None
    command, args = resolved
    print(ui.info(f"Interpreted as: {' '.join([command.value, *args])}"))
    if command in ai_parser.CONFIRM_COMMANDS:
        try:
            answer = input("Run it? [y/N] ")
        except (KeyboardInterrupt, EOFError):
            answer = ""
        if answer.strip().lower() not in ("y", "yes"):
            print(ui.info("Cancelled."))
            return None
    return command, args


def main() -> None:
    """Run the interactive command loop until the user exits."""
    init(autoreset=True)
    book = ContactBook()
    notes = NoteBook()
    print(ui.banner())

    while True:
        try:
            user_input = input(ui.prompt())
        except (KeyboardInterrupt, EOFError):
            print()
            break

        keyword, args = parse_input(user_input)
        if not keyword:
            continue

        command = Command.parse(keyword)
        if command is None:
            if not ai_parser.is_enabled():
                print(unknown_command(keyword))
                continue
            resolved = ai_command(user_input, keyword)
            if resolved is None:
                continue
            command, args = resolved
        if command is Command.EXIT:
            break
        if command is Command.HELP:
            print(ui.help_table())
            continue

        handler = COMMANDS.get(command)
        if handler is None:
            print(unknown_command(keyword))
            continue
        print(handler(args, notes if command in NOTE_COMMANDS else book))

    print(ui.goodbye())
