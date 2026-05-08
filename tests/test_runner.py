from pathlib import Path

from stem_agent.agent import StemAgent
from stem_agent.backends import HeuristicBackend
from stem_agent.benchmark import Benchmark
from stem_agent.policy import Policy
from stem_agent.runner import TaskRunner


def test_runner_solves_task_with_source_first_policy() -> None:
    benchmark = Benchmark(Path("benchmark"))
    task = benchmark.load_task("task_001")
    agent = StemAgent(HeuristicBackend())
    runner = TaskRunner(agent)
    policy = Policy(inspect_order="source_first", max_files_to_read=1)
    result = runner.run_task(task, policy)
    assert result.solved is True
    assert result.changed_lines > 0
    assert result.observed_files == ("parser_utils.py",)


def test_seed_policy_fails_when_it_only_reads_visible_tests() -> None:
    benchmark = Benchmark(Path("benchmark"))
    task = benchmark.load_task("task_001")
    agent = StemAgent(HeuristicBackend())
    runner = TaskRunner(agent)
    result = runner.run_task(task, Policy.seed())
    assert result.solved is False
    assert result.observed_files == ("visible_tests/test_parser_utils.py",)


def test_run_command_timeout_is_handled_without_exception() -> None:
    outcome = TaskRunner._run_command(
        "python -c \"import time; time.sleep(2)\"",
        cwd=Path("."),
        timeout=1,
    )
    assert outcome.returncode == 124
    assert "timed out" in outcome.text
