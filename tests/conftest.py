"""Shared fixtures: isolated books, a command runner and a fixed "today"."""

import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from personal_assistant.cli import COMMANDS, NOTE_COMMANDS, Command, parse_input
from personal_assistant.models import Contact, ContactBook, NoteBook

ANSI_CODES = re.compile(r"\x1b\[[0-9;]*m")
SRC_DIR = Path(__file__).resolve().parent.parent / "src"


def plain(text: str) -> str:
    """Remove terminal colors, so tests compare only the message."""
    return ANSI_CODES.sub("", text)


@pytest.fixture
def book() -> ContactBook:
    return ContactBook()


@pytest.fixture
def notes() -> NoteBook:
    return NoteBook()


@pytest.fixture
def make_contact(book):
    """Add a contact to the book with any of its optional fields."""

    def make(name, phones=(), birthday=None, email=None, address=None) -> Contact:
        contact = Contact(name)
        for phone in phones:
            contact.add_phone(phone)
        if birthday:
            contact.add_birthday(birthday)
        if email:
            contact.add_email(email)
        if address:
            contact.add_address(address)
        book.add_contact(contact)
        return contact

    return make


@pytest.fixture
def run(book, notes):
    """Run one input line the way the main loop does and return the plain answer."""

    def execute(line: str) -> str:
        keyword, args = parse_input(line)
        command = Command.parse(keyword)
        assert command is not None, f"unknown command: {keyword}"
        target = notes if command in NOTE_COMMANDS else book
        return plain(COMMANDS[command](args, target))

    return execute


@pytest.fixture
def freeze_today(monkeypatch):
    """Make date.today() in ContactBook return the given date."""

    def freeze(year: int, month: int, day: int) -> None:
        class FixedDate(date):
            @classmethod
            def today(cls):
                return date(year, month, day)

        monkeypatch.setattr("personal_assistant.models.contact_book.date", FixedDate)

    return freeze


class App:
    """The real app in a temporary home folder; call it with input lines."""

    def __init__(self, home: Path) -> None:
        self.home = home

    def __call__(
        self, *lines: str, end_with_exit: bool = True
    ) -> subprocess.CompletedProcess:
        return self._run(lines, end_with_exit)

    def _run(
        self, lines: tuple[str, ...], end_with_exit: bool
    ) -> subprocess.CompletedProcess:
        home = self.home
        typed = [*lines, "exit"] if end_with_exit else list(lines)
        env = {
            **os.environ,
            "HOME": str(home),
            "USERPROFILE": str(home),
            "PYTHONPATH": str(SRC_DIR),
            "PYTHONIOENCODING": "utf-8",
            "ANTHROPIC_API_KEY": "",
            "ANTHROPIC_AUTH_TOKEN": "",
        }
        result = subprocess.run(
            [sys.executable, "-m", "personal_assistant"],
            input="\n".join(typed) + "\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            cwd=home,
            timeout=30,
        )
        result.stdout = plain(result.stdout)
        return result


@pytest.fixture
def app(tmp_path):
    """Start the real app in a temporary home folder and feed it input lines."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return App(home)
