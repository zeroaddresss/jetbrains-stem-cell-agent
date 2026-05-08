from counters import merge_counts


def test_missing_override_uses_default() -> None:
    assert merge_counts({"warnings": 3}, {}) == {"warnings": 3}


def test_zero_override_is_preserved() -> None:
    assert merge_counts({"errors": 2}, {"errors": 0}) == {"errors": 0}
