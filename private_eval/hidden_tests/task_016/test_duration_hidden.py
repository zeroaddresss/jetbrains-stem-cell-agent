from duration import format_duration


def test_minutes_roll_over_into_hours() -> None:
    assert format_duration(125) == "2h 5m"


def test_exact_hour_has_zero_remaining_minutes() -> None:
    assert format_duration(120) == "2h 0m"


def test_sub_hour_duration_is_unchanged() -> None:
    assert format_duration(30) == "0h 30m"
