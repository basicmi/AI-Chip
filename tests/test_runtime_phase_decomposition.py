import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from decompose_runtime_phases import decompose_database, decompose_record
from validate_benchmark_results import validate_runtime_trace


def event(event_id, category, start_ms, end_ms, *, parent="request-event",
          correlation=None, token_index=None):
    item = {
        "event_id": event_id,
        "name": event_id.replace("-", " "),
        "category": category,
        "started_at": iso_ms(start_ms),
        "ended_at": iso_ms(end_ms),
    }
    if parent is not None:
        item["parent_event_id"] = parent
    if correlation is not None:
        item["correlation_id"] = correlation
    if token_index is not None:
        item["token_index"] = token_index
    return item


def iso_ms(milliseconds):
    seconds = milliseconds / 1000
    whole = int(seconds)
    fraction = int(round((seconds - whole) * 1_000_000))
    return f"2026-11-13T10:00:{whole:02d}.{fraction:06d}Z"


def trace_for(events, *, clock_domain="utc_wall_clock", start_ms=0, end_ms=1000):
    if clock_domain == "utc_wall_clock":
        sampling = {"started_at": iso_ms(start_ms), "ended_at": iso_ms(end_ms)}
    else:
        sampling = {"started_at": start_ms * 1_000_000, "ended_at": end_ms * 1_000_000}
    trace = {
        "schema_version": "1.0",
        "collector": {"name": "Serving Runtime Trace", "version": "1.0", "type": "runtime_trace"},
        "clock_domain": clock_domain,
        "sampling": sampling,
        "provenance": {
            "source_type": "runtime_trace_export",
            "source_url": "https://example.com/runtime.json",
            "collected_at": "2026-11-13T10:01:00Z",
        },
        "events": events,
    }
    if clock_domain == "monotonic_ns":
        trace["clock_mapping"] = {
            "method": "piecewise_linear",
            "anchors": [
                {"monotonic_ns": start_ms * 1_000_000, "utc_at": iso_ms(start_ms)},
                {"monotonic_ns": end_ms * 1_000_000, "utc_at": iso_ms(end_ms)},
            ],
            "max_error_ns": 0,
        }
    return trace


def request_fixture(request_id="request-1", offset_ms=0):
    def e(event_id, category, start, end, **kwargs):
        return event(event_id, category, offset_ms + start, offset_ms + end, **kwargs)
    return [
        e("request-event", "request", 0, 200, parent=None, correlation=request_id),
        e("queue", "queue_wait", 0, 20),
        e("batch", "batch_wait", 20, 30),
        e("prefill", "prefill", 30, 50),
        e("kernel", "kernel", 35, 45, parent="prefill"),
        e("decode", "decode", 50, 100),
        e("communication", "communication", 75, 80, parent="decode"),
        e("host", "host_runtime", 80, 90),
        e("token-1", "token_emit", 50, 50, token_index=1),
        e("token-2", "token_emit", 75, 75, token_index=2),
        e("token-3", "token_emit", 100, 100, token_index=3),
    ]


def record(events, *, clock_domain="utc_wall_clock", start_ms=0, end_ms=1000):
    return {
        "id": "phase-fixture",
        "runtime_trace": trace_for(events, clock_domain=clock_domain, start_ms=start_ms, end_ms=end_ms),
    }


