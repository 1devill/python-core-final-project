"""Main entry point and command loop of the Personal Assistant."""

from difflib import get_close_matches

from colorama import init

from personal_assistant.cli import ui
from personal_assistant.cli.command import Command
from personal_assistant.cli.parser import parse_input
from personal_assistant.cli.note_commands import NOTE_COMMANDS
from personal_assistant.cli.registry import COMMANDS
from personal_assistant.models.contact_book import ContactBook
from personal_assistant.models.note_book import NoteBook
from personal_assistant.storage.storage import Storage


def unknown_command(keyword: str) -> str:
    """Return an error message, suggesting a similar command if any."""
    matches = get_close_matches(keyword, Command.keywords(), n=1)
    message = f"Unknown command '{keyword}'."
    if matches:
        message += f" Did you mean '{matches[0]}'?"
    return ui.error(message) + "\n" + ui.info("Type 'help' to see commands.")


def main() -> None:
    """Run the interactive command loop until the user exits."""
    init(autoreset=True)
    storage = Storage()
    book, notes, warnings = storage.load()
    print(ui.banner())
    for warning in warnings:
        print(ui.error(warning))

    try:
        run_loop(book, notes)
    finally:
        storage.save(book, notes)
    print(ui.goodbye())


def run_loop(book: ContactBook, notes: NoteBook) -> None:
    """Read and execute commands until the user exits."""
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
