import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_intelligence_semantic_support import prepare, evaluate, markdown_report


def batch():
    return {
        "schema_version": "1.0", "batch_id": "claim-review-fixture",
        "generated_at": "2026-11-20T12:00:00Z",
        "summary": {"selected_for_this_batch": 2},
        "policy": {"decisions_written": False, "factual_verification_performed": False},
        "items": [
            {"claim_id": "claim-1", "review_state": "pending", "claim": {
                "claim_id": "claim-1", "statement": "GPU inference improves throughput 25 percent.",
                "evidence_quote": "Our GPU inference improves throughput 25 percent.",
                "source": {"url": "https://example.org/a", "source_type": "research_paper"},
            }},
            {"claim_id": "claim-2", "review_state": "pending", "claim": {
                "claim_id": "claim-2", "statement": "KV cache is faster on the new architecture.",
                "evidence_quote": "KV cache is faster on the new architecture.",
                "source": {"url": "https://example.org/b", "source_type": "vendor_primary"},
            }},
        ],
    }


def human(reviewer, label, *, checked=True):
    return {"reviewer": reviewer, "label": label, "source_checked": checked,
            "rationale": "I inspected the original document and the scope and wording of this Claim."}


class SemanticSupportTests(unittest.TestCase):
    def test_blank_packet_does_not_create_decisions(self):
        packet = prepare(batch())
        self.assertEqual(len(packet["items"]), 2)
        self.assertEqual(packet["items"][0]["reviewers"][0]["label"], "")
        self.assertTrue(packet["policy"]["cannot_promote_to_verified"])
        scored = evaluate(packet)
        self.assertIsNone(scored["raw_agreement"])
        self.assertEqual(scored["pending_claim_ids"], ["claim-1", "claim-2"])
        self.assertEqual(scored["automatically_verified_claims"], 0)

    def test_two_distinct_human_reviews_agree(self):
        packet = prepare(batch())
        packet["items"][0]["reviewers"] = [human("alice", "supported_by_source"),
                                               human("bob", "supported_by_source")]
        packet["items"][1]["reviewers"] = [human("alice", "insufficient_context"),
                                               human("bob", "insufficient_context")]
        scored = evaluate(packet)
        self.assertEqual(scored["status"], "complete")
        self.assertEqual(scored["raw_agreement"], 1.0)
        self.assertEqual(len(scored["agreements"]), 2)
        self.assertIn("Agreement measures reviewer consistency", markdown_report(scored))

    def test_disagreement_requires_manual_adjudication(self):
        packet = prepare(batch())
        packet["items"][0]["reviewers"] = [human("alice", "supported_by_source"),
                                               human("bob", "contradicted_by_source")]
        scored = evaluate(packet)
        self.assertEqual(scored["human_adjudication_needed"], 1)
        self.assertEqual(scored["raw_agreement"], 0.0)
        self.assertEqual(scored["status"], "pending")

    def test_one_reviewer_never_produces_agreement(self):
        packet = prepare(batch())
        packet["items"][0]["reviewers"][0] = human("alice", "supported_by_source")
        scored = evaluate(packet)
        self.assertEqual(scored["double_reviewed_claims"], 0)
        self.assertIsNone(scored["raw_agreement"])

    def test_same_reviewer_rejected_even_with_case_variation(self):
        packet = prepare(batch())
        packet["items"][0]["reviewers"] = [human("Alice", "supported_by_source"),
                                               human("alice", "supported_by_source")]
        with self.assertRaisesRegex(ValueError, "distinct identities"):
            evaluate(packet)

    def test_source_unavailable_requires_false_source_checked(self):
        packet = prepare(batch())
        packet["items"][0]["reviewers"][0] = human("alice", "source_unavailable", checked=True)
        with self.assertRaisesRegex(ValueError, "cannot be marked source_checked"):
            evaluate(packet)
        packet["items"][0]["reviewers"][0]["source_checked"] = False
        self.assertEqual(evaluate(packet)["double_reviewed_claims"], 0)

    def test_supported_label_requires_original_source_checked(self):
        packet = prepare(batch())
        packet["items"][0]["reviewers"][0] = human("alice", "supported_by_source", checked=False)
        with self.assertRaisesRegex(ValueError, "checked original source"):
            evaluate(packet)

    def test_short_rationale_or_unknown_label_rejected(self):
        packet = prepare(batch())
        packet["items"][0]["reviewers"][0] = human("alice", "unverified")
        with self.assertRaisesRegex(ValueError, "rationale"):
            evaluate(packet)
        packet["items"][0]["reviewers"][0] = human("alice", "supported_by_source")
        packet["items"][0]["reviewers"][0]["rationale"] = "short"
        with self.assertRaisesRegex(ValueError, "rationale"):
            evaluate(packet)

    def test_invalid_schema_or_promotion_rejected(self):
        packet = prepare(batch())
        packet["policy"]["cannot_promote_to_verified"] = False
        with self.assertRaisesRegex(ValueError, "cannot promote"):
            evaluate(packet)
        other = batch()
        other["policy"]["factual_verification_performed"] = True
        with self.assertRaisesRegex(ValueError, "unverified"):
            prepare(other)

    def test_duplicate_ids_and_bad_urls_rejected(self):
        source = batch()
        source["items"][1]["claim_id"] = "claim-1"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            prepare(source)
        source = batch()
        source["items"][0]["claim"]["source"]["url"] = "http://example.org/a"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            prepare(source)

    def test_disallow_non_pending_claims_and_bad_counts(self):
        source = batch()
        source["items"][0]["review_state"] = "rejected"
        with self.assertRaisesRegex(ValueError, "pending"):
            prepare(source)
        source = batch()
        source["summary"]["selected_for_this_batch"] = 1
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            prepare(source)

    def test_does_not_mutate_input(self):
        source = batch()
        before = copy.deepcopy(source)
        prepare(source)
        self.assertEqual(source, before)


if __name__ == "__main__":
    unittest.main()
