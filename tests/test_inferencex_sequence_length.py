import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_inferencex_sequence_length import build_report


def row(rid, isl=1024, osl=256, concurrency=16, metrics=None):
    default_metrics = {
        "output_throughput_per_gpu": {"value": 100, "unit": "tok/s/GPU", "family": "throughput", "direction": "higher"},
        "median_ttft": {"value": 1.0, "unit": "s", "family": "latency", "direction": "lower"},
        "median_tpot": {"value": 0.02, "unit": "s", "family": "latency", "direction": "lower"},
    }
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
                     "concurrency": concurrency, "precision": "FP8",
                     "speculative_method": "none", "disaggregated": False},
        "normalized_metrics": metrics if metrics is not None else default_metrics,
        "source_url": "https://example.org/" + rid,
    }


class SequenceLengthTests(unittest.TestCase):
    def test_isl_sweep_holds_osl_and_other_context_fixed(self):
        a=row("a",isl=1024);b=row("b",isl=4096)
        b["normalized_metrics"]["median_ttft"]["value"]=2.0
        report=build_report({"records":[a,b]})
        ttft=next(s for s in report["sweeps"] if s["dimension"]=="isl" and s["metric"]=="median_ttft")
        self.assertEqual([p["sequence_length"] for p in ttft["points"]],[1024,4096])
        self.assertEqual(ttft["endpoint_change"]["relative_change_percent"],100.0)
        self.assertEqual(len(ttft["points"][0]["observations"]),1)

    def test_osl_sweep_holds_isl_and_other_context_fixed(self):
        a=row("a",osl=128);b=row("b",osl=2048)
        b["normalized_metrics"]["median_tpot"]["value"]=0.03
        report=build_report({"records":[a,b]})
        tpot=next(s for s in report["sweeps"] if s["dimension"]=="osl" and s["metric"]=="median_tpot")
        self.assertEqual([p["sequence_length"] for p in tpot["points"]],[128,2048])
        self.assertAlmostEqual(tpot["endpoint_change"]["relative_change_percent"],50.0)

    def test_other_sequence_dimension_and_concurrency_must_match(self):
        cases=[("osl",2048),("concurrency",32)]
        for field,value in cases:
            with self.subTest(field=field):
                a=row("a");b=row("b",isl=4096)
                b["workload"][field]=value
                self.assertFalse(build_report({"records":[a,b]})["sweeps"])

    def test_system_and_recipe_must_match(self):
        a=row("a");b=row("b",isl=4096)
        b["system"]["physical_decode_gpus"]=16
        self.assertFalse(build_report({"records":[a,b]})["sweeps"])
        b=row("b",isl=4096);b["software"]["recipe_fingerprint"]="different"
        self.assertFalse(build_report({"records":[a,b]})["sweeps"])

    def test_invalid_lengths_and_metric_units_are_excluded(self):
        b=row("b",isl=4096);b["normalized_metrics"]["median_ttft"]["unit"]="ms"
        self.assertFalse(build_report({"records":[row("a"),b]})["sweeps"])
        b=row("b",isl=True)
        self.assertFalse(build_report({"records":[row("a"),b]})["sweeps"])

    def test_deterministic_and_source_linked(self):
        a=row("a",isl=1024);b=row("b",isl=4096)
        one=build_report({"records":[a,b]})
        two=build_report({"records":[b,a]})
        self.assertEqual(one,two)
        sweep=next(s for s in one["sweeps"] if s["dimension"]=="isl")
        self.assertTrue(all(o["source_url"] for p in sweep["points"] for o in p["observations"]))


if __name__ == "__main__":
    unittest.main()
