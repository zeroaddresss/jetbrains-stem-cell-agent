from pathlib import Path

from stem_agent.benchmark import Benchmark


def test_benchmark_loads_manifest_and_splits() -> None:
    benchmark = Benchmark(Path("benchmark"))
    assert benchmark.task_ids == (
        "task_001",
        "task_002",
        "task_003",
        "task_004",
        "task_005",
        "task_006",
        "task_007",
        "task_008",
        "task_009",
        "task_010",
        "task_011",
        "task_012",
        "task_013",
        "task_014",
        "task_015",
        "task_016",
        "task_017",
        "task_018",
    )
    train = benchmark.load_split("train")
    assert [task.task_id for task in train] == [
        "task_001",
        "task_002",
        "task_003",
        "task_004",
        "task_005",
        "task_006",
        "task_007",
        "task_008",
        "task_009",
    ]
    assert train[0].hidden_tests_dir.name == "task_001"
    val = benchmark.load_split("val")
    assert [task.task_id for task in val] == ["task_010", "task_011", "task_012"]
    test = benchmark.load_split("test")
    assert [task.task_id for task in test] == [
        "task_013",
        "task_014",
        "task_015",
        "task_016",
        "task_017",
        "task_018",
    ]


def test_all_manifest_tasks_have_required_files() -> None:
    benchmark = Benchmark(Path("benchmark"))
    for task_id in benchmark.task_ids:
        task = benchmark.load_task(task_id)
        assert task.repo_dir.is_dir()
        assert task.issue_path.is_file()
        assert task.hidden_tests_dir.is_dir()
        assert task.visible_tests_dir is not None
        assert task.visible_tests_dir.is_dir()
