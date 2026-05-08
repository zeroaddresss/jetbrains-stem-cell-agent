def merge_counts(defaults: dict[str, int], overrides: dict[str, int | None]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for key, default in defaults.items():
        merged[key] = overrides.get(key) or default
    return merged
