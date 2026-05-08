from config_utils import normalize_config_value


def test_whitespace_only_value_becomes_missing() -> None:
    assert normalize_config_value("   ") is None


def test_tabs_and_newlines_also_count_as_missing() -> None:
    assert normalize_config_value("\t\n  ") is None
