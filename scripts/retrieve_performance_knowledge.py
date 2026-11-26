#!/usr/bin/env python3
"""Retrieve bounded performance knowledge for a new engineering question."""
import argparse
import json
import re
from pathlib import Path

from review_performance_experiment_evidence import require, digest
from assess_performance_knowledge_applicability import assess_entry

STOP = {"the", "and", "for", "with", "from", "into", "that", "this", "under",
        "when", "what", "how", "does", "can", "using", "performance", "issue",
        "problem", "system", "model", "current", "target"}


def tokens(value):
    words = re.findall(r"[a-z0-9][a-z0-9_.+-]*", str(value).casefold())
    return {word for word in words if len(word) > 1 and word not in STOP}


def metric_status(entry, metric):
    if metric is None:
        return "not_assessed"
    source = entry.get("scope", {}).get("metric", {})
    keys = ("key", "unit", "direction")
    if not isinstance(metric, dict) or not all(k in metric for k in keys):
        return "incomplete_target_metric"
    return "exact_match" if all(source.get(k) == metric.get(k) for k in keys) else "mismatch_or_unknown"


def retrieve(catalog, query, target, metric=None, limit=20):
    require(isinstance(catalog, dict) and catalog.get("schema_version") == "1.0"
            and isinstance(catalog.get("entries"), list), "Invalid knowledge catalog")
    require(isinstance(query, str) and query.strip(), "A non-empty engineering question is required")
    require(isinstance(target, dict) and target, "A non-empty target context is required")
    require(type(limit) is int and 1 <= limit <= 100, "Limit must be between 1 and 100")
    query_terms = tokens(query)
    candidates = []
    for entry in catalog["entries"]:
        require(isinstance(entry, dict) and entry.get("knowledge_status") == "human_reviewed_claim",
                "Catalog contains a non-reviewed or invalid knowledge entry")
        fields = {
            "topic": entry.get("topic", ""),
            "hypothesis": entry.get("hypothesis", ""),
            "reviewer_interpretation": entry.get("reviewer_interpretation", ""),
            "applicability": entry.get("applicability", ""),
            "limitations": entry.get("limitations", ""),
        }
        searchable = {name: tokens(value) for name, value in fields.items()}
        matched = sorted(query_terms & set().union(*searchable.values())) if query_terms else []
        topic_match = bool(query_terms & searchable["topic"])
        phrase_match = bool(query_terms & (searchable["hypothesis"] | searchable["reviewer_interpretation"]))
        applicability = assess_entry(entry, target)
        metric_match = metric_status(entry, metric)
        verdict = entry.get("verdict")
        context = applicability["applicability_status"]
        if context == "declared_context_match" and metric_match in ("exact_match", "not_assessed"):
            tier = "priority_human_review"
            reason = "Declared context matches; metric is compatible or was not supplied."
        elif context == "declared_context_match" and metric_match == "mismatch_or_unknown":
            tier = "exploratory_only"
            reason = "Context matches but target metric differs or is unknown."
        elif context == "insufficient_context":
            tier = "exploratory_only"
            reason = "One or more source context fields are missing from the target."
        else:
            tier = "not_applicable_under_declared_context"
            reason = "At least one declared context field differs."
        if verdict == "refuted":
            tier = "exploratory_only"
            reason = "Refuted claim retained as counter-evidence; never a reusable recommendation."
        elif verdict != "supported":
            tier = "exploratory_only"
            reason = "Knowledge verdict is not a reusable Supported claim."
        candidates.append({
            "knowledge_id": entry["knowledge_id"],
            "topic": entry.get("topic"),
            "verdict": verdict,
            "knowledge_status": entry.get("knowledge_status"),
            "query_matches": matched,
            "topic_match": topic_match,
            "technical_text_match": phrase_match,
            "applicability_status": context,
            "metric_compatibility": metric_match,
            "retrieval_tier": tier,
            "triage_reason": reason,
            "missing_context_fields": [x["field"] for x in applicability["comparisons"] if x["status"] == "unknown"],
            "mismatched_context_fields": [x["field"] for x in applicability["comparisons"] if x["status"] == "mismatch"],
            "unassessed_target_fields": applicability["unassessed_target_fields"],
            "applicability_report": applicability,
            "reviewer_interpretation": entry.get("reviewer_interpretation"),
            "applicability": entry.get("applicability"),
            "limitations": entry.get("limitations"),
            "evidence_refs": entry.get("evidence", []),
            "evidence_identity": entry.get("evidence_identity"),
            "review_sha256": entry.get("review_sha256"),
        })
    tier_order = {"priority_human_review": 0, "exploratory_only": 1,
                  "not_applicable_under_declared_context": 2}
    candidates.sort(key=lambda x: (
        tier_order[x["retrieval_tier"]],
        0 if x["topic_match"] else 1,
        0 if x["technical_text_match"] else 1,
        -len(x["query_matches"]),
        x["knowledge_id"]))
    selected = candidates[:limit]
    contradictions = catalog.get("potential_contradictions", [])
    selected_ids = {x["knowledge_id"] for x in selected}
    related_conflicts = [c for c in contradictions
                         if c.get("knowledge_id_a") in selected_ids
                         or c.get("knowledge_id_b") in selected_ids]
    return {
        "schema_version": "1.0",
        "report_type": "performance_knowledge_retrieval",
        "query": query,
        "query_sha256": digest(query),
        "target_context": target,
        "target_context_sha256": digest(target),
        "result_count": len(selected),
        "catalog_entry_count": len(candidates),
        "results": selected,
        "related_potential_contradictions": related_conflicts,
        "policy": {
            "retrieval_is_not_recommendation": True,
            "context_mismatch_blocks_direct_reuse": True,
            "human_review_required": True,
            "automatic_configuration_advice": False,
            "ranking_is_heuristic_not_learned": True,
        },
        "limitations": [
            "Keyword overlap is a retrieval aid, not semantic equivalence or causal similarity.",
            "A priority result still requires human review of original evidence and measurement boundaries.",
            "A refuted claim is retrieved as counter-evidence, not as a recommended practice.",
            "No performance outcome is predicted and no configuration is recommended.",
            "Catalog integrity and source authenticity must be checked in the repository workflow."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--metric", type=Path)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = [args.catalog, args.target] + ([args.metric] if args.metric else [])
    require(args.output.resolve() not in {p.resolve() for p in inputs},
            "Output must not overwrite an input")
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    target = json.loads(args.target.read_text(encoding="utf-8"))
    metric = json.loads(args.metric.read_text(encoding="utf-8")) if args.metric else None
    report = retrieve(catalog, args.query, target, metric, args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
