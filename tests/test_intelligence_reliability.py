"""Offline end-to-end reliability replay for the intelligence stages."""
import copy
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_intelligence_discovery import run_discovery
from extract_intelligence_claims import extract_report
from build_intelligence_evidence_graph import graph_for_claims
from triage_intelligence_claims import build_queue
from track_intelligence_review_state import update_state
from audit_intelligence_run import audit_pipeline, markdown_report

NOW = datetime(2026, 11, 14, 10, tzinfo=timezone.utc)
REGISTRY = {"sources": [
    {"id":"a","name":"Software release","active":True,"kind":"github_releases","repo":"test/project","category":"runtime"},
    {"id":"b","name":"Vendor announcement","active":True,"kind":"rss_atom","publisher":"Test Vendor",
     "category":"vendor-announcement","feed_url":"https://example.org/feed"}
]}
RELEASE = [{"tag_name":"v1.0","name":"GPU runtime release v1.0",
    "published_at":"2026-11-13T00:00:00Z",
    "updated_at":"2026-11-13T00:00:00Z",
    "html_url":"https://github.com/test/project/releases/tag/v1.0",
    "body":"New kernel supports FP8 inference and 180 GB memory per GPU.",
    "prerelease":False,"draft":False}]
RSS = """<rss><channel><item><title>Test accelerator memory</title>
<link>https://example.org/test-accelerator</link>
<pubDate>Fri, 13 Nov 2026 00:00:00 GMT</pubDate>
<description>GPU platform has 192 GB memory per GPU.</description>
</item></channel></rss>"""
MODEL_REPORT = {"models":[],"model_count":0,"observed":0,
                "new_publisher_candidates":[],"publisher_discovery_errors":[]}

def replay(now, discovery_state=None, review_cache=None, failure=None):
    discovery_state=copy.deepcopy(discovery_state or {"schema_version":"1.0","items":{}})
    def releases(_):
        if failure in {"all","release"}: raise TimeoutError("synthetic release outage")
        return RELEASE
    def feed(_):
        if failure in {"all","feed"}: raise TimeoutError("synthetic feed outage")
        return RSS
    discovered=run_discovery(REGISTRY,{"models":[]},now=now,
        release_fetcher=releases,feed_fetcher=feed,
        model_report=MODEL_REPORT,state=discovery_state)
    claim_report=extract_report(discovered,generated_at=now.isoformat().replace("+00:00","Z"))
    graph=graph_for_claims(claim_report,generated_at=now.isoformat().replace("+00:00","Z"))
    triage=build_queue(discovered,claim_report,graph,now=now)
    review,new_review=update_state(triage,claim_report,review_cache,now=now)
    audit=audit_pipeline(discovered,claim_report,graph,triage,review,
        generated_at=now.isoformat().replace("+00:00","Z"))
    return discovered,claim_report,graph,triage,review,audit,discovery_state,new_review

class IntelligenceReliabilityTests(unittest.TestCase):
    def test_all_stages_agree_and_no_factual_verification(self):
        d,c,g,t,s,a,dc,rc=replay(NOW)
        self.assertEqual(a["health"],"healthy")
        self.assertTrue(a["cache_commit_allowed"])
        self.assertGreater(c["claim_count"],0)
        self.assertEqual(a["summary"]["extracted_claims"],c["claim_count"])
        self.assertFalse(a["factual_verification_performed"])
        self.assertFalse(a["production_writes"])
        self.assertIn("Cache checkpoint allowed",markdown_report(a))
    def test_partial_outage_is_reported_and_queue_still_works(self):
        d,c,g,t,s,a,dc,rc=replay(NOW,failure="release")
        self.assertEqual(a["health"],"degraded")
        self.assertEqual(a["summary"]["sources_unavailable"],1)
        self.assertTrue(a["cache_commit_allowed"])
        self.assertGreater(c["claim_count"],0)
    def test_total_source_outage_blocks_checkpoint(self):
        d,c,g,t,s,a,dc,rc=replay(NOW,failure="all")
        self.assertEqual(a["health"],"failed")
        self.assertFalse(a["cache_commit_allowed"])
        self.assertIn("all active discovery sources",a["errors"][0])
    def test_second_week_unchanged_leads_keep_backlog(self):
        d,c,g,t,s,a,dc,rc=replay(NOW)
        second=replay(NOW+timedelta(days=8),dc,rc)
        d2,c2,g2,t2,s2,a2,dc2,rc2=second
        self.assertEqual(d2["change_counts"]["new"],0)
        self.assertEqual(c2["claim_count"],0)
        self.assertEqual(a2["health"],"healthy")
        self.assertEqual(s2["summary"]["tracked_current_claims"],0)
        self.assertEqual(s2["summary"]["tracked_backlog_claims"],c["claim_count"])
        self.assertEqual(s2["summary"]["backlog_not_observed_this_run"],c["claim_count"])
        self.assertEqual(s2["summary"]["aging_alerts"]["overdue_7d"],c["claim_count"])
    def test_corrupted_stage_membership_fails_closed(self):
        d,c,g,t,s,a,*_=replay(NOW)
        g["nodes"]=[row for row in g["nodes"] if row.get("type")!="claim_candidate"]
        self.assertEqual(audit_pipeline(d,c,g,t,s)["health"],"failed")
    def test_claim_status_escalation_is_rejected(self):
        d,c,g,t,s,a,*_=replay(NOW)
        c["claims"][0]["review_status"]="independently_verified"
        self.assertEqual(audit_pipeline(d,c,g,t,s)["health"],"failed")
    def test_review_state_missing_backlog_fails_closed(self):
        d,c,g,t,s,a,*_=replay(NOW)
        s["aging_backlog"].clear()
        self.assertEqual(audit_pipeline(d,c,g,t,s)["health"],"failed")
    def test_candidate_count_mismatch_fails_closed(self):
        d,c,g,t,s,a,*_=replay(NOW)
        d["source_count"]+=1
        self.assertEqual(audit_pipeline(d,c,g,t,s)["health"],"failed")

if __name__=="__main__": unittest.main()
