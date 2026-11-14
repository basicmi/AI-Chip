import copy
import socket
import sys
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_intelligence_discovery import (
    bounded_retry, failure_category, retryable, fetch_bytes, run_discovery
)

NOW=datetime(2026,11,14,12,tzinfo=timezone.utc)
SOURCE={"id":"test-feed","name":"Test vendor RSS","active":True,
        "kind":"rss_atom","publisher":"Test Vendor",
        "category":"vendor-announcement","feed_url":"https://example.org/feed"}
XML=b"""<rss><channel><item><title>GPU memory product launch</title>
<link>https://example.org/article</link><pubDate>Fri, 13 Nov 2026 10:00:00 GMT</pubDate>
<description>180 GB HBM memory.</description></item></channel></rss>"""
MODEL={"models":[],"model_count":0,"observed":0,
       "new_publisher_candidates":[],"publisher_discovery_errors":[]}

def discover(fetcher, state):
    return run_discovery({"sources":[SOURCE]},{"models":[]},now=NOW,
        model_report=MODEL,feed_fetcher=fetcher,state=state)

class SourceRecoveryTests(unittest.TestCase):
    def test_timeout_retries_with_bounded_backoff(self):
        attempts=[]
        sleeps=[]
        def failing_then_success():
            attempts.append(1)
            if len(attempts)<3: raise TimeoutError("synthetic outage")
            return "ok"
        value,count=bounded_retry(failing_then_success,sleep=sleeps.append)
        self.assertEqual((value,count),("ok",3))
        self.assertEqual(sleeps,[0.2,0.4])
    def test_invalid_payload_not_retried(self):
        calls=[]
        def fail():
            calls.append(1)
            raise ValueError("bad feed")
        with self.assertRaises(ValueError):
            bounded_retry(fail,sleep=lambda _:None)
        self.assertEqual(len(calls),1)
        self.assertEqual(failure_category(ValueError("x")),"invalid_payload")
    def test_http_404_not_retried_but_429_and_503_retry(self):
        def http(code):
            return urllib.error.HTTPError("https://example.org/feed",code,"HTTP status",{},None)
        self.assertFalse(retryable(http(404)))
        self.assertTrue(retryable(http(429)))
        self.assertTrue(retryable(http(503)))
        self.assertEqual(failure_category(http(429)),"http_rate_limit")
        self.assertEqual(failure_category(http(404)),"http_client_error")
    def test_empty_feed_is_success_not_failure(self):
        state={"schema_version":"1.0","items":{}}
        result=discover(lambda _:b"<rss><channel></channel></rss>",state)
        self.assertEqual(result["source_results"][0]["status"],"observed")
        self.assertEqual(result["source_results"][0]["recent_item_count"],0)
        self.assertEqual(result["source_health_summary"]["empty_successes"],1)
        self.assertEqual(result["sources_unavailable"],0)
    def test_consecutive_outages_and_recovery_persist_across_runs(self):
        state={"schema_version":"1.0","items":{}}
        def outage(_): raise ValueError("malformed feed")
        for day in range(3):
            result=run_discovery({"sources":[SOURCE]},{"models":[]},
                 now=NOW.replace(day=14+day),model_report=MODEL,feed_fetcher=outage,state=state)
            self.assertEqual(result["source_results"][0]["consecutive_failures"],day+1)
        self.assertEqual(result["source_results"][0]["failure_tier"],"critical")
        self.assertEqual(result["errors"][0]["failure_category"],"invalid_payload")
        result=run_discovery({"sources":[SOURCE]},{"models":[]},
                 now=NOW.replace(day=18),model_report=MODEL,
                 feed_fetcher=lambda _:XML,state=state)
        self.assertEqual(result["source_results"][0]["health_transition"],"recovered")
        self.assertEqual(result["source_results"][0]["consecutive_failures"],0)
        self.assertEqual(state["source_health"]["test-feed"]["consecutive_failures"],0)
        self.assertEqual(result["sources_observed"],1)
    def test_partial_failure_does_not_discard_other_source(self):
        second={**SOURCE,"id":"good","feed_url":"https://example.org/good"}
        def fetch(url):
            if url.endswith("feed"):raise ValueError("invalid XML")
            return XML
        state={"schema_version":"1.0","items":{}}
        report=run_discovery({"sources":[SOURCE,second]},{"models":[]},now=NOW,
             model_report=MODEL,feed_fetcher=fetch,state=state)
        self.assertEqual(report["sources_observed"],1)
        self.assertEqual(report["source_results"][0]["status"],"unavailable")
        self.assertEqual(report["source_results"][1]["status"],"observed")
        self.assertEqual(report["source_results"][1]["recent_item_count"],1)
        self.assertEqual(len(report["review_queue"]),1)
    def test_failure_labels_exclude_credentials_and_urls(self):
        err=urllib.error.URLError("private-token-query=secret")
        self.assertEqual(failure_category(err),"network")
    def test_rejects_invalid_retry_budget(self):
        with self.assertRaisesRegex(ValueError,"attempts"):
            bounded_retry(lambda:None,attempts=0)

if __name__=="__main__": unittest.main()
