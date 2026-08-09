#!/usr/bin/env python3
"""Validate RKX blueprint-coverage fixtures and qualified pairs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PERCENT = re.compile(r"(?:100|[1-9]?\d)%$")
TARGETS = {
    "invariant",
    "contract",
    "failure_mode",
    "flow_transition",
    "protocol_requirement",
    "deployment_boundary",
    "reference_architecture",
    "interconnection_contract",
}
IMPACTS = {"root_hypothesis", "remediation_plan", "root_confidence"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    return value


def percentage(value: Any) -> int:
    if not isinstance(value, str) or not PERCENT.fullmatch(value):
        raise ValueError("confidence and relevance fields must be exact percentages")
    return int(value[:-1])


def validate_pair(pair: dict[str, Any]) -> None:
    required = {
        "pair_id",
        "zone_relevance",
        "reference_applicability",
        "relation",
        "verification_targets",
        "impact_targets",
        "evidence_refs",
        "confidence",
        "confidence_basis",
    }
    missing = required - set(pair)
    if missing:
        raise ValueError(f"missing fields: {', '.join(sorted(missing))}")
    if percentage(pair["zone_relevance"]) < 70 or percentage(pair["reference_applicability"]) < 70:
        raise ValueError("qualified pair does not meet the 70% threshold")
    percentage(pair["confidence"])
    if pair["relation"] not in {"root_zone", "causal_predecessor"}:
        raise ValueError("invalid causal relation")
    if not set(pair["verification_targets"]) & TARGETS:
        raise ValueError("missing verification target")
    if not set(pair["impact_targets"]) & IMPACTS:
        raise ValueError("missing impact target")
    if not pair["evidence_refs"] or not isinstance(pair["confidence_basis"], str):
        raise ValueError("missing evidence or confidence basis")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-results", action="store_true")
    args = parser.parse_args()
    fixture_root = ROOT / "scripts/fixtures/blueprint"
    valid = load(fixture_root / "qualified-pair-minimal.json")
    validate_pair(valid)

    invalid = load(fixture_root / "missing-confidence-basis.json")
    try:
        validate_pair(invalid)
    except ValueError:
        pass
    else:
        raise SystemExit("FAIL invalid fixture unexpectedly passed")

    if args.require_results and not valid["evidence_refs"]:
        raise SystemExit("FAIL required results are missing")
    print("PASS RKX blueprint coverage validation")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        raise SystemExit(1)
