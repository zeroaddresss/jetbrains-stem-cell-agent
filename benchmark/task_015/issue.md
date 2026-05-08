Title: Remove only a trailing .tmp suffix

The helper should strip a temporary-file suffix only when the filename actually ends with .tmp.
Expected behavior: strip_tmp_suffix("report.tmp.backup") should stay unchanged.
Please keep the current function signature.
