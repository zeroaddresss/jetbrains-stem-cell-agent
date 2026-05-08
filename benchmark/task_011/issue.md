Title: Maximum allowed value should be inclusive

The validator is supposed to accept values in the closed interval [minimum, maximum].
Expected behavior: is_within_limit(10, minimum=0, maximum=10) should return True.
Please preserve the current function signature.
