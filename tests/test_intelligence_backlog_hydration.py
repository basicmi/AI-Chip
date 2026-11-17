"""Offline tests for historical Claim payload recovery."""
import io
import json
import sys
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hydrate_intelligence_review_backlog import hydrate_state

NOW = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)


def claim(claim_id, candidate_id, statement):
    return {
        "claim_id": claim_id, "candidate_id": candidate_id,
        "claim_type": "performance_result", "assertion_class": "research_result_candidate",
        "topic": "performance",
        "relevance": {"class": "direct_ai_compute", "matched_signals": ["gpu"]},
        "statement": statement, "value": 123, "unit": "tokens/s",
        "scope": {"status": "not_explicitly_stated", "text": None}, "qualifiers": [],
        "source": {
            "candidate_id": candidate_id, "source_id": "example-source",
            "source_name": "Example source", "publisher": "Example",
            "source_type": "vendor_primary", "independence": "not_independent",
            "url": "https://example.org/" + claim_id,
            "published_at": "2026-11-16T00:00:00Z",
            "evidence_scope": "vendor_primary_statement",
        },
        "evidence_class": "vendor_primary_statement", "evidence_quote": statement,
        "extraction": {"method": "deterministic_rules_v4", "confidence": "low", "requires_semantic_review": True},
        "review_status": "unverified_candidate",
        "review_gates": ["Verify the original source and exact configuration."],
    }


def artifact_bytes():
    claims = [
        claim("claim-a", "candidate-a", "Example accelerator reaches 123 tokens/s."),
        claim("claim-b", "candidate-b", "Example GPU supports a new memory mode."),
    ]
    discovery = {
        "schema_version": "1.1", "generated_at": "2026-11-16T10:00:00Z",
        "review_queue": [
            {"candidate_id": "candidate-a", "change_status": "new"},
            {"candidate_id": "candidate-b", "change_status": "updated"},
        ],
    }
    claim_report = {
        "schema_version": "1.0", "generated_at": discovery["generated_at"],
        "claim_count": len(claims), "claims": claims,
    }
    graph = {
        "schema_version": "1.0", "generated_at": discovery["generated_at"],
        "input_claim_count": len(claims), "summary": {"independently_verified_claims": 0},
        "nodes": [{"type": "claim_candidate", "claim_id": row["claim_id"]} for row in claims],
        "scoped_comparisons": [],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ai-chip-intelligence-discovery.json", json.dumps(discovery))
        archive.writestr("ai-chip-intelligence-claims.json", json.dumps(claim_report))
        archive.writestr("ai-chip-intelligence-evidence-graph.json", json.dumps(graph))
    return buffer.getvalue()


def state_with(ids):
    return {
        "schema_version": "1.0", "last_run_at": "2026-11-16T10:00:00Z",
        "items": {
            claim_id: {"first_seen_at": "2026-11-16T10:00:00Z", "last_seen_at": "2026-11-16T10:00:00Z"}
            for claim_id in ids
        },
    }


class HistoricalBacklogHydrationTests(unittest.TestCase):
    manifest = [{"artifact_id": 123, "run_id": 456}]

    def test_recovers_payload_and_recomputes_priority_without_decisions(self):
        state = state_with(["claim-a", "claim-b"])
        payload, calls = artifact_bytes(), []
        def fetcher(repo, artifact_id, token):
            calls.append((repo, artifact_id, token))
            return payload
        report, changed = hydrate_state(
            state, repo="basicmi/AI-Chip", token="test-token",
            fetcher=fetcher, artifact_manifest=self.manifest, now=NOW,
        )
        self.assertTrue(changed)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["recovered_claim_count"], 2)
        self.assertEqual(report["hydrated_item_count"], 2)
        self.assertEqual(report["claim_payloads_missing"], 0)
        self.assertEqual(calls, [("basicmi/AI-Chip", 123, "test-token")])
        self.assertIn("Example accelerator", state["items"]["claim-a"]["claim_snapshot"]["statement"])
        self.assertGreater(state["items"]["claim-a"]["score"], 0)
        self.assertFalse(state["items"]["claim-a"]["priority"]["score_is_truth_confidence"])
        self.assertEqual(state["items"]["claim-a"]["first_seen_at"], "2026-11-16T10:00:00Z")
        self.assertEqual(state["backlog_hydration"]["status"], "complete")

    def test_reports_state_ids_that_have_no_recovered_payload(self):
        state = state_with(["claim-a", "claim-b", "claim-missing"])
        report, changed = hydrate_state(
            state, repo="basicmi/AI-Chip", token="test-token",
            fetcher=lambda *_: artifact_bytes(),
            artifact_manifest=self.manifest, now=NOW,
        )
        self.assertTrue(changed)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["missing_claim_ids"], ["claim-missing"])
        self.assertEqual(report["claim_payloads_available"], 2)

    def test_skips_network_when_every_item_is_already_hydrated(self):
        state = state_with(["claim-a"])
        state["items"]["claim-a"]["claim_snapshot"] = {"claim_id": "claim-a", "statement": "already here"}
        report, changed = hydrate_state(
            state, repo="basicmi/AI-Chip", token="test-token",
            fetcher=lambda *_: self.fail("should not download artifacts"),
            artifact_manifest=self.manifest, now=NOW,
        )
        self.assertFalse(changed)
        self.assertEqual(report["status"], "skipped_already_hydrated")

    def test_skips_empty_cache_without_network(self):
        state = {"schema_version": "1.0", "items": {}}
        report, changed = hydrate_state(
            state, repo="basicmi/AI-Chip", token="test-token",
            fetcher=lambda *_: self.fail("should not download artifacts"),
            artifact_manifest=self.manifest, now=NOW,
        )
        self.assertFalse(changed)
        self.assertEqual(report["status"], "skipped_empty_state")

    def test_network_failure_leaves_cache_unchanged(self):
        state = state_with(["claim-a"])
        before = json.dumps(state, sort_keys=True)
        report, changed = hydrate_state(
            state, repo="basicmi/AI-Chip", token="test-token",
            fetcher=lambda *_: (_ for _ in ()).throw(TimeoutError("synthetic timeout")),
            artifact_manifest=self.manifest, now=NOW,
        )
        self.assertFalse(changed)
        self.assertEqual(report["status"], "unavailable")
        self.assertEqual(json.dumps(state, sort_keys=True), before)


if __name__ == "__main__":
    unittest.main()
