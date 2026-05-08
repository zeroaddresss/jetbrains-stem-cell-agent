import os


def join_under_base(base: str, child: str) -> str:
    return os.path.join(base, child)
