"""Custom exceptions of the Personal Assistant."""


class AssistantError(Exception):
    """Base class for errors whose message is safe to show to the user as-is."""


class ValidationError(AssistantError):
    """Raised when a value fails validation."""


class ContactDoesNotExist(AssistantError):
    """Raised when a contact is not found in the book."""

    def __init__(self, name: str):
        super().__init__(f"Contact '{name}' does not exist.")
        self.name = name


class NoteDoesNotExist(AssistantError):
    """Raised when a contact is not found in the book."""

    def __init__(self, name: str):
        super().__init__(f"Note '{name}' does not exist.")
        self.name = name
