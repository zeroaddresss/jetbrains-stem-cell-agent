from limits import is_within_limit


def test_maximum_value_is_allowed() -> None:
    assert is_within_limit(10, minimum=0, maximum=10) is True


def test_minimum_value_is_still_allowed() -> None:
    assert is_within_limit(0, minimum=0, maximum=10) is True


def test_out_of_range_values_are_rejected() -> None:
    assert is_within_limit(-1, minimum=0, maximum=10) is False
    assert is_within_limit(12, minimum=0, maximum=10) is False
