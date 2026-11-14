"""Real-registry replay of the reviewed-evidence flow, with an unmistakably fake fixture source.

No reviewer approval or authentic evidence is asserted by this rehearsal.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from propose_evidence_update import create_patch, fingerprint_claim
from verify_evidence_patch import verify_patch

FIXTURE_URL = "https://example.org/ai-chip-evidence-rehearsal-only"


def build_rehearsal():
    db = json.loads((ROOT / "data/company-profiles.json").read_text(encoding="utf-8"))
    company = next(c for c in db["companies"] if c["id"] == "nvidia")
    target = next(c for c in company["claims"] if c["id"] == "b200-memory-capacity")
    assert FIXTURE_URL not in {e.get("url") for e in company["evidence"]}
    extracted = {
        "schema_version": "1.0",
        "claims": [{
            "claim_id": "claim-rehearsal-nvidia-b200",
            "review_status": "unverified_candidate",
            "source": {"url": FIXTURE_URL},
            "evidence_quote": target["statement"],
        }]
    }
    # This is a test fixture, not an actual review. It MUST NOT be committed to
    # reviews/approvals/ or dispatched via the write-capable workflow.
    approval = {
        "schema_version": "1.0",
        "approval_id": "test-only-b200-memory-capacity",
        "reviewer": "ci-rehearsal-not-a-human-approval",
        "reviewed_at": "2026-11-14",
        "decision": "approved_evidence_attachment",
        "company_id": "nvidia",
        "existing_claim_id": target["id"],
        "expected_claim_sha256": fingerprint_claim(target),
        "extracted_claim_id": "claim-rehearsal-nvidia-b200",
        "evidence": {
            "id": "test-only-synthetic-b200-source",
            "title": "Synthetic CI rehearsal source — NOT factual evidence",
            "url": FIXTURE_URL,
            "publisher": "Synthetic CI Test Fixture",
            "source_type": "other", "independence": "project",
            "published_at": None, "checked_at": "2026-11-14",
            "review_status": "reviewed",
            "notes": "Synthetic fixture for testing the shape of the approval and update workflow only.",
        },
        "review_notes": "This is a machine-generated test approval for CI rehearsal only, not a real review or statement of factual support.",
    }
    return db, extracted, approval


class EndToEndRehearsalTests(unittest.TestCase):
    def test_real_registry_mock_approval_generates_exact_two_field_update(self):
        db, extracted, approval = build_rehearsal()
        before = copy.deepcopy(db)
        updated, audit = create_patch(db, extracted, approval)
        self.assertEqual(db, before)
        verification = verify_patch(db, updated, approval, audit)
        self.assertEqual(verification["verification_status"], "exact_append_only_change")
        self.assertEqual(verification["unapproved_changes"], 0)
        self.assertFalse(verification["source_truth_verified"])
        company = next(c for c in updated["companies"] if c["id"] == "nvidia")
        target = next(c for c in company["claims"] if c["id"] == "b200-memory-capacity")
        self.assertEqual(target["claim_status"], "vendor_reported")
        self.assertIn("test-only-synthetic-b200-source", target["evidence_ids"])

    def test_real_registry_rejects_existing_vendor_evidence_url(self):
        db, extracted, approval = build_rehearsal()
        existing = next(c for c in db["companies"] if c["id"] == "nvidia")["evidence"][0]["url"]
        extracted["claims"][0]["source"]["url"] = existing
        approval["evidence"]["url"] = existing
        with self.assertRaisesRegex(ValueError, "evidence URL already exists"):
            create_patch(db, extracted, approval)

    def test_verifier_detects_unrelated_company_or_claim_changes(self):
        db, extracted, approval = build_rehearsal()
        updated, audit = create_patch(db, extracted, approval)
        tampered = copy.deepcopy(updated)
        tampered["companies"][0]["claims"][0]["value"] = "changed"
        with self.assertRaisesRegex(ValueError, "beyond approved|unrelated claim"):
            verify_patch(db, tampered, approval, audit)
        tampered = copy.deepcopy(updated)
        tampered["companies"][0]["summary"] = "tampered"
        with self.assertRaisesRegex(ValueError, "unapproved database fields"):
            verify_patch(db, tampered, approval, audit)

    def test_verifier_detects_extra_evidence_or_status_escalation(self):
        db, extracted, approval = build_rehearsal()
        updated, audit = create_patch(db, extracted, approval)
        tampered = copy.deepcopy(updated)
        tampered["companies"][0]["evidence"].append({"id": "illicit"})
        with self.assertRaisesRegex(ValueError, "only one evidence"):
            verify_patch(db, tampered, approval, audit)
        tampered = copy.deepcopy(updated)
        target = next(c for c in tampered["companies"][0]["claims"] if c["id"] == "b200-memory-capacity")
        target["claim_status"] = "independently_verified"
        with self.assertRaisesRegex(ValueError, "beyond approved"):
            verify_patch(db, tampered, approval, audit)

    def test_cli_generation_and_independent_verifier(self):
        db, extracted, approval = build_rehearsal()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for filename, value in (("original.json", db), ("claims.json", extracted), ("approval.json", approval)):
                (root / filename).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
            generation = subprocess.run(
                [sys.executable, str(ROOT / "scripts/propose_evidence_update.py"),
                 "--company-profiles", str(root / "original.json"),
                 "--claim-report", str(root / "claims.json"),
                 "--approval", str(root / "approval.json"),
                 "--output", str(root / "updated.json"),
                 "--audit-output", str(root / "audit.json"),
                 "--diff-output", str(root / "proposal.diff")],
                capture_output=True, text=True, check=False)
            self.assertEqual(generation.returncode, 0, generation.stdout + generation.stderr)
            verified = subprocess.run(
                [sys.executable, str(ROOT / "scripts/verify_evidence_patch.py"),
                 "--original", str(root / "original.json"),
                 "--updated", str(root / "updated.json"),
                 "--approval", str(root / "approval.json"),
                 "--audit", str(root / "audit.json"),
                 "--output", str(root / "verification.json")],
                capture_output=True, text=True, check=False)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            self.assertIn("exact evidence-only update", verified.stdout)
            self.assertIn("test-only-synthetic-b200-source", (root / "proposal.diff").read_text())
            self.assertFalse(json.loads((root / "verification.json").read_text())["source_truth_verified"])


if __name__ == "__main__":
    unittest.main()
