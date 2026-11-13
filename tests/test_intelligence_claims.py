import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from extract_intelligence_claims import METHOD,extract_candidate_claims,extract_report,validate_claim,markdown_summary

class ClaimExtractionTests(unittest.TestCase):
 def setUp(self):
  self.candidate={"candidate_id":"feed:nvidia:123","candidate_type":"vendor_announcement",
   "source_id":"nvidia-news","source_name":"NVIDIA Newsroom","publisher":"NVIDIA",
   "source_type":"vendor_primary","independence":"vendor","url":"https://example.com/announcement",
   "published_at":"2026-11-12T00:00:00Z","evidence_scope":"official_vendor_feed_metadata_and_excerpt",
   "title":"New GPU platform announced",
   "excerpt":"The system provides 72 GPUs per rack and up to 1.8 TB/s interconnect bandwidth. The platform supports FP8 inference."}
 def test_extracts_numeric_claims_and_scope(self):
  claims=extract_candidate_claims(self.candidate); numeric=[x for x in claims if x["value"] is not None]
  self.assertEqual(len(numeric),2); self.assertEqual(numeric[0]["value"],72)
  self.assertEqual(numeric[0]["unit"].lower(),"gpus")
  self.assertEqual(numeric[0]["scope"]["status"],"explicit_per_unit")
  self.assertEqual(numeric[1]["value"],1.8); self.assertEqual(numeric[1]["unit"].lower(),"tb/s")
 def test_qualitative_claim_has_no_invented_value(self):
  claims=extract_candidate_claims(self.candidate)
  qualitative=[x for x in claims if x["value"] is None]
  self.assertTrue(any("supports FP8 inference" in x["statement"] for x in qualitative))
  self.assertTrue(all(x["unit"] is None for x in qualitative))
 def test_all_claims_remain_unverified(self):
  for claim in extract_candidate_claims(self.candidate):
   self.assertEqual(claim["review_status"],"unverified_candidate")
   self.assertEqual(claim["extraction"]["method"],METHOD)
   self.assertEqual(claim["extraction"]["confidence"],"low")
   self.assertEqual(validate_claim(claim),[])
 def test_rejects_invalid_source_url(self):
  self.assertEqual(extract_candidate_claims({**self.candidate,"url":"javascript:alert(1)"}),[])
 def test_preprint_not_relabelled_verified(self):
  c={**self.candidate,"candidate_type":"research_preprint","source_type":"research_paper","independence":"independent"}
  claims=extract_candidate_claims(c)
  self.assertTrue(any(x["claim_type"]=="research_finding" for x in claims))
  self.assertTrue(all(x["review_status"]=="unverified_candidate" for x in claims))
 def test_report_and_summary(self):
  report=extract_report({"review_queue":[self.candidate]},generated_at="2026-11-13T00:00:00Z")
  self.assertEqual(report["claim_count"],len(report["claims"]))
  self.assertIn("human review required",markdown_summary(report))
  self.assertIn("unverified candidates",report["policy"])
 def test_deduplicates_identical_sentence(self):
  c={**self.candidate,"title":"Overview","excerpt":"The system provides 72 GPUs per rack. The system provides 72 GPUs per rack."}
  self.assertEqual(len(extract_candidate_claims(c)),1)

if __name__=="__main__": unittest.main()
