from stats_utils import average_or_default


def test_average_of_values_is_unchanged() -> None:
    assert average_or_default([2.0, 4.0, 6.0]) == 4.0


def test_empty_input_uses_default() -> None:
    assert average_or_default([], default=1.5) == 1.5
