import pytest

from bool_parser import parse_bool


def test_mixed_case_values_are_supported() -> None:
    assert parse_bool("True") is True
    assert parse_bool("FALSE") is False


def test_title_case_false_is_supported() -> None:
    assert parse_bool("False") is False


def test_invalid_values_still_raise() -> None:
    with pytest.raises(ValueError):
        parse_bool("1")
