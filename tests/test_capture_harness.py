import json, sqlite3, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_capture_harness import build_capture_bundle, write_bundle
from validate_benchmark_results import validate_hardware_evidence, validate_runtime_trace

BASE_NS = 1794528000000000000
TRACE_ID = "0123456789abcdef0123456789abcdef"
ROOT_ID = "0123456789abcdef"

def kv(key, value):
    kind = "stringValue" if isinstance(value, str) else "intValue"
    return {"key": key, "value": {kind: value}}

def otel_fixture():
    def span(sid, name, start, end, kind="SPAN_KIND_INTERNAL", parent=None):
        item = {"traceId": TRACE_ID, "spanId": sid, "name": name, "kind": kind,
                "startTimeUnixNano": str(BASE_NS + start), "endTimeUnixNano": str(BASE_NS + end),
                "attributes": [], "events": []}
        if parent: item["parentSpanId"] = parent
        return item
    return {"resourceSpans": [{"resource": {"attributes": [kv("service.name", "vllm")]},
        "scopeSpans": [{"scope": {"name": "test"}, "spans": [
            span(ROOT_ID, "POST /v1/chat/completions", 0, 10_000_000_000, "SPAN_KIND_SERVER"),
            span("1111111111111111", "queue wait", 100_000_000, 1_000_000_000, parent=ROOT_ID),
        ]}]}]}

def dcgm_fixture():
    def row(name, value): return name + '{gpu="0",UUID="GPU-abc"} ' + str(value)
    return {"schema_version": "1.0", "source_format": "dcgm_exporter_prometheus_text",
        "snapshots": [
            {"captured_at": "2026-11-13T00:00:00Z", "body": row("DCGM_FI_DEV_BOARD_POWER_WATTS", 220)},
            {"captured_at": "2026-11-13T00:00:01Z", "body": row("DCGM_FI_DEV_BOARD_POWER_WATTS", 240)}]}

def nsys_fixture(path):
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE StringIds (id INTEGER, value TEXT)")
        db.execute("INSERT INTO StringIds VALUES (1, 'test_kernel')")
        db.execute("CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL (start INTEGER, end INTEGER, deviceId INTEGER, contextId INTEGER, streamId INTEGER, correlationId INTEGER, globalPid INTEGER, shortName INTEGER)")
        db.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (100000000, 200000000, 0, 3, 7, 11, 123 << 24, 1)")
        db.commit()
    finally: db.close()

class CaptureHarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.otel = self.root / "trace.json"; self.otel.write_text(json.dumps(otel_fixture()))
        self.dcgm = self.root / "dcgm.json"; self.dcgm.write_text(json.dumps(dcgm_fixture()))
        self.nsys = self.root / "nsys.sqlite"; nsys_fixture(self.nsys)
        self.anchors = {"method": "piecewise_linear", "anchors": [
            {"monotonic_ns": 0, "utc_at": "2026-11-13T00:00:00Z"},
            {"monotonic_ns": 500000000, "utc_at": "2026-11-13T00:00:00.500Z"}], "max_error_ns": 0}

    def test_three_layer_bundle_emits_valid_artifacts_and_coarse_alignments(self):
        outputs, report = build_capture_bundle(run_id="trial-001", otel_json=self.otel,
            otel_source_url="https://trace.example/trace/1", nsys_sqlite=self.nsys,
            nsys_source_url="https://profiler.example/session.sqlite", clock_anchors=self.anchors,
            dcgm_capture=self.dcgm, dcgm_source_url="https://artifacts.example/dcgm.json",
            device_model="RTX 3090")
        self.assertEqual(report["status"], "complete")
        self.assertEqual(set(report["layers_available"]), {"opentelemetry_runtime", "nsight_systems", "nvidia_dcgm"})
        self.assertEqual(report["summary"]["otel_request_records"], 1)
        self.assertEqual(report["summary"]["nsys_utc_trace_records"], 1)
        self.assertEqual(report["summary"]["dcgm_gpu_records"], 1)
        self.assertEqual(report["summary"]["runtime_dcgm_pairs"], 1)
        self.assertEqual(report["summary"]["nsys_dcgm_pairs"], 1)
        self.assertEqual(outputs["runtime-dcgm-alignment.json"]["eligible_metric_phase_join_count"], 0)
        self.assertEqual(outputs["nsight-dcgm-alignment.json"]["eligible_metric_phase_join_count"], 0)
        trace = outputs["runtime-traces.json"]["records"][0]["runtime_trace"]
        self.assertEqual(validate_runtime_trace(trace, "test"), [])
        evidence = outputs["dcgm-hardware-evidence.json"]["records"][0]["hardware_evidence"]
        self.assertEqual(validate_hardware_evidence({"hardware_evidence": evidence}, "test"), [])

    def test_nsys_without_anchors_is_retained_but_not_utc_aligned(self):
        outputs, report = build_capture_bundle(run_id="trial-raw", nsys_sqlite=self.nsys,
            nsys_source_url="https://profiler.example/session.sqlite", dcgm_capture=self.dcgm,
            dcgm_source_url="https://artifacts.example/dcgm.json")
        self.assertEqual(report["summary"]["nsys_events"], 1)
        self.assertEqual(report["summary"]["nsys_utc_trace_records"], 0)
        self.assertNotIn("nsight-dcgm-alignment.json", outputs)
        self.assertTrue(any("clock anchors" in item for item in report["warnings"]))

    def test_alignment_pair_limit_fails_closed(self):
        payload = json.loads(self.otel.read_text())
        second_root = dict(payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0])
        second_root["spanId"] = "2222222222222222"
        second_root["startTimeUnixNano"] = str(BASE_NS + 20_000_000_000)
        second_root["endTimeUnixNano"] = str(BASE_NS + 30_000_000_000)
        payload["resourceSpans"][0]["scopeSpans"][0]["spans"].append(second_root)
        two_requests = self.root / "two-requests.json"
        two_requests.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "alignment would create"):
            build_capture_bundle(run_id="trial-limit", otel_json=two_requests,
                otel_source_url="https://trace.example/trace/1", nsys_sqlite=self.nsys,
                nsys_source_url="https://profiler.example/session.sqlite", clock_anchors=self.anchors,
                dcgm_capture=self.dcgm, dcgm_source_url="https://artifacts.example/dcgm.json",
                max_alignment_pairs=1)

    def test_rejects_empty_input_and_unsafe_run_id(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            build_capture_bundle(run_id="trial-empty")
        with self.assertRaisesRegex(ValueError, "run_id"):
            build_capture_bundle(run_id="../bad", nsys_sqlite=self.nsys,
                nsys_source_url="https://profiler.example/session.sqlite")

    def test_output_manifest_and_no_overwrite_default(self):
        outputs, report = build_capture_bundle(run_id="trial-write", otel_json=self.otel,
            otel_source_url="https://trace.example/trace/1")
        target = self.root / "bundle"
        final = write_bundle(target, outputs, report)
        saved = json.loads((target / "capture-report.json").read_text())
        self.assertEqual(saved["artifacts"], final["artifacts"])
        self.assertTrue(all((target / item["file"]).is_file() for item in final["artifacts"]))
        with self.assertRaises(FileExistsError): write_bundle(target, outputs, report)

if __name__ == "__main__": unittest.main()
