from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import unified_diff
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Sequence

from .agent import StemAgent
from .benchmark import TaskSpec
from .jsonl import append_jsonl
from .policy import Policy


@dataclass(frozen=True)
class TaskRunResult:
    task_id: str
    policy_id: str
    solved: bool
    hidden_exit_code: int
    hidden_output: str
    visible_output: str | None
    runtime_sec: float
    changed_lines: int
    attempts: int
    observed_files: tuple[str, ...]
    diagnosis: str
    score: float
    backend_error_type: str | None = None
    backend_error_message: str | None = None


@dataclass(frozen=True)
class EvaluationSummary:
    split: str
    policy_id: str
    tasks_solved: int
    task_count: int
    mean_score: float
    mean_runtime_sec: float
    mean_changed_lines: float


@dataclass(frozen=True)
class DetailedEvaluation:
    split: str
    policy_id: str
    runs: tuple[TaskRunResult, ...]
    summary: EvaluationSummary


class TaskRunner:
    def __init__(self, agent: StemAgent, results_dir: Path | None = None) -> None:
        self.agent = agent
        self.results_dir = results_dir

    def run_task(self, task: TaskSpec, policy: Policy) -> TaskRunResult:
        start = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix=f"{task.task_id}_") as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            shutil.copytree(task.repo_dir, workspace)
            if task.visible_tests_dir:
                shutil.copytree(task.visible_tests_dir, workspace / "visible_tests")

            visible_pre_output = None
            if policy.run_visible_tests_before_patch and task.visible_eval:
                visible_pre_output = self._run_command(task.visible_eval, cwd=workspace, timeout=task.time_budget_sec).text

            agent_run = self.agent.run(
                workspace=workspace,
                task=task,
                policy=policy,
                visible_test_output=visible_pre_output,
            )
            changed_lines = self._apply_edits(workspace, agent_run.proposal.edits)
            visible_post_output = None
            if task.visible_eval:
                visible_post_output = self._run_command(task.visible_eval, cwd=workspace, timeout=task.time_budget_sec)
            hidden_output = self._run_hidden_tests(task=task, workspace=workspace)

        runtime_sec = time.perf_counter() - start
        solved = hidden_output.returncode == 0
        score = self._score_run(solved=solved, changed_lines=changed_lines, runtime_sec=runtime_sec)
        result = TaskRunResult(
            task_id=task.task_id,
            policy_id=policy.policy_id,
            solved=solved,
            hidden_exit_code=hidden_output.returncode,
            hidden_output=hidden_output.text,
            visible_output=visible_post_output.text if visible_post_output else None,
            runtime_sec=runtime_sec,
            changed_lines=changed_lines,
            attempts=agent_run.attempts,
            observed_files=tuple(observed.path for observed in agent_run.observed_files),
            diagnosis=agent_run.diagnosis,
            score=score,
            backend_error_type=agent_run.backend_error_type,
            backend_error_message=agent_run.backend_error_message,
        )
        self._log_result(result)
        return result

    def evaluate_split(self, split: str, tasks: Sequence[TaskSpec], policy: Policy) -> EvaluationSummary:
        return self.evaluate_split_detailed(split, tasks, policy).summary

    def evaluate_split_detailed(self, split: str, tasks: Sequence[TaskSpec], policy: Policy) -> DetailedEvaluation:
        runs = tuple(self.run_task(task, policy) for task in tasks)
        summary = self.summarize_runs(split=split, policy_id=policy.policy_id, runs=runs)
        return DetailedEvaluation(split=split, policy_id=policy.policy_id, runs=runs, summary=summary)

    @staticmethod
    def summarize_runs(split: str, policy_id: str, runs: Sequence[TaskRunResult]) -> EvaluationSummary:
        task_count = len(runs)
        solved = sum(1 for run in runs if run.solved)
        mean_score = sum(run.score for run in runs) / max(task_count, 1)
        mean_runtime = sum(run.runtime_sec for run in runs) / max(task_count, 1)
        mean_changed_lines = sum(run.changed_lines for run in runs) / max(task_count, 1)
        return EvaluationSummary(
            split=split,
            policy_id=policy_id,
            tasks_solved=solved,
            task_count=task_count,
            mean_score=mean_score,
            mean_runtime_sec=mean_runtime,
            mean_changed_lines=mean_changed_lines,
        )

    def _run_hidden_tests(self, *, task: TaskSpec, workspace: Path) -> CompletedProcessView:
        command = f"pytest -q {task.hidden_tests_dir}"
        return self._run_command(command, cwd=workspace, timeout=task.time_budget_sec)

    @staticmethod
    def _run_command(command: str, *, cwd: Path, timeout: int) -> CompletedProcessView:
        args = shlex.split(command)
        if args and args[0] == "pytest":
            args = [sys.executable, "-m", "pytest", *args[1:]]
        try:
            process = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            output = "\n".join(part for part in (process.stdout, process.stderr) if part)
            return CompletedProcessView(returncode=process.returncode, text=output)
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            detail = "\n".join(part for part in (stdout, stderr) if part)
            message = f"Command timed out after {timeout}s: {command}"
            if detail:
                message = f"{message}\n{detail}"
            return CompletedProcessView(returncode=124, text=message)

    @staticmethod
    def _apply_edits(workspace: Path, edits: Sequence[object]) -> int:
        changed_lines = 0
        for edit in edits:
            path = workspace / edit.path
            old_content = path.read_text(encoding="utf-8")
            new_content = edit.new_content
            diff = list(
                unified_diff(
                    old_content.splitlines(),
                    new_content.splitlines(),
                    fromfile=edit.path,
                    tofile=edit.path,
                    lineterm="",
                )
            )
            changed_lines += sum(1 for line in diff if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
            path.write_text(new_content, encoding="utf-8")
        return changed_lines

    @staticmethod
    def _score_run(*, solved: bool, changed_lines: int, runtime_sec: float) -> float:
        return (1.0 if solved else 0.0) - (0.01 * changed_lines) - (0.001 * runtime_sec)

    def _log_result(self, result: TaskRunResult) -> None:
        if not self.results_dir:
            return
        append_jsonl(self.results_dir / "task_runs.jsonl", asdict(result))


@dataclass(frozen=True)
class CompletedProcessView:
    returncode: int
    text: str
