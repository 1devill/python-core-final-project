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

        if days_interval < 0:
            raise ValidationError("Days must be 0 or more")

        for contact in self.data.values():
            if contact.birthday is None:
                continue

            next_birthday = contact.birthday.next_occurrence(today)
            if 0 <= (next_birthday - today).days <= days_interval:
                upcoming_birthdays.append(UpcomingBirthday(contact, next_birthday))

        return sorted(upcoming_birthdays, key=lambda upcoming: upcoming.next_birthday)

    def search_contacts(
        self,
        *,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
    ) -> list[Contact]:
        """
        find contacts matching ALL given filters; filters are keyword-only (find-contacts passes them as **kwargs)
        :param name: part of the contact name: str, any case
        :param phone: part of any of the contact phones: str
        :param email: part of the contact email: str, any case
        :param address: part of the contact address: str, any case
        :return: list[Contact], empty if nothing matches; raises ValueError if no filter is given
            and ValidationError if a given filter is empty ("" is in every text and would match all contacts)
        """
        filters = {"name": name, "phone": phone, "email": email, "address": address}
        if all(value is None for value in filters.values()):
            raise ValueError("At least one search parameter is required")
        for key, value in filters.items():
            if value is not None and not value.strip():
                raise ValidationError(f"Filter '{key}' must not be empty")

        contacts = list(self.data.values())
        if name is not None:
            name = name.lower()
            contacts = [
                contact for contact in contacts if name in contact.name.value.lower()
            ]
        if phone is not None:
            contacts = [
                contact
                for contact in contacts
                if any(phone in number.value for number in contact.phones)
            ]
        if email is not None:
            email = email.lower()
            contacts = [
                contact
                for contact in contacts
                if contact.email and email in contact.email.value.lower()
            ]
        if address is not None:
            address = address.lower()
            contacts = [
                contact
                for contact in contacts
                if contact.address and address in contact.address.value.lower()
            ]
        return contacts
