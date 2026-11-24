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


if __name__ == "__main__":
    unittest.main()
