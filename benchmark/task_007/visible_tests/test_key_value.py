from key_value import split_key_value


def test_simple_key_value_line() -> None:
    assert split_key_value("host: localhost") == ("host", "localhost")


def test_value_can_contain_colons() -> None:
    assert split_key_value("url: https://example.com:443") == ("url", "https://example.com:443")
