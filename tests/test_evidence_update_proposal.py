import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from propose_evidence_update import create_patch, fingerprint_claim, build_diff


def fixture():
    existing = {
        "id": "b200-hbm", "subject_type": "product", "subject_id": "b200",
        "topic": "memory_capacity", "statement": "Vendor lists 180 GB HBM.",
        "value": 180, "unit": "GB", "scope": "Per B200 GPU",
        "claim_status": "vendor_reported", "evidence_ids": ["older"], "last_reviewed": "2026-11-05"
    }
    database = {"companies": [{
        "id": "nvidia", "products": [{"id": "b200", "claim_ids": ["b200-hbm"]}],
        "claims": [existing], "evidence": [{"id": "older", "url": "https://vendor.example/older"}]
    }]}
    extracted = {"schema_version": "1.0", "claims": [{
        "claim_id": "claim-abc", "review_status": "unverified_candidate",
        "source": {"url": "https://vendor.example/new"}, "evidence_quote": "The system has 180 GB HBM."
    }]}
    approval = {
        "schema_version": "1.0", "approval_id": "review-b200-hbm",
        "reviewer": "hardware-evidence-maintainer", "reviewed_at": "2026-11-14",
        "decision": "approved_evidence_attachment", "company_id": "nvidia",
        "existing_claim_id": "b200-hbm", "expected_claim_sha256": fingerprint_claim(existing),
        "extracted_claim_id": "claim-abc",
        "evidence": {
            "id": "new-evidence", "title": "Vendor updated product specifications",
            "url": "https://vendor.example/new", "publisher": "Vendor",
            "source_type": "vendor_primary", "independence": "vendor",
            "published_at": "2026-11-12", "checked_at": "2026-11-14",
            "review_status": "reviewed", "notes": "Manually inspected original vendor product page."
        },
        "review_notes": "Maintainer manually checked the product, exact quote and supporting specification."
    }
    return database, extracted, approval


class EvidenceUpdateTests(unittest.TestCase):
    def test_only_adds_evidence_and_claim_reference(self):
        source, claims, approval = fixture()
        initial = copy.deepcopy(source)
        updated, audit = create_patch(source, claims, approval)
        self.assertEqual(source, initial)
        company = updated["companies"][0]
        self.assertEqual(company["claims"][0]["evidence_ids"], ["older", "new-evidence"])
        self.assertEqual(company["claims"][0]["claim_status"], "vendor_reported")
        self.assertEqual(company["claims"][0]["value"], 180)
        self.assertEqual(company["evidence"][-1]["id"], "new-evidence")
        self.assertEqual(len(audit["changed_fields"]), 2)
        self.assertIn("+", build_diff(source, updated))

    def test_refuses_stale_target_claim(self):
        source, claims, approval = fixture()
        source["companies"][0]["claims"][0]["value"] = 192
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            create_patch(source, claims, approval)

    def test_rejects_missing_human_approval(self):
        source, claims, approval = fixture()
        approval["decision"] = "suggested"
        with self.assertRaisesRegex(ValueError, "approved_evidence_attachment"):
            create_patch(source, claims, approval)

    def test_rejects_non_matching_source(self):
        source, claims, approval = fixture()
        approval["evidence"]["url"] = "https://different.example/new"
        with self.assertRaisesRegex(ValueError, "exactly match"):
            create_patch(source, claims, approval)

    def test_rejects_duplicate_evidence(self):
        source, claims, approval = fixture()
        approval["evidence"]["id"] = "older"
        with self.assertRaisesRegex(ValueError, "already exists"):
            create_patch(source, claims, approval)

    def test_rejects_unknown_company_or_claim(self):
        source, claims, approval = fixture()
        approval["company_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "exactly one existing company"):
            create_patch(source, claims, approval)
        source, claims, approval = fixture()
        approval["existing_claim_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "exactly one claim"):
            create_patch(source, claims, approval)

    def test_rejects_unreviewed_extracted_claim(self):
        source, claims, approval = fixture()
        claims["claims"][0]["review_status"] = "verified"
        with self.assertRaisesRegex(ValueError, "unverified extracted"):
            create_patch(source, claims, approval)

    def test_rejects_arbitrary_approval_fields(self):
        source, claims, approval = fixture()
        approval["new_claim_status"] = "independently_verified"
        with self.assertRaisesRegex(ValueError, "exactly"):
            create_patch(source, claims, approval)

    def test_rejects_future_evidence_check_relative_to_review(self):
        source, claims, approval = fixture()
        approval["evidence"]["checked_at"] = "2026-11-15"
        with self.assertRaisesRegex(ValueError, "after review"):
            create_patch(source, claims, approval)


if __name__ == "__main__":
    unittest.main()
