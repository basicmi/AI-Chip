import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from retrieve_performance_knowledge import retrieve


def make_entry(kid, verdict="supported", fixed=None, topic="runtime_scheduling",
               hypothesis="Decode TP reduces queueing and median TPOT",
               interpretation="Under the measured decode workload, queueing was lower."):
    return {
        "knowledge_id": kid, "knowledge_status": "human_reviewed_claim",
        "topic": topic, "verdict": verdict, "hypothesis": hypothesis,
        "reviewer_interpretation": interpretation,
        "applicability": "Only declared hardware and workload.",
        "limitations": "One controlled configuration; no cross-device transfer.",
        "scope": {"fixed_context": fixed or {
            "hardware": {"gpu": "A100", "num_gpus": 8},
            "model": "Model-X",
            "workload": {"isl": 4096, "batch_size": 32},
            "parallelism": {"tp": 8},
            "software": {"runtime": "v1"},
        }, "metric": {"key": "median_tpot", "unit": "ms", "direction": "lower"}},
        "evidence": [{"run_id": "b1", "condition": "baseline", "source_url": "https://example.org/b1"},
                     {"run_id": "t1", "condition": "treatment", "source_url": "https://example.org/t1"}],
        "evidence_identity": {"record_id": kid}, "review_sha256": "a" * 64
    }


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.a = make_entry("pk-a")
        self.b = make_entry("pk-b", fixed={"hardware": {"gpu": "H100", "num_gpus": 8},
            "model": "Model-X", "workload": {"isl": 8192, "batch_size": 32},
            "parallelism": {"tp": 8}, "software": {"runtime": "v2"}})
        self.target = self.a["scope"]["fixed_context"]
        self.catalog = {"schema_version": "1.0", "entries": [self.b, self.a],
                        "potential_contradictions": []}

    def test_exact_context_priority(self):
        result = retrieve(self.catalog, "decode TP queueing", self.target,
            {"key": "median_tpot", "unit": "ms", "direction": "lower"})
        self.assertEqual(result["results"][0]["knowledge_id"], "pk-a")
        self.assertEqual(result["results"][0]["retrieval_tier"], "priority_human_review")
        self.assertEqual(result["results"][0]["metric_compatibility"], "exact_match")

    def test_mismatch_is_counterexample_not_direct_reuse(self):
        result = retrieve(self.catalog, "decode TP", self.target)
        by_id = {x["knowledge_id"]: x for x in result["results"]}
        self.assertEqual(by_id["pk-b"]["retrieval_tier"], "not_applicable_under_declared_context")
        self.assertTrue(by_id["pk-b"]["mismatched_context_fields"])

    def test_missing_context_is_exploratory(self):
        target = {"hardware": {"gpu": "A100", "num_gpus": 8}, "model": "Model-X"}
        result = retrieve(self.catalog, "decode TP", target)
        by_id = {x["knowledge_id"]: x for x in result["results"]}
        self.assertEqual(by_id["pk-a"]["retrieval_tier"], "exploratory_only")
        self.assertTrue(by_id["pk-a"]["missing_context_fields"])

    def test_refuted_claim_is_not_recommendation(self):
        catalog = {"schema_version": "1.0", "entries": [make_entry("pk-r", "refuted")]}
        result = retrieve(catalog, "decode TP", self.target)
        self.assertEqual(result["results"][0]["retrieval_tier"], "exploratory_only")
        self.assertEqual(result["results"][0]["verdict"], "refuted")

    def test_contradictions_are_returned(self):
        catalog = {"schema_version": "1.0", "entries": [self.a],
                   "potential_contradictions": [{"knowledge_id_a": "pk-a", "knowledge_id_b": "pk-z"}]}
        result = retrieve(catalog, "decode TP", self.target)
        self.assertEqual(len(result["related_potential_contradictions"]), 1)

    def test_metric_mismatch_and_limit(self):
        result = retrieve(self.catalog, "decode TP", self.target,
            {"key": "p99_tpot", "unit": "ms", "direction": "lower"}, 1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["metric_compatibility"], "mismatch_or_unknown")

    def test_invalid_catalog_entry_and_empty_target(self):
        with self.assertRaises(ValueError):
            retrieve({"schema_version": "1.0", "entries": [{"knowledge_id": "bad"}]},
                     "decode", self.target)
        with self.assertRaises(ValueError):
            retrieve(self.catalog, "decode", {})


if __name__ == "__main__":
    unittest.main()
