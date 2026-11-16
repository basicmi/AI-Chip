import copy
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_intelligence_operational_snapshot import snapshot

METRICS_A={
 "request_count":2,"failed_request_count":1,"response_bytes":1200,
 "total_elapsed_ms":6000.0,"average_request_ms":3000.0,"max_request_ms":5000.0,
 "last_http_error_status":503,"last_request_failure_category":"http_server_error",
}
METRICS_B={
 "request_count":1,"failed_request_count":0,"response_bytes":300,
 "total_elapsed_ms":1000.0,"average_request_ms":1000.0,"max_request_ms":1000.0,
 "last_http_error_status":None,"last_request_failure_category":None,
}
DISCOVERY={"schema_version":"1.1","read_only":True,"generated_at":"2026-11-14T10:00:00Z",
  "candidate_count":5,"change_counts":{"new":3,"updated":1},
  "source_results":[
    {"source_id":"github","source_name":"GitHub releases","kind":"github_releases",
     "status":"observed","recent_item_count":3,"request_diagnostics":METRICS_A},
    {"source_id":"feed","source_name":"Example RSS","kind":"rss_atom",
     "status":"unavailable","recent_item_count":0,"request_diagnostics":METRICS_B}]}
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
  self.assertEqual(result["schema_version"],"1.1")

 def test_no_cache_info_is_unknown_not_false(self):
  report=snapshot(DISCOVERY,HEALTH,REVIEW)
  self.assertIsNone(report["cache"]["discovery_restored_file_present"])
  self.assertIsNone(report["cache"]["review_restored_file_present"])


 def test_request_telemetry_is_aggregated_and_retained_per_source(self):
  result=snapshot(DISCOVERY,HEALTH,REVIEW)
  summary=result["summary"]
  self.assertEqual(summary["request_telemetry_sources"],2)
  self.assertEqual(summary["total_requests"],3)
  self.assertEqual(summary["failed_requests"],1)
  self.assertEqual(summary["response_bytes"],1500)
  self.assertEqual(summary["sources_with_slow_request_over_5s"],1)
  self.assertEqual(result["sources"][1]["request_diagnostics"],METRICS_A)
  self.assertEqual(result["sources"][0]["request_diagnostics"],METRICS_B)

 def test_legacy_discovery_without_request_metrics_remains_supported(self):
  discovery=copy.deepcopy(DISCOVERY)
  for row in discovery["source_results"]:
   row.pop("request_diagnostics")
  result=snapshot(discovery,HEALTH,REVIEW)
  self.assertEqual(result["summary"]["request_telemetry_sources"],0)
  self.assertEqual(result["summary"]["total_requests"],0)
  self.assertEqual(result["summary"]["failed_requests"],0)
  self.assertIsNone(result["sources"][0]["request_diagnostics"])

 def test_untrusted_extra_fields_are_not_copied(self):
  discovery=copy.deepcopy(DISCOVERY)
  discovery["source_results"][0]["request_diagnostics"]["url"]="https://example.org/?token=secret"
  result=snapshot(discovery,HEALTH,REVIEW)
  self.assertNotIn("url",result["sources"][1]["request_diagnostics"])
  self.assertNotIn("secret",str(result))

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

 def test_failed_request_count_cannot_exceed_request_count(self):
  discovery=copy.deepcopy(DISCOVERY)
  discovery["source_results"][0]["request_diagnostics"]["failed_request_count"]=3
  with self.assertRaisesRegex(ValueError,"failed request count"):
   snapshot(discovery,HEALTH,REVIEW)

 def test_average_latency_must_match_total(self):
  discovery=copy.deepcopy(DISCOVERY)
  discovery["source_results"][0]["request_diagnostics"]["average_request_ms"]=1
  with self.assertRaisesRegex(ValueError,"average request latency"):
   snapshot(discovery,HEALTH,REVIEW)

 def test_non_finite_latency_rejected(self):
  discovery=copy.deepcopy(DISCOVERY)
  discovery["source_results"][0]["request_diagnostics"]["total_elapsed_ms"]=math.nan
  with self.assertRaisesRegex(ValueError,"total_elapsed_ms"):
   snapshot(discovery,HEALTH,REVIEW)

 def test_unknown_failure_category_rejected(self):
  discovery=copy.deepcopy(DISCOVERY)
  discovery["source_results"][0]["request_diagnostics"]["last_request_failure_category"]="raw_exception"
  with self.assertRaisesRegex(ValueError,"failure category"):
   snapshot(discovery,HEALTH,REVIEW)

 def test_non_string_failure_category_rejected(self):
  discovery=copy.deepcopy(DISCOVERY)
  discovery["source_results"][0]["request_diagnostics"]["last_request_failure_category"]={"raw":"exception"}
  with self.assertRaisesRegex(ValueError,"failure category"):
   snapshot(discovery,HEALTH,REVIEW)

 def test_boolean_counter_rejected(self):
  discovery=copy.deepcopy(DISCOVERY)
  discovery["source_results"][0]["request_diagnostics"]["request_count"]=True
  with self.assertRaisesRegex(ValueError,"request_count"):
   snapshot(discovery,HEALTH,REVIEW)

if __name__=="__main__": unittest.main()
