from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    task_dir: Path
    repo_dir: Path
    issue_path: Path
    visible_tests_dir: Path | None
    hidden_tests_dir: Path
    entry_hints: tuple[str, ...]
    visible_eval: str | None
    time_budget_sec: int
    max_agent_steps: int

    @property
    def issue_text(self) -> str:
        return self.issue_path.read_text(encoding="utf-8")


class Benchmark:
    def __init__(self, root: Path, hidden_root: Path | None = None) -> None:
        self.root = root.resolve()
        self.hidden_root = (hidden_root or root.parent / "private_eval" / "hidden_tests").resolve()
        manifest_path = self.root / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        self.version = manifest.get("version", 1)
        self.task_ids = tuple(manifest.get("tasks", ()))

    def load_task(self, task_id: str) -> TaskSpec:
        task_dir = self.root / task_id
        data = self._load_yaml(task_dir / "task.yaml")
        visible_tests_dir = task_dir / "visible_tests"
        if not visible_tests_dir.exists():
            visible_tests_dir = None
        return TaskSpec(
            task_id=data["id"],
            task_dir=task_dir,
            repo_dir=task_dir / "repo",
            issue_path=task_dir / "issue.md",
            visible_tests_dir=visible_tests_dir,
            hidden_tests_dir=self.hidden_root / data["hidden_eval_id"],
            entry_hints=tuple(data.get("entry_hints", ())),
            visible_eval=data.get("visible_eval"),
            time_budget_sec=int(data.get("time_budget_sec", 180)),
            max_agent_steps=int(data.get("max_agent_steps", 12)),
        )

    def load_split(self, split: str) -> list[TaskSpec]:
        split_path = self.root / "splits" / f"{split}.txt"
        task_ids = [line.strip() for line in split_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return [self.load_task(task_id) for task_id in task_ids]

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
