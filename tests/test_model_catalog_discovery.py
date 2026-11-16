import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from discover_model_catalog import discover, discover_publisher_candidates
from run_intelligence_discovery import candidate_from_hf


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.close()


class DiscoveryTests(unittest.TestCase):
    def test_discovery_never_adds_support_records(self):
        catalog = {"models": [
            {"model_id": "publisher/checkpoint", "catalog_checked_at": "2026-11-13",
             "catalog_source_status": "official_model_card"}]}
        def mock(mid):
            return {"status": "observed", "repo_sha": "abc123"}
        report = discover(catalog, query=mock,
            publisher_search=lambda _, **__: {
                "candidates": [{"model_id": "Qwen/new-checkpoint",
                                "status": "discovery_candidate_not_reviewed"}],
                "source_errors": []},
            now=datetime(2026, 11, 16, tzinfo=timezone.utc))
        self.assertTrue(report["read_only"])
        self.assertEqual(report["model_count"], 1)
        self.assertEqual(report["observed"], 1)
        self.assertNotIn("support_paths", report)
        self.assertEqual(report["new_publisher_candidates"][0]["model_id"], "Qwen/new-checkpoint")

    def test_publisher_listing_requests_expanded_metadata_and_filters_old_repos(self):
        now = datetime(2026, 11, 16, tzinfo=timezone.utc)
        payload = [
            {"id": "Qwen/recent-model", "createdAt": "2026-11-10T00:00:00Z",
             "lastModified": "2026-11-12T00:00:00Z", "sha": "abc",
             "pipeline_tag": "text-generation", "library_name": "transformers",
             "tags": ["text-generation", "safetensors"], "downloads": 1200,
             "likes": 30, "gated": False, "private": False},
            {"id": "Qwen/old-model", "createdAt": "2026-08-01T00:00:00Z"},
            {"id": "Qwen/undated-model"},
            {"id": "Qwen/already-curated", "createdAt": "2026-11-11T00:00:00Z"},
            {"id": "other/foreign-model", "createdAt": "2026-11-12T00:00:00Z"},
        ]
        requests = []
        def opener(request, timeout):
            requests.append((request.full_url, timeout))
            return FakeResponse(json.dumps(payload).encode())
        result = discover_publisher_candidates(
            {"models": [{"model_id": "Qwen/already-curated"}]},
            opener=opener, days=45, now=now, limit=30)
        self.assertEqual(len(requests), 6)
        query = parse_qs(urlsplit(requests[0][0]).query)
        self.assertEqual(query["author"], ["Qwen"])
        self.assertEqual(query["limit"], ["30"])
        self.assertIn("createdAt", query["expand[]"])
        self.assertIn("lastModified", query["expand[]"])
        self.assertIn("pipeline_tag", query["expand[]"])
        ids = {item["model_id"] for item in result["candidates"]}
        self.assertEqual(ids, {"Qwen/recent-model", "Qwen/undated-model"})
        recent = next(item for item in result["candidates"] if item["model_id"] == "Qwen/recent-model")
        self.assertEqual(recent["repo_sha"], "abc")
        self.assertEqual(recent["pipeline_tag"], "text-generation")
        self.assertEqual(recent["downloads"], 1200)
        self.assertEqual(recent["tags"], ["text-generation", "safetensors"])
        self.assertEqual(recent["date_status"], "observed")
        undated = next(item for item in result["candidates"] if item["model_id"] == "Qwen/undated-model")
        self.assertEqual(undated["date_status"], "unknown")

    def test_publisher_listing_rejects_invalid_date_window(self):
        with self.assertRaisesRegex(ValueError, "days"):
            discover_publisher_candidates({"models": []}, days=0)

    def test_hf_candidate_preserves_listing_metadata_without_claiming_support(self):
        candidate = candidate_from_hf({
            "model_id": "Qwen/example", "created_at": "2026-11-10T00:00:00Z",
            "last_modified": "2026-11-12T00:00:00Z", "repo_sha": "abc",
            "pipeline_tag": "text-generation", "library_name": "transformers",
            "tags": ["text-generation"], "downloads": 100, "likes": 5,
            "gated": False, "private": False,
            "status": "discovery_candidate_not_reviewed",
        })
        self.assertEqual(candidate["published_at"], "2026-11-10T00:00:00Z")
        self.assertEqual(candidate["updated_at"], "2026-11-12T00:00:00Z")
        self.assertEqual(candidate["evidence_scope"], "publisher_listing_metadata_only")
        self.assertEqual(candidate["source_type"], "publisher_listing")
        self.assertEqual(candidate["pipeline_tag"], "text-generation")
        self.assertEqual(candidate["repo_sha"], "abc")
        popularity_only_change = candidate_from_hf({
            "model_id": "Qwen/example", "created_at": "2026-11-10T00:00:00Z",
            "last_modified": "2026-11-12T00:00:00Z", "repo_sha": "abc",
            "pipeline_tag": "text-generation", "library_name": "transformers",
            "tags": ["text-generation"], "downloads": 9000, "likes": 500,
            "gated": False, "private": False,
            "status": "discovery_candidate_not_reviewed",
        })
        self.assertEqual(candidate["fingerprint"], popularity_only_change["fingerprint"])
        self.assertNotIn("support_paths", candidate)


if __name__ == "__main__":
    unittest.main()
