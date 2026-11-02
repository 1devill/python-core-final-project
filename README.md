# Personal Assistant

A command-line personal assistant for managing contacts and notes.
Team project for the Neoversity course _Python Programming: Foundations and Best Practices_.

> **Status:** in development. Commands and installation steps below describe the planned interface and will be updated as features land.

## Features

### Contacts

- Add contacts with name, address, phone numbers, email and birthday
- Validate phone numbers and emails on create/edit
- Search contacts (by name and other fields)
- Edit and delete contacts
- Show contacts with a birthday in the next N days

### Notes

- Add, search, edit and delete text notes
- Tag notes with keywords; search and sort notes by tags

### Storage

- All data is saved to the user's home folder (`~/.personal_assistant/`)
- Data persists between restarts

## Requirements

- Python 3.10+

## Installation

```bash
git clone <repo-url>
cd python-core-final-project

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .
```

After installation, the assistant can be started from any directory:

```bash
assistant
```

or

```bash
python -m personal_assistant
```

## Usage

The assistant runs in an interactive loop: type a command, press Enter, and it responds until you exit.

| Command                                                      | Description                                     |
| ------------------------------------------------------------ | ----------------------------------------------- |
| `hello`                                                      | Greeting                                        |
| `add [name] [phone]`                                         | Add a contact or a phone to an existing contact |
| `change-phone [name] [old phone] [new phone]`                | Change a contact's phone                        |
| `phone [name]`                                               | Show a contact's phones                         |
| `all`                                                        | Show all contacts                               |
| `add-birthday [name] [DD.MM.YYYY]`                           | Add a birthday to a contact                     |
| `add-email [name] [email]`                                   | Add an email to a contact                       |
| `add-address [name] [address]`                               | Add an address to a contact                     |
| `show-birthday` / `show-email` / `show-address [name]`       | Show a contact's birthday / email / address     |
| `remove [name]`                                              | Remove a contact                                |
| `remove-phone [name] [phone]`                                | Remove a contact's phone                        |
| `remove-birthday` / `remove-email` / `remove-address [name]` | Remove a contact's birthday / email / address   |
| `help`                                                       | Show all commands                               |
| `exit` / `close` / `bye` / `quit`                            | Save data and exit                              |

_Note commands will be documented here as they are implemented._

## Project structure

The project uses the `src/` layout. Some modules below are planned and will be added as features are implemented.

```
python-core-final-project/
├── pyproject.toml                 # package metadata, `assistant` console command
├── README.md
└── src/
    └── personal_assistant/
        ├── __init__.py
        ├── __main__.py            # enables `python -m personal_assistant`
        ├── main.py                # main loop: load data → read input → dispatch → save on exit
        ├── exceptions.py          # custom exceptions (AssistantError, ValidationError, ...)
        ├── constants.py           # shared constants (date format, email regex)
        │
        ├── models/                # domain classes — no input()/print() here
        │   ├── fields.py          # Field base class + Name, Phone, Email, Address, Birthday
        │   ├── contact.py         # Contact: one person, composed of fields
        │   ├── contact_book.py    # ContactBook: add, find, delete contacts
        │   ├── note.py            # Note: text + tags
        │   └── note_book.py       # NoteBook: add, find, delete, search/sort by tags
        │
        ├── storage/
        │   └── storage.py         # save/load data in ~/.personal_assistant/
        │
        └── cli/                   # everything related to user interaction
            ├── parser.py          # splits user input into command + arguments
            ├── command.py         # Command enum: keyword, usage, description, aliases
            ├── ui.py              # colors, banner, help table, message formatting
            ├── decorators.py      # handle_cmd_error: turns exceptions into user messages
            ├── general_commands.py  # hello
            ├── contact_commands.py  # contact command handlers + CONTACT_COMMANDS dict
            ├── note_commands.py     # note command handlers + NOTE_COMMANDS dict
            └── registry.py        # merges all handler dicts into one COMMANDS dict
```

### How the layers work together

```
user input → main.py → parser → registry (COMMANDS) → handler in cli/ → models/ → result string → main.py prints it
```

- **`models/`** holds the data and business logic. Classes validate their own values and **raise exceptions** on invalid input. They never print or ask for input.
- **`cli/`** connects the user to the models. Handlers take parsed arguments, call model methods and **return a string**. They don't print.
- **`storage/`** is the only place that reads or writes files.
- **`main.py`** only runs the loop. It parses the keyword into a `Command`, handles `help` and `exit` itself, and looks up every other command's handler in `COMMANDS`.

### Adding a new command

1. Add a member to the `Command` enum in `cli/command.py`: `NAME = ("keyword", "usage", "description")` (optionally a tuple of aliases as the 4th item). It shows up in `help` automatically.
2. Write a handler in the matching module (`contact_commands.py` or `note_commands.py`). It takes `(args, book)` and returns a string.
3. Wrap it with `@handle_cmd_error(Command.NAME)` — validation errors are shown to the user, wrong arguments print the usage.
4. Add `Command.NAME: handler` to that module's commands dict.
5. Add it to the **Usage** table in this README.

You don't need to change `main.py` to add a command.

## Contributing

1. Create a branch from `main`: `git switch -c feature/<short-name>`
2. Follow PEP 8 and add docstrings to classes and public methods
3. Open a pull request into `main` and request a review from a teammate

## Team

- Daniil Derbas
- Leonid
- Andrii Koptiev
