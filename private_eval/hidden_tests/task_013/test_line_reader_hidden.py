from line_reader import read_lines


def test_last_line_without_trailing_newline_is_kept() -> None:
    assert read_lines("alpha\nbeta") == ["alpha", "beta"]


def test_single_line_without_newline_is_returned() -> None:
    assert read_lines("solo") == ["solo"]


def test_empty_input_is_still_empty() -> None:
    assert read_lines("") == []
