from tags import add_tag


def test_explicit_list_is_still_supported() -> None:
    existing = ["core"]
    assert add_tag("ui", existing) == ["core", "ui"]


def test_separate_default_calls_do_not_share_state() -> None:
    first = add_tag("alpha")
    second = add_tag("beta")
    assert first == ["alpha"]
    assert second == ["beta"]
