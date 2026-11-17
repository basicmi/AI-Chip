#!/usr/bin/env python3
"""Build a deterministic, bounded human-review batch from persistent Claim state.

This creates a review packet and an empty decision template. It never records
decisions, changes the decision ledger, or promotes a Claim to verified status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DECISIONS = ("needs_more_evidence", "rejected", "accepted_for_evidence_attachment")


def parse_utc(value):
    if not isinstance(value, str):
        raise ValueError("Claim first_seen_at must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid Claim first_seen_at: " + value) from error
    if parsed.tzinfo is None:
        raise ValueError("Claim first_seen_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def build_review_batch(review_state, *, batch_size=25):
    if type(batch_size) is not int or not 1 <= batch_size <= 100:
        raise ValueError("batch_size must be 1..100")
    if not isinstance(review_state, dict) or review_state.get("schema_version") != "1.0":
        raise ValueError("expected review-state schema 1.0")
    if review_state.get("observation_state") != "cache_persisted" or review_state.get("state_is_approval") is not False:
        raise ValueError("review state must be a persisted observation, not an approval")
    summary = review_state.get("summary")
    rows = review_state.get("aging_backlog")
    if not isinstance(summary, dict) or not isinstance(rows, list):
        raise ValueError("review state requires summary and aging_backlog")
    ids = [row.get("claim_id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or any(not isinstance(cid, str) or not cid for cid in ids) or len(set(ids)) != len(ids):
        raise ValueError("aging_backlog Claim IDs must be unique and non-empty")
    expected = summary.get("unresolved_backlog")
    if expected is not None and expected != len(rows):
        raise ValueError("unresolved backlog count does not match aging_backlog")
    counts = summary.get("review_states")
    if isinstance(counts, dict):
        expected_unresolved = counts.get("pending", 0) + counts.get("needs_more_evidence", 0)
        if expected_unresolved != len(rows):
            raise ValueError("review-state counts do not match aging_backlog")

    pending, follow_up, missing = [], [], []
    for row in rows:
        state = row.get("review_state")
        if state not in ("pending", "needs_more_evidence"):
            raise ValueError("aging_backlog may contain only unresolved review states")
        snapshot = row.get("claim_snapshot")
        if not isinstance(snapshot, dict):
            missing.append(row["claim_id"])
            continue
        if snapshot.get("claim_id") != row["claim_id"]:
            raise ValueError("Claim snapshot ID does not match review-state ID")
        statement = snapshot.get("statement")
        source = snapshot.get("source")
        if not isinstance(statement, str) or not statement.strip():
            missing.append(row["claim_id"])
            continue
        if not isinstance(source, dict) or not isinstance(source.get("url"), str) or not source["url"].startswith(("https://", "http://")):
            missing.append(row["claim_id"])
            continue
        priority = row.get("priority") if isinstance(row.get("priority"), dict) else {}
        score = priority.get("score", row.get("last_priority_score", 0))
        if type(score) not in (int, float):
            score = 0
        parse_utc(row.get("first_seen_at"))
        age_days = row.get("days_since_first_seen", 0)
        if type(age_days) is not int or age_days < 0:
            raise ValueError("days_since_first_seen must be a non-negative integer")
        item = {
            "claim_id": row["claim_id"],
            "review_state": state,
            "first_seen_at": row.get("first_seen_at"),
            "days_since_first_seen": age_days,
            "priority_score": score,
            "priority_score_is_truth_confidence": False,
            "priority_score_factors": priority.get("score_factors", {}),
            "risk_flags": priority.get("risk_flags", []),
            "claim": snapshot,
        }
        if state == "pending":
            pending.append(item)
        else:
            follow_up.append(item)

    # A first-pass batch should move through never-reviewed items. Claims
    # explicitly marked needs_more_evidence are reported separately and do
    # not repeatedly displace new work from the first-pass queue.
    pending.sort(key=lambda item: (
        -item["priority_score"],
        -item["days_since_first_seen"],
        item["claim_id"],
    ))
    selected = pending[:batch_size]
    follow_up.sort(key=lambda item: (
        -item["days_since_first_seen"],
        -item["priority_score"],
        item["claim_id"],
    ))

    batch_key = "\n".join(item["claim_id"] for item in selected)
    batch_id = "claim-review-" + hashlib.sha256(batch_key.encode("utf-8")).hexdigest()[:12]
    status = ("empty" if not rows else "unavailable" if not selected and missing
              else "follow_up_only" if not selected and follow_up and not missing
              else "ready" if selected and not missing else "partial")
    decision_template = {
        "schema_version": "1.0",
        "decisions": [
            {
                "claim_id": item["claim_id"],
                "decision": "",
                "reviewer": "",
                "decided_at": "",
                "notes": "",
            }
            for item in selected
        ],
    }
    packet = {
        "schema_version": "1.0",
        "generated_at": review_state.get("generated_at"),
        "status": status,
        "batch_id": batch_id,
        "batch_size_limit": batch_size,
        "selection_method": "pending_only; priority_score_desc, first_seen_age_desc, claim_id_asc",
        "summary": {
            "unresolved_claims": len(rows),
            "pending_claims": len(pending),
            "needs_more_evidence_follow_ups": len(follow_up),
            "reviewable_pending_claims": len(pending),
            "selected_for_this_batch": len(selected),
            "remaining_pending_after_batch": max(0, len(pending) - len(selected)),
            "allowed_decisions": list(DECISIONS),
            "missing_or_invalid_payloads": len(missing),
            "missing_claim_ids": sorted(missing),
        },
        "policy": {
            "decisions_written": False,
            "factual_verification_performed": False,
            "priority_is_truth_confidence": False,
            "review_rule": "Open the original source and verify exact product/model, configuration, units, scope, date and independent corroboration. Record uncertainty explicitly.",
            "accepted_for_evidence_attachment": "Means only that a claim is suitable for preparing a proposed evidence attachment; it does not mean the claim is independently verified or approved for a formal registry.",
        },
        "items": selected,
        "follow_up_queue": follow_up,
        "decision_template": decision_template,
    }
    return packet


def markdown_report(packet):
    summary = packet["summary"]
    lines = [
        "# AI Chip — Claim Review Batch",
        "",
        f"- Status: **{packet['status']}**",
        f"- Batch: {packet['batch_id']}",
        f"- Selected: **{summary['selected_for_this_batch']} / {summary['pending_claims']} pending Claims**",
        f"- Remaining first-pass queue: {summary['remaining_pending_after_batch']}",
        f"- Needs-more-evidence follow-ups: {summary['needs_more_evidence_follow_ups']}",
        f"- Missing/invalid Claim payloads: {summary['missing_or_invalid_payloads']}",
        "",
        "> Priority is a work-routing score, not confidence in truth. No decision is made by this report.",
        "",
        "## Review protocol",
        "",
        "1. Open the original source; do not rely on the extracted quote alone.",
        "2. Verify exact product/model, configuration, units, workload, measurement method and date.",
        "3. Distinguish vendor statements, preprints and independent measurements.",
        "4. Record a concise rationale (at least 30 characters) and reviewer identity.",
        "5. Use accepted_for_evidence_attachment only to request preparation of a separate evidence proposal; it is not verification.",
        "",
    ]
    for index, item in enumerate(packet["items"], 1):
        claim = item["claim"]
        source = claim.get("source") or {}
        scope = claim.get("scope") or {}
        lines.extend([
            f"## {index}. {claim.get('topic') or 'unclassified'} — {item['claim_id']}",
            "",
            f"- Priority: {item['priority_score']} · first seen: {item['days_since_first_seen']} days ago",
            f"- Claim type: {claim.get('claim_type') or 'unknown'} · assertion: {claim.get('assertion_class') or 'unknown'}",
            f"- Evidence class: {claim.get('evidence_class') or 'unknown'} · source type: {source.get('source_type') or 'unknown'}",
            f"- Publisher: {source.get('publisher') or source.get('source_name') or 'unknown'}",
            f"- Original source: {source.get('url') or 'unavailable'}",
            "",
            "**Claim candidate**",
            "",
            str(claim.get("statement") or "").strip(),
            "",
            "**Extracted source excerpt**",
            "",
            str(claim.get("evidence_quote") or "[No excerpt retained]").strip(),
            "",
            f"- Scope: {scope.get('text') or scope.get('status') or 'not stated'}",
            f"- Value/unit: {claim.get('value')!r} / {claim.get('unit') or 'not stated'}",
            f"- Qualifiers: {', '.join(str(x) for x in claim.get('qualifiers', [])) or 'none extracted'}",
            f"- Risk flags: {', '.join(item.get('risk_flags', [])) or 'none flagged'}",
            "",
            "**Human review**",
            "",
            "- [ ] Original source opened and checked",
            "- [ ] Product/model and configuration identified",
            "- [ ] Units, scope and workload checked",
            "- [ ] Independent corroboration sought or explicitly unavailable",
            "- [ ] Decision and rationale entered in the JSON template",
            "",
        ])
    if summary["missing_claim_ids"]:
        lines.extend(["## Missing payloads", ""])
        lines.extend(f"- {cid}" for cid in summary["missing_claim_ids"])
        lines.append("")
    if packet["follow_up_queue"]:
        lines.extend([
            "## Separate follow-up queue",
            "",
            f"{len(packet['follow_up_queue'])} Claims already marked needs_more_evidence are kept out of the first-pass batch so they do not displace never-reviewed items.",
            "",
        ])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--decision-template", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=25)
    args = parser.parse_args()
    try:
        state = json.loads(args.review_state.read_text(encoding="utf-8"))
        packet = build_review_batch(state, batch_size=args.batch_size)
        for path in (args.output, args.markdown, args.decision_template):
            path.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        args.markdown.write_text(markdown_report(packet), encoding="utf-8")
        args.decision_template.write_text(json.dumps(packet["decision_template"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Claim review batch: {packet['status']}; {packet['summary']['selected_for_this_batch']} selected.")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
