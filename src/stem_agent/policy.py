from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha1
from pathlib import Path
from typing import Any, ClassVar

import yaml


@dataclass(frozen=True)
class Policy:
    prompt_style: str = "concise_debug"
    inspect_order: str = "tests_first"
    max_files_to_read: int = 1
    max_total_lines: int = 300
    max_edit_attempts: int = 1
    patch_size_soft_limit: int = 25
    temperature: float = 0.0
    run_visible_tests_before_patch: bool = False

    SEARCH_SPACE: ClassVar[dict[str, tuple[Any, ...]]] = {
        "prompt_style": ("concise_debug", "surgical_bugfix"),
        "inspect_order": ("tests_first", "source_first"),
        "max_files_to_read": (1, 2, 3, 4),
        "max_total_lines": (200, 300, 600),
        "max_edit_attempts": (1, 2),
        "patch_size_soft_limit": (20, 25, 40),
        "temperature": (0.0, 0.2),
        "run_visible_tests_before_patch": (False, True),
    }

    @property
    def policy_id(self) -> str:
        digest = sha1(repr(self.to_dict()).encode("utf-8")).hexdigest()[:10]
        return f"policy_{digest}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Policy":
        return cls(**data)

    @classmethod
    def seed(cls) -> "Policy":
        return cls()

    @classmethod
    def from_yaml(cls, path: Path) -> "Policy":
        with path.open("r", encoding="utf-8") as handle:
            return cls.from_dict(yaml.safe_load(handle) or {})

    def to_yaml(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(self.to_dict(), handle, sort_keys=False)

    def neighbors(self) -> list["Policy"]:
        variants: list[Policy] = []
        current = self.to_dict()
        for field_name, values in self.SEARCH_SPACE.items():
            for value in values:
                if current[field_name] == value:
                    continue
                mutated = dict(current)
                mutated[field_name] = value
                variants.append(Policy.from_dict(mutated))
        variants.sort(key=lambda item: item.policy_id)
        return variants
