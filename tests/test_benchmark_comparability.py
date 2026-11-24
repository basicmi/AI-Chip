import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from assess_benchmark_comparability import build_report


def record(record_id, accelerator, framework="vllm"):
    return {
        "id": record_id,
        "source_id": "public-suite",
        "source_class": "third_party_public_benchmark",
        "evidence_level": "third_party_public_benchmark",
        "benchmark_suite": "Inference Suite",
        "benchmark_version": "2.1",
        "model": "Model A",
        "scenario": "online",
        "division": "closed",
        "availability": "available",
        "accuracy_text": "Reference accuracy passed",
        "weight_data_types": "FP8",
        "inferred": False,
        "errors": 0,
        "workload": {"input_tokens": 1024, "output_tokens": 256, "concurrency": 64},
        "configuration": {"batching": "continuous", "metric_window": "steady_state"},
        "system_type": "datacenter",
        "system_name": accelerator + " server",
        "accelerator_vendor": accelerator,
        "platform_id": accelerator.lower() + "-platform",
        "product_id": accelerator.lower() + "-gpu",
        "system": {
            "nodes": 1,
            "total_accelerators": 8,
            "accelerators_per_node": 8,
            "host_processor_model": "CPU X",
            "accelerator_model": accelerator,
        },
        "software": {"framework": framework, "framework_version": "1.0", "runtime": "runtime-x"},
        "normalized_metrics": {
            "output_throughput": {
                "value": 1000 if accelerator == "GPU A" else 1200,
                "unit": "token/s",
                "direction": "higher",
                "label": "Output throughput",
                "source_metric": "output_tput",
                "family": "throughput",
            }
        },
        "source_url": "https://example.org/results/" + record_id,
    }


class BenchmarkComparabilityTests(unittest.TestCase):
    def test_exact_protocol_and_software_yield_direct_comparison(self):
        report = build_report({"records": [record("a", "GPU A"), record("b", "GPU B")]})
        self.assertEqual(report["summary"]["comparison_groups"], 1)
        group = report["groups"][0]
        self.assertEqual(group["status"], "directly_comparable")
        self.assertEqual(group["pair_count"], 1)
        self.assertEqual(group["metric"]["unit"], "token/s")

    def test_software_difference_downgrades_to_conditional(self):
        report = build_report({
            "records": [record("a", "GPU A"), record("b", "GPU B", framework="TensorRT-LLM")]
        })
        self.assertEqual(report["summary"]["conditional_comparison_pairs"], 1)
        self.assertEqual(report["groups"][0]["status"], "conditionally_comparable")

    def test_workload_difference_does_not_form_comparison_group(self):
        second = record("b", "GPU B")
        second["workload"]["concurrency"] = 128
        report = build_report({"records": [record("a", "GPU A"), second]})
        self.assertEqual(report["summary"]["comparison_groups"], 0)

    def test_missing_system_boundary_is_excluded(self):
        second = record("b", "GPU B")
        second["system"]["total_accelerators"] = None
        report = build_report({"records": [record("a", "GPU A"), second]})
        self.assertEqual(report["summary"]["comparison_groups"], 0)
        self.assertIn("missing_or_invalid_system_total_accelerators",
                      report["excluded_records"][0]["reasons"])

    def test_inferred_result_is_excluded(self):
        second = record("b", "GPU B")
        second["inferred"] = True
        report = build_report({"records": [record("a", "GPU A"), second]})
        self.assertEqual(report["summary"]["comparison_groups"], 0)
        self.assertIn("result_is_inferred_or_inference_status_unknown",
                      report["excluded_records"][0]["reasons"])

    def test_same_accelerator_identity_does_not_form_cross_hardware_group(self):
        report = build_report({"records": [record("a", "GPU A"), record("b", "GPU A")]})
        self.assertEqual(report["summary"]["comparison_groups"], 0)

    def test_different_benchmark_versions_do_not_mix(self):
        second = record("b", "GPU B")
        second["benchmark_version"] = "2.2"
        report = build_report({"records": [record("a", "GPU A"), second]})
        self.assertEqual(report["summary"]["comparison_groups"], 0)

    def test_unknown_metric_unit_is_not_compared(self):
        second = record("b", "GPU B")
        second["normalized_metrics"]["output_throughput"]["unit"] = None
        report = build_report({"records": [record("a", "GPU A"), second]})
        self.assertEqual(report["summary"]["comparison_groups"], 0)

    def test_mlperf_profile_uses_official_submission_context(self):
        def mlperf(rid, accelerator):
            item = {
                "id": rid, "source_id": "mlperf-inference-v6.1",
                "source_class": "standardized_public_submission",
                "evidence_level": "mlcommons_published_submission",
                "benchmark_suite": "MLPerf Inference", "benchmark_version": "v6.1",
                "model": "resnet", "scenario": "Server", "division": "closed",
                "availability": "available", "accuracy_text": "99% target",
                "weight_data_types": "INT8", "inferred": False, "errors": 0,
                "result_value": 1000 if accelerator == "GPU A" else 1200,
                "result_unit": "queries/s",
                "system_type": "datacenter", "system_name": accelerator,
                "product_id": accelerator.lower(), "accelerator_vendor": accelerator,
                "system": {"nodes": 1, "total_accelerators": 8, "accelerators_per_node": 8,
                           "host_processor_model": "CPU X", "accelerator_model": accelerator},
                "software": {"framework": "LoadGen 1.0", "operating_system": "Linux"},
            }
            return item
        report = build_report({"records": [mlperf("a", "GPU A"), mlperf("b", "GPU B")]})
        self.assertEqual(report["summary"]["comparison_groups"], 1)
        self.assertEqual(report["groups"][0]["status"], "directly_comparable")

    def test_inferencex_profile_uses_published_workload_and_gpu_roles(self):
        def inferencex(rid, accelerator):
            item = record(rid, accelerator)
            item.update({
                "source_id": "inferencex",
                "benchmark_suite": "SemiAnalysis InferenceX",
                "benchmark_version": None,
                "model": "dsr1",
                "model_display_name": "DeepSeek-R1-0528",
                "scenario": "single_turn",
                "division": "third_party",
                "availability": "published",
                "accuracy_text": "",
                "weight_data_types": "FP8",
                "result_value": None,
                "result_unit": "",
                "workload": {
                    "benchmark_type": "single_turn", "isl": 1024, "osl": 1024,
                    "concurrency": 32, "precision": "FP8",
                    "speculative_method": "none", "disaggregated": False,
                },
                "configuration": {"decode_tp": 8},
                "system": {
                    "accelerator_model": accelerator,
                    "physical_prefill_gpus": 0, "physical_decode_gpus": 8,
                    "is_multinode": False, "workers": [],
                },
                "software": {"framework": "vllm", "operating_system": ""},
            })
            return item
        report = build_report({
            "records": [inferencex("a", "GPU A"), inferencex("b", "GPU B")]
        })
        self.assertEqual(report["summary"]["comparison_groups"], 1)
        self.assertEqual(report["groups"][0]["status"], "directly_comparable")
        self.assertEqual(report["groups"][0]["protocol"]["benchmark_version"], None)


if __name__ == "__main__":
    unittest.main()
