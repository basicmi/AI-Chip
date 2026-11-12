import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from derive_hardware_metrics import derive_metrics
from validate_benchmark_results import validate_hardware_evidence


def base_evidence():
    return {
        "schema_version": "1.0",
        "collector": {"name": "fixture", "type": "profiler"},
        "system_scope": {"scope_type": "per_gpu", "device_count": 1},
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
            {"metric_id": "compute_flop_count", "value": 8e12, "unit": "FLOP",
             "measurement_kind": "hardware_counter", "aggregation": "sum",
             "scope": "per_gpu", "source_name": "flop_count_fp8",
             "precision": "FP8", "sparsity": "dense"},
            {"metric_id": "theoretical_peak_flops", "value": 2e12, "unit": "FLOP/s",
             "measurement_kind": "telemetry", "aggregation": "max",
             "scope": "per_gpu", "source_name": "device_peak_fp8",
             "precision": "FP8", "sparsity": "dense"},
            {"metric_id": "dram_read_bytes", "value": 6e9, "unit": "byte",
             "measurement_kind": "hardware_counter", "aggregation": "sum",
             "scope": "per_gpu", "source_name": "dram_read_bytes"},
            {"metric_id": "dram_write_bytes", "value": 4e9, "unit": "byte",
             "measurement_kind": "hardware_counter", "aggregation": "sum",
             "scope": "per_gpu", "source_name": "dram_write_bytes"},
            {"metric_id": "dram_peak_bandwidth_bytes_per_s", "value": 2e9, "unit": "byte/s",
             "measurement_kind": "telemetry", "aggregation": "max",
             "scope": "per_gpu", "source_name": "hbm_peak"},
            {"metric_id": "kv_cache_used_bytes", "value": 50e9, "unit": "byte",
             "measurement_kind": "telemetry", "aggregation": "mean",
             "scope": "per_gpu", "source_name": "kv_used"},
            {"metric_id": "kv_cache_capacity_bytes", "value": 100e9, "unit": "byte",
             "measurement_kind": "telemetry", "aggregation": "mean",
             "scope": "per_gpu", "source_name": "kv_capacity"},
            {"metric_id": "link_bandwidth_bytes_per_s", "value": 80e9, "unit": "byte/s",
             "measurement_kind": "telemetry", "aggregation": "mean",
             "scope": "per_link", "source_name": "nvlink_bw",
             "link_type": "nvlink", "entity_id": "nvlink:L0"},
            {"metric_id": "link_peak_bandwidth_bytes_per_s", "value": 100e9, "unit": "byte/s",
             "measurement_kind": "telemetry", "aggregation": "max",
             "scope": "per_link", "source_name": "nvlink_peak",
             "link_type": "nvlink", "entity_id": "nvlink:L0"},
        ],
    }


class HardwareMetricDerivationTests(unittest.TestCase):
    def test_derives_compute_hbm_kv_and_link_metrics(self):
        evidence = base_evidence()
        result, added, warnings = derive_metrics(evidence)
        values = {(metric["metric_id"], metric.get("entity_id")): metric["value"] for metric in added}
        self.assertAlmostEqual(values[("achieved_flops", None)], 8e11)
        self.assertAlmostEqual(values[("compute_peak_utilization_pct", None)], 40)
        self.assertAlmostEqual(values[("dram_bandwidth_bytes_per_s", None)], 1e9)
        self.assertAlmostEqual(values[("dram_bandwidth_utilization_pct", None)], 50)
        self.assertAlmostEqual(values[("kv_cache_occupancy_pct", None)], 50)
        self.assertAlmostEqual(values[("link_utilization_pct", "nvlink:L0")], 80)
        self.assertEqual(warnings, [])
        self.assertEqual(len(evidence["metrics"]), 9, "input evidence must not be mutated")
        self.assertEqual(validate_hardware_evidence(
            {"hardware_evidence": result}, "derived"
        ), [])

    def test_does_not_derive_compute_utilization_across_mismatched_precision(self):
        evidence = base_evidence()
        evidence["metrics"][1]["precision"] = "BF16"
        result, added, warnings = derive_metrics(evidence)
        self.assertFalse(any(item["metric_id"] == "compute_peak_utilization_pct" for item in added))
        self.assertTrue(any(item["metric_id"] == "achieved_flops" for item in added))

    def test_does_not_derive_bandwidth_from_one_direction_only(self):
        evidence = base_evidence()
        evidence["metrics"] = [
            metric for metric in evidence["metrics"] if metric["metric_id"] != "dram_write_bytes"
        ]
        _, added, _ = derive_metrics(evidence)
        self.assertFalse(any(item["metric_id"] == "dram_bandwidth_bytes_per_s" for item in added))

    def test_derives_link_bandwidth_from_directional_per_link_byte_totals(self):
        evidence = base_evidence()
        evidence["metrics"] = [
            metric for metric in evidence["metrics"]
            if metric["metric_id"] != "link_bandwidth_bytes_per_s"
        ]
        evidence["metrics"].extend([
            {"metric_id": "nvlink_tx_bytes", "value": 400e9, "unit": "byte",
             "measurement_kind": "hardware_counter", "aggregation": "sum",
             "scope": "per_link", "source_name": "DCGM_FI_PROF_NVLINK_L0_TX_BYTES",
             "link_type": "nvlink", "entity_id": "nvlink:L0"},
            {"metric_id": "nvlink_rx_bytes", "value": 400e9, "unit": "byte",
             "measurement_kind": "hardware_counter", "aggregation": "sum",
             "scope": "per_link", "source_name": "DCGM_FI_PROF_NVLINK_L0_RX_BYTES",
             "link_type": "nvlink", "entity_id": "nvlink:L0"},
        ])
        result, added, warnings = derive_metrics(evidence)
        link_bandwidth = next(item for item in added if item["metric_id"] == "link_bandwidth_bytes_per_s")
        link_utilization = next(item for item in added if item["metric_id"] == "link_utilization_pct")
        self.assertAlmostEqual(link_bandwidth["value"], 80e9)
        self.assertAlmostEqual(link_utilization["value"], 80)
        self.assertEqual(link_bandwidth["entity_id"], "nvlink:L0")
        self.assertEqual(validate_hardware_evidence(
            {"hardware_evidence": result}, "derived-link"
        ), [])

    def test_does_not_compare_different_link_entities(self):
        evidence = base_evidence()
        evidence["metrics"][-1]["entity_id"] = "nvlink:L1"
        _, added, _ = derive_metrics(evidence)
        self.assertFalse(any(item["metric_id"] == "link_utilization_pct" for item in added))

    def test_out_of_range_ratios_are_skipped_not_clamped(self):
        evidence = base_evidence()
        evidence["metrics"][4]["value"] = 0.5e9
        _, added, warnings = derive_metrics(evidence)
        self.assertFalse(any(item["metric_id"] == "dram_bandwidth_utilization_pct" for item in added))
        self.assertTrue(any("outside [0, 100]" in warning for warning in warnings))

    def test_missing_or_timezone_naive_window_is_rejected(self):
        evidence = base_evidence()
        evidence["sampling"]["started_at"] = "2026-11-12T10:00:00"
        with self.assertRaises(ValueError):
            derive_metrics(evidence)


if __name__ == "__main__":
    unittest.main()
