#!/usr/bin/env python3
"""Write a compact terminal RKX summary for humans and scripts.

The hook is deliberately fail-open. It only writes after a terminal,
conversation-matched lifecycle artifact is found and never copies raw slot
transcripts, logs, credentials, or the full chat transcript.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import rkx_lifecycle_common as lifecycle

TERMINAL_KINDS = {"blocked", "completed", "failed", "wave_cap"}
REDACTION_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\b(?:xox[baprs]|token|secret|password|passwd|api[_-]?key)\b\s*[:=]\s*\S+"), "[REDACTED]"),
    (re.compile(r"(?i)(X-PARTNER-APP-TOKEN\s*[=:]\s*)\S+"), r"\1[REDACTED]"),
)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _payload_from_stdin() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return _as_dict(json.loads(raw)) if raw.strip() else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _clean_text(value: Any, limit: int = 1200) -> str:
    if not isinstance(value, str):
        return ""
    text = re.sub(r"`+", "", value)
    for pattern, replacement in REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def _repo_root(payload: dict[str, Any]) -> Path | None:
    return lifecycle.repo_root(payload)


def _conversation_id(payload: dict[str, Any]) -> str:
    return lifecycle.conversation_id(payload)


def _load_terminal_artifact(repo_root: Path, conversation_id: str) -> tuple[Path, dict[str, Any]] | None:
    max_age_seconds = int(
        os.environ.get(
            "RKX_SLACK_NOTIFICATION_MAX_AGE_SEC",
            os.environ.get("RKX_SLACK_STATE_MAX_AGE_SEC", "1800"),
        )
    )
    return lifecycle.artifact_by_exact_event(
        repo_root,
        conversation_id,
        max_age_seconds=max_age_seconds,
        predicate=lambda artifact: artifact.get("kind") in TERMINAL_KINDS,
    )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _field(text: str, name: str) -> str:
    match = re.search(
        rf"(?m)^\s*(?:-\s*)?`?{re.escape(name)}`?\s*:\s*[\"']?([^\"'\n]+)",
        text,
    )
    return _clean_text(match.group(1)) if match else ""


def _latest_decision(repo_root: Path, run_dir: Path) -> tuple[Path | None, str]:
    pointer = run_dir / "latest-decision.json"
    try:
        pointer_data = _as_dict(json.loads(pointer.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, TypeError):
        pointer_data = {}
    decision = _as_dict(pointer_data.get("decision_artifact"))
    decision_ref = decision.get("path")
    if isinstance(decision_ref, str) and decision_ref:
        decision_path = (repo_root / decision_ref).resolve()
        try:
            decision_path.relative_to(repo_root.resolve())
        except ValueError:
            decision_path = None
        if decision_path is not None and decision_path.is_file():
            return decision_path, _read_text(decision_path)

    pointer_text = _read_text(run_dir / "latest-decision.yaml")
    legacy_match = re.search(
        r"(?m)^\s*(?:decision_artifact_path|recovery|merge|decision)\s*:\s*(\S+)",
        pointer_text,
    )
    if legacy_match:
        legacy_path = (repo_root / legacy_match.group(1)).resolve()
        try:
            legacy_path.relative_to(repo_root.resolve())
        except ValueError:
            legacy_path = None
        if legacy_path is not None and legacy_path.is_file():
            return legacy_path, _read_text(legacy_path)

    candidates = sorted(
        [path for path in run_dir.glob("wave-*/*.md") if path.name in {"recovery.md", "merge.md"}],
        key=lambda path: path.stat().st_mtime,
    )
    if candidates:
        return candidates[-1], _read_text(candidates[-1])
    return None, ""


def _capture_target(repo_root: Path, run_dir: Path, artifact: dict[str, Any]) -> Path:
    capture_dir = artifact.get("capture_dir")
    if not isinstance(capture_dir, str) or not capture_dir:
        return run_dir
    candidate = (repo_root / capture_dir).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return run_dir
    return candidate if candidate.is_dir() else run_dir


def _escape_cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", " ").strip()


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.chmod(0o644)
    temporary.replace(path)


def _render(repo_root: Path, artifact_path: Path, artifact: dict[str, Any]) -> tuple[Path, str]:
    run_id = _clean_text(artifact.get("run_id"), 160)
    run_dir = artifact_path.parent
    decision_path, decision_text = _latest_decision(repo_root, run_dir)
    state_text = _read_text(run_dir / "state.md")
    confidence_candidate = (
        _field(decision_text, "root_confidence")
        or _field(decision_text, "confidence")
        or _field(state_text, "root_confidence")
    )
    confidence = (
        confidence_candidate
        if re.fullmatch(r"(?:100|[1-9]?\d)%", confidence_candidate)
        else ""
    )
    phase = _field(state_text, "phase") or _field(decision_text, "kind") or _clean_text(artifact.get("kind"))
    model = _field(decision_text, "MODEL")
    blocker = _clean_text(artifact.get("blocker"), 900)
    next_action = _clean_text(artifact.get("next_action"), 900)
    summary = _clean_text(artifact.get("summary"), 1400)
    problem = _clean_text(artifact.get("problem_title"), 300)
    decision_ref = _clean_text(
        str(decision_path.relative_to(repo_root.resolve())) if decision_path else "",
        400,
    )
    target_dir = _capture_target(repo_root, run_dir, artifact)
    output_path = target_dir / "easy-summarize.md"
    lines = [
        "# RKX easy summary",
        "",
        f"Run: `{run_id}`",
        f"Problem: {problem}",
        f"Lifecycle kind: `{_clean_text(artifact.get('kind'), 80)}`",
        f"Lifecycle event: `{_clean_text(artifact.get('event_id'), 300)}`",
        "",
        "## Summary",
        summary,
    ]
    if blocker:
        lines.extend(["", "## Blocker", blocker])
    if next_action:
        lines.extend(["", "## Next action", next_action])
    details = []
    if phase:
        details.append(f"- Phase: `{phase}`")
    if confidence:
        details.append(f"- Recorded confidence: `{confidence}`")
    if model:
        details.append(f"- Recorded synthesis model: `{model}`")
    if decision_ref:
        details.append(f"- Decision artifact: `{decision_ref}`")
    if details:
        lines.extend(["", "## Recorded metadata", *details])
    lines.extend(
        [
            "",
            "The complete Chat summary remains canonical. This file is a safe compact export and does not reconstruct a verdict.",
            "",
        ]
    )
    content = "\n".join(lines)
    return output_path, content


def process(payload: dict[str, Any]) -> Path | None:
    repo_root = _repo_root(payload)
    conversation_id = _conversation_id(payload)
    if repo_root is None or not conversation_id:
        return None
    match = _load_terminal_artifact(repo_root, conversation_id)
    if match is None:
        return None
    artifact_path, artifact = match
    output_path, content = _render(repo_root, artifact_path, artifact)
    _write_atomic(output_path, content)
    return output_path


def main() -> int:
    try:
        process(_payload_from_stdin())
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        print(f"[rkx-easy-summary] fail-open: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
