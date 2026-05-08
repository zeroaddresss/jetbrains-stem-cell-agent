Title: Drop None values but keep 0

The helper is supposed to remove missing values, but it also removes zeros.
Expected behavior: drop_missing([0, 1, None]) should return [0, 1].
Only fix the filtering logic.
