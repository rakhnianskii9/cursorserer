#!/usr/bin/env python3
"""Scenario tests for RKX wave-engine packet contracts."""

from __future__ import annotations

import json
import hashlib
import io
from contextlib import redirect_stdout
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(ROOT / "scripts"))

import rkx_lifecycle_common as lifecycle  # noqa: E402
import validate_rkx_loops as control_plane  # noqa: E402

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None


PACKETS = ROOT / "schemas" / "packets"
FIXTURES = ROOT / "scripts" / "fixtures" / "control-plane" / "packets"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_errors(schema_name: str, value: dict) -> list:
    assert Draft202012Validator is not None
    return list(
        Draft202012Validator(load_json(PACKETS / schema_name)).iter_errors(value)
    )


@unittest.skipIf(Draft202012Validator is None, "jsonschema not installed")
class PacketSchemaTests(unittest.TestCase):
    def test_all_packet_fixtures_validate(self) -> None:
        for schema_path in sorted(PACKETS.glob("*-v1.json")):
            fixture_path = FIXTURES / schema_path.name
            self.assertTrue(fixture_path.is_file(), schema_path.name)
            schema = load_json(schema_path)
            fixture = load_json(fixture_path)
            errors = list(Draft202012Validator(schema).iter_errors(fixture))
            self.assertEqual(errors, [], f"{schema_path.name}: {errors}")

    def test_accepted_decision_requires_advocate(self) -> None:
        fixture = load_json(FIXTURES / "accepted-decision-v1.json")
        fixture.pop("advocate_verdict")
        self.assertTrue(schema_errors("accepted-decision-v1.json", fixture))

    def test_material_advocate_hole_cannot_be_accepted(self) -> None:
        fixture = {
            **load_json(FIXTURES / "accepted-decision-v1.json"),
            "advocate_verdict": "HOLE",
            "advocate_material": True,
        }
        self.assertTrue(schema_errors("accepted-decision-v1.json", fixture))

    def test_accepted_decision_rejects_wave_21(self) -> None:
        fixture = {**load_json(FIXTURES / "accepted-decision-v1.json"), "wave_id": 21}
        self.assertTrue(schema_errors("accepted-decision-v1.json", fixture))

    def test_post_wave_10_next_routes_to_boss(self) -> None:
        fixture = {
            **load_json(FIXTURES / "accepted-decision-v1.json"),
            "wave_id": 10,
            "action": "NEXT_WAVE_SPEC",
            "route_action": "CALL_BOSS",
        }
        self.assertEqual(schema_errors("accepted-decision-v1.json", fixture), [])
        fixture["route_action"] = "PREFLIGHT"
        self.assertTrue(schema_errors("accepted-decision-v1.json", fixture))

    def test_checkpoint_10_next_routes_to_wave_11_preflight(self) -> None:
        fixture = {
            **load_json(FIXTURES / "accepted-decision-v1.json"),
            "wave_id": 10,
            "action": "NEXT_WAVE_SPEC",
            "origin": "BOSS_CHECKPOINT",
            "route_action": "PREFLIGHT",
        }
        self.assertEqual(schema_errors("accepted-decision-v1.json", fixture), [])

    def test_checkpoint_20_next_routes_to_waiting_user(self) -> None:
        fixture = {
            **load_json(FIXTURES / "accepted-decision-v1.json"),
            "wave_id": 20,
            "action": "NEXT_WAVE_SPEC",
            "origin": "BOSS_CHECKPOINT",
            "route_action": "ASK_USER",
        }
        self.assertEqual(schema_errors("accepted-decision-v1.json", fixture), [])
        fixture["route_action"] = "PREFLIGHT"
        self.assertTrue(schema_errors("accepted-decision-v1.json", fixture))

    def test_one_wave_policy_pauses_after_non_checkpoint_next(self) -> None:
        fixture = {
            **load_json(FIXTURES / "accepted-decision-v1.json"),
            "action": "NEXT_WAVE_SPEC",
            "continuation_policy": "ONE_WAVE",
            "route_action": "DELIVER",
        }
        self.assertEqual(schema_errors("accepted-decision-v1.json", fixture), [])
        fixture["route_action"] = "PREFLIGHT"
        self.assertTrue(schema_errors("accepted-decision-v1.json", fixture))

    def test_advocate_hole_requires_one_check(self) -> None:
        fixture = {
            **load_json(FIXTURES / "advocate-packet-v1.json"),
            "verdict": "HOLE",
            "material": True,
            "single_next_check": None,
        }
        self.assertTrue(schema_errors("advocate-packet-v1.json", fixture))

    def test_boss_checkpoint_must_match_wave(self) -> None:
        fixture = {**load_json(FIXTURES / "boss-packet-v1.json"), "wave_id": 20}
        self.assertTrue(schema_errors("boss-packet-v1.json", fixture))

    def test_preflight_decision_action_cannot_contradict_decision(self) -> None:
        fixture = {
            **load_json(FIXTURES / "preflight-decision-v1.json"),
            "action": "ASK_USER",
        }
        self.assertTrue(schema_errors("preflight-decision-v1.json", fixture))

    def test_request_envelope_rejects_two_run_identities(self) -> None:
        fixture = {
            **load_json(FIXTURES / "request-envelope-v1.json"),
            "run_id": "run-a",
            "resume_run_id": "run-b",
        }
        self.assertTrue(schema_errors("request-envelope-v1.json", fixture))

    def test_wave_cap_lifecycle_requires_attention_at_wave_20(self) -> None:
        fixture = {
            **load_json(FIXTURES / "lifecycle-event-v1.json"),
            "wave_id": 20,
            "kind": "wave_cap",
            "waiting_reason": "WAVE_CAP",
            "notification_type": "attention",
        }
        self.assertEqual(schema_errors("lifecycle-event-v1.json", fixture), [])
        fixture["notification_type"] = "result"
        self.assertTrue(schema_errors("lifecycle-event-v1.json", fixture))

    def test_one_wave_pause_has_nonterminal_chat_only_lifecycle(self) -> None:
        fixture = {
            **load_json(FIXTURES / "lifecycle-event-v1.json"),
            "kind": "wave_result",
            "notification_type": "result",
            "waiting_reason": None,
        }
        self.assertEqual(schema_errors("lifecycle-event-v1.json", fixture), [])
        self.assertIsNone(lifecycle.notification_type(fixture))

    def test_completed_checkpoint_20_cannot_dispatch(self) -> None:
        fixture = {
            **load_json(FIXTURES / "current-state-v1.json"),
            "current_wave": 20,
            "checkpoint_10_completed": True,
            "checkpoint_20_completed": True,
            "pending_action": "DISPATCH_WAVE",
            "pending_action_id": "action-dispatch",
        }
        self.assertTrue(schema_errors("current-state-v1.json", fixture))
        fixture["pending_action"] = "BLOCKER_RECOVERY"
        fixture["pending_action_id"] = "action-recovery"
        self.assertTrue(schema_errors("current-state-v1.json", fixture))


