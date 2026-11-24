import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_intelligence_decision_analytics import build

def fixtures():
 review={"schema_version":"1.0","generated_at":"2026-11-24T02:00:00Z","observation_state":"cache_persisted","state_is_approval":False,
 "summary":{"tracked_current_claims":3,"tracked_backlog_claims":3,"review_states":{"pending":1,"needs_more_evidence":1,"rejected":0,"accepted_for_evidence_attachment":1}},
 "claim_aging":[
 {"claim_id":"claim-a","first_seen_at":"2026-11-20T00:00:00Z","days_since_first_seen":4,"review_state":"accepted_for_evidence_attachment"},
 {"claim_id":"claim-b","first_seen_at":"2026-11-21T00:00:00Z","days_since_first_seen":3,"review_state":"needs_more_evidence"},
 {"claim_id":"claim-c","first_seen_at":"2026-11-24T00:00:00Z","days_since_first_seen":0,"review_state":"pending"}]}
 ledger={"schema_version":"1.0","decisions":[
 {"claim_id":"claim-a","decision":"accepted_for_evidence_attachment","reviewer":"reviewer-a","decided_at":"2026-11-22T00:00:00Z","notes":"Original source and product configuration inspected for evidence attachment."},
 {"claim_id":"claim-b","decision":"needs_more_evidence","reviewer":"reviewer-b","decided_at":"2026-11-23T00:00:00Z","notes":"Measurement conditions and test configuration remain unclear in source."}]}
 reasons={"schema_version":"1.0","records":[
 {"claim_id":"claim-a","primary_reason":"missing_configuration_or_version","secondary_reasons":["independent_corroboration_needed"],"coded_by":"reviewer-a","coded_at":"2026-11-23T00:00:00Z","rationale":"Product configuration is still not explicit enough for a comparable database entry."}]}
 return review,ledger,reasons

class DecisionAnalyticsTests(unittest.TestCase):
 def test_explicit_reasons_and_latency(self):
  out=build(*fixtures());m=out["metrics"]
  self.assertEqual(m["decisions_recorded"],2);self.assertEqual(m["reason_coded_decisions"],1)
  self.assertEqual(m["reason_code_coverage"],.5)
  self.assertEqual(m["primary_reason_counts"],{"missing_configuration_or_version":1})
  self.assertEqual(m["review_latency_days"]["overall"]["median_days"],2.0)
  self.assertFalse(out["factual_verification_performed"])
 def test_free_text_is_not_automatically_classified(self):
  r,l,c=fixtures();c["records"]=[]
  out=build(r,l,c)
  self.assertEqual(out["metrics"]["reason_coded_decisions"],0)
  self.assertEqual(out["metrics"]["primary_reason_counts"],{})
  self.assertEqual(len(out["metrics"]["uncoded_decision_claim_ids"]),2)
 def test_rejects_reason_for_unknown_decision(self):
  r,l,c=fixtures();c["records"][0]["claim_id"]="claim-c"
  with self.assertRaisesRegex(ValueError,"uniquely reference"):build(r,l,c)
 def test_rejects_duplicate_reason_code(self):
  r,l,c=fixtures();c["records"].append(dict(c["records"][0]))
  with self.assertRaisesRegex(ValueError,"uniquely reference"):build(r,l,c)
 def test_rejects_unsupported_taxonomy(self):
  r,l,c=fixtures();c["records"][0]["primary_reason"]="automatically_true"
  with self.assertRaisesRegex(ValueError,"primary reason"):build(r,l,c)
 def test_rejects_reason_timestamp_before_decision(self):
  r,l,c=fixtures();c["records"][0]["coded_at"]="2026-11-21T00:00:00Z"
  with self.assertRaisesRegex(ValueError,"must follow decision"):build(r,l,c)
 def test_rejects_future_decision(self):
  r,l,c=fixtures();l["decisions"][0]["decided_at"]="2026-11-25T00:00:00Z"
  with self.assertRaisesRegex(ValueError,"later than analytics"):build(r,l,c)
 def test_rejects_claim_aging_count_mismatch(self):
  r,l,c=fixtures();r["claim_aging"].pop()
  with self.assertRaisesRegex(ValueError,"do not match persistent backlog"):build(r,l,c)
 def test_age_buckets_count_only_unresolved(self):
  r,l,c=fixtures();r["claim_aging"][1]["days_since_first_seen"]=15
  out=build(r,l,c)
  self.assertEqual(out["metrics"]["overdue_14d_or_more"],1)
if __name__=="__main__":unittest.main()
