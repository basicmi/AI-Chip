import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_inferencex_isl_osl_interaction import build_report


def row(rid, isl, osl, value):
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
        "workload": {"benchmark_type": "single_turn", "isl": isl, "osl": osl,
                     "concurrency": 16, "precision": "FP8",
                     "speculative_method": "none", "disaggregated": False},
        "normalized_metrics": {"output_throughput_per_gpu": {
            "value": value, "unit": "tok/s/GPU", "family": "throughput", "direction": "higher"}},
        "source_url": "https://example.org/" + rid,
    }


class InteractionMatrixTests(unittest.TestCase):
    def test_complete_observed_grid_and_repeats(self):
        rows=[
            row("a",512,128,100),row("b",512,512,90),
            row("c",2048,128,80),row("d",2048,512,70),
            row("e",2048,512,74),
        ]
        report=build_report({"records":rows})
        self.assertEqual(len(report["matrices"]),1)
        matrix=report["matrices"][0]
        self.assertEqual(matrix["isl_values"],[512,2048])
        self.assertEqual(matrix["osl_values"],[128,512])
        self.assertEqual(matrix["expected_grid_cells"],4)
        self.assertEqual(matrix["observed_grid_cells"],4)
        cell=next(c for c in matrix["cells"] if c["isl"]==2048 and c["osl"]==512)
        self.assertEqual(cell["count"],2)
        self.assertEqual(cell["median_of_published_values"],72)
        self.assertEqual(cell["observations"][0]["source_url"],"https://example.org/d")

    def test_sparse_grid_is_not_filled(self):
        rows=[row("a",512,128,100),row("b",512,512,90),row("c",2048,128,80)]
        matrix=build_report({"records":rows})["matrices"][0]
        self.assertEqual(matrix["expected_grid_cells"],4)
        self.assertEqual(matrix["observed_grid_cells"],3)
        self.assertAlmostEqual(matrix["coverage_fraction"],0.75)
        self.assertNotIn((2048,512),{(c["isl"],c["osl"]) for c in matrix["cells"]})

    def test_requires_two_values_on_both_axes(self):
        rows=[row("a",512,128,100),row("b",512,512,90),row("c",512,1024,80)]
        self.assertEqual(build_report({"records":rows})["matrices"],[])

    def test_other_workload_and_system_context_must_match(self):
        a=row("a",512,128,100)
        b=row("b",2048,512,80)
        b["workload"]["concurrency"]=32
        self.assertEqual(build_report({"records":[a,b]})["matrices"],[])
        b=row("b",2048,512,80)
        b["system"]["physical_decode_gpus"]=16
        self.assertEqual(build_report({"records":[a,b]})["matrices"],[])

    def test_recipe_and_configuration_must_match(self):
        a=row("a",512,128,100)
        b=row("b",2048,512,80)
        b["software"]["recipe_fingerprint"]="different"
        self.assertEqual(build_report({"records":[a,b]})["matrices"],[])
        b=row("b",2048,512,80)
        b["configuration"]["decode_tp"]=4
        self.assertEqual(build_report({"records":[a,b]})["matrices"],[])

    def test_invalid_metric_does_not_remove_valid_observation(self):
        a=row("a",512,128,100)
        b=row("b",2048,512,80)
        b["normalized_metrics"]["output_throughput_per_gpu"]["unit"]="tok/s"
        self.assertEqual(build_report({"records":[a,b]})["matrices"],[])

    def test_deterministic_and_source_linked(self):
        rows=[row("a",512,128,100),row("b",512,512,90),row("c",2048,128,80)]
        self.assertEqual(build_report({"records":rows}),build_report({"records":rows[::-1]}))
        matrix=build_report({"records":rows})["matrices"][0]
        self.assertTrue(all(o["source_url"] for cell in matrix["cells"] for o in cell["observations"]))


if __name__ == "__main__":
    unittest.main()
