#!/usr/bin/env python3
"""Render and deliver the safe, run-scoped RKX Slack notification card."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import fcntl
from pathlib import Path
from typing import Any

import rkx_lifecycle_common as lifecycle

KIND_LABELS = {
    "started": ("🔎", "Check started"),
    "progress": ("🔎", "Check in progress"),
    "waiting_user": ("⏸", "Needs your step"),
    "blocked": ("❌", "Check stopped"),
    "completed": ("✅", "Check completed"),
    "failed": ("❌", "Check failed"),
    "wave_cap": ("⏸", "Check hit the wave limit"),
}
NOTIFICATION_TYPE_LABELS = {
    "attention": ("⚠️", "Needs attention"),
    "result": ("✅", "Work summary"),
}
ATTENTION_KINDS = {"waiting_user", "blocked", "failed", "wave_cap"}
RESULT_KINDS = {"completed"}
TERMINAL_KINDS = {"waiting_user", "blocked", "completed", "failed", "wave_cap"}
SUPPORTED_KINDS = set(KIND_LABELS)
SUPPORTED_NOTIFICATION_TYPES = set(NOTIFICATION_TYPE_LABELS)
REDACTION_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]+"), "[REDACTED_TOKEN]"),
    (
        re.compile(r"(?i)(hooks\.slack\.com/services/)[A-Za-z0-9/_-]+"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+"),
        r"\1=[REDACTED]",
    ),
)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _clean_text(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    text = re.sub(r"`+", "", value)
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n:-")
    for pattern, replacement in REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def _slack_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _slack_mention() -> str:
    value = os.environ.get("SLACK_NOTIFY_MENTION", "").strip()
    if re.fullmatch(r"<@[UW][A-Z0-9]+>", value):
        return value
    if re.fullmatch(r"[UW][A-Z0-9]+", value):
        return f"<@{value}>"
    return ""


def _safe_url(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 3000:
        return ""
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if parsed.username or parsed.password:
        return ""
    if re.search(r"(?i)(?:^|[?&])(token|secret|password|api[_-]?key)=", parsed.query):
        return ""
    return value


def _payload_from_stdin(raw: str) -> dict[str, Any]:
    try:
        return _as_dict(json.loads(raw)) if raw.strip() else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _conversation_id(payload: dict[str, Any]) -> str:
    return _clean_text(lifecycle.conversation_id(payload), 255)


def _repo_root(payload: dict[str, Any]) -> Path | None:
    return lifecycle.repo_root(payload)


def _read_artifact(path: Path) -> dict[str, Any] | None:
    return lifecycle.read_artifact(path)


def load_notification_artifact(
    repo_root: Path,
    conversation_id: str,
    now: float | None = None,
    max_age_seconds: int = 1800,
) -> dict[str, Any] | None:
    """Return only an artifact belonging to the current Cursor conversation."""

    if not conversation_id:
        return None
    match = lifecycle.latest_artifact(
        repo_root,
        conversation_id,
        max_age_seconds=max_age_seconds,
        predicate=lambda artifact: lifecycle.notification_type(artifact) is not None,
        now=now,
    )
    return match[1] if match else None


def _metadata_line(artifact: dict[str, Any]) -> str:
    metadata = [
        _clean_text(artifact.get("run_id"), 160),
        _clean_text(artifact.get("wave"), 80),
    ]
    return " · ".join(value for value in metadata if value)


def notification_type(artifact: dict[str, Any]) -> str | None:
    """Classify a lifecycle artifact into one of the two user-facing cards."""
    return lifecycle.notification_type(artifact)


def render_card(artifact: dict[str, Any]) -> dict[str, Any] | None:
    """Render the Slack message and Block Kit payload from safe artifact fields."""

    artifact = lifecycle.normalize_artifact(artifact)
    kind = artifact.get("kind")
    message_type = notification_type(artifact)
    if kind not in SUPPORTED_KINDS or message_type is None:
        return None

    icon, status_label = NOTIFICATION_TYPE_LABELS[message_type]
    problem_title = _clean_text(artifact.get("problem_title"), 150)
    summary = _clean_text(artifact.get("summary"), 1000)
    blocker = _clean_text(artifact.get("blocker"), 700)
    next_action = _clean_text(artifact.get("next_action"), 700)
    if message_type == "attention" and not next_action:
        next_action = "Reply in Cursor and choose the next step."
    run_id = _clean_text(artifact.get("run_id"), 160)
    wave = _clean_text(artifact.get("wave"), 80)
    event_id = _clean_text(artifact.get("event_id"), 255)
    full_verdict_url = _safe_url(artifact.get("full_verdict_url"))

    if not problem_title or not summary or not event_id or not run_id:
        return None

    headline = f"{icon} {status_label}: {problem_title}"
    mention = _slack_mention()
    lines = [f"{mention} {headline}".strip(), "", summary]
    if blocker:
        lines.append(f"Blocker: {blocker}")
    if next_action:
        action_label = "Need from you" if message_type == "attention" else "Next step"
        lines.append(f"{action_label}: {next_action}")
    if artifact.get("full_verdict_available") and not full_verdict_url:
        lines.append("Full verdict: in Cursor")
    if full_verdict_url:
        lines.append(f"Full verdict: {full_verdict_url}")
    metadata = _metadata_line(artifact)
    if metadata:
        lines.extend(["", metadata])

    summary_mrkdwn = f"{mention} {_slack_escape(summary)}".strip()
    detail_lines = []
    if blocker:
        detail_lines.append(f"*Blocker:* {_slack_escape(blocker)}")
    if next_action:
        action_label = "Need from you" if message_type == "attention" else "Next step"
        detail_lines.append(f"*{action_label}:* {_slack_escape(next_action)}")
    if full_verdict_url:
        detail_lines.append(
            f"*Full verdict:* <{full_verdict_url}|Open full verdict>"
        )

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": headline[:150]},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary_mrkdwn[:3000]},
        },
    ]
    if detail_lines:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n".join(detail_lines)[:3000]},
            }
        )
    if metadata:
        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": _slack_escape(metadata)}],
            }
        )

    return {
        "text": "\n".join(lines),
        "blocks": blocks,
        "dedup_key": "|".join(
            [
                _clean_text(artifact.get("conversation_id"), 255),
                event_id,
                kind,
            ]
        ),
        "event_id": event_id,
        "kind": kind,
    }


def _dedup_path() -> Path:
    configured = os.environ.get("RKX_SLACK_DEDUP_FILE")
    if configured:
        return Path(configured)
    return Path.home() / ".cursor" / "rkx-slack-notify.dedup.json"


def _read_dedup_entries(stream: Any, now: float, ttl_seconds: int) -> dict[str, dict[str, Any]]:
    try:
        stream.seek(0)
        raw_entries = _as_dict(json.load(stream))
    except (json.JSONDecodeError, TypeError):
        raw_entries = {}

    entries: dict[str, dict[str, Any]] = {}
    for key, raw_entry in raw_entries.items():
        if isinstance(raw_entry, (int, float)):
            raw_entry = {
                "state": "delivered",
                "claimed_at": raw_entry,
                "expires_at": raw_entry + ttl_seconds,
            }
        entry = _as_dict(raw_entry)
        expires_at = entry.get("expires_at")
        if (
            isinstance(expires_at, (int, float))
            and expires_at > now
            and entry.get("state") in {"pending", "delivered"}
        ):
            entries[key] = entry
    return entries


def _write_dedup_entries(stream: Any, entries: dict[str, dict[str, Any]]) -> None:
    stream.seek(0)
    stream.truncate()
    json.dump(entries, stream, ensure_ascii=False, sort_keys=True)
    stream.flush()
    os.fsync(stream.fileno())


def _with_locked_entries(
    path: Path, now: float, ttl_seconds: int, operation: Any
) -> Any:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        os.chmod(path, 0o600)
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            entries = _read_dedup_entries(stream, now, ttl_seconds)
            result, changed = operation(entries)
            if changed:
                _write_dedup_entries(stream, entries)
            return result
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def claim_delivery(
    path: Path,
    key: str,
    now: float,
    ttl_seconds: int,
    pending_seconds: int,
) -> bool:
    """Claim one send, recovering a pending claim after its short lease."""

    def claim(entries: dict[str, dict[str, Any]]) -> tuple[bool, bool]:
        entry = entries.get(key)
        if entry is not None and entry.get("state") == "delivered":
            return False, False
        if entry is not None and entry.get("state") == "pending":
            claimed_at = entry.get("claimed_at")
            if isinstance(claimed_at, (int, float)) and now - claimed_at < pending_seconds:
                return False, False
        entries[key] = {
            "state": "pending",
            "claimed_at": now,
            "expires_at": now + pending_seconds,
        }
        return True, True

    return bool(_with_locked_entries(path, now, ttl_seconds, claim))


def finalize_delivery(path: Path, key: str, now: float, ttl_seconds: int) -> None:
    def finalize(entries: dict[str, dict[str, Any]]) -> tuple[None, bool]:
        entries[key] = {
            "state": "delivered",
            "claimed_at": now,
            "expires_at": now + ttl_seconds,
        }
        return None, True

    _with_locked_entries(path, now, ttl_seconds, finalize)


def release_claim(path: Path, key: str, now: float, ttl_seconds: int) -> None:
    def release(entries: dict[str, dict[str, Any]]) -> tuple[None, bool]:
        if entries.get(key, {}).get("state") == "pending":
            entries.pop(key, None)
            return None, True
        return None, False

    _with_locked_entries(path, now, ttl_seconds, release)


def is_duplicate(path: Path, key: str, now: float, ttl_seconds: int) -> bool:
    def inspect(entries: dict[str, dict[str, Any]]) -> tuple[bool, bool]:
        return key in entries, False

    return bool(_with_locked_entries(path, now, ttl_seconds, inspect))


def remember_delivery(path: Path, key: str, now: float, ttl_seconds: int) -> None:
    finalize_delivery(path, key, now, ttl_seconds)


def _log(message: str) -> None:
    line = f"[rkx-slack-notify] {message}"
    print(line, file=sys.stderr)
    try:
        log_path = Path.home() / ".cursor" / "rkx-slack-notify.log"
        log_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {message}\n")
    except OSError:
        pass


def _post_json(url: str, body: dict[str, Any], headers: dict[str, str]) -> None:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response_body = response.read().decode("utf-8", errors="replace")
    if "slack.com/api/" in url:
        response_data = _as_dict(json.loads(response_body))
        if response_data.get("ok") is not True:
            raise RuntimeError("Slack API rejected notification")


def deliver(card: dict[str, Any]) -> None:
    body = {"text": card["text"], "blocks": card["blocks"]}
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    bot_token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    channel = os.environ.get("SLACK_NOTIFY_CHANNEL", "").strip()

    if webhook_url:
        if not _slack_mention():
            _log("warn: SLACK_NOTIFY_MENTION empty — channel webhook may not push mobile")
        _post_json(
            webhook_url,
            body,
            {"Content-Type": "application/json; charset=utf-8"},
        )
        return
    if bot_token and channel:
        _post_json(
            "https://slack.com/api/chat.postMessage",
            {"channel": channel, **body},
            {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {bot_token}",
            },
        )
        return
    raise RuntimeError("Slack transport is not configured")


def deliver_with_retries(card: dict[str, Any]) -> None:
    attempts = max(1, int(os.environ.get("RKX_SLACK_DELIVER_RETRIES", "3")))
    delays = [0.4, 1.0, 2.0]
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            deliver(card)
            return
        except (OSError, RuntimeError, ValueError, urllib.error.URLError) as error:
            last_error = error
            if attempt + 1 >= attempts:
                break
            time.sleep(delays[min(attempt, len(delays) - 1)])
    assert last_error is not None
    raise last_error


def _should_send(mode: str, artifact: dict[str, Any]) -> bool:
    message_type = notification_type(artifact)
    if message_type is None:
        return False
    if mode in {"all", "events", "terminal_only", "attention_and_result"}:
        return True
    if mode == "attention":
        return message_type == "attention"
    if mode == "result":
        return message_type == "result"
    return False


def _max_age_seconds() -> int:
    return int(
        os.environ.get(
            "RKX_SLACK_NOTIFICATION_MAX_AGE_SEC",
            os.environ.get("RKX_SLACK_STATE_MAX_AGE_SEC", "1800"),
        )
    )


def _deliver_artifact(artifact: dict[str, Any]) -> bool:
    mode = os.environ.get("RKX_SLACK_NOTIFY_MODE", "attention_and_result")
    if not _should_send(mode, artifact):
        _log(
            f"skip non-sendable kind={artifact.get('kind')} "
            f"type={notification_type(artifact)} mode={mode}"
        )
        return False

    card = render_card(artifact)
    if card is None:
        _log(f"skip render_failed event_id={artifact.get('event_id')}")
        return False

    now = time.time()
    max_age = _max_age_seconds()
    dedup_ttl = int(os.environ.get("RKX_SLACK_DEDUP_SEC", str(max_age)))
    pending_ttl = int(os.environ.get("RKX_SLACK_PENDING_SEC", "120"))
    dedup_path = _dedup_path()
    if not claim_delivery(dedup_path, card["dedup_key"], now, dedup_ttl, pending_ttl):
        _log(f"skip dedup event_id={card['event_id']}")
        return False

    try:
        deliver_with_retries(card)
    except (OSError, RuntimeError, ValueError, urllib.error.URLError) as error:
        try:
            release_claim(dedup_path, card["dedup_key"], now, dedup_ttl)
        except OSError:
            pass
        _log(f"deliver_failed event_id={card['event_id']}: {error}")
        return False

    try:
        finalize_delivery(dedup_path, card["dedup_key"], now, dedup_ttl)
    except OSError as error:
        _log(f"dedup write skipped: {error}")
    _log(
        f"delivered type={notification_type(artifact)} "
        f"kind={card['kind']} event_id={card['event_id']}"
    )
    return True


def process(payload: dict[str, Any], repo_root: Path | None = None) -> bool:
    conversation_id = _conversation_id(payload)
    if not conversation_id:
        _log("skip stop: missing conversation_id")
        return False

    repo_root = repo_root or _repo_root(payload)
    if repo_root is None:
        _log("skip stop: repo_root unresolved")
        return False
    artifact = load_notification_artifact(
        repo_root, conversation_id, max_age_seconds=_max_age_seconds()
    )
    if artifact is None:
        _log(f"skip stop: no sendable artifact for conversation={conversation_id}")
        return False
    return _deliver_artifact(artifact)


def process_artifact_file(path: Path) -> bool:
    """Normalize + immediately deliver one loops/*/slack-notification.json write."""

    try:
        resolved = path.expanduser().resolve()
    except OSError:
        _log(f"skip write: unreadable path={path}")
        return False
    if resolved.name != "slack-notification.json":
        return False
    if resolved.parent.parent.name != "loops":
        _log(f"skip write: not under loops/<run>/ path={resolved}")
        return False

    artifact = lifecycle.persist_normalized_artifact(resolved)
    if artifact is None:
        _log(f"skip write: invalid artifact path={resolved}")
        return False
    return _deliver_artifact(artifact)


def process_file_edit(payload: dict[str, Any]) -> bool:
    """afterFileEdit entry: fire as soon as the lifecycle artifact is written."""

    raw_path = payload.get("file_path") or payload.get("filePath") or ""
    if not isinstance(raw_path, str) or not raw_path:
        return False
    if not raw_path.endswith("slack-notification.json"):
        return False

    path = Path(raw_path)
    if not path.is_absolute():
        for root in payload.get("workspace_roots") or payload.get("workspaceRoots") or []:
            if not isinstance(root, str):
                continue
            candidate = Path(root) / raw_path
            if candidate.exists():
                path = candidate
                break
    return process_artifact_file(path)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        raw = sys.stdin.read()
        payload = _payload_from_stdin(raw)
        if "--on-write" in args or payload.get("hook_event_name") == "afterFileEdit":
            process_file_edit(payload)
        elif "--file" in args:
            index = args.index("--file")
            if index + 1 >= len(args):
                _log("fail-open: --file requires a path")
            else:
                process_artifact_file(Path(args[index + 1]))
        else:
            process(payload)
    except (OSError, ValueError, TypeError) as error:
        _log(f"fail-open: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
