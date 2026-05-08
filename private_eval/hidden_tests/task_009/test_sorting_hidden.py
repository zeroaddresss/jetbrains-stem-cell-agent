from sorting import sort_numbers


def test_default_sort_order_is_ascending() -> None:
    assert sort_numbers([3, 1, 2]) == [1, 2, 3]


def test_explicit_descending_order_still_works() -> None:
    assert sort_numbers([3, 1, 2], reverse=True) == [3, 2, 1]
