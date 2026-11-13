import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_intelligence_discovery import (
    collect_arxiv, collect_rss_atom, run_discovery, build_evidence_review_packet,
)
from validate_intelligence_sources import validate_registry

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)

RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>New GPU inference stack</title><link>https://vendor.example/news/gpu</link>
<guid>gpu-1</guid><pubDate>Thu, 12 Nov 2026 10:00:00 GMT</pubDate>
<description><![CDATA[<p>New HBM and inference features.</p>]]></description></item>
<item><title>Old item</title><link>https://vendor.example/old</link>
<pubDate>Thu, 01 Jan 2026 10:00:00 GMT</pubDate></item>
<item><title>Missing date</title><link>https://vendor.example/missing</link></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><id>https://arxiv.org/abs/2611.01234</id><title>GPU Systems for LLM Serving</title>
<updated>2026-11-12T10:00:00Z</updated><published>2026-11-12T09:00:00Z</published>
<summary>We study GPU memory bandwidth and inference scheduling.</summary>
<author><name>A. Researcher</name></author>
<category term="cs.DC"/></entry></feed>"""

class IntelligenceFeedTests(unittest.TestCase):
    def test_registry_accepts_all_supported_source_types(self):
        registry = json.loads((ROOT / "data/intelligence-sources.json").read_text())
        self.assertEqual(validate_registry(registry, today=NOW.date()), [])
        kinds = {source["kind"] for source in registry["sources"]}
        self.assertEqual(kinds, {"github_releases", "rss_atom", "arxiv_api"})

    def test_rss_parser_filters_old_and_undated_items(self):
        source = {"id":"vendor-feed","name":"Vendor feed","publisher":"Vendor",
                  "category":"vendor-announcement","feed_url":"https://vendor.example/feed"}
        items = collect_rss_atom(source, since=datetime(2026, 10, 1, tzinfo=timezone.utc),
                                 fetcher=lambda _: RSS)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["title"], "New GPU inference stack")
        self.assertEqual(item["publisher"], "Vendor")
        self.assertEqual(item["topic_tags"], ["accelerator", "inference", "memory"])
        self.assertEqual(item["review_status"], "requires_human_review")

    def test_atom_parser_extracts_authors_categories_and_abstract(self):
        source = {"id":"research","name":"arXiv research","publisher":"arXiv",
                  "category":"research-preprint","query":"all:GPU","max_results":20}
        items = collect_arxiv(source, since=datetime(2026, 10, 1, tzinfo=timezone.utc),
                              fetcher=lambda _: ATOM)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://arxiv.org/abs/2611.01234")
        self.assertEqual(items[0]["authors"], ["A. Researcher"])
        self.assertEqual(items[0]["categories"], ["cs.DC"])
        self.assertEqual(items[0]["peer_review_status"], "not_verified")
        self.assertIn("GPU memory bandwidth", items[0]["excerpt"])

    def test_run_continues_when_one_feed_fails(self):
        registry = {"sources":[
            {"id":"bad","name":"Broken feed","kind":"rss_atom","active":True,"feed_url":"https://bad.example/feed"},
            {"id":"good","name":"Working feed","kind":"rss_atom","active":True,"publisher":"Vendor",
             "category":"vendor-announcement","feed_url":"https://vendor.example/feed"},
        ]}
        def fetcher(url):
            if "bad.example" in url:
                raise TimeoutError()
            return RSS
        report = run_discovery(registry, {"models":[]}, now=NOW, feed_fetcher=fetcher,
                               model_report={"models":[],"model_count":0,"observed":0,
                                             "new_publisher_candidates":[],"publisher_discovery_errors":[]},
                               state={"schema_version":"1.0","items":{}})
        self.assertEqual(report["sources_observed"], 1)
        self.assertEqual(report["sources_unavailable"], 1)
        self.assertEqual(len(report["review_queue"]), 1)
        self.assertTrue(report["read_only"])

    def test_review_packet_has_evidence_and_manual_gates(self):
        report = run_discovery({"sources":[]}, {"models":[]}, now=NOW,
                               model_report={"models":[],"model_count":0,"observed":0,
                                             "new_publisher_candidates":[]},
                               state={"schema_version":"1.0","items":{}})
        packet = build_evidence_review_packet(report)
        self.assertIn("Evidence-to-PR protocol", packet)
        self.assertIn("No production registry is modified automatically", packet)
        self.assertIn("Review queue", packet)

if __name__ == "__main__":
    unittest.main()
