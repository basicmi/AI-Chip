import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from assess_performance_knowledge_applicability import assess_entry,assess_catalog


def entry():
    return {"knowledge_id":"pk-test","knowledge_status":"human_reviewed_claim","topic":"runtime",
      "verdict":"supported","scope":{"fixed_context":{
        "hardware":{"gpu":"A100","num_gpus":8},
        "model":"M","workload":{"isl":4096,"batch_size":32},
        "parallelism":{"tp":8},"software":{"runtime":"v1"},
        "topology":{"interconnect":"NVLink"}},
        "metric":{"key":"median_tpot","unit":"s","direction":"lower"},
        "intervention":{"parameter":"tp","baseline_value":4,"treatment_value":8}}}


class ApplicabilityTests(unittest.TestCase):
    def test_exact_declared_context_match(self):
        e=entry()
        target=e["scope"]["fixed_context"]
        result=assess_entry(e,target)
        self.assertEqual(result["applicability_status"],"declared_context_match")
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["automatic_transfer_approval"])

    def test_missing_is_unknown_not_match(self):
        e=entry()
        target={"hardware":{"gpu":"A100","num_gpus":8},"model":"M"}
        result=assess_entry(e,target)
        self.assertEqual(result["applicability_status"],"insufficient_context")
        self.assertGreater(result["unknown_count"],0)

    def test_hardware_or_workload_mismatch_blocks_reuse(self):
        e=entry()
        target={**e["scope"]["fixed_context"],"hardware":{"gpu":"H100","num_gpus":8}}
        result=assess_entry(e,target)
        self.assertEqual(result["applicability_status"],"not_applicable_under_declared_context")
        self.assertGreater(result["mismatch_count"],0)

    def test_target_only_fields_are_not_silently_ignored(self):
        e=entry()
        target={**e["scope"]["fixed_context"],"new_field":"unknown-stack"}
        result=assess_entry(e,target)
        self.assertIn("new_field",result["unassessed_target_fields"])

    def test_catalog_order_and_metric_match(self):
        e=entry()
        catalog={"schema_version":"1.0","entries":[e]}
        target=e["scope"]["fixed_context"]
        report=assess_catalog(catalog,target,{"key":"median_tpot","unit":"s","direction":"lower"})
        self.assertEqual(report["results"][0]["metric_compatibility"],"exact_match")
        self.assertEqual(report["policy"]["missing_context_is_unknown"],True)

    def test_metric_mismatch(self):
        e=entry()
        report=assess_catalog({"schema_version":"1.0","entries":[e]},
          e["scope"]["fixed_context"],{"key":"p99_tpot","unit":"s","direction":"lower"})
        self.assertEqual(report["results"][0]["metric_compatibility"],"mismatch_or_unknown")


if __name__=="__main__":
    unittest.main()
