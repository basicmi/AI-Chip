#!/usr/bin/env python3
"""Diagnose missed known arXiv items against query vocabulary and category coverage.

This is an offline lexical/category proxy, not a replay of arXiv's search engine.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ALL_TERM = re.compile(r'all:"([^"]+)"|all:([A-Za-z0-9][A-Za-z0-9._-]*)', re.I)
CATEGORY = re.compile(r"cat:([A-Za-z0-9.]+)", re.I)


def normalize(value):
    value = str(value or "").casefold().replace("-", " ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def contains_phrase(text, phrase):
    haystack, needle = normalize(text), normalize(phrase)
    if not needle:
        return False
    return f" {needle} " in f" {haystack} "


def query_profile(query):
    return {
        "categories": set(CATEGORY.findall(query or "")),
        "terms": [a or b for a, b in ALL_TERM.findall(query or "")],
    }


def diagnose(golden, evaluation, registry):
    sources = {
        row["id"]: query_profile(row.get("query", ""))
        for row in registry.get("sources", [])
        if row.get("kind") == "arxiv_api" and row.get("active", True)
    }
    result_sources = {row["source_id"] for row in evaluation.get("sources", [])}
    if sources and sources.keys() != result_sources:
        raise ValueError("Evaluation and registry arXiv source IDs differ")
    entries = {}
    for entry in golden.get("examples", []):
        pid = entry.get("paper_id")
        if not pid:
            raise ValueError("Golden entry missing paper_id")
        key = re.sub(r"v\d+$", "", pid.removeprefix("arxiv:"))
        if key in entries:
            raise ValueError("Duplicate golden paper: " + key)
        entries[key] = entry

    diagnoses = []
    counts = Counter()
    for miss in evaluation.get("missing", []):
        key = miss["paper_id"]
        entry = entries.get(key)
        if entry is None:
            raise ValueError("Missing item not found in golden set: " + key)
        text = " ".join((entry.get("title", ""), entry.get("abstract_excerpt", "")))
        cats = set(entry.get("arxiv_categories", []))
        category_status = entry.get("category_metadata_status", "not_captured")
        covered, uncovered = [], sorted(cats - set().union(*(p["categories"] for p in sources.values()))) if cats and sources else sorted(cats)
        term_matches, eligible_sources = {}, []
        for sid, profile in sources.items():
            if cats and category_status != "not_captured":
                if not cats.intersection(profile["categories"]):
                    continue
            eligible_sources.append(sid)
            matches = [term for term in profile["terms"] if contains_phrase(text, term)]
            if matches:
                term_matches[sid] = matches
            if cats and cats.intersection(profile["categories"]):
                covered.append(sid)

        if cats and category_status != "not_captured" and not covered:
            classification = "category_filter_gap"
        elif term_matches:
            classification = "query_lexical_match_but_not_returned"
        elif cats and category_status != "not_captured":
            classification = "query_vocabulary_gap"
        else:
            classification = "lexical_gap_category_unknown"

        suggestions = entry.get("candidate_query_terms", [])
        ungrounded = [term for term in suggestions if not contains_phrase(text, term)]
        if ungrounded:
            raise ValueError(f"Ungrounded candidate query terms for {key}: {ungrounded}")
        counts[classification] += 1
        diagnoses.append({
            "paper_id": key,
            "title": entry["title"],
            "expected_relevance": entry["expected_relevance"],
            "classification": classification,
            "arxiv_categories": sorted(cats),
            "category_metadata_status": category_status,
            "category_evidence_url": entry.get("category_evidence_url"),
            "category_covered_sources": sorted(covered),
            "uncovered_categories": uncovered,
            "eligible_sources": eligible_sources,
            "existing_query_term_matches": term_matches,
            "candidate_query_terms": suggestions,
            "note": {
                "category_filter_gap": "Known categories do not overlap any active arXiv shard; verify category metadata before adding a category.",
                "query_lexical_match_but_not_returned": "At least one configured query phrase appears in title/abstract, but the item was not observed; inspect API semantics, ranking, index timing and page-cap truncation.",
                "query_vocabulary_gap": "At least one shard covers a known category, but none of its configured all: phrases appears in the title/abstract; candidate vocabulary may be missing.",
                "lexical_gap_category_unknown": "No configured phrase matched the title/abstract, but category metadata is absent or not authoritative; category coverage cannot be concluded.",
            }[classification],
        })

    return {
        "schema_version": "1.0",
        "benchmark_id": evaluation.get("benchmark_id"),
        "discovery_generated_at": evaluation.get("discovery_generated_at"),
        "scope": "diagnostic proxy for curated known-item misses; not a replay of arXiv query semantics",
        "missing_count": len(diagnoses),
        "classification_counts": dict(sorted(counts.items())),
        "diagnoses": diagnoses,
        "policy": [
            "Do not infer a confirmed root cause from lexical overlap alone.",
            "Category evidence tagged secondary_index is provisional; not_captured means unknown, not an empty category set.",
            "Candidate query terms are copied from title/abstract evidence and are proposals only.",
            "Do not automatically widen OR queries: broadening can increase page-cap competition and reduce precision.",
        ],
    }


def markdown_report(report):
    lines = [
        "# AI Chip — arXiv retrieval miss diagnosis", "",
        f"- Discovery: {report.get('discovery_generated_at')}",
        f"- Known-item misses: {report['missing_count']}",
        f"- Scope: {report['scope']}", "",
        "## Diagnosis summary", "",
        "| Classification | Papers |", "|---|---:|",
    ]
    for label, count in report["classification_counts"].items():
        lines.append(f"| {label} | {count} |")
    for item in report["diagnoses"]:
        lines.extend([
            "", f"## {item['paper_id']} — {item['title']}", "",
            f"- Diagnosis: **{item['classification']}**",
            f"- Categories: {', '.join(item['arxiv_categories']) or 'not captured'} ({item['category_metadata_status']})",
            f"- Category-covered shards: {', '.join(item['category_covered_sources']) or 'unknown / none'}",
            f"- Existing query phrase matches: {json.dumps(item['existing_query_term_matches'], ensure_ascii=False) if item['existing_query_term_matches'] else 'none'}",
            f"- Interpretation: {item['note']}",
            "- Candidate query terms: " + ", ".join(item["candidate_query_terms"]),
        ])
        if item.get("category_evidence_url"):
            lines.append(f"- Category metadata: {item['category_evidence_url']}")
    lines.extend(["", "## Guardrails", ""])
    lines.extend("- " + x for x in report["policy"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    report = diagnose(
        json.loads(args.golden.read_text(encoding="utf-8")),
        json.loads(args.evaluation.read_text(encoding="utf-8")),
        json.loads(args.registry.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(markdown_report(report), encoding="utf-8")
    print(markdown_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
