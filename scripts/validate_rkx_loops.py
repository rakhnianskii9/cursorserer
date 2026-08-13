#!/usr/bin/env python3
"""Validate RKX contracts, fixtures, and every canonical (non-legacy) run."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError as error:  # pragma: no cover - explicit runtime dependency
    raise SystemExit(f"FAIL missing validator dependency: {error}")


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT
PACKET_SCHEMAS = ROOT / "schemas" / "packets"
FIXTURES = ROOT / "scripts" / "fixtures" / "control-plane"


def fail(message: str) -> None:
    print(f"FAIL {message}")
    raise SystemExit(1)


class StaleTransition(RuntimeError):
    """CAS mismatch on state/current.yaml."""


def revision_filename(revision_seq: int) -> str:
    return f"{int(revision_seq):04d}.yaml"


def slot_report_ref(run_id: str, wave_id: int, slot_id: str, attempt_id: int) -> str:
    return (
        f"loops/{run_id}/wave-{wave_id}/slots/{slot_id}/attempts/{attempt_id}/report.md"
    )


def spec_ref(run_id: str, wave_id: int, revision_seq: int) -> str:
    return f"loops/{run_id}/wave-{wave_id}/specs/{revision_filename(revision_seq)}"


def preflight_ref(run_id: str, wave_id: int, revision_seq: int) -> str:
    return f"loops/{run_id}/wave-{wave_id}/preflights/{revision_filename(revision_seq)}"


def apply_state_cas(current: dict[str, Any], expected_state_revision: int, next_state: dict[str, Any]) -> dict[str, Any]:
    if current.get("state_revision") != expected_state_revision:
        raise StaleTransition("STALE_TRANSITION")
    next_revision = int(expected_state_revision) + 1
    if next_state.get("state_revision") != next_revision:
        fail("CAS next state_revision must be expected_state_revision + 1")
    if next_state.get("previous_state_revision") != expected_state_revision:
        fail("CAS previous_state_revision must equal expected_state_revision")
    return next_state


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"{path.relative_to(REPO)} is not valid JSON: {error}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(REPO)} must contain an object")
    return value


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        fail(f"{path.relative_to(REPO)} is not valid YAML: {error}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(REPO)} must contain a mapping")
    return value


def join_receipt_identity_errors(join: dict[str, Any]) -> list[str]:
    planned = join.get("planned_slot_ids") or []
    slot_ids = [item.get("slot_id") for item in join.get("slot_receipts") or []]
    dispatch_ids = [item.get("slot_id") for item in join.get("dispatch_receipts") or []]
    errors: list[str] = []
    if slot_ids != planned:
        errors.append("slot_receipts do not match planned slots exactly once")
    if dispatch_ids != planned:
        errors.append("dispatch_receipts do not match planned slots exactly once")
    return errors


def cas_contiguous_errors(state: dict[str, Any]) -> list[str]:
    revision = state.get("state_revision")
    previous = state.get("previous_state_revision")
    if revision == 1:
        if previous is not None or state.get("previous_state_sha256") is not None:
            return ["revision 1 cannot cite a previous state"]
        return []
    if not isinstance(revision, int) or revision < 2:
        return []
    if previous != revision - 1:
        return ["previous_state_revision is not CAS-contiguous"]
    if not isinstance(state.get("previous_state_sha256"), str):
        return ["lacks previous_state_sha256"]
    return []


def current_state_contract_errors(state: dict[str, Any]) -> list[str]:
    errors = cas_contiguous_errors(state)
    pending = state.get("pending_action")
    action_id = state.get("pending_action_id")
    awaiting = state.get("awaiting_input")
    if pending == "NONE":
        if action_id is not None:
            errors.append("idle state cannot park a pending_action_id")
    elif not isinstance(action_id, str) or not action_id:
        errors.append("non-idle pending_action requires pending_action_id")
    if awaiting == "USER" and pending != "NONE":
        errors.append("awaiting_input=USER requires pending_action=NONE")
    if pending == "ASK_USER" and awaiting is not None:
        errors.append("ASK_USER is deliver-once; awaiting_input stays null until applied")
    wave_id = state.get("current_wave")
    if pending == "BLOCKER_RECOVERY" and isinstance(wave_id, int) and wave_id >= 20:
        errors.append("BLOCKER_RECOVERY is forbidden at wave cap")
    return errors


def validate_value(value: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
            for error in errors[:8]
        )
        fail(f"{label} violates schema: {details}")
    schema_id = str(schema.get("$id") or "")
    extra: list[str] = []
    if schema_id == "rkx-join-receipt-v1":
        extra = join_receipt_identity_errors(value)
    elif schema_id == "rkx-current-state-v1":
        extra = current_state_contract_errors(value)
    if extra:
        fail(f"{label} violates contract: {'; '.join(extra)}")


def frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path.relative_to(REPO)} lacks YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        fail(f"{path.relative_to(REPO)} has malformed frontmatter")
    try:
        value = yaml.safe_load(parts[1])
    except yaml.YAMLError as error:
        fail(f"{path.relative_to(REPO)} has invalid frontmatter: {error}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(REPO)} frontmatter must be a mapping")
    return value


def validate_static_control_plane() -> None:
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        metadata = frontmatter(path)
        if not metadata.get("name") or not metadata.get("description"):
            fail(f"{path.relative_to(REPO)} frontmatter requires name and description")

    for path in sorted((ROOT / "agents").glob("*.md")):
        frontmatter(path)

    orchestrator = ROOT / "agents" / "rkx-loop.md"
    merger = ROOT / "agents" / "merger.md"
    orchestrator_meta = frontmatter(orchestrator)
    if orchestrator_meta.get("readonly") is not True:
        fail("Orchestrator must declare readonly: true")
    orchestrator_text = orchestrator.read_text(encoding="utf-8")
    if "writes **zero** files" not in orchestrator_text and "writes zero files" not in orchestrator_text:
        fail("Orchestrator must explicitly own zero write paths")
    if "only** writer of shared run/wave artifacts" not in merger.read_text(encoding="utf-8"):
        fail("Merger must be the sole shared-state writer")

    codex_agents = [path for path in (ROOT / "agents").rglob("*") if path.is_file() and "codex" in path.name.lower()]
    if codex_agents:
        fail("CODEX agent files remain active: " + ", ".join(str(path.relative_to(REPO)) for path in codex_agents))

    settings_text = (ROOT / "settings.json").read_text(encoding="utf-8")
    if "codex" in settings_text.lower():
        fail("CODEX model routing remains in settings.json")

    hooks = read_json(ROOT / "hooks.json")
    stop_commands = [
        item.get("command")
        for item in hooks.get("hooks", {}).get("stop", [])
        if isinstance(item, dict)
    ]
    expected_hooks = {
        "bash .cursor/hooks/rkx-slack-notify.sh",
        "bash hooks/rkx-slack-notify.sh",
    }
    if not expected_hooks.intersection(stop_commands):
        fail("Slack exact-event stop hook is not connected in hooks.json")
    if not (ROOT / "hooks/rkx-slack-notify.sh").is_file():
        fail("Slack stop-hook command target is missing")

    active_text_paths = [
        *sorted((ROOT / "agents").glob("*.md")),
        *sorted((ROOT / "commands").glob("*.md")),
        *sorted((ROOT / "skills").glob("rkx-loop-*/SKILL.md")),
        ROOT / "CURSOR-UX.md",
        ROOT / "CURSOR-MODELS.md",
        ROOT / "RKX-LOOP-BLUEPRINT-FLOW.md",
        ROOT / "rules/rkx-loops.mdc",
        ROOT / "loops/RUN.md",
        ROOT / "loops/_registry.md",
    ]
    if "Never infer the next role from" not in orchestrator_text:
        fail("Orchestrator must not infer the next role from AcceptedDecision")
    stale_patterns = {
        r"1[–-]10 slots.*group": "per-group slot budget",
        r"ATTACK_PACKET": "legacy Advocate packet",
        r"SCHEME-OF-WORK": "live-only scheme path",
        r"loops/<run-id>/state\.md": "legacy current-state path",
        r"loops/<run-id>/slack-notification\.json": "legacy notification path",
        r"Manual Boss": "manual Boss checkpoint",
        r"REDISPATCH_EXACT_SLOT": "renamed REDISPATCH_SLOT",
        r"On accepted [`']?NEXT_WAVE_SPEC": "decision-inferred orchestrator routing",
        r"Controlling actions after gates": "decision/action conflation",
    }
    for path in active_text_paths:
        text = path.read_text(encoding="utf-8")
        for pattern, label in stale_patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                fail(f"{path.relative_to(REPO)} contains {label}")


def validate_contracts_and_fixtures() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for schema_path in sorted(PACKET_SCHEMAS.glob("*-v1.json")):
        schema = read_json(schema_path)
        Draft202012Validator.check_schema(schema)
        schemas[schema_path.name] = schema
        fixture_path = FIXTURES / "packets" / schema_path.name
        if not fixture_path.is_file():
            fail(f"missing fixture for {schema_path.name}")
        validate_value(read_json(fixture_path), schema, str(fixture_path.relative_to(REPO)))

    wave_schema = read_json(ROOT / "schemas" / "wave-spec-v1.json")
    preflight_schema = read_json(ROOT / "schemas" / "preflight-v1.json")
    Draft202012Validator.check_schema(wave_schema)
    Draft202012Validator.check_schema(preflight_schema)
    validate_value(read_json(FIXTURES / "wave-spec-v1.json"), wave_schema, "wave fixture")
    validate_value(read_json(FIXTURES / "preflight-v1.json"), preflight_schema, "preflight fixture")
    schemas["wave-spec-v1.json"] = wave_schema
    schemas["preflight-v1.json"] = preflight_schema
    return schemas


def validate_run(run_dir: Path, schemas: dict[str, dict[str, Any]]) -> None:
    state_path = run_dir / "state" / "current.yaml"
    state = read_yaml(state_path)
    validate_value(state, schemas["current-state-v1.json"], str(state_path.relative_to(REPO)))
    run_id = run_dir.name
    if state.get("run_id") != run_id:
        fail(f"{state_path.relative_to(REPO)} run_id must equal folder name")
    manifest_path = run_dir / "manifest.yaml"
    if not manifest_path.is_file():
        fail(f"{run_dir.relative_to(REPO)} lacks canonical manifest.yaml")
    manifest = read_yaml(manifest_path)
    if manifest.get("run_id") != run_id:
        fail(f"{manifest_path.relative_to(REPO)} run_id must equal folder name")
    manifest_required = {
        "run_id", "mode", "executor_mode", "token_mode",
        "billing_credential_scope", "continuation_policy",
        "implementation_authorized", "conversation_id", "correlation_id",
        "problem_title", "scope", "artifact_root", "state_pointer",
    }
    if manifest_required - set(manifest):
        fail(f"{manifest_path.relative_to(REPO)} is missing canonical manifest fields")
    if manifest.get("mode") not in {"ide", "auto"} or manifest.get("token_mode") != manifest.get("executor_mode"):
        fail(f"{manifest_path.relative_to(REPO)} has inconsistent execution mode")
    expected_billing = {
        "API": "API_CREDENTIALS",
        "CURSOR": "CURSOR_SUBSCRIPTION",
    }.get(manifest.get("executor_mode"))
    if manifest.get("billing_credential_scope") != expected_billing:
        fail(f"{manifest_path.relative_to(REPO)} has inconsistent billing scope")
    if manifest.get("artifact_root") != f"loops/{run_id}/" or manifest.get("state_pointer") != f"loops/{run_id}/state/current.yaml":
        fail(f"{manifest_path.relative_to(REPO)} has non-canonical artifact pointers")
    for field in ("conversation_id", "executor_mode", "continuation_policy", "implementation_authorized", "correlation_id"):
        if manifest.get(field) != state.get(field):
            fail(f"{manifest_path.relative_to(REPO)} disagrees with current state field {field}")

    proposal_by_id: dict[str, tuple[dict[str, Any], Path]] = {}
    advocate_by_proposal: dict[str, tuple[dict[str, Any], Path]] = {}
    decision_by_id: dict[str, tuple[dict[str, Any], Path]] = {}
    boss_packets: list[tuple[dict[str, Any], Path]] = []
    spec_by_wave: dict[int, dict[str, Any]] = {}
    specs_by_revision: dict[tuple[int, str], dict[str, Any]] = {}
    recovery_proposals: set[str] = set()

    for wave_dir in sorted(run_dir.glob("wave-*")):
        match = re.fullmatch(r"wave-(\d+)", wave_dir.name)
        if not match:
            continue
        wave_id = int(match.group(1))
        if not 1 <= wave_id <= 20:
            fail(f"{wave_dir.relative_to(REPO)} exceeds wave cap 20")
        if (wave_dir / "spec.yaml").is_file() or (wave_dir / "preflight.yaml").is_file():
            fail(f"{wave_dir.relative_to(REPO)} still uses singleton spec.yaml/preflight.yaml")
        spec_files = sorted((wave_dir / "specs").glob("*.yaml"))
        if not spec_files:
            fail(f"canonical run wave lacks specs/: {wave_dir.relative_to(REPO)}")
        wave_specs: list[dict[str, Any]] = []
        for spec_path in spec_files:
            spec = read_yaml(spec_path)
            validate_value(spec, schemas["wave-spec-v1.json"], str(spec_path.relative_to(REPO)))
            if spec.get("run_id") != run_id or spec.get("wave_id") != wave_id:
                fail(f"{spec_path.relative_to(REPO)} identity does not match its path")
            if spec_path.name != revision_filename(spec["revision_seq"]):
                fail(f"{spec_path.relative_to(REPO)} filename does not match revision_seq")
            slot_ids = [slot.get("slot_id") for slot in spec.get("slots", [])]
            hypothesis_ids = [item.get("hypothesis_id") for item in spec.get("hypotheses", [])]
            if len(slot_ids) != len(set(slot_ids)):
                fail(f"{spec_path.relative_to(REPO)} contains duplicate slot_id values")
            if len(hypothesis_ids) != len(set(hypothesis_ids)):
                fail(f"{spec_path.relative_to(REPO)} contains duplicate hypothesis_id values")
            if any(slot.get("hypothesis_id") not in set(hypothesis_ids) for slot in spec.get("slots", [])):
                fail(f"{spec_path.relative_to(REPO)} contains an orphan slot hypothesis")
            key = (wave_id, spec["spec_revision"])
            if key in specs_by_revision:
                fail(f"duplicate spec_revision {spec['spec_revision']} in wave {wave_id}")
            specs_by_revision[key] = spec
            if spec.get("kind") == "BLOCKER_RECOVERY_SPEC":
                if wave_id >= 20:
                    fail(f"{spec_path.relative_to(REPO)} BLOCKER_RECOVERY is forbidden at wave cap")
                proposal_id = spec.get("blocker_recovery_of_proposal_id")
                if proposal_id in recovery_proposals:
                    fail(f"BLOCKER_RECOVERY repeated for proposal_id {proposal_id}")
                recovery_proposals.add(str(proposal_id))
            wave_specs.append(spec)
        spec = max(wave_specs, key=lambda item: int(item["revision_seq"]))
        spec_by_wave[wave_id] = spec
        slot_ids = [slot.get("slot_id") for slot in spec.get("slots", [])]

        preflight_by_seq: dict[int, Path] = {}
        for preflight_path in sorted((wave_dir / "preflights").glob("*.yaml")):
            preflight = read_yaml(preflight_path)
            validate_value(preflight, schemas["preflight-v1.json"], str(preflight_path.relative_to(REPO)))
            if preflight_path.name != revision_filename(preflight["revision_seq"]):
                fail(f"{preflight_path.relative_to(REPO)} filename does not match revision_seq")
            matched_spec = next(
                (
                    item
                    for item in wave_specs
                    if item["revision_seq"] == preflight["revision_seq"]
                    and item["spec_revision"] == preflight["preflight_spec_revision"]
                ),
                None,
            )
            if (
                matched_spec is None
                or preflight.get("run_id") != run_id
                or preflight.get("wave_id") != wave_id
            ):
                fail(f"{preflight_path.relative_to(REPO)} does not reference its exact WaveSpec")
            matched_slot_ids = [slot.get("slot_id") for slot in matched_spec.get("slots", [])]
            preflight_ids = [slot.get("slot_id") for slot in preflight.get("slots", [])]
            if len(preflight_ids) != len(set(preflight_ids)) or set(preflight_ids) != set(matched_slot_ids):
                fail(f"{preflight_path.relative_to(REPO)} does not account for the exact planned slot set")
            preflight_by_seq[int(preflight["revision_seq"])] = preflight_path
        preflight_path = preflight_by_seq.get(int(spec["revision_seq"]))

        join_path = wave_dir / "join-receipt.yaml"
        if join_path.is_file():
            join = read_yaml(join_path)
            validate_value(join, schemas["join-receipt-v1.json"], str(join_path.relative_to(REPO)))
            join_spec = specs_by_revision.get((wave_id, join.get("spec_revision")))
            if join_spec is None:
                fail(f"{join_path.relative_to(REPO)} does not match a write-once WaveSpec revision")
            spec = join_spec
            spec_by_wave[wave_id] = spec
            preflight_path = preflight_by_seq.get(int(spec["revision_seq"]))
            planned = join.get("planned_slot_ids", [])
            accounted = join.get("accounted_slot_ids", [])
            spec_slots = [slot.get("slot_id") for slot in spec.get("slots", [])]
            if join.get("complete") is not True or planned != spec_slots or set(accounted) != set(planned) or len(accounted) != len(planned):
                fail(f"{join_path.relative_to(REPO)} does not account for every planned slot exactly once")
            slot_receipts = join.get("slot_receipts", [])
            dispatch_receipts = join.get("dispatch_receipts", [])
            if (
                [item.get("slot_id") for item in slot_receipts] != planned
                or [item.get("slot_id") for item in dispatch_receipts] != planned
            ):
                fail(f"{join_path.relative_to(REPO)} receipt arrays do not match planned slots exactly once")
            identity = {
                "run_id": run_id,
                "phase_id": spec.get("phase_id"),
                "wave_id": wave_id,
                "spec_revision": spec.get("spec_revision"),
                "correlation_id": spec.get("correlation_id"),
            }
            for receipt in [*slot_receipts, *dispatch_receipts]:
                if any(receipt.get(field) != value for field, value in identity.items()):
                    fail(f"{join_path.relative_to(REPO)} contains a receipt from another parent identity")
            dispatch_by_slot = {item["slot_id"]: item for item in dispatch_receipts}
            for receipt in slot_receipts:
                attempt_id = int(receipt["attempt_id"])
                expected_ref = slot_report_ref(run_id, wave_id, receipt["slot_id"], attempt_id)
                report_path = REPO / expected_ref
                if receipt.get("report_ref") != expected_ref or not report_path.is_file():
                    fail(f"{join_path.relative_to(REPO)} has a missing or non-canonical slot report")
                digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
                if digest.lower() != str(receipt.get("sha256", "")).lower():
                    fail(f"{join_path.relative_to(REPO)} slot report digest mismatch")
                report = frontmatter(report_path)
                validate_value(report, schemas["slot-report-v1.json"], str(report_path.relative_to(REPO)))
                slot = next(item for item in spec["slots"] if item["slot_id"] == receipt["slot_id"])
                if any(
                    report.get(field) != value
                    for field, value in {**identity, "slot_id": receipt["slot_id"], "attempt_id": attempt_id}.items()
                ):
                    fail(f"{report_path.relative_to(REPO)} frontmatter has the wrong parent identity")
                dispatch = dispatch_by_slot[receipt["slot_id"]]
                if dispatch.get("attempt_id") != attempt_id:
                    fail(f"{join_path.relative_to(REPO)} effective dispatch attempt_id disagrees with SlotReceipt")
                if (
                    report.get("hypothesis_id") != slot.get("hypothesis_id")
                    or report.get("status") != receipt.get("status")
                    or report.get("model") != receipt.get("model")
                ):
                    fail(f"{report_path.relative_to(REPO)} disagrees with its WaveSpec/SlotReceipt")
            if any(item.get("attempt_id", 0) > spec.get("max_slot_attempts", 0) for item in dispatch_receipts):
                fail(f"{join_path.relative_to(REPO)} exceeds max_slot_attempts")

        proposal_paths = sorted((wave_dir / "proposals").glob("*.yaml"))
        if proposal_paths and (preflight_path is None or not preflight_path.is_file() or not join_path.is_file()):
            fail(f"{wave_dir.relative_to(REPO)} has a Proposal without completed preflight and join")
        for proposal_path in proposal_paths:
            proposal = read_yaml(proposal_path)
            validate_value(proposal, schemas["proposal-v1.json"], str(proposal_path.relative_to(REPO)))
            if any(
                proposal.get(field) != spec.get(field)
                for field in ("run_id", "phase_id", "wave_id", "spec_revision", "correlation_id")
            ):
                fail(f"{proposal_path.relative_to(REPO)} does not match its WaveSpec identity")
            proposal_id = proposal["proposal_id"]
            if proposal_path.stem != proposal_id:
                fail(f"{proposal_path.relative_to(REPO)} filename does not match proposal_id")
            if proposal_id in proposal_by_id:
                fail(f"duplicate proposal_id {proposal_id}")
            proposal_by_id[proposal_id] = (proposal, proposal_path)
            if proposal.get("spec_revision") != spec.get("spec_revision"):
                fail(f"{proposal_path.relative_to(REPO)} has a stale parent spec_revision")

        for advocate_path in sorted((wave_dir / "advocate").glob("*.yaml")):
            advocate = read_yaml(advocate_path)
            validate_value(advocate, schemas["advocate-packet-v1.json"], str(advocate_path.relative_to(REPO)))
            if any(
                advocate.get(field) != spec.get(field)
                for field in ("run_id", "phase_id", "wave_id", "spec_revision", "correlation_id")
            ):
                fail(f"{advocate_path.relative_to(REPO)} does not match its WaveSpec identity")
            if advocate["proposal_id"] in advocate_by_proposal:
                fail(f"duplicate AdvocatePacket for proposal_id {advocate['proposal_id']}")
            if advocate_path.stem != advocate["proposal_id"]:
                fail(f"{advocate_path.relative_to(REPO)} filename does not match proposal_id")
            advocate_by_proposal[advocate["proposal_id"]] = (advocate, advocate_path)

    wave_ids = sorted(spec_by_wave)
    if wave_ids and wave_ids != list(range(1, wave_ids[-1] + 1)):
        fail(f"{run_dir.relative_to(REPO)} has a non-contiguous canonical wave sequence")
    current_wave = state.get("current_wave")
    if isinstance(current_wave, int) and current_wave > 0:
        current_spec = specs_by_revision.get((current_wave, state.get("spec_revision")))
        if current_spec is None:
            fail(f"{state_path.relative_to(REPO)} does not point to its current WaveSpec revision")
        expected_spec_ref = spec_ref(run_id, current_wave, current_spec["revision_seq"])
        if state.get("spec_ref") != expected_spec_ref:
            fail(f"{state_path.relative_to(REPO)} spec_ref is not the exact active WaveSpec path")
        expected_preflight_ref = preflight_ref(run_id, current_wave, current_spec["revision_seq"])
        if state.get("preflight_ref") != expected_preflight_ref:
            fail(f"{state_path.relative_to(REPO)} preflight_ref is not the exact active preflight path")

    if state.get("state_revision") == 1:
        if state.get("previous_state_revision") is not None or state.get("previous_state_sha256") is not None:
            fail(f"{state_path.relative_to(REPO)} revision 1 cannot cite a previous state")
    else:
        if state.get("previous_state_revision") != int(state["state_revision"]) - 1:
            fail(f"{state_path.relative_to(REPO)} previous_state_revision is not CAS-contiguous")
        if not isinstance(state.get("previous_state_sha256"), str):
            fail(f"{state_path.relative_to(REPO)} lacks previous_state_sha256")

    for proposal_path in sorted(run_dir.glob("checkpoints/*/proposals/*.yaml")):
        proposal = read_yaml(proposal_path)
        validate_value(proposal, schemas["proposal-v1.json"], str(proposal_path.relative_to(REPO)))
        checkpoint_dir = proposal_path.parent.parent
        if checkpoint_dir.name not in {"10", "20"}:
            fail(f"{proposal_path.relative_to(REPO)} is outside checkpoint 10/20")
        checkpoint = int(checkpoint_dir.name)
        if (
            proposal.get("wave_id") != checkpoint
            or proposal_path.stem != proposal.get("proposal_id")
            or not (checkpoint_dir / "boss.yaml").is_file()
        ):
            fail(f"{proposal_path.relative_to(REPO)} lacks its exact Boss checkpoint parent")
        spec = spec_by_wave.get(checkpoint)
        if spec is None or any(
            proposal.get(field) != spec.get(field)
            for field in ("run_id", "phase_id", "wave_id", "spec_revision", "correlation_id")
        ):
            fail(f"{proposal_path.relative_to(REPO)} does not match its checkpoint WaveSpec identity")
        if proposal["proposal_id"] in proposal_by_id:
            fail(f"duplicate proposal_id {proposal['proposal_id']}")
        proposal_by_id[proposal["proposal_id"]] = (proposal, proposal_path)
    for boss_path in sorted(run_dir.glob("checkpoints/*/boss.yaml")):
        boss = read_yaml(boss_path)
        validate_value(boss, schemas["boss-packet-v1.json"], str(boss_path.relative_to(REPO)))
        if str(boss["checkpoint"]) != boss_path.parent.name:
            fail(f"{boss_path.relative_to(REPO)} checkpoint does not match its path")
        spec = spec_by_wave.get(boss["checkpoint"])
        if spec is None or any(
            boss.get(field) != spec.get(field)
            for field in ("run_id", "phase_id", "wave_id", "spec_revision", "correlation_id")
        ):
            fail(f"{boss_path.relative_to(REPO)} does not match its checkpoint WaveSpec identity")
        boss_packets.append((boss, boss_path))

    for decision_path in sorted((run_dir / "decisions").glob("*.yaml")):
        decision = read_yaml(decision_path)
        validate_value(decision, schemas["accepted-decision-v1.json"], str(decision_path.relative_to(REPO)))
        decision_id = decision["decision_id"]
        if decision_path.stem != decision_id:
            fail(f"{decision_path.relative_to(REPO)} filename does not match decision_id")
        if decision_id in decision_by_id:
            fail(f"duplicate decision_id {decision_id}")
        decision_by_id[decision_id] = (decision, decision_path)
        if decision["proposal_id"] not in proposal_by_id:
            fail(f"{decision_path.relative_to(REPO)} references a missing proposal")
        proposal, _ = proposal_by_id[decision["proposal_id"]]
        if any(
            decision.get(field) != proposal.get(field)
            for field in ("run_id", "phase_id", "wave_id", "spec_revision", "correlation_id")
        ):
            fail(f"{decision_path.relative_to(REPO)} does not match its Proposal identity")
        if decision["action"] != proposal["candidate_action"]:
            fail(f"{decision_path.relative_to(REPO)} changes the settled Proposal action")
        proposal_path = proposal_by_id[decision["proposal_id"]][1]
        expected_origin = "BOSS_CHECKPOINT" if "checkpoints" in proposal_path.parts else "POST_WAVE"
        if decision["origin"] != expected_origin:
            fail(f"{decision_path.relative_to(REPO)} origin disagrees with its Proposal path")
        if decision["proposal_id"] not in advocate_by_proposal:
            fail(f"{decision_path.relative_to(REPO)} has no persisted AdvocatePacket")
        advocate = advocate_by_proposal[decision["proposal_id"]][0]
        if (
            decision["advocate_verdict"] != advocate["verdict"]
            or decision["advocate_material"] != advocate["material"]
        ):
            fail(f"{decision_path.relative_to(REPO)} disagrees with its AdvocatePacket")

    accepted_proposals = [decision[0]["proposal_id"] for decision in decision_by_id.values()]
    if len(accepted_proposals) != len(set(accepted_proposals)):
        fail(f"{run_dir.relative_to(REPO)} accepts the same proposal more than once")

    post_wave_by_wave: dict[int, list[dict[str, Any]]] = {}
    for decision, _ in decision_by_id.values():
        if decision["origin"] == "POST_WAVE":
            post_wave_by_wave.setdefault(decision["wave_id"], []).append(decision)
    required_completed_waves = set(range(1, int(state.get("current_wave", 0))))
    if state.get("pending_action") in {"CALL_BOSS", "DELIVER", "CALL_IMPLEMENTER", "VALIDATE_IMPLEMENTATION", "ASK_USER", "NONE"} and state.get("investigation_status") in {
        "PAUSED_AFTER_WAVE", "WAITING_USER", "BLOCKED", "CONCLUDED"
    } | ({"ACTIVE"} if state.get("pending_action") == "CALL_BOSS" else set()):
        required_completed_waves.add(int(state.get("current_wave", 0)))
    for wave_id in sorted(required_completed_waves - {0}):
        if len(post_wave_by_wave.get(wave_id, [])) != 1:
            fail(f"{run_dir.relative_to(REPO)} wave {wave_id} lacks exactly one accepted POST_WAVE decision")

    for boss, boss_path in boss_packets:
        opening = decision_by_id.get(boss["checkpoint_decision_id"])
        if opening is None:
            fail(f"{boss_path.relative_to(REPO)} references a missing checkpoint decision")
        opening_decision = opening[0]
        if not (
            opening_decision["origin"] == "POST_WAVE"
            and opening_decision["wave_id"] == boss["checkpoint"]
            and opening_decision["action"] == "NEXT_WAVE_SPEC"
            and opening_decision["route_action"] == "CALL_BOSS"
        ):
            fail(f"{boss_path.relative_to(REPO)} was not opened by the required post-wave NEXT decision")

    latest_decision_id = state.get("latest_decision_id")
    if latest_decision_id and latest_decision_id not in decision_by_id:
        fail(f"{state_path.relative_to(REPO)} references a missing accepted decision")
    if latest_decision_id:
        latest_decision = decision_by_id[latest_decision_id][0]
        expected_status = {
            "END": "CONCLUDED",
            "HARD_BLOCKER": "BLOCKED",
        }.get(latest_decision["action"])
        if latest_decision["action"] == "NEXT_WAVE_SPEC" and latest_decision["route_action"] == "DELIVER":
            expected_status = "PAUSED_AFTER_WAVE"
        if latest_decision["route_action"] == "ASK_USER":
            expected_status = "WAITING_USER"
        if expected_status and state.get("investigation_status") != expected_status:
            fail(f"{state_path.relative_to(REPO)} status disagrees with its latest accepted decision")
    latest_proposal_id = state.get("latest_proposal_id")
    if latest_proposal_id and latest_proposal_id not in proposal_by_id:
        fail(f"{state_path.relative_to(REPO)} references a missing Proposal")

    if state.get("pending_action") == "CALL_BOSS":
        wave_id = state["current_wave"]
        if not any(
            decision[0]["origin"] == "POST_WAVE"
            and decision[0]["wave_id"] == wave_id
            and decision[0]["action"] == "NEXT_WAVE_SPEC"
            and decision[0]["route_action"] == "CALL_BOSS"
            for decision in decision_by_id.values()
        ):
            fail(f"{state_path.relative_to(REPO)} requests Boss without an opening post-wave NEXT decision")

    if any(wave_id >= 11 for wave_id in wave_ids):
        checkpoint_10 = [
            item[0]
            for item in decision_by_id.values()
            if item[0]["origin"] == "BOSS_CHECKPOINT" and item[0]["wave_id"] == 10
        ]
        if not (run_dir / "checkpoints/10/boss.yaml").is_file() or not any(
            item["action"] == "NEXT_WAVE_SPEC" and item["route_action"] == "PREFLIGHT"
            for item in checkpoint_10
        ):
            fail(f"{run_dir.relative_to(REPO)} entered wave 11 without a settled checkpoint 10")

    if state.get("checkpoint_20_completed"):
        checkpoint_20 = [
            item[0]
            for item in decision_by_id.values()
            if item[0]["origin"] == "BOSS_CHECKPOINT" and item[0]["wave_id"] == 20
        ]
        if not (run_dir / "checkpoints/20/boss.yaml").is_file() or not checkpoint_20:
            fail(f"{run_dir.relative_to(REPO)} marks checkpoint 20 complete without its Boss settlement")

    for phase_dir in sorted((run_dir / "implementation").glob("*")):
        request_path = phase_dir / "request.yaml"
        request: dict[str, Any] | None = None
        if request_path.is_file():
            request = read_yaml(request_path)
            validate_value(request, schemas["implementation-request-v1.json"], str(request_path.relative_to(REPO)))
            if request.get("run_id") != run_id or request.get("phase_id") != phase_dir.name:
                fail(f"{request_path.relative_to(REPO)} identity does not match its path")
            accepted = decision_by_id.get(request.get("decision_id"))
            if (
                not state.get("implementation_authorized")
                or accepted is None
                or accepted[0].get("action") != "END"
                or any(
                    request.get(field) != accepted[0].get(field)
                    for field in ("run_id", "phase_id", "wave_id", "spec_revision", "correlation_id")
                )
            ):
                fail(f"{request_path.relative_to(REPO)} is not authorized by its accepted END")
        receipt_path = phase_dir / "receipt.yaml"
        if receipt_path.is_file():
            receipt = read_yaml(receipt_path)
            validate_value(receipt, schemas["implementation-receipt-v1.json"], str(receipt_path.relative_to(REPO)))
            if receipt.get("run_id") != run_id or receipt.get("phase_id") != phase_dir.name:
                fail(f"{receipt_path.relative_to(REPO)} identity does not match its path")
            if request is None or any(
                receipt.get(field) != request.get(field)
                for field in ("run_id", "phase_id", "wave_id", "spec_revision", "decision_id", "correlation_id")
            ):
                fail(f"{receipt_path.relative_to(REPO)} has no exact ImplementationRequest parent")
            report_path = REPO / str(receipt.get("report_ref", ""))
            expected_report = run_dir / "implementation" / phase_dir.name / "implementer-report.md"
            if report_path.resolve() != expected_report.resolve() or not report_path.is_file():
                fail(f"{receipt_path.relative_to(REPO)} has a missing/non-canonical implementation report")

    if state.get("pending_action") == "CALL_IMPLEMENTER":
        request_path = run_dir / "implementation" / str(state["phase_id"]) / "request.yaml"
        if not request_path.is_file():
            fail(f"{state_path.relative_to(REPO)} dispatches Implementer without ImplementationRequest")
    if latest_decision_id:
        latest = decision_by_id[latest_decision_id][0]
        request_path = run_dir / "implementation" / str(state["phase_id"]) / "request.yaml"
        if latest["action"] == "END" and state.get("implementation_authorized"):
            if state.get("implementation_status") == "NOT_REQUESTED" or not request_path.is_file():
                fail(f"{state_path.relative_to(REPO)} did not prepare automatic ImplementationRequest after authorized END")
        if latest["action"] == "END" and not state.get("implementation_authorized") and request_path.exists():
            fail(f"{state_path.relative_to(REPO)} prepared implementation for an analysis-only request")

    for lifecycle_path in sorted(run_dir.glob("deliveries/*/lifecycle.json")):
        lifecycle = read_json(lifecycle_path)
        validate_value(lifecycle, schemas["lifecycle-event-v1.json"], str(lifecycle_path.relative_to(REPO)))
        if lifecycle.get("run_id") != run_id or lifecycle.get("event_id") != lifecycle_path.parent.name:
            fail(f"{lifecycle_path.relative_to(REPO)} identity does not match its path")

    pending_event_id = state.get("pending_delivery_event_id")
    if pending_event_id:
        expected_ref = f"loops/{run_id}/deliveries/{pending_event_id}/lifecycle.json"
        if state.get("delivery_ref") != expected_ref or not (REPO / expected_ref).is_file():
            fail(f"{state_path.relative_to(REPO)} pending delivery pointer is not exact")

    if state.get("waiting_reason") == "WAVE_CAP":
        event_id = state.get("pending_delivery_event_id")
        expected_ref = f"loops/{run_id}/deliveries/{event_id}/lifecycle.json"
        if state.get("delivery_ref") != expected_ref:
            fail(f"{state_path.relative_to(REPO)} WAVE_CAP delivery_ref is not exact")
        lifecycle_path = REPO / expected_ref
        lifecycle = read_json(lifecycle_path)
        validate_value(lifecycle, schemas["lifecycle-event-v1.json"], str(lifecycle_path.relative_to(REPO)))
        if lifecycle.get("kind") != "wave_cap" or lifecycle.get("notification_type") != "attention":
            fail(f"{lifecycle_path.relative_to(REPO)} must be WAVE_CAP attention")
        if (
            state.get("pending_action") != "NONE"
            or state.get("awaiting_input") != "USER"
        ):
            fail(f"{state_path.relative_to(REPO)} WAVE_CAP must park awaiting_input=USER with pending_action=NONE")
        latest = decision_by_id.get(state.get("latest_decision_id"), ({}, Path()))[0]
        if not (
            latest.get("origin") == "BOSS_CHECKPOINT"
            and latest.get("wave_id") == 20
            and latest.get("action") == "NEXT_WAVE_SPEC"
            and latest.get("route_action") == "ASK_USER"
        ):
            fail(f"{state_path.relative_to(REPO)} WAVE_CAP lacks final Boss/Merger/Advocate NEXT settlement")

    if state.get("implementation_status") in {"VALIDATED", "FAILED"}:
        event_id = state.get("pending_delivery_event_id")
        expected_ref = f"loops/{run_id}/deliveries/{event_id}/lifecycle.json"
        if not event_id or state.get("delivery_ref") != expected_ref or not (REPO / expected_ref).is_file():
            fail(f"{state_path.relative_to(REPO)} implementation result lacks terminal DeliveryPacket")
        lifecycle = read_json(REPO / expected_ref)
        expected_kind = "completed" if state["implementation_status"] == "VALIDATED" else "failed"
        if lifecycle.get("kind") != expected_kind:
            fail(f"{(REPO / expected_ref).relative_to(REPO)} must close L2 as {expected_kind}")


def validate_canonical_runs(schemas: dict[str, dict[str, Any]]) -> int:
    loops_root = REPO / "loops"
    canonical = sorted(loops_root.glob("*/state/current.yaml")) if loops_root.is_dir() else []
    validated = 0
    for state_path in canonical:
        state = read_yaml(state_path)
        run_dir = state_path.parent.parent
        has_revisioned_specs = any(run_dir.glob("wave-*/specs/*.yaml"))
        if "state_revision" not in state:
            if has_revisioned_specs:
                fail(
                    f"{run_dir.relative_to(REPO)} uses revisioned specs/ "
                    "but current.yaml lacks state_revision"
                )
            continue
        if not has_revisioned_specs:
            continue
        validate_run(run_dir, schemas)
        validated += 1
    return validated


def main() -> int:
    validate_static_control_plane()
    schemas = validate_contracts_and_fixtures()
    run_count = validate_canonical_runs(schemas)
    print(f"PASS RKX contracts, fixtures, ownership, hooks, and {run_count} canonical run(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
