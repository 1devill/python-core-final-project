"""Contact: one person in the book, composed of fields."""

from personal_assistant.exceptions import ValidationError
from personal_assistant.models.fields import Address, Birthday, Email, Name, Phone


class Contact:
    def __init__(self, name: str) -> None:
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

    def add_phone(self, phone_num: str) -> None:
        phone = Phone(phone_num)

        if self.find_phone(phone_num) is not None:
            raise ValidationError(f"Phone number {phone_num} already exists")

        self.phones.append(phone)

    def add_birthday(self, birthday: str) -> None:
        self.birthday = Birthday(birthday)

    def add_email(self, email: str) -> None:
        self.email = Email(email)

    def add_address(self, address: str) -> None:
        self.address = Address(address)

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
