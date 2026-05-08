import pytest

from safe_paths import join_under_base


def test_relative_child_path_is_joined_normally() -> None:
    assert join_under_base("/srv/app", "logs/output.txt") == "/srv/app/logs/output.txt"


def test_absolute_child_path_is_rejected() -> None:
    with pytest.raises(ValueError):
        join_under_base("/srv/app", "/tmp/output.txt")


def test_nested_absolute_like_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        join_under_base("/srv/app", "/var/log/app.log")
