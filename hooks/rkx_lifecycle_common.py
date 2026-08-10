"""Shared validation for safe, run-scoped RKX lifecycle artifacts."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable


ATTENTION_KINDS = {"waiting_user", "blocked", "failed", "wave_cap"}
RESULT_KINDS = {"completed"}
TERMINAL_KINDS = {"blocked", "completed", "failed", "wave_cap"}
SUPPORTED_KINDS = {"started", "progress", *ATTENTION_KINDS, *RESULT_KINDS}
SUPPORTED_NOTIFICATION_TYPES = {"attention", "result"}

# Agents routinely confuse notification_type with kind. Map aliases so delivery
# stays industrial even when writers use the wrong vocabulary.
_KIND_ALIASES = {
    "started": "started",
    "start": "started",
    "progress": "progress",
    "waiting_user": "waiting_user",
    "waiting": "waiting_user",
    "wait": "waiting_user",
    "user": "waiting_user",
    "needs_user": "waiting_user",
    "blocked": "blocked",
    "block": "blocked",
    "blocker": "blocked",
    "failed": "failed",
    "fail": "failed",
    "failure": "failed",
    "error": "failed",
    "wave_cap": "wave_cap",
    "cap": "wave_cap",
    "completed": "completed",
    "complete": "completed",
    "done": "completed",
    "end": "completed",
    # Common mistakes: card type used as kind
    "attention": "__attention__",
    "result": "completed",
}


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


def _canonical_kind(kind_value: Any, *, has_blocker: bool) -> str | None:
    raw = _string(kind_value).lower().replace("-", "_").replace(" ", "_")
    if not raw:
        return None
    mapped = _KIND_ALIASES.get(raw, raw if raw in SUPPORTED_KINDS else None)
    if mapped == "__attention__":
        return "blocked" if has_blocker else "waiting_user"
    return mapped


def normalize_artifact(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a best-effort canonical lifecycle artifact.

    Fixes the frequent agent mistakes of writing notification_type values into
    `kind`, and upgrades progress/started when an explicit card type is present.
    """

    artifact = dict(as_dict(raw))
    has_blocker = bool(_string(artifact.get("blocker")))
    explicit_type = artifact.get("notification_type")
    if isinstance(explicit_type, str):
        explicit_type = explicit_type.strip().lower()
    else:
        explicit_type = None
    if explicit_type not in {None, *SUPPORTED_NOTIFICATION_TYPES}:
        explicit_type = None

    kind = _canonical_kind(artifact.get("kind"), has_blocker=has_blocker)

    # If writers put the card type only in notification_type while leaving an
    # audit kind, promote to a sendable lifecycle kind.
    if kind in {None, "started", "progress"} and explicit_type in SUPPORTED_NOTIFICATION_TYPES:
        if explicit_type == "result":
            kind = "completed"
        else:
            kind = "blocked" if has_blocker else "waiting_user"

    if kind is None:
        return artifact

    artifact["kind"] = kind
    if kind in ATTENTION_KINDS:
        artifact["notification_type"] = "attention"
    elif kind in RESULT_KINDS:
        artifact["notification_type"] = "result"
    else:
        artifact.pop("notification_type", None)
    return artifact


def notification_type(artifact: dict[str, Any]) -> str | None:
    normalized = normalize_artifact(artifact)
    explicit = normalized.get("notification_type")
    kind = normalized.get("kind")
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
        artifact = normalize_artifact(as_dict(json.loads(path.read_text(encoding="utf-8"))))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    if artifact.get("schema_version") != 1 or artifact.get("kind") not in SUPPORTED_KINDS:
        return None
    required = ("conversation_id", "event_id", "run_id", "problem_title", "summary")
    if any(not _string(artifact.get(field)) for field in required):
        return None
    if artifact.get("run_id") != path.parent.name:
        return None
    if "full_verdict_available" in artifact and not isinstance(
        artifact["full_verdict_available"], bool
    ):
        return None
    explicit = artifact.get("notification_type")
    if explicit not in {None, *SUPPORTED_NOTIFICATION_TYPES}:
        return None
    derived = notification_type(artifact)
    if explicit is not None and derived != explicit:
        return None
    return artifact


def persist_normalized_artifact(path: Path) -> dict[str, Any] | None:
    """Normalize on disk when aliases were used, then return the validated artifact."""

    try:
        original_text = path.read_text(encoding="utf-8")
        original = as_dict(json.loads(original_text))
    except (OSError, json.JSONDecodeError, TypeError):
        return None

    normalized = normalize_artifact(original)
    if normalized != original:
        try:
            tmp = path.with_name(f".{path.name}.tmp")
            tmp.write_text(
                json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            tmp.replace(path)
        except OSError:
            return read_artifact(path)
    return read_artifact(path)


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
