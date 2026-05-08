from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Sequence

from .benchmark import Benchmark, TaskSpec
from .evolution import EvolutionConfig, EvolutionResult, evolve_policy
from .policy import Policy
from .runner import DetailedEvaluation, EvaluationSummary, TaskRunResult, TaskRunner


@dataclass(frozen=True)
class StudyConfig:
    backend: str
    model: str | None
    generations: int
    patience: int
    base_url: str | None = None


@dataclass(frozen=True)
class StudyResult:
    baseline_policy: Policy
    evolved_policy: Policy
    evolution_result: EvolutionResult
    baseline_evaluations: dict[str, DetailedEvaluation]
    evolved_evaluations: dict[str, DetailedEvaluation]


def run_study(
    *,
    benchmark: Benchmark,
    runner: TaskRunner,
    initial_policy: Policy,
    evolution_config: EvolutionConfig,
    study_config: StudyConfig,
    results_dir: Path,
    train_tasks: Sequence[TaskSpec] | None = None,
    validation_tasks: Sequence[TaskSpec] | None = None,
    test_tasks: Sequence[TaskSpec] | None = None,
) -> StudyResult:
    results_dir.mkdir(parents=True, exist_ok=True)
    train_tasks = list(train_tasks or benchmark.load_split("train"))
    validation_tasks = list(validation_tasks or benchmark.load_split("val"))
    test_tasks = list(test_tasks or benchmark.load_split("test"))

    baseline_evaluations = {
        "train": runner.evaluate_split_detailed("train", train_tasks, initial_policy),
        "val": runner.evaluate_split_detailed("val", validation_tasks, initial_policy),
        "test": runner.evaluate_split_detailed("test", test_tasks, initial_policy),
    }

    evolution_result = evolve_policy(
        runner=runner,
        train_tasks=train_tasks,
        validation_tasks=validation_tasks,
        initial_policy=initial_policy,
        config=evolution_config,
        results_dir=results_dir,
    )

    evolved_policy = evolution_result.best_policy
    evolved_evaluations = {
        "train": runner.evaluate_split_detailed("train", train_tasks, evolved_policy),
        "val": runner.evaluate_split_detailed("val", validation_tasks, evolved_policy),
        "test": runner.evaluate_split_detailed("test", test_tasks, evolved_policy),
    }

    initial_policy.to_yaml(results_dir / "baseline_policy.yaml")
    evolved_policy.to_yaml(results_dir / "best_policy.yaml")
    result = StudyResult(
        baseline_policy=initial_policy,
        evolved_policy=evolved_policy,
        evolution_result=evolution_result,
        baseline_evaluations=baseline_evaluations,
        evolved_evaluations=evolved_evaluations,
    )
    _write_study_artifacts(
        benchmark=benchmark,
        result=result,
        study_config=study_config,
        results_dir=results_dir,
        train_tasks=train_tasks,
        validation_tasks=validation_tasks,
        test_tasks=test_tasks,
    )
    return result


def _write_study_artifacts(
    *,
    benchmark: Benchmark,
    result: StudyResult,
    study_config: StudyConfig,
    results_dir: Path,
    train_tasks: Sequence[TaskSpec],
    validation_tasks: Sequence[TaskSpec],
    test_tasks: Sequence[TaskSpec],
) -> None:
    summary_payload = {
        "benchmark_version": benchmark.version,
        "study_config": asdict(study_config),
        "splits": {
            "train": [task.task_id for task in train_tasks],
            "val": [task.task_id for task in validation_tasks],
            "test": [task.task_id for task in test_tasks],
        },
        "baseline_policy": result.baseline_policy.to_dict(),
        "evolved_policy": result.evolved_policy.to_dict(),
        "evolution": {
            "generations_run": result.evolution_result.generations_run,
            "train_summary": asdict(result.evolution_result.train_summary),
            "validation_summary": asdict(result.evolution_result.validation_summary),
        },
        "baseline_summaries": {
            split: _summary_payload(evaluation.summary)
            for split, evaluation in result.baseline_evaluations.items()
        },
        "evolved_summaries": {
            split: _summary_payload(evaluation.summary)
            for split, evaluation in result.evolved_evaluations.items()
        },
        "headline_improvement": {
            "split": "test",
            "baseline_tasks_solved": result.baseline_evaluations["test"].summary.tasks_solved,
            "evolved_tasks_solved": result.evolved_evaluations["test"].summary.tasks_solved,
            "delta_tasks_solved": result.evolved_evaluations["test"].summary.tasks_solved
            - result.baseline_evaluations["test"].summary.tasks_solved,
        },
        "error_counts": {
            "baseline": {
                split: _count_backend_errors(evaluation.runs)
                for split, evaluation in result.baseline_evaluations.items()
            },
            "evolved": {
                split: _count_backend_errors(evaluation.runs)
                for split, evaluation in result.evolved_evaluations.items()
            },
        },
    }
    (results_dir / "study_summary.json").write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    _write_summary_csv(results_dir / "split_summaries.csv", result)
    _write_runs_csv(results_dir / "task_runs.csv", result)
    (results_dir / "report.md").write_text(_build_markdown_report(result, study_config), encoding="utf-8")


