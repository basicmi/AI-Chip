import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from import_benchmark_results import (
    normalize_inferencex_record,
    normalize_mlperf_record,
    summarize,
    hardware_identity,
)
from validate_benchmark_results import validate_database


class HardwareIdentityTests(unittest.TestCase):
    def test_first_wave_product_links_are_exact(self):
        self.assertEqual(hardware_identity("AMD Instinct MI355X 288GB HBM3e"),
                         ("AMD", "amd-gpu", "mi355x"))
        self.assertEqual(hardware_identity("NVIDIA GB200"),
                         ("NVIDIA", "nvidia-gpu", "gb200-nvl72"))
        self.assertEqual(hardware_identity("Intel Gaudi 3"),
                         ("Intel", "intel-gaudi", "gaudi3"))
        self.assertEqual(hardware_identity("Cerebras WSE-2"),
                         ("Cerebras", "cerebras-wse", "wse2"))
        self.assertEqual(hardware_identity("Cerebras CS-3"),
                         ("Cerebras", "cerebras-wse", None))
        self.assertEqual(hardware_identity("Unknown accelerator"), (None, None, None))


class NormalizationTests(unittest.TestCase):
    def test_mlperf_preserves_submission_context_and_inferred_flag(self):
        row = {
            "Organization": "AMD",
            "Availability": "available",
            "Division": "closed",
            "SystemType": "datacenter",
            "SystemName": "8xMI355X",
            "Model": "deepseek-r1",
            "Scenario": "Server",
            "Result": 123.5,
            "Units": "Tokens/s",
            "Accuracy": "99% of reference",
            "accelerator_model_name": "AMD Instinct MI355X 288GB HBM3e",
            "accelerators_per_node": 8,
            "total_accelerators": 8,
            "number_of_nodes": 1,
            "framework": "PyTorch + ROCm",
            "operating_system": "Ubuntu",
            "inferred": 1,
            "has_power": False,
            "Location": "./closed/AMD/results/example",
            "version": "v6.1",
        }
        result = normalize_mlperf_record("7", row)
        self.assertEqual(result["product_id"], "mi355x")
        self.assertEqual(result["platform_id"], "amd-gpu")
        self.assertTrue(result["inferred"])
        self.assertFalse(result["power_metrics_available"])
        self.assertEqual(result["result_value"], 123.5)
        self.assertIn("/closed/AMD/results/example", result["source_url"])

    def test_inferencex_power_requires_validated_schema_v2(self):
        base = {
            "id": 421, "hardware": "h200_sxm", "framework": "vllm",
            "model": "dsr1", "precision": "fp8", "benchmark_type": "single_turn",
            "isl": 1024, "osl": 1024, "conc": 32, "num_prefill_gpu": 0,
            "num_decode_gpu": 8, "metrics": {"output_tput_per_gpu": 1000},
            "date": "2026-11-01", "run_url": "https://github.com/example/run/1",
        }
        endpoint = "https://inferencex.semianalysis.com/api/v1/benchmarks?model=dsr1"
        result = normalize_inferencex_record(base, endpoint)
        self.assertEqual(result["source_class"], "third_party_public_benchmark")
        self.assertEqual(result["metrics"]["output_tput_per_gpu"], 1000)
        self.assertFalse(result["power_metrics_available"])
        base["metrics"].update({"power_valid": 1, "power_metric_schema_version": 2})
        validated = normalize_inferencex_record(base, endpoint)
        self.assertTrue(validated["power_metrics_available"])


class RegistryValidationTests(unittest.TestCase):
    def test_summary_counts_are_source_specific(self):
        records = [
            {"source_id": "a", "availability": "available", "division": "closed",
             "system_type": "datacenter", "inferred": False, "power_metrics_available": False,
             "submitter": "Vendor A", "model": "Model A"},
            {"source_id": "b", "availability": "published", "division": "third_party",
             "system_type": "datacenter", "inferred": False, "power_metrics_available": True,
             "submitter": "Publisher", "model": "Model A"},
        ]
        result = summarize(records)
        self.assertEqual(result["total_records"], 2)
        self.assertEqual(result["by_source"], {"a": 1, "b": 1})
        self.assertEqual(result["power_records"], 1)

    def test_validator_rejects_unknown_source_and_bad_power_claim(self):
        source = {
            "id": "inferencex", "source_class": "third_party_public_benchmark",
            "record_count": 1, "results_url": "https://example.com",
            "dataset_url": "https://example.com/api",
        }
        row = {
            "id": "inferencex-1", "source_id": "inferencex",
            "source_class": "third_party_public_benchmark",
            "evidence_level": "publisher_published_observation",
            "benchmark_suite": "InferenceX", "benchmark_version": "public-api-v1",
            "publication_date": "2026-11-01", "submitter": "SemiAnalysis",
            "accelerator_vendor": "NVIDIA", "platform_id": None, "product_id": None,
            "system_type": "datacenter", "system_name": "h200_sxm",
            "division": "third_party", "availability": "published", "model": "dsr1",
            "scenario": "single_turn", "result_value": None, "result_unit": "",
            "accuracy_text": "", "inferred": False, "power_metrics_available": True,
            "design_power_watts": None, "system": {}, "software": {}, "workload": {},
            "configuration": {}, "metrics": {"power_valid": 0, "power_metric_schema_version": 2},
            "notes": "", "compliance": "publisher_published", "errors": 0,
            "weight_data_types": "fp8", "source_record_key": "1", "source_location": "",
            "source_url": "https://example.com/api", "detail_url": None,
            "dataset_url": "https://example.com/api", "release_url": "https://example.com",
        }
        db = {
            "schema_version": "1.0", "sources": [source], "records": [row],
            "summary": summarize([row]),
        }
        errors = validate_database(db)
        self.assertTrue(any("strict power record" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
