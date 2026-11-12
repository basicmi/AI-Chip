import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from diagnose_hardware_performance import (
    analyze_communication,
    analyze_roofline,
    analyze_serving_runtime,
    diagnose_record,
)


def metric(metric_id, value, unit, kind, aggregation, scope, source_name, **extra):
    return {
        "metric_id": metric_id,
        "value": value,
        "unit": unit,
        "measurement_kind": kind,
        "aggregation": aggregation,
        "scope": scope,
        "source_name": source_name,
        **extra,
    }


def base_evidence():
    return {
        "schema_version": "1.0",
        "collector": {"name": "fixture", "type": "profiler", "version": "1.0"},
        "system_scope": {"scope_type": "per_gpu", "device_count": 1, "device_model": "Test GPU"},
        "sampling": {
            "started_at": "2026-11-12T10:00:00Z",
            "ended_at": "2026-11-12T10:00:10Z",
            "sample_interval_ms": 1000,
            "sample_count": 10,
        },
        "provenance": {
            "source_type": "independent_measurement",
            "source_url": "https://example.com/evidence.json",
            "collected_at": "2026-11-12T10:00:11Z",
        },
        "metrics": [
            metric("compute_flop_count", 8e12, "FLOP", "hardware_counter", "sum",
                   "per_gpu", "flop_count_fp8", precision="FP8", sparsity="dense"),
            metric("theoretical_peak_flops", 2e12, "FLOP/s", "telemetry", "max",
                   "per_gpu", "device_peak_fp8", precision="FP8", sparsity="dense"),
            metric("dram_read_bytes", 6e9, "byte", "hardware_counter", "sum",
                   "per_gpu", "dram_read_bytes"),
            metric("dram_write_bytes", 4e9, "byte", "hardware_counter", "sum",
                   "per_gpu", "dram_write_bytes"),
            metric("dram_peak_bandwidth_bytes_per_s", 2e9, "byte/s", "telemetry", "max",
                   "per_gpu", "hbm_peak"),
            metric("kv_cache_used_bytes", 50e9, "byte", "telemetry", "mean",
                   "per_gpu", "kv_used"),
            metric("kv_cache_capacity_bytes", 100e9, "byte", "telemetry", "mean",
                   "per_gpu", "kv_capacity"),
            metric("throttle_active_pct", 0, "%", "telemetry", "mean",
                   "per_gpu", "throttle_active"),
        ],
    }


def base_record():
    return {
        "id": "fixture-record",
        "hardware_evidence": base_evidence(),
        "workload": {"isl": 4096, "osl": 1024, "concurrency": 64},
        "configuration": {"prefill_tp": 4, "decode_tp": 8},
        "normalized_metrics": {
            "median_ttft": {"value": 0.8, "unit": "s", "direction": "lower", "family": "latency"},
            "p99_ttft": {"value": 1.6, "unit": "s", "direction": "lower", "family": "latency"},
            "median_tpot": {"value": 0.04, "unit": "s", "direction": "lower", "family": "latency"},
            "p99_tpot": {"value": 0.08, "unit": "s", "direction": "lower", "family": "latency"},
            "p99_itl": {"value": 0.09, "unit": "s", "direction": "lower", "family": "latency"},
            "output_throughput_per_gpu": {
                "value": 120, "unit": "tok/s/GPU", "direction": "higher", "family": "throughput"
            },
            "mean_gpu_utilization": {"value": 72, "unit": "%", "direction": "context", "family": "telemetry"},
            "mean_gpu_memory_used": {"value": 70000, "unit": "MB", "direction": "context", "family": "telemetry"},
        },
    }


