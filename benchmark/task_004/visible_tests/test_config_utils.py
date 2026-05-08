from config_utils import normalize_config_value


def test_regular_values_are_trimmed() -> None:
    assert normalize_config_value("  hello ") == "hello"


def test_whitespace_only_value_becomes_missing() -> None:
    assert normalize_config_value("   ") is None
