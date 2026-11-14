import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_intelligence_evidence_graph import graph_for_claims, markdown_report


def claim(cid, statement, value, url, *, unit="GB", qualifiers=None, scope=None):
    return {
        "claim_id": cid, "candidate_id": "candidate-" + cid,
        "topic": "memory_capacity", "statement": statement, "value": value, "unit": unit,
        "qualifiers": qualifiers if qualifiers is not None else [],
        "scope": scope if scope is not None else {"status": "explicit_per_unit", "text": "per GPU"},
        "source": {"url": url, "publisher": "Vendor", "source_type": "vendor_primary",
                   "independence": "vendor"}, "review_status": "unverified_candidate"
    }


def report(*claims):
    return {"schema_version": "1.0", "claims": list(claims)}


def annotated(*items):
    return {"schema_version": "1.0", "claims": {
        cid: {
            "subject_key": "vendor:gpu-x",
            "metric_key": "hbm-capacity",
            "context_key": "sku-x:fp8:per-gpu:peak",
            "comparison_kind": "specification",
            "evidence_origin_key": origin,
        } for cid, origin in items
    }}


class EvidenceGraphTests(unittest.TestCase):
    def setUp(self):
        self.a = claim("a", "GPU X contains 180 GB HBM per GPU", 180,
                       "https://vendor.example/announcement")
        self.b = claim("b", "GPU X contains 180 GB HBM per GPU", 180,
                       "https://news.example/reprint")
        self.c = claim("c", "GPU X contains 192 GB HBM per GPU", 192,
                       "https://independent.example/analysis")

    def test_exact_duplicates_do_not_prove_independence(self):
        graph = graph_for_claims(report(self.a, self.b), generated_at="2026-11-14T00:00:00Z")
        self.assertEqual(graph["summary"]["exact_statement_duplicate_clusters"], 1)
        self.assertEqual(graph["duplicate_clusters"][0]["distinct_source_document_count"], 2)
        self.assertFalse(graph["duplicate_clusters"][0]["independent_corroboration"])
        self.assertEqual(graph["summary"]["independently_verified_claims"], 0)
        self.assertEqual(graph["scoped_comparisons"], [])

    def test_explicit_scoped_specification_conflict_only(self):
        a = annotated(("a", "vendor-release"), ("c", "independent-study"))
        graph = graph_for_claims(report(self.a, self.c), annotations=a)
        comparison = graph["scoped_comparisons"][0]
        self.assertEqual(comparison["status"], "possible_specification_conflict")
        self.assertTrue(comparison["unit_comparable"])
        self.assertEqual(comparison["origin_count"], 2)
        self.assertFalse(comparison["independently_verified"])
        self.assertEqual(graph["summary"]["possible_specification_conflicts"], 1)
        self.assertIn("Review protocol", markdown_report(graph))

    def test_same_origin_is_not_independent_corroboration(self):
        graph = graph_for_claims(report(self.a, self.b), annotations=annotated(
            ("a", "original-vendor-release"), ("b", "original-vendor-release")))
        comp = graph["scoped_comparisons"][0]
        self.assertEqual(comp["origin_count"], 1)
        self.assertEqual(comp["status"], "numerical_agreement_candidate")
        self.assertIn("not count as independent", comp["independence_warning"])

    def test_different_context_not_compared(self):
        a = annotated(("a", "vendor"), ("c", "study"))
        a["claims"]["c"]["context_key"] = "sku-x:fp8:per-rack:peak"
        graph = graph_for_claims(report(self.a, self.c), annotations=a)
        self.assertEqual(graph["scoped_comparisons"], [])
        self.assertEqual(graph["summary"]["possible_specification_conflicts"], 0)

    def test_different_units_not_marked_conflict(self):
        c = copy.deepcopy(self.c)
        c["unit"] = "TB"
        graph = graph_for_claims(report(self.a, c),
                                 annotations=annotated(("a", "vendor"), ("c", "study")))
        self.assertEqual(graph["scoped_comparisons"][0]["status"], "unit_or_scope_mismatch")

    def test_measurements_not_specification_conflicts(self):
        annotations = annotated(("a", "vendor"), ("c", "study"))
        for row in annotations["claims"].values():
            row["comparison_kind"] = "measurement"
        graph = graph_for_claims(report(self.a, self.c), annotations=annotations)
        self.assertEqual(graph["scoped_comparisons"][0]["status"], "different_values_require_context_review")
        self.assertEqual(graph["summary"]["possible_specification_conflicts"], 0)

    def test_rejects_unknown_claim_annotations(self):
        annotations = annotated(("z", "vendor"))
        with self.assertRaisesRegex(ValueError, "unknown claim ID"):
            graph_for_claims(report(self.a), annotations=annotations)

    def test_rejects_missing_context_or_unknown_fields(self):
        annotations = annotated(("a", "vendor"))
        annotations["claims"]["a"].pop("context_key")
        with self.assertRaisesRegex(ValueError, "exactly"):
            graph_for_claims(report(self.a), annotations=annotations)

    def test_rejects_claim_promotion(self):
        promoted = copy.deepcopy(self.a)
        promoted["review_status"] = "verified"
        with self.assertRaisesRegex(ValueError, "unverified"):
            graph_for_claims(report(promoted))

    def test_rejects_duplicate_claim_id(self):
        with self.assertRaisesRegex(ValueError, "duplicated"):
            graph_for_claims(report(self.a, self.a))

    def test_rejects_non_https_source(self):
        tampered = copy.deepcopy(self.a)
        tampered["source"]["url"] = "http://example.com"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            graph_for_claims(report(tampered))

    def test_qualitative_claims_not_auto_compared(self):
        a = claim("a", "GPU X supports FP8", None, "https://vendor.example/spec", unit=None)
        b = claim("b", "GPU X supports FP8", None, "https://review.example/spec", unit=None)
        annotation = annotated(("a", "vendor"), ("b", "reviewer"))
        annotation["claims"]["a"]["comparison_kind"] = "capability"
        annotation["claims"]["b"]["comparison_kind"] = "capability"
        graph = graph_for_claims(report(a, b), annotations=annotation)
        self.assertEqual(graph["scoped_comparisons"][0]["status"], "non_numeric_claims_not_automatically_comparable")
        self.assertEqual(graph["summary"]["independently_verified_claims"], 0)


if __name__ == "__main__":
    unittest.main()
