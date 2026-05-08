Title: Tag accumulator leaks values across calls

The helper should build a fresh list of tags for each call unless the caller passes an existing list explicitly.
Expected behavior: two separate calls without the optional argument should not share state.
Please preserve the public API.
