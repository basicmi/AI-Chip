#!/usr/bin/env python3
"""Validate the human intelligence review decision ledger.

The ledger records workflow decisions only. It never proves technical truth,
changes a company profile, or promotes a Claim to verified status.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DECISIONS = {
    "needs_more_evidence",
    "rejected",
    "accepted_for_evidence_attachment",
}
CLAIM_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("decided_at must be a timezone-aware ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("decided_at must be a valid ISO-8601 timestamp") from error
    if parsed.utcoffset() is None:
        raise ValueError("decided_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_decisions(ledger, allowed_ids=None, now=None):
    """Return normalized decisions keyed by Claim ID; fail closed on bad input."""
    if ledger is None:
        return {}
    if (not isinstance(ledger, dict) or set(ledger) != {"schema_version", "decisions"}
            or ledger.get("schema_version") != "1.0"
            or not isinstance(ledger.get("decisions"), list)):
        raise ValueError("human review decision ledger must be schema 1.0 with exactly schema_version and decisions")

    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("validation time must be timezone-aware")
    now = now.astimezone(timezone.utc)

    result = {}
    for decision in ledger["decisions"]:
        required = {"claim_id", "decision", "reviewer", "decided_at", "notes"}
        if not isinstance(decision, dict) or set(decision) != required:
            raise ValueError("human decision must contain exactly claim_id, decision, reviewer, decided_at and notes")
        claim_id = decision["claim_id"]
        if not isinstance(claim_id, str) or not CLAIM_ID.fullmatch(claim_id):
            raise ValueError("human decision Claim ID must be a lowercase slug")
        if allowed_ids is not None and claim_id not in allowed_ids:
            raise ValueError("human decision references unknown Claim ID: " + claim_id)
        if claim_id in result:
            raise ValueError("duplicate human decision Claim ID: " + claim_id)
        if not isinstance(decision["decision"], str) or decision["decision"] not in DECISIONS:
            raise ValueError("invalid human decision outcome for " + claim_id)
        reviewer = decision["reviewer"]
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("human reviewer identity required for " + claim_id)
        notes = decision["notes"]
        if not isinstance(notes, str) or len(notes.strip()) < 30:
            raise ValueError("human review notes must have at least 30 characters for " + claim_id)
        decided = parse_timestamp(decision["decided_at"])
        if decided > now:
            raise ValueError("human decision cannot be future-dated: " + claim_id)
        result[claim_id] = {
            "claim_id": claim_id,
            "decision": decision["decision"],
            "reviewer": reviewer.strip(),
            "decided_at": iso(decided),
            "notes": notes.strip(),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=Path("data/intelligence-review-decisions.json"))
    parser.add_argument("--review-state", type=Path,
                        help="Optional persisted review-state JSON; if supplied, every Claim ID must exist in its items.")
    args = parser.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        if ledger is None:
            raise ValueError("ledger file must contain a schema 1.0 object, not null")
        allowed_ids = None
        if args.review_state:
            state = json.loads(args.review_state.read_text(encoding="utf-8"))
            if (not isinstance(state, dict) or state.get("schema_version") != "1.0"
                    or not isinstance(state.get("items"), dict)):
                raise ValueError("review state must be schema 1.0 with an items mapping")
            allowed_ids = set(state["items"])
        decisions = load_decisions(ledger, allowed_ids)
        print("PASS: validated " + str(len(decisions)) + " human review decisions.")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
