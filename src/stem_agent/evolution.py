from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .benchmark import TaskSpec
from .jsonl import append_jsonl
from .policy import Policy
from .runner import EvaluationSummary, TaskRunner


@dataclass(frozen=True)
class EvolutionConfig:
    generations: int = 5
    patience: int = 2


@dataclass(frozen=True)
class EvolutionResult:
    best_policy: Policy
    train_summary: EvaluationSummary
    validation_summary: EvaluationSummary
    generations_run: int


def evolve_policy(
    *,
    runner: TaskRunner,
    train_tasks: list[TaskSpec],
    validation_tasks: list[TaskSpec],
    initial_policy: Policy,
    config: EvolutionConfig,
    results_dir: Path | None = None,
) -> EvolutionResult:
    best_policy = initial_policy
    best_train = runner.evaluate_split("train", train_tasks, best_policy)
    best_validation = runner.evaluate_split("validation", validation_tasks, best_policy)
    stagnant_generations = 0
    generations_run = 0
    _log_generation(results_dir, 0, best_policy, best_train, best_validation)

    for generation in range(1, config.generations + 1):
        generations_run = generation
        candidate_summaries: list[tuple[Policy, EvaluationSummary, EvaluationSummary]] = []
        for candidate in best_policy.neighbors():
            train_summary = runner.evaluate_split("train", train_tasks, candidate)
            validation_summary = runner.evaluate_split("validation", validation_tasks, candidate)
            candidate_summaries.append((candidate, train_summary, validation_summary))

        candidate_summaries.sort(
            key=lambda item: (
                item[2].tasks_solved,
                item[2].mean_score,
                item[1].tasks_solved,
                item[1].mean_score,
                item[0].policy_id,
            ),
            reverse=True,
        )
        candidate, train_summary, validation_summary = candidate_summaries[0]
        _log_generation(results_dir, generation, candidate, train_summary, validation_summary)

        improved = (validation_summary.tasks_solved, validation_summary.mean_score) > (
            best_validation.tasks_solved,
            best_validation.mean_score,
        )
        if improved:
            best_policy = candidate
            best_train = train_summary
            best_validation = validation_summary
            stagnant_generations = 0
        else:
            stagnant_generations += 1
            if stagnant_generations >= config.patience:
                break

    return EvolutionResult(
        best_policy=best_policy,
        train_summary=best_train,
        validation_summary=best_validation,
        generations_run=generations_run,
    )


def _log_generation(
    results_dir: Path | None,
    generation: int,
    policy: Policy,
    train_summary: EvaluationSummary,
    validation_summary: EvaluationSummary,
) -> None:
    if not results_dir:
        return
    append_jsonl(
        results_dir / "evolution.jsonl",
        {
            "generation": generation,
            "policy": policy.to_dict(),
            "policy_id": policy.policy_id,
            "train": asdict(train_summary),
            "validation": asdict(validation_summary),
        },
    )
