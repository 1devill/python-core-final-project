"""Corner cases of input and filter parsing."""

import pytest

from personal_assistant.cli.parser import (
    parse_filters,
    parse_input,
    split_address_args,
)
from personal_assistant.exceptions import ValidationError

KEYS = ("name", "text")


@pytest.mark.parametrize(
    "line, expected",
    [
        ("", ("", [])),
        ("    ", ("", [])),
        ("\t\n", ("", [])),
        ("hello", ("hello", [])),
        ("HeLLo", ("hello", [])),
        ("  add   Anna   0123456789  ", ("add", ["Anna", "0123456789"])),
    ],
)
def test_parse_input(line, expected):
    assert parse_input(line) == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        (["name=anna"], {"name": "anna"}),
        (["NAME=anna"], {"name": "anna"}),
        (["text=buy", "milk"], {"text": "buy milk"}),
        (["text=buy", "milk", "name=a"], {"text": "buy milk", "name": "a"}),
        (["text=a=b"], {"text": "a=b"}),
        (["text=x", "y=2"], {"text": "x y=2"}),
        (["name="], {"name": ""}),
        (["name=", "anna"], {"name": "anna"}),
    ],
)
def test_parse_filters(args, expected):
    assert parse_filters(args, KEYS) == expected


def test_no_args_raises_value_error_for_the_usage_hint():
    with pytest.raises(ValueError):
        parse_filters([], KEYS)


@pytest.mark.parametrize(
    "args",
    [["anna"], ["=anna"], ["foo=bar"], ["name=a", "name=b"], ["name=a", "NAME=b"]],
    ids=["no-key", "empty-key", "unknown-key", "repeated", "repeated-case"],
)
def test_bad_filters(args):
    with pytest.raises(ValidationError):
        parse_filters(args, KEYS)


class TestSplitAddressArgs:
    def test_joins_all_words_after_the_name(self):
        assert split_address_args(["anna", "Kyiv", "Main", "St", "5"]) == (
            "anna",
            "Kyiv Main St 5",
        )

    @pytest.mark.parametrize("args", [[], ["anna"]])
    def test_missing_address_raises_value_error(self, args):
        with pytest.raises(ValueError):
            split_address_args(args)
