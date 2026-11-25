import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_inferencex_coverage import build_report


def row(rid, isl=1024, osl=256, concurrency=16, gpu=8, recipe="recipe-a"):
    return {
        "id": rid, "source_id": "inferencex", "source_class": "third_party_public_benchmark",
        "evidence_level": "publisher_published_observation",
        "benchmark_suite": "SemiAnalysis InferenceX", "benchmark_version": "2026.1",
        "model": "model-a", "model_display_name": "Model A",
        "scenario": "single_turn", "division": "third_party", "availability": "published",
        "weight_data_types": "FP8", "inferred": False, "errors": 0,
        "system_type": "datacenter",
        "system": {"hardware": "GPU A", "physical_prefill_gpus": 0,
                   "physical_decode_gpus": gpu, "is_multinode": False, "workers": []},
        "software": {"framework": "vllm", "recipe_fingerprint": recipe},
        "configuration": {"decode_tp": 8, "workflow_run_id": rid},
        "workload": {"benchmark_type": "single_turn", "isl": isl, "osl": osl,
                     "concurrency": concurrency, "precision": "FP8",
                     "speculative_method": "none", "disaggregated": False},
        "normalized_metrics": {
            "output_throughput_per_gpu": {"value": 100, "unit": "tok/s/GPU", "family": "throughput", "direction": "higher"},
            "median_ttft": {"value": 1.0, "unit": "s", "family": "latency", "direction": "lower"},
        },
        "source_url": "https://example.org/" + rid,
    }


class CoverageTests(unittest.TestCase):
    def test_field_coverage_counts_false_boolean_as_present(self):
        report=build_report({"records":[row("a"),row("b")]})
        field=report["field_coverage"]["is_multinode"]
        self.assertEqual(field["present_records"],2)
        self.assertEqual(field["distinct_values"],1)

    def test_metric_coverage_validates_units_and_values(self):
        a,b=row("a"),row("b")
        b["normalized_metrics"]["median_ttft"]["unit"]="ms"
        report=build_report({"records":[a,b]})
        self.assertEqual(report["metric_coverage"]["median_ttft"]["valid_records"],1)
        self.assertEqual(report["metric_coverage"]["output_throughput_per_gpu"]["valid_records"],2)

    def test_candidate_sweeps_require_matching_context_and_two_levels(self):
        rows=[row("a",concurrency=8),row("b",concurrency=32)]
        report=build_report({"records":rows})
        self.assertGreater(report["analysis_readiness"]["concurrency_sweeps"]["candidate_metric_series"],0)
        rows[1]["software"]["recipe_fingerprint"]="other"
        report=build_report({"records":rows})
        self.assertEqual(report["analysis_readiness"]["concurrency_sweeps"]["candidate_metric_series"],0)

    def test_isl_osl_grid_requires_two_values_on_both_axes(self):
        rows=[row("a",isl=512,osl=128),row("b",isl=512,osl=512),row("c",isl=512,osl=1024)]
        report=build_report({"records":rows})
        self.assertEqual(report["analysis_readiness"]["isl_osl_interaction"]["candidate_metric_series"],0)
        rows.append(row("d",isl=2048,osl=512))
        report=build_report({"records":rows})
        self.assertGreater(report["analysis_readiness"]["isl_osl_interaction"]["candidate_metric_series"],0)

    def test_gpu_count_coverage_and_records_without_blockers(self):
        report=build_report({"records":[row("a",gpu=8),row("b",gpu=16)]})
        self.assertEqual(report["field_coverage"]["physical_decode_gpus"]["distinct_values"],2)
        self.assertEqual(report["summary"]["records_without_any_comparability_blocker"],2)

    def test_missing_recipe_does_not_qualify_for_strict_analysis(self):
        a,b=row("a",concurrency=8),row("b",concurrency=32)
        del b["software"]["recipe_fingerprint"]
        report=build_report({"records":[a,b]})
        self.assertEqual(report["analysis_readiness"]["concurrency_sweeps"]["candidate_metric_series"],0)
        self.assertEqual(report["field_coverage"]["recipe_fingerprint"]["present_records"],1)

    def test_non_inferencex_records_are_ignored(self):
        a=row("a")
        a["source_id"]="other"
        report=build_report({"records":[a]})
        self.assertEqual(report["summary"]["inferencex_records"],0)

    def test_deterministic(self):
        rows=[row("a",concurrency=8),row("b",concurrency=32)]
        self.assertEqual(build_report({"records":rows}),build_report({"records":rows[::-1]}))


if __name__ == "__main__":
    unittest.main()
