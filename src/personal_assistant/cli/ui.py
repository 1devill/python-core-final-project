"""Terminal output helpers: colors, banner, help table and messages."""

from colorama import Fore, Style

from personal_assistant.cli.command import Command

WIDTH = 52
EXIT_COMMANDS = ("exit", "close")


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


def help_table(commands: dict[str, Command]) -> str:
    """Return a formatted list of all commands with descriptions."""
    rows = [(cmd.usage, cmd.description) for cmd in commands.values()]
    rows.append(("help", "Show this help message"))
    rows.append((" / ".join(EXIT_COMMANDS), "Save data and exit"))

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


def goodbye() -> str:
    """Return the farewell message."""
    return f"{Fore.MAGENTA}{Style.BRIGHT}👋 Goodbye! See you next time."
