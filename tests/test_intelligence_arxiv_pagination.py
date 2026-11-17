"""Bounded arXiv paging, id deduplication, and raw-cap coverage audit."""
import json
import sys
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import parse_qs,urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_intelligence_discovery import (collect_arxiv,run_discovery, retry_after_seconds, bounded_retry)
from audit_intelligence_source_coverage import coverage_report
from validate_intelligence_sources import validate_registry

NOW=datetime(2026,11,14,12,tzinfo=timezone.utc)
SOURCE={"id":"arxiv-test","name":"Test arXiv query","kind":"arxiv_api",
        "active":True,"query":"all:GPU","max_results":2,"category":"research-preprint"}
MODEL={"models":[],"model_count":0,"observed":0,
       "new_publisher_candidates":[],"publisher_discovery_errors":[]}
def atom(ids,old_ids=()):
    entries=[]
    for identifier in ids:
        when="2026-01-01T00:00:00Z" if identifier in old_ids else "2026-11-13T00:00:00Z"
        entries.append(f"""<entry><id>https://arxiv.org/abs/{identifier}</id>
          <title>GPU inference paper {identifier}</title><published>{when}</published>
          <updated>{when}</updated><summary>GPU memory and LLM serving.</summary></entry>""")
    return '<feed xmlns="http://www.w3.org/2005/Atom">'+"".join(entries)+"</feed>"
def fetch_pages(pages):
    calls=[]
    def fetch(url):
        params=parse_qs(urlsplit(url).query)
        start=int(params["start"][0]);calls.append(start)
        content=pages.get(start,[])
        if isinstance(content,Exception):raise content
        return atom(content)
    return fetch,calls

