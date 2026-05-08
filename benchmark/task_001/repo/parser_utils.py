def parse_csv_line(line: str) -> list[str]:
    """Parse a simple comma-separated row."""
    return line.rstrip(",").split(",")
