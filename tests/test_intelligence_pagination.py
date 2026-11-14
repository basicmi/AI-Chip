"""PR #104: bounded GitHub release pagination and coverage completeness regression."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_intelligence_discovery import collect_releases,run_discovery
from audit_intelligence_source_coverage import coverage_report

NOW=datetime(2026,11,14,12,tzinfo=timezone.utc)
SOURCE={"id":"github-test","name":"Test project","kind":"github_releases",
        "active":True,"repo":"example/test","category":"runtime"}
MODEL={"models":[],"model_count":0,"observed":0,
       "new_publisher_candidates":[],"publisher_discovery_errors":[]}

def release(tag,when="2026-11-12T00:00:00Z"):
    return {"tag_name":tag,"name":tag,"published_at":when,
            "updated_at":when,"html_url":"https://github.com/example/test/releases/tag/"+tag,
            "body":"GPU inference memory improvement","draft":False,"prerelease":False}

def pages(mapping):
    calls=[]
    def fetch(url):
        page=int(parse_qs(urlsplit(url).query)["page"][0])
        calls.append(page)
        result=mapping.get(page,[])
        if isinstance(result,Exception):raise result
        return result
    return fetch,calls

class PaginationTests(unittest.TestCase):
    def test_page_two_is_retrieved_without_duplicate_release(self):
        fetch,calls=pages({1:[release("v"+str(i)) for i in range(20)],
                           2:[release("v19"),release("v20"),release("v21")]})
        diag={}
        found=collect_releases(SOURCE,since=datetime(2026,10,1,tzinfo=timezone.utc),
                               fetcher=fetch,paging=diag)
        self.assertEqual(calls,[1,2])
        self.assertEqual(len(found),22)
        self.assertEqual(diag["pages_fetched"],2)
        self.assertFalse(diag["paging_cap_reached"])
        self.assertEqual(diag["raw_items_scanned"],23)
    def test_full_third_page_warns_even_when_few_results_in_window(self):
        old="2026-01-01T00:00:00Z"
        fetch,calls=pages({i:[release(f"v{i}-{j}",old if j else "2026-11-13T00:00:00Z")
                             for j in range(20)] for i in (1,2,3)})
        diag={}
        found=collect_releases(SOURCE,since=datetime(2026,10,1,tzinfo=timezone.utc),
                               fetcher=fetch,paging=diag)
        self.assertEqual(calls,[1,2,3])
        self.assertEqual(len(found),3)
        self.assertTrue(diag["paging_cap_reached"])
        report=run_discovery({"sources":[SOURCE]},{"models":[]},now=NOW,
                             release_fetcher=fetch,model_report=MODEL,
                             state={"schema_version":"1.0","items":{}})
        self.assertEqual(report["source_results"][0]["pagination"]["raw_items_scanned"],60)
        result=coverage_report({"schema_version":"1.0","sources":[SOURCE]},report)
        self.assertEqual(result["summary"]["potentially_truncated_sources"],1)
        self.assertEqual(result["sources"][0]["recent_item_count"],3)
    def test_short_first_page_stops_immediately(self):
        fetch,calls=pages({1:[release("v1")]})
        diag={}
        found=collect_releases(SOURCE,since=datetime(2026,10,1,tzinfo=timezone.utc),
                               fetcher=fetch,paging=diag)
        self.assertEqual(calls,[1])
        self.assertEqual(len(found),1)
        self.assertEqual(diag["pages_fetched"],1)
    def test_later_page_failure_does_not_checkpoint_partial_source(self):
        fetch,calls=pages({1:[release("v"+str(i)) for i in range(20)],
                           2:ValueError("synthetic malformed release response")})
        state={"schema_version":"1.0","items":{}}
        report=run_discovery({"sources":[SOURCE]},{"models":[]},now=NOW,
                             release_fetcher=fetch,model_report=MODEL,state=state)
        self.assertEqual(report["sources_observed"],0)
        self.assertEqual(report["source_results"][0]["status"],"unavailable")
        self.assertEqual(report["candidate_count"],0)
        self.assertEqual(state["items"],{})
    def test_oversized_page_is_invalid_payload(self):
        fetch,calls=pages({1:[release("v"+str(i)) for i in range(21)]})
        with self.assertRaisesRegex(ValueError,"oversized"):
            collect_releases(SOURCE,since=datetime(2026,10,1,tzinfo=timezone.utc),fetcher=fetch)
    def test_full_third_page_without_more_page_is_not_claimed_complete(self):
        fetch,calls=pages({i:[release(f"v{i}-{j}") for j in range(20)] for i in (1,2,3)})
        diag={}
        found=collect_releases(SOURCE,since=datetime(2026,10,1,tzinfo=timezone.utc),
                               fetcher=fetch,paging=diag)
        self.assertEqual(len(found),60)
        self.assertTrue(diag["paging_cap_reached"])
        self.assertEqual(max(calls),3)
    def test_invalid_pagination_diagnostics_rejected(self):
        registry={"schema_version":"1.0","sources":[SOURCE]}
        fetch,calls=pages({1:[release("v1")]})
        report=run_discovery(registry,{"models":[]},now=NOW,release_fetcher=fetch,
                             model_report=MODEL,state={"schema_version":"1.0","items":{}})
        report["source_results"][0]["pagination"]["pages_fetched"]=99
        with self.assertRaisesRegex(ValueError,"pagination diagnostics"):
            coverage_report(registry,report)

if __name__=="__main__":unittest.main()
