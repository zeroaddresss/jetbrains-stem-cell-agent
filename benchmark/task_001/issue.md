Title: CSV parser drops the last empty column

When parsing a line that ends with a trailing comma, the parser returns one fewer field than expected.
Expected behavior: "a,b," should parse to ["a", "b", ""].
Please fix the source code without changing the function signature.
