from tags import add_tag


def test_separate_default_calls_do_not_share_state() -> None:
    assert add_tag("alpha") == ["alpha"]
    assert add_tag("beta") == ["beta"]


def test_explicit_list_is_mutated_in_place() -> None:
    existing = ["core"]
    result = add_tag("ops", existing)
    assert result is existing
    assert existing == ["core", "ops"]