def _summary_payload(summary: EvaluationSummary) -> dict[str, object]:
    payload = asdict(summary)
    payload["success_rate"] = summary.tasks_solved / max(summary.task_count, 1)
    return payload


def _write_summary_csv(path: Path, result: StudyResult) -> None:
    fieldnames = [
        "condition",
        "split",
        "policy_id",
        "tasks_solved",
        "task_count",
        "success_rate",
        "mean_score",
        "mean_runtime_sec",
        "mean_changed_lines",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for condition, evaluations in (
            ("baseline", result.baseline_evaluations),
            ("evolved", result.evolved_evaluations),
        ):
            for split, evaluation in evaluations.items():
                summary = evaluation.summary
                writer.writerow(
                    {
                        "condition": condition,
                        "split": split,
                        "policy_id": summary.policy_id,
                        "tasks_solved": summary.tasks_solved,
                        "task_count": summary.task_count,
                        "success_rate": f"{summary.tasks_solved / max(summary.task_count, 1):.4f}",
                        "mean_score": f"{summary.mean_score:.6f}",
                        "mean_runtime_sec": f"{summary.mean_runtime_sec:.6f}",
                        "mean_changed_lines": f"{summary.mean_changed_lines:.6f}",
                    }
                )


def _write_runs_csv(path: Path, result: StudyResult) -> None:
    fieldnames = [
        "condition",
        "split",
        "task_id",
        "policy_id",
        "solved",
        "hidden_exit_code",
        "runtime_sec",
        "changed_lines",
        "attempts",
        "observed_files",
        "diagnosis",
        "score",
        "backend_error_type",
        "backend_error_message",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for condition, evaluations in (
            ("baseline", result.baseline_evaluations),
            ("evolved", result.evolved_evaluations),
        ):
            for split, evaluation in evaluations.items():
                for run in evaluation.runs:
                    writer.writerow(
                        {
                            "condition": condition,
                            "split": split,
                            "task_id": run.task_id,
                            "policy_id": run.policy_id,
                            "solved": int(run.solved),
                            "hidden_exit_code": run.hidden_exit_code,
                            "runtime_sec": f"{run.runtime_sec:.6f}",
                            "changed_lines": run.changed_lines,
                            "attempts": run.attempts,
                            "observed_files": "|".join(run.observed_files),
                            "diagnosis": run.diagnosis,
                            "score": f"{run.score:.6f}",
                            "backend_error_type": run.backend_error_type or "",
                            "backend_error_message": run.backend_error_message or "",
                        }
                    )


def _count_backend_errors(runs: Sequence[TaskRunResult]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for run in runs:
        if not run.backend_error_type:
            continue
        counts[run.backend_error_type] = counts.get(run.backend_error_type, 0) + 1
    return counts


def _build_markdown_report(result: StudyResult, study_config: StudyConfig) -> str:
    lines = [
        "# Study Report",
        "",
        "## Configuration",
        "",
        f"- Backend: `{study_config.backend}`",
        f"- Model: `{study_config.model or 'n/a'}`",
        f"- Base URL: `{study_config.base_url or 'default'}`",
        f"- Generations: `{study_config.generations}`",
        f"- Patience: `{study_config.patience}`",
        "",
        "## Summary Table",
        "",
        "| Split | Condition | Solved | Success Rate | Mean Score | Mean Runtime (s) | Mean Changed Lines |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split in ("train", "val", "test"):
        for condition, evaluations in (
            ("baseline", result.baseline_evaluations),
            ("evolved", result.evolved_evaluations),
        ):
            summary = evaluations[split].summary
            lines.append(
                "| {split} | {condition} | {solved}/{count} | {rate:.1%} | {score:.3f} | {runtime:.3f} | {changed:.2f} |".format(
                    split=split,
                    condition=condition,
                    solved=summary.tasks_solved,
                    count=summary.task_count,
                    rate=summary.tasks_solved / max(summary.task_count, 1),
                    score=summary.mean_score,
                    runtime=summary.mean_runtime_sec,
                    changed=summary.mean_changed_lines,
                )
            )
    baseline_test = result.baseline_evaluations["test"].summary
    evolved_test = result.evolved_evaluations["test"].summary
    lines.extend(
        [
            "",
            "## Headline",
            "",
            "- Test solved: `{baseline}/{count}` baseline vs `{evolved}/{count}` evolved (`delta={delta:+d}`).".format(
                baseline=baseline_test.tasks_solved,
                evolved=evolved_test.tasks_solved,
                count=baseline_test.task_count,
                delta=evolved_test.tasks_solved - baseline_test.tasks_solved,
            ),
            "",
            "## Best Policy",
            "",
            "```yaml",
            *[f"{key}: {value}" for key, value in result.evolved_policy.to_dict().items()],
            "```",
            "",
            "## Backend Errors",
            "",
            "| Split | Condition | Error Type | Count |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for split in ("train", "val", "test"):
        for condition, evaluations in (
            ("baseline", result.baseline_evaluations),
            ("evolved", result.evolved_evaluations),
        ):
            counts = _count_backend_errors(evaluations[split].runs)
            if not counts:
                lines.append(f"| {split} | {condition} | none | 0 |")
                continue
            for error_type, count in sorted(counts.items()):
                lines.append(f"| {split} | {condition} | {error_type} | {count} |")
    return "\n".join(lines) + "\n"
