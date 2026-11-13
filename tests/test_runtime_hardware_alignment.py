import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from align_runtime_hardware_traces import align_database, align_record
from validate_benchmark_results import validate_hardware_evidence, validate_runtime_trace


def hardware_evidence(*, metric_window=True, metric_scope="per_gpu",
                      metric_entity="gpu0", started_at="2026-11-13T10:00:00Z",
                      ended_at="2026-11-13T10:00:10Z"):
    metric = {
        "metric_id": "sm_active_pct",
        "value": 72.5,
        "unit": "%",
        "measurement_kind": "hardware_counter",
        "aggregation": "mean",
        "scope": metric_scope,
        "source_name": "sm__active.avg.pct_of_peak_sustained_elapsed",
        "entity_id": metric_entity,
    }
    if metric_window:
        metric["sampling_window"] = {
            "started_at": "2026-11-13T10:00:02Z",
            "ended_at": "2026-11-13T10:00:04Z",
        }
    return {
        "schema_version": "1.0",
        "collector": {"name": "Nsight Compute", "version": "2026.3", "type": "profiler"},
        "system_scope": {"scope_type": "per_gpu", "device_count": 1, "device_model": "H200"},
        "sampling": {
            "started_at": started_at,
            "ended_at": ended_at,
            "sample_interval_ms": 100,
            "sample_count": 100,
        },
        "provenance": {
            "source_type": "profiler_export",
            "source_url": "https://example.com/hardware.json",
            "collected_at": "2026-11-13T10:00:11Z",
        },
        "metrics": [metric],
    }


def runtime_trace(*, events=None, started_at="2026-11-13T10:00:00Z",
                  ended_at="2026-11-13T10:00:10Z", clock_domain="utc_wall_clock"):
    if events is None:
        events = [
            {
                "event_id": "prefill-1", "name": "prefill batch 1",
                "category": "prefill",
                "started_at": "2026-11-13T10:00:01Z",
                "ended_at": "2026-11-13T10:00:08Z",
                "entity_id": "gpu0",
            },
            {
                "event_id": "kernel-1", "name": "attention kernel",
                "category": "kernel",
                "started_at": "2026-11-13T10:00:02Z",
                "ended_at": "2026-11-13T10:00:04Z",
                "entity_id": "gpu0",
                "correlation_id": "request-17",
                "parent_event_id": "prefill-1",
                "stream_id": "stream-0",
            },
        ]
    return {
        "schema_version": "1.0",
        "collector": {"name": "Serving Runtime Trace", "version": "1.0", "type": "runtime_trace"},
        "clock_domain": clock_domain,
        "sampling": {"started_at": started_at, "ended_at": ended_at},
        "provenance": {
            "source_type": "runtime_trace_export",
            "source_url": "https://example.com/runtime-trace.json",
            "collected_at": "2026-11-13T10:00:12Z",
        },
        "events": events,
    }


def record(*, metric_window=True, metric_scope="per_gpu", metric_entity="gpu0",
           trace=None, evidence=None):
    return {
        "id": "alignment-fixture",
        "hardware_evidence": evidence if evidence is not None else hardware_evidence(
            metric_window=metric_window, metric_scope=metric_scope, metric_entity=metric_entity
        ),
        "runtime_trace": trace if trace is not None else runtime_trace(),
    }


