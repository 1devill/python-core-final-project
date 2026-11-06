"""Contact fields. Each field validates its own value."""

import re
from datetime import date, datetime

from personal_assistant.constants import DATE_PARSE_FORMAT, EMAIL_REGEX
from personal_assistant.exceptions import ValidationError


class Field:
    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    def __init__(self, value: str) -> None:
        super().__init__(value.capitalize())


class Birthday(Field):
    FORMAT = "DD.MM.YYYY"

    def __init__(self, value: str) -> None:
        try:
            self.bd_date = datetime.strptime(value, DATE_PARSE_FORMAT).date()
        except ValueError:
            raise ValidationError(f"Invalid date format. Use {Birthday.FORMAT}")
        super().__init__(value)

    def next_occurrence(self, today: date) -> date:
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
    def __init__(self, phone_num: str) -> None:
        if not isinstance(phone_num, str) or not phone_num.isdigit():
            raise ValidationError("Phone number must contain only digits")

        if len(phone_num) != 10:
            raise ValidationError("Phone number must be exactly 10 digits long")

        super().__init__(phone_num)


class Email(Field):
    def __init__(self, email: str) -> None:
        if not isinstance(email, str) or not re.fullmatch(EMAIL_REGEX, email):
            raise ValidationError("Email format is incorrect")

        super().__init__(email)


class Address(Field):
    pass


class Tag(Field):
    """
    note tag: stored in lowercase, must not be empty
    """

    def __init__(self, value: str) -> None:
        if not value or value.strip() == "":
            raise ValidationError(f"{self.__class__.__name__} Tag must not be empty")
        super().__init__(value.lower())


class Text(Field):
    """
    note text: must not be empty
    """

    def __init__(self, value: str) -> None:
        if not value or value.strip() == "":
            raise ValidationError(f"{self.__class__.__name__} Text must not be empty")
        super().__init__(value)
