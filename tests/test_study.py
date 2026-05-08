from pathlib import Path
import json

from stem_agent.agent import StemAgent
from stem_agent.backends import HeuristicBackend
from stem_agent.benchmark import Benchmark
from stem_agent.evolution import EvolutionConfig
from stem_agent.policy import Policy
from stem_agent.runner import TaskRunner
from stem_agent.study import StudyConfig, run_study


def test_run_study_writes_summary_artifacts(tmp_path) -> None:
    benchmark = Benchmark(Path("benchmark"))
    runner = TaskRunner(StemAgent(HeuristicBackend()))
    result = run_study(
        benchmark=benchmark,
        runner=runner,
        initial_policy=Policy.seed(),
        evolution_config=EvolutionConfig(generations=1, patience=1),
        study_config=StudyConfig(backend="heuristic", model=None, generations=1, patience=1),
        results_dir=tmp_path,
        train_tasks=[benchmark.load_task("task_001"), benchmark.load_task("task_002")],
        validation_tasks=[benchmark.load_task("task_003")],
        test_tasks=[benchmark.load_task("task_001"), benchmark.load_task("task_003")],
    )
    assert result.evolved_evaluations["test"].summary.task_count == 2
    summary = json.loads((tmp_path / "study_summary.json").read_text(encoding="utf-8"))
    assert summary["headline_improvement"]["split"] == "test"
    assert "error_counts" in summary
    assert summary["study_config"]["backend"] == "heuristic"
    assert (tmp_path / "split_summaries.csv").is_file()
    assert (tmp_path / "task_runs.csv").is_file()
    report_text = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "| Split | Condition | Solved |" in report_text
    assert (tmp_path / "best_policy.yaml").is_file()
