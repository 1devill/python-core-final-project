"""ContactBook: stores contacts by name."""

from collections import UserDict

from personal_assistant.exceptions import ContactDoesNotExist, ValidationError

from .contact import Contact


class ContactBook(UserDict):
    def __str__(self) -> str:
        if not self.data:
            return "No contacts yet"
        return "\n".join(str(contact) for contact in self.data.values())

    def add_contact(self, contact: Contact) -> None:
        name = contact.name.value

        if name in self.data:
            raise ValidationError(f"Contact '{name}' already exists")

        self.data[name] = contact

    def find(self, name: str) -> Contact:
        if name not in self.data:
            raise ContactDoesNotExist(name)
        return self.data[name]

    def delete(self, name: str) -> None:
        if name not in self.data:
            raise ContactDoesNotExist(name)

        del self.data[name]
