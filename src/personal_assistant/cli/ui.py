"""Terminal output helpers: colors, banner, help table and messages."""

from collections.abc import Iterable

from colorama import Fore, Style

from personal_assistant.cli.command import Command
from personal_assistant.models.contact import Contact
from personal_assistant.models.note import Note

WIDTH = 52


def banner() -> str:
    """Return the welcome banner shown on startup."""
    inner = WIDTH - 2
    border = f"{Fore.CYAN}{Style.BRIGHT}"
    title = "PERSONAL ASSISTANT".center(inner)
    subtitle = "Contacts & notes in your terminal".center(inner)
    hint = (
        f"Type {Fore.GREEN}help{Style.RESET_ALL} to see commands, "
        f"{Fore.GREEN}exit{Style.RESET_ALL} to quit."
    )
    return (
        f"{border}╔{'═' * inner}╗\n"
        f"{border}║{Fore.WHITE}{title}{border}║\n"
        f"{border}║{Style.NORMAL}{Fore.CYAN}{subtitle}{border}║\n"
        f"{border}╚{'═' * inner}╝{Style.RESET_ALL}\n"
        f"{hint}"
    )


def prompt() -> str:
    """Return the input prompt string."""
    return f"\n{Fore.CYAN}{Style.BRIGHT}❯ {Style.RESET_ALL}"


def help_table(commands: Iterable[Command] = Command) -> str:
    """Return a formatted list of all commands with descriptions."""
    rows = [(cmd.usage, cmd.description) for cmd in commands]

    usage_width = max(len(usage) for usage, _ in rows)
    lines = [f"{Style.BRIGHT}Available commands:{Style.RESET_ALL}"]
    for usage, description in rows:
        lines.append(
            f"  {Fore.GREEN}{usage:<{usage_width}}{Style.RESET_ALL}"
            f"  {Style.DIM}{description}{Style.RESET_ALL}"
        )
    return "\n".join(lines)


def success(message: str) -> str:
    """Format a success message."""
    return f"{Fore.GREEN}✔ {message}{Style.RESET_ALL}"


def error(message: str) -> str:
    """Format an error message."""
    return f"{Fore.RED}✖ {message}{Style.RESET_ALL}"


def info(message: str) -> str:
    """Format a neutral informational message."""
    return f"{Fore.YELLOW}{message}{Style.RESET_ALL}"


def highlight(text: object) -> str:
    """Make text bold without resetting the surrounding color."""
    return f"{Style.BRIGHT}{text}{Style.NORMAL}"


def field(label: str, value: object) -> str:
    """Format a 'Label: value' line with a colored label."""
    return f"{Fore.CYAN}{label}:{Style.RESET_ALL} {value}"


def contact_card(contact: Contact) -> str:
    """Format one contact as a multi-line card."""
    phones = ", ".join(str(phone) for phone in contact.phones)
    lines = [
        f"{Fore.CYAN}{Style.BRIGHT}● {contact.name}{Style.RESET_ALL}",
        "  " + field("Phones", phones or f"{Style.DIM}-{Style.RESET_ALL}"),
    ]
    optional = (
        ("Birthday", contact.birthday),
        ("Email", contact.email),
        ("Address", contact.address),
    )
    lines += ["  " + field(label, value) for label, value in optional if value]
    return "\n".join(lines)


def contact_list(contacts: Iterable[Contact]) -> str:
    """Format all contacts as cards under a header with the total count."""
    cards = [contact_card(contact) for contact in contacts]
    if not cards:
        return info("No contacts yet.")
    header = f"{Style.BRIGHT}Contacts ({len(cards)}):{Style.RESET_ALL}"
    return header + "\n" + "\n\n".join(cards)


def note_card(note: Note) -> str:
    """
    one note as a card for output: name and #tags on the first line, text on the second
    :param note: Note
    :return: card: str
    """
    tags = ", ".join(f"#{tag}" for tag in note.tags)
    return (
        f"{Fore.CYAN}{Style.BRIGHT}● {note.name}{Style.RESET_ALL}"
        f"  {Fore.MAGENTA}{tags}{Style.RESET_ALL}\n"
        f"  {note.text}"
    )


def note_list(notes: Iterable[Note], title: str = "Notes") -> str:
    """
    notes as cards under a header with their count
    :param notes: notes to show: Iterable[Note]
    :param title: header text: str
    :return: header and cards: str, or a message if there are no notes
    """
    cards = [note_card(note) for note in notes]
    if not cards:
        return info("No notes yet.")
    header = f"{Style.BRIGHT}{title} ({len(cards)}):{Style.RESET_ALL}"
    return header + "\n" + "\n\n".join(cards)


def greeting() -> str:
    """Return the reply to the 'hello' command."""
    return f"{Fore.MAGENTA}{Style.BRIGHT}👋 Hello! How can I help you today?"


def goodbye() -> str:
    """Return the farewell message."""
    return f"{Fore.MAGENTA}{Style.BRIGHT}👋 Goodbye! See you next time."
