from parser_utils import parse_csv_line


def test_trailing_comma_keeps_empty_field() -> None:
    assert parse_csv_line("a,b,") == ["a", "b", ""]


def test_single_empty_column() -> None:
    assert parse_csv_line(",") == ["", ""]
