import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_intelligence_quality import evaluate, markdown_report

GOLDEN = json.loads((ROOT / "data/intelligence-quality-golden.json").read_text(encoding="utf-8"))


class IntelligenceQualityEvaluationTests(unittest.TestCase):
    def test_golden_set_is_balanced_and_has_negative_controls(self):
        examples = GOLDEN["examples"]
        labels = [item["expected_relevance"] for item in examples]
        self.assertGreaterEqual(len(examples), 20)
        self.assertGreaterEqual(labels.count("direct_ai_compute"), 8)
        self.assertGreaterEqual(labels.count("adjacent_ai_systems"), 3)
        self.assertGreaterEqual(labels.count("out_of_scope"), 6)
        self.assertEqual(len({item["candidate_id"] for item in examples}), len(examples))

    def test_evaluation_emits_candidate_and_sentence_metrics(self):
        report = evaluate(GOLDEN)
        candidate = report["candidate_relevance"]
        claims = report["claim_extraction"]
        self.assertEqual(candidate["sample_count"], len(GOLDEN["examples"]))
        self.assertGreaterEqual(candidate["relevant_vs_out_of_scope"]["precision"], 0.90)
        self.assertGreaterEqual(candidate["relevant_vs_out_of_scope"]["recall"], 0.90)
        self.assertGreaterEqual(candidate["macro_f1"], 0.80)
        self.assertGreater(claims["evaluated_candidate_count"], 0)
        self.assertGreaterEqual(claims["precision"], 0.80)
        self.assertGreaterEqual(claims["recall"], 0.70)
        self.assertEqual(claims["evidence_quote_failures"], 0)
        self.assertIn("does not measure recall", markdown_report(report).lower())

    def test_metric_rows_are_scored_at_sentence_granularity(self):
        report = evaluate(GOLDEN)
        claims = report["claim_extraction"]
        self.assertGreaterEqual(claims["duplicate_claim_rows_collapsed_for_sentence_scoring"], 0)
        self.assertEqual(
            claims["true_positive_sentences"] + claims["false_negative_sentences"],
            sum(len(x.get("expected_claim_fragments", [])) for x in GOLDEN["examples"]),
        )


if __name__ == "__main__":
    unittest.main()
