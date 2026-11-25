import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_inferencex_gpu_scaling import build_report


def row(rid, gpus, per_gpu, prefill=0, multinode=False):
    return {
        "id": rid, "source_id": "inferencex", "source_class": "third_party_public_benchmark",
        "evidence_level": "publisher_published_observation",
        "benchmark_suite": "SemiAnalysis InferenceX", "benchmark_version": None,
        "model": "dsr1", "model_display_name": "DeepSeek-R1-0528",
        "scenario": "single_turn", "division": "third_party", "availability": "published",
        "weight_data_types": "FP8", "inferred": False, "errors": 0,
        "system_type": "datacenter",
        "system": {"hardware": "GPU A", "physical_prefill_gpus": prefill,
                   "physical_decode_gpus": gpus, "is_multinode": multinode, "workers": []},
        "software": {"framework": "vllm", "recipe_fingerprint": "recipe-a"},
        "configuration": {"decode_tp": 8, "workflow_run_id": rid},
        "workload": {"benchmark_type": "single_turn", "isl": 1024, "osl": 1024,
                     "concurrency": 32, "precision": "FP8",
                     "speculative_method": "none", "disaggregated": False},
        "normalized_metrics": {"output_throughput_per_gpu": {
            "value": per_gpu, "unit": "tok/s/GPU", "family": "throughput", "direction": "higher"}},
        "source_url": "https://example.org/" + rid,
    }


class GpuScalingTests(unittest.TestCase):
    def test_ideal_linear_scaling_is_one_hundred_percent(self):
        report=build_report({"records":[row("a",8,100),row("b",16,100)]})
        self.assertEqual(len(report["series"]),1)
        points=report["series"][0]["points"]
        self.assertEqual([p["decode_gpu_count"] for p in points],[8,16])
        self.assertEqual([p["estimated_aggregate_throughput"]["value"] for p in points],[800,1600])
        self.assertEqual([p["relative_scaling_efficiency_percent"] for p in points],[100,100])

    def test_sublinear_scaling_is_quantified_against_baseline(self):
        report=build_report({"records":[row("a",8,100),row("b",16,80),row("c",32,60)]})
        points=report["series"][0]["points"]
        self.assertEqual([p["relative_scaling_efficiency_percent"] for p in points],[100,80,60])

    def test_repeated_observations_use_median_and_retain_sources(self):
        report=build_report({"records":[row("a",8,90),row("b",8,110),row("c",16,100)]})
        points=report["series"][0]["points"]
        self.assertEqual(points[0]["throughput_per_gpu"]["median_of_published_values"],100)
        self.assertEqual(points[0]["count"],2)
        self.assertEqual(len(points[0]["observations"]),2)

    def test_workload_recipe_and_stable_config_must_match(self):
        for mutate in [
            lambda r: r["workload"].update(isl=2048),
            lambda r: r["software"].update(recipe_fingerprint="recipe-b"),
            lambda r: r["configuration"].update(decode_tp=16),
        ]:
            a,b=row("a",8,100),row("b",16,80)
            mutate(b)
            self.assertEqual(build_report({"records":[a,b]})["series"],[])

    def test_multinode_and_hardware_context_are_not_mixed(self):
        a,b=row("a",8,100),row("b",16,80,multinode=True)
        self.assertEqual(build_report({"records":[a,b]})["series"],[])
        b=row("b",16,80);b["system"]["hardware"]="GPU B"
        self.assertEqual(build_report({"records":[a,b]})["series"],[])

    def test_mixed_prefill_decode_system_is_excluded(self):
        report=build_report({"records":[row("a",8,100,prefill=8),row("b",16,80,prefill=16)]})
        self.assertEqual(report["series"],[])
        self.assertEqual(report["summary"]["exclusion_reason_counts"]["prefill_decode_disaggregated_or_mixed_system"],2)

    def test_invalid_gpu_count_and_metric_are_excluded(self):
        a,b=row("a",8,100),row("b",16,80)
        b["system"]["physical_decode_gpus"]=0
        self.assertEqual(build_report({"records":[a,b]})["series"],[])
        b=row("b",16,80)
        b["normalized_metrics"]["output_throughput_per_gpu"]["unit"]="tok/s"
        self.assertEqual(build_report({"records":[a,b]})["series"],[])

    def test_deterministic_and_estimate_is_labelled(self):
        rows=[row("a",8,100),row("b",16,90)]
        one=build_report({"records":rows})
        self.assertEqual(one,build_report({"records":rows[::-1]}))
        point=one["series"][0]["points"][0]
        self.assertTrue(point["estimated_aggregate_throughput"]["not_directly_measured"])
        self.assertTrue(all(o["source_url"] for o in point["observations"]))


if __name__ == "__main__":
    unittest.main()
