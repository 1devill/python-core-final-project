"""General commands that are not tied to contacts or notes."""

from personal_assistant.cli.command import Command


def hello(_: list[str]) -> str:
    """Return a greeting message."""
    return "Hello! How can I help you today?"


GENERAL_COMMANDS = {
    "hello": Command(hello, "hello", "Greet the assistant"),
}
