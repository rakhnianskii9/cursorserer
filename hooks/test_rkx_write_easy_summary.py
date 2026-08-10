#!/usr/bin/env python3
"""Tests for the safe terminal RKX easy-summary export."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

import rkx_write_easy_summary as summary  # noqa: E402


class EasySummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.run_id = "2026-08-08-rkx-fixture"
        self.run_dir = self.repo_root / "loops" / self.run_id
        self.run_dir.mkdir(parents=True)
        self.artifact_path = self.run_dir / "slack-notification.json"
        self.artifact = {
            "schema_version": 1,
            "conversation_id": "conversation-1",
            "event_id": "event-1",
            "run_id": self.run_id,
            "wave": "wave-1",
            "kind": "completed",
            "notification_type": "result",
            "problem_title": "Fixture scenario",
            "summary": "The fixture completed safely.",
            "full_verdict_available": False,
        }
        self.write_artifact()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_artifact(self) -> None:
        self.artifact_path.write_text(
            json.dumps(self.artifact),
            encoding="utf-8",
        )

    def test_completed_artifact_writes_compact_export(self) -> None:
        output = summary.process(
            {"conversationId": "conversation-1", "workspaceRoots": [str(self.repo_root)]}
        )

        self.assertEqual(output, self.run_dir / "easy-summarize.md")
        content = output.read_text(encoding="utf-8")
        self.assertIn("Fixture scenario", content)
        self.assertNotIn("## 5)", content)
        self.assertNotIn("Verdict", content)

    def test_waiting_user_does_not_write_terminal_export(self) -> None:
        self.artifact.update(
            {"kind": "waiting_user", "notification_type": "attention"}
        )
        self.write_artifact()

        output = summary.process(
            {"sessionId": "conversation-1", "workspace_roots": [str(self.repo_root)]}
        )

        self.assertIsNone(output)

    def test_capture_dir_is_explicit_and_workspace_bounded(self) -> None:
        capture_dir = self.repo_root / "rkx_capture_fixture"
        capture_dir.mkdir()
        self.artifact["capture_dir"] = "rkx_capture_fixture"
        self.write_artifact()

        output = summary.process(
            {"conversation_id": "conversation-1", "workspace_roots": [str(self.repo_root)]}
        )

        self.assertEqual(output, capture_dir / "easy-summarize.md")
        self.assertTrue(output.is_file())

    def test_decision_pointer_controls_recorded_metadata(self) -> None:
        decision_path = self.run_dir / "wave-1" / "merge.md"
        decision_path.parent.mkdir()
        decision_path.write_text(
            "root_confidence: 96%\nMODEL: Fixture Model\n",
            encoding="utf-8",
        )
        (self.run_dir / "latest-decision.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "run_id": self.run_id,
                    "decision_artifact": {
                        "path": f"loops/{self.run_id}/wave-1/merge.md",
                        "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                    },
                }
            ),
            encoding="utf-8",
        )

        output = summary.process(
            {"conversation_id": "conversation-1", "workspace_roots": [str(self.repo_root)]}
        )

        content = output.read_text(encoding="utf-8")
        self.assertIn("Recorded confidence: `96%`", content)
        self.assertIn("Recorded synthesis model: `Fixture Model`", content)

    def test_unknown_confidence_does_not_render_a_placeholder(self) -> None:
        output = summary.process(
            {"conversation_id": "conversation-1", "workspace_roots": [str(self.repo_root)]}
        )

        content = output.read_text(encoding="utf-8")
        self.assertNotIn("confidence", content.lower())
        self.assertNotIn("not provided", content)


if __name__ == "__main__":
    unittest.main()
