import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_intelligence_conversion_funnel import build_funnel, markdown_report


def fixtures(root):
    discovery = {
        "schema_version": "1.1", "generated_at": "2026-11-24T00:00:00Z",
        "read_only": True, "candidate_count": 5,
    }
    claims = {
        "schema_version": "1.0", "generated_at": "2026-11-24T00:00:01Z",
        "input_candidate_count": 5, "candidate_count_with_claims": 3,
        "claim_count": 4,
        "claims": [{"claim_id": "claim-a"}, {"claim_id": "claim-b"},
                   {"claim_id": "claim-c"}, {"claim_id": "claim-d"}],
    }
    triage = {
        "schema_version": "1.0", "generated_at": "2026-11-24T00:00:02Z",
        "claim_report_generated_at": claims["generated_at"],
        "summary": {"input_claims": 4, "triage_groups": 3,
                    "collapsed_duplicate_claims": 1},
    }
    ids = ["claim-a", "claim-b", "claim-c", "claim-d", "claim-old"]
    review_state = {
        "schema_version": "1.0", "generated_at": "2026-11-24T00:00:03Z",
        "observation_state": "cache_persisted", "state_is_approval": False,
        "summary": {
            "tracked_current_claims": 4, "tracked_backlog_claims": 5,
            "review_states": {
                "pending": 2, "needs_more_evidence": 1, "rejected": 1,
                "accepted_for_evidence_attachment": 1,
            },
        },
        "items": {cid: {} for cid in ids},
    }
    ledger = {
        "schema_version": "1.0",
        "decisions": [
            {"claim_id": "claim-c", "decision": "rejected", "reviewer": "Reviewer A",
             "decided_at": "2026-11-23T00:00:00Z", "notes": "The source does not support the stated product configuration."},
            {"claim_id": "claim-d", "decision": "accepted_for_evidence_attachment", "reviewer": "Reviewer B",
             "decided_at": "2026-11-23T00:00:00Z", "notes": "The claim is suitable for preparing a source-linked evidence attachment."},
            {"claim_id": "claim-old", "decision": "needs_more_evidence", "reviewer": "Reviewer A",
             "decided_at": "2026-11-22T00:00:00Z", "notes": "Need an original source and exact model configuration before proceeding."},
        ],
    }
    manifest = {
        "schema_version": "1.0", "integrations": [],
        "policy": {"manual_only": True, "automatic_registry_writes": False},
    }
    (root / "data").mkdir()
    (root / "data" / "company-profiles.json").write_text(json.dumps({
        "schema_version": "1.0",
        "companies": [{"id": "company-x", "products": [{"id": "product-x"}]}],
    }), encoding="utf-8")
    return discovery, claims, triage, review_state, ledger, manifest


class ConversionFunnelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data = fixtures(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, data=None):
        return build_funnel(*(data or self.data), self.root)

    def test_counts_each_stage_and_keeps_denominators_explicit(self):
        report = self.build()
        m = report["metrics"]
        self.assertEqual(m["discovery_candidates"], 5)
        self.assertEqual(m["candidates_with_claims"], 3)
        self.assertEqual(m["claims_extracted"], 4)
        self.assertEqual(m["triage_groups"], 3)
        self.assertEqual(m["duplicate_claims_collapsed"], 1)
        self.assertEqual(m["persistent_review_backlog"], 5)
        self.assertEqual(m["human_decisions_recorded"], 3)
        self.assertEqual(m["accepted_for_evidence_attachment"], 1)
        self.assertEqual(m["decision_coverage"]["rate"], .6)
        self.assertEqual(m["acceptance_rate_among_decisions"]["rate"], round(1/3, 4))
        self.assertIsNone(m["integration_coverage"]["rate"])
        self.assertFalse(report["policy"]["formal_factual_verification_performed"])
        self.assertFalse(report["policy"]["automatic_registry_writes"])

    def test_markdown_explains_decision_boundary(self):
        report = self.build()
        text = markdown_report(report)
        self.assertIn("not factual verification", text)
        self.assertIn("Integration coverage of eligible Claims: N/A", text)

    def test_accepts_manual_receipt_only_for_accepted_claim_and_existing_record(self):
        data = copy.deepcopy(self.data)
        data[5]["integrations"].append({
            "claim_id": "claim-d", "target_registry": "data/company-profiles.json",
            "target_record_id": "product-x",
            "merged_pr_url": "https://github.com/basicmi/AI-Chip/pull/900",
            "merge_commit_sha": "a" * 40, "integrated_at": "2026-11-24T00:00:00Z",
            "reviewer": "Reviewer B",
            "notes": "Merged a manually reviewed source-linked product record into the curated registry.",
        })
        report = self.build(data)
        self.assertEqual(report["metrics"]["integrated_claims"], 1)
        self.assertEqual(report["metrics"]["integration_coverage"]["rate"], 1.0)
        self.assertEqual(report["metrics"]["eligible_claims_not_integrated"], 0)

    def test_rejects_receipt_for_non_accepted_claim(self):
        data = copy.deepcopy(self.data)
        row = {
            "claim_id": "claim-c", "target_registry": "data/company-profiles.json",
            "target_record_id": "product-x",
            "merged_pr_url": "https://github.com/basicmi/AI-Chip/pull/900",
            "merge_commit_sha": "a" * 40, "integrated_at": "2026-11-24T00:00:00Z",
            "reviewer": "Reviewer B",
            "notes": "Merged a manually reviewed source-linked product record into the curated registry.",
        }
        data[5]["integrations"].append(row)
        with self.assertRaisesRegex(ValueError, "only accepted"):
            self.build(data)

    def test_rejects_receipt_for_missing_registry_record(self):
        data = copy.deepcopy(self.data)
        row = {
            "claim_id": "claim-d", "target_registry": "data/company-profiles.json",
            "target_record_id": "missing-product",
            "merged_pr_url": "https://github.com/basicmi/AI-Chip/pull/900",
            "merge_commit_sha": "a" * 40, "integrated_at": "2026-11-24T00:00:00Z",
            "reviewer": "Reviewer B",
            "notes": "Merged a manually reviewed source-linked product record into the curated registry.",
        }
        data[5]["integrations"].append(row)
        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.build(data)

    def test_rejects_noncanonical_pr_url(self):
        data = copy.deepcopy(self.data)
        data[5]["integrations"].append({
            "claim_id": "claim-d", "target_registry": "data/company-profiles.json",
            "target_record_id": "product-x",
            "merged_pr_url": "https://example.com/pull/900",
            "merge_commit_sha": "a" * 40, "integrated_at": "2026-11-24T00:00:00Z",
            "reviewer": "Reviewer B",
            "notes": "Merged a manually reviewed source-linked product record into the curated registry.",
        })
        with self.assertRaisesRegex(ValueError, "canonical merged"):
            self.build(data)

    def test_rejects_review_state_ledger_mismatch(self):
        data = copy.deepcopy(self.data)
        data[3]["summary"]["review_states"]["rejected"] = 0
        data[3]["summary"]["review_states"]["pending"] = 3
        with self.assertRaisesRegex(ValueError, "do not match"):
            self.build(data)

    def test_rejects_triage_count_mismatch(self):
        data = copy.deepcopy(self.data)
        data[2]["summary"]["triage_groups"] = 2
        with self.assertRaisesRegex(ValueError, "reconcile"):
            self.build(data)

    def test_rejects_automatic_write_policy(self):
        data = copy.deepcopy(self.data)
        data[5]["policy"]["automatic_registry_writes"] = True
        with self.assertRaisesRegex(ValueError, "prohibit automatic"):
            self.build(data)


if __name__ == "__main__":
    unittest.main()
