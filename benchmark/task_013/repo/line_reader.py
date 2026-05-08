def read_lines(text: str) -> list[str]:
    lines: list[str] = []
    current: list[str] = []
    for char in text:
        if char == "\n":
            lines.append("".join(current))
            current = []
        else:
            current.append(char)
    return lines
