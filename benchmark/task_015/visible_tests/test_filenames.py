from filenames import strip_tmp_suffix


def test_trailing_tmp_suffix_is_removed() -> None:
    assert strip_tmp_suffix("report.tmp") == "report"


def test_internal_tmp_substring_is_not_removed() -> None:
    assert strip_tmp_suffix("report.tmp.backup") == "report.tmp.backup"
