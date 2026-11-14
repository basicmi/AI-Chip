#!/usr/bin/env python3
"""Create a conservative review-only claim/evidence graph from PR #90 output.

Exact text duplicates may be clustered automatically. Comparisons of values
across sources require explicit reviewer-authored subject/metric/context keys.
No result is promoted to a verified hardware capability or measured benchmark.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ALLOWED_COMPARISON_KINDS = {"specification", "measurement", "availability", "capability"}
SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/+-]{0,199}$")


def digest(*parts):
    data = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:20]


def normalized_text(text):
    if not isinstance(text, str):
        return ""
    return " ".join(text.casefold().split()).rstrip(" .;:")


def canonical_url(url):
    if not isinstance(url, str):
        raise ValueError("source URL must be a string")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("source URL must be HTTPS without credentials")
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path.rstrip("/") or "/", parsed.query, ""))


def validate_annotations(annotations, claim_ids):
    if not isinstance(annotations, dict) or annotations.get("schema_version") != "1.0":
        raise ValueError("annotations must be a version 1.0 object")
    entries = annotations.get("claims", {})
    if not isinstance(entries, dict):
        raise ValueError("annotations.claims must be a mapping")
    for claim_id, row in entries.items():
        if claim_id not in claim_ids:
            raise ValueError("annotation refers to unknown claim ID: " + claim_id)
        if not isinstance(row, dict):
            raise ValueError("annotation must be an object for " + claim_id)
        required = {"subject_key", "metric_key", "context_key", "comparison_kind", "evidence_origin_key"}
        if set(row) != required:
            raise ValueError("annotation must contain exactly subject_key, metric_key, context_key, comparison_kind, evidence_origin_key")
        for name in ("subject_key", "metric_key", "context_key", "evidence_origin_key"):
            if not isinstance(row[name], str) or not SLUG.fullmatch(row[name]):
                raise ValueError("invalid reviewer-assigned " + name)
        if row["comparison_kind"] not in ALLOWED_COMPARISON_KINDS:
            raise ValueError("invalid comparison_kind")


def graph_for_claims(report, *, annotations=None, generated_at=None):
    if not isinstance(report, dict) or report.get("schema_version") != "1.0":
        raise ValueError("expected PR #90 claim extraction version 1.0")
    claims = report.get("claims")
    if not isinstance(claims, list):
        raise ValueError("input claims must be an array")
    ids = set()
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("claim must be an object")
        cid = claim.get("claim_id")
        if not isinstance(cid, str) or not cid or cid in ids:
            raise ValueError("claim ID missing or duplicated")
        ids.add(cid)
        if claim.get("review_status") != "unverified_candidate":
            raise ValueError("all input claims must remain unverified")
    annotations = annotations or {"schema_version": "1.0", "claims": {}}
    validate_annotations(annotations, ids)

    nodes = []
    edges = []
    origin_nodes = {}
    source_nodes = {}
    quote_groups = defaultdict(list)
    comparison_groups = defaultdict(list)
    claims_by_id = {claim["claim_id"]: claim for claim in claims}

    for claim in sorted(claims, key=lambda row: row["claim_id"]):
        cid = claim["claim_id"]
        source = claim.get("source")
        if not isinstance(source, dict):
            raise ValueError("claim source must be an object")
        url = canonical_url(source.get("url"))
        source_id = "source-" + digest(url)
        if source_id not in source_nodes:
            source_nodes[source_id] = {
                "id": source_id, "type": "source_document",
                "url": url, "publisher": source.get("publisher"),
                "source_type": source.get("source_type"),
                "independence": source.get("independence"),
            }
        nodes.append({"id": "claim:" + cid, "type": "claim_candidate",
                      "claim_id": cid, "statement": claim.get("statement"),
                      "topic": claim.get("topic"), "value": claim.get("value"),
                      "unit": claim.get("unit"), "review_status": "unverified_candidate"})
        edges.append({"from": "claim:" + cid, "to": source_id, "relation": "extracted_from"})
        statement = normalized_text(claim.get("statement"))
        # Same words do not imply independent measurements or true agreement.
        if statement:
            quote_groups[statement].append(cid)
        annotation = annotations["claims"].get(cid)
        if annotation:
            origin_id = "origin-" + digest(annotation["evidence_origin_key"])
            if origin_id not in origin_nodes:
                origin_nodes[origin_id] = {
                    "id": origin_id, "type": "reviewer_assigned_evidence_origin",
                    "origin_key": annotation["evidence_origin_key"]
                }
            edges.append({"from": source_id, "to": origin_id,
                          "relation": "reviewer_assigned_origin"})
            key = tuple(annotation[field] for field in
                        ("subject_key", "metric_key", "context_key", "comparison_kind"))
            comparison_groups[key].append(cid)
            subject_id = "subject-" + digest(annotation["subject_key"])
            nodes.append({"id": "subject-reference:" + cid, "type": "reviewer_assigned_subject_reference",
                          "subject_key": annotation["subject_key"]})
            edges.append({"from": "claim:" + cid, "to": "subject-reference:" + cid,
                          "relation": "reviewer_assigned_subject"})

    duplicates = []
    for quote, cids in sorted(quote_groups.items()):
        source_ids = {"source-" + digest(canonical_url(claims_by_id[cid]["source"]["url"]))
                      for cid in cids}
        if len(cids) < 2:
            continue
        duplicates.append({
            "cluster_id": "duplicate-" + digest(quote),
            "claim_ids": sorted(cids),
            "distinct_source_document_count": len(source_ids),
            "relationship": "exact_normalized_statement_match",
            "independent_corroboration": False,
            "review_status": "candidate_duplicate_only",
            "warning": "Identical wording, including syndication or multiple statements from one document, never proves independent corroboration.",
        })
        for cid in cids:
            edges.append({"from": "claim:" + cid, "to": "claim:" + sorted(cids)[0],
                          "relation": "same_normalized_statement_candidate"})
    comparisons = []
    for key, cids in sorted(comparison_groups.items()):
        if len(cids) < 2:
            continue
        subject, metric, context, kind = key
        rows = [(cid, claims_by_id[cid], annotations["claims"][cid]) for cid in sorted(cids)]
        origin_count = len({annotation["evidence_origin_key"] for _, _, annotation in rows})
        values = [(cid, claim.get("value"), str(claim.get("unit") or "").strip().casefold())
                  for cid, claim, _ in rows]
        numeric = [x for x in values if type(x[1]) in (int, float)]
        all_numeric = len(numeric) == len(rows)
        same_units = all_numeric and len({x[2] for x in numeric}) == 1 and bool(numeric[0][2])
        same_values = same_units and len({x[1] for x in numeric}) == 1
        difference = same_units and len({x[1] for x in numeric}) > 1
        qualifier_sets = {tuple(sorted(claim.get("qualifiers", []))) for _, claim, _ in rows}
        scope_sets = {str(claim.get("scope", {}).get("status")) + ":" +
                      str(claim.get("scope", {}).get("text")) for _, claim, _ in rows}
        context_consistent = len(qualifier_sets) == 1 and len(scope_sets) == 1
        if same_values and context_consistent:
            relation = "numerical_agreement_candidate"
        elif difference and context_consistent and kind == "specification":
            relation = "possible_specification_conflict"
        elif difference:
            relation = "different_values_require_context_review"
        elif not all_numeric:
            relation = "non_numeric_claims_not_automatically_comparable"
        else:
            relation = "unit_or_scope_mismatch"
        origin_warning = (
            "Reviewer-assigned origin labels differ; editorial independence is not independently verified."
            if origin_count > 1 else
            "Claims share an evidence origin; multiple documents do not count as independent corroboration."
        )
        comparisons.append({
            "comparison_id": "comparison-" + digest(*key),
            "subject_key": subject, "metric_key": metric, "context_key": context,
            "comparison_kind": kind, "claim_ids": sorted(cids),
            "origin_count": origin_count, "unit_comparable": bool(same_units),
            "status": relation, "review_status": "requires_human_review",
            "independently_verified": False,
            "independence_warning": origin_warning,
        })
        comparison_node = "comparison:" + digest(*key)
        nodes.append({"id": comparison_node, "type": "reviewer_scoped_comparison",
                      "status": relation, "review_status": "requires_human_review"})
        for cid in cids:
            edges.append({"from": "claim:" + cid, "to": comparison_node,
                          "relation": "candidate_comparison_member"})

    nodes.extend(source_nodes.values())
    nodes.extend(origin_nodes.values())
    nodes.sort(key=lambda row: row["id"])
    edges.sort(key=lambda row: (row["from"], row["to"], row["relation"]))
    now = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": "1.0", "generated_at": now,
        "input_claim_count": len(claims), "graph_node_count": len(nodes),
        "graph_edge_count": len(edges), "nodes": nodes, "edges": edges,
        "duplicate_clusters": duplicates, "scoped_comparisons": comparisons,
        "summary": {"exact_statement_duplicate_clusters": len(duplicates),
                    "annotated_comparison_groups": len(comparisons),
                    "possible_specification_conflicts": sum(
                        c["status"] == "possible_specification_conflict" for c in comparisons),
                    "independently_verified_claims": 0,
                    "unreviewed_claims": len(claims)},
        "policy": "The graph organizes unverified candidates. Automated text duplicates and reviewer-scoped numeric comparisons are not factual verification, causal evidence, independent reproduction, or production database updates.",
    }


def markdown_report(graph):
    lines = [
        "# AI Chip Intelligence — Evidence Graph Review", "",
        f"- Generated: {graph['generated_at']}",
        f"- Claim candidates: {graph['input_claim_count']}",
        f"- Exact-quote duplicate clusters: {graph['summary']['exact_statement_duplicate_clusters']}",
        f"- Reviewer-scoped comparison groups: {graph['summary']['annotated_comparison_groups']}",
        f"- Possible specification conflicts: {graph['summary']['possible_specification_conflicts']}",
        "- Independently verified claims: 0 (automatic verification prohibited)",
        "", "## Possible conflicts", "",
    ]
    conflicts = [row for row in graph["scoped_comparisons"] if row["status"] == "possible_specification_conflict"]
    if not conflicts:
        lines.append("No reviewer-scoped specification conflicts detected. This does not establish consistency.")
    for row in conflicts:
        lines.extend([f"### {row['subject_key']} / {row['metric_key']}",
                      f"- Context: {row['context_key']}",
                      f"- Candidate claim IDs: {', '.join(row['claim_ids'])}",
                      f"- Evidence origins: {row['origin_count']}",
                      f"- Independence: {row['independence_warning']}", ""])
    lines.extend(["", "## Exact text duplicates", ""])
    if not graph["duplicate_clusters"]:
        lines.append("No exact normalized statement duplicate clusters.")
    for row in graph["duplicate_clusters"][:100]:
        lines.append("- " + ", ".join(row["claim_ids"]) + " (not independent verification)")
    lines.extend(["", "## Review protocol", "",
                  "1. Read original URLs and confirm that each extracted quote is accurate.",
                  "2. Assign explicit subject, metric and configuration keys only when the evidence supports them.",
                  "3. Record the common underlying origin for syndication, reprints, copied releases and dependent benchmarks.",
                  "4. Recheck precision, sparsity, workload, peak-vs-measured, per-chip-vs-rack and units.",
                  "5. Treat numerical disagreements as review leads, never automatic factual contradictions.",
                  "6. No claim is promoted to verified without a separate governed review process."])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-path", type=Path)
    args = parser.parse_args()
    try:
        report = json.loads(args.input.read_text(encoding="utf-8"))
        annotations = json.loads(args.annotations.read_text(encoding="utf-8")) if args.annotations else None
        graph = graph_for_claims(report, annotations=annotations)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.summary_path:
            args.summary_path.parent.mkdir(parents=True, exist_ok=True)
            args.summary_path.write_text(markdown_report(graph), encoding="utf-8")
        print(f"PASS: {graph['input_claim_count']} unverified claims; "
              f"{graph['summary']['exact_statement_duplicate_clusters']} duplicate clusters; "
              f"{graph['summary']['annotated_comparison_groups']} reviewer-scoped comparisons.")
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
