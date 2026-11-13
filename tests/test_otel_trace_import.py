import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from decompose_runtime_phases import decompose_database
from import_otel_traces import import_otlp_json
from validate_benchmark_results import validate_runtime_trace

TRACE_ID = "0123456789abcdef0123456789abcdef"
ROOT_ID = "0123456789abcdef"
BASE_NS = 1794564000000000000


def kv(key, value):
    kind = "stringValue" if isinstance(value, str) else "intValue"
    return {"key": key, "value": {kind: value}}


def span(span_id, name, start, end, *, parent="", kind="SPAN_KIND_INTERNAL", attrs=None, events=None):
    item = {
        "traceId": TRACE_ID, "spanId": span_id, "name": name, "kind": kind,
        "startTimeUnixNano": str(BASE_NS + start), "endTimeUnixNano": str(BASE_NS + end),
        "attributes": [kv(k, v) for k, v in (attrs or {}).items()], "events": events or [],
    }
    if parent:
        item["parentSpanId"] = parent
    return item


def token(index, offset):
    return {"name": "token_emit", "timeUnixNano": str(BASE_NS + offset),
            "attributes": [kv("token_index", index)]}


def otlp(spans, service="vllm"):
    return {"resourceSpans": [{
        "resource": {"attributes": [kv("service.name", service), kv("service.version", "0.12.0")]},
        "scopeSpans": [{"scope": {"name": "vllm"}, "spans": spans}],
    }]}


class OTelTraceImportTests(unittest.TestCase):
    def test_imports_request_phases_and_explicit_token_markers_into_existing_analyzer(self):
        result = import_otlp_json(otlp([
            span(ROOT_ID, "POST /v1/chat/completions", 0, 10_000_000_000,
                 kind="SPAN_KIND_SERVER", events=[token(1, 3_000_000_000), token(2, 4_000_000_000)]),
            span("1111111111111111", "queue wait", 100_000_000, 1_000_000_000, parent=ROOT_ID),
            span("2222222222222222", "model prefill", 1_000_000_000, 3_000_000_000, parent=ROOT_ID),
            span("3333333333333333", "unmapped internal span", 4_000_000_000, 5_000_000_000, parent=ROOT_ID),
        ]), source_url="https://jaeger.example/trace/" + TRACE_ID)
        trace = result["records"][0]["runtime_trace"]
        self.assertEqual(validate_runtime_trace(trace, "test"), [])
        categories = {e["name"]: e["category"] for e in trace["events"]}
        self.assertEqual(categories["queue wait"], "queue_wait")
        self.assertEqual(categories["model prefill"], "prefill")
        self.assertEqual(categories["unmapped internal span"], "other")
        report = decompose_database({"records": result["records"]})
        request = report["records"][0]["requests"][0]
        self.assertEqual(request["ttft_ms"], 3000)
        self.assertEqual(request["tpot_ms"], 1000)
        self.assertEqual(request["critical_path"]["status"], "not_attested")

    def test_aggregate_latency_attributes_do_not_create_token_markers(self):
        result = import_otlp_json(otlp([
            span(ROOT_ID, "POST /v1/completions", 0, 5_000_000_000,
                 kind="SPAN_KIND_SERVER", attrs={
                     "gen_ai.usage.completion_tokens": 12,
                     "gen_ai.latency.time_to_first_token": 0.25,
                 }),
            span("1111111111111111", "model decode", 250_000_000, 4_000_000_000, parent=ROOT_ID),
        ]), source_url="https://jaeger.example/trace/" + TRACE_ID)
        trace = result["records"][0]["runtime_trace"]
        self.assertFalse(any(e["category"] == "token_emit" for e in trace["events"]))
        request = decompose_database({"records": result["records"]})["records"][0]["requests"][0]
        self.assertIsNone(request["ttft_ms"])
        self.assertIsNone(request["tpot_ms"])

    def test_explicit_category_attribute_and_exact_name_map_override_heuristics(self):
        result = import_otlp_json(otlp([
            span(ROOT_ID, "server", 0, 5_000_000_000, kind="SPAN_KIND_SERVER"),
            span("1111111111111111", "model prefill", 1_000_000_000, 2_000_000_000,
                 parent=ROOT_ID, attrs={"ai_chip.runtime.category": "decode"}),
            span("2222222222222222", "custom stage", 2_000_000_000, 3_000_000_000, parent=ROOT_ID),
        ]), source_url="https://jaeger.example/trace/" + TRACE_ID,
            category_map={"custom stage": "communication"})
        categories = {e["name"]: e["category"] for e in result["records"][0]["runtime_trace"]["events"]}
        self.assertEqual(categories["model prefill"], "decode")
        self.assertEqual(categories["custom stage"], "communication")

    def test_service_filter_selects_root_service_and_keeps_cross_service_descendants(self):
        source = {"resourceSpans": [
            {"resource":{"attributes":[kv("service.name","vllm")]},
             "scopeSpans":[{"spans":[span(ROOT_ID,"request",0,5_000_000_000,kind="SPAN_KIND_SERVER")]}]},
            {"resource":{"attributes":[kv("service.name","worker")]},
             "scopeSpans":[{"spans":[span("1111111111111111","worker prefill",1_000_000_000,2_000_000_000,parent=ROOT_ID)]}]},
        ]}
        result = import_otlp_json(source, source_url="https://jaeger.example/trace/" + TRACE_ID, service_name="vllm")
        self.assertEqual(len(result["records"][0]["runtime_trace"]["events"]), 2)

    def test_root_name_regex_selects_non_server_vllm_root(self):
        result = import_otlp_json(otlp([
            span(ROOT_ID, "vllm request lifecycle", 0, 5_000_000_000),
            span("1111111111111111", "model execute", 1_000_000_000, 2_000_000_000, parent=ROOT_ID),
        ]), source_url="https://tempo.example/trace/" + TRACE_ID, root_span_name=r"vllm request lifecycle")
        self.assertEqual(result["records"][0]["runtime_trace"]["events"][0]["category"], "request")

    def test_fails_closed_when_no_request_root_is_selected(self):
        with self.assertRaisesRegex(ValueError, "no request roots found"):
            import_otlp_json(otlp([span(ROOT_ID, "client call", 0, 5_000_000_000)]),
                             source_url="https://jaeger.example/trace/" + TRACE_ID)

    def test_invalid_token_event_is_skipped_not_fabricated(self):
        result = import_otlp_json(otlp([
            span(ROOT_ID, "server", 0, 5_000_000_000, kind="SPAN_KIND_SERVER",
                 events=[{"name":"token_emit","timeUnixNano":str(BASE_NS+1_000_000_000),"attributes":[]}]),
        ]), source_url="https://jaeger.example/trace/" + TRACE_ID)
        self.assertEqual(result["diagnostics"]["counts"]["token_events_skipped_without_valid_index"], 1)
        self.assertFalse(any(e["category"] == "token_emit" for e in result["records"][0]["runtime_trace"]["events"]))


if __name__ == "__main__":
    unittest.main()