class ArxivPaginationTests(unittest.TestCase):
    def test_curated_arxiv_queries_are_sharded_and_bounded(self):
        registry = json.loads((ROOT / "data/intelligence-sources.json").read_text(encoding="utf-8"))
        sources = [item for item in registry["sources"] if item["kind"] == "arxiv_api"]
        self.assertEqual(len(sources), 4)
        self.assertEqual({item["id"] for item in sources}, {
            "arxiv-ai-systems", "arxiv-ai-hardware",
            "arxiv-ai-kernels-compilers", "arxiv-agentic-physical-ai",
        })
        for source in sources:
            self.assertEqual(source["max_results"], 50)
            self.assertEqual(source["max_pages"], 2)
            self.assertEqual(source["max_attempts"], 2)
            query = source["query"]
            for term in ("all:compiler", "all:kernel", "all:inference", "all:serving",
                         "all:parallelism", 'all:"machine learning" OR',
                         'all:"deep learning" OR', 'all:"neural network" OR'):
                self.assertNotIn(term, query)
        by_id = {item["id"]: item["query"] for item in sources}
        self.assertIn('all:"LLM inference"', by_id["arxiv-ai-systems"])
        self.assertIn("all:HBM", by_id["arxiv-ai-hardware"])
        self.assertIn("all:CUDA", by_id["arxiv-ai-kernels-compilers"])
        self.assertIn('all:"agent runtime"', by_id["arxiv-agentic-physical-ai"])

    def test_registry_validates_arxiv_limits_against_collector(self):
        registry = json.loads((ROOT / "data/intelligence-sources.json").read_text(encoding="utf-8"))
        source = next(item for item in registry["sources"] if item["kind"] == "arxiv_api")
        original = dict(source)
        source["max_results"] = 101
        self.assertTrue(any("max_results" in error for error in validate_registry(registry, today=NOW.date())))
        source.clear()
        source.update(original)
        source["max_pages"] = 4
        self.assertTrue(any("max_pages" in error for error in validate_registry(registry, today=NOW.date())))
        source.clear()
        source.update(original)
        source["max_attempts"] = 0
        self.assertTrue(any("max_attempts" in error for error in validate_registry(registry, today=NOW.date())))

    def test_arxiv_source_max_pages_is_configurable(self):
        source = {**SOURCE, "max_pages": 1}
        fetch, calls = fetch_pages({0:["2611.00001", "2611.00002"]})
        diag = {}
        result = collect_arxiv(source, since=datetime(2026,10,1,tzinfo=timezone.utc),
                               fetcher=fetch, paging=diag, sleep=lambda _:None)
        self.assertEqual(len(result), 2)
        self.assertEqual(calls, [0])
        self.assertEqual(diag["pages_fetched"], 1)
        self.assertTrue(diag["paging_cap_reached"])

    def test_arxiv_shards_fail_independently_and_respect_spacing(self):
        sources = [
            {**SOURCE, "id":"arxiv-slow", "name":"Slow shard",
             "query":"cat:cs.DC", "max_pages":1, "max_attempts":2},
            {**SOURCE, "id":"arxiv-good", "name":"Working shard",
             "query":"cat:cs.AR", "max_pages":1, "max_attempts":2},
        ]
        calls = []
        sleeps = []
        def fetch(url):
            query = parse_qs(urlsplit(url).query)["search_query"][0]
            calls.append(query)
            if "cs.DC" in query:
                raise TimeoutError("synthetic arXiv timeout")
            return atom(["2611.00009"])
        state = {"schema_version":"1.0", "items":{}}
        report = run_discovery(
            {"sources":sources}, {"models":[]}, now=NOW,
            feed_fetcher=fetch, model_report=MODEL, state=state,
            retry_sleep=sleeps.append)
        self.assertEqual(report["sources_observed"], 1)
        self.assertEqual(report["sources_unavailable"], 1)
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["source_results"][0]["attempt_count"], 2)
        self.assertEqual(report["source_results"][0]["failure_category"], "timeout")
        self.assertEqual(report["source_results"][1]["status"], "observed")
        self.assertEqual(len(calls), 3)
        # One backoff retry plus one inter-query delay to respect arXiv's
        # request spacing even when a previous shard failed.
        self.assertEqual(sleeps, [3.0, 3])

    def test_reads_second_page_deduplicates_and_waits(self):
        fetch,calls=fetch_pages({0:["2611.00001","2611.00002"],
                                 2:["2611.00002","2611.00003"]})
        sleeps=[]
        diag={}
        result=collect_arxiv(SOURCE,since=datetime(2026,10,1,tzinfo=timezone.utc),
                             fetcher=fetch,paging=diag,sleep=sleeps.append)
        self.assertEqual(calls,[0,2,4])
        self.assertEqual(sleeps,[3,3])
        self.assertEqual(len(result),3)
        self.assertEqual(diag["raw_items_scanned"],4)
        self.assertEqual(diag["pages_fetched"],3)
        self.assertFalse(diag["paging_cap_reached"])
    def test_short_first_page_avoids_additional_requests(self):
        fetch,calls=fetch_pages({0:["2611.00001"]})
        diag={}
        out=collect_arxiv(SOURCE,since=datetime(2026,10,1,tzinfo=timezone.utc),
                          fetcher=fetch,paging=diag,sleep=lambda _:None)
        self.assertEqual(len(out),1)
        self.assertEqual(calls,[0])
        self.assertEqual(diag["pages_fetched"],1)
    def test_three_full_pages_flag_possible_truncation_even_when_recent_few(self):
        ids=["2611.00001","2611.00002","2611.00003","2611.00004","2611.00005","2611.00006"]
        def fetch(url):
            start=int(parse_qs(urlsplit(url).query)["start"][0])
            selected=ids[start:start+2]
            old=set(selected[1:])
            return atom(selected,old)
        diag={}
        out=collect_arxiv(SOURCE,since=datetime(2026,10,1,tzinfo=timezone.utc),
                          fetcher=fetch,paging=diag,sleep=lambda _:None)
        self.assertEqual(len(out),3)
        self.assertTrue(diag["paging_cap_reached"])
        self.assertEqual(diag["raw_items_scanned"],6)
        # Compare the metadata from the actual scanner result, without network.
        # Keeping each page below cap would mask this risk under the old audit.
    def test_arxiv_retry_uses_three_second_spacing(self):
        calls = []
        sleeps = []
        def fetch(url):
            calls.append(url)
            if len(calls) == 1:
                raise TimeoutError("synthetic timeout")
            return atom(["2611.00001"])
        state = {"schema_version": "1.0", "items": {}}
        report = run_discovery(
            {"sources": [SOURCE]}, {"models": []}, now=NOW,
            feed_fetcher=fetch, model_report=MODEL, state=state,
            retry_sleep=sleeps.append)
        row = report["source_results"][0]
        self.assertEqual(row["status"], "observed")
        self.assertEqual(row["attempt_count"], 2)
        self.assertEqual(sleeps, [3.0])
        self.assertEqual(row["request_diagnostics"]["request_count"], 2)
        self.assertEqual(row["request_diagnostics"]["failed_request_count"], 1)

    def test_subsequent_page_failure_fails_entire_source(self):
        def fetch(url):
            start=int(parse_qs(urlsplit(url).query)["start"][0])
            if start:raise ValueError("invalid arXiv feed at offset")
            return atom(["2611.00001","2611.00002"])
        state={"schema_version":"1.0","items":{}}
        # Avoid 3-second real sleeps by monkey-patching this controlled test
        import run_intelligence_discovery as mod
        original=mod.time.sleep
        mod.time.sleep=lambda _:None
        try:
            result=run_discovery({"sources":[SOURCE]},{"models":[]},now=NOW,
                feed_fetcher=fetch,model_report=MODEL,state=state)
        finally:
            mod.time.sleep=original
        self.assertEqual(result["sources_observed"],0)
        self.assertEqual(result["candidate_count"],0)
        self.assertEqual(result["source_results"][0]["status"],"unavailable")
        self.assertEqual(state["items"],{})
    def test_oversized_arxiv_page_fails_closed(self):
        def fetch(_):
            return atom(["2611.00001","2611.00002","2611.00003"])
        with self.assertRaisesRegex(ValueError,"more entries"):
            collect_arxiv(SOURCE,since=datetime(2026,10,1,tzinfo=timezone.utc),
                          fetcher=fetch,sleep=lambda _:None)
    def test_wrong_page_limit_rejected(self):
        source={**SOURCE,"max_results":101}
        with self.assertRaisesRegex(ValueError,"max_results"):
            collect_arxiv(source,since=datetime(2026,10,1,tzinfo=timezone.utc),
                          fetcher=lambda _:atom([]),sleep=lambda _:None)
    def test_audit_uses_raw_page_metadata_for_arxiv(self):
        from test_intelligence_source_coverage import fixtures
        registry,discovery=fixtures()
        row=next(x for x in discovery["source_results"] if x["source_id"]=="arxiv")
        row["pagination"]={"pages_fetched":3,"raw_items_scanned":6,
                           "paging_cap_reached":True,"max_pages":3,"per_page":2}
        report=coverage_report(registry,discovery)
        record=next(x for x in report["sources"] if x["source_id"]=="arxiv")
        self.assertTrue(record["possible_window_truncation"])
        row["pagination"]["pages_fetched"]=4
        with self.assertRaisesRegex(ValueError,"pagination diagnostics"):
            coverage_report(registry,discovery)

