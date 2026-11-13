import http.client
import json
import os
import stat
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from collect_otel_http import create_server
from process_otel_captures import assemble_captures
from decompose_runtime_phases import decompose_database

TRACE = "0123456789abcdef0123456789abcdef"
ROOT = "0123456789abcdef"
BASE = 1794564000000000000


def span(sid, name, start, end, *, kind=1, parent="", events=None):
    result = {"traceId": TRACE, "spanId": sid, "name": name, "kind": kind,
              "startTimeUnixNano": str(BASE + start), "endTimeUnixNano": str(BASE + end),
              "events": events or []}
    if parent:
        result["parentSpanId"] = parent
    return result


def batch(spans):
    return {"resourceSpans": [{"resource": {"attributes": [
        {"key": "service.name", "value": {"stringValue": "vllm"}}]},
        "scopeSpans": [{"spans": spans}]}]}


def token(n, t):
    return {"name": "token_emit", "timeUnixNano": str(BASE + t),
            "attributes": [{"key": "token_index", "value": {"intValue": str(n)}}]}


def post(port, body, *, kind="application/json", auth=None, path="/v1/traces"):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"Content-Type": kind}
    if auth:
        headers["Authorization"] = auth
    connection.request("POST", path, body, headers=headers)
    response = connection.getresponse()
    status = response.status
    result = json.loads(response.read())
    connection.close()
    return status, result


class LiveOTLPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / "captures"
        self.server = create_server("127.0.0.1", 0, self.directory, max_body=4096)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def test_split_batches_are_durable_and_assembled_into_request(self):
        one = batch([span(ROOT, "POST /v1/completions", 0, 5_000_000_000, kind=2,
                          events=[token(1, 2_000_000_000), token(2, 3_000_000_000)])])
        two = batch([span("1111111111111111", "model prefill", 500_000_000, 2_000_000_000, parent=ROOT)])
        self.assertEqual(post(self.server.server_port, json.dumps(one).encode())[0], 200)
        self.assertEqual(post(self.server.server_port, json.dumps(two).encode())[0], 200)
        files = list(self.directory.glob("otlp-*.json"))
        self.assertEqual(len(files), 2)
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(files[0].stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o700)
        normalized = assemble_captures(self.directory, source_url="https://trace.example/1")
        self.assertEqual(normalized["capture_batch_count"], 2)
        self.assertEqual(len(normalized["records"]), 1)
        self.assertEqual(len(normalized["records"][0]["runtime_trace"]["events"]), 4)
        request = decompose_database({"records": normalized["records"]})["records"][0]["requests"][0]
        self.assertEqual(request["ttft_ms"], 2000)
        self.assertEqual(request["tpot_ms"], 1000)

    def test_rejects_non_json_protobuf_missing_schema_and_oversize(self):
        port = self.server.server_port
        self.assertEqual(post(port, b"{invalid")[0], 400)
        self.assertEqual(post(port, b"proto", kind="application/x-protobuf")[0], 415)
        self.assertEqual(post(port, json.dumps({"x": 1}).encode())[0], 400)
        self.assertEqual(post(port, b"x" * 4097)[0], 413)
        self.assertEqual(post(port, b"{}", path="/wrong")[0], 404)
        self.assertEqual(list(self.directory.glob("otlp-*.json")), [])

    def test_quota_rejects_without_deleting(self):
        other = Path(self.tmp.name) / "small"
        server = create_server("127.0.0.1", 0, other, file_limit=1)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            body = json.dumps(batch([])).encode()
            self.assertEqual(post(server.server_port, body)[0], 200)
            self.assertEqual(post(server.server_port, body)[0], 507)
            self.assertEqual(len(list(other.glob("otlp-*.json"))), 1)
        finally:
            server.shutdown()
            server.server_close()

    def test_remote_listener_requires_optin_and_bearer_token(self):
        with self.assertRaisesRegex(ValueError, "non-loopback"):
            create_server("0.0.0.0", 0, Path(self.tmp.name) / "remote")
        with self.assertRaisesRegex(ValueError, "bearer token"):
            create_server("0.0.0.0", 0, Path(self.tmp.name) / "remote", allow_remote=True)

    def test_bearer_token_rejects_unauthorized(self):
        other = Path(self.tmp.name) / "auth"
        server = create_server("127.0.0.1", 0, other, token="secret")
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            body = json.dumps(batch([])).encode()
            self.assertEqual(post(server.server_port, body)[0], 401)
            self.assertEqual(post(server.server_port, body, auth="Bearer wrong")[0], 401)
            self.assertEqual(post(server.server_port, body, auth="Bearer secret")[0], 200)
            self.assertEqual(len(list(other.glob("otlp-*.json"))), 1)
        finally:
            server.shutdown()
            server.server_close()

    def test_health_endpoint(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.request("GET", "/healthz")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.read()), {"status": "ok"})
        conn.close()


if __name__ == "__main__":
    unittest.main()
