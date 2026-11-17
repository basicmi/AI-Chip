"""Tests for deterministic, bounded human Claim review batches."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_intelligence_claim_review_batch import build_review_batch, markdown_report


def make_claim(claim_id, *, statement=None, url=None):
    return {
        "claim_id": claim_id,
        "candidate_id": "candidate-" + claim_id,
        "topic": "performance",
        "claim_type": "performance_result",
        "assertion_class": "research_result_candidate",
        "evidence_class": "research_preprint",
        "statement": statement or "Model X achieved 123 tokens/s on workload Y.",
        "value": 123,
        "unit": "tokens/s",
        "scope": {"status": "explicit", "text": "single accelerator, batch 1"},
        "qualifiers": ["vendor-reported"],
        "evidence_quote": "The measured throughput was 123 tokens/s.",
        "source": {
            "url": url or "https://example.org/" + claim_id,
            "publisher": "Example Lab",
            "source_type": "research_paper",
        },
    }


def make_row(claim_id, *, score=10, age=5, state="pending", snapshot=True, first_seen="2026-11-01T00:00:00Z"):
    row = {
        "claim_id": claim_id,
        "review_state": state,
        "first_seen_at": first_seen,
        "days_since_first_seen": age,
        "last_priority_score": score,
        "priority": {"score": score, "score_factors": {"high_impact_topic": score}, "risk_flags": ["research_preprint_not_independent_measurement"]},
    }
    if snapshot:
        row["claim_snapshot"] = make_claim(claim_id)
    return row


def make_state(rows):
    return {
        "schema_version": "1.0",
        "generated_at": "2026-11-17T10:00:00Z",
        "observation_state": "cache_persisted",
        "state_is_approval": False,
        "summary": {
            "tracked_backlog_claims": len(rows),
            "review_states": {
                "pending": sum(row["review_state"] == "pending" for row in rows),
                "needs_more_evidence": sum(row["review_state"] == "needs_more_evidence" for row in rows),
                "rejected": 0,
                "accepted_for_evidence_attachment": 0,
            },
        },
        "aging_backlog": rows,
    }


class ClaimReviewBatchTests(unittest.TestCase):
    def test_selects_highest_priority_pending_claims_deterministically(self):
        state = make_state([
            make_row("low", score=5, age=40),
            make_row("high-old", score=90, age=10),
            make_row("high-young", score=90, age=2),
            make_row("medium", score=40, age=20),
        ])
        first = build_review_batch(state, batch_size=2)
        second = build_review_batch(state, batch_size=2)
        ids = [item["claim_id"] for item in first["items"]]
        self.assertEqual(ids, ["high-old", "high-young"])
        self.assertEqual(first["batch_id"], second["batch_id"])
        self.assertEqual(first["status"], "ready")
        self.assertEqual(first["summary"]["remaining_pending_after_batch"], 2)

    def test_follow_up_items_do_not_displace_never_reviewed_pending_items(self):
        state = make_state([
            make_row("follow-up", score=1000, state="needs_more_evidence"),
            make_row("pending", score=10),
        ])
        packet = build_review_batch(state, batch_size=1)
        self.assertEqual([x["claim_id"] for x in packet["items"]], ["pending"])
        self.assertEqual([x["claim_id"] for x in packet["follow_up_queue"]], ["follow-up"])

    def test_missing_payloads_are_reported_and_status_is_partial(self):
        state = make_state([make_row("good"), make_row("missing", snapshot=False)])
        packet = build_review_batch(state, batch_size=10)
        self.assertEqual(packet["status"], "partial")
        self.assertEqual(packet["summary"]["missing_claim_ids"], ["missing"])
        self.assertEqual(packet["summary"]["selected_for_this_batch"], 1)

    def test_decision_template_matches_human_ledger_shape_and_is_blank(self):
        packet = build_review_batch(make_state([make_row("claim-1")]))
        template = packet["decision_template"]
        self.assertEqual(set(template), {"schema_version", "decisions"})
        self.assertEqual(template["schema_version"], "1.0")
        self.assertEqual(set(template["decisions"][0]), {"claim_id", "decision", "reviewer", "decided_at", "notes"})
        self.assertTrue(all(value == "" for key, value in template["decisions"][0].items() if key != "claim_id"))
        self.assertFalse(packet["policy"]["decisions_written"])
        self.assertFalse(packet["policy"]["factual_verification_performed"])

    def test_markdown_contains_original_source_claim_and_review_checklist(self):
        packet = build_review_batch(make_state([make_row("claim-1")]))
        report = markdown_report(packet)
        self.assertIn("Model X achieved 123 tokens/s", report)
        self.assertIn("https://example.org/claim-1", report)
        self.assertIn("Original source opened and checked", report)
        self.assertIn("Priority is a work-routing score", report)

    def test_rejects_non_persisted_or_approval_state(self):
        state = make_state([make_row("claim-1")])
        state["state_is_approval"] = True
        with self.assertRaisesRegex(ValueError, "not an approval"):
            build_review_batch(state)

    def test_rejects_snapshot_id_mismatch_and_duplicate_ids(self):
        state = make_state([make_row("claim-1")])
        state["aging_backlog"][0]["claim_snapshot"]["claim_id"] = "other"
        with self.assertRaisesRegex(ValueError, "snapshot ID"):
            build_review_batch(state)
        duplicate = make_state([make_row("claim-1"), make_row("claim-1")])
        with self.assertRaisesRegex(ValueError, "unique"):
            build_review_batch(duplicate)

    def test_reports_follow_up_only_and_empty_states(self):
        follow = make_state([make_row("follow", state="needs_more_evidence")])
        packet = build_review_batch(follow)
        self.assertEqual(packet["status"], "follow_up_only")
        self.assertEqual(packet["summary"]["selected_for_this_batch"], 0)
        empty = make_state([])
        packet = build_review_batch(empty)
        self.assertEqual(packet["status"], "empty")

    def test_rejects_bad_batch_size_and_mismatched_counts(self):
        state = make_state([make_row("claim-1")])
        with self.assertRaisesRegex(ValueError, "batch_size"):
            build_review_batch(state, batch_size=0)
        state["summary"]["review_states"]["pending"] = 9
        with self.assertRaisesRegex(ValueError, "counts"):
            build_review_batch(state)


if __name__ == "__main__":
    unittest.main()
