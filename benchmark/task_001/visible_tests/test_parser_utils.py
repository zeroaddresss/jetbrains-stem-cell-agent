from parser_utils import parse_csv_line


def test_regular_line_is_unchanged() -> None:
    assert parse_csv_line("a,b,c") == ["a", "b", "c"]


def test_trailing_comma_keeps_empty_field() -> None:
    assert parse_csv_line("a,b,") == ["a", "b", ""]
