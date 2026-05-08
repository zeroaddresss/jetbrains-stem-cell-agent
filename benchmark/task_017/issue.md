Title: Child path must stay relative to the base directory

The helper is intended to join a trusted base path with a relative child path.
Expected behavior: passing an absolute child path should raise ValueError instead of silently ignoring the base.
Please preserve the current function signature.
