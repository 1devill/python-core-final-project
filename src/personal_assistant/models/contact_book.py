"""ContactBook: stores contacts by name."""

from collections import UserDict
from datetime import date
from typing import NamedTuple

from personal_assistant.exceptions import ContactDoesNotExist, ValidationError

from .contact import Contact
from .fields import Name


class UpcomingBirthday(NamedTuple):
    contact: Contact
    next_birthday: date


class ContactBook(UserDict[str, Contact]):
    def __str__(self) -> str:
        if not self.data:
            return "No contacts yet"
        return "\n".join(str(contact) for contact in self.data.values())

    def _key(self, name: str) -> str | None:
        """Return the stored key for a name typed in any case, or None."""
        wanted = name.strip().casefold()
        return next((key for key in self.data if key.casefold() == wanted), None)

    def add_contact(self, contact: Contact) -> None:
        """Add a contact; raises ValidationError if the name is taken in any case."""
        name = contact.name.value

        if self._key(name) is not None:
            raise ValidationError(f"Contact '{name}' already exists")

        self.data[name] = contact

    def find(self, name: str) -> Contact:
        """Return the contact with this name in any case; raises ContactDoesNotExist."""
        key = self._key(name)
        if key is None:
            raise ContactDoesNotExist(Name(name).value)
        return self.data[key]

    def rename(self, name: str, new_name: str) -> Contact:
        """Give a contact a new name and return it.

        Raises ContactDoesNotExist if there is no contact with the old name, and
        ValidationError if the new name is invalid, the same as the current one, or
        used by another contact in any case. Nothing changes if it raises.
        """
        key = self._key(name)
        if key is None:
            raise ContactDoesNotExist(Name(name).value)
        new = Name(new_name)
        if new.value == key:
            raise ValidationError("New name is the same as the current one")
        taken = self._key(new.value)
        if taken is not None and taken != key:
            raise ValidationError(f"Contact '{taken}' already exists")
        contact = self.data.pop(key)
        contact.name = new
        self.data[new.value] = contact
        return contact

    def find_by_phone(self, phone: str) -> Contact | None:
        """Return the contact that has this phone number, or None."""
        return next(
            (c for c in self.data.values() if c.find_phone(phone) is not None), None
        )

    def check_phone_is_free(self, phone: str, contact: Contact | None = None) -> None:
        """Raise ValidationError if another contact already has this phone.

        The contact itself is skipped: it reports a repeated phone on its own.
        """
        owner = self.find_by_phone(phone)
        if owner is not None and owner is not contact:
            raise ValidationError(
                f"Phone number {phone} already belongs to '{owner.name.value}'"
            )

    def delete(self, name: str) -> None:
        """Delete the contact with this name in any case; raises ContactDoesNotExist."""
        key = self._key(name)
        if key is None:
            raise ContactDoesNotExist(Name(name).value)

        del self.data[key]

    def sorted_contacts(self) -> list[Contact]:
        """Return all contacts sorted by name, ignoring case."""
        return sorted(
            self.data.values(), key=lambda contact: contact.name.value.casefold()
        )

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
        :return: list[Contact] sorted by name, empty if nothing matches; raises ValueError if no filter is given
            and ValidationError if a given filter is empty ("" is in every text and would match all contacts)
        """
        filters = {"name": name, "phone": phone, "email": email, "address": address}
        if all(value is None for value in filters.values()):
            raise ValueError("At least one search parameter is required")
        for key, value in filters.items():
            if value is not None and not value.strip():
                raise ValidationError(f"Filter '{key}' must not be empty")

        contacts = self.sorted_contacts()
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