class HardwarePerformanceDiagnosisTests(unittest.TestCase):
    def test_roofline_uses_matching_compute_and_memory_measurements(self):
        result = analyze_roofline(base_evidence())
        self.assertEqual(result["status"], "complete")
        item = result["analyses"][0]
        self.assertAlmostEqual(item["arithmetic_intensity_flop_per_byte"], 800)
        self.assertAlmostEqual(item["achieved_flops_per_second"], 8e11)
        self.assertAlmostEqual(item["measured_dram_bandwidth_bytes_per_second"], 1e9)
        self.assertAlmostEqual(item["compute_ceiling_flops_per_second"], 2e12)
        self.assertAlmostEqual(item["memory_ceiling_flops_per_second"], 1.6e12)
        self.assertAlmostEqual(item["roofline_ceiling_flops_per_second"], 1.6e12)
        self.assertEqual(item["lower_theoretical_ceiling"], "memory")
        self.assertAlmostEqual(item["roofline_attainment_pct"], 50)

    def test_zero_read_bytes_are_valid_when_write_traffic_is_present(self):
        evidence = base_evidence()
        evidence["metrics"][2]["value"] = 0
        result = analyze_roofline(evidence)
        self.assertEqual(result["status"], "complete")
        self.assertAlmostEqual(result["analyses"][0]["arithmetic_intensity_flop_per_byte"], 800)

    def test_roofline_does_not_mix_different_scopes(self):
        evidence = base_evidence()
        evidence["metrics"][3]["scope"] = "per_system"
        result = analyze_roofline(evidence)
        item = result["analyses"][0]
        self.assertIsNone(item["arithmetic_intensity_flop_per_byte"])
        self.assertIn("dram_write_bytes (sum, same scope/entity)", item["missing_inputs"])

    def test_roofline_requires_precision_and_sparsity_matched_peak(self):
        evidence = base_evidence()
        evidence["metrics"][1]["precision"] = "BF16"
        result = analyze_roofline(evidence)
        item = result["analyses"][0]
        self.assertIsNone(item["compute_ceiling_flops_per_second"])
        self.assertIsNone(item["roofline_ceiling_flops_per_second"])
        self.assertIn("theoretical_peak_flops (same precision, sparsity, scope/entity)", item["missing_inputs"])

    def test_multiple_gpus_are_analyzed_independently(self):
        evidence = base_evidence()
        second = []
        for item in evidence["metrics"]:
            clone = dict(item)
            clone["entity_id"] = "gpu:1"
            item["entity_id"] = "gpu:0"
            second.append(clone)
        evidence["metrics"].extend(second)
        result = analyze_roofline(evidence)
        self.assertEqual(len(result["analyses"]), 2)
        self.assertEqual({item["entity_id"] for item in result["analyses"]}, {"gpu:0", "gpu:1"})

    def test_communication_derives_same_link_bidirectional_utilization(self):
        evidence = base_evidence()
        evidence["metrics"].extend([
            metric("nvlink_tx_bytes", 400e9, "byte", "hardware_counter", "sum",
                   "per_link", "nvlink_l0_tx", link_type="nvlink", entity_id="nvlink:L0"),
            metric("nvlink_rx_bytes", 400e9, "byte", "hardware_counter", "sum",
                   "per_link", "nvlink_l0_rx", link_type="nvlink", entity_id="nvlink:L0"),
            metric("link_peak_bandwidth_bytes_per_s", 100e9, "byte/s", "telemetry", "max",
                   "per_link", "nvlink_l0_peak", link_type="nvlink",
                   entity_id="nvlink:L0", directionality="bidirectional"),
        ])
        result = analyze_communication(evidence)
        self.assertEqual(result["status"], "complete")
        link = result["links"][0]
        self.assertAlmostEqual(link["measured_bandwidth_bytes_per_second"], 80e9)
        self.assertAlmostEqual(link["utilization_pct"], 80)
        self.assertEqual(link["entity_id"], "nvlink:L0")

    def test_communication_never_pairs_counters_from_different_links(self):
        evidence = base_evidence()
        evidence["metrics"].extend([
            metric("nvlink_tx_bytes", 400e9, "byte", "hardware_counter", "sum",
                   "per_link", "nvlink_l0_tx", link_type="nvlink", entity_id="nvlink:L0"),
            metric("nvlink_rx_bytes", 400e9, "byte", "hardware_counter", "sum",
                   "per_link", "nvlink_l1_rx", link_type="nvlink", entity_id="nvlink:L1"),
            metric("link_peak_bandwidth_bytes_per_s", 100e9, "byte/s", "telemetry", "max",
                   "per_link", "nvlink_l0_peak", link_type="nvlink",
                   entity_id="nvlink:L0", directionality="bidirectional"),
        ])
        result = analyze_communication(evidence)
        self.assertEqual(result["status"], "partial")
        self.assertIsNone(result["links"][0]["measured_bandwidth_bytes_per_second"])
        self.assertIsNone(result["links"][0]["utilization_pct"])

    def test_communication_requires_directionality_matched_peak(self):
        evidence = base_evidence()
        evidence["metrics"].extend([
            metric("link_bandwidth_bytes_per_s", 80e9, "byte/s", "telemetry", "mean",
                   "per_link", "nvlink_l0_bw", link_type="nvlink",
                   entity_id="nvlink:L0", directionality="bidirectional"),
            metric("link_peak_bandwidth_bytes_per_s", 100e9, "byte/s", "telemetry", "max",
                   "per_link", "nvlink_l0_tx_peak", link_type="nvlink",
                   entity_id="nvlink:L0", directionality="tx"),
        ])
        result = analyze_communication(evidence)
        self.assertEqual(result["status"], "partial")
        self.assertIsNone(result["links"][0]["utilization_pct"])

    def test_reported_link_utilization_is_retained_without_inventing_peak(self):
        evidence = base_evidence()
        evidence["metrics"].append(
            metric("link_utilization_pct", 61, "%", "telemetry", "mean",
                   "per_link", "nvlink_l0_util", link_type="nvlink",
                   entity_id="nvlink:L0", directionality="tx")
        )
        result = analyze_communication(evidence)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["links"][0]["utilization_pct"], 61)
        self.assertEqual(result["links"][0]["utilization_source"], "reported_link_utilization_pct")

    def test_serving_runtime_validates_units_and_exposes_tail_ratios(self):
        result = analyze_serving_runtime(base_record())
        self.assertEqual(result["status"], "available")
        self.assertAlmostEqual(result["derived_descriptive_ratios"]["ttft_p99_to_median_ratio"], 2)
        self.assertAlmostEqual(result["derived_descriptive_ratios"]["tpot_p99_to_median_ratio"], 2)
        self.assertEqual(result["workload"]["concurrency"], 64)
        self.assertEqual(result["parallelism"]["decode_tp"], 8)
        record = base_record()
        record["normalized_metrics"]["p99_ttft"]["unit"] = "ms"
        self.assertNotIn("p99_ttft", analyze_serving_runtime(record)["metrics"])

    def test_power_energy_runtime_signals_require_strict_power_verdict(self):
        record = base_record()
        record["normalized_metrics"]["decode_energy_per_output_token"] = {
            "value": 0.2, "unit": "J/output token", "direction": "lower", "family": "energy"
        }
        self.assertNotIn("decode_energy_per_output_token", analyze_serving_runtime(record)["metrics"])
        record["power_measurement_valid"] = True
        record["gpu_power_metrics_available"] = True
        self.assertIn("decode_energy_per_output_token", analyze_serving_runtime(record)["metrics"])

    def test_diagnosis_never_emits_automatic_bottleneck_verdict(self):
        report = diagnose_record(base_record())
        self.assertEqual(report["overall_verdict"], "undetermined")
        self.assertFalse(report["attribution"]["automatic_bottleneck_classification"])
        self.assertTrue(any(
            item["mechanism"] == "runtime_scheduling_or_queueing" and item["status"] == "not_attributed"
            for item in report["attribution"]["candidates"]
        ))
        self.assertTrue(any(item["mechanism"] == "kv_cache_occupancy" for item in report["attribution"]["candidates"]))

    def test_throttle_counter_is_reported_as_observed_not_as_root_cause(self):
        record = base_record()
        record["hardware_evidence"]["metrics"].append(
            metric("temperature_c", 88, "°C", "telemetry", "mean", "per_gpu", "gpu_temp")
        )
        record["hardware_evidence"]["metrics"].append(
            metric("gpu_clock_hz", 1.1e9, "Hz", "telemetry", "mean", "per_gpu", "gpu_clock")
        )
        record["hardware_evidence"]["metrics"].append(
            metric("gpu_power_w", 650, "W", "telemetry", "mean", "per_gpu", "gpu_power")
        )
        record["hardware_evidence"]["metrics"][-4]["value"] = 12
        report = diagnose_record(record)
        candidate = next(item for item in report["attribution"]["candidates"]
                         if item["mechanism"] == "thermal_or_power_throttling")
        self.assertEqual(candidate["status"], "observed")
        self.assertIn("does not identify the specific throttle reason", candidate["not_proven"])

    def test_missing_hardware_evidence_does_not_become_zero_or_idle(self):
        report = diagnose_record({"id": "runtime-only"})
        self.assertEqual(report["overall_status"], "insufficient_evidence")
        self.assertEqual(report["overall_verdict"], "undetermined")
        self.assertEqual(report["roofline"]["status"], "insufficient_evidence")
        self.assertIn("unknown, never zero", report["limitations"][-1])

    def test_invalid_hardware_evidence_is_rejected(self):
        record = base_record()
        record["hardware_evidence"]["sampling"]["started_at"] = "2026-11-12T10:00:00"
        with self.assertRaises(ValueError):
            diagnose_record(record)


if __name__ == "__main__":
    unittest.main()
