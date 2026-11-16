"""PR #106: per-source live request telemetry and fail-closed audit validation."""
import sys
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from run_intelligence_discovery import run_discovery
from audit_intelligence_source_coverage import coverage_report, markdown_report

NOW=datetime(2026,11,16,12,tzinfo=timezone.utc)
SOURCE={"id":"test-feed","name":"Test RSS","active":True,"kind":"rss_atom",
        "publisher":"Test","category":"vendor-announcement","feed_url":"https://example.org/feed"}
XML=b"""<rss><channel><item><title>GPU inference release</title>
<link>https://example.org/item</link><pubDate>Sun, 15 Nov 2026 10:00:00 GMT</pubDate>
<description>Inference and HBM performance update.</description></item></channel></rss>"""
MODEL={"models":[],"model_count":0,"observed":0,
       "new_publisher_candidates":[],"publisher_discovery_errors":[]}

def scan(fetcher, *, clock=None, retry_sleep=lambda _:None):
    return run_discovery({"sources":[SOURCE]},{"models":[]},now=NOW,
        feed_fetcher=fetcher,model_report=MODEL,
        state={"schema_version":"1.0","items":{}},
        clock=clock or (lambda:0.0),retry_sleep=retry_sleep)

class RequestDiagnosticsTests(unittest.TestCase):
    def test_success_records_latency_and_payload_bytes_without_url(self):
        values=iter([1.0,1.125])
        report=scan(lambda _:XML,clock=lambda:next(values))
        row=report["source_results"][0]
        metrics=row["request_diagnostics"]
        self.assertEqual(metrics["request_count"],1)
        self.assertEqual(metrics["failed_request_count"],0)
        self.assertEqual(metrics["response_bytes"],len(XML))
        self.assertEqual(metrics["total_elapsed_ms"],125.0)
        self.assertEqual(metrics["average_request_ms"],125.0)
        self.assertEqual(metrics["max_request_ms"],125.0)
        self.assertNotIn("url",metrics)
    def test_retry_attempts_and_http_failure_are_counted(self):
        calls=[]
        sleeps=[]
        values=iter([0.0,0.01,1.0,1.04])
        def fetch(_):
            calls.append(1)
            if len(calls)==1:
                raise urllib.error.HTTPError("https://example.org/feed",503,"Unavailable",{},None)
            return XML
        report=scan(fetch,clock=lambda:next(values),retry_sleep=sleeps.append)
        metrics=report["source_results"][0]["request_diagnostics"]
        self.assertEqual(len(calls),2)
        self.assertEqual(sleeps,[0.2])
        self.assertEqual(metrics["request_count"],2)
        self.assertEqual(metrics["failed_request_count"],1)
        self.assertEqual(metrics["last_http_error_status"],503)
        self.assertEqual(metrics["last_request_failure_category"],"http_server_error")
        self.assertEqual(report["source_results"][0]["attempt_count"],2)
    def test_parse_failure_is_not_misreported_as_http_failure(self):
        report=scan(lambda _:b"<rss><channel>")
        row=report["source_results"][0]
        self.assertEqual(row["status"],"unavailable")
        self.assertEqual(row["failure_category"],"parse_error")
        self.assertEqual(row["request_diagnostics"]["request_count"],1)
        self.assertEqual(row["request_diagnostics"]["failed_request_count"],0)
        self.assertIsNone(row["request_diagnostics"]["last_http_error_status"])
    def test_http_404_is_captured_without_exposing_url_or_body(self):
        def fail(_):
            raise urllib.error.HTTPError("https://example.org/feed?token=secret",404,"Not found",{},None)
        report=scan(fail)
        metrics=report["source_results"][0]["request_diagnostics"]
        self.assertEqual(metrics["request_count"],1)
        self.assertEqual(metrics["failed_request_count"],1)
        self.assertEqual(metrics["last_http_error_status"],404)
        self.assertNotIn("secret",str(metrics))
        self.assertNotIn("example.org",str(metrics))
    def test_coverage_audit_aggregates_runtime_diagnostics(self):
        from test_intelligence_source_coverage import fixtures
        registry,discovery=fixtures()
        for row in discovery["source_results"]:
            row["request_diagnostics"]={
                "request_count":2,"failed_request_count":1,"response_bytes":1200,
                "total_elapsed_ms":6000.0,"average_request_ms":3000.0,
                "max_request_ms":5000.0,"last_http_error_status":503,
                "last_request_failure_category":"http_server_error"}
        result=coverage_report(registry,discovery)
        self.assertEqual(result["summary"]["total_requests"],6)
        self.assertEqual(result["summary"]["failed_requests"],3)
        self.assertEqual(result["summary"]["response_bytes"],3600)
        self.assertEqual(result["summary"]["sources_with_slow_request_over_5s"],3)
        markdown=markdown_report(result)
        self.assertIn("Per-source runtime diagnostics",markdown)
        self.assertIn("HTTP requests / failed requests: 6 / 3",markdown)
    def test_coverage_rejects_inconsistent_request_totals(self):
        from test_intelligence_source_coverage import fixtures
        registry,discovery=fixtures()
        discovery["source_results"][0]["request_diagnostics"]={
            "request_count":1,"failed_request_count":2,"response_bytes":10,
            "total_elapsed_ms":1.0,"average_request_ms":1.0,
            "max_request_ms":1.0,"last_http_error_status":None,
            "last_request_failure_category":None}
        with self.assertRaisesRegex(ValueError,"failed request count"):
            coverage_report(registry,discovery)
    def test_legacy_discovery_reports_remain_supported(self):
        from test_intelligence_source_coverage import fixtures
        registry,discovery=fixtures()
        result=coverage_report(registry,discovery)
        self.assertEqual(result["summary"]["total_requests"],0)
        self.assertIsNone(result["sources"][0]["request_diagnostics"])

if __name__=="__main__":unittest.main()
