def average_or_default(values: list[float], default: float = 0.0) -> float:
    return sum(values) / len(values)
