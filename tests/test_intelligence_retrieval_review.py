"""Tests for stratified retrieval review packets and human-label precision."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_intelligence_retrieval_review import build_review_packet
from evaluate_intelligence_retrieval_review import evaluate


def experiment():
    return {
        "experiment_id": "test-run-1",
        "discovery_generated_at": "2026-11-17T00:00:00Z",
        "status": "complete",
        "groups": [
            {
                "id": "gpu-comm", "name": "GPU communication", "status": "observed",
                "candidate_results": [
                    {"paper_id": "2611.10001", "candidate_id": "arxiv:2611.10001v1",
                     "title": "GPU systems paper A", "url": "https://arxiv.org/abs/2611.10001v1",
                     "excerpt": "GPU communication.", "predicted_relevance": "direct_ai_compute",
                     "observed_position": 1},
                    {"paper_id": "2611.10002", "candidate_id": "arxiv:2611.10002v1",
                     "title": "Generic paper B", "url": "https://arxiv.org/abs/2611.10002v1",
                     "excerpt": "Generic methods.", "predicted_relevance": "out_of_scope",
                     "observed_position": 2},
                    {"paper_id": "2611.10003", "candidate_id": "arxiv:2611.10003v1",
                     "title": "GPU paper C", "url": "https://arxiv.org/abs/2611.10003v1",
                     "excerpt": "GPU systems.", "predicted_relevance": "direct_ai_compute",
                     "observed_position": 3},
                ],
            },
            {
                "id": "agent-runtime", "name": "Agent runtime", "status": "observed",
                "candidate_results": [
                    {"paper_id": "2611.10001", "candidate_id": "arxiv:2611.10001v1",
                     "title": "GPU systems paper A", "url": "https://arxiv.org/abs/2611.10001v1",
                     "excerpt": "GPU communication.", "predicted_relevance": "direct_ai_compute",
                     "observed_position": 1},
                    {"paper_id": "2611.10004", "candidate_id": "arxiv:2611.10004v1",
                     "title": "Agent paper D", "url": "https://arxiv.org/abs/2611.10004v1",
                     "excerpt": "Agent systems.", "predicted_relevance": "adjacent_ai_systems",
                     "observed_position": 2},
                ],
            },
        ],
    }


class RetrievalReviewTests(unittest.TestCase):
    def test_sample_is_reproducible_and_group_stratified(self):
        first = build_review_packet(experiment(), sample_per_group=2)
        second = build_review_packet(experiment(), sample_per_group=2)
        self.assertEqual(first, second)
        self.assertEqual([row["sample_count"] for row in first["groups"]], [2, 2])
        self.assertEqual(len(first["candidates"]), len({row["paper_id"] for row in first["candidates"]}))
        shared = next(row for row in first["candidates"] if row["paper_id"] == "2611.10001")
        if "gpu-comm" in shared["sampled_for_groups"] and "agent-runtime" in shared["sampled_for_groups"]:
            self.assertEqual(shared["sampled_for_groups"], ["agent-runtime", "gpu-comm"])

    def test_invalid_sample_size_rejected(self):
        with self.assertRaisesRegex(ValueError, "1..50"):
            build_review_packet(experiment(), sample_per_group=0)

    def test_pending_labels_do_not_produce_precision(self):
        packet = build_review_packet(experiment(), sample_per_group=2)
        report = evaluate(packet)
        self.assertEqual(report["status"], "pending")
        self.assertTrue(all(row["precision"] is None for row in report["groups"]))

    def test_fully_adjudicated_sample_produces_group_precision(self):
        packet = build_review_packet(experiment(), sample_per_group=2)
        for index, row in enumerate(packet["candidates"]):
            row["adjudication"]["label"] = "direct_ai_compute" if index % 2 == 0 else "out_of_scope"
            row["adjudication"]["reviewer"] = "reviewer-1"
        report = evaluate(packet)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["scorable_group_count"], 2)
        self.assertTrue(all(row["precision"] is not None for row in report["groups"]))
        self.assertTrue(all(row["wilson_95_interval"] is not None for row in report["groups"]))

    def test_uncertain_is_not_silently_counted_as_negative(self):
        packet = build_review_packet(experiment(), sample_per_group=2)
        row = packet["candidates"][0]
        row["adjudication"]["label"] = "uncertain"
        row["adjudication"]["reviewer"] = "reviewer-1"
        report = evaluate(packet)
        self.assertEqual(report["status"], "pending")
        self.assertGreater(sum(x["uncertain_count"] for x in report["groups"]), 0)

    def test_invalid_label_rejected(self):
        packet = build_review_packet(experiment(), sample_per_group=2)
        packet["candidates"][0]["adjudication"]["label"] = "probably_relevant"
        packet["candidates"][0]["adjudication"]["reviewer"] = "reviewer-1"
        with self.assertRaisesRegex(ValueError, "Invalid adjudication label"):
            evaluate(packet)

    def test_census_precision_is_exact_for_returned_set(self):
        packet = build_review_packet(experiment(), sample_per_group=50)
        for row in packet["candidates"]:
            row["adjudication"]["label"] = "out_of_scope"
            row["adjudication"]["reviewer"] = "reviewer-1"
        report = evaluate(packet)
        self.assertTrue(all(row["exact_for_returned_set"] for row in report["groups"]))
        self.assertTrue(all(row["wilson_95_interval"] is None for row in report["groups"]))


if __name__ == "__main__":
    unittest.main()
