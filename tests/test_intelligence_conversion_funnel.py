import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_intelligence_conversion_funnel import build

def fixtures():
 review={"schema_version":"1.0","generated_at":"2026-11-24T00:00:00Z","observation_state":"cache_persisted","state_is_approval":False,
 "summary":{"tracked_current_claims":4,"tracked_backlog_claims":4,"review_states":{"pending":1,"needs_more_evidence":1,"rejected":1,"accepted_for_evidence_attachment":1}}}
 ledger={"schema_version":"1.0","decisions":[
 {"claim_id":"claim-a","decision":"accepted_for_evidence_attachment","reviewer":"r1","decided_at":"2026-11-23T00:00:00Z","notes":"Original source inspected; evidence attachment accepted for further curation."},
 {"claim_id":"claim-b","decision":"needs_more_evidence","reviewer":"r1","decided_at":"2026-11-23T00:00:00Z","notes":"Configuration and measurement conditions are not yet sufficiently documented."},
 {"claim_id":"claim-c","decision":"rejected","reviewer":"r2","decided_at":"2026-11-23T00:00:00Z","notes":"The linked source does not support the extracted technical statement."}]}
 manifest={"schema_version":"1.0","records":[{"claim_id":"claim-a","target_dataset":"chip_products","pull_request":136,"merged_commit":"a"*40,"integrated_at":"2026-11-24T00:00:00Z","reviewer":"r1","notes":"Merged reviewed product record with source provenance and configuration context."}]}
 return review,ledger,manifest

class FunnelTests(unittest.TestCase):
 def test_counts_only_explicit_merged_pr_manifest(self):
  out=build(*fixtures());m=out["metrics"]
  self.assertEqual(m["decisions_recorded"],3);self.assertEqual(m["database_integrated_claims"],1)
  self.assertEqual(m["accepted_to_integrated_rate"],1.0);self.assertFalse(out["factual_verification_performed"])
 def test_empty_manifest_means_zero_integrated_not_accepted(self):
  r,l,_=fixtures();out=build(r,l,{"schema_version":"1.0","records":[]})
  self.assertEqual(out["metrics"]["database_integrated_claims"],0)
  self.assertEqual(out["availability"]["database_integration"],"no_integration_records")
 def test_rejects_integration_without_acceptance(self):
  r,l,m=fixtures();m["records"][0]["claim_id"]="claim-b"
  with self.assertRaisesRegex(ValueError,"only explicitly accepted"):build(r,l,m)
 def test_rejects_bad_commit_sha(self):
  r,l,m=fixtures();m["records"][0]["merged_commit"]="deadbeef"
  with self.assertRaisesRegex(ValueError,"full Git SHA"):build(r,l,m)
 def test_rejects_state_count_mismatch(self):
  r,l,m=fixtures();r["summary"]["review_states"]["pending"]=2
  with self.assertRaisesRegex(ValueError,"do not reconcile"):build(r,l,m)
 def test_rejects_duplicate_decisions(self):
  r,l,m=fixtures();l["decisions"].append(dict(l["decisions"][0]))
  with self.assertRaisesRegex(ValueError,"duplicate"):build(r,l,m)
 def test_rejects_timezone_naive_integration(self):
  r,l,m=fixtures();m["records"][0]["integrated_at"]="2026-11-24T00:00:00"
  with self.assertRaisesRegex(ValueError,"timezone"):build(r,l,m)
if __name__=="__main__":unittest.main()
