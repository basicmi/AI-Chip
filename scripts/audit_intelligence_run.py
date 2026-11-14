#!/usr/bin/env python3
"""Fail-closed audit of the weekly AI Chip Intelligence pipeline artifacts.

Validates cross-stage identifiers and marks source outages clearly. No network,
claim approvals, source-truth assessments, or production registry mutations.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def check(condition, message, errors):
    if not condition:
        errors.append(message)


def audit_pipeline(discovery, claims, graph, triage, review_state, *, generated_at=None):
    errors, warnings = [], []
    source_rows = discovery.get("source_results", [])
    check(discovery.get("schema_version") == "1.1" and discovery.get("read_only") is True,
          "discovery must be read-only schema v1.1", errors)
    check(isinstance(source_rows, list), "source_results must be an array", errors)
    source_rows = source_rows if isinstance(source_rows, list) else []
    observed = sum(row.get("status") == "observed" for row in source_rows if isinstance(row, dict))
    unavailable = [row.get("source_id") for row in source_rows
                   if isinstance(row, dict) and row.get("status") == "unavailable"]
    check(discovery.get("source_count") == len(source_rows), "discovery source_count mismatch", errors)
    check(discovery.get("sources_observed") == observed, "discovery observed count mismatch", errors)
    check(observed + len(unavailable) == len(source_rows),
          "every source must be observed or unavailable", errors)
    check(len({row.get("source_id") for row in source_rows if isinstance(row, dict)}) == len(source_rows),
          "duplicate source IDs in source results", errors)
    if len(source_rows) > 0 and observed == 0:
        errors.append("all active discovery sources are unavailable: prevent change-state checkpoint")
    elif unavailable:
        warnings.append(f"{len(unavailable)} of {len(source_rows)} discovery sources unavailable")
    if discovery.get("errors"):
        warnings.append(f"{len(discovery['errors'])} discovery error records; investigate external sources")
    severe = [row.get("source_id") for row in source_rows
              if isinstance(row, dict) and row.get("failure_tier") == "critical"]
    recovered = [row.get("source_id") for row in source_rows
                 if isinstance(row, dict) and row.get("health_transition") == "recovered"]
    if severe:
        warnings.append(f"{len(severe)} discovery sources have failed at least 3 consecutive runs")
    if recovered:
        warnings.append(f"{len(recovered)} discovery sources recovered since their last failure")
    for row in source_rows:
        if not isinstance(row, dict):
            continue
        if row.get("status") == "unavailable" and row.get("failure_category") is not None and (
                row["failure_category"] not in {
                    "http_rate_limit", "http_server_error", "http_client_error",
                    "timeout", "network", "parse_error", "invalid_payload", "source_error"}):
            errors.append("unknown classified source failure")

    if discovery.get("model_catalog_summary", {}).get("known_models_checked", 0) and (
        discovery.get("model_catalog_summary", {}).get("known_model_repositories_observed", 0) == 0
    ):
        warnings.append("none of the known model repositories was observed")

    candidates = discovery.get("review_queue", [])
    check(isinstance(candidates, list), "discovery review_queue must be an array", errors)
    candidates = candidates if isinstance(candidates, list) else []
    candidate_ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict)]
    check(len(candidate_ids) == len(candidates) and len(set(candidate_ids)) == len(candidate_ids),
          "discovery candidate IDs must be unique", errors)
    claim_rows = claims.get("claims", [])
    check(claims.get("schema_version") == "1.0" and isinstance(claim_rows, list),
          "claim extraction schema mismatch", errors)
    claim_rows = claim_rows if isinstance(claim_rows, list) else []
    claim_ids = [row.get("claim_id") for row in claim_rows if isinstance(row, dict)]
    claim_set = set(claim_ids)
    check(len(claim_ids) == len(claim_rows) and len(claim_set) == len(claim_ids),
          "claim IDs must be unique", errors)
    check(claims.get("claim_count") == len(claim_rows), "claim_count mismatch", errors)
    check(all(row.get("review_status") == "unverified_candidate" for row in claim_rows if isinstance(row, dict)),
          "all extracted claims must remain unverified", errors)
    check(all(row.get("candidate_id") in candidate_ids for row in claim_rows if isinstance(row, dict)),
          "some claims have no source candidate in discovery", errors)

    check(graph.get("schema_version") == "1.0" and graph.get("input_claim_count") == len(claim_rows),
          "graph claim count/version mismatch", errors)
    check(graph.get("summary", {}).get("independently_verified_claims") == 0,
          "graph must not claim automatic verification", errors)
    graph_ids = [row.get("claim_id") for row in graph.get("nodes", [])
                 if isinstance(row, dict) and row.get("type") == "claim_candidate"]
    check(len(graph_ids) == len(claim_ids) and set(graph_ids) == claim_set,
          "graph Claim ID membership mismatch", errors)

    check(triage.get("schema_version") == "1.0" and
          triage.get("summary", {}).get("input_claims") == len(claim_rows) and
          triage.get("summary", {}).get("automatically_verified") == 0 and
          triage.get("score_is_truth_confidence") is False,
          "triage count/policy mismatch", errors)
    triage_seen = set()
    for item in triage.get("queue", []):
        for cid in item.get("related_claim_ids", []):
            if cid not in claim_set or cid in triage_seen:
                errors.append("triage has unknown/repeated Claim ID")
            triage_seen.add(cid)
    if triage.get("total_queue_groups", 0) < len(triage.get("queue", [])):
        errors.append("triage total groups cannot be smaller than included queue")
    if len(triage_seen) < len(claim_ids):
        warnings.append("triage queue is truncated; review-state must still track all claims")

    check(review_state.get("schema_version") == "1.0" and
          review_state.get("observation_state") == "cache_persisted" and
          review_state.get("state_is_approval") is False,
          "review state status/policy mismatch", errors)
    age_rows = review_state.get("claim_aging", [])
    age_rows = age_rows if isinstance(age_rows, list) else []
    age_ids = [row.get("claim_id") for row in age_rows if isinstance(row, dict)]
    age_set = set(age_ids)
    check(len(age_ids) == len(age_rows) and len(age_set) == len(age_rows),
          "review age IDs must be unique", errors)
    current_seen = {row.get("claim_id") for row in age_rows
                    if isinstance(row, dict) and row.get("observed_this_run") is True}
    check(current_seen == claim_set, "review state current-run Claim IDs mismatch", errors)
    check(review_state.get("summary", {}).get("tracked_current_claims") == len(claim_ids),
          "review state current count mismatch", errors)
    check(review_state.get("summary", {}).get("tracked_backlog_claims") == len(age_rows),
          "review state backlog count mismatch", errors)
    check(all(row.get("review_is_factual_verification") is False for row in age_rows
              if isinstance(row, dict)),
          "review state must not assert factual verification", errors)
    pending_ids = {row["claim_id"] for row in age_rows
                   if isinstance(row, dict) and row.get("review_state") in {"pending", "needs_more_evidence"}}
    backlog_ids = [row.get("claim_id") for row in review_state.get("aging_backlog", [])
                   if isinstance(row, dict)]
    check(len(backlog_ids) == len(set(backlog_ids)) and set(backlog_ids) == pending_ids,
          "aging_backlog must contain every unresolved Claim exactly once", errors)
    for key in ("generated_at",):
        check(isinstance(discovery.get(key), str) and isinstance(claims.get(key), str)
              and isinstance(graph.get(key), str) and isinstance(triage.get(key), str)
              and isinstance(review_state.get(key), str), "missing stage timestamp", errors)

    now = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    summary = {
        "source_count": len(source_rows),
        "sources_observed": observed,
        "sources_unavailable": len(unavailable),
        "sources_critical_failures": len(severe),
        "sources_recovered": len(recovered),
        "sources_empty_success": sum(row.get("status") == "observed" and row.get("recent_item_count") == 0 for row in source_rows if isinstance(row, dict)),
        "source_unavailable_ids": sorted(str(x) for x in unavailable),
        "review_candidates": len(candidates),
        "extracted_claims": len(claim_rows),
        "triage_groups_shown": len(triage.get("queue", [])),
        "persistent_backlog": len(age_rows),
        "unresolved_backlog": len(pending_ids),
        "oldest_unresolved_days": max(
            (row.get("days_since_first_seen", 0) for row in age_rows
             if isinstance(row, dict) and row.get("claim_id") in pending_ids), default=0),
    }
    return {
        "schema_version": "1.0", "generated_at": now,
        "health": "failed" if errors else "degraded" if warnings else "healthy",
        "errors": errors, "warnings": warnings, "summary": summary,
        "cache_commit_allowed": not errors,
        "production_writes": False,
        "factual_verification_performed": False,
        "policy": "Operational health and consistency only; review states do not verify underlying technical claims.",
    }


def markdown_report(result):
    s = result["summary"]
    lines = ["# Intelligence Reliability Audit", "",
             f"**Status: {result['health'].upper()}**",
             f"- Sources: {s['sources_observed']}/{s['source_count']} observed ({s['sources_unavailable']} unavailable)",
             f"- Review leads: {s['review_candidates']} · claims: {s['extracted_claims']}",
             f"- Persistent backlog: {s['persistent_backlog']} · unresolved: {s['unresolved_backlog']}",
             f"- Oldest unresolved (first seen): {s['oldest_unresolved_days']} days",
             f"- Cache checkpoint allowed: {result['cache_commit_allowed']}",
             "", "## Warnings", ""]
    lines.extend(f"- {warning}" for warning in result["warnings"])
    if not result["warnings"]:
        lines.append("- None")
    lines.extend(["", "## Blocking errors", ""])
    lines.extend(f"- {error}" for error in result["errors"])
    if not result["errors"]:
        lines.append("- None")
    lines.extend(["", "A successful audit does not mean any source claim is true or independently verified."])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("discovery", "claims", "graph", "triage", "review-state", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    try:
        sources = [json.loads(getattr(args, name.replace("-", "_")).read_text(encoding="utf-8"))
                   for name in ("discovery", "claims", "graph", "triage", "review-state")]
        result = audit_pipeline(*sources)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(markdown_report(result), encoding="utf-8")
        print(f"Intelligence reliability: {result['health']}; "
              f"{result['summary']['sources_observed']}/{result['summary']['source_count']} sources.")
        return 0 if result["cache_commit_allowed"] else 1
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
