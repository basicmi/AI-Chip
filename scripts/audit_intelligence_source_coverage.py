#!/usr/bin/env python3
"""Coverage audit for the 24 curated AI Chip Intelligence sources.

The audit uses actual Discovery run artifacts. It does not fetch sources itself
or claim that observed items exhaust a feed or that metadata claims are true.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def utc(value):
    if not isinstance(value, str):
        return None
    try:
        timestamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return timestamp.astimezone(timezone.utc) if timestamp.utcoffset() is not None else None
    except ValueError:
        return None


def normalized_url(value):
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        if url.scheme not in {"http", "https"} or not url.hostname:
            return None
        hostname = url.hostname.casefold()
        # Strip tracking fragments and scheme/default ports; retain the query,
        # since it may distinguish resources.
        port = url.port
        if port and (url.scheme, port) not in {("http", 80), ("https", 443)}:
            hostname += ":" + str(port)
        return urlunsplit((url.scheme, hostname, url.path.rstrip("/") or "/", url.query, ""))
    except ValueError:
        return None


def coverage_report(registry, discovery, *, generated_at=None):
    if not isinstance(registry, dict) or registry.get("schema_version") != "1.0":
        raise ValueError("expected curated source registry version 1.0")
    sources = registry.get("sources")
    if not isinstance(sources, list):
        raise ValueError("registry sources must be an array")
    active = [source for source in sources if source.get("active") is True]
    ids = [source.get("id") for source in active]
    if not all(isinstance(x, str) and x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("active source identifiers must be unique and nonempty")
    if discovery.get("schema_version") != "1.1" or discovery.get("read_only") is not True:
        raise ValueError("expected read-only Discovery report 1.1")
    timestamp = utc(discovery.get("generated_at"))
    if not timestamp:
        raise ValueError("discovery timestamp must be timezone-aware")
    if generated_at is not None:
        current = utc(generated_at)
        if not current or abs((current - timestamp).total_seconds()) > 3600:
            raise ValueError("coverage and Discovery timestamps do not align")
    scan_rows = discovery.get("source_results")
    observations = discovery.get("all_observations")
    if not isinstance(scan_rows, list) or not isinstance(observations, list):
        raise ValueError("Discovery source_results/all_observations must be arrays")
    row_ids = [row.get("source_id") for row in scan_rows if isinstance(row, dict)]
    if len(row_ids) != len(scan_rows) or len(set(row_ids)) != len(row_ids) or set(row_ids) != set(ids):
        raise ValueError("Discovery source membership differs from active registry")
    scans = {row["source_id"]: row for row in scan_rows}
    if not all(row.get("status") in {"observed", "unavailable"} for row in scan_rows):
        raise ValueError("source scan status is invalid")
    observed_count = sum(row["status"] == "observed" for row in scan_rows)
    if (discovery.get("source_count") != len(scan_rows)
            or discovery.get("sources_observed") != observed_count
            or discovery.get("sources_unavailable") != len(scan_rows) - observed_count):
        raise ValueError("Discovery source summary inconsistent with scan records")
    if discovery.get("candidate_count") != len(observations):
        raise ValueError("Discovery candidate_count inconsistent with observations")
    grouped = defaultdict(list)
    url_sources = defaultdict(set)
    invalid_dates = Counter()
    for item in observations:
        if not isinstance(item, dict):
            raise ValueError("invalid observation record")
        sid = item.get("source_id")
        # Other upstream catalog candidates may be provided separately and
        # must not be counted as one of the configured feed sources.
        if sid not in scans:
            if sid == "huggingface-model-catalog":
                continue
            raise ValueError("observation references unknown source: " + str(sid))
        if scans[sid]["status"] != "observed":
            raise ValueError("unavailable source unexpectedly has observations")
        grouped[sid].append(item)
        pub = item.get("published_at")
        if utc(pub) is None:
            invalid_dates[sid] += 1
        url = normalized_url(item.get("url"))
        if url:
            url_sources[url].add(sid)
    shared_urls = {url: sorted(source_ids) for url, source_ids in url_sources.items()
                   if len(source_ids) > 1}
    kinds = Counter(source["kind"] for source in active)
    records, warnings = [], []
    for source in active:
        sid = source["id"]
        row = scans[sid]
        items = grouped[sid]
        if row.get("recent_item_count") != len(items):
            raise ValueError("recent item count differs from observations for " + sid)
        dates = [pub for item in items if (pub := utc(item.get("published_at"))) is not None]
        latest = max(dates) if dates else None
        oldest = min(dates) if dates else None
        latest_age = max(0, (timestamp - latest).days) if latest else None
        # Reaching the configured extraction cap is a possible missed-page
        # indicator; it does not prove a release is missing.
        cap = 20 if source["kind"] == "github_releases" else (
            source.get("max_results", 100) if source["kind"] == "arxiv_api" else None)
        pagination = row.get("pagination")
        if pagination is not None and source["kind"] in {"github_releases", "arxiv_api"}:
            expected_per_page = 20 if source["kind"] == "github_releases" else source.get("max_results", 100)
            if (not isinstance(pagination, dict)
                    or pagination.get("per_page") != expected_per_page
                    or pagination.get("max_pages") != 3
                    or type(pagination.get("pages_fetched")) is not int
                    or not 1 <= pagination["pages_fetched"] <= 3
                    or type(pagination.get("raw_items_scanned")) is not int
                    or pagination["raw_items_scanned"] < len(items)
                    or type(pagination.get("paging_cap_reached")) is not bool):
                raise ValueError("invalid source pagination diagnostics for " + sid)
            at_cap = pagination["paging_cap_reached"]
        else:
            # Legacy source reports and arXiv only expose filtered counts.
            at_cap = row["status"] == "observed" and isinstance(cap, int) and cap > 0 and len(items) >= cap
        repeated = sum(1 for item in items if (
            normalized_url(item.get("url")) in shared_urls))
        risk_flags = []
        if row["status"] == "unavailable":
            risk_flags.append("source_unavailable")
        elif not items:
            risk_flags.append("no_recent_items_not_a_failure")
        if at_cap:
            risk_flags.append("possible_window_truncation")
        if latest_age is not None and latest_age > 30:
            risk_flags.append("latest_observed_publication_over_30d")
        if invalid_dates[sid]:
            risk_flags.append("missing_or_invalid_publication_date")
        if repeated:
            risk_flags.append("cross_source_same_url_not_independent")
        failures = row.get("consecutive_failures", 0)
        if row.get("failure_tier") == "critical" or (
            isinstance(failures, int) and failures >= 3):
            risk_flags.append("repeated_source_failure")
        result = {
            "source_id": sid, "kind": source["kind"], "status": row["status"],
            "recent_item_count": len(items),
            "newest_publication_at": latest.isoformat().replace("+00:00", "Z") if latest else None,
            "oldest_publication_at": oldest.isoformat().replace("+00:00", "Z") if oldest else None,
            "latest_observed_publication_age_days": latest_age,
            "invalid_publication_date_count": invalid_dates[sid],
            "per_request_item_limit": cap,
            "pagination": pagination if source["kind"] in {"github_releases", "arxiv_api"} else None,
            "possible_window_truncation": bool(at_cap),
            "same_url_observations": repeated,
            "failure_category": row.get("failure_category"),
            "failure_tier": row.get("failure_tier"),
            "consecutive_failures": failures,
            "risk_flags": risk_flags,
        }
        records.append(result)
        if risk_flags:
            warnings.append({"source_id": sid, "risk_flags": risk_flags})
    return {
        "schema_version": "1.0",
        "generated_at": timestamp.isoformat().replace("+00:00", "Z"),
        "audit_kind": "post_discovery_source_coverage",
        "verified_remote_endpoints": False,
        "factual_verification_performed": False,
        "source_kinds": dict(sorted(kinds.items())),
        "summary": {
            "configured_active_sources": len(active),
            "observed_sources": observed_count,
            "unavailable_sources": len(active) - observed_count,
            "empty_success_sources": sum(x["status"] == "observed" and x["recent_item_count"] == 0 for x in records),
            "potentially_truncated_sources": sum(x["possible_window_truncation"] for x in records),
            "cross_source_shared_url_groups": len(shared_urls),
            "sources_needing_attention": len(warnings),
        },
        "sources": sorted(records, key=lambda x: x["source_id"]),
        # Do not publish source URL values in the report: paths and queries
        # can contain sensitive tokens. Only source IDs and risk counts.
        "shared_urls_by_source_ids": sorted(shared_urls.values()),
        "attention": sorted(warnings, key=lambda x: x["source_id"]),
        "policy": "Coverage diagnostics from one actual run. Empty success differs from failure; cap saturation is a warning only; duplicates do not establish independent evidence.",
    }


def markdown_report(report):
    s = report["summary"]
    lines = [
        "# AI Chip Intelligence Source Coverage Audit", "",
        f"- Active configured sources: **{s['configured_active_sources']}**",
        f"- Sources successfully reached and parsed: **{s['observed_sources']}**",
        f"- Unavailable sources: **{s['unavailable_sources']}**",
        f"- Empty successful sources: {s['empty_success_sources']}",
        f"- Possible per-request truncation: {s['potentially_truncated_sources']}",
        f"- Cross-source shared URL groups: {s['cross_source_shared_url_groups']}",
        "", "## Attention queue", "",
    ]
    if report["attention"]:
        for row in report["attention"]:
            lines.append(f"- **{row['source_id']}** — {', '.join(row['risk_flags'])}")
    else:
        lines.append("- No flags detected in observed metadata.")
    lines.extend([
        "", "## Limits", "",
        "- A valid, empty source is not a failure.",
        "- The scan does **not** guarantee full history coverage or detect every missing article.",
        "- Hitting an API result limit is a potential completeness risk, not proof of missing data.",
        "- The same URL appearing in multiple sources is not independent corroboration.",
        "- One observation cannot prove a feed is permanently inactive.",
        "- No candidate Claim is automatically verified or promoted.", "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        discovery = json.loads(args.discovery.read_text(encoding="utf-8"))
        report = coverage_report(registry, discovery)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(markdown_report(report) + "\n", encoding="utf-8")
        print("PASS: source coverage audited for", report["summary"]["configured_active_sources"], "active sources")
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
