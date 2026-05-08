from limits import is_within_limit


def test_values_inside_range_are_valid() -> None:
    assert is_within_limit(5, minimum=0, maximum=10) is True


def test_maximum_value_is_allowed() -> None:
    assert is_within_limit(10, minimum=0, maximum=10) is True


def test_values_above_maximum_are_invalid() -> None:
    assert is_within_limit(11, minimum=0, maximum=10) is False
