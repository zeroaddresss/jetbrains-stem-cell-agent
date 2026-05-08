Title: Month should be zero-padded in ISO dates

The date formatter is meant to return ISO-like YYYY-MM-DD strings.
Expected behavior: format_iso_date(2024, 1, 9) should return "2024-01-09".
Please keep the current function signature.
