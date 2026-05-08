from key_value import split_key_value


def test_value_can_contain_colons() -> None:
    assert split_key_value("url: https://example.com:443") == ("url", "https://example.com:443")


def test_only_the_first_separator_is_used() -> None:
    assert split_key_value("time: 10:30:45") == ("time", "10:30:45")
