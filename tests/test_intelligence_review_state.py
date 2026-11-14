import json,sys,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from track_intelligence_review_state import update_state,markdown
from test_intelligence_triage import fixtures

NOW=datetime(2026,11,14,12,tzinfo=timezone.utc)

def previous_at(when,claim_ids=("a","b","c")):
    return {"schema_version":"1.0","items":{cid:{"first_seen_at":when,"last_seen_at":when} for cid in claim_ids}}
def decision(cid,when,status="needs_more_evidence"):
    return {"claim_id":cid,"decision":status,"reviewer":"actual-maintainer",
            "decided_at":when,"notes":"The original source was checked but more technical evidence is required."}

class ReviewStateTests(unittest.TestCase):
    def test_first_run_creates_pending_without_approvals(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW)
        result,state=update_state(triage,c,now=NOW)
        self.assertEqual(result["summary"]["review_states"]["pending"],3)
        self.assertEqual(result["summary"]["aging_alerts"]["overdue_7d"],0)
        self.assertFalse(result["state_is_approval"])
        self.assertEqual(len(state["items"]),3)
    def test_persistence_counts_14_and_30_day_overdue(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW)
        state=previous_at("2026-10-01T12:00:00Z")
        result,new=update_state(triage,c,state,now=NOW)
        self.assertEqual(result["summary"]["aging_alerts"]["overdue_30d"],3)
        self.assertEqual(result["claim_aging"][0]["days_since_first_seen"],44)
        later,_=update_state(triage,c,new,now=NOW+timedelta(days=3))
        self.assertEqual(later["claim_aging"][0]["days_since_first_seen"],47)
        self.assertIn("Overdue 7/14/30",markdown(result))
    def test_human_decisions_do_not_claim_factual_verification(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW)
        ledger={"schema_version":"1.0","decisions":[
            decision("a","2026-11-12T00:00:00Z","rejected"),
            decision("b","2026-11-12T00:00:00Z","accepted_for_evidence_attachment"),
            decision("c","2026-11-12T00:00:00Z")]}
        result,_=update_state(triage,c,previous_at("2026-10-01T12:00:00Z"),ledger,now=NOW)
        self.assertEqual(result["summary"]["review_states"]["pending"],0)
        self.assertEqual(result["summary"]["review_states"]["needs_more_evidence"],1)
        self.assertEqual(result["summary"]["aging_alerts"]["follow_up_needed"],1)
        self.assertTrue(all(not x["review_is_factual_verification"] for x in result["claim_aging"]))
        self.assertEqual(result["summary"]["review_states"]["accepted_for_evidence_attachment"],1)
    def test_does_not_promote_local_draft_ledger(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW)
        ledger={"schema_version":"1.0","status":"local_draft_only","decisions":[]}
        with self.assertRaisesRegex(ValueError,"human review decision"):
            update_state(triage,c,ledger=ledger,now=NOW)
    def test_rejects_future_timestamp_and_unknown_claim(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW)
        ledger={"schema_version":"1.0","decisions":[decision("missing","2026-11-12T00:00:00Z")]}
        with self.assertRaisesRegex(ValueError,"unknown"):
            update_state(triage,c,ledger=ledger,now=NOW)
        ledger["decisions"][0]["claim_id"]="a"
        ledger["decisions"][0]["decided_at"]="2026-12-12T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"future"):
            update_state(triage,c,ledger=ledger,now=NOW)
    def test_bad_state_fails_closed(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW)
        with self.assertRaisesRegex(ValueError,"inconsistent"):
            update_state(triage,c,previous_at("2027-01-01T00:00:00Z"),now=NOW)
    def test_source_absence_does_not_equal_review(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW)
        state=previous_at("2026-10-01T12:00:00Z",("a","b","c","old"))
        result,new=update_state(triage,c,state,now=NOW)
        self.assertEqual(result["summary"]["tracked_current_claims"],3)
        self.assertIn("old",new["items"])
    def test_truncated_top_n_still_tracks_all_claims(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW,top=1)
        result,state=update_state(triage,c,now=NOW)
        self.assertEqual(result["summary"]["tracked_current_claims"],3)
        self.assertEqual(len(state["items"]),3)
    def test_backlog_survives_change_only_discovery_gap(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW)
        _,state=update_state(triage,c,now=NOW)
        later=NOW+timedelta(days=16)
        empty_triage={"schema_version":"1.0","queue":[],"summary":{"input_claims":0,"automatically_verified":0}}
        empty_claims={"schema_version":"1.0","claims":[]}
        result,new=update_state(empty_triage,empty_claims,state,now=later)
        self.assertEqual(result["summary"]["tracked_current_claims"],0)
        self.assertEqual(result["summary"]["tracked_backlog_claims"],3)
        self.assertEqual(result["summary"]["backlog_not_observed_this_run"],3)
        self.assertEqual(result["summary"]["aging_alerts"]["overdue_14d"],3)
        self.assertEqual(len(result["aging_backlog"]),3)
        self.assertFalse(result["aging_backlog"][0]["observed_this_run"])
        self.assertEqual(new["items"]["a"]["last_seen_at"],"2026-11-14T12:00:00Z")
        ledger={"schema_version":"1.0","decisions":[decision("a","2026-11-17T00:00:00Z","rejected")]}
        result,_=update_state(empty_triage,empty_claims,new,ledger,now=later)
        self.assertEqual(result["summary"]["review_states"]["rejected"],1)
        self.assertEqual(result["summary"]["review_states"]["pending"],2)
    def test_claim_promotion_disallowed(self):
        d,c,g=fixtures()
        triage=__import__("triage_intelligence_claims").build_queue(d,c,g,now=NOW)
        c["claims"][0]["review_status"]="verified"
        with self.assertRaisesRegex(ValueError,"unverified"):
            update_state(triage,c,now=NOW)
if __name__=="__main__": unittest.main()
