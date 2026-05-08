Title: Values may contain colons

The key/value parser should split on the first colon only, because the value part can contain additional colons.
Expected behavior: split_key_value("url: https://example.com:443") should keep the entire URL in the value.
Please keep the return type and public API unchanged.
