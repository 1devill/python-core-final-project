# Personal Assistant

A command-line personal assistant for managing contacts and notes.
Team project for the Neoversity course *Python Programming: Foundations and Best Practices*.

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

| Command | Description |
|---|---|
| `hello` | Greeting |
| `help` | Show all commands |
| `exit` / `close` | Save data and exit |

_Contact and note commands will be documented here as they are implemented._

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
        ├── exceptions.py          # custom exceptions (validation, not found, ...)
        │
        ├── models/                # domain classes — no input()/print() here
        │   ├── fields.py          # Field base class + Name, Phone, Email, Address, Birthday
        │   ├── record.py          # Record: one contact, composed of fields
        │   ├── address_book.py    # AddressBook: add, find, delete, upcoming birthdays
        │   ├── note.py            # Note: text + tags
        │   └── note_book.py       # NoteBook: add, find, delete, search/sort by tags
        │
        ├── storage/
        │   └── storage.py         # save/load data in ~/.personal_assistant/
        │
        └── cli/                   # everything related to user interaction
            ├── parser.py          # splits user input into command + arguments
            ├── command.py         # Command(handler, usage, description) tuple
            ├── ui.py              # colors, banner, help table, message formatting
            ├── decorators.py      # input_error: turns exceptions into user messages
            ├── general_commands.py  # hello
            ├── contact_commands.py  # contact command handlers + CONTACT_COMMANDS dict
            ├── note_commands.py     # note command handlers + NOTE_COMMANDS dict
            └── registry.py        # merges all command dicts into one COMMANDS dict
```

### How the layers work together

```
user input → main.py → parser → registry (COMMANDS) → handler in cli/ → models/ → result string → main.py prints it
```

- **`models/`** holds the data and business logic. Classes validate their own values and **raise exceptions** on invalid input. They never print or ask for input.
- **`cli/`** connects the user to the models. Handlers take parsed arguments, call model methods and **return a string**. They don't print.
- **`storage/`** is the only place that reads or writes files.
- **`main.py`** only runs the loop. It handles `help` and `exit`/`close` itself, and looks up every other command in `COMMANDS`.

### Adding a new command

1. Write a handler function in the matching module (`contact_commands.py` or `note_commands.py`). It takes the arguments and returns a string.
2. Wrap it with the `@input_error` decorator.
3. Add it to that module's commands dict with a short description.
4. Add it to the **Usage** table in this README.

You don't need to change `main.py` to add a command.

## Contributing

1. Create a branch from `main`: `git switch -c feature/<short-name>`
2. Follow PEP 8 and add docstrings to classes and public methods
3. Open a pull request into `main` and request a review from a teammate

## Team

- Daniil Derbas
- Leonid
- Andrii Koptiev
