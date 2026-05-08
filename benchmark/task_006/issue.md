Title: Empty averages should use the configured fallback

The helper computes averages correctly for non-empty inputs, but it crashes on empty lists.
Expected behavior: average_or_default([], default=2.5) should return 2.5.
Please preserve the existing function signature.
