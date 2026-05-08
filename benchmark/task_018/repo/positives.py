def summarize_positives(values) -> tuple[int, list[int]]:
    count = sum(1 for value in values if value > 0)
    positives = [value for value in values if value > 0]
    return count, positives
