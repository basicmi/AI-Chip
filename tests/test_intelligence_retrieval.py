"""Offline tests for bounded known-item arXiv retrieval evaluation."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_intelligence_retrieval import evaluate, paper_id, markdown_report

GOLDEN = json.loads((ROOT / "data/intelligence-retrieval-golden.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "data/intelligence-sources.json").read_text(encoding="utf-8"))


def fixture(*, unavailable=False):
    ids = ["arxiv-ai-systems", "arxiv-ai-hardware", "arxiv-ai-kernels-compilers", "arxiv-agentic-physical-ai"]
    return {
        "generated_at": "2026-11-16T07:00:00Z",
        "lookback_days": 45,
        "source_results": [
            {"source_id": sid, "kind": "arxiv_api",
             "status": ("unavailable" if unavailable and i == 0 else "observed"),
             "pagination": {"max_pages": 2, "per_page": 50, "pages_fetched": 1,
                            "paging_cap_reached": False}}
            for i, sid in enumerate(ids)
        ],
        "all_observations": [
            {"source_id": "arxiv-ai-systems", "candidate_id": "arxiv:2611.18459v2"},
            {"source_id": "arxiv-ai-hardware", "candidate_id": "arxiv:2611.18422v1"},
        ],
    }


class KnownItemRecallTests(unittest.TestCase):
    def test_seed_is_positive_and_dated(self):
        examples = GOLDEN["examples"]
        self.assertEqual(len(examples), 16)
        self.assertEqual(len({paper_id(x["paper_id"]) for x in examples}), 16)
        self.assertTrue(all(x.get("published_on") and x.get("rationale") for x in examples))

    def test_version_insensitive_match_and_recall(self):
        result = evaluate(GOLDEN, fixture(), registry=REGISTRY)
        self.assertTrue(result["scorable"])
        self.assertEqual(result["eligible_count"], 16)
        self.assertEqual(result["rates"]["25"]["hits"], 2)
        self.assertEqual(len(result["missing"]), 14)
        self.assertIn("not representative", markdown_report(result).lower())

    def test_per_shard_rank_not_global_rank(self):
        report = fixture()
        report["all_observations"] = [
            {"source_id": "arxiv-ai-systems", "candidate_id": f"arxiv:2611.{90000+i}v1"}
            for i in range(26)
        ] + [{"source_id": "arxiv-ai-hardware", "candidate_id": "arxiv:2611.18459v3"}]
        result = evaluate(GOLDEN, report, registry=REGISTRY)
        self.assertEqual(result["rates"]["25"]["hits"], 1)

    def test_unavailable_shard_is_not_scored_as_failure(self):
        result = evaluate(GOLDEN, fixture(unavailable=True), registry=REGISTRY)
        self.assertFalse(result["scorable"])
        self.assertEqual(result["unavailable_arxiv_sources"], ["arxiv-ai-systems"])

    def test_window_scope_is_explicit(self):
        data = {**GOLDEN, "examples": [{**GOLDEN["examples"][0], "published_on": "2026-08-01"}]}
        result = evaluate(data, fixture(), registry=REGISTRY)
        self.assertEqual(result["eligible_count"], 0)
        self.assertEqual(result["out_of_window_count"], 1)
        self.assertIsNone(result["rates"]["25"]["recall"])
        self.assertFalse(result["scorable"])

    def test_registry_mismatch_fails_closed(self):
        report = fixture()
        report["source_results"] = report["source_results"][:-1]
        with self.assertRaisesRegex(ValueError, "source IDs"):
            evaluate(GOLDEN, report, registry=REGISTRY)

    def test_duplicate_and_invalid_ids_are_rejected(self):
        first = GOLDEN["examples"][0]
        dup = {**GOLDEN, "examples": [first, {**first, "paper_id": paper_id(first["paper_id"])}]}
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            evaluate(dup, fixture())
        with self.assertRaisesRegex(ValueError, "Invalid arXiv ID"):
            paper_id("http://attacker.example/abs/2611.18459")


if __name__ == "__main__":
    unittest.main()
