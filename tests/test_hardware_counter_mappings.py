import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hardware_counter_mapping import load_catalog, normalize_counter, normalize_payload
from validate_benchmark_results import validate_hardware_evidence
from validate_hardware_counter_mappings import validate_catalog


class HardwareCounterMappingTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog()

    def test_catalog_references_only_known_canonical_metrics(self):
        self.assertEqual(validate_catalog(self.catalog), [])
        self.assertEqual(len(self.catalog["sources"]), 3)
        self.assertGreaterEqual(len(self.catalog["mappings"]), 50)

    def test_dcgm_ratio_is_converted_to_percent_without_changing_semantics(self):
        result = normalize_counter(
            "nvidia-dcgm", "DCGM_FI_PROF_TENSOR_UTIL_RATIO", 0.72,
            catalog=self.catalog,
        )
        self.assertTrue(result["mapped"])
        metric = result["metric"]
        self.assertEqual(metric["metric_id"], "tensor_active_pct")
        self.assertAlmostEqual(metric["value"], 72.0)
        self.assertEqual(metric["unit"], "%")
        self.assertEqual(metric["mapping_quality"], "direct")
        self.assertIn("tensor pipe active", metric["mapping_note"])

    def test_dcgm_clock_is_converted_from_mhz_to_hz(self):
        result = normalize_counter(
            "nvidia-dcgm", "DCGM_FI_DEV_SM_CLOCK", 1410,
            catalog=self.catalog,
        )
        self.assertEqual(result["metric"]["metric_id"], "gpu_clock_hz")
        self.assertEqual(result["metric"]["value"], 1_410_000_000)
        self.assertEqual(result["metric"]["unit"], "Hz")

    def test_per_link_nvlink_mapping_preserves_link_identity(self):
        result = normalize_counter(
            "nvidia-dcgm", "DCGM_FI_PROF_NVLINK_L7_TX_BYTES", 123456,
            catalog=self.catalog,
        )
        metric = result["metric"]
        self.assertEqual(metric["metric_id"], "nvlink_tx_bytes")
        self.assertEqual(metric["scope"], "per_link")
        self.assertEqual(metric["entity_id"], "nvlink:L7")
        self.assertEqual(metric["link_type"], "nvlink")

    def test_monotonic_pcie_counter_requires_explicit_delta(self):
        source = "DCGM_FI_PROF_PCIE_TX_BYTES_TOTAL"
        missing = normalize_counter("nvidia-dcgm", source, 9000, catalog=self.catalog)
        self.assertFalse(missing["mapped"])
        self.assertEqual(missing["reason"], "counter_delta_required")
        mapped = normalize_counter(
            "nvidia-dcgm", source, 9000, counter_delta=1250, catalog=self.catalog
        )
        self.assertEqual(mapped["metric"]["value"], 1250)
        self.assertEqual(mapped["metric"]["aggregation"], "sum")

    def test_nsight_throughput_remains_kernel_scoped_and_distinct_from_sm_activity(self):
        result = normalize_counter(
            "nvidia-nsight-compute",
            "sm__throughput.avg.pct_of_peak_sustained_elapsed",
            72,
            catalog=self.catalog,
        )
        metric = result["metric"]
        self.assertEqual(metric["metric_id"], "sm_throughput_pct")
        self.assertEqual(metric["scope"], "per_kernel")
        self.assertNotEqual(metric["metric_id"], "sm_active_pct")

    def test_profiler_only_flop_metric_is_not_falsely_mapped_to_absolute_flops(self):
        result = normalize_counter(
            "amd-rocm-compute-profiler", "FLOPs (Total)", 100,
            catalog=self.catalog,
        )
        self.assertFalse(result["mapped"])
        self.assertEqual(result["reason"], "reference_only_semantics_not_normalized")

    def test_unknown_source_metric_is_explicitly_unmapped(self):
        result = normalize_counter("nvidia-dcgm", "NOT_A_REAL_COUNTER", 1, catalog=self.catalog)
        self.assertFalse(result["mapped"])
        self.assertEqual(result["reason"], "no_exact_source_mapping")

    def test_payload_normalization_emits_valid_evidence_and_unmapped_queue(self):
        payload = {
            "source_id": "nvidia-dcgm",
            "collector": {"name": "DCGM", "version": "4.x", "type": "device_telemetry"},
            "system_scope": {"scope_type": "per_gpu", "device_count": 1, "device_model": "H200"},
            "sampling": {
                "started_at": "2026-11-12T10:00:00Z", "ended_at": "2026-11-12T10:01:00Z",
                "sample_interval_ms": 1000, "sample_count": 60,
            },
            "provenance": {
                "source_type": "telemetry_export", "source_url": "https://example.com/dcgm.json",
                "collected_at": "2026-11-12T10:02:00Z",
            },
            "counters": [
                {"source_metric": "DCGM_FI_PROF_SM_UTIL_RATIO", "value": 0.8},
                {"source_metric": "DCGM_FI_PROF_NVLINK_L0_TX_BYTES", "value": 1000},
                {"source_metric": "DCGM_FI_DEV_SM_CLOCK", "value": 1410},
                {"source_metric": "DCGM_FI_DEV_CLOCKS_EVENT_REASONS", "value": 4},
            ],
        }
        result = normalize_payload(payload, self.catalog)
        self.assertEqual(len(result["hardware_evidence"]["metrics"]), 3)
        self.assertEqual(len(result["unmapped_counters"]), 1)
        self.assertEqual(validate_hardware_evidence(
            {"hardware_evidence": result["hardware_evidence"]}, "test"
        ), [])


if __name__ == "__main__":
    unittest.main()
