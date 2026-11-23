import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_intelligence_evidence_quality import audit_evidence_quality, markdown_report


def candidate(candidate_id="candidate-a", **overrides):
    row = {
        "candidate_id": candidate_id,
        "source_id": "feed-a",
        "publisher": "Example Research Lab",
        "source_type": "research_paper",
        "independence": "independent",
        "url": "https://example.org/paper-a",
        "published_at": "2026-11-16T00:00:00Z",
        "evidence_scope": "abstract",
        "excerpt": "We built a GPU serving system that reduces decode latency by 20 percent.",
    }
    row.update(overrides)
    return row


def claim(claim_id="claim-a", candidate_id="candidate-a", **overrides):
    row = {
        "claim_id": claim_id,
        "candidate_id": candidate_id,
        "statement": "We built a GPU serving system that reduces decode latency by 20 percent.",
        "evidence_quote": "We built a GPU serving system that reduces decode latency by 20 percent.",
        "source": {
            "candidate_id": candidate_id,
            "source_id": "feed-a",
            "publisher": "Example Research Lab",
            "source_type": "research_paper",
            "independence": "independent",
            "url": "https://example.org/paper-a",
            "published_at": "2026-11-16T00:00:00Z",
            "evidence_scope": "abstract",
        },
        "evidence_class": "research_preprint",
        "assertion_class": "research_result_candidate",
        "review_status": "unverified_candidate",
    }
    row.update(overrides)
    return row


def inputs(claims=None, candidates=None, graph=None):
    claims = claims if claims is not None else [claim()]
    candidates = candidates if candidates is not None else [candidate()]
    graph = graph if graph is not None else {
        "schema_version": "1.0",
        "input_claim_count": len(claims),
        "summary": {
            "independently_verified_claims": 0,
            "unreviewed_claims": len(claims),
        },
        "nodes": [],
        "edges": [],
        "duplicate_clusters": [],
    }
    return (
        {"schema_version": "1.1", "review_queue": candidates},
        {"schema_version": "1.0", "claim_count": len(claims), "claims": claims},
        graph,
    )


class IntelligenceEvidenceQualityAuditTests(unittest.TestCase):
    def test_reports_grounded_quote_and_complete_provenance(self):
        report = audit_evidence_quality(*inputs(), generated_at="2026-11-17T00:00:00Z")
        summary = report["summary"]
        self.assertEqual(summary["claim_count"], 1)
        self.assertEqual(summary["quote_grounded_claims"], 1)
        self.assertEqual(summary["quote_grounding_rate"], 1.0)
        self.assertEqual(summary["provenance_complete_claims"], 1)
        self.assertEqual(summary["provenance_completeness_rate"], 1.0)
        self.assertEqual(summary["distinct_source_documents"], 1)
        self.assertEqual(summary["distinct_publishers"], 1)
        self.assertEqual(summary["claims_remaining_unverified"], 1)
        self.assertEqual(report["claim_audits"][0]["flags"], [])

    def test_detects_quote_not_found_and_statement_quote_mismatch(self):
        row = claim(evidence_quote="This sentence is not in the source.")
        discovery, claims, graph = inputs([row])
        report = audit_evidence_quality(discovery, claims, graph)
        flags = report["claim_audits"][0]["flags"]
        self.assertIn("evidence_quote_not_found_in_candidate_excerpt", flags)
        self.assertIn("claim_statement_quote_mismatch", flags)
        self.assertEqual(report["summary"]["quote_grounding_rate"], 0.0)

    def test_detects_source_metadata_mismatch(self):
        row = claim()
        row["source"]["publisher"] = "Different Publisher"
        report = audit_evidence_quality(*inputs([row]))
        self.assertEqual(report["summary"]["claims_with_source_metadata_mismatch"], 1)
        self.assertIn("claim_candidate_source_metadata_mismatch", report["claim_audits"][0]["flags"])

    def test_unknown_independence_is_not_counted_as_complete_provenance(self):
        source = dict(claim()["source"], independence="unknown")
        row = claim(source=source)
        report = audit_evidence_quality(*inputs([row]))
        self.assertEqual(report["summary"]["independence_label_counts"], {"unknown": 1})
        self.assertEqual(report["summary"]["provenance_complete_claims"], 0)
        self.assertIn("incomplete_source_provenance", report["claim_audits"][0]["flags"])

    def test_counts_reviewer_origin_annotations_without_calling_them_independent(self):
        graph = {
            "schema_version": "1.0",
            "input_claim_count": 1,
            "summary": {"independently_verified_claims": 0, "unreviewed_claims": 1},
            "nodes": [
                {"id": "origin-x", "type": "reviewer_assigned_evidence_origin", "origin_key": "same-lab-study"},
            ],
            "edges": [
                {"from": "source-x", "to": "origin-x", "relation": "reviewer_assigned_origin"},
            ],
            "duplicate_clusters": [],
        }
        report = audit_evidence_quality(*inputs(graph=graph))
        self.assertEqual(report["summary"]["reviewer_assigned_origin_count"], 1)
        self.assertEqual(report["summary"]["source_documents_with_reviewer_origin_annotation"], 1)
        self.assertEqual(report["summary"]["claims_remaining_unverified"], 1)

    def test_duplicate_wording_across_documents_is_not_independent_corroboration(self):
        graph = {
            "schema_version": "1.0",
            "input_claim_count": 1,
            "summary": {"independently_verified_claims": 0, "unreviewed_claims": 1},
            "nodes": [],
            "edges": [],
            "duplicate_clusters": [{
                "distinct_source_document_count": 2,
                "independent_corroboration": False,
            }],
        }
        report = audit_evidence_quality(*inputs(graph=graph))
        duplicate = report["summary"]["duplicate_statement_clusters"]
        self.assertEqual(duplicate["multi_document_cluster_count"], 1)
        self.assertFalse(duplicate["independent_corroboration_claimed"])
        self.assertIn("not proof of independent corroboration", report["policy"])

    def test_rejects_claim_promoted_to_verified(self):
        row = claim(review_status="verified")
        with self.assertRaisesRegex(ValueError, "remain unverified"):
            audit_evidence_quality(*inputs([row]))

    def test_rejects_missing_candidate_and_duplicate_ids(self):
        row = claim(candidate_id="missing")
        with self.assertRaisesRegex(ValueError, "no discovery candidate"):
            audit_evidence_quality(*inputs([row]))
        with self.assertRaisesRegex(ValueError, "duplicate discovery candidate_id"):
            audit_evidence_quality(*inputs(candidates=[candidate(), candidate()]))

    def test_rejects_automated_verification_and_cross_stage_count_mismatch(self):
        discovery, claims, graph = inputs()
        graph["summary"]["independently_verified_claims"] = 1
        with self.assertRaisesRegex(ValueError, "automated factual verification"):
            audit_evidence_quality(discovery, claims, graph)
        graph["summary"]["independently_verified_claims"] = 0
        claims["claim_count"] = 2
        with self.assertRaisesRegex(ValueError, "claim count mismatch"):
            audit_evidence_quality(discovery, claims, graph)

    def test_markdown_states_interpretation_limits(self):
        report = audit_evidence_quality(*inputs())
        rendered = markdown_report(report).lower()
        self.assertIn("not a composite quality score", rendered)
        self.assertIn("all claims remain unverified", rendered)


if __name__ == "__main__":
    unittest.main()
