import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_gpu_execution_efficiency import analyze_gpu_execution_efficiency
from diagnose_hardware_performance import diagnose_record


def metric(metric_id, value, unit, scope, entity_id="gpu0", sampling_window=None, **extra):
    item = {
        "metric_id": metric_id,
        "value": value,
        "unit": unit,
        "measurement_kind": "telemetry",
        "aggregation": "mean",
        "scope": scope,
        "source_name": "fixture_" + metric_id,
    }
    if entity_id is not None:
        item["entity_id"] = entity_id
    if sampling_window is not None:
        item["sampling_window"] = sampling_window
    item.update(extra)
    return item


def window(start, end):
    return {
        "started_at": f"2026-11-13T10:00:{start:02d}Z",
        "ended_at": f"2026-11-13T10:00:{end:02d}Z",
    }


def evidence(metrics):
    return {
        "schema_version": "1.0",
        "collector": {"name": "fixture", "type": "profiler", "version": "1.0"},
        "system_scope": {"scope_type": "per_gpu", "device_count": 1, "device_model": "Test GPU"},
        "sampling": {
            "started_at": "2026-11-13T10:00:00Z",
            "ended_at": "2026-11-13T10:00:10Z",
            "sample_interval_ms": 100,
            "sample_count": 100,
        },
        "provenance": {
            "source_type": "independent_measurement",
            "source_url": "https://example.com/evidence.json",
            "collected_at": "2026-11-13T10:00:11Z",
        },
        "metrics": metrics,
    }


def event(event_id, category, start, end, *, parent="request-root", entity="gpu0", correlation=None):
    item = {
        "event_id": event_id,
        "name": event_id.replace("-", " "),
        "category": category,
        "started_at": f"2026-11-13T10:00:{start:02d}Z",
        "ended_at": f"2026-11-13T10:00:{end:02d}Z",
    }
    if parent is not None:
        item["parent_event_id"] = parent
    if entity is not None:
        item["entity_id"] = entity
    if correlation is not None:
        item["correlation_id"] = correlation
    return item


def trace(events):
    return {
        "schema_version": "1.0",
        "collector": {"name": "Serving Runtime Trace", "version": "1.0", "type": "runtime_trace"},
        "clock_domain": "utc_wall_clock",
        "sampling": {
            "started_at": "2026-11-13T10:00:00Z",
            "ended_at": "2026-11-13T10:00:10Z",
        },
        "provenance": {
            "source_type": "runtime_trace_export",
            "source_url": "https://example.com/runtime.json",
            "collected_at": "2026-11-13T10:00:12Z",
        },
        "events": events,
    }


def runtime_fixture():
    return trace([
        event("request-root", "request", 0, 10, parent=None, entity=None, correlation="r1"),
        event("prefill", "prefill", 1, 2),
        event("decode", "decode", 2, 6),
        event("kernel", "kernel", 3, 5, parent="decode"),
        event("communication", "communication", 4, 6),
        event("communication-wait", "communication_wait", 5, 6),
    ])


