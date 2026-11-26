import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from review_performance_experiment_evidence import build_review,digest
from build_performance_experiment_plan import build_plan
from diagnose_hardware_performance import diagnose_record


def fixture():
    r={"id":"sample","model":"M","workload":{"isl":1024},"configuration":{"decode_tp":4}}
    p=build_plan(r,diagnose_record(r),repetitions=2)
    e=p["experiments"][0]
    s={"schema_version":"1.0","record_sha256":digest(r),"plan_sha256":digest(p),
       "plan_id":p["plan_id"],"experiment_id":e["experiment_id"],
       "protocol":{"parameter":"decode_tp","baseline_value":4,"treatment_value":8,
       "primary_metric":{"key":"median_tpot","unit":"s","direction":"lower"},
       "practical_effect_percent":10,"protocol_source_url":"https://example.org/protocol",
       "fixed_context":{"model":"M","isl":1024}},"runs":[]}
    for condition,degree,values in [("baseline",4,[1,1]),("treatment",8,[.8,.8])]:
        for i,v in enumerate(values):
            s["runs"].append({"run_id":condition+str(i),"condition":condition,"status":"valid",
                "source_url":"https://example.org/run/"+condition+str(i),"fixed_context":s["protocol"]["fixed_context"].copy(),
                "parameter_value":degree,"metric_key":"median_tpot","unit":"s","value":v})
    return r,p,s


class EvidenceReviewTests(unittest.TestCase):
    def test_descriptive_effect_not_verdict(self):
        result=build_review(*fixture())
        self.assertAlmostEqual(result["relative_improvement_percent"],20)
        self.assertTrue(result["effect_threshold_met"])
        self.assertEqual(result["hypothesis_verdict"],"undetermined")
        self.assertEqual(result["review_status"],"needs_review")
        self.assertFalse(result["automatic_execution"])

    def test_hash_mismatch(self):
        r,p,s=fixture()
        r["model"]="Changed"
        with self.assertRaisesRegex(ValueError,"Record digest mismatch"):
            build_review(r,p,s)

    def test_context_mismatch(self):
        r,p,s=fixture()
        s["runs"][0]["fixed_context"]["isl"]=2048
        with self.assertRaisesRegex(ValueError,"context mismatch"):
            build_review(r,p,s)

    def test_failed_run_retained(self):
        r,p,s=fixture()
        s["runs"][0].update(status="failed",reason="timeout")
        result=build_review(r,p,s)
        self.assertEqual(result["review_status"],"blocked")
        self.assertIsNone(result["effect_threshold_met"])
        self.assertIn("insufficient_valid_repetitions",result["review_blockers"])
        self.assertEqual(len(result["runs"]),4)

    def test_invalid_unit_duplicate_and_nonfinite(self):
        for key,val in [("unit","ms"),("run_id","baseline1"),("value",float("nan"))]:
            r,p,s=fixture()
            s["runs"][0][key]=val
            with self.assertRaises(ValueError):
                build_review(r,p,s)

    def test_zero_baseline(self):
        r,p,s=fixture()
        for run in s["runs"][:2]:run["value"]=0
        result=build_review(r,p,s)
        self.assertIsNone(result["relative_improvement_percent"])
        self.assertEqual(result["review_status"],"blocked")


if __name__=="__main__":
    unittest.main()
