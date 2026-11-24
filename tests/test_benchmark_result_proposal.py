import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_benchmark_result_proposal import build_package, verify_package
from validate_benchmark_results import summarize


class BenchmarkResultProposalTests(unittest.TestCase):
    def setUp(self):
        self.source_url = "https://vendor.example.com/benchmark/results"
        self.database = {
            "schema_version": "1.0",
            "database_version": "test",
            "last_imported_at": "2026-11-01",
            "scope": "test registry",
            "sources": [{
                "id": "vendor-benchmark",
                "name": "Vendor Benchmark",
                "publisher": "Vendor",
                "source_class": "vendor_reported",
                "results_url": self.source_url,
                "record_count": 0,
                "notes": "Existing registered source",
            }],
            "summary": summarize([]),
            "records": [],
        }
        self.raw = (json.dumps(self.database, ensure_ascii=False, indent=2) + "\n").encode()
        self.approval = {
            "schema_version": "1.0",
            "approval_id": "review-benchmark-001",
            "reviewer": "reviewer@example",
            "reviewed_at": "2026-11-20",
            "decision": "approved_new_benchmark_result",
            "source_id": "vendor-benchmark",
            "review_notes": "Inspected the original results page and confirmed the workload and system context.",
            "record": {
                "id": "vendor-benchmark-model-a-001",
                "source_id": "vendor-benchmark",
                "source_class": "vendor_reported",
                "evidence_level": "vendor_reported",
                "benchmark_suite": "Vendor Inference Benchmark",
                "benchmark_version": "2026.1",
                "publication_date": "2026-11-18",
                "submitter": "Vendor",
                "accelerator_vendor": "Vendor",
                "platform_id": None,
                "product_id": None,
                "system_type": "datacenter",
                "system_name": "Eight accelerator server",
                "division": "closed",
                "availability": "available",
                "model": "Model A",
                "scenario": "offline",
                "result_value": 1250.0,
                "result_unit": "tokens/s",
                "accuracy_text": "Not reported",
                "inferred": False,
                "power_metrics_available": False,
                "design_power_watts": None,
                "system": {"nodes": 1, "accelerator_model": "Vendor X", "accelerators_per_node": 8},
                "software": {"framework": "Framework X"},
                "notes": "Single reviewed vendor-reported result.",
                "compliance": "Not independently assessed",
                "errors": 0,
                "weight_data_types": "BF16",
                "source_record_key": "vendor-row-001",
                "source_location": "results table row 1",
                "source_url": self.source_url,
                "dataset_url": None,
                "release_url": None,
            },
        }

    def test_build_and_verify_exact_append(self):
        package, patch, audit, diff, updated = build_package(
            self.database, self.raw, self.approval, "2026-11-21T12:00:00Z"
        )
        self.assertEqual(len(updated["records"]), 1)
        self.assertEqual(updated["sources"][0]["record_count"], 1)
        self.assertEqual(updated["summary"], summarize(updated["records"]))
        self.assertEqual([op["op"] for op in patch["operations"]], ["add", "replace", "replace", "replace", "replace"])
        self.assertFalse(audit["source_truth_verified"])
        self.assertFalse(package["policy"]["evidence_level_promoted"])
        verified, patch2, audit2, diff2 = verify_package(
            self.database, package, self.raw, self.approval
        )
        self.assertEqual(verified, updated)
        self.assertEqual(patch2, patch)
        self.assertEqual(audit2, audit)
        self.assertEqual(diff2, diff)

    def test_reject_duplicate_record_id(self):
        db = copy.deepcopy(self.database)
        existing = copy.deepcopy(self.approval["record"])
        db["records"] = [existing]
        db["sources"][0]["record_count"] = 1
        db["summary"] = summarize(db["records"])
        raw = (json.dumps(db, ensure_ascii=False, indent=2) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "ID already exists"):
            build_package(db, raw, self.approval, "2026-11-21T12:00:00Z")

    def test_reject_duplicate_source_key(self):
        db = copy.deepcopy(self.database)
        existing = copy.deepcopy(self.approval["record"])
        existing["id"] = "another-result"
        db["records"] = [existing]
        db["sources"][0]["record_count"] = 1
        db["summary"] = summarize(db["records"])
        raw = (json.dumps(db, ensure_ascii=False, indent=2) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "source_record_key already exists"):
            build_package(db, raw, self.approval, "2026-11-21T12:00:00Z")

    def test_reject_evidence_promotion(self):
        approval = copy.deepcopy(self.approval)
        approval["record"]["evidence_level"] = "independent_measurement"
        with self.assertRaisesRegex(ValueError, "no evidence promotion"):
            build_package(self.database, self.raw, approval, "2026-11-21T12:00:00Z")

    def test_reject_unregistered_source_url(self):
        approval = copy.deepcopy(self.approval)
        approval["record"]["source_url"] = "https://other.example/result"
        with self.assertRaisesRegex(ValueError, "must match a URL"):
            build_package(self.database, self.raw, approval, "2026-11-21T12:00:00Z")

    def test_reject_power_claims_in_v1(self):
        approval = copy.deepcopy(self.approval)
        approval["record"]["power_metrics_available"] = True
        with self.assertRaisesRegex(ValueError, "does not accept power claims"):
            build_package(self.database, self.raw, approval, "2026-11-21T12:00:00Z")

    def test_reject_tampered_package(self):
        package, _, _, _, _ = build_package(
            self.database, self.raw, self.approval, "2026-11-21T12:00:00Z"
        )
        package["operations"][0]["value"]["result_value"] = 999999
        with self.assertRaisesRegex(ValueError, "differs from deterministic rebuild"):
            verify_package(self.database, package, self.raw, self.approval)

    def test_reject_stale_base_registry(self):
        package, _, _, _, _ = build_package(
            self.database, self.raw, self.approval, "2026-11-21T12:00:00Z"
        )
        changed = copy.deepcopy(self.database)
        changed["database_version"] = "newer"
        raw = (json.dumps(changed, ensure_ascii=False, indent=2) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "base SHA256"):
            verify_package(changed, package, raw, self.approval)


if __name__ == "__main__":
    unittest.main()
