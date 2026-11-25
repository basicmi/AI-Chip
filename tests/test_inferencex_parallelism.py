import unittest
from test_inferencex_prefill_decode_scaling import row
from analyze_inferencex_parallelism import build_report


def pair():
    a, b = row("a", 8, 8), row("b", 8, 8)
    b["configuration"]["decode_tp"] = 4
    return a, b


class ParallelismTests(unittest.TestCase):
    def test_strict(self):
        a,b=pair()
        report=build_report({"records":[a,b]})
        self.assertTrue(report["strict_series"])
        self.assertFalse(report["review_candidates"])
        self.assertTrue(all(s["axis"]=="decode_tp" for s in report["strict_series"]))
        self.assertEqual([p["parallelism_degree"] for p in report["strict_series"][0]["points"]],[4,8])

    def test_recipe_mismatch(self):
        a,b=pair()
        b["software"]["recipe_fingerprint"]="different"
        report=build_report({"records":[a,b]})
        self.assertFalse(report["strict_series"])
        self.assertTrue(report["review_candidates"])
        self.assertIn("recipe_fingerprints_differ",report["review_candidates"][0]["review_reasons"])
        self.assertNotIn("median_of_published_values",report["review_candidates"][0]["levels"][0])

    def test_missing_recipe(self):
        a,b=pair()
        del b["software"]["recipe_fingerprint"]
        report=build_report({"records":[a,b]})
        self.assertFalse(report["strict_series"])
        self.assertIn("recipe_fingerprint_missing",report["review_candidates"][0]["review_reasons"])

    def test_other_axis_or_gpu_count_cannot_change(self):
        for section,field,value in [
            ("configuration","prefill_tp",4),
            ("system","physical_decode_gpus",16),
            ("workload","isl",4096),
            ("software","framework","other"),
        ]:
            a,b=pair()
            b[section][field]=value
            report=build_report({"records":[a,b]})
            self.assertFalse(report["strict_series"])
            self.assertFalse(report["review_candidates"])

    def test_ep_axis(self):
        a,b=row("a",8,8),row("b",8,8)
        a["configuration"]["prefill_ep"]=1
        b["configuration"]["prefill_ep"]=2
        report=build_report({"records":[a,b]})
        self.assertTrue(report["strict_series"])
        self.assertTrue(all(s["axis"]=="prefill_ep" for s in report["strict_series"]))

    def test_invalid_axis(self):
        a,b=pair()
        b["configuration"]["decode_tp"]=True
        self.assertFalse(build_report({"records":[a,b]})["strict_series"])

    def test_strict_subset_survives_missing_recipe(self):
        a,b=pair()
        c=row("c",8,8)
        del c["software"]["recipe_fingerprint"]
        report=build_report({"records":[a,b,c]})
        self.assertTrue(report["strict_series"])
        self.assertTrue(report["review_candidates"])
        self.assertTrue(all(o["record_id"]!="c" for s in report["strict_series"] for p in s["points"] for o in p["observations"]))

    def test_deterministic(self):
        a,b=pair()
        self.assertEqual(build_report({"records":[a,b]}),build_report({"records":[b,a]}))


if __name__=="__main__":
    unittest.main()
