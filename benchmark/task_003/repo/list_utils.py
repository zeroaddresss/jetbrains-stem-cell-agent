def drop_missing(values: list[int | None]) -> list[int]:
    return [value for value in values if value]
