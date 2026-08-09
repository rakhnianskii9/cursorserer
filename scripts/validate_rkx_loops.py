#!/usr/bin/env python3
"""Dependency-free validation for the portable RKX control plane."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIDENCE = re.compile(r"(?:100|[1-9]?\d)%$")
REQUIRED_SPEC_FIELDS = {
    "schema_version",
    "kind",
    "run_id",
    "wave_id",
    "token_mode",
    "billing_credential_scope",
    "spec_revision",
    "confidence",
    "confidence_basis",
    "hypotheses",
    "slots",
    "dispatch",
    "stop_condition",
}


def fail(message: str) -> None:
    print(f"FAIL {message}")
    raise SystemExit(1)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {error}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require_text(path: Path, *tokens: str) -> None:
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            fail(f"{path.relative_to(ROOT)} is missing required contract token: {token}")


def validate_frontmatter() -> None:
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            fail(f"{path.relative_to(ROOT)} lacks YAML frontmatter")
        frontmatter = text.split("---\n", 2)
        if len(frontmatter) < 3:
            fail(f"{path.relative_to(ROOT)} has malformed frontmatter")
        header = frontmatter[1]
        if not re.search(r"(?m)^name:\s*\S+", header):
            fail(f"{path.relative_to(ROOT)} frontmatter lacks name")
        if not re.search(r"(?m)^description:\s*\S+", header):
            fail(f"{path.relative_to(ROOT)} frontmatter lacks description")


def validate_wave_spec() -> None:
    spec = read_json(ROOT / "scripts/fixtures/control-plane/wave-spec-v1.json")
    missing = REQUIRED_SPEC_FIELDS - set(spec)
    if missing:
        fail(f"wave-spec-v1.json missing fields: {', '.join(sorted(missing))}")
    if spec["schema_version"] != 1:
        fail("wave-spec-v1.json must use schema_version 1")
    if spec["kind"] not in {"BOOTSTRAP_WAVE_SPEC", "NEXT_WAVE_SPEC", "WAVE_DECISION"}:
        fail("wave-spec-v1.json has an invalid kind")
    if spec["token_mode"] not in {"API", "CURSOR"}:
        fail("wave-spec-v1.json has an invalid token_mode")
    if spec["billing_credential_scope"] not in {"API_CREDENTIALS", "CURSOR_SUBSCRIPTION"}:
        fail("wave-spec-v1.json has an invalid billing_credential_scope")
    if not CONFIDENCE.fullmatch(str(spec["confidence"])):
        fail("wave-spec-v1.json has an invalid confidence")
    for hypothesis in spec["hypotheses"]:
        if not hypothesis.get("hypothesis_id"):
            fail("wave-spec-v1.json has a hypothesis without hypothesis_id")
        if hypothesis.get("state") not in {"CANDIDATE", "SUPPORTED", "WEAKENED", "REJECTED"}:
            fail("wave-spec-v1.json has an invalid hypothesis state")
    for slot in spec["slots"]:
        for field in (
            "expected_decision_change",
            "requirement",
            "correlation_refs",
            "searchability",
        ):
            if field not in slot:
                fail(f"wave-spec-v1.json slot lacks {field}")
        if slot["requirement"] not in {"REQUIRED", "OPTIONAL"}:
            fail("wave-spec-v1.json has an invalid slot requirement")
        if slot["searchability"] not in {"KNOWN", "UNKNOWN", "NOT_APPLICABLE"}:
            fail("wave-spec-v1.json has an invalid slot searchability")
    dispatch = spec["dispatch"]
    if dispatch.get("mode") != "PARALLEL" or dispatch.get("join") != "MERGER":
        fail("wave-spec-v1.json must use parallel dispatch with a Merger join")
    if not isinstance(dispatch.get("coverage_budget"), int) or dispatch["coverage_budget"] < 0:
        fail("wave-spec-v1.json has an invalid coverage budget")

    preflight = read_json(ROOT / "scripts/fixtures/control-plane/preflight-v1.json")
    if preflight.get("schema_version") != 1:
        fail("preflight-v1.json must use schema_version 1")
    if preflight.get("preflight_spec_revision") != spec["spec_revision"]:
        fail("preflight spec revision does not match wave spec")
    if preflight.get("orchestrator_resolution") != "DISPATCH_READY":
        fail("fixture preflight must dispatch READY slots")
    if any(slot.get("status") != "READY" for slot in preflight.get("slots", [])):
        fail("fixture preflight contains a non-ready slot")

    terminal = read_json(
        ROOT / "scripts/fixtures/control-plane/terminal-lifecycle.json"
    )
    required_terminal = {
        "schema_version",
        "conversation_id",
        "event_id",
        "run_id",
        "kind",
        "notification_type",
        "problem_title",
        "summary",
        "decision_artifact",
    }
    if required_terminal - set(terminal):
        fail("terminal lifecycle fixture is incomplete")
    if terminal["kind"] != "completed" or terminal["notification_type"] != "result":
        fail("terminal lifecycle fixture must be a completed result")
    if not isinstance(terminal["decision_artifact"], dict):
        fail("terminal lifecycle fixture lacks a decision artifact pointer")

    blocker = read_json(
        ROOT / "scripts/fixtures/control-plane/hard-blocker-decision.json"
    )
    if blocker.get("decision") != "HARD_BLOCKER":
        fail("hard-blocker fixture lacks HARD_BLOCKER")
    if blocker.get("advocate_mode") != "hard":
        fail("HARD_BLOCKER must enter the hard Advocate gate")
    if blocker.get("confidence") != "100%":
        fail("fixture must prove HARD_BLOCKER priority over high confidence")


def main() -> int:
    read_json(ROOT / "hooks.json")
    read_json(ROOT / "hooks.example.json")
    read_json(ROOT / "mcp.json.example")
    require_text(
        ROOT / "skills/rkx-loop-core/SKILL.md",
        "schema_version: 1",
        "spec_revision:",
        "expected_decision_change:",
        "CAPABILITY_PREFLIGHT",
    )
    require_text(
        ROOT / "hooks/rkx_slack_notify.py",
        "claim_delivery",
        "finalize_delivery",
        "latest_artifact",
    )
    validate_frontmatter()
    validate_wave_spec()
    print("PASS RKX control-plane schema and portable-surface checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
