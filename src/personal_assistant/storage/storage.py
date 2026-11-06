"""Save and load the contact book and the note book in a pickle file.

Every contact and note is pickled with its own ``__getstate__`` (plain built-in
data) and stored as a separate blob. On load the unpickler only accepts the
``Contact`` and ``Note`` classes, and ``__setstate__`` passes every value through
the model constructors, so corrupted data is validated again and invalid
records are skipped one by one instead of crashing.
"""

import io
import os
import pickle

from pathlib import Path

from personal_assistant.models import Contact, ContactBook, Note, NoteBook

DATA_DIR = Path.home() / ".personal_assistant"
DATA_FILE = DATA_DIR / "data.pkl"

_ALLOWED_CLASSES = {
    (Contact.__module__, Contact.__name__): Contact,
    (Note.__module__, Note.__name__): Note,
}


class _SafeUnpickler(pickle.Unpickler):
    """Loads only the model classes; anything else in the file is refused."""

    def find_class(self, module: str, name: str):
        try:
            return _ALLOWED_CLASSES[(module, name)]
        except KeyError:
            raise pickle.UnpicklingError(f"Forbidden object {module}.{name}") from None


class Storage:
    """Reads and writes both books in one pickle file."""

    def __init__(self, path: Path = DATA_FILE) -> None:
        self.path = path
        self._backup_pending = False

    def _save_backup(self) -> Path:
        """Move the data file to a new backup, keeping older ones, and return its path."""
        backup = self.path.with_name(f"{self.path.name}.bak")
        counter = 0

        while backup.exists():
            counter += 1
            backup = self.path.with_name(f"{self.path.name}.bak{counter}")
        self.path.rename(backup)
        return backup

    def save(self, book: ContactBook, notes: NoteBook) -> None:
        """Write both books to the file, creating the folder if needed.

        Raises OSError if the file can't be written, or if a damaged file is
        still in the way and can't be backed up: it is never overwritten.
        """
        payload = {
            "contacts": [pickle.dumps(c) for c in book.data.values()],
            "notes": [pickle.dumps(n) for n in notes.data.values()],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self._backup_pending:
            if self.path.exists():
                self._save_backup()
            self._backup_pending = False
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp, "wb") as file:
            pickle.dump(payload, file)
        os.replace(tmp, self.path)

    def load(self) -> tuple[ContactBook, NoteBook, list[str]]:
        """Load both books. Creates the file if missing.

        Returns the books and a list of warnings about skipped or ignored data.
        A file with any unusable data is moved to a backup before it is replaced.
        """
        warnings: list[str] = []
        book, notes = ContactBook(), NoteBook()

        payload = self._read_payload(warnings)

        for kind, cls, items, add in (
            ("contact", Contact, payload.get("contacts"), book.add_contact),
            ("note", Note, payload.get("notes"), notes.add_note),
        ):
            if not isinstance(items, list):
                warnings.append(f"Data file {self.path} has no valid {kind} list.")
                items = []
            for blob in items:
                try:
                    obj = _SafeUnpickler(io.BytesIO(blob)).load()
                    if not isinstance(obj, cls):
                        raise TypeError(f"expected {cls.__name__}")
                    add(obj)
                except Exception as e:
                    warnings.append(f"Skipped invalid {kind} record: {e!r}")

        if warnings:
            try:
                warnings.append(f"The original file was kept as {self._save_backup()}.")
            except OSError as e:
                self._backup_pending = True
                warnings.append(f"Could not back up {self.path}, so it won't be replaced: {e}")

        if not self.path.exists():
            try:
                self.save(book, notes)
            except OSError as e:
                warnings.append(f"Could not write {self.path}: {e}")
        return book, notes, warnings

    def _read_payload(self, warnings: list[str]) -> dict:
        """Return the stored payload, or an empty one if the file is missing or broken."""
        empty = {"contacts": [], "notes": []}
        if not self.path.exists():
            return empty
        try:
            with open(self.path, "rb") as file:
                payload = _SafeUnpickler(file).load()
        except EOFError:
            warnings.append(f"Data file {self.path} is empty or truncated and was ignored.")
            return empty
        except Exception:
            warnings.append(f"Data file {self.path} is corrupted or unreadable and was ignored.")
            return empty
        if not isinstance(payload, dict):
            warnings.append(f"Data file {self.path} has unexpected content and was ignored.")
            return empty
        return payload
