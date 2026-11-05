"""Corner cases of contact lookup, upcoming birthdays and search."""

from datetime import date

import pytest

from personal_assistant.exceptions import ContactDoesNotExist, ValidationError
from personal_assistant.models import Contact


def names(contacts) -> list[str]:
    return [contact.name.value for contact in contacts]


def upcoming(book, days: int) -> list[str]:
    return [item.contact.name.value for item in book.find_upcoming_birthdays(days)]


class TestLookup:
    def test_duplicate_name_is_rejected_in_any_case(self, book, make_contact):
        make_contact("anna")
        with pytest.raises(ValidationError):
            book.add_contact(Contact("ANNA"))

    def test_find_missing(self, book):
        with pytest.raises(ContactDoesNotExist):
            book.find("Anna")

    def test_delete_missing(self, book):
        with pytest.raises(ContactDoesNotExist):
            book.delete("Anna")

    def test_delete(self, book, make_contact):
        make_contact("anna")
        book.delete("Anna")
        assert "Anna" not in book

    @pytest.mark.xfail(
        strict=True,
        raises=ContactDoesNotExist,
        reason="BUG: ContactBook.find is case-sensitive, NoteBook.get_note is not",
    )
    def test_find_ignores_case_like_notebook(self, book, make_contact):
        make_contact("anna")
        assert book.find("anna").name.value == "Anna"


class TestUpcomingBirthdays:
    @pytest.mark.parametrize(
        "birthday, days, found",
        [
            ("10.06.1990", 0, True),
            ("10.06.1990", 7, True),
            ("11.06.1990", 0, False),
            ("11.06.1990", 1, True),
            ("17.06.1990", 7, True),
            ("18.06.1990", 7, False),
            ("09.06.1990", 7, False),
            ("09.06.1990", 364, True),
            ("09.06.1990", 363, False),
        ],
    )
    def test_window_edges(
        self, book, make_contact, freeze_today, birthday, days, found
    ):
        freeze_today(2026, 6, 10)
        make_contact("anna", birthday=birthday)
        assert upcoming(book, days) == (["Anna"] if found else [])

    def test_crosses_new_year(self, book, make_contact, freeze_today):
        freeze_today(2026, 12, 28)
        make_contact("anna", birthday="02.01.1990")
        assert book.find_upcoming_birthdays(7)[0].next_birthday == date(2027, 1, 2)

    def test_leap_day_in_a_common_year(self, book, make_contact, freeze_today):
        freeze_today(2027, 2, 27)
        make_contact("anna", birthday="29.02.2000")
        assert upcoming(book, 1) == []
        assert book.find_upcoming_birthdays(2)[0].next_birthday == date(2027, 3, 1)

    def test_sorted_by_next_date_not_birth_year(self, book, make_contact, freeze_today):
        freeze_today(2026, 12, 28)
        make_contact("january", birthday="01.01.1950")
        make_contact("today", birthday="28.12.2001")
        make_contact("december", birthday="30.12.1970")
        assert upcoming(book, 7) == ["Today", "December", "January"]

    def test_same_day_lists_everyone(self, book, make_contact, freeze_today):
        freeze_today(2026, 6, 10)
        make_contact("anna", birthday="12.06.1990")
        make_contact("bob", birthday="12.06.2000")
        assert sorted(upcoming(book, 2)) == ["Anna", "Bob"]

    def test_skips_contacts_without_birthday(self, book, make_contact, freeze_today):
        freeze_today(2026, 6, 10)
        make_contact("anna")
        assert upcoming(book, 365) == []

    def test_each_contact_listed_once_in_a_long_window(
        self, book, make_contact, freeze_today
    ):
        freeze_today(2026, 6, 10)
        make_contact("anna", birthday="11.06.1990")
        assert upcoming(book, 5000) == ["Anna"]

    def test_empty_book(self, book):
        assert book.find_upcoming_birthdays(7) == []

    def test_negative_days(self, book):
        with pytest.raises(ValidationError):
            book.find_upcoming_birthdays(-1)


class TestSearch:
    @pytest.fixture(autouse=True)
    def contacts(self, make_contact):
        make_contact(
            "anna",
            phones=["0123456789", "0987654321"],
            email="Anna@Gmail.com",
            address="Kyiv Main St 5",
        )
        make_contact("hanna", phones=["0555555555"], email="h@ukr.net")
        make_contact("bob")

    @pytest.mark.parametrize(
        "filters, expected",
        [
            ({"name": "AN"}, ["Anna", "Hanna"]),
            ({"name": "bob"}, ["Bob"]),
            ({"phone": "0987"}, ["Anna"]),
            ({"phone": "0"}, ["Anna", "Hanna"]),
            ({"email": "GMAIL"}, ["Anna"]),
            ({"email": "@"}, ["Anna", "Hanna"]),
            ({"address": "main st"}, ["Anna"]),
            ({"name": "an", "email": "ukr"}, ["Hanna"]),
            ({"name": "an", "phone": "0000"}, []),
            ({"name": "zzz"}, []),
        ],
    )
    def test_filters(self, book, filters, expected):
        assert names(book.search_contacts(**filters)) == expected

    def test_no_filters(self, book):
        with pytest.raises(ValueError):
            book.search_contacts()

    @pytest.mark.parametrize("key", ["name", "phone", "email", "address"])
    @pytest.mark.parametrize("value", ["", "   "])
    def test_empty_filter(self, book, key, value):
        with pytest.raises(ValidationError):
            book.search_contacts(**{key: value})

    def test_filters_are_keyword_only(self, book):
        with pytest.raises(TypeError):
            book.search_contacts("anna")
