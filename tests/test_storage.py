"""Corner cases of saving and loading the data file."""

import pickle

import pytest

from personal_assistant.models import Contact, ContactBook, Note, NoteBook
from personal_assistant.models.fields import Phone
from personal_assistant.storage import Storage


@pytest.fixture
def path(tmp_path):
    return tmp_path / "nested" / "folder" / "data.pkl"


@pytest.fixture
def storage(path) -> Storage:
    return Storage(path)


def filled_books() -> tuple[ContactBook, NoteBook]:
    book, notes = ContactBook(), NoteBook()
    contact = Contact("anna")
    contact.add_phone("0123456789")
    contact.add_phone("0987654321")
    contact.add_birthday("29.02.2000")
    contact.add_email("a@b.co")
    contact.add_address("Київ, Головна 5")
    book.add_contact(contact)
    book.add_contact(Contact("no phones"))
    notes.add_note(Note("shop", ["home", "food"], "купити молоко"))
    return book, notes


def write_raw(path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_payload(path, contacts=(), notes=()) -> None:
    payload = {"contacts": list(contacts), "notes": list(notes)}
    write_raw(path, pickle.dumps(payload))


def good_contact(name: str = "anna") -> bytes:
    return pickle.dumps(Contact(name))


def test_round_trip(storage):
    book, notes = filled_books()
    storage.save(book, notes)
    loaded_book, loaded_notes, warnings = storage.load()
    assert warnings == []
    assert list(loaded_book) == list(book)
    assert loaded_book["Anna"].__getstate__() == book["Anna"].__getstate__()
    assert loaded_book["Anna"].birthday.bd_date == book["Anna"].birthday.bd_date
    assert loaded_notes["Shop"].__getstate__() == notes["Shop"].__getstate__()


def test_missing_file_is_created_with_its_folders(storage, path):
    book, notes, warnings = storage.load()
    assert (len(book), len(notes), warnings) == (0, 0, [])
    assert path.exists()


def test_empty_books_round_trip(storage):
    storage.save(ContactBook(), NoteBook())
    book, notes, warnings = storage.load()
    assert (len(book), len(notes), warnings) == (0, 0, [])


def test_save_leaves_no_temp_file(storage, path):
    storage.save(*filled_books())
    assert [file.name for file in path.parent.iterdir()] == ["data.pkl"]


def test_save_replaces_old_data(storage):
    storage.save(*filled_books())
    storage.save(ContactBook(), NoteBook())
    book, _, _ = storage.load()
    assert len(book) == 0


@pytest.mark.parametrize(
    "data",
    [
        b"not a pickle",
        b"\x80\x04garbage",
        pickle.dumps(["a", "list"]),
        pickle.dumps(42),
    ],
    ids=["text", "broken-pickle", "list", "number"],
)
def test_broken_file_gives_a_warning_and_empty_books(storage, path, data):
    write_raw(path, data)
    book, notes, warnings = storage.load()
    assert (len(book), len(notes)) == (0, 0)
    assert len(warnings) == 1


@pytest.mark.xfail(
    strict=True, reason="BUG: a broken data file is overwritten on load, no backup"
)
def test_broken_file_is_not_destroyed(storage, path):
    write_raw(path, b"not a pickle")
    storage.load()
    survivors = [file.read_bytes() for file in path.parent.iterdir()]
    assert b"not a pickle" in survivors


@pytest.mark.xfail(strict=True, reason="BUG: a truncated data file gives no warning")
def test_truncated_file_gives_a_warning(storage, path):
    storage.save(*filled_books())
    path.write_bytes(b"")
    _, _, warnings = storage.load()
    assert warnings


def test_one_bad_record_does_not_lose_the_others(storage, path):
    write_payload(path, contacts=[b"garbage", good_contact("anna"), 123])
    book, _, warnings = storage.load()
    assert list(book) == ["Anna"]
    assert len(warnings) == 2


def test_record_with_invalid_field_is_skipped(storage, path):
    contact = Contact("broken")
    phone = Phone("0123456789")
    phone.value = "not a phone"
    contact.phones.append(phone)
    write_payload(path, contacts=[pickle.dumps(contact), good_contact("anna")])
    book, _, warnings = storage.load()
    assert list(book) == ["Anna"]
    assert len(warnings) == 1


def test_duplicate_record_is_skipped(storage, path):
    write_payload(path, contacts=[good_contact(), good_contact()])
    book, _, warnings = storage.load()
    assert len(book) == 1
    assert len(warnings) == 1


def test_wrong_class_in_a_list_is_skipped(storage, path):
    write_payload(path, contacts=[pickle.dumps(Note("n", ["t"], "x"))])
    book, _, warnings = storage.load()
    assert len(book) == 0
    assert len(warnings) == 1


@pytest.mark.parametrize(
    "payload",
    [{}, {"contacts": None, "notes": "text"}, {"other": 1}],
    ids=["empty", "wrong-types", "unknown-key"],
)
def test_odd_payload_gives_empty_books(storage, path, payload):
    write_raw(path, pickle.dumps(payload))
    book, notes, _ = storage.load()
    assert (len(book), len(notes)) == (0, 0)


class Exploit:
    """Runs code when unpickled, unless the loader refuses it."""

    def __init__(self, marker):
        self.marker = marker

    def __reduce__(self):
        return (open, (str(self.marker), "w"))


def test_code_in_a_record_is_not_executed(storage, path, tmp_path):
    marker = tmp_path / "hacked"
    write_payload(path, contacts=[pickle.dumps(Exploit(marker))])
    _, _, warnings = storage.load()
    assert not marker.exists()
    assert "Forbidden" in warnings[0]


def test_code_in_the_file_is_not_executed(storage, path, tmp_path):
    marker = tmp_path / "hacked"
    write_raw(path, pickle.dumps(Exploit(marker)))
    _, _, warnings = storage.load()
    assert not marker.exists()
    assert len(warnings) == 1


def test_unwritable_location_gives_a_warning_on_load(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("in the way")
    _, _, warnings = Storage(blocker / "data.pkl").load()
    assert any("Could not write" in warning for warning in warnings)
