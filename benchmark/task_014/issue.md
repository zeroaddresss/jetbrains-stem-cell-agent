Title: Explicit zero overrides should be preserved

When merging override counts onto defaults, a count of zero is valid and should not fall back to the default value.
Expected behavior: merge_counts({"errors": 2}, {"errors": 0}) should keep 0.
Keep the current public API.
