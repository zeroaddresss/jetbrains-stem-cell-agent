def sum_inclusive(start: int, end: int) -> int:
    total = 0
    for value in range(start, end):
        total += value
    return total
