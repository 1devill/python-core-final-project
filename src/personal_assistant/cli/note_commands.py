"""Note command handlers and the NOTE_COMMANDS dict."""

from personal_assistant.exceptions import ValidationError
from personal_assistant.models import Note, NoteBook

from .ui import success, highlight, info, note_list
from .decorators import handle_cmd_error
from .command import Command, Handler

SEARCH_KEYS = ("name", "tag", "text")


def strip_brackets(tags: str) -> str:
    """
    remove the brackets around tags typed from the usage hint: "[a,b]" -> "a,b".
    Done here and not in Tag: Tag also runs when notes are loaded from the file,
    where a note saved with such tags would turn invalid and be dropped
    :param tags: tag or comma-separated tags as typed: str
    :return: tags without the surrounding brackets: str
    """
    return tags.strip("[]")


def parse_filters(args: list[str]) -> dict[str, str]:
    """
    turn find-notes args into kwargs for NoteBook.find:
    ["text=buy", "milk", "tag=home"] -> {"text": "buy milk", "tag": "home"};
    words without "=" belong to the previous key, so text may contain spaces
    :param args: command args: list[str]
    :return: filters: dict[str, str]; raises ValueError if there are no args (handle_cmd_error shows the usage),
        ValidationError for an unknown or repeated key or a word before the first key (its text is shown)
    """
    filters: dict[str, list[str]] = {}
    key = None
    for word in args:
        candidate, sep, value = word.partition("=")
        if sep and candidate.lower() in SEARCH_KEYS:
            key = candidate.lower()
            if key in filters:
                raise ValidationError(f"Filter '{key}' is given twice")
            filters[key] = [value] if value else []
        elif key is None:
            raise ValidationError(
                f"Unexpected '{word}'. Filters: {', '.join(k + '=..' for k in SEARCH_KEYS)}"
            )
        else:
            filters[key].append(word)
    if not args:
        raise ValueError("At least one filter is required")
    return {key: " ".join(words) for key, words in filters.items()}


@handle_cmd_error(Command.ADD_NOTE)
def add_note(args: list[str], book: NoteBook) -> str:
    """
    command `add-note [name] [tag1,tag2] [text]`: create a new note
    :param args: [name, tags, *text words]: list[str]; tags are comma-separated, text words are joined with spaces
    :param book: NoteBook
    :return: answer to print with the tags, so a text word taken as a tag is seen at once;
        a duplicate name, empty tags or text (ValidationError) and wrong args (ValueError)
        are handled by handle_cmd_error
    """
    name, tags, *text_parts = args
    note = Note(name, strip_brackets(tags).split(","), " ".join(text_parts))
    book.add_note(note)
    tags = ", ".join(f"#{tag}" for tag in note.tags)
    return success(f"Note '{highlight(note.name)}' added with tags {tags}.")


@handle_cmd_error(Command.REMOVE_NOTE)
def remove_note(args: list[str], book: NoteBook) -> str:
    """
    command `remove-note [name]`: delete a note
    :param args: [name]: list[str]
    :param book: NoteBook
    :return: answer to print; a missing note (NoteDoesNotExist) is handled by handle_cmd_error
    """
    (name,) = args
    note = book.get_note(name)
    book.delete_note(name)
    return success(f"Note '{highlight(note.name)}' removed.")


@handle_cmd_error(Command.ADD_NOTE_TAG)
def add_note_tag(args: list[str], book: NoteBook) -> str:
    """
    command `add-note-tag [name] [tag]`: add a tag to a note
    :param args: [name, tag]: list[str]
    :param book: NoteBook
    :return: answer to print; a missing note (NoteDoesNotExist), an existing tag (ValidationError)
        and wrong args (ValueError) are handled by handle_cmd_error
    """
    name, tag = args
    tag = strip_brackets(tag)
    note = book.get_note(name)
    note.edit_tag(tag)
    return success(f"Tag '{tag.lower()}' added to '{highlight(note.name)}'.")


