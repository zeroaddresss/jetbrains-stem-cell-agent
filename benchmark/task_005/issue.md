Title: Deduplication should keep the first-seen order

The helper removes duplicates, but it also reorders items.
Expected behavior: unique_names(["beta", "alpha", "beta", "gamma"]) should return ["beta", "alpha", "gamma"].
Do not change the public API.
