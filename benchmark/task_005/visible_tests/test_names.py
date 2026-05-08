from names import unique_names


def test_unique_values_stay_unique() -> None:
    assert unique_names(["alpha", "beta"]) == ["alpha", "beta"]


def test_duplicate_values_keep_first_seen_order() -> None:
    assert unique_names(["beta", "alpha", "beta", "gamma"]) == ["beta", "alpha", "gamma"]
