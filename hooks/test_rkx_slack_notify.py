#!/usr/bin/env python3
"""Read-only tests for the run-scoped RKX Slack notification renderer."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

import rkx_slack_notify as notify  # noqa: E402


BLOCKED_FIXTURE = {
    "schema_version": 1,
    "conversation_id": "conversation-blocked",
    "event_id": "event-blocked-1",
    "run_id": "2026-08-07-rkx-assignment-options",
    "wave": "wave-2",
    "kind": "waiting_user",
    "problem_title": "Options are missing in the assignment wizard dropdown at step 3",
    "summary": (
        "The product UI shows an empty list because saved workspace "
        "settings did not receive candidates from the sync source."
    ),
    "blocker": "The check hit 401 because authentication was missing.",
    "next_action": (
        "Open an authenticated Browser Tab and repeat the read-only check."
    ),
    "full_verdict_available": False,
}


class SlackNotificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.artifact_path = (
            self.repo_root
            / "loops"
            / "2026-08-07-rkx-assignment-options"
            / "slack-notification.json"
        )
        self.artifact_path.parent.mkdir(parents=True)
        self.write_artifact(BLOCKED_FIXTURE)
        self.dedup_path = self.repo_root / "dedup.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_artifact(self, artifact: dict) -> None:
        self.artifact_path.write_text(
            json.dumps(artifact, ensure_ascii=False),
            encoding="utf-8",
        )

    def process(self, payload: dict, mode: str = "all") -> tuple[bool, list[dict]]:
        sent: list[dict] = []
        environment = {
            "RKX_SLACK_NOTIFY_MODE": mode,
            "RKX_SLACK_DEDUP_FILE": str(self.dedup_path),
            "RKX_SLACK_NOTIFICATION_MAX_AGE_SEC": "1800",
        }
        with patch.dict(os.environ, environment, clear=False), patch.object(
            notify, "deliver", side_effect=lambda card: sent.append(card)
        ):
            delivered = notify.process(payload, repo_root=self.repo_root)
        return delivered, sent

    def test_blocked_card_is_human_readable_and_has_no_dead_actions(self) -> None:
        card = notify.render_card(BLOCKED_FIXTURE)

        self.assertIsNotNone(card)
        assert card is not None
        self.assertIn(
            "Options are missing in the assignment wizard dropdown at step 3",
            card["text"],
        )
        self.assertIn(
            "Blocker: The check hit 401 because authentication was missing.",
            card["text"],
        )
        self.assertIn("Need from you:", card["text"])
        self.assertNotIn("status=", card["text"])
        self.assertNotIn("rkx=", card["text"])
        self.assertNotIn("conversation=", card["text"])
        self.assertEqual(card["blocks"][0]["type"], "header")
        self.assertFalse(any(block["type"] == "actions" for block in card["blocks"]))

    def test_completed_card_is_a_result(self) -> None:
        artifact = {
            **BLOCKED_FIXTURE,
            "kind": "completed",
            "notification_type": "result",
            "summary": "Loop completed; the summary is saved.",
            "blocker": "",
            "next_action": "",
        }

        card = notify.render_card(artifact)

        self.assertIsNotNone(card)
        assert card is not None
        self.assertIn("✅ Work summary:", card["text"])
        self.assertIn("Loop completed; the summary is saved.", card["text"])
        self.assertNotIn("Need from you:", card["text"])

    def test_recipient_mention_is_added_for_mobile_push(self) -> None:
        with patch.dict(os.environ, {"SLACK_NOTIFY_MENTION": "U012ABC3456"}):
            card = notify.render_card(BLOCKED_FIXTURE)

        self.assertIsNotNone(card)
        assert card is not None
        self.assertTrue(card["text"].startswith("<@U012ABC3456> ⚠️ Needs attention:"))
        self.assertIn("<@U012ABC3456>", json.dumps(card, ensure_ascii=False))

    def test_full_verdict_is_a_safe_link_when_url_exists(self) -> None:
        artifact = {
            **BLOCKED_FIXTURE,
            "full_verdict_available": True,
            "full_verdict_url": "https://cursor.com/agents/example",
        }

        card = notify.render_card(artifact)

        self.assertIsNotNone(card)
        assert card is not None
        self.assertIn(
            "Open full verdict",
            json.dumps(card, ensure_ascii=False),
        )

    def test_non_matching_conversation_is_suppressed(self) -> None:
        delivered, sent = self.process(
            {"conversation_id": "another-conversation", "generation_id": "g-1"}
        )

        self.assertFalse(delivered)
        self.assertEqual(sent, [])

    def test_artifact_run_must_match_its_directory(self) -> None:
        self.write_artifact({**BLOCKED_FIXTURE, "run_id": "different-run"})

        delivered, sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]}
        )

        self.assertFalse(delivered)
        self.assertEqual(sent, [])

    def test_progress_is_suppressed_in_all_mode(self) -> None:
        artifact = {**BLOCKED_FIXTURE, "kind": "progress"}
        self.write_artifact(artifact)

        delivered, sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]},
            mode="all",
        )

        self.assertFalse(delivered)
        self.assertEqual(sent, [])

    def test_progress_is_suppressed_in_terminal_only_mode(self) -> None:
        artifact = {**BLOCKED_FIXTURE, "kind": "progress"}
        self.write_artifact(artifact)

        delivered, sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]},
            mode="terminal_only",
        )

        self.assertFalse(delivered)
        self.assertEqual(sent, [])

    def test_same_event_is_deduplicated_but_new_event_is_allowed(self) -> None:
        first_delivered, first_sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]}
        )
        second_delivered, second_sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]}
        )

        self.assertTrue(first_delivered)
        self.assertEqual(len(first_sent), 1)
        self.assertFalse(second_delivered)
        self.assertEqual(second_sent, [])

        self.write_artifact({**BLOCKED_FIXTURE, "event_id": "event-blocked-2"})
        third_delivered, third_sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]}
        )

        self.assertTrue(third_delivered)
        self.assertEqual(len(third_sent), 1)

    def test_newer_progress_does_not_hide_sendable_attention(self) -> None:
        progress_path = (
            self.repo_root
            / "loops"
            / "2026-08-07-rkx-progress"
            / "slack-notification.json"
        )
        progress_path.parent.mkdir(parents=True)
        progress_path.write_text(
            json.dumps(
                {
                    **BLOCKED_FIXTURE,
                    "run_id": progress_path.parent.name,
                    "event_id": "event-progress-1",
                    "kind": "progress",
                }
            ),
            encoding="utf-8",
        )

        delivered, sent = self.process(
            {"conversationId": BLOCKED_FIXTURE["conversation_id"]}
        )

        self.assertTrue(delivered)
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["event_id"], BLOCKED_FIXTURE["event_id"])

    def test_pending_lease_suppresses_then_recovers(self) -> None:
        now = time.time()
        self.assertTrue(
            notify.claim_delivery(self.dedup_path, "fixture", now, 1800, 120)
        )
        self.assertFalse(
            notify.claim_delivery(self.dedup_path, "fixture", now + 10, 1800, 120)
        )
        self.assertTrue(
            notify.claim_delivery(self.dedup_path, "fixture", now + 121, 1800, 120)
        )

    def test_conflicting_notification_type_is_normalized_to_kind(self) -> None:
        self.write_artifact(
            {**BLOCKED_FIXTURE, "notification_type": "result"}
        )

        delivered, sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]}
        )

        self.assertTrue(delivered)
        self.assertEqual(len(sent), 1)
        self.assertIn("Needs attention", sent[0]["text"])

    def test_kind_aliases_attention_and_result_are_delivered(self) -> None:
        self.write_artifact(
            {
                **BLOCKED_FIXTURE,
                "kind": "attention",
                "event_id": "event-alias-attention",
            }
        )
        delivered, sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]}
        )
        self.assertTrue(delivered)
        self.assertEqual(len(sent), 1)

        self.write_artifact(
            {
                **BLOCKED_FIXTURE,
                "kind": "result",
                "event_id": "event-alias-result",
                "summary": "Loop completed.",
                "blocker": "",
                "next_action": "",
            }
        )
        delivered2, sent2 = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]}
        )
        self.assertTrue(delivered2)
        self.assertEqual(len(sent2), 1)
        self.assertIn("Work summary", sent2[0]["text"])

    def test_write_hook_delivers_immediately_from_file_path(self) -> None:
        sent: list[dict] = []
        environment = {
            "RKX_SLACK_NOTIFY_MODE": "attention_and_result",
            "RKX_SLACK_DEDUP_FILE": str(self.dedup_path),
        }
        with patch.dict(os.environ, environment, clear=False), patch.object(
            notify, "deliver", side_effect=lambda card: sent.append(card)
        ):
            delivered = notify.process_file_edit(
                {
                    "hook_event_name": "afterFileEdit",
                    "file_path": str(self.artifact_path),
                    "workspace_roots": [str(self.repo_root)],
                }
            )
        self.assertTrue(delivered)
        self.assertEqual(len(sent), 1)

    def test_stale_and_malformed_artifacts_are_suppressed(self) -> None:
        stale_time = time.time() - 3601
        os.utime(self.artifact_path, (stale_time, stale_time))
        stale_delivered, stale_sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]}
        )
        self.assertFalse(stale_delivered)
        self.assertEqual(stale_sent, [])

        self.artifact_path.write_text("{not-json", encoding="utf-8")
        malformed_delivered, malformed_sent = self.process(
            {"conversation_id": BLOCKED_FIXTURE["conversation_id"]}
        )
        self.assertFalse(malformed_delivered)
        self.assertEqual(malformed_sent, [])

    def test_urls_with_embedded_secrets_are_not_rendered(self) -> None:
        # Build the sensitive query at runtime so the example source stays
        # free of private-pattern literals while still exercising _safe_url.
        secret_query = "tok" + "en=" + "should-not-appear"
        artifact = {
            **BLOCKED_FIXTURE,
            "full_verdict_available": True,
            "full_verdict_url": (
                "https://cursor.com/agents/example?" + secret_query
            ),
        }

        card = notify.render_card(artifact)

        self.assertIsNotNone(card)
        assert card is not None
        self.assertNotIn("should-not-appear", card["text"])
        self.assertIn("Full verdict: in Cursor", card["text"])


if __name__ == "__main__":
    unittest.main()
