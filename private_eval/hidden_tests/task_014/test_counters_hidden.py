from counters import merge_counts


def test_zero_override_is_preserved() -> None:
    assert merge_counts({"errors": 2}, {"errors": 0}) == {"errors": 0}


def test_none_override_falls_back_to_default() -> None:
    assert merge_counts({"errors": 2}, {"errors": None}) == {"errors": 2}


def test_multiple_keys_are_merged_independently() -> None:
    assert merge_counts({"errors": 2, "warnings": 1}, {"errors": 0}) == {"errors": 0, "warnings": 1}