class RuntimeHardwareAlignmentTests(unittest.TestCase):
    def test_metric_window_inside_nested_kernel_event_joins_to_leaf_event(self):
        report = align_record(record())
        self.assertEqual(report["status"], "overlapping_capture_windows")
        self.assertEqual(report["eligible_metric_phase_join_count"], 1)
        metric = report["metric_alignments"][0]
        self.assertEqual(metric["alignment_status"], "fully_contained_single_leaf_event")
        self.assertEqual(metric["selected_event"]["event_id"], "kernel-1")
        self.assertEqual(metric["selected_event"]["category"], "kernel")
        self.assertEqual(metric["entity_identity_status"], "exact_match")
        self.assertTrue(metric["eligible_for_phase_join"])
        self.assertEqual(metric["causal_attribution"], "not_claimed")

    def test_bundle_level_window_reports_overlap_but_never_phase_joins(self):
        report = align_record(record(metric_window=False))
        metric = report["metric_alignments"][0]
        self.assertEqual(metric["metric_window_source"], "bundle_level_fallback")
        self.assertEqual(metric["alignment_status"], "metric_window_missing")
        self.assertGreater(metric["runtime_event_coverage_pct"], 0)
        self.assertFalse(metric["eligible_for_phase_join"])
        self.assertEqual(report["eligible_metric_phase_join_count"], 0)

    def test_entity_mismatch_prevents_phase_join(self):
        trace = runtime_trace(events=[
            {
                "event_id": "kernel-1", "name": "kernel", "category": "kernel",
                "started_at": "2026-11-13T10:00:01Z",
                "ended_at": "2026-11-13T10:00:05Z", "entity_id": "gpu1",
            }
        ])
        report = align_record(record(trace=trace))
        metric = report["metric_alignments"][0]
        self.assertEqual(metric["alignment_status"], "identity_or_scope_mismatch")
        self.assertEqual(metric["entity_identity_status"], "mismatch")
        self.assertFalse(metric["eligible_for_phase_join"])

    def test_per_kernel_counter_requires_kernel_event_and_exact_entity(self):
        report = align_record(record(metric_scope="per_kernel"))
        metric = report["metric_alignments"][0]
        self.assertTrue(metric["eligible_for_phase_join"])
        trace = runtime_trace(events=[
            {
                "event_id": "decode-1", "name": "decode", "category": "decode",
                "started_at": "2026-11-13T10:00:01Z",
                "ended_at": "2026-11-13T10:00:05Z", "entity_id": "gpu0",
            }
        ])
        metric = align_record(record(metric_scope="per_kernel", trace=trace))["metric_alignments"][0]
        self.assertEqual(metric["phase_join_reason"], "event_category_does_not_match_metric_scope")
        self.assertFalse(metric["eligible_for_phase_join"])

    def test_no_temporal_overlap_is_explicit(self):
        trace = runtime_trace(
            started_at="2026-11-13T10:01:00Z",
            ended_at="2026-11-13T10:01:10Z",
            events=[{
                "event_id": "decode-1", "name": "decode", "category": "decode",
                "started_at": "2026-11-13T10:01:01Z",
                "ended_at": "2026-11-13T10:01:09Z",
            }],
        )
        report = align_record(record(trace=trace))
        self.assertEqual(report["status"], "no_temporal_overlap")
        self.assertEqual(report["capture_alignment"]["overlap_seconds"], 0)
        self.assertEqual(report["metric_alignments"][0]["alignment_status"], "no_temporal_overlap")

    def test_partial_event_overlap_is_not_phase_attribution(self):
        trace = runtime_trace(events=[{
            "event_id": "prefill-1", "name": "prefill", "category": "prefill",
            "started_at": "2026-11-13T10:00:03Z",
            "ended_at": "2026-11-13T10:00:05Z", "entity_id": "gpu0",
        }])
        metric = align_record(record(trace=trace))["metric_alignments"][0]
        self.assertEqual(metric["alignment_status"], "partial_or_multiple_event_overlap")
        self.assertFalse(metric["eligible_for_phase_join"])

    def test_multiple_leaf_events_are_ambiguous(self):
        events = [
            {
                "event_id": "kernel-a", "name": "kernel A", "category": "kernel",
                "started_at": "2026-11-13T10:00:01Z",
                "ended_at": "2026-11-13T10:00:05Z", "entity_id": "gpu0",
            },
            {
                "event_id": "kernel-b", "name": "kernel B", "category": "kernel",
                "started_at": "2026-11-13T10:00:01Z",
                "ended_at": "2026-11-13T10:00:05Z", "entity_id": "gpu0",
            },
        ]
        metric = align_record(record(trace=runtime_trace(events=events)))["metric_alignments"][0]
        self.assertEqual(metric["alignment_status"], "ambiguous_multiple_leaf_events")
        self.assertFalse(metric["eligible_for_phase_join"])

    def test_capture_overlap_and_category_coverage_do_not_double_count(self):
        events = [
            {
                "event_id": "prefill-a", "name": "prefill A", "category": "prefill",
                "started_at": "2026-11-13T10:00:01Z",
                "ended_at": "2026-11-13T10:00:04Z",
            },
            {
                "event_id": "prefill-b", "name": "prefill B", "category": "prefill",
                "started_at": "2026-11-13T10:00:03Z",
                "ended_at": "2026-11-13T10:00:05Z",
            },
        ]
        report = align_record(record(trace=runtime_trace(events=events)))
        metric = report["metric_alignments"][0]
        self.assertEqual(metric["category_overlap"]["prefill"]["overlap_seconds"], 2)
        self.assertEqual(metric["category_overlap"]["prefill"]["overlap_pct"], 100)

    def test_runtime_trace_parent_must_contain_child(self):
        events = [
            {
                "event_id": "parent", "name": "prefill", "category": "prefill",
                "started_at": "2026-11-13T10:00:01Z",
                "ended_at": "2026-11-13T10:00:03Z",
            },
            {
                "event_id": "child", "name": "kernel", "category": "kernel",
                "started_at": "2026-11-13T10:00:02Z",
                "ended_at": "2026-11-13T10:00:04Z", "parent_event_id": "parent",
            },
        ]
        errors = validate_runtime_trace(runtime_trace(events=events), "test")
        self.assertTrue(any("child event must be contained" in error for error in errors))

    def test_metric_sampling_window_must_fit_hardware_capture(self):
        evidence = hardware_evidence()
        evidence["metrics"][0]["sampling_window"] = {
            "started_at": "2026-11-13T09:59:59Z",
            "ended_at": "2026-11-13T10:00:04Z",
        }
        errors = validate_hardware_evidence({"hardware_evidence": evidence}, "test")
        self.assertTrue(any("must be contained by hardware_evidence.sampling" in error for error in errors))

    def test_multiple_samples_of_same_counter_can_have_distinct_windows(self):
        evidence = hardware_evidence(metric_scope="per_kernel")
        second = dict(evidence["metrics"][0])
        second["value"] = 81
        second["sampling_window"] = {
            "started_at": "2026-11-13T10:00:05Z",
            "ended_at": "2026-11-13T10:00:07Z",
        }
        evidence["metrics"].append(second)
        errors = validate_hardware_evidence({"hardware_evidence": evidence}, "test")
        self.assertEqual(errors, [])
        report = align_record(record(evidence=evidence))
        self.assertEqual(len(report["metric_alignments"]), 2)
        self.assertEqual(report["eligible_metric_phase_join_count"], 1)

    def test_derived_counter_inputs_must_share_the_same_capture_window(self):
        evidence = hardware_evidence()
        evidence["metrics"].extend([
            {
                "metric_id": "compute_flop_count", "value": 1e12, "unit": "FLOP",
                "measurement_kind": "hardware_counter", "aggregation": "sum",
                "scope": "per_gpu", "source_name": "flop_count",
                "entity_id": "gpu0", "precision": "FP8", "sparsity": "dense",
                "sampling_window": {
                    "started_at": "2026-11-13T10:00:02Z",
                    "ended_at": "2026-11-13T10:00:04Z",
                },
            },
            {
                "metric_id": "achieved_flops", "value": 5e11, "unit": "FLOP/s",
                "measurement_kind": "derived", "aggregation": "mean",
                "scope": "per_gpu", "source_name": "derived_achieved_flops",
                "entity_id": "gpu0", "precision": "FP8", "sparsity": "dense",
                "formula": "compute_flop_count / measured_window_seconds",
                "input_metric_ids": ["compute_flop_count"],
                "sampling_window": {
                    "started_at": "2026-11-13T10:00:03Z",
                    "ended_at": "2026-11-13T10:00:05Z",
                },
            },
        ])
        errors = validate_hardware_evidence({"hardware_evidence": evidence}, "test")
        self.assertTrue(any("derived input compute_flop_count has no matching scope/entity/fabric" in error for error in errors))

    def test_naive_timestamps_and_unmapped_monotonic_clock_are_rejected(self):
        trace = runtime_trace(clock_domain="monotonic_ns")
        errors = validate_runtime_trace(trace, "test")
        self.assertTrue(any("clock_mapping is required for monotonic_ns" in error for error in errors))
        trace = runtime_trace()
        trace["events"][0]["started_at"] = "2026-11-13T10:00:01"
        errors = validate_runtime_trace(trace, "test")
        self.assertTrue(any("positive and timezone-aware" in error for error in errors))

    def test_monotonic_trace_maps_to_utc_with_explicit_two_anchor_clock_model(self):
        trace = runtime_trace(
            clock_domain="monotonic_ns",
            started_at=0,
            ended_at=10_000_000_000,
            events=[
                {
                    "event_id": "prefill-1", "name": "prefill", "category": "prefill",
                    "started_at": 1_000_000_000, "ended_at": 8_000_000_000,
                    "entity_id": "gpu0",
                },
                {
                    "event_id": "kernel-1", "name": "attention kernel", "category": "kernel",
                    "started_at": 1_999_000_000, "ended_at": 4_001_000_000,
                    "entity_id": "gpu0", "parent_event_id": "prefill-1",
                },
            ],
        )
        trace["clock_mapping"] = {
            "method": "piecewise_linear",
            "anchors": [
                {"monotonic_ns": 0, "utc_at": "2026-11-13T10:00:00Z"},
                {"monotonic_ns": 10_000_000_000, "utc_at": "2026-11-13T10:00:10Z"},
            ],
            "max_error_ns": 100_000,
        }
        errors = validate_runtime_trace(trace, "test")
        self.assertEqual(errors, [])
        report = align_record(record(trace=trace))
        metric = report["metric_alignments"][0]
        self.assertTrue(metric["eligible_for_phase_join"])
        self.assertEqual(metric["selected_event"]["event_id"], "kernel-1")
        self.assertEqual(report["capture_alignment"]["clock_mapping_method"], "piecewise_linear")
        self.assertEqual(report["capture_alignment"]["clock_mapping_max_error_ns"], 100_000)

    def test_monotonic_clock_mapping_does_not_extrapolate_outside_anchor_range(self):
        trace = runtime_trace(clock_domain="monotonic_ns", started_at=0, ended_at=11_000_000_000)
        trace["clock_mapping"] = {
            "method": "piecewise_linear",
            "anchors": [
                {"monotonic_ns": 1_000_000_000, "utc_at": "2026-11-13T10:00:01Z"},
                {"monotonic_ns": 10_000_000_000, "utc_at": "2026-11-13T10:00:10Z"},
            ],
            "max_error_ns": 0,
        }
        errors = validate_runtime_trace(trace, "test")
        self.assertTrue(any("lie within clock anchors" in error for error in errors))

    def test_clock_mapping_uncertainty_is_a_containment_guard_band(self):
        trace = runtime_trace(
            clock_domain="monotonic_ns",
            started_at=0,
            ended_at=10_000_000_000,
            events=[{
                "event_id": "kernel-1", "name": "kernel", "category": "kernel",
                "started_at": 2_000_000_000, "ended_at": 4_000_000_000,
                "entity_id": "gpu0",
            }],
        )
        trace["clock_mapping"] = {
            "method": "piecewise_linear",
            "anchors": [
                {"monotonic_ns": 0, "utc_at": "2026-11-13T10:00:00Z"},
                {"monotonic_ns": 10_000_000_000, "utc_at": "2026-11-13T10:00:10Z"},
            ],
            "max_error_ns": 1_000_000,
        }
        metric = align_record(record(trace=trace))["metric_alignments"][0]
        self.assertEqual(metric["alignment_status"], "partial_or_multiple_event_overlap")
        self.assertFalse(metric["eligible_for_phase_join"])
        self.assertEqual(metric["clock_mapping_uncertainty_seconds"], 0.001)

    def test_clock_anchors_must_be_strictly_monotonic(self):
        trace = runtime_trace(clock_domain="monotonic_ns", started_at=0, ended_at=10_000_000_000)
        trace["clock_mapping"] = {
            "method": "piecewise_linear",
            "anchors": [
                {"monotonic_ns": 0, "utc_at": "2026-11-13T10:00:00Z"},
                {"monotonic_ns": 0, "utc_at": "2026-11-13T10:00:10Z"},
            ],
            "max_error_ns": 0,
        }
        errors = validate_runtime_trace(trace, "test")
        self.assertTrue(any("monotonic_ns anchors must be strictly increasing" in error for error in errors))

    def test_parent_references_must_exist_and_cycles_are_rejected(self):
        events = [
            {
                "event_id": "a", "name": "a", "category": "prefill",
                "started_at": "2026-11-13T10:00:01Z",
                "ended_at": "2026-11-13T10:00:08Z", "parent_event_id": "b",
            },
            {
                "event_id": "b", "name": "b", "category": "decode",
                "started_at": "2026-11-13T10:00:01Z",
                "ended_at": "2026-11-13T10:00:08Z", "parent_event_id": "a",
            },
        ]
        errors = validate_runtime_trace(runtime_trace(events=events), "test")
        self.assertTrue(any("hierarchy contains a cycle" in error for error in errors))
        events[0]["parent_event_id"] = "missing"
        events[1].pop("parent_event_id")
        errors = validate_runtime_trace(runtime_trace(events=events), "test")
        self.assertTrue(any("unknown parent_event_id" in error for error in errors))

    def test_align_database_reports_coverage_without_fabricating_missing_data(self):
        rows = [
            record(),
            {"id": "without-trace", "hardware_evidence": hardware_evidence()},
            {"id": "without-hardware", "runtime_trace": runtime_trace()},
            {"id": "without-either"},
        ]
        report = align_database(rows)
        self.assertEqual(report["input_record_count"], 4)
        self.assertEqual(report["records_with_hardware_evidence"], 2)
        self.assertEqual(report["records_with_runtime_trace"], 2)
        self.assertEqual(report["records_with_overlapping_capture_windows"], 1)
        self.assertEqual(report["eligible_metric_phase_join_count"], 1)

    def test_metric_window_with_naive_time_is_rejected_without_type_error(self):
        evidence = hardware_evidence()
        evidence["metrics"][0]["sampling_window"]["started_at"] = "2026-11-13T10:00:02"
        errors = validate_hardware_evidence({"hardware_evidence": evidence}, "test")
        self.assertTrue(any("positive and timezone-aware" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
