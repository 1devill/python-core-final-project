"""Corner cases of a single contact."""

import pytest

from personal_assistant.exceptions import ValidationError
from personal_assistant.models import Contact

FIRST, SECOND, THIRD = "0123456789", "0987654321", "0555555555"


@pytest.fixture
def contact() -> Contact:
    contact = Contact("anna")
    contact.add_phone(FIRST)
    contact.add_phone(SECOND)
    return contact


def phones(contact: Contact) -> list[str]:
    return [phone.value for phone in contact.phones]


def test_new_contact_has_only_a_name():
    contact = Contact("anna")
    assert contact.name.value == "Anna"
    assert contact.phones == []
    assert (contact.birthday, contact.email, contact.address) == (None, None, None)


def test_duplicate_phone_is_rejected(contact):
    with pytest.raises(ValidationError):
        contact.add_phone(FIRST)
    assert phones(contact) == [FIRST, SECOND]


def test_invalid_phone_is_not_added(contact):
    with pytest.raises(ValidationError):
        contact.add_phone("123")
    assert phones(contact) == [FIRST, SECOND]


def test_edit_phone_keeps_position(contact):
    contact.edit_phone(FIRST, THIRD)
    assert phones(contact) == [THIRD, SECOND]


@pytest.mark.parametrize(
    "old, new",
    [
        (FIRST, FIRST),
        (THIRD, "0111111111"),
        (FIRST, SECOND),
        (FIRST, "123"),
    ],
    ids=["identical", "old-missing", "new-exists", "new-invalid"],
)
def test_edit_phone_failure_changes_nothing(contact, old, new):
    with pytest.raises(ValidationError):
        contact.edit_phone(old, new)
    assert phones(contact) == [FIRST, SECOND]


def test_remove_missing_phone(contact):
    with pytest.raises(ValidationError):
        contact.remove_phone(THIRD)


def test_can_remove_the_last_phone(contact):
    contact.remove_phone(FIRST)
    contact.remove_phone(SECOND)
    assert contact.phones == []
    assert contact.get_phones() == "No phones for current contact"


@pytest.mark.parametrize(
    "method", ["remove_email", "remove_birthday", "remove_address"]
)
def test_removing_an_unset_field_is_an_error(contact, method):
    with pytest.raises(ValidationError):
        getattr(contact, method)()


def test_failed_update_keeps_the_old_value(contact):
    contact.add_email("a@b.co")
    contact.add_birthday("15.03.1990")
    with pytest.raises(ValidationError):
        contact.add_email("bad")
    with pytest.raises(ValidationError):
        contact.add_birthday("bad")
    assert contact.email.value == "a@b.co"
    assert contact.birthday.value == "15.03.1990"


def test_str_without_phones():
    assert str(Contact("anna")) == "Contact name: Anna, phones: -"


def test_state_round_trip(contact):
    contact.add_birthday("29.02.2000")
    contact.add_email("a@b.co")
    contact.add_address("Kyiv")
    restored = Contact.__new__(Contact)
    restored.__setstate__(contact.__getstate__())
    assert restored.__getstate__() == contact.__getstate__()
    assert restored.birthday is not None and contact.birthday is not None
    assert restored.birthday.bd_date == contact.birthday.bd_date


@pytest.mark.parametrize(
    "broken",
    [{"phones": ["123"]}, {"birthday": "bad"}, {"email": "bad"}],
    ids=["phone", "birthday", "email"],
)
def test_invalid_state_is_rejected(broken):
    restored = Contact.__new__(Contact)
    with pytest.raises(ValidationError):
        restored.__setstate__({"name": "Anna", **broken})
