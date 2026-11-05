"""Translate free-form user input into an assistant command with Claude.

The model never touches the data: it only picks one of the existing commands and
its arguments. The normal handlers and field validators still run afterwards.

The feature is optional. It is on only when the `anthropic` package is installed and
ANTHROPIC_API_KEY (or ANTHROPIC_AUTH_TOKEN) is set; otherwise the assistant behaves
exactly as before.
"""

import os
from datetime import date

from personal_assistant.cli.command import Command

try:
    import anthropic
except ImportError:  # the AI parser is an optional extra
    anthropic = None

try:  # read ANTHROPIC_API_KEY / ASSISTANT_AI_MODEL from a .env file, if any
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True))
except ImportError:
    pass

MODEL = os.environ.get("ASSISTANT_AI_MODEL", "claude-opus-5-5")
TOOL_NAME = "run_command"

# Commands the model may not choose: the loop handles them itself.
EXCLUDED = {Command.HELP, Command.EXIT}

# Commands that delete data: the user must confirm them before they run.
CONFIRM_COMMANDS = {
    Command.REMOVE_CONTACT,
    Command.REMOVE_PHONE,
    Command.REMOVE_EMAIL,
    Command.REMOVE_BIRTHDAY,
    Command.REMOVE_ADDRESS,
    Command.REMOVE_NOTE,
    Command.REMOVE_NOTE_TAG,
}

_client = None


class AIParserError(Exception):
    """The AI request failed; the message is safe to show to the user."""


def is_enabled() -> bool:
    """Return True if the SDK is installed and credentials are configured."""
    return anthropic is not None and bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )


def _available_commands() -> list[Command]:
    return [command for command in Command if command not in EXCLUDED]


def _system_prompt() -> str:
    catalog = "\n".join(
        f"- {command.usage}: {command.description}" for command in _available_commands()
    )
    return (
        "You translate a user's request for a contacts and notes assistant into exactly "
        f"one assistant command. Always answer by calling the {TOOL_NAME} tool; if no "
        "command fits the request, answer in one short sentence without calling it.\n\n"
        f"Commands:\n{catalog}\n\n"
        "Rules:\n"
        "- Contact names and note names are a single word. Use only what the user wrote; "
        "never invent names, phones, emails or other values.\n"
        "- Pass phone numbers and emails exactly as the user wrote them.\n"
        "- Birthdays must be DD.MM.YYYY. Convert dates like 'March 5, 1990' to 05.03.1990.\n"
        "- Tags are one comma-separated argument without spaces, e.g. work,urgent.\n"
        "- Free text (an address, a note text) may be one argument or several words.\n"
        "- find-notes filters are arguments like name=..., tag=..., text=....\n"
        f"- Today is {date.today().strftime('%d.%m.%Y')}."
    )


def _tool() -> dict:
    return {
        "name": TOOL_NAME,
        "description": "Run one assistant command with its arguments.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": [command.value for command in _available_commands()],
                },
                "args": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["command", "args"],
            "additionalProperties": False,
        },
    }


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=30.0, max_retries=1)
    return _client


def parse(user_input: str) -> tuple[Command, list[str]] | None:
    """Return the command and arguments the user meant, or None if nothing fits.

    :raises AIParserError: the request failed (network, auth, rate limit, refusal)
    """
    try:
        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=4096,
            output_config={"effort": "low"},
            system=_system_prompt(),
            tools=[_tool()],
            messages=[{"role": "user", "content": user_input}],
        )
    except anthropic.AuthenticationError:
        raise AIParserError("AI parser: invalid API key.") from None
    except anthropic.RateLimitError:
        raise AIParserError("AI parser: rate limited, try again later.") from None
    except anthropic.APIConnectionError:
        raise AIParserError("AI parser: cannot reach the API.") from None
    except anthropic.APIError as error:
        raise AIParserError(f"AI parser failed: {error.message}") from None
    return _extract(response)


def _extract(response) -> tuple[Command, list[str]] | None:
    """Pull the command out of a response; None if the model chose no command."""
    if response.stop_reason == "refusal":
        return None
    for block in response.content:
        if block.type == "tool_use" and block.name == TOOL_NAME:
            command = Command.parse(str(block.input.get("command", "")))
            if command is None or command in EXCLUDED:
                return None
            args = [str(arg) for arg in block.input.get("args", [])]
            return command, args
    return None
