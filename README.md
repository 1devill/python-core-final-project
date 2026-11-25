# Personal Assistant

A command-line personal assistant for managing contacts and notes.
Team project for the Neoversity course _Python Programming: Foundations and Best Practices_.

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

Contacts and notes are kept in one file, `~/.personal_assistant/data.pkl`, and saved after every command.
If the file is damaged, the assistant starts with an empty book, tells you, and keeps the damaged
file next to it as `data.pkl.bak` (then `data.pkl.bak1`, `data.pkl.bak2`, ...), so nothing is lost.

## Requirements

- Python 3.10+

## Installation

```bash
git clone https://github.com/1devill/python-core-final-project.git
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

### Contact commands

| Command                                                      | Description                                     |
| ------------------------------------------------------------ | ----------------------------------------------- |
| `add [name] [phone]`                                         | Add a contact or a phone to an existing contact |
| `add-birthday [name] [DD.MM.YYYY]`                           | Add a birthday (fails if one is set)            |
| `add-email [name] [email]`                                   | Add an email (fails if one is set)              |
| `add-address [name] [address]`                               | Add an address (fails if one is set)            |
| `all`                                                        | Show all contacts                               |
| `phone [name]`                                               | Show a contact's phones                         |
| `show-birthday` / `show-email` / `show-address [name]`       | Show a contact's birthday / email / address     |
| `show-upcoming-birthdays [days]`                             | Show birthdays within the next N days           |
| `find-contacts [name=..] [phone=..] [email=..] [address=..]` | Find contacts matching all given filters        |
| `change-name [name] [new name]`                              | Rename a contact                                |
| `change-phone [name] [old phone] [new phone]`                | Change a contact's phone                        |
| `change-birthday [name] [DD.MM.YYYY]`                        | Change a contact's birthday                     |
| `change-email [name] [email]`                                | Change a contact's email                        |
| `change-address [name] [new address]`                        | Change a contact's address                      |
| `remove [name]`                                              | Remove a contact                                |
| `remove-phone [name] [phone]`                                | Remove a contact's phone                        |
| `remove-birthday` / `remove-email` / `remove-address [name]` | Remove a contact's birthday / email / address   |

### Note commands

| Command                                                      | Description                                     |
| ------------------------------------------------------------ | ----------------------------------------------- |
| `add-note [name] [tag1,tag2] [text]`                         | Add a note (at least one tag, comma-separated)  |
| `add-note-tag [name] [tag1,tag2]`                            | Add a tag to a note                             |
| `all-notes`                                                  | Show all notes                                  |
| `find-notes [name=..] [tag=..] [text=..]`                    | Find notes matching all given filters           |
| `sort-notes [tag]`                                           | Show all notes, the ones with `[tag]` first     |
| `change-note-name [name] [new name]`                         | Rename a note                                   |
| `change-note-text [name] [text]`                             | Change a note's text                            |
| `change-note-tag [name] [old tag] [new tag]`                 | Replace a note's tag                            |
| `remove-note [name]`                                         | Remove a note                                   |
| `remove-note-tag [name] [tag]`                               | Remove a tag (the last one can't be removed)    |

### General commands

| Command                                                      | Description                                     |
| ------------------------------------------------------------ | ----------------------------------------------- |
| `hello`                                                      | Greeting                                        |
| `help`                                                       | Show all commands, grouped by area              |
| `exit` / `close` / `bye` / `quit`                            | Save data and exit                              |

### Names

Contact and note names are one word and are matched in any case. A name typed all in lowercase or all
in capitals is stored with a capital first letter (`n1` → `N1`, `ANNA` → `Anna`); a name that already
starts with a capital and mixes cases is kept (`McDonald`).

### Adding notes

`add-note [name] [tag1,tag2] [text]` always reads the word after the name as the tags, and everything
after it as the text. The answer shows the tags that were saved, so a mistake is easy to spot:

```text
add-note shop home,food buy milk   →  Note 'Shop' added with tags #home, #food.
add-note shop buy milk             →  Note 'Shop' added with tags #buy.   (text: "milk")
```

`add-note` with no tags or text shows this explanation. `sort-notes [tag]` with a tag no note has
says so and then lists all notes.

### Order of lists

`all`, `all-notes`, `find-contacts` and `find-notes` show items sorted by name (A to Z, ignoring case),
whatever order they were added in. `show-upcoming-birthdays` is sorted by the date of the next birthday.
`sort-notes [tag]` keeps its own order: notes with the tag first, then the rest, each part by name.

### Editing rules

All contact and note commands follow the same rules:

- `add-birthday`, `add-email` and `add-address` **set a missing value**. If the contact already has one, the command is refused and points to the matching `change-*` command.
- `change-name` and `change-note-name` rename a contact or a note. They are refused if the new name is the same or already used by another contact or note.
- `change-phone`, `change-birthday`, `change-email`, `change-address`, `change-note-text` and `change-note-tag` **replace an existing value**. They are refused if there is nothing to change (use `add-*`) or if the new value is the same as the old one.
- A refused or invalid command never changes the data.
- A phone number can belong to only one contact. `add` and `change-phone` refuse a number that another contact already has.
- Emails are stored in lowercase, so `Anna@Example.com` and `anna@example.com` are the same email.
- Commands that take no arguments (`hello`, `all`, `all-notes`, `help`, `exit`) refuse extra words and show their usage, e.g. `help takes no arguments. Usage: help`.

`find-contacts` matches part of a value, in any case, and a phone matches if any of the contact's phones contains it:
`find-contacts name=an address=Kyiv Main St` shows contacts matching both filters.

`find-notes` takes `key=value` filters, which become keyword arguments of `NoteBook.find`:
`find-notes text=buy milk tag=home` → `book.find(text="buy milk", tag="home")`.
Words without `=` belong to the previous filter, so text may contain spaces.
Empty filters (`text=`) are rejected; nothing found (by any filter, name included) prints `No notes found.`

## Project structure

The project uses the `src/` layout.

```
python-core-final-project/
├── pyproject.toml                 # package metadata, `assistant` console command
├── README.md
└── src/
    └── personal_assistant/
        ├── __init__.py
        ├── __main__.py            # enables `python -m personal_assistant`
        ├── main.py                # main loop: load data → read input → dispatch → save after each command
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

   The assistant prints `Interpreted as: ...` and runs the command. Commands that delete or
   change data (`remove-*`, `change-*`, `add-birthday`, `add-email`, `add-address`) ask for
   confirmation first.

