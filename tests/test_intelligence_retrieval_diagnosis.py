"""Tests for evidence-based diagnosis of missed arXiv retrieval seeds."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from diagnose_intelligence_retrieval import diagnose, query_profile, contains_phrase

GOLDEN = json.loads((ROOT / "data/intelligence-retrieval-golden.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "data/intelligence-sources.json").read_text(encoding="utf-8"))


def evaluation(missing_ids):
    sources = [
        {"source_id": row["id"]}
        for row in REGISTRY["sources"]
        if row.get("kind") == "arxiv_api" and row.get("active", True)
    ]
    return {
        "benchmark_id": GOLDEN["benchmark_id"],
        "discovery_generated_at": "2026-11-16T09:10:11Z",
        "sources": sources,
        "missing": [{"paper_id": pid} for pid in missing_ids],
    }


class RetrievalDiagnosisTests(unittest.TestCase):
    def test_query_parser_extracts_categories_and_phrases(self):
        profile = query_profile('cat:cs.DC AND (all:"LLM inference" OR all:NCCL)')
        self.assertEqual(profile["categories"], {"cs.DC"})
        self.assertEqual(profile["terms"], ["LLM inference", "NCCL"])

    def test_hyphen_and_punctuation_normalization(self):
        self.assertTrue(contains_phrase("GPU-initiated communication, all-to-all", "GPU initiated communication"))
        self.assertTrue(contains_phrase("State–action–effect relation", "state action effect"))

    def test_gpu_networking_miss_is_query_vocabulary_gap(self):
        result = diagnose(GOLDEN, evaluation(["2611.18145"]), REGISTRY)
        item = result["diagnoses"][0]
        self.assertEqual(item["classification"], "query_vocabulary_gap")
        self.assertIn("arxiv-ai-systems", item["category_covered_sources"])
        self.assertIn("GPU-initiated communication", item["candidate_query_terms"])

    def test_existing_query_phrase_match_is_not_called_a_query_gap(self):
        result = diagnose(GOLDEN, evaluation(["2611.08156"]), REGISTRY)
        item = result["diagnoses"][0]
        self.assertEqual(item["classification"], "query_lexical_match_but_not_returned")
        self.assertIn("arxiv-agentic-physical-ai", item["existing_query_term_matches"])

    def test_unknown_category_metadata_remains_unknown(self):
        result = diagnose(GOLDEN, evaluation(["2611.10832"]), REGISTRY)
        item = result["diagnoses"][0]
        self.assertEqual(item["classification"], "lexical_gap_category_unknown")
        self.assertEqual(item["arxiv_categories"], [])

    def test_suggestions_must_be_grounded_in_abstract_excerpt(self):
        data = json.loads(json.dumps(GOLDEN))
        item = next(x for x in data["examples"] if x["paper_id"].endswith("2611.18145v1"))
        item["candidate_query_terms"] = ["invented phrase"]
        with self.assertRaisesRegex(ValueError, "Ungrounded"):
            diagnose(data, evaluation(["2611.18145"]), REGISTRY)

    def test_registry_mismatch_fails_closed(self):
        ev = evaluation(["2611.18145"])
        ev["sources"] = ev["sources"][:-1]
        with self.assertRaisesRegex(ValueError, "source IDs"):
            diagnose(GOLDEN, ev, REGISTRY)


if __name__ == "__main__":
    unittest.main()
