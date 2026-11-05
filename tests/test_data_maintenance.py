import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_evidence_links import classify_status, collect_links_from_data
from report_profile_review_queue import build_review_queue, freshness_status


class LinkAuditTests(unittest.TestCase):
    def test_http_status_classification(self):
        self.assertEqual(classify_status(200, "https://example.com"), "ok")
        self.assertEqual(classify_status(301, "https://example.com", "https://example.org"), "redirected")
        self.assertEqual(classify_status(403, "https://example.com"), "blocked")
        self.assertEqual(classify_status(429, "https://example.com"), "blocked")
        self.assertEqual(classify_status(404, "https://example.com"), "broken")
        self.assertEqual(classify_status(503, "https://example.com"), "http_error")

    def test_link_collection_deduplicates_urls_and_keeps_context(self):
        profiles = {
            "companies": [{
                "id": "sample",
                "display_name": "Sample Vendor",
                "references": [{"url": "https://example.com/spec", "label": "Spec page"}],
                "evidence": [{"url": "https://example.com/spec", "title": "Official specs"}],
            }]
        }
        compatibility = {
            "platforms": [{"id": "sample-platform", "name": "Sample", "evidence_urls": ["https://example.com/platform"]}],
            "integrations": [{"id": "sample-runtime", "project": "Runtime", "project_url": "https://example.com/runtime",
                              "evidence": [{"url": "https://example.com/runtime", "claim": "Runtime docs"}]}],
        }
        workloads = {"paths": []}
        benchmarks = {"projects": [{"id": "sample-bench", "name": "Sample benchmark",
                                    "official_url": "https://example.com/bench"}]}
        records = collect_links_from_data(profiles, compatibility, workloads, benchmarks)
        self.assertEqual(len(records), 4)
        self.assertEqual(len(records["https://example.com/spec"]), 2)
        self.assertEqual(len(records["https://example.com/runtime"]), 2)


class ReviewQueueTests(unittest.TestCase):
    def test_freshness_windows(self):
        today = date(2026, 11, 5)
        self.assertEqual(freshness_status(None, today), "unreviewed")
        self.assertEqual(freshness_status("2026-10-01", today), "fresh")
        self.assertEqual(freshness_status("2026-07-01", today), "review_due")
        self.assertEqual(freshness_status("2026-01-01", today), "stale")
        self.assertEqual(freshness_status("not-a-date", today), "invalid_date")

    def test_review_queue_marks_integration_only_as_not_tested(self):
        profiles = {
            "registry_reviewed_at": "2026-11-05",
            "companies": [{
                "id": "sample",
                "display_name": "Sample Vendor",
                "profile_status": "partially_reviewed",
                "products": [{"id": "sample-chip", "name": "Sample Chip"}],
                "claims": [],
                "evidence": [],
                "references": [{"id": "ref-1", "label": "Old source", "review_status": "unreviewed"}],
            }],
        }
        compatibility = {"platforms": [], "integrations": []}
        workloads = {"paths": [{"id": "sample-path", "status": "integration_only"}]}
        report = build_review_queue(profiles, compatibility, workloads, date(2026, 11, 5))
        self.assertIn("Sample Vendor", report)
        self.assertIn("Carried-over references awaiting claim-level review", report)
        self.assertIn("integration_only", report)
        self.assertIn("not workload-tested", report.lower())


if __name__ == "__main__":
    unittest.main()
