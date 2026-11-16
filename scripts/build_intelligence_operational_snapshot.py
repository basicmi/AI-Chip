#!/usr/bin/env python3
"""Create an operational telemetry snapshot from a validated intelligence run.

Inputs are already-produced read-only reports. No source truth, human approval,
vendor availability, or production registry mutation is inferred.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUEST_FAILURE_CATEGORIES = {
    "http_rate_limit", "http_server_error", "http_client_error",
    "timeout", "network", "parse_error", "invalid_payload", "source_error",
}


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


def checked_request_diagnostics(value, source_id):
    """Validate and copy only the allowlisted, URL-free request metrics."""
    if value is None:
        return None  # Backward-compatible with discovery artifacts before PR #106.
    if not isinstance(value, dict):
        raise ValueError("request diagnostics must be an object for " + source_id)

    for field in ("request_count", "failed_request_count", "response_bytes"):
        item = value.get(field)
        if type(item) is not int or item < 0:
            raise ValueError("invalid request diagnostic " + field + " for " + source_id)
    count = value["request_count"]
    failed = value["failed_request_count"]
    if failed > count:
        raise ValueError("failed request count exceeds total for " + source_id)

    for field in ("total_elapsed_ms", "max_request_ms"):
        item = value.get(field)
        if type(item) not in (int, float) or not math.isfinite(item) or item < 0:
            raise ValueError("invalid request timing " + field + " for " + source_id)

    average = value.get("average_request_ms")
    if count == 0:
        if (average is not None or value["response_bytes"] != 0 or failed != 0
                or value["total_elapsed_ms"] != 0 or value["max_request_ms"] != 0):
            raise ValueError("zero-request diagnostics are inconsistent for " + source_id)
    else:
        if (type(average) not in (int, float) or not math.isfinite(average)
                or average < 0
                or abs(average - value["total_elapsed_ms"] / count) > 0.002):
            raise ValueError("average request latency is inconsistent for " + source_id)
        if value["max_request_ms"] > value["total_elapsed_ms"] + 0.002:
            raise ValueError("maximum request latency exceeds total for " + source_id)

    status = value.get("last_http_error_status")
    if status is not None and (type(status) is not int or not 100 <= status <= 599):
        raise ValueError("invalid HTTP error status for " + source_id)
    category = value.get("last_request_failure_category")
    if category is not None and (
            not isinstance(category, str) or category not in REQUEST_FAILURE_CATEGORIES):
        raise ValueError("invalid request failure category for " + source_id)
    if count == 0 and (status is not None or category is not None):
        raise ValueError("zero-request diagnostics cannot contain a failure for " + source_id)
    if failed == 0 and (status is not None or category is not None):
        raise ValueError("failure metadata without failed requests for " + source_id)

    # Explicitly copy fields; never forward arbitrary source data such as URLs.
    return {
        "request_count": count,
        "failed_request_count": failed,
        "response_bytes": value["response_bytes"],
        "total_elapsed_ms": round(value["total_elapsed_ms"], 3),
        "average_request_ms": round(average, 3) if average is not None else None,
        "max_request_ms": round(value["max_request_ms"], 3),
        "last_http_error_status": status,
        "last_request_failure_category": category,
    }


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
        source_id = source["source_id"]
        if source_id in names or source.get("status") not in {"observed", "unavailable"}:
            raise ValueError("invalid duplicate/unknown source status")
        names.add(source_id)
        per_source.append({
            "source_id": source_id,
            "name": str(source.get("source_name") or source_id),
            "kind": source.get("kind"),
            "status": source["status"],
            "recent_item_count": source.get("recent_item_count", 0),
            "failure_category": source.get("failure_category"),
            "failure_tier": source.get("failure_tier"),
            "consecutive_failures": source.get("consecutive_failures", 0),
            "health_transition": source.get("health_transition"),
            "attempt_count": source.get("attempt_count"),
            "request_diagnostics": checked_request_diagnostics(
                source.get("request_diagnostics"), source_id),
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

    for field, value in (("discovery_cache_present", discovery_cache_present),
                         ("review_cache_present", review_cache_present)):
        if value is not None and type(value) is not bool:
            raise ValueError("cache presence must be boolean or unknown")

    measured = [source["request_diagnostics"] for source in per_source
                if source["request_diagnostics"] is not None]
    request_summary = {
        "request_telemetry_sources": len(measured),
        "total_requests": sum(item["request_count"] for item in measured),
        "failed_requests": sum(item["failed_request_count"] for item in measured),
        "response_bytes": sum(item["response_bytes"] for item in measured),
        "sources_with_slow_request_over_5s": sum(
            item["max_request_ms"] >= 5000 for item in measured),
    }
    return {
        "schema_version": "1.1",
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
            "sources_critical_failures": summary.get("sources_critical_failures", 0),
            "sources_recovered": summary.get("sources_recovered", 0),
            "sources_empty_success": summary.get("sources_empty_success", 0),
            "availability_percent": round(100 * observed / len(per_source), 1) if per_source else None,
            "candidate_count": discovery.get("candidate_count"),
            "new_candidates": discovery.get("change_counts", {}).get("new"),
            "updated_candidates": discovery.get("change_counts", {}).get("updated"),
            "review_leads": summary.get("review_candidates"),
            "extracted_claims": summary.get("extracted_claims"),
            "persistent_backlog": summary.get("persistent_backlog"),
            "unresolved_backlog": summary.get("unresolved_backlog"),
            "oldest_unresolved_days": summary.get("oldest_unresolved_days"),
            **request_summary,
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
              f"{data['summary']['sources_observed']}/{data['summary']['sources_total']} sources; "
              f"{data['summary']['total_requests']} requests, {data['summary']['failed_requests']} failed.")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
