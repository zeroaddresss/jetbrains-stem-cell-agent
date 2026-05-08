from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Sequence

from .backends import BackendResponseError, ModelBackend, ObservedFile, ProposedFix
from .benchmark import TaskSpec
from .policy import Policy


TOKEN_RE = re.compile(r"[a-z0-9_]+")


@dataclass(frozen=True)
class AgentRun:
    diagnosis: str
    proposal: ProposedFix
    observed_files: tuple[ObservedFile, ...]
    attempts: int
    prompt: str
    backend_error_type: str | None = None
    backend_error_message: str | None = None


class StemAgent:
    def __init__(self, backend: ModelBackend) -> None:
        self.backend = backend

    def run(
        self,
        *,
        workspace: Path,
        task: TaskSpec,
        policy: Policy,
        visible_test_output: str | None = None,
    ) -> AgentRun:
        candidates = self._rank_candidates(workspace=workspace, task=task, policy=policy)
        last_prompt = ""
        last_observed: tuple[ObservedFile, ...] = ()
        last_proposal = ProposedFix(diagnosis="No patch proposed.", edits=(), raw_response="")
        last_backend_error_type: str | None = None
        last_backend_error_message: str | None = None
        for attempt_index in range(policy.max_edit_attempts):
            observed = self._observe_candidates(
                workspace=workspace,
                candidates=candidates,
                max_files=min(len(candidates), policy.max_files_to_read + attempt_index),
                max_total_lines=policy.max_total_lines,
            )
            prompt = self._build_prompt(
                task=task,
                policy=policy,
                observed_files=observed,
                visible_test_output=visible_test_output,
                attempt_index=attempt_index,
            )
            try:
                proposal = self.backend.propose_fix(
                    prompt=prompt,
                    observed_files=observed,
                    issue=task.issue_text,
                    policy=policy,
                    workspace=workspace,
                    visible_test_output=visible_test_output,
                )
                last_backend_error_type = None
                last_backend_error_message = None
            except BackendResponseError as exc:
                proposal = ProposedFix(
                    diagnosis=f"Backend response error ({exc.error_type}): {exc.message}",
                    edits=(),
                    raw_response="",
                )
                last_backend_error_type = exc.error_type
                last_backend_error_message = exc.message
            except Exception as exc:
                proposal = ProposedFix(
                    diagnosis=f"Backend error: {exc}",
                    edits=(),
                    raw_response="",
                )
                last_backend_error_type = "backend_error"
                last_backend_error_message = str(exc)
            valid_edits = tuple(edit for edit in proposal.edits if self._allow_edit(edit.path, observed))
            proposal = ProposedFix(diagnosis=proposal.diagnosis, edits=valid_edits, raw_response=proposal.raw_response)
            last_prompt = prompt
            last_observed = observed
            last_proposal = proposal
            if proposal.edits:
                return AgentRun(
                    diagnosis=proposal.diagnosis,
                    proposal=proposal,
                    observed_files=observed,
                    attempts=attempt_index + 1,
                    prompt=prompt,
                    backend_error_type=last_backend_error_type,
                    backend_error_message=last_backend_error_message,
                )
        return AgentRun(
            diagnosis=last_proposal.diagnosis,
            proposal=last_proposal,
            observed_files=last_observed,
            attempts=policy.max_edit_attempts,
            prompt=last_prompt,
            backend_error_type=last_backend_error_type,
            backend_error_message=last_backend_error_message,
        )

    def _rank_candidates(self, *, workspace: Path, task: TaskSpec, policy: Policy) -> list[Path]:
        files = [path for path in workspace.rglob("*.py") if path.is_file()]
        issue_tokens = set(TOKEN_RE.findall(task.issue_text.lower()))
        hint_tokens = {token for hint in task.entry_hints for token in TOKEN_RE.findall(hint.lower())}

        def score(path: Path) -> tuple[int, int, str]:
            rel = path.relative_to(workspace).as_posix()
            path_tokens = set(TOKEN_RE.findall(rel.lower()))
            overlap = len(issue_tokens & path_tokens)
            hint_overlap = len(hint_tokens & path_tokens)
            is_test = 1 if rel.startswith("visible_tests/") else 0
            if policy.inspect_order == "tests_first":
                priority = -is_test
            else:
                priority = is_test
            return (priority, -(overlap + hint_overlap * 2), rel)

        return sorted(files, key=score)

    def _observe_candidates(
        self,
        *,
        workspace: Path,
        candidates: Sequence[Path],
        max_files: int,
        max_total_lines: int,
    ) -> tuple[ObservedFile, ...]:
        observed: list[ObservedFile] = []
        total_lines = 0
        for path in candidates:
            rel = path.relative_to(workspace).as_posix()
            content = path.read_text(encoding="utf-8")
            line_count = max(1, content.count("\n") + 1)
            if observed and total_lines + line_count > max_total_lines:
                continue
            observed.append(
                ObservedFile(
                    path=rel,
                    content=content,
                    is_test=rel.startswith("visible_tests/"),
                )
            )
            total_lines += line_count
            if len(observed) >= max_files:
                break
        return tuple(observed)

    def _build_prompt(
        self,
        *,
        task: TaskSpec,
        policy: Policy,
        observed_files: Sequence[ObservedFile],
        visible_test_output: str | None,
        attempt_index: int,
    ) -> str:
        style_line = {
            "concise_debug": "Diagnose the bug briefly and make the smallest source edit that fixes it.",
            "surgical_bugfix": "Prefer a one-line or two-line fix. Do not refactor or touch tests.",
        }[policy.prompt_style]
        sections = [
            style_line,
            f"Attempt: {attempt_index + 1}",
            f"Patch soft limit: {policy.patch_size_soft_limit} changed lines.",
            "Issue:",
            task.issue_text.strip(),
        ]
        if visible_test_output:
            sections.extend(["Visible test output:", visible_test_output.strip()])
        sections.append("Observed files:")
        for observed in observed_files:
            sections.append(f"FILE: {observed.path}")
            sections.append(observed.content.rstrip())
        sections.append(
            "Return JSON only with the shape: "
            '{"diagnosis": "...", "edits": [{"path": "relative/path.py", "new_content": "full file text"}]}'
        )
        return "\n\n".join(sections)

    @staticmethod
    def _allow_edit(path: str, observed_files: Iterable[ObservedFile]) -> bool:
        allowed = {observed.path for observed in observed_files if not observed.is_test}
        return path in allowed and not path.startswith("visible_tests/")
