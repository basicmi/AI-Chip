import copy
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_intelligence_operational_snapshot import snapshot

DISCOVERY={"schema_version":"1.1","read_only":True,"generated_at":"2026-11-14T10:00:00Z",
  "candidate_count":5,"change_counts":{"new":3,"updated":1},
  "source_results":[
    {"source_id":"github","source_name":"GitHub releases","kind":"github_releases","status":"observed","recent_item_count":3},
    {"source_id":"feed","source_name":"Example RSS","kind":"rss_atom","status":"unavailable","recent_item_count":0}]}
HEALTH={"schema_version":"1.0","generated_at":"2026-11-14T10:05:00Z",
 "health":"degraded","cache_commit_allowed":True,"production_writes":False,
 "factual_verification_performed":False,"warnings":["1 source unavailable"],
 "summary":{"source_count":2,"sources_observed":1,"sources_unavailable":1,
 "review_candidates":4,"extracted_claims":6,"persistent_backlog":12,
 "unresolved_backlog":9,"oldest_unresolved_days":28}}
REVIEW={"schema_version":"1.0","generated_at":"2026-11-14T10:03:00Z",
 "state_is_approval":False,
 "summary":{"tracked_backlog_claims":12,
 "review_states":{"pending":7,"needs_more_evidence":2,"rejected":2,"accepted_for_evidence_attachment":1}}}

class OperationalSnapshotTests(unittest.TestCase):
 def test_degraded_run_preserves_per_source_diagnostics(self):
  result=snapshot(DISCOVERY,HEALTH,REVIEW,discovery_cache_present=True,review_cache_present=False)
  self.assertEqual(result["health"],"degraded")
  self.assertEqual(result["summary"]["availability_percent"],50.0)
  self.assertEqual(result["summary"]["unresolved_backlog"],9)
  self.assertEqual(result["cache"]["discovery_restored_file_present"],True)
  self.assertEqual(result["cache"]["review_restored_file_present"],False)
  self.assertTrue(result["operational_only"])
  self.assertEqual(result["sources"][0]["source_id"],"feed")
 def test_no_cache_info_is_unknown_not_false(self):
  report=snapshot(DISCOVERY,HEALTH,REVIEW)
  self.assertIsNone(report["cache"]["discovery_restored_file_present"])
  self.assertIsNone(report["cache"]["review_restored_file_present"])
 def test_mismatched_runs_rejected(self):
  review=copy.deepcopy(REVIEW)
  review["generated_at"]="2026-10-01T10:00:00Z"
  with self.assertRaisesRegex(ValueError,"different runs"):
   snapshot(DISCOVERY,HEALTH,review)
 def test_failed_audit_disallowed(self):
  health=copy.deepcopy(HEALTH)
  health["cache_commit_allowed"]=False
  with self.assertRaisesRegex(ValueError,"failed audit"):
   snapshot(DISCOVERY,health,REVIEW)
 def test_health_count_mismatch_rejected(self):
  health=copy.deepcopy(HEALTH)
  health["summary"]["source_count"]=200
  with self.assertRaisesRegex(ValueError,"source availability"):
   snapshot(DISCOVERY,health,REVIEW)
 def test_backlog_count_mismatch_rejected(self):
  state=copy.deepcopy(REVIEW)
  state["summary"]["tracked_backlog_claims"]=13
  with self.assertRaisesRegex(ValueError,"backlog mismatch"):
   snapshot(DISCOVERY,HEALTH,state)
 def test_duplicate_source_rejected(self):
  discovery=copy.deepcopy(DISCOVERY)
  discovery["source_results"].append(copy.deepcopy(discovery["source_results"][0]))
  with self.assertRaisesRegex(ValueError,"duplicate"):
   snapshot(discovery,HEALTH,REVIEW)
 def test_status_escalation_rejected(self):
  report=copy.deepcopy(HEALTH)
  report["factual_verification_performed"]=True
  with self.assertRaisesRegex(ValueError,"verification"):
   snapshot(DISCOVERY,report,REVIEW)
 def test_invalid_cache_value_rejected(self):
  with self.assertRaisesRegex(ValueError,"cache presence"):
   snapshot(DISCOVERY,HEALTH,REVIEW,discovery_cache_present="yes")

if __name__=="__main__": unittest.main()