class RuntimePhaseDecompositionTests(unittest.TestCase):
    def test_ttft_tpot_and_phase_coverage_are_measured_from_token_markers(self):
        result = decompose_record(record(request_fixture(), end_ms=1000))
        self.assertEqual(result["status"], "decomposed")
        self.assertEqual(result["request_count"], 1)
        request = result["requests"][0]
        self.assertAlmostEqual(request["ttft_ms"], 50)
        self.assertAlmostEqual(request["tpot_ms"], 25)
        self.assertEqual(request["output_token_markers"], 3)
        self.assertTrue(request["token_index_complete"])
        ttft = request["ttft_phase_coverage"]
        self.assertEqual(ttft["primary_phase_coverage"]["queue_wait"], 20)
        self.assertEqual(ttft["primary_phase_coverage"]["batch_wait"], 10)
        self.assertEqual(ttft["primary_phase_coverage"]["prefill"], 20)
        self.assertEqual(ttft["primary_phase_union_ms"], 50)
        self.assertEqual(ttft["unclassified_gap_ms"], 0)
        self.assertEqual(ttft["subphase_coverage"]["kernel"], 10)
        tpot = request["tpot_phase_coverage"]
        self.assertEqual(tpot["primary_phase_coverage"]["decode"], 50)
        self.assertEqual(tpot["primary_phase_coverage"]["host_runtime"], 10)
        self.assertEqual(tpot["primary_phase_overlap_ms"], 10)
        self.assertEqual(tpot["primary_phase_union_ms"], 50)
        self.assertEqual(tpot["subphase_coverage"]["communication"], 5)

    def test_overlapping_primary_phases_are_not_double_counted_in_union(self):
        events = [
            event("request-event", "request", 0, 200, parent=None, correlation="r1"),
            event("prefill", "prefill", 0, 80),
            event("host", "host_runtime", 60, 100),
            event("token-1", "token_emit", 120, 120, token_index=1),
            event("token-2", "token_emit", 150, 150, token_index=2),
        ]
        request = decompose_record(record(events))["requests"][0]
        coverage = request["request_phase_coverage"]
        self.assertEqual(coverage["primary_phase_coverage"]["prefill"], 80)
        self.assertEqual(coverage["primary_phase_coverage"]["host_runtime"], 40)
        self.assertEqual(coverage["primary_phase_union_ms"], 100)
        self.assertEqual(coverage["primary_phase_overlap_ms"], 20)

    def test_multiple_requests_produce_trace_sample_distributions(self):
        first = request_fixture("r1")
        second = request_fixture("r2", 300)
        events = first + second
        result = decompose_record(record(events, end_ms=1000))
        self.assertEqual(result["request_count"], 2)
        self.assertEqual(result["ttft_ms"]["sample_count"], 2)
        self.assertEqual(result["ttft_ms"]["p50"], 50)
        self.assertEqual(result["tpot_ms"]["p95"], 25)
        self.assertEqual(result["phase_summary"]["ttft_phase_coverage"]["sample_count"], 2)

    def test_correlation_id_is_inherited_from_request_root(self):
        events = request_fixture()
        self.assertTrue(all("correlation_id" not in item for item in events[1:]))
        result = decompose_record(record(events))
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["requests"][0]["ttft_ms"], 50)

    def test_missing_token_markers_do_not_infer_ttft_or_tpot(self):
        events = [
            event("request-event", "request", 0, 200, parent=None, correlation="r1"),
            event("prefill", "prefill", 0, 100),
        ]
        request = decompose_record(record(events))["requests"][0]
        self.assertIsNone(request["ttft_ms"])
        self.assertIsNone(request["tpot_ms"])
        self.assertIsNone(request["ttft_phase_coverage"])
        self.assertTrue(any("no token_emit markers" in item for item in request["warnings"]))

    def test_token_index_gap_preserves_ttft_but_withholds_tpot(self):
        events = [
            event("request-event", "request", 0, 200, parent=None, correlation="r1"),
            event("token-1", "token_emit", 50, 50, token_index=1),
            event("token-3", "token_emit", 100, 100, token_index=3),
        ]
        request = decompose_record(record(events))["requests"][0]
        self.assertEqual(request["ttft_ms"], 50)
        self.assertIsNone(request["tpot_ms"])
        self.assertFalse(request["token_index_complete"])

    def test_missing_first_token_index_withholds_ttft(self):
        events = [
            event("request-event", "request", 0, 200, parent=None, correlation="r1"),
            event("token-2", "token_emit", 75, 75, token_index=2),
            event("token-3", "token_emit", 100, 100, token_index=3),
        ]
        request = decompose_record(record(events))["requests"][0]
        self.assertIsNone(request["ttft_ms"])
        self.assertIsNone(request["tpot_ms"])

    def test_non_increasing_token_times_withhold_tpot(self):
        events = [
            event("request-event", "request", 0, 200, parent=None, correlation="r1"),
            event("token-1", "token_emit", 50, 50, token_index=1),
            event("token-2", "token_emit", 40, 40, token_index=2),
        ]
        request = decompose_record(record(events))["requests"][0]
        self.assertEqual(request["ttft_ms"], 50)
        self.assertIsNone(request["tpot_ms"])
        self.assertTrue(any("not strictly increasing" in item for item in request["warnings"]))

    def test_duplicate_request_roots_are_rejected(self):
        events = [
            event("request-a", "request", 0, 100, parent=None, correlation="r1"),
            event("request-b", "request", 100, 200, parent=None, correlation="r1"),
        ]
        with self.assertRaisesRegex(ValueError, "duplicate request root"):
            decompose_record(record(events))

    def test_trace_without_request_events_is_explicit(self):
        events = [event("prefill", "prefill", 10, 50, parent=None)]
        result = decompose_record(record(events))
        self.assertEqual(result["status"], "no_request_events")
        self.assertEqual(result["request_count"], 0)

    def test_missing_trace_is_not_inferred(self):
        result = decompose_record({"id": "no-trace"})
        self.assertEqual(result["status"], "missing_runtime_trace")
        self.assertEqual(result["request_count"], 0)

    def test_monotonic_trace_is_mapped_to_utc_before_decomposition(self):
        events = [
            event("request-event", "request", 0, 200, parent=None, correlation="r1"),
            event("token-1", "token_emit", 50, 50, token_index=1),
            event("token-2", "token_emit", 100, 100, token_index=2),
        ]
        for item in events:
            for key in ("started_at", "ended_at"):
                utc_value = item[key]
                from datetime import datetime, timezone
                parsed = datetime.fromisoformat(utc_value.replace("Z", "+00:00"))
                origin = datetime.fromisoformat("2026-11-13T10:00:00+00:00")
                item[key] = int((parsed - origin).total_seconds() * 1_000_000_000)
        result = decompose_record(record(events, clock_domain="monotonic_ns", end_ms=1000))
        self.assertEqual(result["requests"][0]["ttft_ms"], 50)
        self.assertEqual(result["requests"][0]["tpot_ms"], 50)
        self.assertEqual(result["clock_mapping_method"], "piecewise_linear")

    def test_validator_accepts_instantaneous_token_emit_but_not_other_point_events(self):
        trace = trace_for([
            event("request-event", "request", 0, 200, parent=None, correlation="r1"),
            event("token-1", "token_emit", 50, 50, token_index=1),
        ])
        self.assertEqual(validate_runtime_trace(trace, "test"), [])
        trace["events"][1]["category"] = "decode"
        errors = validate_runtime_trace(trace, "test")
        self.assertTrue(any("event interval must be positive" in error for error in errors))

    def test_validator_requires_token_index_and_request_correlation(self):
        trace = trace_for([
            event("request-event", "request", 0, 200, parent=None),
            event("token-1", "token_emit", 50, 50),
        ])
        errors = validate_runtime_trace(trace, "test")
        self.assertTrue(any("correlation_id is required for request events" in error for error in errors))
        self.assertTrue(any("token_index must be a positive integer" in error for error in errors))

    def test_database_decomposition_preserves_missing_trace_coverage(self):
        result = decompose_database([
            {"id": "with-trace", "runtime_trace": trace_for(request_fixture())},
            {"id": "without-trace"},
            {"id": "without-request", "runtime_trace": trace_for([
                event("prefill", "prefill", 10, 50, parent=None)
            ])},
        ])
        self.assertEqual(result["input_record_count"], 3)
        self.assertEqual(result["records_with_request_events"], 1)
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["records"][1]["status"], "missing_runtime_trace")
        self.assertEqual(result["records"][2]["status"], "no_request_events")


if __name__ == "__main__":
    unittest.main()
