"""Corner cases of notes and the note book."""

import pytest

from personal_assistant.exceptions import NoteDoesNotExist, ValidationError
from personal_assistant.models import Note


def tags(note: Note) -> list[str]:
    return [tag.value for tag in note.tags]


def names(found) -> list[str]:
    return [note.name.value for note in found]


@pytest.fixture
def note() -> Note:
    return Note("shop", ["home", "food"], "buy milk")


class TestNote:
    @pytest.mark.parametrize(
        "bad_tags", [[], [""], ["  "], ["a", ""], ["a", "a"], ["a", "A"]]
    )
    def test_invalid_tags(self, bad_tags):
        with pytest.raises(ValidationError):
            Note("shop", bad_tags, "text")

    def test_find_by_tag_ignores_case(self, note):
        assert note.find_by_tag("HOME").value == "home"
        assert note.find_by_tag("work") is None

    def test_add_tag(self, note):
        note.edit_tag("Work")
        assert tags(note) == ["home", "food", "work"]

    def test_replace_tag_keeps_position(self, note):
        note.edit_tag("work", "home")
        assert tags(note) == ["work", "food"]

    @pytest.mark.parametrize(
        "new, old",
        [
            ("home", None),
            ("HOME", None),
            ("a", "a"),
            ("a", "A"),
            ("x", "y"),
            ("food", "home"),
        ],
        ids=[
            "add-dup",
            "add-dup-case",
            "same",
            "same-case",
            "old-missing",
            "new-exists",
        ],
    )
    def test_edit_tag_failure_changes_nothing(self, note, new, old):
        with pytest.raises(ValidationError):
            note.edit_tag(new, old)
        assert tags(note) == ["home", "food"]

    def test_remove_tag(self, note):
        note.remove_tag("HOME")
        assert tags(note) == ["food"]

    def test_last_tag_cannot_be_removed(self, note):
        note.remove_tag("home")
        with pytest.raises(ValidationError):
            note.remove_tag("food")
        assert tags(note) == ["food"]

    def test_remove_missing_tag(self, note):
        with pytest.raises(ValidationError):
            note.remove_tag("work")

    def test_empty_text_edit_keeps_old_text(self, note):
        with pytest.raises(ValidationError):
            note.edit_text("  ")
        assert note.text.value == "buy milk"

    def test_state_round_trip(self, note):
        restored = Note.__new__(Note)
        restored.__setstate__(note.__getstate__())
        assert restored.__getstate__() == note.__getstate__()


class TestNoteBook:
    @pytest.fixture(autouse=True)
    def stored(self, notes):
        notes.add_note(Note("shop", ["home", "food"], "buy milk"))
        notes.add_note(Note("work", ["office"], "send milk report"))
        notes.add_note(Note("alpha", ["home"], "call anna"))

    def test_duplicate_name_in_any_case(self, notes):
        with pytest.raises(ValidationError):
            notes.add_note(Note("SHOP", ["x"], "y"))

    def test_get_in_any_case(self, notes):
        assert notes.get_note("sHoP").name.value == "Shop"

    def test_get_missing(self, notes):
        with pytest.raises(NoteDoesNotExist):
            notes.get_note("nope")

    def test_delete_in_any_case(self, notes):
        notes.delete_note("SHOP")
        assert "Shop" not in notes

    def test_delete_missing(self, notes):
        with pytest.raises(NoteDoesNotExist):
            notes.delete_note("nope")

    @pytest.mark.parametrize(
        "filters, expected",
        [
            ({"name": "shop"}, ["Shop"]),
            ({"tag": "HOME"}, ["Shop", "Alpha"]),
            ({"text": "MILK"}, ["Shop", "Work"]),
            ({"tag": "home", "text": "milk"}, ["Shop"]),
            ({"name": "shop", "tag": "office"}, []),
            ({"tag": "hom"}, []),
        ],
    )
    def test_find(self, notes, filters, expected):
        assert names(notes.find(**filters)) == expected

    def test_find_without_filters(self, notes):
        with pytest.raises(ValueError):
            notes.find()

    @pytest.mark.parametrize("key", ["name", "tag", "text"])
    def test_find_with_empty_filter(self, notes, key):
        with pytest.raises(ValidationError):
            notes.find(**{key: " "})

    def test_sort_puts_tagged_notes_first_then_by_name(self, notes):
        assert names(notes.sort_by_tag("HOME")) == ["Alpha", "Shop", "Work"]

    def test_sort_by_unknown_tag_keeps_every_note(self, notes):
        assert names(notes.sort_by_tag("nope")) == ["Alpha", "Shop", "Work"]
