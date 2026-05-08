from line_reader import read_lines


def test_text_with_trailing_newline_is_unchanged() -> None:
    assert read_lines("alpha\nbeta\n") == ["alpha", "beta"]


def test_last_line_without_trailing_newline_is_kept() -> None:
    assert read_lines("alpha\nbeta") == ["alpha", "beta"]
