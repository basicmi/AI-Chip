import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from correlate_cross_layer_performance import correlate_records


def record(record_id, *, system_name="H200 SXM", product_id="h200-sxm",
           framework="vLLM 0.11", recipe="vllm-0.11-fp8", isl=1024,
           concurrency=32, throughput=100, ttft=1.0, tpot=0.1,
           configuration=None, hardware_evidence=None):
    normalized = {
        "output_throughput_per_gpu": {
            "value": throughput, "unit": "tok/s/GPU", "direction": "higher",
            "family": "throughput", "label": "Output throughput", "source_metric": "output_tput_per_gpu"
        },
        "p99_ttft": {
            "value": ttft, "unit": "s", "direction": "lower",
            "family": "latency", "label": "P99 TTFT", "source_metric": "p99_ttft"
        },
    }
    raw = {"output_tput_per_gpu": throughput, "p99_ttft": ttft}
    if tpot is not None:
        normalized["p99_tpot"] = {
            "value": tpot, "unit": "s", "direction": "lower",
            "family": "latency", "label": "P99 TPOT", "source_metric": "p99_tpot"
        }
        raw["p99_tpot"] = tpot
    return {
        "id": record_id,
        "source_id": "inferencex",
        "source_class": "third_party_public_benchmark",
        "benchmark_suite": "SemiAnalysis InferenceX",
        "benchmark_version": None,
        "model": "dsr1",
        "model_display_name": "DeepSeek-R1-0528",
        "scenario": "single_turn",
        "division": "third_party",
        "availability": "published",
        "system_type": "datacenter",
        "system_name": system_name,
        "accelerator_vendor": "NVIDIA" if "H200" in system_name else "AMD",
        "platform_id": "nvidia-gpu" if "H200" in system_name else "amd-gpu",
        "product_id": product_id,
        "publication_date": "2026-11-12",
        "source_url": "https://example.com/benchmark/" + record_id,
        "workload": {
            "precision": "FP8", "benchmark_type": "single_turn",
            "isl": isl, "osl": 1024, "concurrency": concurrency,
            "speculative_method": "none", "disaggregated": False,
        },
        "configuration": configuration or {"decode_tp": 8},
        "system": {
            "hardware": system_name, "nodes": 1, "total_accelerators": 8,
            "accelerators_per_node": 8, "is_multinode": False,
            "physical_decode_gpus": 8,
            "workers": [{"role": "decode", "worker_idx": 0, "num_gpus": 8}],
        },
        "software": {"framework": framework, "recipe_fingerprint": recipe},
        "metrics": raw,
        "normalized_metrics": normalized,
        "power_measurement_valid": False,
        "gpu_power_metrics_available": False,
        **({"hardware_evidence": hardware_evidence} if hardware_evidence is not None else {}),
    }


