"""Save and load the contact book and the note book in a pickle file.

Only plain built-in data (dicts, lists, strings) is pickled. On load every
value is passed through the model constructors, so corrupted data is
validated again and invalid records are skipped instead of crashing.
"""

import os
import pickle
from pathlib import Path

from personal_assistant.exceptions import AssistantError
from personal_assistant.models.contact import Contact
from personal_assistant.models.contact_book import ContactBook
from personal_assistant.models.note import Note
from personal_assistant.models.note_book import NoteBook

DATA_DIR = Path.home() / ".personal_assistant"
DATA_FILE = DATA_DIR / "data.pkl"


class _SafeUnpickler(pickle.Unpickler):
    """Refuses to load any class: the file must contain built-in types only."""

    def find_class(self, module: str, name: str):
        raise pickle.UnpicklingError(f"Forbidden object {module}.{name}")


def serialize_contact(contact: Contact) -> dict:
    return {
        "name": contact.name.value,
        "phones": [phone.value for phone in contact.phones],
        "birthday": contact.birthday.value if contact.birthday else None,
        "email": contact.email.value if contact.email else None,
        "address": contact.address.value if contact.address else None,
    }


def deserialize_contact(data: dict) -> Contact:
    """Rebuild a contact through the field constructors; raises on invalid data."""
    contact = Contact(data["name"])
    for phone in data.get("phones") or []:
        contact.add_phone(phone)
    if data.get("birthday") is not None:
        contact.add_birthday(data["birthday"])
    if data.get("email") is not None:
        contact.add_email(data["email"])
    if data.get("address") is not None:
        contact.add_address(data["address"])
    return contact


def serialize_note(note: Note) -> dict:
    return {
        "name": note.name.value,
        "tags": [tag.value for tag in note.tags],
        "text": note.text.value,
    }


def deserialize_note(data: dict) -> Note:
    """Rebuild a note through the field constructors; raises on invalid data."""
    return Note(data["name"], data["tags"], data["text"])


def save_data(book: ContactBook, notes: NoteBook, path: Path = DATA_FILE) -> None:
    """Write both books to the pickle file, creating the folder if needed."""
    payload = {
        "contacts": [serialize_contact(c) for c in book.data.values()],
        "notes": [serialize_note(n) for n in notes.data.values()],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as file:
        pickle.dump(payload, file)
    os.replace(tmp, path)


def _read_payload(path: Path, warnings: list[str]) -> dict:
    """Return the stored payload, or an empty one if the file is missing or broken."""
    empty = {"contacts": [], "notes": []}
    if not path.exists():
        return empty
    try:
        with open(path, "rb") as file:
            payload = _SafeUnpickler(file).load()
    except EOFError:
        return empty
    except Exception:
        warnings.append(f"Data file {path} is corrupted and was ignored.")
        return empty
    if not isinstance(payload, dict):
        warnings.append(f"Data file {path} has unexpected content and was ignored.")
        return empty
    return payload


def load_data(path: Path = DATA_FILE) -> tuple[ContactBook, NoteBook, list[str]]:
    """Load both books. Creates the file if missing.

    Returns the books and a list of warnings about skipped or ignored data.
    """
    warnings: list[str] = []
    book, notes = ContactBook(), NoteBook()

    payload = _read_payload(path, warnings)

    for kind, items, deserialize, add in (
        ("contact", payload.get("contacts"), deserialize_contact, book.add_contact),
        ("note", payload.get("notes"), deserialize_note, notes.add_note),
    ):
        if not isinstance(items, list):
            items = []
        for item in items:
            try:
                add(deserialize(item))
            except (
                AssistantError,
                KeyError,
                TypeError,
                AttributeError,
                ValueError,
            ) as e:
                warnings.append(f"Skipped invalid {kind} record: {e!r}")

    if not path.exists() or warnings:
        try:
            save_data(book, notes, path)
        except OSError as e:
            warnings.append(f"Could not write {path}: {e}")
    return book, notes, warnings
