"""Note command handlers and the NOTE_COMMANDS dict."""

from personal_assistant.cli import ui
from personal_assistant.cli.command import Command, Handler
from personal_assistant.cli.decorators import handle_cmd_error
from personal_assistant.cli.parser import parse_filters
from personal_assistant.models.note import Note
from personal_assistant.models.note_book import NoteBook

SEARCH_KEYS = ("name", "tag", "text")


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
    note = Note(name, tags.split(","), " ".join(text_parts))
    book.add_note(note)
    tags = ", ".join(f"#{tag}" for tag in note.tags)
    return ui.success(f"Note '{ui.highlight(note.name)}' added with tags {tags}.")


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
    return ui.success(f"Note '{ui.highlight(note.name)}' removed.")


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
    note = book.get_note(name)
    note.edit_tag(tag)
    return ui.success(f"Tag '{tag.lower()}' added to '{ui.highlight(note.name)}'.")


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
    note = book.get_note(name)
    note.edit_tag(new_tag, old_tag)
    return ui.success(
        f"Tag '{old_tag.lower()}' replaced with '{new_tag.lower()}' in '{ui.highlight(note.name)}'."
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
    return ui.success(f"Tag '{tag.lower()}' removed from '{ui.highlight(note.name)}'.")


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
    return ui.success(f"Text changed for '{ui.highlight(note.name)}'.")


def show_all_notes(args: list[str], book: NoteBook) -> str:
    """
    command `all-notes`: show all notes of the note book
    :param args: command args (not used)
    :param book: NoteBook
    :return: note cards, or a message if there are none
    """
    return ui.note_list(book.values())


@handle_cmd_error(Command.SORT_NOTES)
def sort_notes(args: list[str], book: NoteBook) -> str:
    """
    command `sort-notes [tag]`: show all notes, the ones with the tag first
    :param args: [tag]: list[str]
    :param book: NoteBook
    :return: note cards; wrong args (ValueError) are handled by handle_cmd_error
    """
    (tag,) = args
    return ui.note_list(book.sort_by_tag(tag))


@handle_cmd_error(Command.FIND_NOTES)
def find_notes(args: list[str], book: NoteBook) -> str:
    """
    command `find-notes [name=..] [tag=..] [text=..]`: show notes matching all given filters
    :param args: key=value words: list[str], parsed by parse_filters into kwargs for NoteBook.find
    :param book: NoteBook
    :return: found note cards, or a message if nothing is found; no filters (ValueError)
        and bad or empty filters (ValidationError) are handled by handle_cmd_error
    """
    found = book.find(**parse_filters(args, SEARCH_KEYS))
    if not found:
        return ui.info("No notes found.")
    return ui.note_list(found, title="Found notes")


NOTE_COMMANDS: dict[Command, Handler] = {
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
