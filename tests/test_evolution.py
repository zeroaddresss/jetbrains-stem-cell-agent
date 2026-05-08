from pathlib import Path

from stem_agent.agent import StemAgent
from stem_agent.backends import HeuristicBackend
from stem_agent.benchmark import Benchmark
from stem_agent.evolution import EvolutionConfig, evolve_policy
from stem_agent.policy import Policy
from stem_agent.runner import TaskRunner


def test_evolution_improves_validation_score_on_sample_benchmark() -> None:
    benchmark = Benchmark(Path("benchmark"))
    runner = TaskRunner(StemAgent(HeuristicBackend()))
    result = evolve_policy(
        runner=runner,
        train_tasks=[benchmark.load_task("task_001"), benchmark.load_task("task_002")],
        validation_tasks=[benchmark.load_task("task_003")],
        initial_policy=Policy.seed(),
        config=EvolutionConfig(generations=2, patience=1),
    )
    assert result.validation_summary.tasks_solved == 1
    assert result.best_policy != Policy.seed()
