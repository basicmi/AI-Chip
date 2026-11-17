import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_intelligence_review_ledger import load_decisions


NOW = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)


def decision(claim_id="claim-abc", **overrides):
    row = {
        "claim_id": claim_id,
        "decision": "needs_more_evidence",
        "reviewer": "maintainer@example",
        "decided_at": "2026-11-17T10:00:00Z",
        "notes": "Inspected the original source; exact SKU and configuration still need corroboration.",
    }
    row.update(overrides)
    return row


def ledger(*rows):
    return {"schema_version": "1.0", "decisions": list(rows)}


class ReviewLedgerValidationTests(unittest.TestCase):
    def test_empty_ledger_is_valid(self):
        self.assertEqual(load_decisions(ledger(), set(), NOW), {})

    def test_valid_decisions_are_normalized(self):
        result = load_decisions(
            ledger(decision(decided_at="2026-11-17T12:00:00+02:00")),
            {"claim-abc"}, NOW
        )
        self.assertEqual(result["claim-abc"]["decided_at"], "2026-11-17T10:00:00Z")
        self.assertEqual(result["claim-abc"]["reviewer"], "maintainer@example")

    def test_all_allowed_outcomes_are_accepted(self):
        rows = [
            decision("claim-a", decision="needs_more_evidence"),
            decision("claim-b", decision="rejected"),
            decision("claim-c", decision="accepted_for_evidence_attachment"),
        ]
        self.assertEqual(len(load_decisions(ledger(*rows), None, NOW)), 3)

    def test_unknown_claim_id_rejected_when_state_allowlist_supplied(self):
        with self.assertRaisesRegex(ValueError, "unknown Claim ID"):
            load_decisions(ledger(decision()), {"claim-other"}, NOW)

    def test_duplicate_claim_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_decisions(ledger(decision(), decision()), None, NOW)

    def test_invalid_or_non_slug_claim_ids_rejected(self):
        for claim_id in ("", "Claim-ABC", "../claim", "claim_id", "claim:abc"):
            with self.subTest(claim_id=claim_id), self.assertRaisesRegex(ValueError, "lowercase slug"):
                load_decisions(ledger(decision(claim_id)), None, NOW)

    def test_unknown_or_missing_top_level_fields_rejected(self):
        for payload in (
            {"schema_version": "1.0", "decisions": [], "status": "approved"},
            {"schema_version": "1.0"},
            {"schema_version": "2.0", "decisions": []},
            [],
        ):
            with self.subTest(payload=payload), self.assertRaisesRegex(ValueError, "schema 1.0"):
                load_decisions(payload, None, NOW)

    def test_unknown_or_missing_decision_fields_rejected(self):
        row = decision()
        row["extra"] = "not allowed"
        with self.assertRaisesRegex(ValueError, "exactly"):
            load_decisions(ledger(row), None, NOW)
        row = decision()
        row.pop("notes")
        with self.assertRaisesRegex(ValueError, "exactly"):
            load_decisions(ledger(row), None, NOW)

    def test_invalid_outcome_rejected(self):
        with self.assertRaisesRegex(ValueError, "outcome"):
            load_decisions(ledger(decision(decision="verified")), None, NOW)

    def test_reviewer_must_be_non_empty(self):
        for reviewer in ("", "  ", None, 123):
            with self.subTest(reviewer=reviewer), self.assertRaisesRegex(ValueError, "reviewer identity"):
                load_decisions(ledger(decision(reviewer=reviewer)), None, NOW)

    def test_notes_must_have_at_least_30_non_whitespace_characters(self):
        for notes in ("too short", " " * 50, None):
            with self.subTest(notes=notes), self.assertRaisesRegex(ValueError, "at least 30"):
                load_decisions(ledger(decision(notes=notes)), None, NOW)

    def test_invalid_naive_or_future_timestamps_rejected(self):
        for stamp in ("not-a-date", "2026-11-17T10:00:00", "2026-11-18T00:00:00Z"):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                load_decisions(ledger(decision(decided_at=stamp)), None, NOW)

    def test_validation_clock_must_be_timezone_aware(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            load_decisions(ledger(), None, datetime(2026, 11, 17))

    def test_cli_rejects_null_ledger_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ledger.json"
            path.write_text("null", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_intelligence_review_ledger.py"),
                 "--ledger", str(path)],
                cwd=ROOT, capture_output=True, text=True, check=False
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not null", result.stderr)

    def test_cli_validates_repository_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ledger.json"
            path.write_text(json.dumps(ledger()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_intelligence_review_ledger.py"),
                 "--ledger", str(path)],
                cwd=ROOT, capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS: validated 0", result.stdout)


if __name__ == "__main__":
    unittest.main()
