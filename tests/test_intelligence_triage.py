import sys, unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from triage_intelligence_claims import build_queue,markdown

NOW=datetime(2026,11,14,tzinfo=timezone.utc)
def fixtures():
    candidates=[{"candidate_id":"c1","change_status":"new"},
                {"candidate_id":"c2","change_status":"updated"},
                {"candidate_id":"c3","change_status":"new"}]
    discovery={"review_queue":candidates}
    def claim(cid,candidate,statement,value,when="2026-11-13T00:00:00Z"):
        return {"claim_id":cid,"candidate_id":candidate,"statement":statement,"topic":"memory_capacity",
                "claim_type":"quantitative_specification","value":value,"unit":"GB",
                "review_status":"unverified_candidate","source":{"publisher":"Vendor","source_type":"vendor_primary",
                "url":"https://example.org/"+cid,"published_at":when}}
    rows=[claim("a","c1","Example GPU has 180 GB HBM",180),
          claim("b","c2","Example GPU has 180 GB HBM",180),
          claim("c","c3","Example GPU has 192 GB HBM",192)]
    claim_report={"schema_version":"1.0","generated_at":"2026-11-14T00:00:00Z","claim_count":3,"claims":rows}
    graph={"schema_version":"1.0","generated_at":"2026-11-14T00:01:00Z",
           "input_claim_count":3,"summary":{"independently_verified_claims":0},
           "nodes":[{"type":"claim_candidate","claim_id":x["claim_id"]} for x in rows],
           "scoped_comparisons":[{"claim_ids":["a","c"],"status":"possible_specification_conflict"}]}
    return discovery,claim_report,graph

class TriageTests(unittest.TestCase):
    def test_exact_duplicates_collapsed_without_corroboration(self):
        result=build_queue(*fixtures(),now=NOW)
        self.assertEqual(result["summary"]["input_claims"],3)
        self.assertEqual(result["summary"]["triage_groups"],2)
        self.assertEqual(result["summary"]["collapsed_duplicate_claims"],1)
        self.assertEqual(result["summary"]["automatically_verified"],0)
        pair=next(x for x in result["queue"] if len(x["related_claim_ids"])>1)
        self.assertEqual(pair["related_claim_ids"],["a","b"])
        self.assertIn("no independent corroboration",pair["note"])
        self.assertFalse(result["score_is_truth_confidence"])
    def test_conflict_prioritizes_but_never_proves(self):
        result=build_queue(*fixtures(),now=NOW)
        self.assertEqual(result["summary"]["possible_conflict_claims"],2)
        self.assertTrue(any("reviewer_scoped_possible_specification_conflict" in x["risk_flags"] for x in result["queue"]))
        self.assertIn("not confidence in truth",markdown(result))
    def test_stale_and_undated_source(self):
        d,c,g=fixtures()
        c["claims"][0]["source"]["published_at"]="2020-01-01T00:00:00Z"
        c["claims"][1]["source"]["published_at"]=None
        result=build_queue(d,c,g,now=NOW)
        self.assertEqual(result["summary"]["stale_or_undated_claims"],2)
    def test_rejects_claim_status_escalation(self):
        d,c,g=fixtures()
        c["claims"][0]["review_status"]="verified"
        with self.assertRaisesRegex(ValueError,"unverified"):
            build_queue(d,c,g,now=NOW)
    def test_rejects_mismatched_counts_and_membership(self):
        d,c,g=fixtures()
        g["input_claim_count"]=10
        with self.assertRaisesRegex(ValueError,"counts"):
            build_queue(d,c,g,now=NOW)
        d,c,g=fixtures()
        g["nodes"].pop()
        with self.assertRaisesRegex(ValueError,"membership"):
            build_queue(d,c,g,now=NOW)
    def test_rejects_missing_discovery_candidate(self):
        d,c,g=fixtures()
        d["review_queue"].pop()
        with self.assertRaisesRegex(ValueError,"missing from discovery"):
            build_queue(d,c,g,now=NOW)
    def test_rejects_fabricated_verification(self):
        d,c,g=fixtures()
        g["summary"]["independently_verified_claims"]=1
        with self.assertRaisesRegex(ValueError,"verification"):
            build_queue(d,c,g,now=NOW)
    def test_deterministic_tie_order_and_top_limit(self):
        a=build_queue(*fixtures(),now=NOW,top=1)
        b=build_queue(*fixtures(),now=NOW,top=1)
        self.assertEqual(a["queue"],b["queue"])
        self.assertEqual(len(a["queue"]),1)
        self.assertEqual(a["total_queue_groups"],2)
if __name__=="__main__":unittest.main()
