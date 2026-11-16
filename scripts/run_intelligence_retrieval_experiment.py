#!/usr/bin/env python3
"""Run isolated, bounded arXiv query experiments without changing production discovery."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from evaluate_intelligence_retrieval import paper_id
from extract_intelligence_claims import relevance_for
from run_intelligence_discovery import (
    bounded_retry, collect_arxiv, failure_category, fetch_text,
    instrument_fetcher, request_diagnostics_snapshot,
)

GROUP_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_config(config):
    if config.get("schema_version") != "1.0":
        raise ValueError("Unsupported experiment config schema_version")
    groups = config.get("groups")
    if not isinstance(groups, list) or not 1 <= len(groups) <= 6:
        raise ValueError("Experiment config requires 1..6 query groups")
    seen = set()
    for index, group in enumerate(groups):
        prefix = f"groups[{index}]"
        group_id = group.get("id")
        if not isinstance(group_id, str) or not GROUP_ID.fullmatch(group_id) or group_id in seen:
            raise ValueError(prefix + ".id must be unique lowercase kebab-case")
        seen.add(group_id)
        if not isinstance(group.get("name"), str) or not group["name"].strip():
            raise ValueError(prefix + ".name must be nonempty")
        query = group.get("query")
        if not isinstance(query, str) or not query.strip() or len(query) > 2500:
            raise ValueError(prefix + ".query must be 1..2500 characters")
        if "://" in query:
            raise ValueError(prefix + ".query must be an arXiv search expression, not a URL")
        limit = group.get("max_results", 50)
        if type(limit) is not int or not 1 <= limit <= 50:
            raise ValueError(prefix + ".max_results must be 1..50")
    return groups


def parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Discovery generated_at must be an ISO timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Discovery generated_at must include timezone")
    return parsed.astimezone(timezone.utc)


def skip_report(discovery, reason, experiment_id):
    return {
        "schema_version": "1.0", "experiment_id": experiment_id,
        "discovery_generated_at": discovery.get("generated_at"),
        "status": "skipped", "scorable": False, "skip_reason": reason,
        "groups": [], "summary": {},
        "interpretation_limits": [
            "The experiment is separate from production discovery and does not modify its source registry.",
            "A skipped experiment cannot support a negative conclusion about query coverage.",
        ],
    }


def run_experiment(config, discovery, baseline, *, fetcher=fetch_text, sleep=time.sleep):
    groups = validate_config(config)
    arxiv_sources = [row for row in discovery.get("source_results", []) if row.get("kind") == "arxiv_api"]
    unavailable = [row.get("source_id") for row in arxiv_sources if row.get("status") != "observed"]
    if not baseline.get("scorable") or not arxiv_sources or unavailable:
        reason = "baseline_recall_unscorable" if not baseline.get("scorable") else (
            "baseline_arxiv_shards_unavailable:" + ",".join(unavailable)
        )
        return skip_report(discovery, reason, config.get("experiment_id"))

    generated = parse_timestamp(discovery["generated_at"])
    lookback_days = discovery.get("lookback_days")
    if type(lookback_days) is not int or lookback_days < 1:
        raise ValueError("Discovery lookback_days must be a positive integer")
    since = generated - timedelta(days=lookback_days)

    baseline_ids = set()
    active_ids = {row["source_id"] for row in arxiv_sources}
    for row in discovery.get("all_observations", []):
        if row.get("source_id") in active_ids and row.get("candidate_type") == "research_preprint":
            baseline_ids.add(paper_id(row.get("candidate_id")))
    eligible = {paper_id(item["paper_id"]) for item in baseline.get("matched", []) + baseline.get("missing", [])}
    baseline_seed_hits = {paper_id(item["paper_id"]) for item in baseline.get("matched", [])}

    all_group_ids, all_incremental_ids, all_incremental_seed_hits = set(), set(), set()
    all_candidates_by_id = {}
    group_reports = []
    for index, group in enumerate(groups):
        if index:
            sleep(3)
        metrics = {
            "request_count": 0, "failed_request_count": 0, "response_bytes": 0,
            "total_elapsed_ms": 0.0, "max_request_ms": 0.0,
            "last_http_error_status": None, "last_request_failure_category": None,
        }
        measured_fetcher = instrument_fetcher(fetcher, metrics)
        paging = {}
        source = {
            "id": "experiment-" + group["id"], "name": group["name"],
            "kind": "arxiv_api", "query": group["query"],
            "max_results": group.get("max_results", 50), "max_pages": 1,
            "category": "retrieval-experiment",
        }
        try:
            candidates, attempts = bounded_retry(
                lambda: collect_arxiv(source, since=since, fetcher=measured_fetcher,
                                      paging=paging, sleep=sleep),
                attempts=2, sleep=sleep, backoff_seconds=3,
            )
            status, error = "observed", None
        except (OSError, TimeoutError, ConnectionError, ValueError, RuntimeError, ET.ParseError) as exc:
            candidates, attempts = [], metrics["request_count"]
            status, error = "unavailable", {
                "type": type(exc).__name__, "category": failure_category(exc)
            }

        by_id = {}
        for candidate in candidates:
            by_id.setdefault(paper_id(candidate["candidate_id"]), candidate)
        ids = set(by_id)
        for pid, candidate in by_id.items():
            all_candidates_by_id.setdefault(pid, candidate)
        group_seed_hits = ids & eligible
        incremental_seed_hits = group_seed_hits - baseline_seed_hits
        incremental_ids = ids - baseline_ids
        all_group_ids.update(ids)
        all_incremental_ids.update(incremental_ids)
        all_incremental_seed_hits.update(incremental_seed_hits)

        screening, previews = Counter(), []
        for pid, candidate in sorted(
            by_id.items(),
            key=lambda item: (item[1].get("published_at") or "", item[0]),
            reverse=True,
        ):
            label, signals = relevance_for(" ".join((candidate.get("title", ""), candidate.get("excerpt", ""))))
            screening[label or "out_of_scope"] += 1
            if len(previews) < 15:
                previews.append({
                    "paper_id": pid, "title": candidate["title"], "url": candidate["url"],
                    "published_at": candidate.get("published_at"),
                    "predicted_relevance": label or "out_of_scope",
                    "screening_signals": signals[:8], "excerpt": candidate.get("excerpt", "")[:600],
                    "is_known_seed": pid in eligible, "was_in_baseline": pid in baseline_ids,
                })

        group_reports.append({
            "id": group["id"], "name": group["name"], "query": group["query"],
            "status": status, "error": error, "attempts": attempts,
            "request_diagnostics": request_diagnostics_snapshot(metrics),
            "candidate_observation_count": len(candidates),
            "api_raw_items_scanned": paging.get("raw_items_scanned", 0),
            "unique_paper_count": len(ids),
            "baseline_overlap_count": len(ids & baseline_ids),
            "incremental_unique_count": len(incremental_ids),
            "known_seed_hits": sorted(group_seed_hits),
            "incremental_known_seed_hits": sorted(incremental_seed_hits),
            "paging": paging, "rule_screening_counts": dict(sorted(screening.items())),
            "preview": previews,
        })

    combined_seed_hits = baseline_seed_hits | all_incremental_seed_hits
    predicted = Counter()
    for candidate in all_candidates_by_id.values():
        label, _ = relevance_for(" ".join((candidate.get("title", ""), candidate.get("excerpt", ""))))
        predicted[label or "out_of_scope"] += 1
    candidate_total = sum(row["candidate_observation_count"] for row in group_reports)
    api_raw_total = sum(row["api_raw_items_scanned"] for row in group_reports)
    total_unique_by_group = sum(row["unique_paper_count"] for row in group_reports)
    all_ok = all(row["status"] == "observed" for row in group_reports)
    return {
        "schema_version": "1.0", "experiment_id": config.get("experiment_id"),
        "discovery_generated_at": discovery["generated_at"], "lookback_days": lookback_days,
        "status": "complete" if all_ok else "partial", "scorable": all_ok,
        "baseline_recall": {
            "hits": len(baseline_seed_hits), "eligible": baseline.get("eligible_count", len(eligible)),
            "recall": baseline.get("rates", {}).get("100", {}).get("recall"),
        },
        "summary": {
            "query_group_count": len(groups),
            "successful_group_count": sum(row["status"] == "observed" for row in group_reports),
            "request_count": sum(row["request_diagnostics"]["request_count"] for row in group_reports),
            "api_raw_items_scanned": api_raw_total,
            "candidate_observation_count": candidate_total,
            "unique_papers_across_groups": len(all_group_ids),
            "cross_group_duplicate_count": total_unique_by_group - len(all_group_ids),
            "baseline_overlap_count": len(all_group_ids & baseline_ids),
            "incremental_unique_papers": len(all_incremental_ids),
            "known_seed_hits_before": len(baseline_seed_hits),
            "incremental_known_seed_hits": sorted(all_incremental_seed_hits),
            "known_seed_hits_after": len(combined_seed_hits),
            "known_seed_denominator": len(eligible),
            "known_seed_recall_after": round(len(combined_seed_hits) / len(eligible), 4) if eligible and all_ok else None,
            "rule_screening_counts_unique_papers_unvalidated": dict(sorted(predicted.items())),
            "measured_precision": None,
            "precision_note": "Precision is not measurable: experiment candidates have not been independently human-labelled. Rule-screening counts are unvalidated triage signals, not precision.",
        },
        "groups": group_reports,
        "interpretation_limits": [
            "This is a one-page, one-run query experiment, not a statistically controlled or exhaustive search.",
            "Known-seed recall uses a curated 16-paper calibration set and is not corpus-wide recall.",
            "New-result relevance precision is not measured because experiment results are not independently human-labelled.",
            "Rule-screening labels are heuristic triage only and must not be treated as verified relevance.",
            "A full page indicates possible truncation; a short page does not prove complete topic coverage.",
            "Candidate query groups do not change production source queries or enter the production review queue.",
        ],
    }


def markdown_report(report):
    summary = report.get("summary", {})
    lines = [
        "# AI Chip — isolated arXiv retrieval expansion experiment", "",
        f"- Experiment: {report.get('experiment_id')}",
        f"- Baseline discovery: {report.get('discovery_generated_at')}",
        f"- Status: **{report.get('status')}** · scorable: **{report.get('scorable')}**",
    ]
    if report.get("skip_reason"):
        lines.extend(["", "Skipped: " + report["skip_reason"]])
        return "\n".join(lines) + "\n"
    lines.extend([
        "", "## Aggregate result", "",
        f"- Requests: {summary.get('request_count', 0)}",
        f"- API raw entries scanned: {summary.get('api_raw_items_scanned', 0)}",
        f"- Candidate observations after date filtering: {summary.get('candidate_observation_count', 0)}",
        f"- Unique papers across groups: {summary.get('unique_papers_across_groups', 0)}",
        f"- New unique papers beyond baseline: {summary.get('incremental_unique_papers', 0)}",
        f"- Cross-group duplicates: {summary.get('cross_group_duplicate_count', 0)}",
        f"- New known-seed hits: {len(summary.get('incremental_known_seed_hits', []))}",
        f"- Curated known-seed recall after expansion: {summary.get('known_seed_hits_after', 0)} / {summary.get('known_seed_denominator', 0)} ({summary.get('known_seed_recall_after')})",
        "- Measured precision: **not available** — independent labels are required.",
        "", "## Query groups", "",
        "| Group | Status | Unique | New vs baseline | Seed hits | Page cap |",
        "|---|---|---:|---:|---:|---|",
    ])
    for row in report.get("groups", []):
        lines.append(
            f"| {row['name']} | {row['status']} | {row['unique_paper_count']} | "
            f"{row['incremental_unique_count']} | {len(row['known_seed_hits'])} | "
            f"{(row.get('paging') or {}).get('paging_cap_reached')} |"
        )
    for row in report.get("groups", []):
        lines.extend(["", f"### {row['name']}", "", "Query: " + row["query"]])
        lines.append("Rule-screening counts (unvalidated): " + json.dumps(row["rule_screening_counts"], ensure_ascii=False))
        if row.get("error"):
            lines.append("Error: " + json.dumps(row["error"]))
        lines.extend(["", "Top returned candidates (up to 15):", ""])
        for item in row.get("preview", []):
            lines.append(
                f"- [{item['title']}]({item['url']}) — {item['predicted_relevance']}"
                + (" · known seed" if item["is_known_seed"] else "")
                + (" · already in baseline" if item["was_in_baseline"] else "")
            )
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend("- " + note for note in report.get("interpretation_limits", []))
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_experiment(
            json.loads(args.config.read_text(encoding="utf-8")),
            json.loads(args.discovery.read_text(encoding="utf-8")),
            json.loads(args.baseline.read_text(encoding="utf-8")),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown_report(report), encoding="utf-8")
        print(markdown_report(report))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
