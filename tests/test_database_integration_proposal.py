import copy
import hashlib
import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_database_integration_proposal import (
    build_package, canonical, sha256_json, verify_package
)
from propose_evidence_update import fingerprint_claim


def fixture():
    target = {
        "id": "b200-hbm", "subject_type": "product", "subject_id": "b200-sxm",
        "topic": "memory_capacity", "statement": "Vendor lists 180 GB HBM.",
        "value": 180, "unit": "GB HBM3e", "scope": "Per B200 SXM GPU",
        "claim_status": "vendor_reported", "evidence_ids": ["older"],
        "last_reviewed": "2026-11-05"
    }
    database = {
        "schema_version": "1.3", "database_version": "2026.11",
        "companies": [{
            "id": "nvidia", "display_name": "NVIDIA", "products": [
                {"id": "b200-sxm", "claim_ids": ["b200-hbm"]}
            ], "claims": [target],
            "evidence": [{"id": "older", "url": "https://vendor.example/older"}]
        }]
    }
    source_claim = {
        "claim_id": "claim-new-b200", "review_status": "unverified_candidate",
        "statement": "NVIDIA describes B200 HBM capacity in updated documentation.",
        "evidence_quote": "The system has 180 GB HBM.",
        "source": {"url": "https://vendor.example/new", "publisher": "Vendor"}
    }
    report = {"schema_version": "1.0", "claim_count": 1, "claims": [source_claim]}
    approval = {
        "schema_version": "1.0", "approval_id": "review-b200-hbm",
        "reviewer": "maintainer@example.org", "reviewed_at": "2026-11-20",
        "decision": "approved_evidence_attachment", "company_id": "nvidia",
        "existing_claim_id": "b200-hbm", "expected_claim_sha256": fingerprint_claim(target),
        "extracted_claim_id": "claim-new-b200",
        "evidence": {
            "id": "new-evidence", "title": "Updated vendor specification",
            "url": "https://vendor.example/new", "publisher": "Vendor",
            "source_type": "vendor_primary", "independence": "vendor",
            "published_at": "2026-11-18", "checked_at": "2026-11-20",
            "review_status": "reviewed", "notes": "Manually inspected the original vendor specification page."
        },
        "review_notes": "Maintainer checked the original source, exact product configuration and the selected database Claim."
    }
    raw = (json.dumps(database, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return database, report, approval, raw


class DatabaseIntegrationProposalTests(unittest.TestCase):
    def build(self):
        db, report, approval, raw = fixture()
        return db, report, approval, raw, build_package(
            db, report, approval, raw, "2026-11-23T04:00:00.000Z"
        )

    def test_package_contains_exactly_two_append_only_operations(self):
        db, report, approval, raw, (package, patch, audit, diff, updated) = self.build()
        self.assertEqual(len(package["operations"]), 2)
        self.assertEqual(package["operations"][0]["op"], "add")
        self.assertEqual(package["operations"][1]["op"], "add")
        self.assertEqual(package["target"]["evidence_ids_before"], ["older"])
        self.assertEqual(package["target"]["evidence_ids_after"], ["older", "new-evidence"])
        self.assertEqual(updated["companies"][0]["claims"][0]["claim_status"], "vendor_reported")
        self.assertEqual(updated["companies"][0]["claims"][0]["value"], 180)
        self.assertFalse(package["policy"]["source_truth_verified"])
        self.assertFalse(audit["source_truth_verified"])
        self.assertIn("new-evidence", diff)
        self.assertEqual(patch["operations"], package["operations"])

    def test_package_verifies_against_exact_base_registry(self):
        db, report, approval, raw, (package, patch, audit, diff, updated) = self.build()
        rebuilt, patch2, audit2, diff2 = verify_package(db, package, raw, report, approval)
        self.assertEqual(rebuilt, updated)
        self.assertEqual(patch2, patch)
        self.assertEqual(audit2, audit)
        self.assertEqual(diff2, diff)

    def test_rejects_stale_registry_even_if_target_claim_unchanged(self):
        db, report, approval, raw, (package, *_rest) = self.build()
        stale = copy.deepcopy(db)
        stale["companies"][0]["summary"] = "changed after proposal"
        stale_raw = (json.dumps(stale, indent=2, ensure_ascii=False) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "does not match current registry"):
            verify_package(stale, package, stale_raw, report, approval)

    def test_rejects_separate_approval_manifest_mismatch(self):
        db, report, approval, raw, (package, *_rest) = self.build()
        changed = copy.deepcopy(approval)
        changed["reviewer"] = "different-reviewer"
        with self.assertRaisesRegex(ValueError, "Approval Manifest"):
            verify_package(db, package, raw, report, changed)

    def test_rejects_separate_original_claim_report_mismatch(self):
        db, report, approval, raw, (package, *_rest) = self.build()
        changed = copy.deepcopy(report)
        changed["claims"][0]["statement"] = "A different source statement."
        with self.assertRaisesRegex(ValueError, "original Claim report"):
            verify_package(db, package, raw, changed, approval)

    def test_rejects_tampered_package_hash(self):
        db, report, approval, raw, (package, *_rest) = self.build()
        package["target"]["claim_id"] = "different"
        with self.assertRaisesRegex(ValueError, "package SHA256 mismatch"):
            verify_package(db, package, raw, report, approval)

    def test_rejects_tampered_patch_even_when_package_rehashed(self):
        db, report, approval, raw, (package, *_rest) = self.build()
        package["operations"][1]["path"] = "/companies/0/claims/0/claim_status"
        body = {k:v for k,v in package.items() if k != "package_sha256"}
        package["package_sha256"] = sha256_json(body)
        with self.assertRaisesRegex(ValueError, "does not match current registry"):
            verify_package(db, package, raw, report, approval)

    def test_rejects_source_claim_url_mismatch(self):
        db, report, approval, raw = fixture()
        report["claims"][0]["source"]["url"] = "https://other.example/source"
        with self.assertRaisesRegex(ValueError, "source URL"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00.000Z")

    def test_rejects_stale_claim_fingerprint(self):
        db, report, approval, raw = fixture()
        db["companies"][0]["claims"][0]["value"] = 192
        raw = (json.dumps(db, indent=2, ensure_ascii=False) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00.000Z")

    def test_rejects_non_evidence_only_approval(self):
        db, report, approval, raw = fixture()
        approval["decision"] = "suggested"
        with self.assertRaisesRegex(ValueError, "approved_evidence_attachment"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00.000Z")

    def test_rejects_future_human_review_date(self):
        db, report, approval, raw = fixture()
        approval["reviewed_at"] = "2099-01-01"
        approval["evidence"]["checked_at"] = "2098-12-31"
        with self.assertRaisesRegex(ValueError, "review date cannot be in the future"):
            build_package(db, report, approval, raw, "2099-01-01T12:00:00.000Z")

    def test_rejects_evidence_published_after_checked_date(self):
        db, report, approval, raw = fixture()
        approval["evidence"]["published_at"] = "2026-11-21"
        with self.assertRaisesRegex(ValueError, "publication date cannot follow"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00.000Z")

    def test_rejects_future_package_timestamp(self):
        db, report, approval, raw = fixture()
        with self.assertRaisesRegex(ValueError, "future"):
            build_package(db, report, approval, raw, "2099-01-01T00:00:00.000Z")

    def test_rejects_invalid_claim_report_count(self):
        db, report, approval, raw = fixture()
        report["claim_count"] = 2
        with self.assertRaisesRegex(ValueError, "count does not match"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00.000Z")


    def test_cli_build_and_verify_round_trip(self):
        db, report, approval, raw = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                "registry.json": raw.decode("utf-8"),
                "claims.json": json.dumps(report, ensure_ascii=False),
                "approval.json": json.dumps(approval, ensure_ascii=False),
            }
            for name, value in files.items():
                (root / name).write_text(value, encoding="utf-8")
            common = [
                sys.executable, str(ROOT / "scripts/build_database_integration_proposal.py")
            ]
            build = subprocess.run(common + [
                "build", "--company-profiles", str(root / "registry.json"),
                "--claim-report", str(root / "claims.json"),
                "--approval", str(root / "approval.json"),
                "--proposal-output", str(root / "proposal.json"),
                "--patch-output", str(root / "patch.json"),
                "--audit-output", str(root / "audit.json"),
                "--diff-output", str(root / "proposal.diff"),
                "--database-output", str(root / "updated.json"),
                "--created-at", "2026-11-23T04:00:00.000Z"
            ], capture_output=True, text=True, check=False)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            verify = subprocess.run(common + [
                "verify", "--company-profiles", str(root / "registry.json"),
                "--proposal", str(root / "proposal.json"),
                "--claim-report", str(root / "claims.json"),
                "--approval", str(root / "approval.json"),
                "--database-output", str(root / "verified.json"),
                "--patch-output", str(root / "verified-patch.json"),
                "--audit-output", str(root / "verified-audit.json"),
                "--diff-output", str(root / "verified.diff")
            ], capture_output=True, text=True, check=False)
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
            self.assertEqual(json.loads((root / "verified.json").read_text()), json.loads((root / "updated.json").read_text()))
            self.assertTrue((root / "proposal.diff").read_text().startswith("--- a/data/company-profiles.json"))


if __name__ == "__main__":
    unittest.main()
