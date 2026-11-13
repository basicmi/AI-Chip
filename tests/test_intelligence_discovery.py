import copy,json,sys,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts"))
from validate_intelligence_sources import validate_registry
from run_intelligence_discovery import apply_change_detection,collect_releases,run_discovery,release_fingerprint
REGISTRY=json.loads((ROOT/"data/intelligence-sources.json").read_text()); CATALOG={"models":[]}
NOW=datetime(2026,11,13,12,0,tzinfo=timezone.utc)
class IntelligenceDiscoveryTests(unittest.TestCase):
 def test_registry_is_valid_and_unique(self):
  self.assertEqual(validate_registry(REGISTRY,today=NOW.date()),[]); self.assertGreaterEqual(len(REGISTRY["sources"]),12)
 def test_rejects_duplicate_repo_and_noncanonical_url(self):
  data=copy.deepcopy(REGISTRY); data["sources"][1]["repo"]=data["sources"][0]["repo"]; data["sources"][1]["source_url"]="https://example.com/fake"
  errors=validate_registry(data,today=NOW.date()); self.assertTrue(any("duplicated" in e for e in errors)); self.assertTrue(any("canonical GitHub" in e for e in errors))
 def test_release_collection_filters_old_draft_and_malformed_items(self):
  source=REGISTRY["sources"][0]
  payload=[{"tag_name":"v1.2","name":"Release 1.2","published_at":"2026-11-12T00:00:00Z","updated_at":"2026-11-12T00:00:00Z","html_url":"https://github.com/o/r/releases/tag/v1.2","body":" New feature\nwith details ","draft":False,"prerelease":False},
  {"tag_name":"old","published_at":"2026-01-01T00:00:00Z","html_url":"https://github.com/o/r/old"},
  {"tag_name":"draft","published_at":"2026-11-12T00:00:00Z","html_url":"https://github.com/o/r/draft","draft":True},
  {"tag_name":"bad","published_at":"not-a-date","html_url":"https://github.com/o/r/bad"}]
  found=collect_releases(source,since=datetime(2026,10,1,tzinfo=timezone.utc),fetcher=lambda url:payload)
  self.assertEqual(len(found),1); self.assertEqual(found[0]["tag_name"],"v1.2"); self.assertEqual(found[0]["review_status"],"requires_human_review")
  self.assertEqual(found[0]["body_excerpt"],"New feature with details")
 def test_change_detection_new_unchanged_updated(self):
  state={"schema_version":"1.0","items":{}}; candidate={"candidate_id":"github-release:o/r:v1","fingerprint":"a"}
  first=apply_change_detection([candidate],state,now="2026-11-13T12:00:00Z"); self.assertEqual(first[0]["change_status"],"new")
  second=apply_change_detection([candidate],state,now="2026-11-14T12:00:00Z"); self.assertEqual(second[0]["change_status"],"unchanged")
  third=apply_change_detection([{**candidate,"fingerprint":"b"}],state,now="2026-11-15T12:00:00Z")
  self.assertEqual(third[0]["change_status"],"updated"); self.assertEqual(third[0]["first_seen_at"],"2026-11-13T12:00:00Z")
 def test_run_is_read_only_and_continues_after_source_error(self):
  def fetcher(url):
   if "NVIDIA/TensorRT-LLM" in url: raise TimeoutError()
   return []
  report=run_discovery(REGISTRY,CATALOG,now=NOW,release_fetcher=fetcher,model_report={"models":[],"model_count":0,"observed":0,"new_publisher_candidates":[],"publisher_discovery_errors":[]},state={"schema_version":"1.0","items":{}})
  self.assertTrue(report["read_only"]); self.assertEqual(report["sources_unavailable"],1); self.assertEqual(len(report["source_results"]),len(REGISTRY["sources"]))
  self.assertIn("does not update formal",report["policy"])
 def test_model_repo_updates_are_fingerprinted_without_claiming_support(self):
  report=run_discovery({"sources":[]},CATALOG,now=NOW,release_fetcher=lambda _:[],model_report={"models":[{"model_id":"org/model","status":"observed","repo_sha":"abc","last_modified":"2026-11-12T00:00:00Z"}],"model_count":1,"observed":1,"new_publisher_candidates":[]},state={"schema_version":"1.0","items":{}})
  self.assertEqual(report["review_queue"][0]["candidate_type"],"model_repository"); self.assertEqual(report["review_queue"][0]["evidence_scope"],"model_repository_metadata_only")
 def test_release_fingerprint_changes_when_release_notes_change(self):
  a={"tag_name":"v1","name":"v1","body":"A","published_at":"2026-11-12T00:00:00Z","html_url":"https://github.com/o/r","prerelease":False}
  self.assertNotEqual(release_fingerprint(a),release_fingerprint({**a,"body":"B"}))
  self.assertNotEqual(release_fingerprint(a),release_fingerprint({**a,"updated_at":"2026-11-13T00:00:00Z"}))
if __name__=="__main__": unittest.main()
