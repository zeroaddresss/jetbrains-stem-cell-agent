from list_utils import drop_missing


def test_empty_input() -> None:
    assert drop_missing([]) == []


def test_zero_is_preserved() -> None:
    assert drop_missing([0, 1, None]) == [0, 1]