class GPUExecutionEfficiencyTests(unittest.TestCase):
    def test_same_scope_entity_and_window_activity_signals_are_grouped(self):
        common = window(1, 2)
        result = analyze_gpu_execution_efficiency({
            "id": "activity",
            "hardware_evidence": evidence([
                metric("sm_active_pct", 80, "%", "per_gpu", sampling_window=common),
                metric("tensor_active_pct", 50, "%", "per_gpu", sampling_window=common),
                metric("dram_active_pct", 40, "%", "per_gpu", sampling_window=common),
                metric("dram_bandwidth_utilization_pct", 75, "%", "per_gpu", sampling_window=common,
                       measurement_kind="derived", formula="measured / peak * 100",
                       input_metric_ids=["dram_bandwidth_bytes_per_s", "dram_peak_bandwidth_bytes_per_s"]),
            ]),
        })
        self.assertEqual(result["status"], "evidence_available")
        groups = result["hardware_activity"]["activity_groups"]
        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(group["scope"], "per_gpu")
        self.assertEqual(group["entity_id"], "gpu0")
        self.assertEqual(group["descriptive_contrasts"]["sm_inactive_cycle_complement_pct"], 20)
        self.assertEqual(group["descriptive_contrasts"]["dram_active_minus_bandwidth_utilization_pp"], -35)
        self.assertEqual(group["descriptive_contrasts"]["tensor_active_minus_sm_active_pp"], -30)
        self.assertIn("not a whole-GPU idle-time estimate", " ".join(result["limitations"] + result["hardware_activity"]["interpretation"]))

    def test_different_windows_and_entities_are_never_combined(self):
        metrics = [
            metric("sm_active_pct", 80, "%", "per_gpu", "gpu0", window(1, 2)),
            metric("sm_throughput_pct", 40, "%", "per_gpu", "gpu0", window(2, 3)),
            metric("dram_active_pct", 50, "%", "per_gpu", "gpu1", window(1, 2)),
            metric("dram_bandwidth_utilization_pct", 70, "%", "per_gpu", "gpu0", window(1, 2)),
        ]
        result = analyze_gpu_execution_efficiency({"id": "boundaries", "hardware_evidence": evidence(metrics)})
        groups = result["hardware_activity"]["activity_groups"]
        self.assertEqual(len(groups), 3)
        self.assertTrue(all(not group["descriptive_contrasts"] for group in groups))

    def test_kernel_counter_requires_exact_entity_and_unique_containing_kernel_event(self):
        kernel_window = {
            "started_at": "2026-11-13T10:00:03Z",
            "ended_at": "2026-11-13T10:00:04Z",
        }
        metrics = [
            metric("sm_throughput_pct", 65, "%", "per_kernel", "gpu0", kernel_window),
        ]
        record = {
            "id": "kernel-join",
            "hardware_evidence": evidence(metrics),
            "runtime_trace": runtime_fixture(),
        }
        result = analyze_gpu_execution_efficiency(record)
        joins = result["hardware_activity"]["metric_to_runtime_joins"]
        self.assertEqual(len(joins), 1)
        self.assertEqual(joins[0]["event_id"], "kernel")
        self.assertEqual(joins[0]["event_category"], "kernel")

    def test_metric_without_specific_window_is_not_phase_joined(self):
        result = analyze_gpu_execution_efficiency({
            "id": "coarse",
            "hardware_evidence": evidence([
                metric("sm_throughput_pct", 65, "%", "per_kernel", "gpu0"),
            ]),
            "runtime_trace": runtime_fixture(),
        })
        self.assertEqual(result["hardware_activity"]["activity_groups"][0]["metrics"]["sm_throughput_pct"][0]["value"], 65)
        self.assertEqual(result["hardware_activity"]["metric_to_runtime_joins"], [])

    def test_wrong_kernel_entity_does_not_join(self):
        kernel_window = {
            "started_at": "2026-11-13T10:00:03Z",
            "ended_at": "2026-11-13T10:00:04Z",
        }
        result = analyze_gpu_execution_efficiency({
            "id": "wrong-entity",
            "hardware_evidence": evidence([
                metric("sm_throughput_pct", 65, "%", "per_kernel", "gpu1", kernel_window),
            ]),
            "runtime_trace": runtime_fixture(),
        })
        self.assertEqual(result["hardware_activity"]["metric_to_runtime_joins"], [])

    def test_communication_compute_overlap_uses_same_request_interval_unions(self):
        result = analyze_gpu_execution_efficiency({"id": "overlap", "runtime_trace": runtime_fixture()})
        overlap = result["runtime_overlap"]
        self.assertEqual(overlap["status"], "available")
        self.assertEqual(overlap["request_count"], 1)
        request = overlap["requests"][0]
        self.assertEqual(request["kernel_union_ms"], 2000)
        self.assertEqual(request["communication_union_ms"], 2000)
        self.assertEqual(request["kernel_communication_overlap_ms"], 1000)
        self.assertEqual(request["communication_overlap_pct"], 50)
        self.assertEqual(request["kernel_decode_coverage_pct"], 50)
        self.assertEqual(request["communication_wait_decode_pct"], 25)
        self.assertEqual(overlap["communication_overlap_pct"]["p50"], 50)

    def test_nested_and_parallel_kernel_intervals_are_union_counted(self):
        events = [
            event("request-root", "request", 0, 10, parent=None, entity=None, correlation="r1"),
            event("decode", "decode", 1, 8),
            event("kernel-a", "kernel", 2, 5),
            event("kernel-b", "kernel", 4, 6),
            event("communication-a", "communication", 3, 7),
            event("communication-b", "communication", 6, 8),
        ]
        result = analyze_gpu_execution_efficiency({"id": "union", "runtime_trace": trace(events)})
        request = result["runtime_overlap"]["requests"][0]
        self.assertEqual(request["kernel_union_ms"], 4000)
        self.assertEqual(request["communication_union_ms"], 5000)
        self.assertEqual(request["kernel_communication_overlap_ms"], 3000)
        self.assertEqual(request["communication_overlap_pct"], 60)

    def test_duplicate_request_roots_are_not_merged(self):
        events = [
            event("request-a", "request", 0, 4, parent=None, entity=None, correlation="r1"),
            event("request-b", "request", 5, 9, parent=None, entity=None, correlation="r1"),
        ]
        result = analyze_gpu_execution_efficiency({"id": "duplicate", "runtime_trace": trace(events)})
        self.assertEqual(result["runtime_overlap"]["status"], "ambiguous_request_roots")
        self.assertEqual(result["runtime_overlap"]["request_count"], 0)

    def test_missing_hardware_and_trace_evidence_remains_unknown(self):
        result = analyze_gpu_execution_efficiency({"id": "empty"})
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["hardware_activity"]["status"], "insufficient_evidence")
        self.assertEqual(result["runtime_overlap"]["status"], "missing_runtime_trace")
        self.assertEqual(result["overall_verdict"], "undetermined")

    def test_diagnosis_report_includes_execution_efficiency_without_verdict(self):
        result = diagnose_record({
            "id": "integrated",
            "hardware_evidence": evidence([
                metric("sm_active_pct", 80, "%", "per_gpu", sampling_window=window(1, 2)),
            ]),
            "runtime_trace": runtime_fixture(),
        })
        self.assertIn("gpu_execution_efficiency", result)
        self.assertEqual(result["gpu_execution_efficiency"]["status"], "evidence_available")
        self.assertEqual(result["gpu_execution_efficiency"]["overall_verdict"], "undetermined")
        self.assertEqual(result["overall_verdict"], "undetermined")

    def test_invalid_hardware_evidence_is_rejected(self):
        bad = evidence([metric("sm_active_pct", 120, "%", "per_gpu", sampling_window=window(1, 2))])
        with self.assertRaisesRegex(ValueError, "percentage value"):
            analyze_gpu_execution_efficiency({"id": "invalid", "hardware_evidence": bad})


if __name__ == "__main__":
    unittest.main()
