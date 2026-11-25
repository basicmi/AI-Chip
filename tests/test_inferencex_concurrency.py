import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_inferencex_concurrency import build_report


def row(rid, concurrency, value):
    return {
        "id": rid, "source_id": "inferencex", "source_class": "third_party_public_benchmark",
        "evidence_level": "publisher_published_observation",
        "benchmark_suite": "SemiAnalysis InferenceX", "benchmark_version": None,
        "model": "dsr1", "model_display_name": "DeepSeek-R1-0528",
        "scenario": "single_turn", "division": "third_party", "availability": "published",
        "weight_data_types": "FP8", "inferred": False, "errors": 0,
        "system_type": "datacenter",
        "system": {"hardware": "GPU A", "physical_prefill_gpus": 0,
                   "physical_decode_gpus": 8, "is_multinode": False, "workers": []},
        "software": {"framework": "vllm", "recipe_fingerprint": "recipe-a"},
        "configuration": {"decode_tp": 8, "workflow_run_id": rid},
        "workload": {"benchmark_type": "single_turn", "isl": 1024, "osl": 1024,
                     "concurrency": concurrency, "precision": "FP8",
                     "speculative_method": "none", "disaggregated": False},
        "normalized_metrics": {"output_throughput_per_gpu": {
            "value": value, "unit": "tok/s/GPU", "family": "throughput", "direction": "higher"}},
        "source_url": "https://example.org/" + rid,
    }


class ConcurrencyTests(unittest.TestCase):
    def test_observed_points_and_repeats(self):
        report = build_report({"records": [row("b", 32, 120), row("a", 8, 80), row("c", 32, 140)]})
        sweep = report["sweeps"][0]
        self.assertEqual(len(report["sweeps"]), 1)
        self.assertEqual([p["concurrency"] for p in sweep["points"]], [8, 32])
        self.assertEqual(sweep["points"][1]["median_of_published_values"], 130)
        self.assertEqual(sweep["points"][1]["count"], 2)
        self.assertEqual(sweep["points"][1]["observations"][0]["source_url"], "https://example.org/b")

    def test_confounded_runs_do_not_mix(self):
        for section, field, value in [
            ("workload", "isl", 2048), ("workload", "precision", "BF16"),
            ("system", "physical_decode_gpus", 16), ("system", "hardware", "GPU B"),
            ("configuration", "decode_tp", 4), ("software", "recipe_fingerprint", "recipe-b"),
        ]:
            with self.subTest(field=field):
                a, b = row("a", 8, 80), row("b", 32, 120)
                b[section][field] = value
                self.assertEqual(build_report({"records": [a, b]})["sweeps"], [])

    def test_missing_recipe_fails_closed(self):
        b = row("b", 32, 120)
        del b["software"]["recipe_fingerprint"]
        report = build_report({"records": [row("a", 8, 80), b]})
        self.assertEqual(report["sweeps"], [])
        self.assertEqual(report["summary"]["exclusion_reason_counts"]["missing_hardware_or_recipe_fingerprint"], 1)

    def test_invalid_unit_and_concurrency(self):
        b = row("b", 32, 120)
        b["normalized_metrics"]["output_throughput_per_gpu"]["unit"] = "tok/s"
        self.assertEqual(build_report({"records": [row("a", 8, 80), b]})["sweeps"], [])
        b = row("b", True, 120)
        self.assertEqual(build_report({"records": [row("a", 8, 80), b]})["sweeps"], [])

    def test_deterministic_order(self):
        rows = [row("a", 8, 80), row("b", 32, 120)]
        self.assertEqual(build_report({"records": rows}), build_report({"records": rows[::-1]}))


if __name__ == "__main__":
    unittest.main()
