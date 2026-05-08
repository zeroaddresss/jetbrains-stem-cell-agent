from date_formatter import format_iso_date


def test_single_digit_month_is_zero_padded() -> None:
    assert format_iso_date(2024, 1, 9) == "2024-01-09"


def test_single_digit_day_stays_zero_padded_too() -> None:
    assert format_iso_date(2024, 4, 3) == "2024-04-03"
