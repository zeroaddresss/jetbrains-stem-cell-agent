from duration import format_duration


def test_sub_hour_duration_is_supported() -> None:
    assert format_duration(45) == "0h 45m"


def test_minutes_roll_over_into_hours() -> None:
    assert format_duration(125) == "2h 5m"
