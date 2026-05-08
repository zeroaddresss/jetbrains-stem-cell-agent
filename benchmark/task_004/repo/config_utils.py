def normalize_config_value(raw: str | None) -> str | None:
    if raw is None:
        return None
    return raw.strip()
