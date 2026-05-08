from stats_utils import average_or_default


def test_empty_input_uses_custom_default() -> None:
    assert average_or_default([], default=2.5) == 2.5


def test_non_empty_input_still_returns_average() -> None:
    assert average_or_default([1.0, 3.0]) == 2.0
