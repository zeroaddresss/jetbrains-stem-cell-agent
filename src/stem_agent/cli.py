from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .agent import StemAgent
from .backends import load_backend
from .benchmark import Benchmark
from .evolution import EvolutionConfig, evolve_policy
from .policy import Policy
from .runner import TaskRunner
from .study import StudyConfig, run_study


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BENCHMARK_ROOT = PROJECT_ROOT / "benchmark"
DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results"


def main() -> None:
    _load_environment()
    parser = argparse.ArgumentParser(description="Minimal evolving stem agent scaffold")
    subparsers = parser.add_subparsers(dest="command", required=True)

    describe = subparsers.add_parser("describe-benchmark")
    describe.add_argument("--benchmark-root", type=Path, default=DEFAULT_BENCHMARK_ROOT)

    run_task = subparsers.add_parser("run-task")
    _add_common_args(run_task)
    run_task.add_argument("--task-id", required=True)

    evaluate = subparsers.add_parser("evaluate")
    _add_common_args(evaluate)
    evaluate.add_argument("--split", default="train", choices=["train", "val", "test"])

    evolve = subparsers.add_parser("evolve")
    _add_common_args(evolve)
    evolve.add_argument("--generations", type=int, default=3)
    evolve.add_argument("--patience", type=int, default=2)

    study = subparsers.add_parser("run-study")
    _add_common_args(study)
    study.add_argument("--generations", type=int, default=3)
    study.add_argument("--patience", type=int, default=2)
    study.add_argument("--train-task-ids", default=None)
    study.add_argument("--val-task-ids", default=None)
    study.add_argument("--test-task-ids", default=None)

    args = parser.parse_args()
    benchmark = Benchmark(args.benchmark_root)
    if args.command == "describe-benchmark":
        payload = {
            "version": benchmark.version,
            "tasks": benchmark.task_ids,
            "splits": {
                split: [task.task_id for task in benchmark.load_split(split)]
                for split in ("train", "val", "test")
            },
        }
        print(json.dumps(payload, indent=2))
        return

    policy = Policy.from_yaml(args.policy_file) if args.policy_file else Policy.seed()
    resolved_model = _resolve_model_name(args.backend, args.model)
    backend = load_backend(args.backend, model=resolved_model)
    runner = TaskRunner(StemAgent(backend), results_dir=args.results_dir)

    if args.command == "run-task":
        task = benchmark.load_task(args.task_id)
        print(json.dumps(asdict(runner.run_task(task, policy)), indent=2))
        return

    if args.command == "evaluate":
        tasks = benchmark.load_split(args.split)
        print(json.dumps(asdict(runner.evaluate_split(args.split, tasks, policy)), indent=2))
        return

    if args.command == "run-study":
        results_dir = args.results_dir or (DEFAULT_RESULTS_ROOT / "study")
        result = run_study(
            benchmark=benchmark,
            runner=runner,
            initial_policy=policy,
            evolution_config=EvolutionConfig(generations=args.generations, patience=args.patience),
            study_config=StudyConfig(
                backend=args.backend,
                model=resolved_model,
                generations=args.generations,
                patience=args.patience,
                base_url=_resolve_effective_base_url(backend),
            ),
            results_dir=results_dir,
            train_tasks=_load_task_override(benchmark, args.train_task_ids),
            validation_tasks=_load_task_override(benchmark, args.val_task_ids),
            test_tasks=_load_task_override(benchmark, args.test_task_ids),
        )
        print(
            json.dumps(
                {
                    "results_dir": str(results_dir),
                    "baseline_test_summary": asdict(result.baseline_evaluations["test"].summary),
                    "evolved_test_summary": asdict(result.evolved_evaluations["test"].summary),
                    "best_policy": result.evolved_policy.to_dict(),
                    "best_policy_id": result.evolved_policy.policy_id,
                },
                indent=2,
            )
        )
        return

    train_tasks = benchmark.load_split("train")
    validation_tasks = benchmark.load_split("val")
    result = evolve_policy(
        runner=runner,
        train_tasks=train_tasks,
        validation_tasks=validation_tasks,
        initial_policy=policy,
        config=EvolutionConfig(generations=args.generations, patience=args.patience),
        results_dir=args.results_dir,
    )
    if args.results_dir:
        result.best_policy.to_yaml(args.results_dir / "best_policy.yaml")
    print(
        json.dumps(
            {
                "best_policy": result.best_policy.to_dict(),
                "best_policy_id": result.best_policy.policy_id,
                "train_summary": asdict(result.train_summary),
                "validation_summary": asdict(result.validation_summary),
                "generations_run": result.generations_run,
            },
            indent=2,
        )
    )


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--benchmark-root", type=Path, default=DEFAULT_BENCHMARK_ROOT)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--policy-file", type=Path, default=None)
    parser.add_argument("--backend", default="heuristic", choices=["heuristic", "openai"])
    parser.add_argument("--model", default=None)


def _load_task_override(benchmark: Benchmark, raw_ids: str | None):
    if not raw_ids:
        return None
    task_ids = [task_id.strip() for task_id in raw_ids.split(",") if task_id.strip()]
    return [benchmark.load_task(task_id) for task_id in task_ids]


def _resolve_base_url() -> str | None:
    return os.getenv("OPENAI_BASE_URL") or os.getenv("OPENROUTER_BASE_URL")


def _resolve_effective_base_url(backend) -> str | None:
    return getattr(backend, "base_url", None) or _resolve_base_url()


def _resolve_model_name(backend_name: str, cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value
    if backend_name != "openai":
        return None
    return os.getenv("OPENAI_MODEL") or os.getenv("OPENROUTER_MODEL") or os.getenv("STEM_AGENT_MODEL")


def _load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    load_dotenv(override=False)


if __name__ == "__main__":
    main()
