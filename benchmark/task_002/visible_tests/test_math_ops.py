from math_ops import sum_inclusive


def test_single_value_interval() -> None:
    assert sum_inclusive(3, 3) == 3


def test_interval_includes_upper_bound() -> None:
    assert sum_inclusive(2, 4) == 9
