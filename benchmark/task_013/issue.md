Title: Last line is skipped when there is no trailing newline

The line reader returns all records when the text ends with a newline, but it drops the last record otherwise.
Expected behavior: read_lines("alpha\nbeta") should return ["alpha", "beta"].
Please fix the source without changing the public API.
