import pytest

from bool_parser import parse_bool


def test_lowercase_values_are_supported() -> None:
    assert parse_bool("true") is True
    assert parse_bool("false") is False


def test_mixed_case_values_are_supported() -> None:
    assert parse_bool("True") is True
    assert parse_bool("FALSE") is False


def test_invalid_values_still_raise() -> None:
    with pytest.raises(ValueError):
        parse_bool("yes")
