import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from import_benchmark_results import (
    import_inferencex,
    merge_inferencex_records,
    normalize_inferencex_record,
    normalize_mlperf_record,
    summarize,
    hardware_identity,
    main as import_main,
)
from validate_benchmark_results import validate_database


class HardwareIdentityTests(unittest.TestCase):
    def test_first_wave_product_links_are_exact(self):
        self.assertEqual(hardware_identity("AMD Instinct MI355X 288GB HBM3e"),
                         ("AMD", "amd-gpu", "mi355x"))
        self.assertEqual(hardware_identity("NVIDIA GB200 NVL72"),
                         ("NVIDIA", "nvidia-gpu", "gb200-nvl72"))
        self.assertEqual(hardware_identity("NVIDIA GB200"),
                         ("NVIDIA", "nvidia-gpu", None))
        self.assertEqual(hardware_identity("B200-SXM-180GB"),
                         ("NVIDIA", "nvidia-gpu", "b200-sxm"))
        self.assertEqual(hardware_identity("B200"),
                         ("NVIDIA", "nvidia-gpu", None))
        self.assertEqual(hardware_identity("Vera Rubin NVL72"),
                         ("NVIDIA", "nvidia-gpu", "vera-rubin-nvl72"))
        self.assertEqual(hardware_identity("h200_sxm"),
                         ("NVIDIA", "nvidia-gpu", None))
        self.assertEqual(hardware_identity("mi355x"),
                         ("AMD", "amd-gpu", "mi355x"))
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

    def test_inferencex_metric_units_and_power_validation_are_explicit(self):
        base = {
            "id": 421, "hardware": "h200_sxm", "framework": "vllm",
            "model": "dsr1", "precision": "fp8", "benchmark_type": "single_turn",
            "isl": 1024, "osl": 1024, "conc": 32, "num_prefill_gpu": 0,
            "num_decode_gpu": 8,
            "metrics": {
                "output_tput_per_gpu": 1000,
                "median_intvty": 42.5,
                "p99_itl": 0.021,
                "avg_power_w": 680.0,
            },
            "date": "2026-11-01", "run_url": "https://github.com/example/run/1",
            "workers": [{"role": "decode", "worker_idx": 0, "num_gpus": 8, "avg_power_w": 680.0}],
        }
        endpoint = "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1-0528"
        result = normalize_inferencex_record(base, endpoint, model_display_name="DeepSeek-R1-0528")
        self.assertEqual(result["source_class"], "third_party_public_benchmark")
        self.assertIsNone(result["benchmark_version"])
        self.assertEqual(result["model"], "dsr1")
        self.assertEqual(result["model_display_name"], "DeepSeek-R1-0528")
        self.assertEqual(result["metrics"]["output_tput_per_gpu"], 1000)
        self.assertEqual(result["normalized_metrics"]["median_interactivity"]["unit"], "tok/s/user")
        self.assertEqual(result["normalized_metrics"]["median_interactivity"]["direction"], "higher")
        self.assertEqual(result["normalized_metrics"]["p99_itl"]["unit"], "s")
        self.assertNotIn("mean_gpu_power_per_gpu", result["normalized_metrics"])
        self.assertFalse(result["power_measurement_valid"])
        self.assertEqual(result["power_measurement_status"], "unreported")
        self.assertEqual(result["cpu_power_measurement_status"], "not_present")
        self.assertFalse(result["power_metrics_available"])
        self.assertEqual(len(result["system"]["workers"]), 1)

        base["metrics"].update({"power_valid": 1, "power_metric_schema_version": 2})
        validated = normalize_inferencex_record(base, endpoint, model_display_name="DeepSeek-R1-0528")
        self.assertTrue(validated["power_measurement_valid"])
        self.assertEqual(validated["power_measurement_status"], "valid")
        self.assertTrue(validated["power_metrics_available"])
        self.assertEqual(validated["normalized_metrics"]["mean_gpu_power_per_gpu"]["unit"], "W/GPU")

        base["metrics"].pop("avg_power_w")
        valid_without_power_value = normalize_inferencex_record(base, endpoint, model_display_name="DeepSeek-R1-0528")
        self.assertTrue(valid_without_power_value["power_measurement_valid"])
        self.assertFalse(valid_without_power_value["power_metrics_available"])

        cpu_only = dict(base)
        cpu_only["metrics"] = {"cpu_power_valid": 1, "avg_cpu_socket_power_w": 240.0, "total_cpu_energy_j": 9000.0}
        cpu_result = normalize_inferencex_record(cpu_only, endpoint, model_display_name="DeepSeek-R1-0528")
        self.assertFalse(cpu_result["power_measurement_valid"])
        self.assertTrue(cpu_result["cpu_power_measurement_valid"])
        self.assertEqual(cpu_result["power_measurement_status"], "unreported")
        self.assertEqual(cpu_result["cpu_power_measurement_status"], "valid")
        self.assertFalse(cpu_result["gpu_power_metrics_available"])
        self.assertTrue(cpu_result["cpu_power_metrics_available"])
        self.assertTrue(cpu_result["power_metrics_available"])
        self.assertEqual(cpu_result["normalized_metrics"]["mean_cpu_socket_power"]["unit"], "W/socket")

    def test_scoped_inferencex_refresh_preserves_other_models(self):
        existing = [
            {"id": "old-r1", "source_id": "inferencex", "model": "dsr1", "model_display_name": "DeepSeek-R1-0528"},
            {"id": "old-r1-legacy", "source_id": "inferencex", "model": "dsr1",
             "source_url": "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1-0528"},
            {"id": "old-qwen", "source_id": "inferencex", "model": "qwen3", "model_display_name": "Qwen3"},
            {"id": "mlperf-1", "source_id": "mlperf-inference-v6.1", "model": "resnet"},
        ]
        imported = [
            {"id": "new-r1", "source_id": "inferencex", "model": "dsr1", "model_display_name": "DeepSeek-R1-0528"},
        ]
        merged = merge_inferencex_records(existing, imported, ["DeepSeek-R1-0528"])
        self.assertEqual({row["id"] for row in merged}, {"new-r1", "old-qwen", "mlperf-1"})

        full_refresh = merge_inferencex_records(existing, imported)
        self.assertEqual({row["id"] for row in full_refresh}, {"new-r1", "mlperf-1"})

    def test_inferencex_empty_availability_is_not_a_valid_empty_snapshot(self):
        with mock.patch("import_benchmark_results.fetch_json", return_value=[]):
            source, records, warnings = import_inferencex()
        self.assertEqual(source["record_count"], 0)
        self.assertEqual(records, [])
        self.assertTrue(any("availability endpoint returned no models" in warning for warning in warnings))


class ImportSafetyTests(unittest.TestCase):
    def test_partial_inferencex_refresh_does_not_overwrite_existing_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "benchmark-results.json"
            original = {"sentinel": "keep-existing-snapshot"}
            output.write_text(json.dumps(original), encoding="utf-8")
            with mock.patch.object(sys, "argv", [
                "import_benchmark_results.py", "--source", "inferencex",
                "--output", str(output)
            ]), mock.patch(
                "import_benchmark_results.import_inferencex",
                return_value=(
                    {"id": "inferencex", "record_count": 0},
                    [],
                    ["model-a: HTTP 503"],
                ),
            ):
                self.assertEqual(import_main(), 2)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), original)


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
            "design_power_watts": None, "system": {"workers": []}, "software": {}, "workload": {},
            "configuration": {}, "metrics": {"power_valid": 0, "power_metric_schema_version": 2},
            "model_display_name": "DeepSeek-R1-0528", "power_measurement_valid": False,
            "power_measurement_status": "failed",
            "cpu_power_measurement_valid": False, "cpu_power_measurement_status": "not_present",
            "gpu_power_metrics_available": False,
            "cpu_power_metrics_available": False, "normalized_metrics": {},
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
