"""Shared validation for safe, run-scoped RKX lifecycle artifacts."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from pathlib import Path
from typing import Any, Callable


ATTENTION_KINDS = {"waiting_user", "blocked", "failed", "wave_cap"}
RESULT_KINDS = {"completed"}
TERMINAL_KINDS = {"blocked", "completed", "failed", "wave_cap"}
SUPPORTED_KINDS = {"started", "progress", *ATTENTION_KINDS, *RESULT_KINDS}
SUPPORTED_NOTIFICATION_TYPES = {"attention", "result"}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def conversation_id(payload: dict[str, Any]) -> str:
    for key in (
        "conversation_id",
        "conversationId",
        "session_id",
        "sessionId",
        "chat_id",
        "chatId",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return _string(as_dict(payload.get("conversation")).get("id"))


def repo_root(payload: dict[str, Any]) -> Path | None:
    candidates: list[Path] = []
    configured_root = os.environ.get("RKX_REPO_ROOT")
    if configured_root:
        candidates.append(Path(configured_root))
    workspace_roots = payload.get("workspace_roots") or payload.get("workspaceRoots") or []
    for workspace_root in workspace_roots:
        if isinstance(workspace_root, str):
            candidates.append(Path(workspace_root))
    candidates.append(Path.cwd())

    for candidate in candidates:
        try:
            if (candidate / "loops").is_dir():
                return candidate
        except OSError:
            continue
    return None


def notification_type(artifact: dict[str, Any]) -> str | None:
    explicit = artifact.get("notification_type")
    kind = artifact.get("kind")
    if explicit in SUPPORTED_NOTIFICATION_TYPES:
        if explicit == "attention" and kind in ATTENTION_KINDS:
            return explicit
        if explicit == "result" and kind in RESULT_KINDS:
            return explicit
        return None
    if kind in ATTENTION_KINDS:
        return "attention"
    if kind in RESULT_KINDS:
        return "result"
    return None


def read_artifact(path: Path) -> dict[str, Any] | None:
    try:
        artifact = as_dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    if artifact.get("schema_version") != 1 or artifact.get("kind") not in SUPPORTED_KINDS:
        return None
    required = (
        "conversation_id",
        "event_id",
        "run_id",
        "wave",
        "problem_title",
        "summary",
        "notification_type",
    )
    if any(not _string(artifact.get(field)) for field in required):
        return None
    if artifact.get("run_id") != path.parent.name:
        return None
    full_verdict_available = artifact.get("full_verdict_available")
    if not isinstance(full_verdict_available, bool):
        return None
    verdict_url = artifact.get("full_verdict_url")
    if full_verdict_available:
        if not isinstance(verdict_url, str):
            return None
        parsed_url = urllib.parse.urlparse(verdict_url)
        if (
            parsed_url.scheme not in {"http", "https"}
            or not parsed_url.netloc
            or parsed_url.username
            or parsed_url.password
        ):
            return None
    elif verdict_url is not None:
        return None
    explicit = artifact.get("notification_type")
    if explicit not in SUPPORTED_NOTIFICATION_TYPES:
        return None
    derived = notification_type(artifact)
    if derived != explicit:
        return None
    return artifact


def latest_artifact(
    repo_root_path: Path,
    conversation: str,
    *,
    max_age_seconds: int,
    predicate: Callable[[dict[str, Any]], bool],
    now: float | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    if not conversation:
        return None
    now = time.time() if now is None else now
    loops_root = repo_root_path / "loops"
    if not loops_root.is_dir():
        return None
    matches: list[tuple[float, Path, dict[str, Any]]] = []
    for path in loops_root.glob("*/slack-notification.json"):
        try:
            modified = path.stat().st_mtime
        except OSError:
            continue
        if now - modified > max_age_seconds:
            continue
        artifact = read_artifact(path)
        if artifact is None or artifact.get("conversation_id") != conversation:
            continue
        if predicate(artifact):
            matches.append((modified, path, artifact))
    if not matches:
        return None
    _, path, artifact = max(matches, key=lambda item: item[0])
    return path, artifact


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
