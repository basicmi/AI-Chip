import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from discover_model_catalog import discover

class DiscoveryTests(unittest.TestCase):
    def test_discovery_never_adds_support_records(self):
        catalog = {"models": [
            {"model_id": "publisher/checkpoint", "catalog_checked_at": "2026-11-13",
             "catalog_source_status": "official_model_card"}]}
        def mock(mid): return {"status": "observed", "repo_sha": "abc123"}
        report = discover(catalog, query=mock,
            publisher_search=lambda _: {"candidates": [{"model_id": "Qwen/new-checkpoint", "status": "discovery_candidate_not_reviewed"}], "source_errors": []})
        self.assertTrue(report["read_only"])
        self.assertEqual(report["model_count"], 1)
        self.assertEqual(report["observed"], 1)
        self.assertNotIn("support_paths", report)
        self.assertEqual(report["new_publisher_candidates"][0]["model_id"], "Qwen/new-checkpoint")

if __name__ == "__main__":
    unittest.main()
