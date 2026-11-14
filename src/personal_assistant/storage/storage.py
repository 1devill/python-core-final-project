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
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from personal_assistant.models import Contact, ContactBook, Note, NoteBook

DATA_DIR = Path.home() / ".personal_assistant"
DATA_FILE = DATA_DIR / "data.pkl"
T = TypeVar("T")

_EMPTY_PAYLOAD: dict = {"contacts": [], "notes": []}

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

    def _target(self) -> Path:
        """Return the real file behind the data path, so a symlink is written through."""
        return Path(os.path.realpath(self.path))

    def _save_backup(self) -> Path | None:
        """Move the data file to a new backup, keeping older ones, and return its path.

        Returns None if the file is already gone, so there is nothing left to protect.
        """
        target = self._target()
        backup = target.with_name(f"{target.name}.bak")
        counter = 0

        while backup.exists():
            counter += 1
            backup = target.with_name(f"{target.name}.bak{counter}")
        moved: Path | None = backup
        try:
            target.rename(backup)
        except FileNotFoundError:
            moved = None
        self._backup_pending = False
        return moved

    def save(self, book: ContactBook, notes: NoteBook) -> Path | None:
        """Write both books to the file, creating the folder if needed.

        Raises OSError if the file can't be written, or if a damaged file is
        still in the way and can't be backed up: it is never overwritten.
        Returns the backup's path if this call moved a damaged file aside.
        """
        payload = {
            "contacts": [pickle.dumps(c) for c in book.data.values()],
            "notes": [pickle.dumps(n) for n in notes.data.values()],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        target = self._target()
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(f"{target.name}.tmp")
        with open(tmp, "wb") as file:
            pickle.dump(payload, file)
        try:
            shutil.copymode(target, tmp)
        except FileNotFoundError:
            pass
        backup = self._save_backup() if self._backup_pending else None
        os.replace(tmp, target)
        return backup

    def _load_records(
        self,
        kind: str,
        cls: type[T],
        items: object,
        add: Callable[[T], None],
        warnings: list[str],
    ) -> None:
        """Unpickle every record of one kind and add it; bad records become warnings."""
        if not isinstance(items, list):
            warnings.append(f"Data file {self.path} has no valid {kind} list.")
            return
        for blob in items:
            try:
                obj = _SafeUnpickler(io.BytesIO(blob)).load()
                if not isinstance(obj, cls):
                    raise TypeError(f"expected {cls.__name__}")
                add(obj)
            except Exception as e:
                warnings.append(f"Skipped invalid {kind} record: {e!r}")

    def load(self) -> tuple[ContactBook, NoteBook, list[str]]:
        """Load both books. Creates the file if missing.

        Returns the books and a list of warnings about skipped or ignored data.
        A file with any unusable data is moved to a backup before it is replaced.
        """
        warnings: list[str] = []
        book, notes = ContactBook(), NoteBook()

        payload = self._read_payload(warnings)
        create_file = payload is None
        if payload is None:
            payload = _EMPTY_PAYLOAD

        self._load_records(
            "contact", Contact, payload.get("contacts"), book.add_contact, warnings
        )
        self._load_records("note", Note, payload.get("notes"), notes.add_note, warnings)

        if warnings:
            self._backup_pending = True
            try:
                backup = self._save_backup()
                create_file = True
                if backup:
                    warnings.append(f"The original file was kept as {backup}.")
            except OSError as e:
                warnings.append(
                    f"Could not back up {self.path}, so it won't be replaced: {e}"
                )

        if create_file:
            try:
                self.save(book, notes)
            except OSError as e:
                warnings.append(f"Could not write {self.path}: {e}")
        return book, notes, warnings

    def _read_payload(self, warnings: list[str]) -> dict | None:
        """Return the stored payload, None if there is no file, or an empty one if it's broken.

        Only FileNotFoundError means "no file": Path.exists can't tell that apart
        from a folder it may not read, and such a file must not be replaced.
        """
        try:
            with open(self.path, "rb") as file:
                payload = _SafeUnpickler(file).load()
                has_trailing_data = bool(file.read(1))
        except FileNotFoundError:
            return None
        except EOFError:
            warnings.append(
                f"Data file {self.path} is empty or truncated and was ignored."
            )
            return _EMPTY_PAYLOAD
        except Exception:
            warnings.append(
                f"Data file {self.path} is corrupted or unreadable and was ignored."
            )
            return _EMPTY_PAYLOAD
        if not isinstance(payload, dict):
            warnings.append(
                f"Data file {self.path} has unexpected content and was ignored."
            )
            return _EMPTY_PAYLOAD
        if has_trailing_data or set(payload) - set(_EMPTY_PAYLOAD):
            warnings.append(
                f"Data file {self.path} has extra data that the app doesn't use."
            )
        return payload
