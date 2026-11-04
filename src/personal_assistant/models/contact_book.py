"""ContactBook: stores contacts by name."""

from collections import UserDict
from datetime import date
from typing import NamedTuple

from personal_assistant.exceptions import ContactDoesNotExist, ValidationError
from personal_assistant.models.contact import Contact


class UpcomingBirthday(NamedTuple):
    contact: Contact
    next_birthday: date


class ContactBook(UserDict[str, Contact]):
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

    def find_upcoming_birthdays(self, days_interval: int) -> list[UpcomingBirthday]:
        today = date.today()
        upcoming_birthdays: list[UpcomingBirthday] = []

        for contact in self.data.values():
            if contact.birthday is None:
                continue

            next_birthday = contact.birthday.next_occurrence(today)
            if 0 <= (next_birthday - today).days <= days_interval:
                upcoming_birthdays.append(UpcomingBirthday(contact, next_birthday))

        return sorted(upcoming_birthdays, key=lambda upcoming: upcoming.next_birthday)
