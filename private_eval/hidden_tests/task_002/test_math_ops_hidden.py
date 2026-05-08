from math_ops import sum_inclusive


def test_closed_interval() -> None:
    assert sum_inclusive(2, 4) == 9


def test_single_value_interval() -> None:
    assert sum_inclusive(5, 5) == 5
