"""Contact fields. Each field validates its own value."""

import re
from datetime import date, datetime

from personal_assistant.constants import DATE_PARSE_FORMAT, EMAIL_REGEX
from personal_assistant.exceptions import ValidationError


class Field:
    """Base class for all fields: stores a value and prints it as text."""

    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class RequiredText(Field):
    """Text field that must not be empty; stored without surrounding spaces."""

    def __init__(self, value: str) -> None:
        if not value.strip():
            raise ValidationError(f"{self.__class__.__name__} must not be empty")
        super().__init__(value.strip())


class Name(RequiredText):
    """Contact or note name: must not be empty, stored stripped.

    A name typed all in one case or starting with a small letter is capitalized
    ("anna", "ANNA" -> "Anna"); a name that already starts with a capital letter
    and mixes cases keeps it ("McDonald", "Anna-Maria", "O'Neil").
    """

    def __init__(self, value: str) -> None:
        super().__init__(value)
        name = self.value
        if not name[0].isupper() or name.isupper():
            self.value = name.capitalize()


class Birthday(Field):
    """Birthday as a DD.MM.YYYY string, not in the future; the date is kept in bd_date."""

    FORMAT = "DD.MM.YYYY"

    def __init__(self, value: str) -> None:
        try:
            self.bd_date = datetime.strptime(value, DATE_PARSE_FORMAT).date()
        except ValueError:
            raise ValidationError(f"Invalid date format. Use {Birthday.FORMAT}")
        if self.bd_date > date.today():
            raise ValidationError("Birthday can't be in the future")
        super().__init__(value)

    def next_occurrence(self, today: date) -> date:
        """Return the next birthday date on or after today."""
        birthday = self._get_next_birthday_date(self.bd_date, today.year)
        if birthday < today:
            return self._get_next_birthday_date(self.bd_date, today.year + 1)
        return birthday

    @staticmethod
    def _get_next_birthday_date(date_of_birth: date, year: int) -> date:
        try:
            return date_of_birth.replace(year=year)
        except ValueError:  # 29 February in a non-leap year moved to March 1
            return date(year, 3, 1)


class Phone(Field):
    """Phone number: exactly 10 digits."""

    def __init__(self, phone_num: str) -> None:
        if not isinstance(phone_num, str) or not re.fullmatch(r"[0-9]+", phone_num):
            raise ValidationError("Phone number must contain only digits")

        if len(phone_num) != 10:
            raise ValidationError("Phone number must be exactly 10 digits long")

        super().__init__(phone_num)


class Email(Field):
    """Email address that matches EMAIL_REGEX; stored in lowercase."""

    def __init__(self, email: str) -> None:
        if not isinstance(email, str) or not re.fullmatch(EMAIL_REGEX, email):
            raise ValidationError("Email format is incorrect")

        super().__init__(email.lower())


class Address(RequiredText):
    """Contact address: free text, not empty, at most MAX_LENGTH characters, stripped."""

    MAX_LENGTH = 200

    def __init__(self, value: str) -> None:
        super().__init__(value)
        if len(self.value) > Address.MAX_LENGTH:
            raise ValidationError(
                f"Address must be at most {Address.MAX_LENGTH} characters long"
            )


class Tag(RequiredText):
    """Note tag: must not be empty, stored stripped and in lowercase."""

    def __init__(self, value: str) -> None:
        super().__init__(value.lower())


class Text(RequiredText):
    """Note text: must not be empty, stored stripped."""
