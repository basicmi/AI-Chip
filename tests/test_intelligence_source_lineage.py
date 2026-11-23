import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_intelligence_evidence_graph import graph_for_claims
from review_intelligence_source_lineage import prepare, evaluate, markdown_report


def claim(cid, url, *, statement="GPU X reaches 180 GB HBM.", value=180):
    return {
        "claim_id": cid, "candidate_id": "candidate-" + cid,
        "statement": statement, "value": value, "unit": "GB",
        "topic": "memory_capacity", "scope": {"status": "explicit", "text": "per GPU"},
        "qualifiers": [], "review_status": "unverified_candidate",
        "source": {"url": url, "publisher": "Publisher " + cid,
                   "source_type": "vendor_primary", "independence": "vendor"},
    }


def graph():
    return graph_for_claims({
        "schema_version": "1.0",
        "claims": [
            claim("a", "https://vendor.example/release"),
            claim("b", "https://press.example/reprint"),
            claim("c", "https://lab.example/results"),
            claim("d", "https://vendor.example/other", statement="Different Claim."),
        ],
    }, generated_at="2026-11-23T00:00:00Z")


def reviewed(origin, relation, reviewer="reviewer-1", checked=True):
    return {
        "origin_key": origin, "relationship": relation, "reviewer": reviewer,
        "source_checked": checked,
        "rationale": "I reviewed the original document and compared the underlying quoted source material.",
    }


class LineageReviewTests(unittest.TestCase):
    def test_prepares_multiple_source_duplicate_cluster_without_verification(self):
        packet = prepare(graph())
        self.assertEqual(packet["summary"]["selected_clusters"], 1)
        self.assertEqual(packet["summary"]["multi_document_duplicate_clusters"], 1)
        self.assertEqual(len(packet["clusters"][0]["sources"]), 3)
        self.assertTrue(all(not row["origin_key"] for row in packet["clusters"][0]["sources"]))
        self.assertFalse(packet["policy"]["independent_corroboration_automatically_verified"])
        self.assertEqual(evaluate(packet)["fully_reviewed_clusters"], 0)

    def test_identifies_reprint_same_origin_only_after_manual_labels(self):
        packet = prepare(graph())
        docs = packet["clusters"][0]["sources"]
        docs[0].update(reviewed("source-vendor-1", "original_material"))
        docs[1].update(reviewed("source-vendor-1", "syndicated_reprint"))
        docs[2].update(reviewed("source-vendor-1", "syndicated_reprint"))
        result = evaluate(packet)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["same_reviewer_assigned_origin_clusters"], 1)
        self.assertEqual(result["different_reviewer_assigned_origin_clusters"], 0)
        self.assertEqual(result["automatically_verified_independent_evidence"], 0)
        self.assertIn("not independent verification", markdown_report(result))

    def test_distinct_origins_are_not_factual_corroboration(self):
        packet = prepare(graph())
        for i, doc in enumerate(packet["clusters"][0]["sources"]):
            doc.update(reviewed("origin-" + str(i), "independent_measurement_claim"))
        result = evaluate(packet)
        self.assertEqual(result["different_reviewer_assigned_origin_clusters"], 1)
        self.assertEqual(result["automatically_verified_independent_evidence"], 0)
        self.assertEqual(result["completed_clusters"][0]["distinct_reviewer_assigned_origin_keys"], 3)

    def test_partial_annotation_is_pending_not_independent(self):
        packet = prepare(graph())
        packet["clusters"][0]["sources"][0].update(reviewed("origin-one", "original_material"))
        result = evaluate(packet)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["fully_reviewed_clusters"], 0)

    def test_uninspected_source_can_only_be_unknown(self):
        packet = prepare(graph())
        doc = packet["clusters"][0]["sources"][0]
        doc.update(reviewed("unknown-origin", "syndicated_reprint", checked=False))
        with self.assertRaisesRegex(ValueError, "uninspected"):
            evaluate(packet)
        doc["relationship"] = "unknown"
        self.assertEqual(evaluate(packet)["fully_reviewed_clusters"], 0)

    def test_rejects_missing_rationale_or_invalid_origin(self):
        packet = prepare(graph())
        doc = packet["clusters"][0]["sources"][0]
        doc.update(reviewed("origin with spaces", "original_material"))
        with self.assertRaisesRegex(ValueError, "valid origin"):
            evaluate(packet)
        doc.update(reviewed("origin-x", "original_material"))
        doc["rationale"] = "too short"
        with self.assertRaisesRegex(ValueError, "rationale"):
            evaluate(packet)

    def test_duplicate_sources_or_clusters_are_rejected(self):
        packet = prepare(graph())
        packet["clusters"][0]["sources"][1]["source_id"] = packet["clusters"][0]["sources"][0]["source_id"]
        with self.assertRaisesRegex(ValueError, "duplicate lineage source"):
            evaluate(packet)
        packet = prepare(graph())
        packet["clusters"].append(copy.deepcopy(packet["clusters"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate lineage cluster"):
            evaluate(packet)

    def test_refuses_graph_asserting_independent_corroboration(self):
        g = graph()
        g["duplicate_clusters"][0]["independent_corroboration"] = True
        with self.assertRaisesRegex(ValueError, "must not assert"):
            prepare(g)

    def test_checks_graph_claim_source_integrity(self):
        g = graph()
        g["duplicate_clusters"][0]["distinct_source_document_count"] = 9
        with self.assertRaisesRegex(ValueError, "source count"):
            prepare(g)
        g = graph()
        g["edges"] = [e for e in g["edges"] if e.get("relation") != "extracted_from"]
        with self.assertRaisesRegex(ValueError, "without a source"):
            prepare(g)

    def test_skips_same_document_duplicates(self):
        g = graph_for_claims({
            "schema_version": "1.0",
            "claims": [claim("a", "https://vendor.example/a"), claim("b", "https://vendor.example/a")],
        })
        self.assertEqual(prepare(g)["summary"]["selected_clusters"], 0)

    def test_cluster_limit_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "max_clusters"):
            prepare(graph(), max_clusters=101)
        with self.assertRaisesRegex(ValueError, "max_clusters"):
            prepare(graph(), max_clusters=0)

    def test_does_not_mutate_graph(self):
        g = graph()
        before = copy.deepcopy(g)
        prepare(g)
        self.assertEqual(g, before)


if __name__ == "__main__":
    unittest.main()
