"""Note: a named text with one or more tags."""

from personal_assistant.exceptions import ValidationError

from .fields import Name, Tag, Text


class Note:
    """
    note: a Name, a non-empty list of unique Tag objects and a Text
    """

    def __init__(self, name: str, tags: list[str], text: str) -> None:
        """
        :param name: note name: str (capitalized by Name)
        :param tags: note tags: list[str] (at least one, unique in any case)
        :param text: note text: str (must not be empty)
        """
        self.name = Name(name)
        self.tags = tags
        self.text = Text(text)

    def __str__(self) -> str:
        return (
            f"Name: {self.name}\n"
            f"\tTags: {', '.join(tag.value for tag in self.tags)}\n"
            f"\tText: {self.text}"
        )

    def __getstate__(self) -> dict:
        """Plain built-in data used by pickle to save the note."""
        return {
            "name": self.name.value,
            "tags": [tag.value for tag in self.tags],
            "text": self.text.value,
        }

    def __setstate__(self, state: dict) -> None:
        """Rebuild the note through the field constructors; raises on invalid data."""
        self.__init__(state["name"], state["tags"], state["text"])

    @property
    def tags(self) -> list[Tag]:
        """
        tags of the note
        :return: list[Tag]
        """
        return self._tags

    @tags.setter
    def tags(self, value: list[str]) -> None:
        """
        replace all tags of the note
        :param value: tags: list[str]; raises ValidationError if the list is empty, a tag is empty
            or two tags are the same in any case
        """
        if not value:
            raise ValidationError("Tags cannot be empty")
        tags = [Tag(tag) for tag in value]
        if len({tag.value for tag in tags}) != len(tags):
            raise ValidationError("Tags must all be unique")
        self._tags = tags

    def find_by_tag(self, tag: str) -> Tag | None:
        """
        find a tag of the note in any case
        :param tag: tag: str
        :return: Tag, or None if the note has no such tag
        """
        return next((t for t in self.tags if t.value == tag.lower()), None)

    def edit_tag(self, new_tag: str, prev_tag: str | None = None) -> None:
        """
        add a new tag, or replace the previous tag with the new one at the same position
        :param new_tag: tag to add: str
        :param prev_tag: tag to replace: str, optional; without it new_tag is added to the end
        :return: None; raises ValidationError if the tags are identical, prev_tag is not found
            or new_tag already exists
        """
        new = Tag(new_tag)

        if prev_tag is None:
            if self.find_by_tag(new.value) is not None:
                raise ValidationError(f"Tag {new} already exists")
            self.tags.append(new)
            return

        prev = Tag(prev_tag)
        if prev.value == new.value:
            raise ValidationError(f"Tags {prev} and {new} are identical")

        tag = self.find_by_tag(prev.value)
        if tag is None:
            raise ValidationError(f"Tag {prev} not found")

        if self.find_by_tag(new.value) is not None:
            raise ValidationError(f"Tag {new} already exists")

        self.tags[self.tags.index(tag)] = new

    def edit_text(self, text: str) -> None:
        """
        replace the text of the note
        :param text: new text: str; raises ValidationError if it is empty
        """
        self.text = Text(text)

    def remove_tag(self, tag_name: str) -> None:
        """
        remove a tag from the note
        :param tag_name: tag: str, any case
        :return: None; raises ValidationError if the tag is not found or it is the last tag of the note
        """
        tag = self.find_by_tag(tag_name)
        if tag is None:
            raise ValidationError(f"Tag {tag_name} not found")
        if len(self.tags) == 1:
            raise ValidationError("Cannot remove the last tag of a note")
        self.tags.remove(tag)
