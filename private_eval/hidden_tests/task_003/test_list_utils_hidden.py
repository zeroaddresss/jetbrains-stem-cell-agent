from list_utils import drop_missing


def test_zero_is_not_dropped() -> None:
    assert drop_missing([0, None, 2]) == [0, 2]


def test_falsey_but_valid_zero_is_kept() -> None:
    assert drop_missing([0, 0, None]) == [0, 0]
