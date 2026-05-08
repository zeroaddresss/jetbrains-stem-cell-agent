from names import unique_names


def test_duplicate_values_keep_first_seen_order() -> None:
    assert unique_names(["beta", "alpha", "beta", "gamma"]) == ["beta", "alpha", "gamma"]


def test_order_is_based_on_first_occurrence_not_sorting() -> None:
    assert unique_names(["zeta", "beta", "zeta", "alpha"]) == ["zeta", "beta", "alpha"]