| Setting                | Purpose                                                                  |
| ---------------------- | ------------------------------------------------------------------------ |
| `ANTHROPIC_API_KEY`    | API key. `ANTHROPIC_AUTH_TOKEN` also works                               |
| `ASSISTANT_AI_MODEL`   | Model to use. Without this setting: `claude-opus-5-5`                    |

Good to know:

- The file must be named `.env`: `.env.local` is not loaded.
- `.env` is looked for in the folder you start the assistant from, or a folder above it, and then
  in `~/.personal_assistant/.env`. Put the key in that last file to use the AI parser from any
  folder. A variable already set in your shell is never overridden.
- `.env` is ignored by Git. Never commit a real key, and do not put one in `.env.example`.
- One request runs one command. If you ask for several, the assistant asks you to send them one
  at a time. If no command fits, it prints the model's short explanation instead of
  `Unknown command`.
- Press Ctrl+C while waiting for the answer to cancel the request.
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

The same checks run in GitHub Actions ([ci.yml](.github/workflows/ci.yml)) on every pull request and
every push to `main`:

| Job                      | What it does                                                                  |
| ------------------------ | ----------------------------------------------------------------------------- |
| Format, lint and types   | `black --check .`, `ruff check .` and `mypy src tests` (Python 3.15)          |
| Tests                    | `pytest` with coverage on Python 3.10 and 3.15 (Ubuntu) and Python 3.15 (Windows) |
| Install as a user        | `pip install .` in a clean virtual environment, then runs `assistant` from another folder and checks that data survives a restart |

A pull request should be merged only when all jobs are green.

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
