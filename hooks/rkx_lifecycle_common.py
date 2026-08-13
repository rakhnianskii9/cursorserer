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
    # Valid chat-only lifecycle event. It is intentionally not in
    # SUPPORTED_KINDS, so Slack ignores manual ONE_WAVE summaries.
    "wave_result": "wave_result",
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
    run_id = _string(artifact.get("run_id"))
    if path.name == "slack-notification.json":
        expected_run = path.parent.name
    elif path.parent.name and path.parent.parent.name == "deliveries":
        expected_run = path.parent.parent.parent.name
    else:
        expected_run = path.parent.name
    if run_id != expected_run:
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


def _load_current_state(run_dir: Path) -> dict[str, Any]:
    for name in ("current.yaml", "current.json"):
        path = run_dir / "state" / name
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if name.endswith(".json"):
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            return as_dict(data)
        # Minimal YAML subset: key: value lines (no nested blocks required).
        state: dict[str, Any] = {}
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip("\"'")
            if value.lower() in {"null", "~", ""}:
                state[key] = None
            elif value.lower() in {"true", "false"}:
                state[key] = value.lower() == "true"
            else:
                try:
                    state[key] = int(value)
                except ValueError:
                    state[key] = value
        return state
    return {}


def _resolve_delivery_path(
    repo_root_path: Path, run_dir: Path, event_id: str, delivery_ref: str | None
) -> Path | None:
    expected = (run_dir / "deliveries" / event_id / "lifecycle.json").resolve()
    candidates: list[Path] = []
    if isinstance(delivery_ref, str) and delivery_ref:
        referenced = (repo_root_path / delivery_ref).resolve()
        if referenced != expected:
            return None
        candidates.append(referenced)
    candidates.append(expected)
    # Legacy single-file runs are readable only through an exact current-state
    # event pointer. New runs always use deliveries/<event_id>/lifecycle.json.
    candidates.append(run_dir / "slack-notification.json")
    for path in candidates:
        try:
            path.relative_to(repo_root_path.resolve())
        except ValueError:
            continue
        if path.is_file():
            return path
    return None


def artifact_by_exact_event(
    repo_root_path: Path,
    conversation: str,
    *,
    max_age_seconds: int,
    predicate: Callable[[dict[str, Any]], bool],
    now: float | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    """Select lifecycle artifact by exact event pointer — never by mtime."""

    if not conversation:
        return None
    now = time.time() if now is None else now
    loops_root = repo_root_path / "loops"
    if not loops_root.is_dir():
        return None

    exact: list[tuple[Path, dict[str, Any]]] = []
    legacy_singles: list[tuple[Path, dict[str, Any]]] = []

    for run_dir in sorted(path for path in loops_root.iterdir() if path.is_dir()):
        state = _load_current_state(run_dir)
        if state.get("conversation_id") == conversation:
            event_id = state.get("pending_delivery_event_id")
            if isinstance(event_id, str) and event_id:
                path = _resolve_delivery_path(
                    repo_root_path,
                    run_dir,
                    event_id,
                    state.get("delivery_ref")
                    if isinstance(state.get("delivery_ref"), str)
                    else None,
                )
                if path is not None:
                    try:
                        modified = path.stat().st_mtime
                    except OSError:
                        modified = now
                    if now - modified <= max_age_seconds:
                        artifact = read_artifact(path)
                        if (
                            artifact is not None
                            and artifact.get("conversation_id") == conversation
                            and artifact.get("event_id") == event_id
                            and predicate(artifact)
                        ):
                            exact.append((path, artifact))

        legacy_path = run_dir / "slack-notification.json"
        if legacy_path.is_file() and not state.get("pending_delivery_event_id"):
            try:
                modified = legacy_path.stat().st_mtime
            except OSError:
                continue
            if now - modified > max_age_seconds:
                continue
            artifact = read_artifact(legacy_path)
            if (
                artifact is not None
                and artifact.get("conversation_id") == conversation
                and predicate(artifact)
            ):
                legacy_singles.append((legacy_path, artifact))

    if len(exact) == 1:
        return exact[0]
    if exact:
        return None
    if len(legacy_singles) == 1:
        return legacy_singles[0]
    return None


latest_artifact = artifact_by_exact_event


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
