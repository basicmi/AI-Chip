import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_product_creation_proposal import (
    build_package, canonical, sha256_json, verify_package
)


def fixture():
    existing_claim = {
        "id": "h100-hbm", "subject_type": "product", "subject_id": "h100",
        "topic": "memory_capacity", "statement": "H100 has 80 GB HBM.",
        "scope": "Per H100 SXM GPU.", "claim_status": "vendor_reported",
        "evidence_ids": ["older"], "last_reviewed": "2026-11-05"
    }
    existing_product = {
        "id": "h100", "name": "H100", "product_type": "gpu",
        "availability": "production", "claim_ids": ["h100-hbm"]
    }
    database = {
        "schema_version": "1.3", "database_version": "2026.11",
        "companies": [{
            "id": "nvidia", "display_name": "NVIDIA",
            "products": [existing_product], "claims": [existing_claim],
            "evidence": [{"id": "older", "url": "https://vendor.example/older"}]
        }]
    }
    source_claim = {
        "claim_id": "claim-rubin-identity", "review_status": "unverified_candidate",
        "statement": "NVIDIA announced the Rubin GPU architecture and product family.",
        "evidence_quote": "Rubin is our next-generation GPU architecture.",
        "source": {"url": "https://vendor.example/rubin", "publisher": "NVIDIA"}
    }
    report = {"schema_version": "1.0", "claim_count": 1, "claims": [source_claim]}
    evidence = {
        "id": "nvidia-rubin-announcement", "title": "NVIDIA Rubin announcement",
        "url": "https://vendor.example/rubin", "publisher": "NVIDIA",
        "source_type": "vendor_primary", "independence": "vendor",
        "published_at": "2026-10-28", "checked_at": "2026-11-20",
        "review_status": "reviewed",
        "notes": "Original vendor announcement inspected by the reviewer."
    }
    product = {
        "id": "rubin", "name": "Rubin", "product_type": "gpu",
        "availability": "announced", "claim_ids": ["rubin-identity"],
        "architecture": "Rubin", "announced_at": "2026-10-28",
        "availability_history": [{
            "status": "announced", "effective_at": "2026-10-28",
            "evidence_id": evidence["id"],
            "notes": "Vendor announced the product family."
        }]
    }
    claim = {
        "id": "rubin-identity", "subject_type": "product", "subject_id": "rubin",
        "topic": "product_identity",
        "statement": source_claim["statement"],
        "scope": "Product identity and vendor-announced architecture only; no performance claim.",
        "claim_status": "vendor_reported", "evidence_ids": [evidence["id"]],
        "last_reviewed": "2026-11-20"
    }
    approval = {
        "schema_version": "1.0", "approval_id": "approve-rubin-product",
        "reviewer": "maintainer@example.org", "reviewed_at": "2026-11-20",
        "decision": "approved_new_product_with_identity_claim",
        "company_id": "nvidia", "extracted_claim_id": source_claim["claim_id"],
        "product": product, "claim": claim, "evidence": evidence,
        "review_notes": "Reviewer inspected the original vendor announcement and verified the product identity and source context."
    }
    raw = (json.dumps(database, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return database, report, approval, raw


class ProductCreationProposalTests(unittest.TestCase):
    def build(self):
        db, report, approval, raw = fixture()
        return db, report, approval, raw, build_package(
            db, report, approval, raw, "2026-11-23T04:00:00Z"
        )

    def test_builds_exact_three_record_append(self):
        db, report, approval, raw, (package, patch, audit, diff, updated) = self.build()
        self.assertEqual([op["path"].split("/")[-1] for op in package["operations"]], ["-", "-", "-"])
        self.assertEqual(len(package["operations"]), 3)
        self.assertEqual(updated["companies"][0]["products"][-1], approval["product"])
        self.assertEqual(updated["companies"][0]["claims"][-1], approval["claim"])
        self.assertEqual(updated["companies"][0]["evidence"][-1], approval["evidence"])
        self.assertEqual(updated["companies"][0]["products"][-1]["claim_ids"], ["rubin-identity"])
        self.assertEqual(updated["companies"][0]["claims"][-1]["claim_status"], "vendor_reported")
        self.assertEqual(patch["operations"], package["operations"])
        self.assertIn("rubin-identity", diff)
        self.assertFalse(audit["source_truth_verified"])
        self.assertEqual(audit["unapproved_changes"], 0)

    def test_rebuild_verifies_package_and_provenance(self):
        db, report, approval, raw, (package, patch, audit, diff, updated) = self.build()
        result = verify_package(db, package, raw, report, approval)
        self.assertEqual(result, (updated, patch, audit, diff))

    def test_rejects_duplicate_product_id(self):
        db, report, approval, raw = fixture()
        db["companies"][0]["products"].append({"id": "rubin"})
        raw = json.dumps(db).encode()
        with self.assertRaisesRegex(ValueError, "Product ID"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_duplicate_claim_id(self):
        db, report, approval, raw = fixture()
        db["companies"][0]["claims"].append({"id": "rubin-identity"})
        raw = json.dumps(db).encode()
        with self.assertRaisesRegex(ValueError, "Claim ID"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_duplicate_evidence_url(self):
        db, report, approval, raw = fixture()
        db["companies"][0]["evidence"].append({"id": "other", "url": approval["evidence"]["url"]})
        raw = json.dumps(db).encode()
        with self.assertRaisesRegex(ValueError, "Evidence ID or URL"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_wrong_product_claim_link(self):
        db, report, approval, raw = fixture()
        approval["product"]["claim_ids"] = ["other-claim"]
        with self.assertRaisesRegex(ValueError, "exactly its one initial"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_claim_with_wrong_product_subject(self):
        db, report, approval, raw = fixture()
        approval["claim"]["subject_id"] = "h100"
        with self.assertRaisesRegex(ValueError, "subject must reference"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_non_identity_or_upgraded_claim_status(self):
        db, report, approval, raw = fixture()
        approval["claim"]["claim_status"] = "independently_verified"
        with self.assertRaisesRegex(ValueError, "conservative vendor_reported"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_statement_that_does_not_match_extracted_claim(self):
        db, report, approval, raw = fixture()
        approval["claim"]["statement"] = "Rubin has 1000 TFLOPS."
        with self.assertRaisesRegex(ValueError, "exactly match"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_source_url_mismatch(self):
        db, report, approval, raw = fixture()
        approval["evidence"]["url"] = "https://other.example/rubin"
        with self.assertRaisesRegex(ValueError, "URL"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_non_https_evidence(self):
        db, report, approval, raw = fixture()
        approval["evidence"]["url"] = "http://vendor.example/rubin"
        report["claims"][0]["source"]["url"] = approval["evidence"]["url"]
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_availability_event_mismatch(self):
        db, report, approval, raw = fixture()
        approval["product"]["availability_history"][0]["status"] = "shipping"
        with self.assertRaisesRegex(ValueError, "match product availability"):
            build_package(db, report, approval, raw, "2026-11-23T04:00:00Z")

    def test_rejects_stale_base_registry(self):
        db, report, approval, raw, (package, *_rest) = self.build()
        stale = copy.deepcopy(db)
        stale["companies"][0]["display_name"] = "Changed"
        stale_raw = (json.dumps(stale, indent=2, ensure_ascii=False) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "base SHA256"):
            verify_package(stale, package, stale_raw, report, approval)

    def test_rejects_separate_approval_mismatch(self):
        db, report, approval, raw, (package, *_rest) = self.build()
        changed = copy.deepcopy(approval)
        changed["reviewer"] = "another-reviewer"
        with self.assertRaisesRegex(ValueError, "Approval Manifest"):
            verify_package(db, package, raw, report, changed)

    def test_rejects_separate_claim_report_mismatch(self):
        db, report, approval, raw, (package, *_rest) = self.build()
        changed = copy.deepcopy(report)
        changed["claims"][0]["evidence_quote"] = "Changed quote."
        with self.assertRaisesRegex(ValueError, "original Claim report"):
            verify_package(db, package, raw, changed, approval)

    def test_rejects_tampered_operations_even_if_rehashed(self):
        db, report, approval, raw, (package, *_rest) = self.build()
        package["operations"][0]["path"] = "/companies/0/summary"
        body = {key: value for key, value in package.items() if key != "package_sha256"}
        package["package_sha256"] = sha256_json(body)
        with self.assertRaisesRegex(ValueError, "deterministic rebuild"):
            verify_package(db, package, raw, report, approval)

    def test_rejects_future_review_date(self):
        db, report, approval, raw = fixture()
        approval["reviewed_at"] = "2099-01-01"
        approval["evidence"]["checked_at"] = "2098-12-31"
        approval["claim"]["last_reviewed"] = "2099-01-01"
        with self.assertRaisesRegex(ValueError, "future"):
            build_package(db, report, approval, raw, "2099-01-02T00:00:00Z")

    def test_cli_build_and_verify_round_trip(self):
        db, report, approval, raw = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content in {
                "registry.json": raw.decode(),
                "claims.json": json.dumps(report),
                "approval.json": json.dumps(approval),
            }.items():
                (root / name).write_text(content, encoding="utf-8")
            common = [sys.executable, str(ROOT / "scripts/build_product_creation_proposal.py")]
            build = subprocess.run(common + [
                "build", "--company-profiles", str(root / "registry.json"),
                "--claim-report", str(root / "claims.json"), "--approval", str(root / "approval.json"),
                "--proposal-output", str(root / "proposal.json"),
                "--database-output", str(root / "updated.json"),
                "--patch-output", str(root / "patch.json"), "--audit-output", str(root / "audit.json"),
                "--diff-output", str(root / "change.diff")
            ], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            verify = subprocess.run(common + [
                "verify", "--company-profiles", str(root / "registry.json"),
                "--claim-report", str(root / "claims.json"), "--approval", str(root / "approval.json"),
                "--proposal", str(root / "proposal.json"),
                "--database-output", str(root / "verified.json"),
                "--patch-output", str(root / "verified-patch.json"),
                "--audit-output", str(root / "verified-audit.json"),
                "--diff-output", str(root / "verified.diff")
            ], capture_output=True, text=True)
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
            self.assertEqual(json.loads((root / "verified.json").read_text()), json.loads((root / "updated.json").read_text()))


if __name__ == "__main__":
    unittest.main()