class RetryAfterTests(unittest.TestCase):
    @staticmethod
    def http_error(code, headers=None):
        import urllib.error
        return urllib.error.HTTPError(
            "https://export.arxiv.org/api/query", code, "synthetic", headers or {}, None
        )

    def test_retry_after_delta_seconds(self):
        error = self.http_error(429, {"Retry-After": "12"})
        self.assertEqual(retry_after_seconds(error, now=NOW), 12.0)

    def test_retry_after_http_date(self):
        import email.utils
        retry_at = NOW + timedelta(seconds=25)
        error = self.http_error(503, {"Retry-After": email.utils.format_datetime(retry_at, usegmt=True)})
        self.assertEqual(retry_after_seconds(error, now=NOW), 25.0)

    def test_bounded_retry_honors_server_retry_after(self):
        calls, sleeps = [], []
        def call():
            calls.append(1)
            if len(calls) == 1:
                raise self.http_error(429, {"Retry-After": "12"})
            return "ok"
        result, attempts = bounded_retry(call, attempts=2, sleep=sleeps.append, backoff_seconds=3)
        self.assertEqual((result, attempts), ("ok", 2))
        self.assertEqual(sleeps, [12.0])

    def test_rate_limit_without_header_uses_conservative_cooldown(self):
        calls, sleeps = [], []
        def call():
            calls.append(1)
            if len(calls) == 1:
                raise self.http_error(429)
            return "ok"
        bounded_retry(call, attempts=2, sleep=sleeps.append, backoff_seconds=3)
        self.assertEqual(sleeps, [30.0])

    def test_retry_after_beyond_budget_fails_without_early_retry(self):
        calls, sleeps = [], []
        def call():
            calls.append(1)
            raise self.http_error(429, {"Retry-After": "301"})
        with self.assertRaises(Exception):
            bounded_retry(call, attempts=3, sleep=sleeps.append, backoff_seconds=3)
        self.assertEqual(len(calls), 1)
        self.assertEqual(sleeps, [])

    def test_arxiv_cooldown_is_shared_across_query_shards(self):
        sources = [
            {**SOURCE, "id": "arxiv-limited", "name": "Rate limited",
             "query": "all:limited", "max_pages": 1, "max_attempts": 1},
            {**SOURCE, "id": "arxiv-next", "name": "Next shard",
             "query": "all:next", "max_pages": 1, "max_attempts": 1},
            {**SOURCE, "id": "arxiv-last", "name": "Last shard",
             "query": "all:last", "max_pages": 1, "max_attempts": 1},
        ]
        calls, sleeps, elapsed = [], [], [0.0]
        def fetch(url):
            query = parse_qs(urlsplit(url).query)["search_query"][0]
            calls.append(query)
            if query == "all:limited":
                import urllib.error
                raise self.http_error(429, {"Retry-After": "10"})
            return atom(["2611.00009"])
        def sleep(seconds):
            sleeps.append(seconds)
            elapsed[0] += seconds
        report = run_discovery(
            {"sources": sources}, {"models": []}, now=NOW,
            feed_fetcher=fetch, model_report=MODEL,
            state={"schema_version": "1.0", "items": {}},
            clock=lambda: elapsed[0], retry_sleep=sleep,
        )
        self.assertEqual(calls, ["all:limited", "all:next", "all:last"])
        self.assertEqual(sleeps, [10.0, 3])
        self.assertEqual(report["source_results"][0]["failure_category"], "http_rate_limit")
        self.assertEqual(report["source_results"][1]["status"], "observed")
        self.assertEqual(report["source_results"][2]["status"], "observed")

    def test_long_arxiv_cooldown_defers_remaining_shards(self):
        sources = [
            {**SOURCE, "id": "arxiv-limited", "query": "all:limited",
             "max_pages": 1, "max_attempts": 1},
            {**SOURCE, "id": "arxiv-next", "query": "all:next",
             "max_pages": 1, "max_attempts": 1},
            {**SOURCE, "id": "arxiv-last", "query": "all:last",
             "max_pages": 1, "max_attempts": 1},
        ]
        calls = []
        def fetch(url):
            query = parse_qs(urlsplit(url).query)["search_query"][0]
            calls.append(query)
            import urllib.error
            raise urllib.error.HTTPError(url, 429, "synthetic", {"Retry-After": "600"}, None)
        report = run_discovery(
            {"sources": sources}, {"models": []}, now=NOW,
            feed_fetcher=fetch, model_report=MODEL,
            state={"schema_version": "1.0", "items": {}},
            clock=lambda: 0.0, retry_sleep=lambda _: self.fail("must defer instead of waiting"),
        )
        self.assertEqual(calls, ["all:limited"])
        self.assertEqual(report["source_results"][1]["failure_category"], "rate_limit_cooldown_deferred")
        self.assertEqual(report["source_results"][2]["failure_category"], "rate_limit_cooldown_deferred")
        self.assertEqual(report["source_results"][1]["attempt_count"], 0)


if __name__=="__main__":unittest.main()
