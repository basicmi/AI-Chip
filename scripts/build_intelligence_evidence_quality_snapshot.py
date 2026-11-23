#!/usr/bin/env python3
"""Create a read-only evidence-quality dashboard snapshot from one discovery run.

Human labels are not inferred from blank review templates. This is not a
factual correctness or independent corroboration score.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def utc_stamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp is missing")
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.utcoffset() is None:
            raise ValueError("timestamp requires timezone")
        return date
    except ValueError as error:
        raise ValueError("invalid timezone-aware timestamp") from error


def count(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(name + " must be a nonnegative integer")
    return value


def snapshot(quality, state, lineage, semantic):
    for name, data in (("quality", quality), ("review-state", state),
                       ("lineage", lineage), ("semantic", semantic)):
        if not isinstance(data, dict) or data.get("schema_version") != "1.0":
            raise ValueError(name + " must use schema 1.0")
    if state.get("observation_state") != "cache_persisted" or state.get("state_is_approval") is not False:
        raise ValueError("review-state must be persisted observation, not factual approval")
    if lineage.get("review_type") != "source_lineage" or lineage.get("policy", {}).get("independent_corroboration_automatically_verified") is not False:
        raise ValueError("lineage must be a read-only, unverified review template")
    if semantic.get("review_type") != "human_semantic_support" or semantic.get("policy", {}).get("cannot_promote_to_verified") is not True:
        raise ValueError("semantic template must prohibit automatic verification")
    if lineage.get("status") != "human_review_required":
        raise ValueError("lineage input must be a blank review worksheet")

    stamp = state.get("generated_at")
    utc_stamp(stamp)
    # Individual stages can have their own generated_at values; the semantic
    # template is built directly from the review-state batch and must match it.
    if semantic.get("generated_at") != stamp:
        raise ValueError("semantic template is from a different review-state run")
    batch_id = semantic.get("batch_id")
    if not isinstance(batch_id, str) or not batch_id.startswith("claim-review-"):
        raise ValueError("semantic template must have a stable Claim review batch ID")
    q = quality.get("summary")
    s = state.get("summary")
    l = lineage.get("summary")
    items = semantic.get("items")
    if not all(isinstance(x, dict) for x in (q, s, l)) or not isinstance(items, list):
        raise ValueError("missing dashboard summary or semantic items")
    total = count(q.get("claim_count"), "claim_count")
    if count(s.get("tracked_current_claims"), "tracked_current_claims") != total:
        raise ValueError("Claim totals disagree across stages")
    if count(q.get("claims_remaining_unverified"), "claims_remaining_unverified") != total:
        raise ValueError("quality report incorrectly claims verified Claims")
    quoted = count(q.get("quote_grounded_claims"), "quote_grounded_claims")
    complete = count(q.get("provenance_complete_claims"), "provenance_complete_claims")
    mismatch = count(q.get("claims_with_source_metadata_mismatch"), "claims_with_source_metadata_mismatch")
    if any(x > total for x in (quoted, complete, mismatch)):
        raise ValueError("evidence quality count exceeds input Claims")
    states = s.get("review_states")
    if not isinstance(states, dict):
        raise ValueError("review-state counts missing")
    for key in ("pending", "needs_more_evidence", "rejected", "accepted_for_evidence_attachment"):
        count(states.get(key), key)
    backlog = count(s.get("tracked_backlog_claims"), "tracked_backlog_claims")
    if sum(states.values()) != backlog:
        raise ValueError("review-state counts do not match backlog")
    unresolved = states["pending"] + states["needs_more_evidence"]
    payloads = count(s.get("claim_payloads_available"), "claim_payloads_available")
    missing = count(s.get("claim_payloads_missing"), "claim_payloads_missing")
    if payloads + missing != backlog:
        raise ValueError("review-state payload coverage mismatch")
    selected = count(l.get("selected_clusters"), "selected_clusters")
    candidates = count(l.get("multi_document_duplicate_clusters"), "multi_document_duplicate_clusters")
    if selected > candidates or selected != len(lineage.get("clusters", [])):
        raise ValueError("lineage selected count mismatch")
    if len(items) > 100 or len({item.get("claim_id") for item in items}) != len(items):
        raise ValueError("invalid semantic review batch IDs")
    if not all(item.get("reviewers") == [
            {"reviewer": "", "label": "", "rationale": "", "source_checked": False},
            {"reviewer": "", "label": "", "rationale": "", "source_checked": False}]
               for item in items):
        raise ValueError("semantic worksheet must not contain fabricated human judgments")
    if count(q.get("distinct_source_documents"), "distinct_source_documents") < 0:
        raise ValueError("invalid source documents")

    def rate(numerator, denominator):
        return round(numerator / denominator, 4) if denominator else None

    return {
        "schema_version": "1.0", "generated_at": stamp,
        "semantic_batch_id": batch_id,
        "read_only": True, "factual_verification_performed": False,
        "metrics": {
            "current_claims": total,
            "quote_traceability": {"passed": quoted, "total": total, "rate": rate(quoted, total)},
            "provenance_completeness": {"passed": complete, "total": total, "rate": rate(complete, total)},
            "source_metadata_mismatches": mismatch,
            "distinct_source_documents": q["distinct_source_documents"],
            "distinct_publishers": count(q.get("distinct_publishers"), "distinct_publishers"),
            "review_backlog": backlog,
            "unresolved_claims": unresolved,
            "pending_claims": states["pending"],
            "needs_more_evidence": states["needs_more_evidence"],
            "accepted_for_evidence_attachment": states["accepted_for_evidence_attachment"],
            "rejected_claims": states["rejected"],
            "payload_coverage": {"passed": payloads, "total": backlog, "rate": rate(payloads, backlog)},
            "multi_document_exact_duplicate_clusters": candidates,
            "lineage_clusters_queued": selected,
            "semantic_claims_queued": len(items),
            "semantic_double_review_rate": None,
            "semantic_reviewer_agreement": None,
            "lineage_human_review_coverage": None,
            "independently_verified_claims": None,
        },
        "availability": {
            "semantic_evaluation": "not_provided",
            "lineage_evaluation": "not_provided",
            "independent_verification": "not_measured",
        },
        "interpretation": (
            "Quote traceability and provenance completeness are extraction hygiene only. "
            "A queued review is not a completed review. Distinct publishers and URLs are not independent evidence. "
            "Human agreement and truth are unavailable without separate reviewed evaluations. "
            "Accepted_for_evidence_attachment is a workflow state, not factual verification."
        ),
    }


def markdown_report(report):
    m = report["metrics"]
    def pct(row):
        return "N/A" if row["rate"] is None else f'{row["rate"]:.1%}'
    return "\n".join([
        "# Evidence Quality Dashboard Snapshot", "",
        f"- Current Claims: {m['current_claims']}",
        f"- Quote traceability: {m['quote_traceability']['passed']}/{m['current_claims']} ({pct(m['quote_traceability'])})",
        f"- Complete provenance: {m['provenance_completeness']['passed']}/{m['current_claims']} ({pct(m['provenance_completeness'])})",
        f"- Review backlog: {m['review_backlog']} (unresolved {m['unresolved_claims']})",
        f"- Historical Claim payload coverage: {m['payload_coverage']['passed']}/{m['review_backlog']} ({pct(m['payload_coverage'])})",
        f"- Cross-document duplicate clusters: {m['multi_document_exact_duplicate_clusters']}",
        f"- Lineage worksheets queued: {m['lineage_clusters_queued']}",
        f"- Semantic Claims queued: {m['semantic_claims_queued']}",
        "- Human semantic agreement: unavailable (no completed labels supplied)",
        "- Human lineage coverage: unavailable (no completed labels supplied)",
        "- Independently verified Claims: not measured",
        "", "These are operational diagnostics, not a composite factual confidence score.", ""
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("quality", "review-state", "lineage", "semantic"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    try:
        reports = [json.loads(getattr(args, key).read_text(encoding="utf-8"))
                   for key in ("quality", "review_state", "lineage", "semantic")]
        report = snapshot(*reports)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(markdown_report(report) + "\n", encoding="utf-8")
        print(f"Evidence quality snapshot: {report['metrics']['current_claims']} current unverified Claims")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
