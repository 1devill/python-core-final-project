"""Contact fields. Each field validates its own value."""

import re
from datetime import datetime

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
