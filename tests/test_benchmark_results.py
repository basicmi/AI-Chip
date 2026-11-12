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
    map_inferencex_display_models,
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

    def test_inferencex_energy_metrics_require_valid_gpu_power_schema(self):
        endpoint = "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1-0528"
        base = {
            "id": 422, "hardware": "h200_sxm", "framework": "vllm",
            "model": "dsr1", "precision": "fp8", "benchmark_type": "single_turn",
            "isl": 1024, "osl": 1024, "conc": 32, "num_prefill_gpu": 0,
            "num_decode_gpu": 8,
            "metrics": {
                "joules_per_output_token": 0.34, "joules_per_total_token": 0.12,
                "joules_per_successful_query": 15.0, "prefill_joules_per_input_token": 0.04,
                "decode_joules_per_output_token": 0.28, "avg_power_w": 680.0,
                "avg_total_gpu_power_w": 5440.0,
            },
        }
        unvalidated = normalize_inferencex_record(base, endpoint)
        self.assertFalse(unvalidated["power_measurement_valid"])
        self.assertNotIn("energy_per_output_token", unvalidated["normalized_metrics"])
        self.assertNotIn("energy_per_total_token", unvalidated["normalized_metrics"])

        base["metrics"].update({"power_valid": 1, "power_metric_schema_version": 2})
        validated = normalize_inferencex_record(base, endpoint)
        self.assertTrue(validated["power_measurement_valid"])
        self.assertTrue(validated["gpu_power_metrics_available"])
        self.assertEqual(validated["normalized_metrics"]["energy_per_output_token"]["value"], 0.34)
        self.assertEqual(validated["normalized_metrics"]["energy_per_output_token"]["unit"], "J/output token")
        self.assertEqual(validated["normalized_metrics"]["energy_per_output_token"]["direction"], "lower")
        self.assertEqual(validated["normalized_metrics"]["energy_per_total_token"]["unit"], "J/total token")
        self.assertEqual(validated["normalized_metrics"]["energy_per_successful_query"]["unit"], "J/query")
        self.assertEqual(validated["normalized_metrics"]["prefill_energy_per_input_token"]["unit"], "J/input token")
        self.assertEqual(validated["normalized_metrics"]["decode_energy_per_output_token"]["unit"], "J/output token")
        self.assertEqual(validated["normalized_metrics"]["mean_total_gpu_power"]["unit"], "W")

        base["metrics"]["power_valid"] = 0
        failed = normalize_inferencex_record(base, endpoint)
        self.assertFalse(failed["power_measurement_valid"])
        self.assertFalse(failed["gpu_power_metrics_available"])
        self.assertNotIn("energy_per_output_token", failed["normalized_metrics"])

    def test_inferencex_preserves_unknown_serving_and_topology_flags(self):
        endpoint = "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1-0528"
        base = {
            "id": 777, "model": "dsr1", "hardware": "h200_sxm",
            "framework": "vllm", "precision": "fp8", "benchmark_type": "single_turn",
            "isl": 1024, "osl": 1024, "conc": 32, "metrics": {},
        }
        unknown = normalize_inferencex_record(base, endpoint, model_display_name="DeepSeek-R1-0528")
        self.assertIsNone(unknown["system"]["is_multinode"])
        self.assertIsNone(unknown["workload"]["disaggregated"])

        explicit_single = normalize_inferencex_record(
            {**base, "is_multinode": False, "disagg": False},
            endpoint, model_display_name="DeepSeek-R1-0528",
        )
        self.assertIs(explicit_single["system"]["is_multinode"], False)
        self.assertIs(explicit_single["workload"]["disaggregated"], False)

        explicit_multi = normalize_inferencex_record(
            {**base, "is_multinode": True, "disagg": True},
            endpoint, model_display_name="DeepSeek-R1-0528",
        )
        self.assertIs(explicit_multi["system"]["is_multinode"], True)
        self.assertIs(explicit_multi["workload"]["disaggregated"], True)

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

    def test_availability_raw_keys_map_to_benchmarks_display_names(self):
        availability = [
            {"model": "dsr1", "isl": 1024, "osl": 1024},
            {"model": "dsv4", "isl": 8192, "osl": 1024},
        ]
        options = {
            "models": [
                {"name": "DeepSeek-R1-0528", "dbKeys": ["dsr1"]},
                {"name": "DeepSeek-V4-Pro", "dbKeys": ["dsv4"]},
                {"name": "Not yet available", "dbKeys": ["future-model"]},
            ]
        }
        mapped, unmapped = map_inferencex_display_models(availability, options)
        self.assertEqual(mapped, {
            "DeepSeek-R1-0528": ["dsr1"],
            "DeepSeek-V4-Pro": ["dsv4"],
        })
        self.assertEqual(unmapped, [])

        row_r1 = {
            "id": 901, "model": "dsr1", "hardware": "h200_sxm", "framework": "vllm",
            "precision": "fp8", "benchmark_type": "single_turn", "isl": 1024,
            "osl": 1024, "conc": 32, "metrics": {"output_tput_per_gpu": 100.0},
            "date": "2026-11-09", "run_url": "https://github.com/example/run/901",
        }
        row_v4 = {
            "id": 902, "model": "dsv4", "hardware": "gb200_nvl72", "framework": "sglang",
            "precision": "fp8", "benchmark_type": "single_turn", "isl": 8192,
            "osl": 1024, "conc": 16, "metrics": {"output_tput_per_gpu": 200.0},
            "date": "2026-11-09", "run_url": "https://github.com/example/run/902",
        }
        responses = {
            "https://inferencex.semianalysis.com/api/v1/availability": availability,
            "https://inferencex.semianalysis.com/api/v1/views/options": options,
            "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1-0528": [row_r1],
            "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-V4-Pro": [row_v4],
        }

        def fake_fetch(url):
            if url not in responses:
                raise AssertionError("Unexpected InferenceX API request: " + url)
            return responses[url]

        with mock.patch("import_benchmark_results.fetch_json", side_effect=fake_fetch) as fetch:
            source, records, warnings = import_inferencex()

        self.assertEqual(warnings, [])
        self.assertEqual(source["availability_model_keys"], ["dsr1", "dsv4"])
        self.assertEqual(source["selected_models"], ["DeepSeek-R1-0528", "DeepSeek-V4-Pro"])
        self.assertEqual(source["model_db_keys"], {
            "DeepSeek-R1-0528": ["dsr1"],
            "DeepSeek-V4-Pro": ["dsv4"],
        })
        self.assertEqual(source["record_count"], 2)
        self.assertTrue(source["retrieved_at"].endswith("+00:00"))
        self.assertEqual(
            {record["model_display_name"] for record in records},
            {"DeepSeek-R1-0528", "DeepSeek-V4-Pro"},
        )
        self.assertEqual(
            {record["model"] for record in records},
            {"dsr1", "dsv4"},
        )
        requested_urls = [call.args[0] for call in fetch.call_args_list]
        self.assertIn(
            "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1-0528",
            requested_urls,
        )
        self.assertIn(
            "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-V4-Pro",
            requested_urls,
        )
        self.assertNotIn(
            "https://inferencex.semianalysis.com/api/v1/benchmarks?model=dsr1",
            requested_urls,
        )

    def test_unmapped_availability_key_fails_closed(self):
        availability = [{"model": "dsr1"}, {"model": "unmapped-key"}]
        options = {"models": [{"name": "DeepSeek-R1-0528", "dbKeys": ["dsr1"]}]}
        with mock.patch(
            "import_benchmark_results.fetch_json",
            side_effect=[availability, options, [{
                "id": 903, "model": "dsr1", "hardware": "h200_sxm",
                "metrics": {}, "date": "2026-11-09",
            }]],
        ):
            source, records, warnings = import_inferencex()
        self.assertEqual(len(records), 1)
        self.assertEqual(source["unmapped_availability_model_keys"], ["unmapped-key"])
        self.assertTrue(any("unmapped-key" in warning for warning in warnings))

    def test_duplicate_display_aliases_are_deduplicated_and_scoped_refresh_removes_raw_key(self):
        availability = [{"model": "dsr1"}]
        options = {
            "models": [
                {"name": "DeepSeek-R1-0528", "dbKeys": ["dsr1"]},
                {"name": "DeepSeek-R1", "dbKeys": ["dsr1"]},
            ]
        }
        row = {
            "id": 904, "model": "dsr1", "hardware": "h200_sxm",
            "metrics": {"output_tput_per_gpu": 100.0}, "date": "2026-11-09",
        }
        responses = {
            "https://inferencex.semianalysis.com/api/v1/availability": availability,
            "https://inferencex.semianalysis.com/api/v1/views/options": options,
            "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1-0528": [row],
            "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1": [row],
        }
        with mock.patch(
            "import_benchmark_results.fetch_json",
            side_effect=lambda url: responses[url],
        ):
            source, imported, warnings = import_inferencex()
        self.assertEqual(warnings, [])
        self.assertEqual(len(imported), 1)
        self.assertEqual(source["rows_by_model"], {
            "DeepSeek-R1-0528": 1,
            "DeepSeek-R1": 1,
        })

        existing = [{
            "id": "old-alias-row", "source_id": "inferencex", "model": "dsr1",
            "model_display_name": "DeepSeek-R1-0528",
            "source_url": "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1-0528",
        }]
        refreshed = merge_inferencex_records(
            existing, imported, ["DeepSeek-R1"],
            selected_raw_model_keys=["dsr1"],
        )
        self.assertEqual(len(refreshed), 1)
        self.assertEqual(refreshed[0]["id"], "inferencex-904")

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
    @staticmethod
    def valid_hardware_evidence():
        return {
            "schema_version": "1.0",
            "collector": {"name": "Nsight Systems", "version": "2026.3", "type": "profiler"},
            "system_scope": {
                "scope_type": "per_gpu", "device_count": 8,
                "device_model": "NVIDIA H200 SXM", "topology": "8-GPU NVLink node",
            },
            "sampling": {
                "started_at": "2026-11-12T10:00:00Z",
                "ended_at": "2026-11-12T10:01:00Z",
                "sample_interval_ms": 1000, "sample_count": 60,
            },
            "provenance": {
                "source_type": "profiler_export",
                "source_url": "https://example.com/run/hardware-counters",
                "collected_at": "2026-11-12T10:02:00Z",
                "artifact_sha256": "a" * 64,
            },
            "metrics": [
                {"metric_id": "sm_active_pct", "value": 78.0, "unit": "%",
                 "measurement_kind": "telemetry", "aggregation": "mean",
                 "scope": "per_gpu", "source_name": "DCGM_FI_PROF_SM_UTIL_RATIO",
                 "mapping_quality": "direct", "mapping_note": "SM active-cycle ratio."},
                {"metric_id": "theoretical_peak_flops", "value": 1.98e15, "unit": "FLOP/s",
                 "measurement_kind": "telemetry", "aggregation": "max",
                 "scope": "per_gpu", "source_name": "device_spec_fp8_peak", "precision": "FP8", "sparsity": "dense"},
                {"metric_id": "compute_flop_count", "value": 7.2e16, "unit": "FLOP",
                 "measurement_kind": "hardware_counter", "aggregation": "sum",
                 "scope": "per_gpu", "source_name": "flop_count_sp",
                 "precision": "FP8", "sparsity": "dense"},
                {"metric_id": "achieved_flops", "value": 1.2e15, "unit": "FLOP/s",
                 "measurement_kind": "derived", "aggregation": "mean",
                 "scope": "per_gpu", "source_name": "derived_achieved_flops",
                 "formula": "compute_flop_count / measured_window_seconds",
                 "input_metric_ids": ["compute_flop_count"], "precision": "FP8", "sparsity": "dense"},
                {"metric_id": "dram_bandwidth_bytes_per_s", "value": 2.2e12, "unit": "byte/s",
                 "measurement_kind": "hardware_counter", "aggregation": "mean",
                 "scope": "per_gpu", "source_name": "dram__bytes.sum / duration"},
                {"metric_id": "dram_peak_bandwidth_bytes_per_s", "value": 3.35e12, "unit": "byte/s",
                 "measurement_kind": "telemetry", "aggregation": "max",
                 "scope": "per_gpu", "source_name": "device_spec_hbm_peak"},
                {"metric_id": "kv_cache_used_bytes", "value": 40e9, "unit": "byte",
                 "measurement_kind": "telemetry", "aggregation": "mean",
                 "scope": "per_gpu", "source_name": "runtime_kv_cache_used_bytes"},
                {"metric_id": "kv_cache_capacity_bytes", "value": 70e9, "unit": "byte",
                 "measurement_kind": "telemetry", "aggregation": "max",
                 "scope": "per_gpu", "source_name": "runtime_kv_cache_capacity_bytes"},
                {"metric_id": "nvlink_tx_bytes", "value": 9e12, "unit": "byte",
                 "measurement_kind": "hardware_counter", "aggregation": "sum",
                 "scope": "per_link", "source_name": "nvlink_tx_bytes", "link_type": "nvlink",
                 "entity_id": "nvlink:L0"},
                {"metric_id": "nvlink_rx_bytes", "value": 8e12, "unit": "byte",
                 "measurement_kind": "hardware_counter", "aggregation": "sum",
                 "scope": "per_link", "source_name": "nvlink_rx_bytes", "link_type": "nvlink",
                 "entity_id": "nvlink:L0"},
                {"metric_id": "link_bandwidth_bytes_per_s", "value": 7.2e11, "unit": "byte/s",
                 "measurement_kind": "telemetry", "aggregation": "mean",
                 "scope": "per_link", "source_name": "nvlink_link_bandwidth", "link_type": "nvlink",
                 "entity_id": "nvlink:L0", "directionality": "bidirectional"},
                {"metric_id": "link_peak_bandwidth_bytes_per_s", "value": 9e11, "unit": "byte/s",
                 "measurement_kind": "telemetry", "aggregation": "max",
                 "scope": "per_link", "source_name": "nvlink_link_peak", "link_type": "nvlink",
                 "entity_id": "nvlink:L0", "directionality": "bidirectional"},
                {"metric_id": "link_utilization_pct", "value": 80.0, "unit": "%",
                 "measurement_kind": "derived", "aggregation": "mean",
                 "scope": "per_link", "source_name": "derived_nvlink_utilization",
                 "link_type": "nvlink", "entity_id": "nvlink:L0", "directionality": "bidirectional",
                 "formula": "link_bandwidth_bytes_per_s / link_peak_bandwidth_bytes_per_s * 100",
                 "input_metric_ids": ["link_bandwidth_bytes_per_s", "link_peak_bandwidth_bytes_per_s"]},
                {"metric_id": "gpu_power_w", "value": 650, "unit": "W",
                 "measurement_kind": "telemetry", "aggregation": "mean",
                 "scope": "per_gpu", "source_name": "gpu_power_w"},
                {"metric_id": "gpu_clock_hz", "value": 1.4e9, "unit": "Hz",
                 "measurement_kind": "telemetry", "aggregation": "mean",
                 "scope": "per_gpu", "source_name": "gpu_clock_hz"},
                {"metric_id": "temperature_c", "value": 72, "unit": "°C",
                 "measurement_kind": "telemetry", "aggregation": "mean",
                 "scope": "per_gpu", "source_name": "gpu_temperature"},
                {"metric_id": "throttle_active_pct", "value": 0, "unit": "%",
                 "measurement_kind": "telemetry", "aggregation": "mean",
                 "scope": "per_gpu", "source_name": "throttle_active_pct"},
            ],
        }

    @staticmethod
    def valid_inferencex_database(row):
        source = {
            "id": "inferencex", "source_class": "third_party_public_benchmark",
            "record_count": 1, "results_url": "https://example.com",
            "dataset_url": "https://example.com/api",
        }
        record = {
            "id": "inferencex-1", "source_id": "inferencex",
            "source_class": "third_party_public_benchmark",
            "evidence_level": "publisher_published_observation",
            "benchmark_suite": "InferenceX", "benchmark_version": "public-api-v1",
            "publication_date": "2026-11-01", "submitter": "SemiAnalysis",
            "accelerator_vendor": "NVIDIA", "platform_id": None, "product_id": None,
            "system_type": "datacenter", "system_name": "h200_sxm",
            "division": "third_party", "availability": "published", "model": "dsr1",
            "scenario": "single_turn", "result_value": None, "result_unit": "",
            "accuracy_text": "", "inferred": False, "power_metrics_available": False,
            "design_power_watts": None, "system": {"workers": []}, "software": {},
            "workload": {}, "configuration": {}, "metrics": {},
            "model_display_name": "DeepSeek-R1-0528", "power_measurement_valid": False,
            "power_measurement_status": "unreported",
            "cpu_power_measurement_valid": False, "cpu_power_measurement_status": "not_present",
            "gpu_power_metrics_available": False,
            "cpu_power_metrics_available": False, "normalized_metrics": {},
            "notes": "", "compliance": "publisher_published", "errors": 0,
            "weight_data_types": "fp8", "source_record_key": "1", "source_location": "",
            "source_url": "https://example.com/api", "detail_url": None,
            "dataset_url": "https://example.com/api", "release_url": "https://example.com",
            **row,
        }
        return {
            "schema_version": "1.0", "sources": [source], "records": [record],
            "summary": summarize([record]),
        }

    def test_hardware_evidence_contract_accepts_provenanced_multilayer_counters(self):
        evidence = self.valid_hardware_evidence()
        db = self.valid_inferencex_database({"hardware_evidence": evidence})
        self.assertEqual(validate_database(db), [])

    def test_hardware_evidence_rejects_unit_scope_time_and_derived_metric_errors(self):
        evidence = self.valid_hardware_evidence()
        evidence["metrics"][0]["unit"] = "FLOP/s"
        evidence["metrics"][1]["value"] = -1
        evidence["metrics"][1].pop("precision")
        next(metric for metric in evidence["metrics"] if metric["metric_id"] == "link_utilization_pct")["input_metric_ids"] = ["missing_counter"]
        evidence["metrics"][0]["value"] = 101
        evidence["metrics"][9]["link_type"] = "unknown-fabric"
        evidence["sampling"]["ended_at"] = "2026-11-12T09:59:00Z"
        db = self.valid_inferencex_database({"hardware_evidence": evidence})
        errors = validate_database(db)
        self.assertTrue(any("sm_active_pct unit must be %" in error for error in errors))
        self.assertTrue(any("non-negative finite number" in error for error in errors))
        self.assertTrue(any("compute FLOP metrics require precision" in error for error in errors))
        self.assertTrue(any("derived input missing_counter is absent" in error for error in errors))
        self.assertTrue(any("sampling window must be positive" in error for error in errors))
        self.assertTrue(any("requires link_type=nvlink" in error for error in errors))

    def test_hardware_evidence_validator_handles_malformed_nested_types(self):
        evidence = self.valid_hardware_evidence()
        evidence["metrics"][0]["metric_id"] = {"unexpected": "object"}
        evidence["metrics"][2]["scope"] = {"unexpected": "object"}
        next(metric for metric in evidence["metrics"] if metric["metric_id"] == "link_utilization_pct")["input_metric_ids"] = [{"unexpected": "object"}]
        db = self.valid_inferencex_database({"hardware_evidence": evidence})
        errors = validate_database(db)
        self.assertTrue(any("unknown metric_id" in error for error in errors))
        self.assertTrue(any("scope is invalid" in error for error in errors))
        self.assertTrue(any("valid input_metric_ids" in error for error in errors))

    def test_hardware_evidence_is_optional_and_never_synthesized_by_importer(self):
        endpoint = "https://inferencex.semianalysis.com/api/v1/benchmarks?model=DeepSeek-R1-0528"
        raw = {"id": 999, "model": "dsr1", "hardware": "h200_sxm", "metrics": {}}
        normalized = normalize_inferencex_record(raw, endpoint)
        self.assertIsNone(normalized["hardware_evidence"])
        evidence = self.valid_hardware_evidence()
        raw["hardware_evidence"] = evidence
        preserved = normalize_inferencex_record(raw, endpoint)
        self.assertEqual(preserved["hardware_evidence"], evidence)

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
