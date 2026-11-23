#!/usr/bin/env python3
"""Prepare and score independent human semantic-support reviews for a Claim batch.

No automatic entailment, truth verification, ledger write or registry change.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

LABELS = (
    "supported_by_source",
    "contradicted_by_source",
    "insufficient_context",
    "source_unavailable",
)
DECISIVE = {"supported_by_source", "contradicted_by_source"}


def valid_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def prepare(batch):
    if not isinstance(batch, dict) or batch.get("schema_version") != "1.0":
        raise ValueError("expected Claim review batch schema 1.0")
    rows = batch.get("items")
    policy = batch.get("policy")
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError("expected bounded Claim review items")
    if not isinstance(policy, dict) or policy.get("decisions_written") is not False or policy.get("factual_verification_performed") is not False:
        raise ValueError("input batch must remain unverified and read-only")
    if batch.get("summary", {}).get("selected_for_this_batch") != len(rows):
        raise ValueError("batch item count mismatch")
    seen = set()
    items = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid Claim batch row")
        claim_id, claim = row.get("claim_id"), row.get("claim")
        if not isinstance(claim_id, str) or not claim_id or claim_id in seen:
            raise ValueError("duplicate or invalid Claim ID")
        seen.add(claim_id)
        if not isinstance(claim, dict) or claim.get("claim_id") != claim_id:
            raise ValueError("Claim ID mismatch")
        source = claim.get("source") or {}
        statement = claim.get("statement")
        if not isinstance(statement, str) or not statement.strip() or not valid_url(source.get("url")):
            raise ValueError("Claim must contain a statement and HTTPS original source")
        if row.get("review_state") != "pending":
            raise ValueError("only pending Claims may enter first-pass semantic review")
        items.append({
            "claim_id": claim_id,
            "statement": statement,
            "evidence_quote": claim.get("evidence_quote") or "",
            "original_source_url": source["url"],
            "scope": claim.get("scope"),
            "assertion_class": claim.get("assertion_class"),
            "source_type": source.get("source_type"),
            "reviewers": [
                {"reviewer": "", "label": "", "rationale": "", "source_checked": False},
                {"reviewer": "", "label": "", "rationale": "", "source_checked": False},
            ],
        })
    return {
        "schema_version": "1.0",
        "batch_id": batch.get("batch_id"),
        "generated_at": batch.get("generated_at"),
        "review_type": "human_semantic_support",
        "allowed_labels": list(LABELS),
        "items": items,
        "policy": {
            "independent_review_slots": 2,
            "unverified_claims_only": True,
            "cannot_promote_to_verified": True,
            "review_meaning": "Whether the original source actually supports the extracted Claim, not whether the underlying statement is true or independently replicated.",
        },
    }


def evaluate(packet):
    if not isinstance(packet, dict) or packet.get("schema_version") != "1.0" or packet.get("review_type") != "human_semantic_support":
        raise ValueError("semantic review packet schema mismatch")
    if packet.get("allowed_labels") != list(LABELS):
        raise ValueError("semantic label set mismatch")
    if packet.get("policy", {}).get("cannot_promote_to_verified") is not True:
        raise ValueError("semantic review cannot promote factual verification")
    rows = packet.get("items")
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError("semantic review items must be bounded")
    seen = set()
    complete, pending, disagreements = [], [], []
    label_counts = Counter()
    for item in rows:
        cid = item.get("claim_id") if isinstance(item, dict) else None
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ValueError("duplicate or invalid semantic Claim ID")
        seen.add(cid)
        if not isinstance(item.get("statement"), str) or not item["statement"].strip() or not valid_url(item.get("original_source_url")):
            raise ValueError("review Claim statement or original source missing")
        reviews = item.get("reviewers")
        if not isinstance(reviews, list) or len(reviews) != 2:
            raise ValueError("exactly two independent reviewer slots required")
        filled = []
        for entry in reviews:
            if not isinstance(entry, dict) or set(entry) != {"reviewer", "label", "rationale", "source_checked"}:
                raise ValueError("review slot fields invalid")
            reviewer, label, note, checked = (
                entry["reviewer"], entry["label"], entry["rationale"], entry["source_checked"]
            )
            if not isinstance(reviewer, str) or not isinstance(label, str) or not isinstance(note, str) or type(checked) is not bool:
                raise ValueError("review slot fields must have valid types")
            blank = not reviewer.strip() and not label and not note.strip() and not checked
            if blank:
                continue
            if not reviewer.strip() or label not in LABELS or len(note.strip()) < 30:
                raise ValueError("completed semantic reviews require reviewer, label and >=30-character rationale")
            if label == "source_unavailable":
                if checked:
                    raise ValueError("source_unavailable cannot be marked source_checked")
            elif not checked:
                raise ValueError("semantic-support label requires checked original source")
            filled.append((reviewer.strip().casefold(), label))
        if len({x[0] for x in filled}) != len(filled):
            raise ValueError("two reviewers must have distinct identities")
        if len(filled) < 2:
            pending.append(cid)
            continue
        for _, label in filled:
            label_counts[label] += 1
        if filled[0][1] == filled[1][1]:
            complete.append({"claim_id": cid, "label": filled[0][1]})
        else:
            disagreements.append({
                "claim_id": cid,
                "labels": [filled[0][1], filled[1][1]],
                "requires_human_adjudication": True,
            })
    double_reviewed = len(complete) + len(disagreements)
    agreement = len(complete) / double_reviewed if double_reviewed else None
    return {
        "schema_version": "1.0",
        "batch_id": packet.get("batch_id"),
        "status": "complete" if not pending and not disagreements else "pending",
        "total_claims": len(rows),
        "double_reviewed_claims": double_reviewed,
        "pending_claim_ids": pending,
        "agreements": complete,
        "disagreements": disagreements,
        "raw_agreement": round(agreement, 4) if agreement is not None else None,
        "reviewer_label_counts": dict(sorted(label_counts.items())),
        "human_adjudication_needed": len(disagreements),
        "automatically_verified_claims": 0,
        "interpretation_limits": [
            "Agreement measures reviewer consistency, not factual accuracy.",
            "Support by a quoted source is not independent corroboration or a valid benchmark result.",
            "Partial review coverage and disagreement never become automatic approval.",
            "A selected priority batch is not a representative random sample of all discovered Claims.",
        ],
    }


def markdown_report(result):
    return "\n".join([
        "# Claim Semantic Support — Human Review",
        "",
        "- Batch: " + str(result["batch_id"]),
        "- Double-reviewed: " + str(result["double_reviewed_claims"]) + "/" + str(result["total_claims"]),
        "- Raw agreement: " + (f'{result["raw_agreement"]:.1%}' if result["raw_agreement"] is not None else "not available"),
        "- Pending review: " + str(len(result["pending_claim_ids"])),
        "- Disagreements requiring adjudication: " + str(result["human_adjudication_needed"]),
        "",
        "## Disputed Claim IDs", "",
        *("- " + item["claim_id"] + " (" + " / ".join(item["labels"]) + ")" for item in result["disagreements"]),
        "",
        "## Interpretation limits", "",
        *("- " + line for line in result["interpretation_limits"]), "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--evaluate", action="store_true", help="Evaluate an already human-labelled semantic packet; otherwise generate a blank packet")
    args = parser.parse_args()
    try:
        batch = json.loads(args.batch.read_text(encoding="utf-8"))
        result = evaluate(batch) if args.evaluate else prepare(batch)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.markdown:
            if not args.evaluate:
                raise ValueError("--markdown requires --evaluate")
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(markdown_report(result) + "\n", encoding="utf-8")
        print("Semantic review " + ("evaluated" if args.evaluate else "template generated") +
              ": " + str(len(result.get("items", [])) if not args.evaluate else result["total_claims"]) + " Claims")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
