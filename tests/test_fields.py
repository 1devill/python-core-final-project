"""Corner cases of field validation and birthday date math."""

from datetime import date

import pytest

from personal_assistant.exceptions import ValidationError
from personal_assistant.models.fields import (
    Address,
    Birthday,
    Email,
    Name,
    Phone,
    Tag,
    Text,
)


class TestName:
    @pytest.mark.parametrize(
        "raw, expected", [("anna", "Anna"), ("ANNA", "Anna"), ("aNnA", "Anna")]
    )
    def test_is_normalized(self, raw, expected):
        assert Name(raw).value == expected

    @pytest.mark.xfail(strict=True, reason="BUG: Name has no validation")
    @pytest.mark.parametrize("value", ["", "   "])
    def test_rejects_empty(self, value):
        with pytest.raises(ValidationError):
            Name(value)

    @pytest.mark.xfail(
        strict=True, reason="BUG: capitalize() lowers the rest of the name"
    )
    @pytest.mark.parametrize("value", ["McDonald", "Anna-Maria", "O'Neil"])
    def test_keeps_inner_capitals(self, value):
        assert Name(value).value == value


class TestPhone:
    def test_accepts_ten_digits(self):
        assert Phone("0123456789").value == "0123456789"

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "123456789",
            "12345678901",
            "012345678a",
            "012 345 678",
            "+380501234",
            "-123456789",
            "012345678.",
            None,
            1234567890,
        ],
    )
    def test_rejects_invalid(self, value):
        with pytest.raises(ValidationError):
            Phone(value)

    @pytest.mark.xfail(
        strict=True, reason="BUG: str.isdigit() accepts non-ASCII digits"
    )
    @pytest.mark.parametrize("value", ["٠١٢٣٤٥٦٧٨٩", "²²²²²²²²²²"])
    def test_rejects_non_ascii_digits(self, value):
        with pytest.raises(ValidationError):
            Phone(value)


class TestEmail:
    @pytest.mark.parametrize(
        "value",
        ["a@b.co", "first.last@example.com", "a+tag@sub.example.org", "A_B-1%@x-y.io"],
    )
    def test_accepts_valid(self, value):
        assert Email(value).value == value

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "plain",
            "@b.com",
            "a@",
            "a@b",
            "a@b.c",
            "a@b..com",
            "a b@c.com",
            "a@b.com\n",
            "a@@b.com",
            None,
        ],
    )
    def test_rejects_invalid(self, value):
        with pytest.raises(ValidationError):
            Email(value)

    @pytest.mark.xfail(
        strict=True, reason="BUG: regex allows misplaced dots and hyphens"
    )
    @pytest.mark.parametrize(
        "value", [".a@b.com", "a.@b.com", "a..b@c.com", "a@-b.com"]
    )
    def test_rejects_misplaced_punctuation(self, value):
        with pytest.raises(ValidationError):
            Email(value)


class TestAddress:
    def test_keeps_value(self):
        assert Address("Kyiv Main St 5").value == "Kyiv Main St 5"

    @pytest.mark.xfail(strict=True, reason="BUG: Address has no validation")
    @pytest.mark.parametrize("value", ["", "   "])
    def test_rejects_empty(self, value):
        with pytest.raises(ValidationError):
            Address(value)


class TestBirthday:
    def test_parses_date(self):
        assert Birthday("15.03.1990").bd_date == date(1990, 3, 15)

    def test_accepts_leap_day(self):
        assert Birthday("29.02.2024").bd_date == date(2024, 2, 29)

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "abc",
            "1990-03-15",
            "15/03/1990",
            "32.01.2000",
            "01.13.2000",
            "00.01.2000",
            "31.04.2000",
            "29.02.2023",
            "15.03.90",
        ],
    )
    def test_rejects_invalid(self, value):
        with pytest.raises(ValidationError):
            Birthday(value)

    @pytest.mark.xfail(strict=True, reason="BUG: a birthday in the future is accepted")
    def test_rejects_future_date(self):
        with pytest.raises(ValidationError):
            Birthday("01.01.2999")

    @pytest.mark.parametrize(
        "birthday, today, expected",
        [
            ("30.12.1990", date(2026, 12, 28), date(2026, 12, 30)),
            ("28.12.1990", date(2026, 12, 28), date(2026, 12, 28)),
            ("27.12.1990", date(2026, 12, 28), date(2027, 12, 27)),
            ("02.01.1990", date(2026, 12, 28), date(2027, 1, 2)),
            ("31.12.1990", date(2026, 12, 31), date(2026, 12, 31)),
            ("01.01.1990", date(2026, 12, 31), date(2027, 1, 1)),
            ("29.02.2000", date(2027, 1, 1), date(2027, 3, 1)),
            ("29.02.2000", date(2027, 3, 1), date(2027, 3, 1)),
            ("29.02.2000", date(2027, 3, 2), date(2028, 2, 29)),
            ("29.02.2000", date(2028, 2, 29), date(2028, 2, 29)),
            ("29.02.2000", date(2028, 3, 1), date(2029, 3, 1)),
        ],
    )
    def test_next_occurrence(self, birthday, today, expected):
        assert Birthday(birthday).next_occurrence(today) == expected


class TestTag:
    def test_is_lowercased(self):
        assert Tag("HoMe").value == "home"

    @pytest.mark.parametrize("value", ["", "   "])
    def test_rejects_empty(self, value):
        with pytest.raises(ValidationError):
            Tag(value)

    @pytest.mark.xfail(
        strict=True, reason="BUG: message reads 'Tag Tag must not be empty'"
    )
    def test_error_message(self):
        with pytest.raises(ValidationError, match="^Tag must not be empty$"):
            Tag("")


class TestText:
    @pytest.mark.parametrize("value", ["", "   "])
    def test_rejects_empty(self, value):
        with pytest.raises(ValidationError):
            Text(value)

    @pytest.mark.xfail(strict=True, reason="BUG: Text lowercases what the user wrote")
    def test_keeps_original_case(self):
        assert Text("Call Anna at 5PM").value == "Call Anna at 5PM"

    @pytest.mark.xfail(
        strict=True, reason="BUG: message reads 'Text Tag must not be empty'"
    )
    def test_error_message(self):
        with pytest.raises(ValidationError, match="^Text must not be empty$"):
            Text("")
