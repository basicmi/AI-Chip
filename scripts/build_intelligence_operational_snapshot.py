#!/usr/bin/env python3
"""Create an operational telemetry snapshot from a validated intelligence run.

Inputs are already-produced read-only reports. No source truth, human approval,
vendor availability, or production registry mutation is inferred.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("missing ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() is None:
            raise ValueError("timestamp must have timezone")
        return parsed.astimezone(timezone.utc)
    except ValueError as error:
        raise ValueError("invalid timezone-aware timestamp") from error


def snapshot(discovery, health, review, *, discovery_cache_present=None, review_cache_present=None):
    if discovery.get("schema_version") != "1.1" or discovery.get("read_only") is not True:
        raise ValueError("expected read-only discovery version 1.1")
    if health.get("schema_version") != "1.0" or health.get("cache_commit_allowed") is not True:
        raise ValueError("cannot emit operational success snapshot for failed audit")
    if health.get("health") not in {"healthy", "degraded"}:
        raise ValueError("health must be healthy or degraded")
    if health.get("production_writes") is not False or health.get("factual_verification_performed") is not False:
        raise ValueError("health report asserts unsupported production writes or verification")
    if review.get("schema_version") != "1.0" or review.get("state_is_approval") is not False:
        raise ValueError("review-state policy mismatch")
    generated = timestamp(health.get("generated_at"))
    for item in (discovery, review):
        observed = timestamp(item.get("generated_at"))
        if abs((generated - observed).total_seconds()) > 3600:
            raise ValueError("operational report stages are from different runs")
    sources = discovery.get("source_results")
    if not isinstance(sources, list):
        raise ValueError("discovery source_results must be an array")
    names = set()
    per_source = []
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("source_id"), str):
            raise ValueError("source is missing a stable ID")
        if source["source_id"] in names or source.get("status") not in {"observed", "unavailable"}:
            raise ValueError("invalid duplicate/unknown source status")
        names.add(source["source_id"])
        per_source.append({
            "source_id": source["source_id"],
            "name": str(source.get("source_name") or source["source_id"]),
            "kind": source.get("kind"),
            "status": source["status"],
            "recent_item_count": source.get("recent_item_count", 0),
        })
    summary = health.get("summary", {})
    observed = sum(source["status"] == "observed" for source in per_source)
    unavailable = len(per_source) - observed
    if (summary.get("source_count") != len(per_source) or
            summary.get("sources_observed") != observed or
            summary.get("sources_unavailable") != unavailable):
        raise ValueError("health/discovery source availability mismatch")
    expected = review.get("summary", {})
    if (summary.get("persistent_backlog") != expected.get("tracked_backlog_claims") or
            summary.get("unresolved_backlog") != (
                expected.get("review_states", {}).get("pending", 0) +
                expected.get("review_states", {}).get("needs_more_evidence", 0))):
        raise ValueError("health/review backlog mismatch")
    for field in ("discovery_cache_present", "review_cache_present"):
        value = {"discovery_cache_present": discovery_cache_present,
                 "review_cache_present": review_cache_present}[field]
        if value is not None and type(value) is not bool:
            raise ValueError("cache presence must be boolean or unknown")
    return {
        "schema_version": "1.0",
        "generated_at": health["generated_at"],
        "health": health["health"],
        "operational_only": True,
        "cache": {
            "discovery_restored_file_present": discovery_cache_present,
            "review_restored_file_present": review_cache_present,
            "checkpoint_audit_passed": True,
            "note": "File presence means cache was available at run start; not proof of continuity, freshness or durable retention.",
        },
        "summary": {
            "sources_total": len(per_source),
            "sources_observed": observed,
            "sources_unavailable": unavailable,
            "availability_percent": round(100 * observed / len(per_source), 1) if per_source else None,
            "candidate_count": discovery.get("candidate_count"),
            "new_candidates": discovery.get("change_counts", {}).get("new"),
            "updated_candidates": discovery.get("change_counts", {}).get("updated"),
            "review_leads": summary.get("review_candidates"),
            "extracted_claims": summary.get("extracted_claims"),
            "persistent_backlog": summary.get("persistent_backlog"),
            "unresolved_backlog": summary.get("unresolved_backlog"),
            "oldest_unresolved_days": summary.get("oldest_unresolved_days"),
        },
        "sources": sorted(per_source, key=lambda x: x["source_id"]),
        "warnings": list(health.get("warnings", [])),
        "policy": "Operational telemetry only. Run availability is not source correctness or Claim truth confidence.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("discovery", "health", "review-state", "output"):
        parser.add_argument("--" + field, required=True, type=Path)
    for field in ("discovery-cache-present", "review-cache-present"):
        parser.add_argument("--" + field, choices=["true", "false", "unknown"], default="unknown")
    args = parser.parse_args()
    try:
        inputs = [json.loads(getattr(args, name).read_text(encoding="utf-8"))
                  for name in ("discovery", "health", "review_state")]
        parse = lambda value: None if value == "unknown" else value == "true"
        data = snapshot(*inputs,
            discovery_cache_present=parse(args.discovery_cache_present),
            review_cache_present=parse(args.review_cache_present))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"PASS: operational snapshot {data['health']}, "
              f"{data['summary']['sources_observed']}/{data['summary']['sources_total']} sources")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
