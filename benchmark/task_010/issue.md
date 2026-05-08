Title: Boolean parser should accept mixed-case input

The parser is meant to accept common boolean strings regardless of casing.
Expected behavior: parse_bool("True") should return True and parse_bool("FALSE") should return False.
Please keep the existing public API and error behavior for invalid values.
