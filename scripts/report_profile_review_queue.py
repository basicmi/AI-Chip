#!/usr/bin/env python3
"""Build a human-readable review queue from the AI Chip Landscape registries."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def freshness_status(checked_at: str | None, today: date | None = None) -> str:
    if not checked_at:
        return "unreviewed"
    today = today or date.today()
    try:
        checked = date.fromisoformat(checked_at[:10])
    except (TypeError, ValueError):
        return "invalid_date"
    age = (today - checked).days
    if age <= 90:
        return "fresh"
    if age <= 180:
        return "review_due"
    return "stale"


def build_review_queue(profiles, compatibility, workloads, today: date | None = None) -> str:
    today = today or date.today()
    companies = profiles.get("companies", [])
    profile_counts = Counter(company.get("profile_status", "unknown") for company in companies)
    total_products = sum(len(company.get("products", [])) for company in companies)
    total_claims = sum(len(company.get("claims", [])) for company in companies)
    total_evidence = sum(len(company.get("evidence", [])) for company in companies)
    total_references = sum(len(company.get("references", [])) for company in companies)

    reference_queue = []
    evidence_queue = []
    missing_metric_context = []
    missing_platform_link = []
    for company in companies:
        name = company.get("display_name", company.get("id", "company"))
        unreviewed_refs = [ref for ref in company.get("references", [])
                           if ref.get("review_status") != "reviewed"]
        if unreviewed_refs:
            reference_queue.append((name, len(unreviewed_refs), unreviewed_refs[:3]))
        for evidence in company.get("evidence", []):
            status = freshness_status(evidence.get("checked_at"), today)
            if status in {"unreviewed", "review_due", "stale", "invalid_date"}:
                evidence_queue.append((name, evidence.get("title", evidence.get("id", "evidence")),
                                       status, evidence.get("checked_at") or "—"))
        for product in company.get("products", []):
            if not product.get("compatibility_platform_ids"):
                missing_platform_link.append((name, product.get("name", product.get("id"))))
        for claim in company.get("claims", []):
            value = claim.get("value")
            numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
            if numeric and claim.get("topic") in {
                "compute", "memory_capacity", "memory_bandwidth", "interconnect", "power"
            } and not claim.get("metric_context"):
                missing_metric_context.append((name, claim.get("id"), claim.get("topic")))

    path_counts = Counter(path.get("status", "unknown") for path in workloads.get("paths", []))
    integration_counts = Counter(item.get("status", "unknown") for item in compatibility.get("integrations", []))
    lines = [
        "# AI Chip Landscape — Weekly Data Review Queue",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Registry date: {profiles.get('registry_reviewed_at', 'unknown')}",
        "",
        "## Coverage",
        "",
        f"- Companies: **{len(companies)}**",
        f"- Products: **{total_products}**",
        f"- Claims: **{total_claims}**",
        f"- Evidence records: **{total_evidence}**",
        f"- Carried-over references: **{total_references}**",
        f"- Compatibility platforms / integrations: **{len(compatibility.get('platforms', []))} / {len(compatibility.get('integrations', []))}**",
        f"- Workload paths: **{len(workloads.get('paths', []))}**",
        "",
        "## Company profile status",
        "",
        "| Status | Companies |",
        "|---|---:|",
    ]
    for status, count in sorted(profile_counts.items()):
        lines.append(f"| {status} | {count} |")

    lines.extend(["", "## Carried-over references awaiting claim-level review", ""])
    if not reference_queue:
        lines.append("No references are awaiting review.")
    else:
        lines.append("| Company | Unreviewed links | Sample labels |")
        lines.append("|---|---:|---|")
        for name, count, refs in reference_queue:
            labels = "; ".join(ref.get("label", ref.get("id", "source")) for ref in refs)
            lines.append(f"| {name} | {count} | {labels} |")

    lines.extend(["", "## Evidence freshness queue", ""])
    if not evidence_queue:
        lines.append("All reviewed evidence is within the current freshness window.")
    else:
        lines.extend(["| Company | Evidence | State | Last checked |", "|---|---|---|---|"])
        for name, title, status, checked in evidence_queue:
            lines.append(f"| {name} | {title} | {status} | {checked} |")

    lines.extend(["", "## Product / metric metadata gaps", ""])
    if not missing_platform_link and not missing_metric_context:
        lines.append("No missing product-platform links or numeric metric contexts were found.")
    else:
        for name, product in missing_platform_link:
            lines.append(f"- Missing compatibility platform link: {name} — {product}")
        for name, claim, topic in missing_metric_context:
            lines.append(f"- Missing metric context: {name} — {claim} ({topic})")

    lines.extend([
        "",
        "## Software integration maturity",
        "",
        "| Status | Integrations |",
        "|---|---:|",
    ])
    for status, count in sorted(integration_counts.items()):
        lines.append(f"| {status} | {count} |")

    lines.extend([
        "",
        "## Workload-path maturity",
        "",
        "| Status | Paths |",
        "|---|---:|",
    ])
    for status, count in sorted(path_counts.items()):
        lines.append(f"| {status} | {count} |")
    lines.extend([
        "",
        "Integration-only paths are documentation records, not workload-tested or benchmarked results. "
        "Prioritize adding reproducible configurations, correctness checks and measurements before changing their status.",
        "",
        "## Review guidance",
        "",
        "1. Review unreviewed company references and promote only claim-supporting sources into evidence records.",
        "2. Re-check stale or review-due evidence; update checked_at only after opening and verifying the source.",
        "3. Keep vendor-reported, derived and independently measured claims distinct.",
        "4. Do not mark an integration-only workload path as tested without a reproducible configuration and correctness evidence.",
        "5. Add product benchmark results only with the exact model, hardware/system boundary, software versions, metrics and source.",
        "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    profiles = load_json(ROOT / "data" / "company-profiles.json")
    compatibility = load_json(ROOT / "data" / "compatibility.json")
    workloads = load_json(ROOT / "data" / "workloads.json")
    report = build_review_queue(profiles, compatibility, workloads)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote review queue to {args.output}.")
    else:
        print(report)


if __name__ == "__main__":
    main()
