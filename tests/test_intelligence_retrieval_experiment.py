"""Offline tests for isolated targeted arXiv retrieval experiments."""
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_intelligence_retrieval_experiment import run_experiment, validate_config, markdown_report


CONFIG = {
    "schema_version": "1.0",
    "experiment_id": "test-exp",
    "groups": [
        {"id": "gpu-comm", "name": "GPU communication", "query": "cat:cs.DC AND all:GPU", "max_results": 2},
        {"id": "agent-runtime", "name": "Agent runtime", "query": "cat:cs.AI AND all:agent", "max_results": 2},
    ],
}
DISCOVERY = {
    "generated_at": "2026-11-16T09:00:00Z",
    "lookback_days": 45,
    "source_results": [{"source_id": "arxiv-main", "kind": "arxiv_api", "status": "observed"}],
    "all_observations": [{
        "source_id": "arxiv-main", "candidate_type": "research_preprint",
        "candidate_id": "arxiv:2611.12345v1",
    }],
}
BASELINE = {
    "scorable": True, "eligible_count": 2,
    "rates": {"100": {"recall": 0.5}},
    "matched": [{"paper_id": "arxiv:2611.12345v1"}],
    "missing": [{"paper_id": "arxiv:2611.12346v1"}],
}


def atom(ids):
    entries = []
    for identifier in ids:
        entries.append(
            f"<entry><id>https://arxiv.org/abs/{identifier}</id>"
            "<title>LLM inference GPU communication paper</title>"
            "<published>2026-11-15T00:00:00Z</published>"
            "<updated>2026-11-15T00:00:00Z</updated>"
            "<summary>LLM inference uses GPU communication and KV cache.</summary></entry>"
        )
    return '<feed xmlns="http://www.w3.org/2005/Atom">' + "".join(entries) + "</feed>"


class RetrievalExperimentTests(unittest.TestCase):
    def test_config_bounds_group_count_query_size_and_page_size(self):
        validate_config(CONFIG)
        bad = {**CONFIG, "groups": [{**CONFIG["groups"][0], "max_results": 51}]}
        with self.assertRaisesRegex(ValueError, "1..50"):
            validate_config(bad)
        bad = {**CONFIG, "groups": [{**CONFIG["groups"][0], "query": "https://example.com"}]}
        with self.assertRaisesRegex(ValueError, "not a URL"):
            validate_config(bad)

    def test_incremental_hits_dedup_overlap_and_courtesy_delay(self):
        calls, delays = [], []

        def fetch(url):
            query = parse_qs(urlsplit(url).query)["search_query"][0]
            calls.append(query)
            if "GPU" in query:
                return atom(["2611.12346v1", "2611.12347v1"])
            return atom(["2611.12346v2", "2611.12348v1"])

        report = run_experiment(CONFIG, DISCOVERY, BASELINE, fetcher=fetch, sleep=delays.append)
        self.assertEqual(report["status"], "complete")
        self.assertTrue(report["scorable"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(delays, [3])
        self.assertEqual(report["summary"]["raw_returned_count"], 4)
        self.assertEqual(report["summary"]["unique_papers_across_groups"], 3)
        self.assertEqual(report["summary"]["cross_group_duplicate_count"], 1)
        self.assertEqual(report["summary"]["incremental_unique_papers"], 3)
        self.assertEqual(report["summary"]["incremental_known_seed_hits"], ["2611.12346"])
        self.assertEqual(report["summary"]["known_seed_hits_after"], 2)
        self.assertEqual(report["summary"]["known_seed_recall_after"], 1.0)
        self.assertTrue(report["groups"][0]["paging"]["paging_cap_reached"])
        self.assertIsNone(report["summary"]["measured_precision"])
        self.assertIn("not available", markdown_report(report))

    def test_failed_query_makes_experiment_partial_not_negative(self):
        calls, delays = [], []

        def fetch(url):
            query = parse_qs(urlsplit(url).query)["search_query"][0]
            calls.append(query)
            if "agent" in query:
                raise TimeoutError("synthetic timeout")
            return atom(["2611.12346v1"])

        report = run_experiment(CONFIG, DISCOVERY, BASELINE, fetcher=fetch, sleep=delays.append)
        self.assertEqual(report["status"], "partial")
        self.assertFalse(report["scorable"])
        self.assertEqual(report["groups"][1]["status"], "unavailable")
        self.assertEqual(report["groups"][1]["request_diagnostics"]["request_count"], 2)
        self.assertEqual(report["summary"]["successful_group_count"], 1)

    def test_unavailable_baseline_skips_without_network_calls(self):
        discovery = {
            **DISCOVERY,
            "source_results": [{"source_id": "arxiv-main", "kind": "arxiv_api", "status": "unavailable"}],
        }
        calls = []
        report = run_experiment(CONFIG, discovery, BASELINE, fetcher=lambda _: calls.append(1), sleep=lambda _: None)
        self.assertEqual(report["status"], "skipped")
        self.assertFalse(report["scorable"])
        self.assertEqual(calls, [])

    def test_unscorable_baseline_skips_without_network_calls(self):
        calls = []
        report = run_experiment(CONFIG, DISCOVERY, {**BASELINE, "scorable": False},
                                fetcher=lambda _: calls.append(1), sleep=lambda _: None)
        self.assertEqual(report["status"], "skipped")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
