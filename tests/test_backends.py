from pathlib import Path

import pytest

from stem_agent.agent import StemAgent
from stem_agent.backends import BackendResponseError, OpenAIBackend
from stem_agent.benchmark import Benchmark
from stem_agent.policy import Policy
from stem_agent.runner import TaskRunner


class AlwaysFailBackend:
    def propose_fix(self, **kwargs):
        raise BackendResponseError("json_parse_error", "malformed response")


def test_openai_backend_parse_json_with_multiple_strategies() -> None:
    assert OpenAIBackend._parse_json('{"diagnosis": "ok", "edits": []}') == {"diagnosis": "ok", "edits": []}
    assert OpenAIBackend._parse_json('```json\n{"diagnosis":"ok","edits":[]}\n```') == {
        "diagnosis": "ok",
        "edits": [],
    }
    assert OpenAIBackend._parse_json("noise before {\"diagnosis\":\"ok\",\"edits\":[]} trailing") == {
        "diagnosis": "ok",
        "edits": [],
    }


def test_openai_backend_validate_payload_and_schema_errors() -> None:
    diagnosis, edits = OpenAIBackend._validate_payload({"diagnosis": "ok", "edits": [{"path": "a.py", "new_content": "x"}]})
    assert diagnosis == "ok"
    assert len(edits) == 1
    with pytest.raises(BackendResponseError) as exc_info:
        OpenAIBackend._validate_payload({"diagnosis": "bad", "edits": "not-a-list"})
    assert exc_info.value.error_type == "schema_error"


def test_openai_backend_env_resolution_with_openrouter_fallback(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    assert OpenAIBackend._resolve_api_key() == "or-key"
    assert OpenAIBackend._resolve_base_url() == OpenAIBackend.OPENROUTER_DEFAULT_BASE_URL


def test_runner_continues_when_backend_response_fails() -> None:
    benchmark = Benchmark(Path("benchmark"))
    task = benchmark.load_task("task_001")
    runner = TaskRunner(StemAgent(AlwaysFailBackend()))
    result = runner.run_task(task, Policy.seed())
    assert result.solved is False
    assert result.backend_error_type == "json_parse_error"
    assert "malformed response" in (result.backend_error_message or "")
