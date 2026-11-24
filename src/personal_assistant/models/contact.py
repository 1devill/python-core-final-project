"""Contact: one person in the book, composed of fields."""

from personal_assistant.exceptions import ValidationError

from .fields import Address, Birthday, Email, Name, Phone


class Contact:
    """One person in the address book: a name plus optional phones, birthday, email, address."""

    def __init__(self, name: str) -> None:
        self._setup(name)

    def _setup(self, name: str) -> None:
        """Set the name and start with no other fields; shared by __init__ and __setstate__."""
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None
        self.email: Email | None = None
        self.address: Address | None = None

    def __str__(self) -> str:
        phones = "; ".join(str(phone) for phone in self.phones) or "-"
        result = f"Contact name: {self.name}, phones: {phones}"
        if self.birthday:
            result += f", birthday: {self.birthday}"
        if self.email:
            result += f", email: {self.email}"
        if self.address:
            result += f", address: {self.address}"
        return result

    def __getstate__(self) -> dict:
        """Plain built-in data used by pickle to save the contact.

        Only strings are stored (not Name/Phone objects), so the file does not depend
        on the field classes and stays loadable if they change.
        """
        return {
            "name": self.name.value,
            "phones": [phone.value for phone in self.phones],
            "birthday": self.birthday.value if self.birthday else None,
            "email": self.email.value if self.email else None,
            "address": self.address.value if self.address else None,
        }

    def __setstate__(self, state: dict) -> None:
        """Rebuild the contact through the field constructors; raises on invalid data.

        Going through the constructors re-validates every value, so a corrupted or
        hand-edited file cannot bring invalid data into the book.
        """
        self._setup(state["name"])
        for phone in state.get("phones") or []:
            self.add_phone(phone)
        if state.get("birthday") is not None:
            self.add_birthday(state["birthday"])
        if state.get("email") is not None:
            self.add_email(state["email"])
        if state.get("address") is not None:
            self.add_address(state["address"])

    def add_phone(self, phone_num: str) -> None:
        phone = Phone(phone_num)

        if self.find_phone(phone_num) is not None:
            raise ValidationError(f"Phone number {phone_num} already exists")

        self.phones.append(phone)

    def add_birthday(self, birthday: str) -> None:
        if self.birthday is not None:
            raise ValidationError("Birthday is already set")
        self.birthday = Birthday(birthday)

    def change_birthday(self, new_birthday: str) -> None:
        if self.birthday is None:
            raise ValidationError("Birthday is not set yet")
        new = Birthday(new_birthday)
        if self.birthday.value == new.value:
            raise ValidationError("New birthday is the same as the current one")
        self.birthday = new

    def add_email(self, email: str) -> None:
        if self.email is not None:
            raise ValidationError("Email is already set")
        self.email = Email(email)

    def change_email(self, new_email: str) -> None:
        if self.email is None:
            raise ValidationError("Email is not set yet")
        new = Email(new_email)
        if self.email.value == new.value:
            raise ValidationError("New email is the same as the current one")
        self.email = new

    def add_address(self, address: str) -> None:
        if self.address is not None:
            raise ValidationError("Address is already set")
        self.address = Address(address)

    def change_address(self, new_address: str) -> None:
        if self.address is None:
            raise ValidationError("Address is not set yet")
        new = Address(new_address)
        if self.address.value == new.value:
            raise ValidationError("New address is the same as the current one")
        self.address = new

    def find_phone(self, phone_num: str) -> Phone | None:
        return next((phone for phone in self.phones if phone.value == phone_num), None)

    def get_phones(self) -> str:
        if not self.phones:
            return "No phones for current contact"
        return "Phones: " + ", ".join(str(phone) for phone in self.phones)

    def edit_phone(self, prev_phone_num: str, new_phone_num: str) -> None:
        if prev_phone_num == new_phone_num:
            raise ValidationError(
                f"Phone numbers {prev_phone_num} and {new_phone_num} are identical"
            )

        phone = self.find_phone(prev_phone_num)

        if phone is None:
            raise ValidationError(f"Phone number {prev_phone_num} not found")

        if self.find_phone(new_phone_num) is not None:
            raise ValidationError(f"Phone number {new_phone_num} already exists")

        new_phone = Phone(new_phone_num)
        self.phones[self.phones.index(phone)] = new_phone

    def remove_phone(self, phone_num: str) -> None:
        phone = self.find_phone(phone_num)

        if phone is None:
            raise ValidationError(f"Phone number {phone_num} not found")

        self.phones.remove(phone)

    def remove_email(self) -> None:
        if self.email is None:
            raise ValidationError("Contact has no email set")
        self.email = None

    def remove_birthday(self) -> None:
        if self.birthday is None:
            raise ValidationError("Contact has no birthday set")
        self.birthday = None

    def remove_address(self) -> None:
        if self.address is None:
            raise ValidationError("Contact has no address set")
        self.address = None
