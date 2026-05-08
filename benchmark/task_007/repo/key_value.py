def split_key_value(line: str) -> tuple[str, str]:
    key, value = [part.strip() for part in line.split(":")]
    return key, value