class WaveBudgetTests(unittest.TestCase):
    def test_wave_spec_rejects_wave_21(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        schema = load_json(ROOT / "schemas" / "wave-spec-v1.json")
        fixture = load_json(ROOT / "scripts" / "fixtures" / "control-plane" / "wave-spec-v1.json")
        invalid = {**fixture, "wave_id": 21}
        errors = list(Draft202012Validator(schema).iter_errors(invalid))
        self.assertTrue(errors)

    def test_wave_spec_caps_slots_at_10(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        schema = load_json(ROOT / "schemas" / "wave-spec-v1.json")
        fixture = load_json(ROOT / "scripts" / "fixtures" / "control-plane" / "wave-spec-v1.json")
        slot = fixture["slots"][0]
        invalid = {**fixture, "slots": [{**slot, "slot_id": f"S-{i}"} for i in range(11)]}
        errors = list(Draft202012Validator(schema).iter_errors(invalid))
        self.assertTrue(errors)

    def test_wave_spec_rejects_decision_kind(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        schema = load_json(ROOT / "schemas" / "wave-spec-v1.json")
        fixture = load_json(ROOT / "scripts" / "fixtures" / "control-plane" / "wave-spec-v1.json")
        invalid = {**fixture, "kind": "WAVE_DECISION", "decision_id": "too-early"}
        errors = list(Draft202012Validator(schema).iter_errors(invalid))
        self.assertTrue(errors)

    def test_preflight_rejects_orchestrator_resolution(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        schema = load_json(ROOT / "schemas" / "preflight-v1.json")
        fixture = load_json(ROOT / "scripts" / "fixtures" / "control-plane" / "preflight-v1.json")
        invalid = {**fixture, "orchestrator_resolution": "DISPATCH_READY"}
        errors = list(Draft202012Validator(schema).iter_errors(invalid))
        self.assertTrue(errors)

    def test_proposal_forbids_decision_id(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        schema = load_json(PACKETS / "proposal-v1.json")
        fixture = load_json(FIXTURES / "proposal-v1.json")
        invalid = {**fixture, "decision_id": "too-early"}
        errors = list(Draft202012Validator(schema).iter_errors(invalid))
        self.assertTrue(errors)


class ExactPointerTests(unittest.TestCase):
    def test_wave_cap_attention_uses_exact_event_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run_id = "12-08-26---19-00---wave-cap"
            run_dir = repo / "loops" / run_id
            event_id = "event-wave-cap-1"
            delivery = run_dir / "deliveries" / event_id
            delivery.mkdir(parents=True)
            (run_dir / "state").mkdir(parents=True)
            (run_dir / "state" / "current.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: 1",
                        f"run_id: {run_id}",
                        "conversation_id: conversation-wave-cap",
                        "investigation_status: WAITING_USER",
                        "waiting_reason: WAVE_CAP",
                        "current_wave: 20",
                        "wave_cap: 20",
                        f"pending_delivery_event_id: {event_id}",
                        f"delivery_ref: loops/{run_id}/deliveries/{event_id}/lifecycle.json",
                        "pending_action: NONE",
                        "awaiting_input: USER",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            artifact = {
                "schema_version": 1,
                "conversation_id": "conversation-wave-cap",
                "event_id": event_id,
                "run_id": run_id,
                "wave": "20",
                "kind": "wave_cap",
                "notification_type": "attention",
                "problem_title": "Wave cap",
                "summary": "Unresolved after checkpoint 20",
                "full_verdict_available": False,
            }
            path = delivery / "lifecycle.json"
            path.write_text(json.dumps(artifact), encoding="utf-8")

            # Decoy older/newer root artifact must not win via mtime.
            decoy = run_dir / "slack-notification.json"
            decoy.write_text(
                json.dumps({**artifact, "event_id": "decoy", "summary": "decoy"}),
                encoding="utf-8",
            )

            matched = lifecycle.artifact_by_exact_event(
                repo,
                "conversation-wave-cap",
                max_age_seconds=3600,
                predicate=lambda item: item.get("kind") == "wave_cap",
            )
            self.assertIsNotNone(matched)
            assert matched is not None
            matched_path, matched_artifact = matched
            self.assertEqual(matched_path, path.resolve())
            self.assertEqual(matched_artifact["event_id"], event_id)
            self.assertEqual(matched_artifact["notification_type"], "attention")

    def test_ambiguous_legacy_mtime_candidates_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for idx, run_id in enumerate(("run-a", "run-b")):
                run_dir = repo / "loops" / run_id
                run_dir.mkdir(parents=True)
                (run_dir / "slack-notification.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "conversation_id": "shared",
                            "event_id": f"event-{idx}",
                            "run_id": run_id,
                            "wave": "1",
                            "kind": "completed",
                            "notification_type": "result",
                            "problem_title": "x",
                            "summary": "y",
                            "full_verdict_available": False,
                        }
                    ),
                    encoding="utf-8",
                )
            matched = lifecycle.artifact_by_exact_event(
                repo,
                "shared",
                max_age_seconds=3600,
                predicate=lambda item: item.get("kind") == "completed",
            )
            self.assertIsNone(matched)

    def test_cross_run_delivery_ref_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_run = repo / "loops" / "run-a"
            event_run = repo / "loops" / "run-b"
            event_id = "event-cross-run"
            (state_run / "state").mkdir(parents=True)
            delivery = event_run / "deliveries" / event_id
            delivery.mkdir(parents=True)
            (state_run / "state" / "current.yaml").write_text(
                "\n".join(
                    [
                        "conversation_id: conversation-cross-run",
                        f"pending_delivery_event_id: {event_id}",
                        f"delivery_ref: loops/run-b/deliveries/{event_id}/lifecycle.json",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (delivery / "lifecycle.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "conversation_id": "conversation-cross-run",
                        "event_id": event_id,
                        "run_id": "run-b",
                        "kind": "wave_cap",
                        "notification_type": "attention",
                        "problem_title": "Cross-run pointer",
                        "summary": "Must not be selected",
                    }
                ),
                encoding="utf-8",
            )
            matched = lifecycle.artifact_by_exact_event(
                repo,
                "conversation-cross-run",
                max_age_seconds=3600,
                predicate=lambda item: item.get("kind") == "wave_cap",
            )
            self.assertIsNone(matched)


class ImplementationGateTests(unittest.TestCase):
    def test_analysis_only_envelope_not_authorized(self) -> None:
        fixture = load_json(FIXTURES / "request-envelope-v1.json")
        self.assertFalse(fixture["implementation_authorized"])

    def test_authorized_envelope_fixture_exists(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        schema = load_json(PACKETS / "request-envelope-v1.json")
        authorized = {
            **load_json(FIXTURES / "request-envelope-v1.json"),
            "implementation_authorized": True,
            "continuation_policy": "CONTINUOUS",
        }
        errors = list(Draft202012Validator(schema).iter_errors(authorized))
        self.assertEqual(errors, [])

    def test_analysis_only_state_cannot_dispatch_implementer(self) -> None:
        fixture = {
            **load_json(FIXTURES / "current-state-v1.json"),
            "pending_action": "CALL_IMPLEMENTER",
        }
        self.assertTrue(schema_errors("current-state-v1.json", fixture))

    def test_pre_authorized_end_dispatches_implementer(self) -> None:
        fixture = {
            **load_json(FIXTURES / "current-state-v1.json"),
            "implementation_authorized": True,
            "implementation_status": "AUTHORIZED",
            "pending_action": "CALL_IMPLEMENTER",
            "pending_action_id": "action-implement",
        }
        self.assertEqual(schema_errors("current-state-v1.json", fixture), [])


@unittest.skipIf(Draft202012Validator is None, "jsonschema not installed")
class CanonicalRunTests(unittest.TestCase):
    def test_complete_canonical_end_run_validates(self) -> None:
        loops_root = ROOT / "loops"
        loops_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".rkx-canonical-test-", dir=loops_root) as tmp:
            run_dir = Path(tmp)
            run_id = run_dir.name
            phase_id = "phase-1"
            revision = f"{run_id}:wave-1:rev"
            correlation_id = "corr-canonical"
            proposal_id = "prop-canonical"
            decision_id = "dec-canonical"
            event_id = "event-canonical"

            def write(path: Path, value: dict) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

            manifest = {
                "run_id": run_id,
                "mode": "ide",
                "conversation_id": "conversation-canonical",
                "executor_mode": "CURSOR",
                "token_mode": "CURSOR",
                "billing_credential_scope": "CURSOR_SUBSCRIPTION",
                "continuation_policy": "CONTINUOUS",
                "implementation_authorized": False,
                "correlation_id": correlation_id,
                "problem_title": "Canonical fixture",
                "scope": "control-plane validation",
                "artifact_root": f"loops/{run_id}/",
                "state_pointer": f"loops/{run_id}/state/current.yaml",
            }
            write(run_dir / "manifest.yaml", manifest)

            wave = load_json(ROOT / "scripts/fixtures/control-plane/wave-spec-v1.json")
            wave.update(
                run_id=run_id,
                phase_id=phase_id,
                spec_revision=revision,
                correlation_id=correlation_id,
                token_mode="CURSOR",
                billing_credential_scope="CURSOR_SUBSCRIPTION",
            )
            wave["slots"][0]["correlation_refs"] = [run_id]
            write(run_dir / "wave-1/specs/0001.yaml", wave)

            report = run_dir / "wave-1/slots/CODE-1/attempts/1/report.md"
            report.parent.mkdir(parents=True)
            report_frontmatter = load_json(FIXTURES / "slot-report-v1.json")
            report_frontmatter.update(
                run_id=run_id,
                phase_id=phase_id,
                spec_revision=revision,
                correlation_id=correlation_id,
            )
            report.write_text(
                "---\n"
                + json.dumps(report_frontmatter, indent=2)
                + "\n---\n\n# Evidence\n\nCanonical fixture.\n",
                encoding="utf-8",
            )
            digest = hashlib.sha256(report.read_bytes()).hexdigest()

            preflight = load_json(ROOT / "scripts/fixtures/control-plane/preflight-v1.json")
            preflight.update(
                run_id=run_id,
                phase_id=phase_id,
                preflight_spec_revision=revision,
                correlation_id=correlation_id,
                token_mode="CURSOR",
                billing_credential_scope="CURSOR_SUBSCRIPTION",
            )
            write(run_dir / "wave-1/preflights/0001.yaml", preflight)

            join = load_json(FIXTURES / "join-receipt-v1.json")
            join.update(run_id=run_id, phase_id=phase_id, spec_revision=revision, correlation_id=correlation_id)
            for receipt in [*join["slot_receipts"], *join["dispatch_receipts"]]:
                receipt.update(run_id=run_id, phase_id=phase_id, spec_revision=revision, correlation_id=correlation_id)
            join["slot_receipts"][0]["report_ref"] = f"loops/{run_id}/wave-1/slots/CODE-1/attempts/1/report.md"
            join["slot_receipts"][0]["sha256"] = digest
            write(run_dir / "wave-1/join-receipt.yaml", join)

            proposal = load_json(FIXTURES / "proposal-v1.json")
            proposal.update(
                proposal_id=proposal_id,
                run_id=run_id,
                phase_id=phase_id,
                spec_revision=revision,
                correlation_id=correlation_id,
            )
            write(run_dir / f"wave-1/proposals/{proposal_id}.yaml", proposal)

            advocate = load_json(FIXTURES / "advocate-packet-v1.json")
            advocate.update(
                proposal_id=proposal_id,
                run_id=run_id,
                phase_id=phase_id,
                spec_revision=revision,
                correlation_id=correlation_id,
            )
            write(run_dir / f"wave-1/advocate/{proposal_id}.yaml", advocate)

            decision = load_json(FIXTURES / "accepted-decision-v1.json")
            decision.update(
                decision_id=decision_id,
                proposal_id=proposal_id,
                run_id=run_id,
                phase_id=phase_id,
                spec_revision=revision,
                correlation_id=correlation_id,
            )
            write(run_dir / f"decisions/{decision_id}.yaml", decision)

            lifecycle_event = load_json(FIXTURES / "lifecycle-event-v1.json")
            lifecycle_event.update(
                event_id=event_id,
                run_id=run_id,
                phase_id=phase_id,
                decision_id=decision_id,
                proposal_id=proposal_id,
                correlation_id=correlation_id,
                conversation_id="conversation-canonical",
            )
            write(run_dir / f"deliveries/{event_id}/lifecycle.json", lifecycle_event)

            state = load_json(FIXTURES / "current-state-v1.json")
            state.update(
                run_id=run_id,
                phase_id=phase_id,
                conversation_id="conversation-canonical",
                spec_revision=revision,
                correlation_id=correlation_id,
                latest_decision_id=decision_id,
                latest_proposal_id=proposal_id,
                pending_delivery_event_id=event_id,
                delivery_ref=f"loops/{run_id}/deliveries/{event_id}/lifecycle.json",
                executor_mode="CURSOR",
                continuation_policy="CONTINUOUS",
                spec_ref=f"loops/{run_id}/wave-1/specs/0001.yaml",
                preflight_ref=f"loops/{run_id}/wave-1/preflights/0001.yaml",
            )
            write(run_dir / "state/current.yaml", state)

            schemas = control_plane.validate_contracts_and_fixtures()
            control_plane.validate_run(run_dir, schemas)

            manifest["implementation_authorized"] = True
            write(run_dir / "manifest.yaml", manifest)
            state.update(
                implementation_authorized=True,
                implementation_status="AUTHORIZED",
                pending_action="CALL_IMPLEMENTER",
                pending_action_id="action-implement",
            )
            write(run_dir / "state/current.yaml", state)
            implementation_request = load_json(FIXTURES / "implementation-request-v1.json")
            implementation_request.update(
                run_id=run_id,
                phase_id=phase_id,
                wave_id=1,
                spec_revision=revision,
                decision_id=decision_id,
                artifact_refs=[f"loops/{run_id}/decisions/{decision_id}.yaml"],
                correlation_id=correlation_id,
            )
            write(run_dir / f"implementation/{phase_id}/request.yaml", implementation_request)
            control_plane.validate_run(run_dir, schemas)

            join["slot_receipts"][0]["sha256"] = "0" * 64
            write(run_dir / "wave-1/join-receipt.yaml", join)
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                control_plane.validate_run(run_dir, schemas)

    def test_twenty_wave_boss_chain_reaches_wave_cap_without_wave_21(self) -> None:
        loops_root = ROOT / "loops"
        loops_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".rkx-wave-cap-test-", dir=loops_root) as tmp:
            run_dir = Path(tmp)
            run_id = run_dir.name
            phase_id = "phase-1"
            correlation_id = "corr-wave-cap"

            def write(path: Path, value: dict) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

            write(
                run_dir / "manifest.yaml",
                {
                    "run_id": run_id,
                    "mode": "auto",
                    "conversation_id": "conversation-wave-cap",
                    "executor_mode": "CURSOR",
                    "token_mode": "CURSOR",
                    "billing_credential_scope": "CURSOR_SUBSCRIPTION",
                    "continuation_policy": "CONTINUOUS",
                    "implementation_authorized": False,
                    "correlation_id": correlation_id,
                    "problem_title": "Twenty-wave fixture",
                    "scope": "checkpoint routing",
                    "artifact_root": f"loops/{run_id}/",
                    "state_pointer": f"loops/{run_id}/state/current.yaml",
                },
            )

            revisions: dict[int, str] = {}
            for wave_id in range(1, 21):
                revision = f"{run_id}:wave-{wave_id}:rev"
                revisions[wave_id] = revision
                wave = load_json(ROOT / "scripts/fixtures/control-plane/wave-spec-v1.json")
                wave.update(
                    kind="BOOTSTRAP_WAVE_SPEC" if wave_id == 1 else "NEXT_WAVE_SPEC",
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=wave_id,
                    spec_revision=revision,
                    correlation_id=correlation_id,
                    token_mode="CURSOR",
                    billing_credential_scope="CURSOR_SUBSCRIPTION",
                )
                wave["slots"][0]["correlation_refs"] = [f"wave-{wave_id}"]
                write(run_dir / f"wave-{wave_id}/specs/0001.yaml", wave)

                report = run_dir / f"wave-{wave_id}/slots/CODE-1/attempts/1/report.md"
                report.parent.mkdir(parents=True)
                report_frontmatter = load_json(FIXTURES / "slot-report-v1.json")
                report_frontmatter.update(
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=wave_id,
                    spec_revision=revision,
                    correlation_id=correlation_id,
                    fact=f"Wave {wave_id} remains unresolved.",
                )
                report.write_text(
                    "---\n" + json.dumps(report_frontmatter, indent=2) + "\n---\n\n# Evidence\n\nBounded fixture.\n",
                    encoding="utf-8",
                )
                digest = hashlib.sha256(report.read_bytes()).hexdigest()

                preflight = load_json(ROOT / "scripts/fixtures/control-plane/preflight-v1.json")
                preflight.update(
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=wave_id,
                    preflight_spec_revision=revision,
                    correlation_id=correlation_id,
                    token_mode="CURSOR",
                    billing_credential_scope="CURSOR_SUBSCRIPTION",
                )
                write(run_dir / f"wave-{wave_id}/preflights/0001.yaml", preflight)

                join = load_json(FIXTURES / "join-receipt-v1.json")
                join.update(
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=wave_id,
                    spec_revision=revision,
                    correlation_id=correlation_id,
                )
                for receipt in [*join["slot_receipts"], *join["dispatch_receipts"]]:
                    receipt.update(
                        run_id=run_id,
                        phase_id=phase_id,
                        wave_id=wave_id,
                        spec_revision=revision,
                        correlation_id=correlation_id,
                    )
                join["slot_receipts"][0]["report_ref"] = (
                    f"loops/{run_id}/wave-{wave_id}/slots/CODE-1/attempts/1/report.md"
                )
                join["slot_receipts"][0]["sha256"] = digest
                write(run_dir / f"wave-{wave_id}/join-receipt.yaml", join)

                proposal_id = f"prop-wave-{wave_id}"
                proposal = load_json(FIXTURES / "proposal-v1.json")
                proposal.update(
                    proposal_id=proposal_id,
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=wave_id,
                    spec_revision=revision,
                    correlation_id=correlation_id,
                    candidate_action="NEXT_WAVE_SPEC",
                )
                write(run_dir / f"wave-{wave_id}/proposals/{proposal_id}.yaml", proposal)

                advocate = load_json(FIXTURES / "advocate-packet-v1.json")
                advocate.update(
                    proposal_id=proposal_id,
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=wave_id,
                    spec_revision=revision,
                    correlation_id=correlation_id,
                )
                write(run_dir / f"wave-{wave_id}/advocate/{proposal_id}.yaml", advocate)

                decision_id = f"dec-wave-{wave_id}"
                decision = load_json(FIXTURES / "accepted-decision-v1.json")
                decision.update(
                    decision_id=decision_id,
                    proposal_id=proposal_id,
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=wave_id,
                    spec_revision=revision,
                    correlation_id=correlation_id,
                    action="NEXT_WAVE_SPEC",
                    origin="POST_WAVE",
                    route_action=(
                        "CALL_BOSS" if wave_id in {10, 20} else "PREFLIGHT"
                    ),
                )
                write(run_dir / f"decisions/{decision_id}.yaml", decision)

            checkpoint_decisions: dict[int, tuple[str, str]] = {}
            for checkpoint in (10, 20):
                revision = revisions[checkpoint]
                boss = load_json(FIXTURES / "boss-packet-v1.json")
                boss.update(
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=checkpoint,
                    spec_revision=revision,
                    checkpoint=checkpoint,
                    checkpoint_decision_id=f"dec-wave-{checkpoint}",
                    correlation_id=correlation_id,
                )
                write(run_dir / f"checkpoints/{checkpoint}/boss.yaml", boss)

                proposal_id = f"prop-checkpoint-{checkpoint}"
                proposal = load_json(FIXTURES / "proposal-v1.json")
                proposal.update(
                    proposal_id=proposal_id,
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=checkpoint,
                    spec_revision=revision,
                    correlation_id=correlation_id,
                    candidate_action="NEXT_WAVE_SPEC",
                )
                write(
                    run_dir / f"checkpoints/{checkpoint}/proposals/{proposal_id}.yaml",
                    proposal,
                )

                advocate = load_json(FIXTURES / "advocate-packet-v1.json")
                advocate.update(
                    proposal_id=proposal_id,
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=checkpoint,
                    spec_revision=revision,
                    correlation_id=correlation_id,
                )
                write(run_dir / f"wave-{checkpoint}/advocate/{proposal_id}.yaml", advocate)

                decision_id = f"dec-checkpoint-{checkpoint}"
                decision = load_json(FIXTURES / "accepted-decision-v1.json")
                decision.update(
                    decision_id=decision_id,
                    proposal_id=proposal_id,
                    run_id=run_id,
                    phase_id=phase_id,
                    wave_id=checkpoint,
                    spec_revision=revision,
                    correlation_id=correlation_id,
                    action="NEXT_WAVE_SPEC",
                    origin="BOSS_CHECKPOINT",
                    route_action="PREFLIGHT" if checkpoint == 10 else "ASK_USER",
                )
                write(run_dir / f"decisions/{decision_id}.yaml", decision)
                checkpoint_decisions[checkpoint] = (proposal_id, decision_id)

            final_proposal_id, final_decision_id = checkpoint_decisions[20]
            event_id = "event-wave-cap"
            lifecycle_event = load_json(FIXTURES / "lifecycle-event-v1.json")
            lifecycle_event.update(
                event_id=event_id,
                run_id=run_id,
                phase_id=phase_id,
                wave_id=20,
                kind="wave_cap",
                notification_type="attention",
                waiting_reason="WAVE_CAP",
                decision_id=final_decision_id,
                proposal_id=final_proposal_id,
                correlation_id=correlation_id,
                conversation_id="conversation-wave-cap",
                summary="Unresolved after final checkpoint 20.",
            )
            write(run_dir / f"deliveries/{event_id}/lifecycle.json", lifecycle_event)

            state = load_json(FIXTURES / "current-state-v1.json")
            state.update(
                run_id=run_id,
                phase_id=phase_id,
                conversation_id="conversation-wave-cap",
                investigation_status="WAITING_USER",
                current_wave=20,
                spec_revision=revisions[20],
                correlation_id=correlation_id,
                checkpoint_10_completed=True,
                checkpoint_20_completed=True,
                pending_action="NONE",
                awaiting_input="USER",
                pending_action_id=None,
                waiting_reason="WAVE_CAP",
                latest_decision_id=final_decision_id,
                latest_proposal_id=final_proposal_id,
                pending_delivery_event_id=event_id,
                delivery_ref=f"loops/{run_id}/deliveries/{event_id}/lifecycle.json",
                executor_mode="CURSOR",
                spec_ref=f"loops/{run_id}/wave-20/specs/0001.yaml",
                preflight_ref=f"loops/{run_id}/wave-20/preflights/0001.yaml",
                continuation_policy="CONTINUOUS",
            )
            write(run_dir / "state/current.yaml", state)

            schemas = control_plane.validate_contracts_and_fixtures()
            control_plane.validate_run(run_dir, schemas)
            self.assertFalse((run_dir / "wave-21").exists())


class ProtocolHoleTests(unittest.TestCase):
    def test_stale_state_transition_is_rejected(self) -> None:
        current = load_json(FIXTURES / "current-state-v1.json")
        nxt = {**current, "state_revision": 2, "previous_state_revision": 1, "previous_state_sha256": "a" * 64}
        with self.assertRaises(control_plane.StaleTransition):
            control_plane.apply_state_cas(current, expected_state_revision=99, next_state=nxt)
        applied = control_plane.apply_state_cas(current, expected_state_revision=1, next_state=nxt)
        self.assertEqual(applied["state_revision"], 2)

    def test_controller_action_redispatch_requires_attempt_identity(self) -> None:
        fixture = load_json(FIXTURES / "controller-action-v1.json")
        invalid = {**fixture, "action": "REDISPATCH_SLOT", "slot_id": None, "attempt_id": None}
        self.assertTrue(schema_errors("controller-action-v1.json", invalid))
        valid = {
            **fixture,
            "action": "REDISPATCH_SLOT",
            "slot_id": "CODE-1",
            "attempt_id": 2,
        }
        self.assertEqual(schema_errors("controller-action-v1.json", valid), [])

    def test_blocker_recovery_spec_is_single_slot_and_bound_to_proposal(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        schema = load_json(ROOT / "schemas" / "wave-spec-v1.json")
        fixture = load_json(ROOT / "scripts" / "fixtures" / "control-plane" / "wave-spec-v1.json")
        recovery = {
            **fixture,
            "kind": "BLOCKER_RECOVERY_SPEC",
            "revision_seq": 2,
            "blocker_recovery_of_proposal_id": "prop-1",
        }
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(recovery)), [])
        recovery.pop("blocker_recovery_of_proposal_id")
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(recovery)))
        at_cap = {
            **fixture,
            "kind": "BLOCKER_RECOVERY_SPEC",
            "wave_id": 20,
            "revision_seq": 2,
            "blocker_recovery_of_proposal_id": "prop-1",
        }
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(at_cap)))
        optional = {
            **fixture,
            "kind": "BLOCKER_RECOVERY_SPEC",
            "revision_seq": 2,
            "blocker_recovery_of_proposal_id": "prop-1",
            "slots": [{**fixture["slots"][0], "requirement": "OPTIONAL"}],
        }
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(optional)))

    def test_late_attempt_cannot_reuse_effective_report_path(self) -> None:
        receipt = load_json(FIXTURES / "slot-receipt-v1.json")
        self.assertEqual(
            receipt["report_ref"],
            "loops/fixture-run/wave-1/slots/CODE-1/attempts/1/report.md",
        )
        second = {
            **receipt,
            "attempt_id": 2,
            "report_ref": "loops/fixture-run/wave-1/slots/CODE-1/attempts/2/report.md",
        }
        self.assertNotEqual(receipt["report_ref"], second["report_ref"])
        self.assertEqual(schema_errors("slot-receipt-v1.json", second), [])
        stale = {
            **receipt,
            "attempt_id": 2,
            "report_ref": "loops/fixture-run/wave-1/slots/CODE-1/report.md",
        }
        self.assertTrue(schema_errors("slot-receipt-v1.json", stale))
        join = load_json(FIXTURES / "join-receipt-v1.json")
        nested_stale = {
            **join,
            "slot_receipts": [{**join["slot_receipts"][0], **stale}],
        }
        self.assertTrue(schema_errors("join-receipt-v1.json", nested_stale))

    def test_replan_uses_new_revision_seq_path(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        schema = load_json(ROOT / "schemas" / "wave-spec-v1.json")
        fixture = load_json(ROOT / "scripts" / "fixtures" / "control-plane" / "wave-spec-v1.json")
        revised = {**fixture, "revision_seq": 2, "spec_revision": "fixture-run:wave-1:rev2"}
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(revised)), [])
        self.assertEqual(control_plane.revision_filename(2), "0002.yaml")
        self.assertEqual(
            control_plane.spec_ref("fixture-run", 1, 2),
            "loops/fixture-run/wave-1/specs/0002.yaml",
        )

    def test_checkpoint_next_does_not_authorize_wave_dispatch(self) -> None:
        fixture = {
            **load_json(FIXTURES / "accepted-decision-v1.json"),
            "wave_id": 10,
            "action": "NEXT_WAVE_SPEC",
            "origin": "POST_WAVE",
            "route_action": "PREFLIGHT",
        }
        self.assertTrue(schema_errors("accepted-decision-v1.json", fixture))

    def test_validated_implementation_requires_product_met(self) -> None:
        fixture = {
            **load_json(FIXTURES / "current-state-v1.json"),
            "implementation_authorized": True,
            "implementation_status": "VALIDATED",
            "product_status": "UNKNOWN",
        }
        self.assertTrue(schema_errors("current-state-v1.json", fixture))
        valid = {
            **load_json(FIXTURES / "current-state-v1.json"),
            "implementation_authorized": True,
            "implementation_status": "VALIDATED",
            "product_status": "MET",
        }
        self.assertEqual(schema_errors("current-state-v1.json", valid), [])
        missing_delivery = {
            **valid,
            "pending_delivery_event_id": None,
            "delivery_ref": None,
        }
        self.assertTrue(schema_errors("current-state-v1.json", missing_delivery))

    def test_join_rejects_duplicate_slot_id(self) -> None:
        schema = load_json(PACKETS / "join-receipt-v1.json")
        join = load_json(FIXTURES / "join-receipt-v1.json")
        duplicate = {
            **join,
            "slot_receipts": [
                join["slot_receipts"][0],
                {
                    **join["slot_receipts"][0],
                    "attempt_id": 2,
                    "report_ref": "loops/fixture-run/wave-1/slots/CODE-1/attempts/2/report.md",
                },
            ],
        }
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            control_plane.validate_value(duplicate, schema, "join")

    def test_cas_rejects_noncontiguous_previous_revision(self) -> None:
        schema = load_json(PACKETS / "current-state-v1.json")
        fixture = {
            **load_json(FIXTURES / "current-state-v1.json"),
            "state_revision": 3,
            "previous_state_revision": 1,
            "previous_state_sha256": "a" * 64,
        }
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            control_plane.validate_value(fixture, schema, "state")

    def test_waiting_user_parks_awaiting_input_not_ask_user(self) -> None:
        parked = {
            **load_json(FIXTURES / "current-state-v1.json"),
            "investigation_status": "WAITING_USER",
            "current_wave": 20,
            "spec_revision": "fixture-run:wave-20:abc",
            "checkpoint_10_completed": True,
            "checkpoint_20_completed": True,
            "pending_action": "NONE",
            "awaiting_input": "USER",
            "waiting_reason": "WAVE_CAP",
            "spec_ref": "loops/fixture-run/wave-20/specs/0001.yaml",
            "preflight_ref": "loops/fixture-run/wave-20/preflights/0001.yaml",
            "product_status": "UNKNOWN",
        }
        self.assertEqual(schema_errors("current-state-v1.json", parked), [])
        replay = {**parked, "pending_action": "ASK_USER", "pending_action_id": "action-ask"}
        self.assertTrue(schema_errors("current-state-v1.json", replay))

    def test_pending_action_requires_action_id(self) -> None:
        fixture = {
            **load_json(FIXTURES / "current-state-v1.json"),
            "implementation_authorized": True,
            "implementation_status": "AUTHORIZED",
            "pending_action": "CALL_IMPLEMENTER",
            "pending_action_id": None,
        }
        self.assertTrue(schema_errors("current-state-v1.json", fixture))
        replay = {
            **fixture,
            "pending_action_id": "action-implement",
            "last_applied_action_id": "action-implement",
        }
        self.assertEqual(schema_errors("current-state-v1.json", replay), [])

    def test_blocker_recovery_controller_action_rejects_wave_20(self) -> None:
        fixture = load_json(FIXTURES / "controller-action-v1.json")
        valid = {
            **fixture,
            "action": "BLOCKER_RECOVERY",
            "wave_id": 19,
            "spec_revision": "fixture-run:wave-19:abc",
        }
        self.assertEqual(schema_errors("controller-action-v1.json", valid), [])
        invalid = {**valid, "wave_id": 20, "spec_revision": "fixture-run:wave-20:abc"}
        self.assertTrue(schema_errors("controller-action-v1.json", invalid))

    def test_leftover_singleton_spec_yaml_fails_validate_run(self) -> None:
        loops_root = ROOT / "loops"
        loops_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".rkx-singleton-test-", dir=loops_root) as tmp:
            run_dir = Path(tmp)
            run_id = run_dir.name

            def write(path: Path, value: dict) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

            state = load_json(FIXTURES / "current-state-v1.json")
            state.update(
                run_id=run_id,
                spec_ref=f"loops/{run_id}/wave-1/specs/0001.yaml",
                preflight_ref=f"loops/{run_id}/wave-1/preflights/0001.yaml",
                delivery_ref=f"loops/{run_id}/deliveries/event-1/lifecycle.json",
            )
            write(run_dir / "state/current.yaml", state)
            write(
                run_dir / "manifest.yaml",
                {
                    "run_id": run_id,
                    "mode": "ide",
                    "conversation_id": state["conversation_id"],
                    "executor_mode": "CURSOR",
                    "token_mode": "CURSOR",
                    "billing_credential_scope": "CURSOR_SUBSCRIPTION",
                    "continuation_policy": state["continuation_policy"],
                    "implementation_authorized": False,
                    "correlation_id": state["correlation_id"],
                    "problem_title": "Singleton leftover",
                    "scope": "control-plane validation",
                    "artifact_root": f"loops/{run_id}/",
                    "state_pointer": f"loops/{run_id}/state/current.yaml",
                },
            )
            leftover = run_dir / "wave-1/spec.yaml"
            leftover.parent.mkdir(parents=True, exist_ok=True)
            leftover.write_text("kind: leftover\n", encoding="utf-8")
            schemas = control_plane.validate_contracts_and_fixtures()
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                control_plane.validate_run(run_dir, schemas)

    def test_revisioned_specs_without_state_revision_fail_canonical_scan(self) -> None:
        loops_root = ROOT / "loops"
        loops_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".rkx-norev-test-", dir=loops_root) as tmp:
            run_dir = Path(tmp)
            (run_dir / "state").mkdir(parents=True)
            (run_dir / "state/current.yaml").write_text("run_id: x\n", encoding="utf-8")
            spec_dir = run_dir / "wave-1/specs"
            spec_dir.mkdir(parents=True)
            (spec_dir / "0001.yaml").write_text("kind: NEXT_WAVE_SPEC\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                control_plane.validate_canonical_runs({})

    def test_legacy_singleton_with_state_revision_is_skipped(self) -> None:
        loops_root = ROOT / "loops"
        loops_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".rkx-legacy-test-", dir=loops_root) as tmp:
            run_dir = Path(tmp)
            (run_dir / "state").mkdir(parents=True)
            (run_dir / "state/current.yaml").write_text(
                "state_revision: 1\nrun_id: legacy\n",
                encoding="utf-8",
            )
            leftover = run_dir / "wave-1/spec.yaml"
            leftover.parent.mkdir(parents=True)
            leftover.write_text("kind: leftover\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                validated = control_plane.validate_canonical_runs({})
            self.assertIsInstance(validated, int)

    def test_noncontiguous_cas_fails_validate_run(self) -> None:
        loops_root = ROOT / "loops"
        loops_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".rkx-cas-test-", dir=loops_root) as tmp:
            run_dir = Path(tmp)
            run_id = run_dir.name

            def write(path: Path, value: dict) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

            state = load_json(FIXTURES / "current-state-v1.json")
            state.update(
                run_id=run_id,
                current_wave=0,
                spec_revision=None,
                spec_ref=None,
                preflight_ref=None,
                investigation_status="BOOTSTRAP",
                state_revision=3,
                previous_state_revision=1,
                previous_state_sha256="a" * 64,
                latest_decision_id=None,
                latest_proposal_id=None,
                pending_delivery_event_id=None,
                delivery_ref=None,
            )
            write(run_dir / "state/current.yaml", state)
            write(
                run_dir / "manifest.yaml",
                {
                    "run_id": run_id,
                    "mode": "ide",
                    "conversation_id": state["conversation_id"],
                    "executor_mode": "CURSOR",
                    "token_mode": "CURSOR",
                    "billing_credential_scope": "CURSOR_SUBSCRIPTION",
                    "continuation_policy": state["continuation_policy"],
                    "implementation_authorized": False,
                    "correlation_id": state["correlation_id"],
                    "problem_title": "CAS hole",
                    "scope": "control-plane validation",
                    "artifact_root": f"loops/{run_id}/",
                    "state_pointer": f"loops/{run_id}/state/current.yaml",
                },
            )
            schemas = control_plane.validate_contracts_and_fixtures()
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                control_plane.validate_run(run_dir, schemas)

    def test_validated_without_delivery_file_fails_validate_run(self) -> None:
        loops_root = ROOT / "loops"
        loops_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".rkx-nodelivery-test-", dir=loops_root) as tmp:
            run_dir = Path(tmp)
            run_id = run_dir.name

            def write(path: Path, value: dict) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

            event_id = "event-missing"
            state = load_json(FIXTURES / "current-state-v1.json")
            state.update(
                run_id=run_id,
                current_wave=0,
                spec_revision=None,
                spec_ref=None,
                preflight_ref=None,
                investigation_status="CONCLUDED",
                implementation_authorized=True,
                implementation_status="VALIDATED",
                product_status="MET",
                latest_decision_id=None,
                latest_proposal_id=None,
                pending_delivery_event_id=event_id,
                delivery_ref=f"loops/{run_id}/deliveries/{event_id}/lifecycle.json",
            )
            write(run_dir / "state/current.yaml", state)
            write(
                run_dir / "manifest.yaml",
                {
                    "run_id": run_id,
                    "mode": "ide",
                    "conversation_id": state["conversation_id"],
                    "executor_mode": "CURSOR",
                    "token_mode": "CURSOR",
                    "billing_credential_scope": "CURSOR_SUBSCRIPTION",
                    "continuation_policy": state["continuation_policy"],
                    "implementation_authorized": True,
                    "correlation_id": state["correlation_id"],
                    "problem_title": "Missing delivery",
                    "scope": "control-plane validation",
                    "artifact_root": f"loops/{run_id}/",
                    "state_pointer": f"loops/{run_id}/state/current.yaml",
                },
            )
            schemas = control_plane.validate_contracts_and_fixtures()
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                control_plane.validate_run(run_dir, schemas)


if __name__ == "__main__":
    unittest.main()
