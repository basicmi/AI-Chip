"""Coverage audit operates on real Discovery metadata shapes with offline fixtures."""
import copy
import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_intelligence_source_coverage import coverage_report,markdown_report

def fixtures():
    registry={"schema_version":"1.0","sources":[
        {"id":"releases","kind":"github_releases","active":True},
        {"id":"rss","kind":"rss_atom","active":True},
        {"id":"arxiv","kind":"arxiv_api","active":True,"max_results":2},
        {"id":"off","kind":"rss_atom","active":False},
    ]}
    rows=[
        {"source_id":"releases","status":"observed","recent_item_count":2,"consecutive_failures":0},
        {"source_id":"rss","status":"observed","recent_item_count":1,"consecutive_failures":0},
        {"source_id":"arxiv","status":"observed","recent_item_count":2,"consecutive_failures":0},
    ]
    observations=[
        {"source_id":"releases","candidate_id":"r1","published_at":"2026-11-12T10:00:00Z","url":"https://example.org/releases/r1"},
        {"source_id":"releases","candidate_id":"r2","published_at":"2026-11-11T10:00:00Z","url":"https://example.org/duplicate#fragment"},
        {"source_id":"rss","candidate_id":"s1","published_at":"2026-11-12T10:00:00Z","url":"https://example.org/duplicate"},
        {"source_id":"arxiv","candidate_id":"a1","published_at":"2026-11-12T10:00:00Z","url":"https://arxiv.org/abs/2611.11111"},
        {"source_id":"arxiv","candidate_id":"a2","published_at":"2026-11-13T10:00:00Z","url":"https://arxiv.org/abs/2611.22222"},
    ]
    report={"schema_version":"1.1","generated_at":"2026-11-14T10:00:00Z",
      "read_only":True,"source_count":3,"sources_observed":3,"sources_unavailable":0,
      "candidate_count":len(observations),"source_results":rows,"all_observations":observations}
    return registry,report

class SourceCoverageTests(unittest.TestCase):
    def test_counts_coverage_duplicate_risk_and_arxiv_limit(self):
        reg,disc=fixtures()
        result=coverage_report(reg,disc)
        summary=result["summary"]
        self.assertEqual(summary["configured_active_sources"],3)
        self.assertEqual(summary["observed_sources"],3)
        self.assertEqual(summary["cross_source_shared_url_groups"],1)
        self.assertEqual(summary["potentially_truncated_sources"],1)
        arxiv=next(x for x in result["sources"] if x["source_id"]=="arxiv")
        self.assertEqual(arxiv["per_request_item_limit"],2)
        self.assertTrue(arxiv["possible_window_truncation"])
        self.assertFalse(result["factual_verification_performed"])
        self.assertFalse(result["verified_remote_endpoints"])
    def test_empty_success_is_not_outage(self):
        reg,disc=fixtures()
        disc["all_observations"]=[x for x in disc["all_observations"] if x["source_id"]!="rss"]
        disc["candidate_count"]=4
        disc["source_results"][1]["recent_item_count"]=0
        result=coverage_report(reg,disc)
        self.assertEqual(result["summary"]["empty_success_sources"],1)
        rss=next(x for x in result["sources"] if x["source_id"]=="rss")
        self.assertEqual(rss["risk_flags"],["no_recent_items_not_a_failure"])
    def test_unavailable_source_is_distinct_from_stale_publication(self):
        reg,disc=fixtures()
        disc["source_results"][1].update(
            status="unavailable",recent_item_count=0,
            failure_category="http_client_error",failure_tier="critical",consecutive_failures=3)
        disc["all_observations"]=[x for x in disc["all_observations"] if x["source_id"]!="rss"]
        disc["candidate_count"]=4
        disc["sources_observed"]=2
        disc["sources_unavailable"]=1
        result=coverage_report(reg,disc)
        rss=next(x for x in result["sources"] if x["source_id"]=="rss")
        self.assertIn("source_unavailable",rss["risk_flags"])
        self.assertIn("repeated_source_failure",rss["risk_flags"])
    def test_publication_age_not_scan_age(self):
        reg,disc=fixtures()
        disc["all_observations"][0]["published_at"]="2026-01-01T00:00:00Z"
        disc["all_observations"][1]["published_at"]="2026-01-02T00:00:00Z"
        result=coverage_report(reg,disc)
        row=next(x for x in result["sources"] if x["source_id"]=="releases")
        self.assertGreater(row["latest_observed_publication_age_days"],30)
        self.assertIn("latest_observed_publication_over_30d",row["risk_flags"])
    def test_invalid_publication_date_is_explicitly_flagged(self):
        reg,disc=fixtures()
        disc["all_observations"][0]["published_at"]=None
        result=coverage_report(reg,disc)
        row=next(x for x in result["sources"] if x["source_id"]=="releases")
        self.assertEqual(row["invalid_publication_date_count"],1)
        self.assertIn("missing_or_invalid_publication_date",row["risk_flags"])
    def test_source_count_mismatch_fails_closed(self):
        reg,disc=fixtures()
        disc["source_results"].pop()
        with self.assertRaisesRegex(ValueError,"membership"):
            coverage_report(reg,disc)
    def test_observation_from_failed_source_rejected(self):
        reg,disc=fixtures()
        disc["source_results"][0]["status"]="unavailable"
        disc["sources_observed"]=2
        disc["sources_unavailable"]=1
        with self.assertRaisesRegex(ValueError,"unavailable source"):
            coverage_report(reg,disc)
    def test_record_count_mismatch_fails_closed(self):
        reg,disc=fixtures()
        disc["source_results"][0]["recent_item_count"]=3
        with self.assertRaisesRegex(ValueError,"recent item count"):
            coverage_report(reg,disc)
    def test_external_model_candidates_not_misclassified(self):
        reg,disc=fixtures()
        disc["all_observations"].append({"candidate_id":"hf-model:test","source_id":"huggingface-model-catalog"})
        disc["candidate_count"]+=1
        result=coverage_report(reg,disc)
        self.assertEqual(result["summary"]["configured_active_sources"],3)
    def test_historical_report_risks_not_claim_verification(self):
        reg,disc=fixtures()
        report=markdown_report(coverage_report(reg,disc))
        self.assertIn("not independent corroboration",report)
        self.assertIn("possible",report.lower())
    def test_registry_active_ids_are_required_unique(self):
        reg,disc=fixtures()
        reg["sources"][2]["id"]="rss"
        with self.assertRaisesRegex(ValueError,"unique"):
            coverage_report(reg,disc)

if __name__=="__main__":
    unittest.main()