def evidence_fixture():
    def metric(metric_id, value, unit, kind, aggregation, scope, source_name, **extra):
        return {
            "metric_id": metric_id, "value": value, "unit": unit,
            "measurement_kind": kind, "aggregation": aggregation,
            "scope": scope, "source_name": source_name, **extra,
        }
    return {
        "schema_version": "1.0",
        "collector": {"name": "Nsight Compute", "type": "profiler", "version": "2026.3"},
        "system_scope": {"scope_type": "per_gpu", "device_count": 1, "device_model": "H200 SXM"},
        "sampling": {
            "started_at": "2026-11-12T10:00:00Z",
            "ended_at": "2026-11-12T10:00:10Z",
            "sample_interval_ms": 1000, "sample_count": 10,
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


class CrossLayerCorrelationTests(unittest.TestCase):
    def test_strict_workload_cohort_compares_hardware_and_runtime_variants(self):
        rows = [
            record("h200-a", throughput=100, ttft=1.0, tpot=0.1),
            record("mi300-a", system_name="MI300X", product_id="mi300x",
                   framework="vLLM ROCm", recipe="vllm-rocm-0.11",
                   throughput=125, ttft=0.9, tpot=0.12),
        ]
        result = correlate_records({
            "sources": [{"id": "inferencex", "version": "Public API v1"}],
            "records": rows,
        })
        self.assertEqual(result["cohort_count"], 1)
        cohort = result["cohorts"][0]
        self.assertEqual(cohort["record_count"], 2)
        self.assertEqual(cohort["execution_group_count"], 2)
        self.assertEqual(len(cohort["pairwise_comparisons"]), 1)
        comparison = cohort["pairwise_comparisons"][0]
        self.assertIn("product_id", comparison["changed_dimensions"])
        self.assertIn("framework", comparison["changed_dimensions"])
        deltas = {item["metric"]: item for item in comparison["metric_deltas"]}
        self.assertAlmostEqual(deltas["output_throughput_per_gpu"]["right_vs_left_change_pct"], 25)
        self.assertAlmostEqual(deltas["output_throughput_per_gpu"]["right_vs_left_improvement_pct"], 25)
        self.assertAlmostEqual(deltas["p99_ttft"]["right_vs_left_improvement_pct"], 10)
        self.assertAlmostEqual(deltas["p99_tpot"]["right_vs_left_improvement_pct"], -20)
        self.assertEqual(comparison["causal_attribution"], "not_claimed")

    def test_repeated_execution_records_use_metric_specific_medians(self):
        rows = [
            record("h200-a", throughput=100, ttft=1.0, tpot=0.1),
            record("h200-b", throughput=120, ttft=0.8, tpot=None),
            record("mi300-a", system_name="MI300X", product_id="mi300x",
                   framework="vLLM ROCm", recipe="vllm-rocm",
                   throughput=130, ttft=0.7, tpot=0.12),
        ]
        result = correlate_records({
            "sources": [{"id": "inferencex", "version": "Public API v1"}],
            "records": rows,
        })
        cohort = result["cohorts"][0]
        h200 = next(group for group in cohort["execution_groups"]
                    if group["execution_identity"]["system_name"] == "H200 SXM")
        self.assertEqual(h200["record_count"], 2)
        self.assertEqual(h200["normalized_metrics"]["output_throughput_per_gpu"]["value"], 110)
        self.assertEqual(h200["normalized_metrics"]["output_throughput_per_gpu"]["record_count"], 2)
        self.assertEqual(h200["normalized_metrics"]["p99_tpot"]["value"], 0.1)
        self.assertEqual(h200["normalized_metrics"]["p99_tpot"]["record_count"], 1)
        self.assertEqual(h200["normalized_metrics"]["p99_tpot"]["group_record_count"], 2)

    def test_workload_differences_are_separate_cohorts_not_wildcards(self):
        rows = [
            record("isl-1024", isl=1024),
            record("isl-2048", isl=2048),
            record("concurrency-64", concurrency=64),
        ]
        result = correlate_records({
            "sources": [{"id": "inferencex", "version": "Public API v1"}],
            "records": rows,
        })
        self.assertEqual(result["cohort_count"], 3)
        self.assertEqual(result["matched_record_count"], 3)
        self.assertTrue(all(cohort["record_count"] == 1 for cohort in result["cohorts"]))
        self.assertTrue(all(not cohort["pairwise_comparisons"] for cohort in result["cohorts"]))

    def test_incomplete_workload_identity_is_excluded_not_wildcarded(self):
        row = record("missing-concurrency")
        row["workload"].pop("concurrency")
        result = correlate_records({
            "sources": [{"id": "inferencex", "version": "Public API v1"}],
            "records": [row],
        })
        self.assertEqual(result["matched_record_count"], 0)
        self.assertEqual(result["excluded_record_count"], 1)
        self.assertIn("concurrency", result["excluded_records"][0]["reason"])

    def test_non_inferencex_sources_are_not_cross_compared(self):
        row = record("other-source")
        row["source_id"] = "mlperf"
        result = correlate_records([row])
        self.assertEqual(result["cohort_count"], 0)
        self.assertEqual(result["excluded_record_count"], 1)

    def test_incomplete_execution_identity_does_not_create_peer_comparisons(self):
        left = record("incomplete-a")
        right = record("incomplete-b", throughput=150)
        for row in (left, right):
            row["system_name"] = None
            row["product_id"] = None
            row["platform_id"] = None
            row["system"]["hardware"] = None
        result = correlate_records({
            "sources": [{"id": "inferencex", "version": "Public API v1"}],
            "records": [left, right],
        })
        cohort = result["cohorts"][0]
        self.assertEqual(cohort["execution_group_count"], 2)
        self.assertEqual(cohort["comparable_execution_group_count"], 0)
        self.assertEqual(cohort["pairwise_comparisons"], [])

    def test_zero_baseline_is_not_divided_or_fabricated(self):
        left = record("zero", throughput=0)
        right = record("nonzero", system_name="MI300X", product_id="mi300x",
                       framework="ROCm", recipe="rocm", throughput=100)
        result = correlate_records({
            "sources": [{"id": "inferencex", "version": "Public API v1"}],
            "records": [left, right],
        })
        comparison = result["cohorts"][0]["pairwise_comparisons"][0]
        self.assertNotIn("output_throughput_per_gpu", {
            item["metric"]: item for item in comparison["metric_deltas"]
        })

    def test_hardware_evidence_is_attached_but_temporal_alignment_is_not_assumed(self):
        row = record("with-evidence", hardware_evidence=evidence_fixture())
        result = correlate_records({
            "sources": [{"id": "inferencex", "version": "Public API v1"}],
            "records": [row],
        })
        profile = result["cohorts"][0]["records"][0]["hardware_evidence"]
        self.assertEqual(profile["status"], "available")
        self.assertEqual(profile["roofline"], "complete")
        self.assertEqual(profile["temporal_alignment"], "not_established")
        self.assertAlmostEqual(profile["roofline_analyses"][0]["roofline_attainment_pct"], 50)
        self.assertEqual(
            result["cohorts"][0]["execution_groups"][0]["hardware_evidence_coverage"]["records_with_evidence"],
            1,
        )

    def test_power_and_energy_metrics_require_validated_gpu_power(self):
        row = record("power")
        row["normalized_metrics"]["energy_per_output_token"] = {
            "value": 0.3, "unit": "J/output token", "direction": "lower",
            "family": "energy", "label": "Energy/output token",
            "source_metric": "joules_per_output_token",
        }
        row["metrics"]["joules_per_output_token"] = 0.3
        result = correlate_records({
            "sources": [{"id": "inferencex", "version": "Public API v1"}],
            "records": [row],
        })
        self.assertNotIn(
            "energy_per_output_token",
            result["cohorts"][0]["records"][0]["normalized_metrics"],
        )

    def test_pairwise_comparison_limit_is_deterministic_and_reported(self):
        rows = [
            record("h200", throughput=100),
            record("mi300", system_name="MI300X", product_id="mi300x",
                   framework="ROCm", recipe="rocm", throughput=110),
            record("gb200", system_name="GB200", product_id="gb200",
                   framework="vLLM", recipe="vllm-gb200", throughput=120),
        ]
        result = correlate_records({
            "sources": [{"id": "inferencex", "version": "Public API v1"}],
            "records": rows,
        }, max_comparisons=1)
        cohort = result["cohorts"][0]
        self.assertEqual(len(cohort["pairwise_comparisons"]), 1)
        self.assertTrue(cohort["pairwise_comparisons_truncated"])
        self.assertEqual(result["total_pairwise_comparisons_omitted"], 2)

    def test_invalid_input_and_comparison_limit_are_rejected(self):
        with self.assertRaises(ValueError):
            correlate_records({"records": "not-a-list"})
        with self.assertRaises(ValueError):
            correlate_records([], max_comparisons=-1)


if __name__ == "__main__":
    unittest.main()
