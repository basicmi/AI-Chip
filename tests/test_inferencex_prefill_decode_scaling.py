import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_inferencex_prefill_decode_scaling import build_report


def row(rid, prefill, decode, ttft=1.0, tpot=0.02, out_tput=100):
    return {
        "id": rid, "source_id": "inferencex", "source_class": "third_party_public_benchmark",
        "evidence_level": "publisher_published_observation",
        "benchmark_suite": "SemiAnalysis InferenceX", "benchmark_version": "2026.1",
        "model": "model-a", "model_display_name": "Model A",
        "scenario": "single_turn", "division": "third_party", "availability": "published",
        "weight_data_types": "FP8", "inferred": False, "errors": 0,
        "system_type": "datacenter",
        "system": {"hardware": "GPU A", "physical_prefill_gpus": prefill,
                   "physical_decode_gpus": decode, "is_multinode": False, "workers": []},
        "software": {"framework": "vllm", "recipe_fingerprint": "recipe-a"},
        "configuration": {"prefill_tp": 8, "decode_tp": 8, "workflow_run_id": rid},
        "workload": {"benchmark_type": "single_turn", "isl": 1024, "osl": 256,
                     "concurrency": 32, "precision": "FP8",
                     "speculative_method": "none", "disaggregated": prefill > 0},
        "normalized_metrics": {
            "median_ttft": {"value": ttft, "unit": "s", "family": "latency", "direction": "lower"},
            "median_tpot": {"value": tpot, "unit": "s", "family": "latency", "direction": "lower"},
            "output_throughput_per_gpu": {"value": out_tput, "unit": "tok/s/GPU", "family": "throughput", "direction": "higher"},
        },
        "source_url": "https://example.org/" + rid,
    }


class PrefillDecodeScalingTests(unittest.TestCase):
    def test_prefill_gpu_count_varies_with_decode_count_fixed(self):
        report=build_report({"records":[row("a",4,8,ttft=2),row("b",8,8,ttft=1)]})
        series=next(s for s in report["series"] if s["phase"]=="prefill" and s["metric"]=="median_ttft")
        self.assertEqual([p["phase_gpu_count"] for p in series["points"]],[4,8])
        self.assertEqual([p["change_from_smallest_observed_gpu_count_percent"] for p in series["points"]],[0,-50])

    def test_decode_gpu_count_varies_with_prefill_count_fixed(self):
        report=build_report({"records":[row("a",0,8,tpot=.02),row("b",0,16,tpot=.015)]})
        series=next(s for s in report["series"] if s["phase"]=="decode" and s["metric"]=="median_tpot")
        self.assertEqual([p["phase_gpu_count"] for p in series["points"]],[8,16])
        self.assertAlmostEqual(series["points"][1]["change_from_smallest_observed_gpu_count_percent"],-25)

    def test_prefill_and_decode_counts_are_not_added_or_mixed(self):
        rows=[row("a",4,8),row("b",8,8),row("c",4,16)]
        report=build_report({"records":rows})
        prefill=next(s for s in report["series"] if s["phase"]=="prefill" and s["metric"]=="median_ttft")
        decode=next(s for s in report["series"] if s["phase"]=="decode" and s["metric"]=="median_tpot")
        self.assertEqual([p["phase_gpu_count"] for p in prefill["points"]],[4,8])
        self.assertEqual([p["phase_gpu_count"] for p in decode["points"]],[8,16])

    def test_workload_recipe_and_other_phase_count_must_match(self):
        a,b=row("a",4,8),row("b",8,8)
        b["workload"]["isl"]=2048
        self.assertFalse(build_report({"records":[a,b]})["series"])
        b=row("b",8,16)
        self.assertFalse(build_report({"records":[a,b]})["series"])
        b=row("b",8,8);b["software"]["recipe_fingerprint"]="other"
        self.assertFalse(build_report({"records":[a,b]})["series"])

    def test_topology_and_parallel_configuration_must_match(self):
        a,b=row("a",4,8),row("b",8,8)
        b["system"]["is_multinode"]=True
        self.assertFalse(build_report({"records":[a,b]})["series"])
        b=row("b",8,8);b["configuration"]["prefill_tp"]=4
        self.assertFalse(build_report({"records":[a,b]})["series"])

    def test_metric_units_are_validated_per_metric(self):
        a,b=row("a",4,8),row("b",8,8)
        b["normalized_metrics"]["median_ttft"]["unit"]="ms"
        report=build_report({"records":[a,b]})
        self.assertFalse(any(s["phase"]=="prefill" and s["metric"]=="median_ttft" for s in report["series"]))
        self.assertTrue(any(s["phase"]=="decode" and s["metric"]=="median_tpot" for s in report["series"]))

    def test_zero_prefill_is_not_a_prefill_scaling_point(self):
        report=build_report({"records":[row("a",0,8),row("b",0,16)]})
        self.assertFalse(any(s["phase"]=="prefill" for s in report["series"]))

    def test_deterministic_and_sources_retained(self):
        rows=[row("a",4,8),row("b",8,8)]
        one=build_report({"records":rows})
        self.assertEqual(one,build_report({"records":rows[::-1]}))
        self.assertTrue(all(o["source_url"] for s in one["series"] for p in s["points"] for o in p["observations"]))


if __name__ == "__main__":
    unittest.main()
