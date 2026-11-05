"""Contact command handlers and the CONTACT_COMMANDS dict."""

from personal_assistant.models import Contact, ContactBook

from . import ui

from .decorators import handle_cmd_error
from .command import Command, Handler
from .parser import parse_filters

SEARCH_KEYS = ("name", "phone", "email", "address")


def normalize_name(name: str) -> str:
    return name.capitalize()


@handle_cmd_error(Command.ADD)
def add_contact(args: list[str], book: ContactBook) -> str:
    name, phone, *_ = args
    name = normalize_name(name)
    if name not in book:
        contact = Contact(name)
        contact.add_phone(phone)
        book.add_contact(contact)
        return ui.success(f"Contact '{ui.highlight(name)}' added.")
    book.find(name).add_phone(phone)
    return ui.success(f"Phone added to '{ui.highlight(name)}'.")


@handle_cmd_error(Command.CHANGE_PHONE)
def update_contact_phone(args: list[str], book: ContactBook) -> str:
    name, old_phone, new_phone = args
    name = normalize_name(name)
    contact = book.find(name)
    contact.edit_phone(old_phone, new_phone)
    return ui.success(f"Phone changed for '{ui.highlight(name)}'.")


@handle_cmd_error(Command.REMOVE_CONTACT)
def remove_contact(args: list[str], book: ContactBook) -> str:
    (name,) = args
    name = normalize_name(name)
    book.delete(name)
    return ui.success(f"Contact '{ui.highlight(name)}' removed.")


@handle_cmd_error(Command.REMOVE_PHONE)
def remove_phone(args: list[str], book: ContactBook) -> str:
    name, phone = args
    name = normalize_name(name)
    contact = book.find(name)
    contact.remove_phone(phone)
    return ui.success(f"Phone removed from '{ui.highlight(name)}'.")


@handle_cmd_error(Command.SHOW_PHONE)
def get_phones(args: list[str], book: ContactBook) -> str:
    (name,) = args
    name = normalize_name(name)
    contact = book.find(name)
    if not contact.phones:
        return ui.info(f"Contact '{name}' has no phones.")
    return ui.field("Phones", ", ".join(str(phone) for phone in contact.phones))


def show_all(args: list[str], book: ContactBook) -> str:
    return ui.contact_list(book.values())


@handle_cmd_error(Command.ADD_BIRTHDAY)
def add_birthday(args: list[str], book: ContactBook) -> str:
    name, birth_date = args
    name = normalize_name(name)
    contact = book.find(name)
    contact.add_birthday(birth_date)
    return ui.success(f"Birthday added for '{ui.highlight(name)}'.")


@handle_cmd_error(Command.ADD_EMAIL)
def add_email(args: list[str], book: ContactBook) -> str:
    name, email = args
    name = normalize_name(name)
    contact = book.find(name)
    contact.add_email(email)
    return ui.success(f"Email added for '{ui.highlight(name)}'.")


@handle_cmd_error(Command.ADD_ADDRESS)
def add_address(args: list[str], book: ContactBook) -> str:
    name, *address_parts = args
    if not address_parts:
        raise ValueError("Address is required")
    address = " ".join(address_parts)
    name = normalize_name(name)
    contact = book.find(name)
    contact.add_address(address)
    return ui.success(f"Address added for '{ui.highlight(name)}'.")


@handle_cmd_error(Command.SHOW_BIRTHDAY)
def show_birthday(args: list[str], book: ContactBook) -> str:
    (name,) = args
    name = normalize_name(name)
    contact = book.find(name)
    if contact.birthday is None:
        return ui.info(f"Contact '{name}' has no birthday set.")
    return ui.field(f"{name}'s birthday", contact.birthday)


@handle_cmd_error(Command.SHOW_EMAIL)
def show_email(args: list[str], book: ContactBook) -> str:
    (name,) = args
    name = normalize_name(name)
    contact = book.find(name)
    if contact.email is None:
        return ui.info(f"Contact '{name}' has no email set.")
    return ui.field(f"{name}'s email", contact.email)


@handle_cmd_error(Command.SHOW_ADDRESS)
def show_address(args: list[str], book: ContactBook) -> str:
    (name,) = args
    name = normalize_name(name)
    contact = book.find(name)
    if contact.address is None:
        return ui.info(f"Contact '{name}' has no address set.")
    return ui.field(f"{name}'s address", contact.address)


@handle_cmd_error(Command.REMOVE_EMAIL)
def remove_email(args: list[str], book: ContactBook) -> str:
    (name,) = args
    name = normalize_name(name)
    contact = book.find(name)
    contact.remove_email()
    return ui.success(f"{ui.highlight(name)}'s email was removed.")


@handle_cmd_error(Command.REMOVE_BIRTHDAY)
def remove_birthday(args: list[str], book: ContactBook) -> str:
    (name,) = args
    name = normalize_name(name)
    contact = book.find(name)
    contact.remove_birthday()
    return ui.success(f"{ui.highlight(name)}'s birthday was removed.")


@handle_cmd_error(Command.REMOVE_ADDRESS)
def remove_address(args: list[str], book: ContactBook) -> str:
    (name,) = args
    name = normalize_name(name)
    contact = book.find(name)
    contact.remove_address()
    return ui.success(f"{ui.highlight(name)}'s address was removed.")


@handle_cmd_error(Command.SHOW_UPCOMING_BIRTHDAYS)
def get_upcoming_birthdays(args: list[str], book: ContactBook) -> str:
    (days,) = args
    days_interval = int(days)
    return ui.birthday_list(book.find_upcoming_birthdays(days_interval))


@handle_cmd_error(Command.FIND_CONTACTS)
def find_contacts(args: list[str], book: ContactBook) -> str:
    found = book.search_contacts(**parse_filters(args, SEARCH_KEYS))
    if not found:
        return ui.info("No contacts found.")
    return ui.contact_list(found, title="Found contacts")


CONTACT_COMMANDS: dict[Command, Handler[ContactBook]] = {
    Command.ADD: add_contact,
    Command.CHANGE_PHONE: update_contact_phone,
    Command.SHOW_PHONE: get_phones,
    Command.ALL: show_all,
    Command.ADD_BIRTHDAY: add_birthday,
    Command.ADD_EMAIL: add_email,
    Command.ADD_ADDRESS: add_address,
    Command.SHOW_BIRTHDAY: show_birthday,
    Command.SHOW_EMAIL: show_email,
    Command.SHOW_ADDRESS: show_address,
    Command.REMOVE_CONTACT: remove_contact,
    Command.REMOVE_ADDRESS: remove_address,
    Command.REMOVE_BIRTHDAY: remove_birthday,
    Command.REMOVE_EMAIL: remove_email,
    Command.REMOVE_PHONE: remove_phone,
    Command.SHOW_UPCOMING_BIRTHDAYS: get_upcoming_birthdays,
    Command.FIND_CONTACTS: find_contacts,
}
