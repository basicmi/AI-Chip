"""Offline tests for evidence-driven, non-executing performance experiment plans."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from diagnose_hardware_performance import diagnose_record
from build_performance_experiment_plan import build_plan, markdown_report


def record():
    return {
        "id": "fixture-decode-tp",
        "model": "test-model",
        "model_display_name": "Test Model",
        "workload": {"benchmark_type": "decode", "isl": 4096, "osl": 1024, "concurrency": 32, "precision": "FP8", "disaggregated": False},
        "system": {"hardware": "Test GPU", "nodes": 1, "total_accelerators": 8, "accelerators_per_node": 8},
        "software": {"framework": "vLLM", "recipe_fingerprint": "recipe-abc"},
        "configuration": {"decode_tp": 8},
        "normalized_metrics": {
            "median_tpot": {"value": 0.04, "unit": "s", "direction": "lower", "family": "latency"},
            "output_throughput_per_gpu": {"value": 120, "unit": "tok/s/GPU", "direction": "higher", "family": "throughput"}
        }
    }


class PerformanceExperimentPlanTests(unittest.TestCase):
    def test_plan_is_generated_from_diagnosis_without_running_experiments(self):
        source = record()
        diagnosis = diagnose_record(source)
        plan = build_plan(source, diagnosis)
        self.assertEqual(plan["diagnosis_verdict"], "undetermined")
        self.assertFalse(plan["automatic_experiment_execution"])
        self.assertEqual(plan["record_context"]["record_id"], source["id"])
        self.assertGreaterEqual(plan["experiment_count"], 5)
        self.assertTrue(all(item["execution"]["performed"] is False for item in plan["experiments"]))
        self.assertTrue(all(item["execution"]["result"] == "not_run" for item in plan["experiments"]))
        self.assertTrue(all(item["priority"] == "not_ranked" for item in plan["experiments"]))
        self.assertTrue(all(item["treatment"]["parameter"] is None for item in plan["experiments"]))
        self.assertTrue(any(item["mechanism"] == "roofline" for item in plan["experiments"]))
        self.assertTrue(any(item["mechanism"] == "communication" for item in plan["experiments"]))
        self.assertTrue(any(item["mechanism"] == "kv_cache_capacity_pressure" for item in plan["experiments"]))
        self.assertTrue(any(item["mechanism"] == "runtime_scheduling_or_queueing" for item in plan["experiments"]))

    def test_compute_and_memory_ceiling_candidates_are_not_conflated(self):
        source = record()
        diagnosis = diagnose_record(source)
        diagnosis["attribution"]["candidates"] = [
            {"mechanism": "roofline_compute_ceiling", "status": "observed", "observation": "compute ceiling lower"},
            {"mechanism": "roofline_memory_ceiling", "status": "observed", "observation": "memory ceiling lower"}
        ]
        plan = build_plan(source, diagnosis)
        self.assertEqual([x["mechanism"] for x in plan["experiments"]], ["roofline_compute", "roofline_memory"])

    def test_plan_contains_falsifiable_support_and_disconfirmation_criteria(self):
        source = record()
        plan = build_plan(source, diagnose_record(source))
        for item in plan["experiments"]:
            self.assertTrue(item["hypothesis"])
            self.assertTrue(item["falsifiable_question"])
            self.assertTrue(item["supporting_result"])
            self.assertTrue(item["disconfirming_result"])
            self.assertTrue(item["controls"])
            self.assertTrue(item["measurements"])
            self.assertTrue(item["interpretation_limit"])

    def test_record_mismatch_and_non_undetermined_verdict_are_rejected(self):
        source = record()
        diagnosis = diagnose_record(source)
        with self.assertRaisesRegex(ValueError, "does not match"):
            build_plan(source, {**diagnosis, "record_id": "another-record"})
        with self.assertRaisesRegex(ValueError, "undetermined"):
            build_plan(source, {**diagnosis, "overall_verdict": "bottleneck"})

    def test_repetitions_are_bounded_and_markdown_is_explicitly_not_run(self):
        source = record()
        diagnosis = diagnose_record(source)
        with self.assertRaisesRegex(ValueError, "2..10"):
            build_plan(source, diagnosis, repetitions=1)
        report = markdown_report(build_plan(source, diagnosis, repetitions=4))
        self.assertIn("Execution: **not performed**", report)
        self.assertIn("must be specified by the engineer", report)
        self.assertIn("4 per condition", report)


if __name__ == "__main__":
    unittest.main()