@handle_cmd_error(Command.CHANGE_NOTE_TAG)
def change_note_tag(args: list[str], book: NoteBook) -> str:
    """
    command `change-note-tag [name] [old tag] [new tag]`: replace a tag of a note
    (same order as change-phone [name] [old phone] [new phone])
    :param args: [name, old_tag, new_tag]: list[str]
    :param book: NoteBook
    :return: answer to print; a missing note (NoteDoesNotExist), a missing/duplicate tag (ValidationError)
        and wrong args (ValueError) are handled by handle_cmd_error
    """
    name, old_tag, new_tag = args
    new_tag = strip_brackets(new_tag)
    note = book.get_note(name)
    note.edit_tag(new_tag, old_tag)
    return success(
        f"Tag '{old_tag.lower()}' replaced with '{new_tag.lower()}' in '{highlight(note.name)}'."
    )


@handle_cmd_error(Command.REMOVE_NOTE_TAG)
def remove_note_tag(args: list[str], book: NoteBook) -> str:
    """
    command `remove-note-tag [name] [tag]`: remove a tag from a note
    :param args: [name, tag]: list[str]
    :param book: NoteBook
    :return: answer to print; a missing note (NoteDoesNotExist), a missing or the last tag (ValidationError)
        are handled by handle_cmd_error
    """
    name, tag = args
    note = book.get_note(name)
    note.remove_tag(tag)
    return success(f"Tag '{tag.lower()}' removed from '{highlight(note.name)}'.")


@handle_cmd_error(Command.CHANGE_NOTE_TEXT)
def change_note_text(args: list[str], book: NoteBook) -> str:
    """
    command `change-note-text [name] [text]`: replace the text of a note
    :param args: [name, *text words]: list[str]; text words are joined with spaces
    :param book: NoteBook
    :return: answer to print; a missing note (NoteDoesNotExist) and empty text (ValidationError)
        are handled by handle_cmd_error
    """
    name, *text_parts = args
    note = book.get_note(name)
    note.edit_text(" ".join(text_parts))
    return success(f"Text changed for '{highlight(note.name)}'.")


def show_all_notes(args: list[str], book: NoteBook) -> str:
    """
    command `all-notes`: show all notes of the book
    :param args: command args (not used)
    :param book: NoteBook
    :return: note cards, or a message if there are none
    """
    return note_list(book.values())


@handle_cmd_error(Command.SORT_NOTES)
def sort_notes(args: list[str], book: NoteBook) -> str:
    """
    command `sort-notes [tag]`: show all notes, the ones with the tag first
    :param args: [tag]: list[str]
    :param book: NoteBook
    :return: note cards; wrong args (ValueError) are handled by handle_cmd_error
    """
    (tag,) = args
    return note_list(book.sort_by_tag(tag))


@handle_cmd_error(Command.FIND_NOTES)
def find_notes(args: list[str], book: NoteBook) -> str:
    """
    command `find-notes [name=..] [tag=..] [text=..]`: show notes matching all given filters
    :param args: key=value words: list[str], parsed by parse_filters into kwargs for NoteBook.find
    :param book: NoteBook
    :return: found note cards, or a message if nothing is found; no filters (ValueError)
        and bad or empty filters (ValidationError) are handled by handle_cmd_error
    """
    found = book.find(**parse_filters(args))
    if not found:
        return info("No notes found.")
    return note_list(found, title="Found notes")


NOTE_COMMANDS: dict[Command, Handler[NoteBook]] = {
    Command.ADD_NOTE: add_note,
    Command.REMOVE_NOTE: remove_note,
    Command.ADD_NOTE_TAG: add_note_tag,
    Command.CHANGE_NOTE_TAG: change_note_tag,
    Command.REMOVE_NOTE_TAG: remove_note_tag,
    Command.CHANGE_NOTE_TEXT: change_note_text,
    Command.ALL_NOTES: show_all_notes,
    Command.SORT_NOTES: sort_notes,
    Command.FIND_NOTES: find_notes,
}
