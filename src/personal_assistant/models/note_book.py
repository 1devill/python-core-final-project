"""NoteBook: stores notes by name, searches and sorts them."""

from collections import UserDict

from personal_assistant.exceptions import NoteDoesNotExist, ValidationError

from .note import Note


class NoteBook(UserDict):
    """
    note book: notes stored in self.data by note name (capitalized)
    """

    data: dict[str, Note]

    def __str__(self) -> str:
        if not self.data:
            return "No notes yet"
        return "\n".join(str(note) for note in self.data.values())

    def add_note(self, note: Note) -> None:
        """
        add a note to the note book
        :param note: Note; raises ValidationError if a note with the same name already exists
        """
        name = note.name.value
        if name in self.data:
            raise ValidationError(f"Note '{name}' already exists")
        self.data[name] = note

    def get_note(self, name: str) -> Note:
        """
        get one note by name
        :param name: note name: str, any case
        :return: Note; raises NoteDoesNotExist if not found
        """
        name = name.capitalize()
        if name not in self.data:
            raise NoteDoesNotExist(name)
        return self.data[name]

    def search_by_text(self, text: str) -> list[Note]:
        """
        find notes whose text contains the given text, in any case
        :param text: part of the text: str
        :return: list[Note], empty if nothing is found
        """
        text = text.lower()
        return [note for note in self.data.values() if text in note.text.value.lower()]

    def search_by_tag(self, tag: str) -> list[Note]:
        """
        find notes that have the given tag
        :param tag: tag: str, any case
        :return: list[Note], empty if nothing is found
        """
        return [note for note in self.data.values() if note.find_by_tag(tag)]

    def find(
        self,
        *,
        name: str | None = None,
        tag: str | None = None,
        text: str | None = None,
    ) -> list[Note]:
        """
        find notes matching ALL given filters; filters are keyword-only (find-notes passes them as **kwargs)
        :param name: note name: str, any case
        :param tag: one of the note tags: str, any case
        :param text: part of the note text: str, any case
        :return: list[Note], empty if nothing matches; raises ValueError if no filter is given
            and ValidationError if a given filter is empty ("" is in every text and would match all notes)
        """
        filters = {"name": name, "tag": tag, "text": text}
        if all(value is None for value in filters.values()):
            raise ValueError("At least one search parameter is required")
        for key, value in filters.items():
            if value is not None and not value.strip():
                raise ValidationError(f"Filter '{key}' must not be empty")

        notes = list(self.data.values())
        if name is not None:
            notes = [note for note in notes if note.name.value == name.capitalize()]
        if tag is not None:
            notes = [note for note in notes if note.find_by_tag(tag)]
        if text is not None:
            text = text.lower()
            notes = [note for note in notes if text in note.text.value.lower()]
        return notes

    def delete_note(self, name: str) -> None:
        """
        delete a note by name
        :param name: note name: str, any case; raises NoteDoesNotExist if not found
        """
        del self.data[self.get_note(name).name.value]

    def sort_by_tag(self, tag: str) -> list[Note]:
        """
        all notes: the ones with the tag first, then the rest; sorted by name inside each group
        :param tag: tag: str, any case
        :return: list[Note]
        """
        return sorted(
            self.data.values(),
            key=lambda note: (note.find_by_tag(tag) is None, note.name.value),
        )
