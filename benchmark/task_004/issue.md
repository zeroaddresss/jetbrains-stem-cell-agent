Title: Whitespace-only config values should count as missing

The config normalizer trims surrounding whitespace, but values that become empty after trimming should be treated as missing.
Expected behavior: normalize_config_value("   ") should return None.
Please keep the current function signature.
