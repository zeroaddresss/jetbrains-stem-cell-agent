from date_formatter import format_iso_date


def test_double_digit_month_is_unchanged() -> None:
    assert format_iso_date(2024, 11, 9) == "2024-11-09"


def test_single_digit_month_is_zero_padded() -> None:
    assert format_iso_date(2024, 1, 9) == "2024-01-09"
