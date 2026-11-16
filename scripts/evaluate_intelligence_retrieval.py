#!/usr/bin/env python3
"""Evaluate bounded arXiv retrieval against a separately curated relevance seed.

This is known-item, observed-window Recall@K, NOT corpus-level retrieval recall.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

K_VALUES = (25, 50, 100)
ARXIV_ID = re.compile(r"^(?:arxiv:)?((?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7}))(?:v\d+)?$", re.I)


def paper_id(value):
    """Canonicalize explicit arXiv IDs/abs URLs, dropping *only* the version."""
    value = str(value or "").strip()
    if value.startswith("https://arxiv.org/abs/"):
        value = value.split("/abs/", 1)[1].split("?", 1)[0].split("#", 1)[0]
    match = ARXIV_ID.fullmatch(value)
    if not match:
        raise ValueError("Invalid arXiv ID: " + value[:80])
    return match.group(1).casefold()


def as_utc(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected ISO-8601 UTC timestamp")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timezone missing")
    return dt.astimezone(timezone.utc)


def evaluate(golden, discovery, *, registry=None):
    if golden.get("schema_version") != "1.0":
        raise ValueError("Unsupported recall set version")
    examples = golden.get("examples")
    if not isinstance(examples, list) or not examples:
        raise ValueError("Recall set requires nonempty examples")
    generated = as_utc(discovery["generated_at"])
    lookback = discovery.get("lookback_days")
    if type(lookback) is not int or lookback < 1:
        raise ValueError("Discovery report requires positive lookback_days")
    cutoff = generated - timedelta(days=lookback)
    sources = {r["source_id"]: r for r in discovery["source_results"] if r.get("kind") == "arxiv_api"}
    if not sources:
        raise ValueError("No arXiv sources in discovery")
    configured = {}
    if registry is not None:
        configured = {s["id"]: s for s in registry.get("sources", []) if s.get("kind") == "arxiv_api" and s.get("active", True)}
        if set(sources) != set(configured):
            raise ValueError("Discovery arXiv source IDs differ from active registry")

    # The discovery pipeline appends raw observations in source page order.
    # Preserve this order rather than globally sorting by publication timestamp.
    positions = defaultdict(dict)
    source_positions = Counter()
    for row in discovery.get("all_observations", []):
        sid = row.get("source_id")
        if sid not in sources:
            continue
        pid = paper_id(row.get("candidate_id"))
        source_positions[sid] += 1
        positions[pid].setdefault(sid, source_positions[sid])

    # Explicit K is a per-shard depth, not a global ordering across sources.
    scored, out_of_window, unknown_date, missing, matched = [], [], [], [], []
    ids_seen = set()
    for entry in examples:
        pid = paper_id(entry.get("paper_id"))
        if pid in ids_seen:
            raise ValueError("Duplicate recall paper_id: " + pid)
        ids_seen.add(pid)
        if entry.get("expected_relevance") not in ("direct_ai_compute", "adjacent_ai_systems"):
            raise ValueError("Recall benchmark must contain relevant papers only")
        if not entry.get("title") or not entry.get("rationale") or not entry.get("source_url"):
            raise ValueError("Missing title, rationale or source_url: " + pid)
        if paper_id(entry["source_url"]) != pid:
            raise ValueError("Source URL and paper_id mismatch: " + pid)

        published = entry.get("published_on")
        item = {
            "paper_id": pid, "title": entry["title"],
            "expected_relevance": entry["expected_relevance"],
            "rationale": entry["rationale"],
            "published_on": published,
            "abstract_excerpt": entry.get("abstract_excerpt", ""),
            "arxiv_categories": entry.get("arxiv_categories", []),
            "category_metadata_status": entry.get("category_metadata_status", "not_captured"),
            "category_evidence_url": entry.get("category_evidence_url"),
            "candidate_query_terms": entry.get("candidate_query_terms", []),
            "positions": positions.get(pid, {}),
        }
        if not published:
            unknown_date.append(item)
            continue
        if not isinstance(published, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", published):
            raise ValueError("published_on must be an ISO calendar date: " + pid)
        when = datetime.strptime(published, "%Y-%m-%d").date()
        if not cutoff.date() <= when <= generated.date():
            out_of_window.append(item)
            continue
        scored.append(item)
        if item["positions"]:
            matched.append(item)
        else:
            missing.append(item)

    # An unavailable shard makes misses ambiguous, not hard negatives.
    unavailable = [sid for sid, row in sources.items() if row.get("status") != "observed"]
    complete = not unavailable
    rates = {}
    for k in K_VALUES:
        hits = sum(any(index <= k for index in x["positions"].values()) for x in scored)
        rates[str(k)] = {
            "hits": hits, "denominator": len(scored),
            "recall": round(hits / len(scored), 4) if scored else None,
        }
    coverage = []
    for sid, row in sources.items():
        pg = row.get("pagination") or {}
        coverage.append({
            "source_id": sid, "status": row.get("status"),
            "records": source_positions[sid],
            "per_page": pg.get("per_page"),
            "max_pages": pg.get("max_pages"),
            "paging_cap_reached": pg.get("paging_cap_reached"),
        })

    return {
        "schema_version": "1.0", "benchmark_id": golden.get("benchmark_id"),
        "discovery_generated_at": discovery["generated_at"],
        "lookback_days": lookback, "window_start_at": cutoff.isoformat(),
        "scope": "curated known-item, bounded observed-window retrieval; per-shard Recall@K",
        "scorable": complete and bool(scored),
        "unavailable_arxiv_sources": unavailable,
        "dataset_count": len(examples), "eligible_count": len(scored),
        "out_of_window_count": len(out_of_window), "unknown_date_count": len(unknown_date),
        "rates": rates, "matched": matched, "missing": missing,
        "out_of_window": out_of_window, "unknown_date": unknown_date,
        "sources": coverage,
        "limitations": [
            "Curated from historically discovered and manually selected papers; not representative or independent.",
            "Recall@K uses order of observed items per source, not a global relevance ranking.",
            "A missing paper can be due to search terms, arXiv categories, page caps, indexing or query timing; no cause is inferred.",
            "Unavailable shards make the run unscorable; the rates, if present, are diagnostic only.",
            "Full last-page flags indicate possible truncation; absent results are not necessarily query misses.",
            "Only the manually dated within-window items are in the denominator; no inference about the full publication corpus.",
        ],
    }


def markdown_report(report):
    lines = [
        "# AI Chip — arXiv known-item retrieval benchmark", "",
        f"- Benchmark: \`{report['benchmark_id']}\`",
        f"- Discovery run generated: {report['discovery_generated_at']}",
        f"- Window: {report['lookback_days']} days",
        f"- Curated papers: {report['dataset_count']}, eligible: {report['eligible_count']}",
        f"- Out of window: {report['out_of_window_count']}, unknown publication date: {report['unknown_date_count']}",
        f"- Scorable: **{'yes' if report['scorable'] else 'no'}**", "",
        "| Per-shard depth | Matched / eligible | Known-item recall |",
        "|---|---:|---:|",
    ]
    for k, value in report["rates"].items():
        rate = f"{value['recall']:.1%}" if value["recall"] is not None else "N/A"
        lines.append(f"| @ {k} | {value['hits']} / {value['denominator']} | {rate} |")
    lines.extend(["", "## arXiv source coverage", "",
                  "| Source | Status | Records | Page cap reached |",
                  "|---|---|---:|---|"])
    for s in report["sources"]:
        lines.append(f"| {s['source_id']} | {s['status']} | {s['records']} | {s['paging_cap_reached']} |")
    lines.extend(["", "## Eligible but not observed", ""])
    for entry in report["missing"]:
        lines.append(f"- \`{entry['paper_id']}\` — {entry['title']}")
    if not report["missing"]:
        lines.append("- None")
    lines.extend(["", "## Limitations", ""])
    for note in report["limitations"]:
        lines.append("- " + note)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    golden = json.loads(args.golden.read_text(encoding="utf-8"))
    discovery = json.loads(args.discovery.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8")) if args.registry else None
    report = evaluate(golden, discovery, registry=registry)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = markdown_report(report)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(summary, encoding="utf-8")
    print(summary)
    # A source outage is not a relevance-regression failure. Surface it as
    # non-scorable without discarding the discovery artifact.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
