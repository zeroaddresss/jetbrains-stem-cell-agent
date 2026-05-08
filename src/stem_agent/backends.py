from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

from .policy import Policy


@dataclass(frozen=True)
class ObservedFile:
    path: str
    content: str
    is_test: bool


@dataclass(frozen=True)
class FileEdit:
    path: str
    new_content: str


@dataclass(frozen=True)
class ProposedFix:
    diagnosis: str
    edits: tuple[FileEdit, ...]
    raw_response: str


class BackendResponseError(RuntimeError):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class ModelBackend(Protocol):
    def propose_fix(
        self,
        *,
        prompt: str,
        observed_files: Sequence[ObservedFile],
        issue: str,
        policy: Policy,
        workspace: Path,
        visible_test_output: str | None,
    ) -> ProposedFix:
        ...


class HeuristicBackend:
    """Deterministic backend for smoke tests and local development."""

    def propose_fix(
        self,
        *,
        prompt: str,
        observed_files: Sequence[ObservedFile],
        issue: str,
        policy: Policy,
        workspace: Path,
        visible_test_output: str | None,
    ) -> ProposedFix:
        lower_issue = issue.lower()
        edits: list[FileEdit] = []
        diagnosis = "No fix identified from the current context."
        for observed in observed_files:
            if observed.is_test:
                continue
            content = observed.content
            if "trailing comma" in lower_issue or "empty column" in lower_issue:
                needle = 'return line.rstrip(",").split(",")'
                if needle in content:
                    edits.append(FileEdit(observed.path, content.replace(needle, 'return line.split(",")')))
                    diagnosis = "The parser strips the trailing delimiter before splitting."
                    break
            if "inclusive" in lower_issue or "including the end" in lower_issue:
                needle = "for value in range(start, end):"
                if needle in content:
                    edits.append(FileEdit(observed.path, content.replace(needle, "for value in range(start, end + 1):")))
                    diagnosis = "The summation loop excludes the upper bound."
                    break
            if "keep 0" in lower_issue or "drop none" in lower_issue or "preserve zero" in lower_issue:
                needle = "return [value for value in values if value]"
                if needle in content:
                    edits.append(FileEdit(observed.path, content.replace(needle, "return [value for value in values if value is not None]")))
                    diagnosis = "The filter removes all falsy values instead of only None."
                    break
        return ProposedFix(diagnosis=diagnosis, edits=tuple(edits), raw_response=diagnosis)


class OpenAIBackend:
    OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, model: str) -> None:
        self.model = model
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the 'openai' extra to use the OpenAI backend.") from exc
        self.api_key = self._resolve_api_key()
        self.base_url = self._resolve_base_url()
        self.default_headers = self._resolve_default_headers()
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=self.default_headers or None,
        )

    def propose_fix(
        self,
        *,
        prompt: str,
        observed_files: Sequence[ObservedFile],
        issue: str,
        policy: Policy,
        workspace: Path,
        visible_test_output: str | None,
    ) -> ProposedFix:
        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                temperature=policy.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You fix small Python repository bugs. Return JSON only with keys "
                            "'diagnosis' and 'edits'. Each edit must include 'path' and 'new_content'."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:
            raise BackendResponseError("api_error", f"OpenAI-compatible request failed: {exc}") from exc

        raw = completion.choices[0].message.content or "{}"
        payload = self._parse_json(raw)
        diagnosis, edits = self._validate_payload(payload)
        return ProposedFix(diagnosis=diagnosis, edits=edits, raw_response=raw)

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        parse_errors: list[str] = []
        raw = raw.strip()
        if not raw:
            raise BackendResponseError("json_parse_error", "Model returned empty response.")

        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError as exc:
            parse_errors.append(f"direct parse: {exc}")

        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", raw, flags=re.DOTALL)
        if fenced:
            candidate = fenced.group(1)
            try:
                payload = json.loads(candidate)
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError as exc:
                parse_errors.append(f"fenced parse: {exc}")

        extracted = OpenAIBackend._extract_first_json_object(raw)
        if extracted is not None:
            try:
                payload = json.loads(extracted)
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError as exc:
                parse_errors.append(f"embedded parse: {exc}")

        detail = "; ".join(parse_errors) if parse_errors else "no parse strategy succeeded"
        raise BackendResponseError("json_parse_error", f"Unable to parse model JSON response ({detail}).")

    @staticmethod
    def _extract_first_json_object(raw: str) -> str | None:
        decoder = json.JSONDecoder()
        for index, char in enumerate(raw):
            if char != "{":
                continue
            try:
                _, end_index = decoder.raw_decode(raw[index:])
                return raw[index : index + end_index]
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> tuple[str, tuple[FileEdit, ...]]:
        diagnosis_raw = payload.get("diagnosis", "")
        diagnosis = diagnosis_raw if isinstance(diagnosis_raw, str) else str(diagnosis_raw)
        edits_raw = payload.get("edits", [])
        if not isinstance(edits_raw, list):
            raise BackendResponseError("schema_error", "'edits' must be a list.")
        edits: list[FileEdit] = []
        invalid_edits = 0
        for item in edits_raw:
            if not isinstance(item, dict):
                invalid_edits += 1
                continue
            path = item.get("path")
            new_content = item.get("new_content")
            if not isinstance(path, str) or not isinstance(new_content, str):
                invalid_edits += 1
                continue
            edits.append(FileEdit(path=path, new_content=new_content))
        if invalid_edits and not edits:
            raise BackendResponseError("schema_error", "All edit entries are invalid.")
        return diagnosis, tuple(edits)

    @staticmethod
    def _resolve_api_key() -> str:
        key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("Set OPENAI_API_KEY or OPENROUTER_API_KEY to use the OpenAI-compatible backend.")
        return key

    @classmethod
    def _resolve_base_url(cls) -> str | None:
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENROUTER_BASE_URL")
        if base_url:
            return base_url
        has_openrouter_only_key = bool(os.getenv("OPENROUTER_API_KEY")) and not bool(os.getenv("OPENAI_API_KEY"))
        if has_openrouter_only_key:
            return cls.OPENROUTER_DEFAULT_BASE_URL
        return None

    @staticmethod
    def _resolve_default_headers() -> dict[str, str]:
        referer = os.getenv("OPENROUTER_HTTP_REFERER") or os.getenv("OPENROUTER_REFERER")
        title = os.getenv("OPENROUTER_X_TITLE") or os.getenv("OPENROUTER_TITLE")
        headers: dict[str, str] = {}
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
        return headers


def load_backend(name: str, model: str | None = None) -> ModelBackend:
    if name == "heuristic":
        return HeuristicBackend()
    if name == "openai":
        if not model:
            raise ValueError("The OpenAI backend requires --model.")
        return OpenAIBackend(model=model)
    raise ValueError(f"Unsupported backend: {name}")
