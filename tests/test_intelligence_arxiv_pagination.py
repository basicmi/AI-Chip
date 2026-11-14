"""Bounded arXiv paging, id deduplication, and raw-cap coverage audit."""
import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import parse_qs,urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_intelligence_discovery import collect_arxiv,run_discovery
from audit_intelligence_source_coverage import coverage_report

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
if __name__=="__main__":unittest.main()
