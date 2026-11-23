import copy
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_intelligence_evidence_quality_snapshot import snapshot,markdown_report


def fixtures():
    quality={"schema_version":"1.0","summary":{
        "claim_count":4,"claims_remaining_unverified":4,
        "quote_grounded_claims":3,"provenance_complete_claims":2,
        "claims_with_source_metadata_mismatch":1,
        "distinct_source_documents":3,"distinct_publishers":2}}
    state={"schema_version":"1.0","generated_at":"2026-11-23T00:00:00Z",
        "observation_state":"cache_persisted","state_is_approval":False,
        "summary":{"tracked_current_claims":4,"tracked_backlog_claims":12,
        "claim_payloads_available":10,"claim_payloads_missing":2,
        "review_states":{"pending":6,"needs_more_evidence":3,
        "rejected":2,"accepted_for_evidence_attachment":1}}}
    lineage={"schema_version":"1.0","review_type":"source_lineage",
        "status":"human_review_required",
        "summary":{"multi_document_duplicate_clusters":3,"selected_clusters":1},
        "clusters":[{"cluster_id":"one"}],
        "policy":{"independent_corroboration_automatically_verified":False}}
    blank={"reviewer":"","label":"","rationale":"","source_checked":False}
    semantic={"schema_version":"1.0","review_type":"human_semantic_support",
        "generated_at":"2026-11-23T00:00:00Z",
        "policy":{"cannot_promote_to_verified":True},
        "items":[{"claim_id":"claim-a","reviewers":[dict(blank),dict(blank)]}]}
    return quality,state,lineage,semantic


class DashboardSnapshotTests(unittest.TestCase):
    def test_measures_hygiene_without_fabricating_review(self):
        report=snapshot(*fixtures())
        m=report["metrics"]
        self.assertEqual(m["quote_traceability"]["rate"],.75)
        self.assertEqual(m["provenance_completeness"]["rate"],.5)
        self.assertEqual(m["payload_coverage"]["rate"],round(10/12,4))
        self.assertEqual(m["unresolved_claims"],9)
        self.assertEqual(m["lineage_clusters_queued"],1)
        self.assertIsNone(m["semantic_reviewer_agreement"])
        self.assertIsNone(m["independently_verified_claims"])
        self.assertFalse(report["factual_verification_performed"])
        self.assertIn("not measured",markdown_report(report))

    def test_rejects_cross_stage_current_claim_count_mismatch(self):
        reports=list(fixtures())
        reports[1]["summary"]["tracked_current_claims"]=5
        with self.assertRaisesRegex(ValueError,"Claim totals disagree"):
            snapshot(*reports)

    def test_rejects_forged_automated_verification(self):
        reports=list(fixtures())
        reports[0]["summary"]["claims_remaining_unverified"]=3
        with self.assertRaisesRegex(ValueError,"incorrectly claims verified"):
            snapshot(*reports)

    def test_rejects_forged_lineage_verification(self):
        reports=list(fixtures())
        reports[2]["policy"]["independent_corroboration_automatically_verified"]=True
        with self.assertRaisesRegex(ValueError,"lineage"):
            snapshot(*reports)

    def test_rejects_cross_run_semantic_template(self):
        reports=list(fixtures())
        reports[3]["generated_at"]="2026-11-22T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"different review-state run"):
            snapshot(*reports)

    def test_rejects_filled_semantic_templates_as_completed_reviews(self):
        reports=list(fixtures())
        reports[3]["items"][0]["reviewers"][0]["label"]="supported_by_source"
        with self.assertRaisesRegex(ValueError,"fabricated human"):
            snapshot(*reports)

    def test_rejects_backlog_state_count_mismatch(self):
        reports=list(fixtures())
        reports[1]["summary"]["tracked_backlog_claims"]=13
        with self.assertRaisesRegex(ValueError,"do not match backlog"):
            snapshot(*reports)

    def test_rejects_payload_coverage_mismatch(self):
        reports=list(fixtures())
        reports[1]["summary"]["claim_payloads_missing"]=3
        with self.assertRaisesRegex(ValueError,"payload coverage"):
            snapshot(*reports)

    def test_rejects_oversubscribed_lineage_queue(self):
        reports=list(fixtures())
        reports[2]["summary"]["selected_clusters"]=4
        with self.assertRaisesRegex(ValueError,"lineage selected count"):
            snapshot(*reports)

    def test_empty_claims_rates_are_unavailable_not_success(self):
        reports=list(fixtures())
        reports[0]["summary"].update(claim_count=0,claims_remaining_unverified=0,
            quote_grounded_claims=0,provenance_complete_claims=0,
            claims_with_source_metadata_mismatch=0,distinct_source_documents=0,distinct_publishers=0)
        reports[1]["summary"]["tracked_current_claims"]=0
        result=snapshot(*reports)
        self.assertIsNone(result["metrics"]["quote_traceability"]["rate"])

    def test_does_not_mutate_inputs(self):
        reports=fixtures()
        original=copy.deepcopy(reports)
        snapshot(*reports)
        self.assertEqual(reports,original)


if __name__=="__main__":
    unittest.main()
