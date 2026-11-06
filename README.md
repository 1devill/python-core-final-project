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
- Show contacts with a birthday within the next N days

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
| `find-contacts [name=..] [phone=..] [email=..] [address=..]` | Find contacts matching all given filters        |
| `add-birthday [name] [DD.MM.YYYY]`                           | Add a birthday to a contact                     |
| `add-email [name] [email]`                                   | Add an email to a contact                       |
| `add-address [name] [address]`                               | Add an address to a contact                     |
| `show-birthday` / `show-email` / `show-address [name]`       | Show a contact's birthday / email / address     |
| `show-upcoming-birthdays [days]`                             | Show birthdays within the next N days           |
| `remove [name]`                                              | Remove a contact                                |
| `remove-phone [name] [phone]`                                | Remove a contact's phone                        |
| `remove-birthday` / `remove-email` / `remove-address [name]` | Remove a contact's birthday / email / address   |
| `add-note [name] [tag1,tag2] [text]`                         | Add a note (at least one tag, comma-separated)  |
| `all-notes`                                                  | Show all notes                                  |
| `find-notes [name=..] [tag=..] [text=..]`                    | Find notes matching all given filters           |
| `sort-notes [tag]`                                           | Show all notes, the ones with `[tag]` first     |
| `change-note-text [name] [text]`                             | Replace a note's text                           |
| `add-note-tag [name] [tag]`                                  | Add a tag to a note                             |
| `change-note-tag [name] [old tag] [new tag]`                 | Replace a note's tag                            |
| `remove-note-tag [name] [tag]`                               | Remove a tag (the last one can't be removed)    |
| `remove-note [name]`                                         | Remove a note                                   |
| `help`                                                       | Show all commands                               |
| `exit` / `close` / `bye` / `quit`                            | Save data and exit                              |

`find-contacts` matches part of a value, in any case, and a phone matches if any of the contact's phones contains it:
`find-contacts name=an address=Kyiv Main St` shows contacts matching both filters.

`find-notes` takes `key=value` filters, which become keyword arguments of `NoteBook.find`:
`find-notes text=buy milk tag=home` → `book.find(text="buy milk", tag="home")`.
Words without `=` belong to the previous filter, so text may contain spaces.
Empty filters (`text=`) are rejected; nothing found (by any filter, name included) prints `No notes found.`

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
        │   └── storage.py         # Storage class: save/load data in ~/.personal_assistant/
        │
        └── cli/                   # everything related to user interaction
            ├── parser.py          # splits user input into command + arguments, parses search filters
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
3. Run the [checks](#checks-before-a-pull-request) and fix what they report
4. Open a pull request into `main` and request a review from a teammate

### Development setup

Install the project with the development tools, inside the virtual environment:

```bash
pip install -e ".[dev]"
```

Run the same command again after `pyproject.toml` changes. To work on the AI parser too, see
[AI parser](#ai-parser).

| Tool                                           | Purpose                                  |
| ---------------------------------------------- | ---------------------------------------- |
| [Black](https://black.readthedocs.io)          | Code formatting                          |
| [Ruff](https://docs.astral.sh/ruff/)           | Linting and import sorting               |
| [mypy](https://mypy.readthedocs.io)            | Type checking                            |
| [pytest](https://docs.pytest.org)              | Tests                                    |

All tools are configured in `pyproject.toml`. Black is the only formatter: do not use `ruff format`.

### AI parser

The AI parser is optional. It turns input that is not a known command into one, using the
[Claude API](https://platform.claude.com/docs). Without its packages or an API key, the assistant
works as usual.

1. Install the extra packages:

   ```bash
   pip install -e ".[dev,ai]"
   ```

2. Create your local settings file in the project root:

   ```bash
   cp .env.example .env
   ```

3. Put your key from the [Claude Console](https://platform.claude.com/) in `.env`:

   ```bash
   ANTHROPIC_API_KEY=your_api_token_here
   ASSISTANT_AI_MODEL=claude-haiku-5-5
   ```

4. Check that the assistant sees the settings:

   ```bash
   python -c "from personal_assistant.cli import ai_parser as a; print(a.is_enabled(), a.MODEL)"
   ```

   It prints `True` and the model name. This only checks that a key is set: a wrong key shows
   `AI parser: invalid API key.` on the first request.

5. Start the assistant from the project root and type something that is not a command:

   ```text
   please show all my contacts
   ```

   The assistant prints `Interpreted as: ...` and runs the command. Commands that delete data
   ask for confirmation first.

| Setting                | Purpose                                                                  |
| ---------------------- | ------------------------------------------------------------------------ |
| `ANTHROPIC_API_KEY`    | API key. `ANTHROPIC_AUTH_TOKEN` also works                               |
| `ASSISTANT_AI_MODEL`   | Model to use. Without this setting: `claude-opus-5-5`                    |

Good to know:

- The file must be named `.env`: `.env.local` is not loaded.
- `.env` is found only in the folder you start the assistant from, or a folder above it. To use
  the AI parser from anywhere, export `ANTHROPIC_API_KEY` in your shell instead.
- `.env` is ignored by Git. Never commit a real key, and do not put one in `.env.example`.
- Requests cost money and are billed to the key's account.
- Any line that is not a known command, typos included, is sent to the Anthropic API.
- A line that starts with a known command never reaches the AI parser: `add anna to contacts`
  runs `add`.

Tests never call the API, so they need no key. Tests that use the real SDK are skipped without the
`ai` extra.

### Checks before a pull request

```bash
black .              # format the code
ruff check --fix .   # lint and sort imports
mypy src tests       # check types
pytest               # run the tests
```

Tests marked `xfail` are known bugs. When you fix one, its test fails with `XPASS(strict)`:
remove its `@pytest.mark.xfail` line.

To see test coverage:

```bash
pytest --cov=personal_assistant --cov-report=term-missing
```

### VS Code

Install the extensions [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter),
[Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) and
[Mypy Type Checker](https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker).
Select the `.venv` interpreter with **Python: Select Interpreter**, then add this to your settings
to format and sort imports on save:

```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports.ruff": "explicit"
    }
  }
}
```

## Team

- Daniil Derbas
- Leonid Tsarov
- Andrii Koptiev
