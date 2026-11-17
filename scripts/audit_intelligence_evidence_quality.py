#!/usr/bin/env python3
"""Audit evidence provenance and quote traceability without scoring claim truth.

Publisher diversity, declared independence labels and source classes are
descriptive metadata. None establishes independent corroboration or truth.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from extract_intelligence_claims import clean

REQUIRED_SOURCE_FIELDS = (
    "candidate_id", "source_id", "publisher", "source_type",
    "independence", "url", "published_at", "evidence_scope",
)
DECLARED_INDEPENDENCE = {"vendor", "project", "independent", "unknown"}
EVIDENCE_CLASSES = {
    "research_preprint", "vendor_primary_statement",
    "project_maintainer_statement", "repository_metadata",
    "independent_reporting", "unclassified_source",
}


def valid_https(url):
    if not isinstance(url, str):
        return False
    try:
        parsed = urlsplit(url)
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def parse_date(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def audit_evidence_quality(discovery, claims_report, graph, *, generated_at=None):
    if not isinstance(discovery, dict) or discovery.get("schema_version") != "1.1":
        raise ValueError("discovery must be read-only schema 1.1")
    if not isinstance(claims_report, dict) or claims_report.get("schema_version") != "1.0":
        raise ValueError("claims must use schema 1.0")
    if not isinstance(graph, dict) or graph.get("schema_version") != "1.0":
        raise ValueError("evidence graph must use schema 1.0")
    candidates = discovery.get("review_queue")
    claims = claims_report.get("claims")
    if not isinstance(candidates, list) or not isinstance(claims, list):
        raise ValueError("discovery review_queue and claims must be arrays")
    if claims_report.get("claim_count") != len(claims) or graph.get("input_claim_count") != len(claims):
        raise ValueError("claim count mismatch across evidence audit inputs")
    if graph.get("summary", {}).get("independently_verified_claims") != 0:
        raise ValueError("evidence graph must not claim automated factual verification")

    candidate_map = {}
    for candidate in candidates:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("candidate_id"), str):
            raise ValueError("every discovery candidate needs a candidate_id")
        cid = candidate["candidate_id"]
        if cid in candidate_map:
            raise ValueError("duplicate discovery candidate_id: " + cid)
        candidate_map[cid] = candidate

    claim_ids = set()
    source_docs, publishers = set(), set()
    source_independence = {}
    independence_counts, evidence_counts, assertion_counts = Counter(), Counter(), Counter()
    flag_counts = Counter()
    claim_rows = []
    quote_grounded = provenance_complete = 0
    metadata_mismatch = 0
    source_claim_counts = Counter()
    publisher_claim_counts = Counter()

    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("claim row must be an object")
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id or claim_id in claim_ids:
            raise ValueError("claim IDs must be nonempty and unique")
        claim_ids.add(claim_id)
        if claim.get("review_status") != "unverified_candidate":
            raise ValueError("all claims must remain unverified_candidate")
        candidate_id = claim.get("candidate_id")
        candidate = candidate_map.get(candidate_id)
        if candidate is None:
            raise ValueError("claim has no discovery candidate: " + claim_id)
        source = claim.get("source")
        if not isinstance(source, dict):
            raise ValueError("claim source must be an object: " + claim_id)

        flags, mismatched = [], []
        for field in REQUIRED_SOURCE_FIELDS:
            default = "unknown" if field in ("source_type", "independence", "evidence_scope") else None
            expected = candidate.get(field, default)
            if source.get(field, default) != expected:
                mismatched.append(field)
        if mismatched:
            metadata_mismatch += 1
            flags.append("claim_candidate_source_metadata_mismatch")

        url = source.get("url")
        if not valid_https(url):
            flags.append("invalid_or_missing_https_source_url")
        else:
            source_docs.add(url)
            source_claim_counts[url] += 1
            source_independence.setdefault(url, source.get("independence", "unknown"))

        publisher = source.get("publisher")
        if isinstance(publisher, str) and publisher.strip():
            publishers.add(publisher.strip().casefold())
            publisher_claim_counts[publisher.strip()] += 1
        else:
            flags.append("missing_publisher")

        independence = source.get("independence")
        missing = []
        for field, value in (
            ("publisher", publisher), ("source_type", source.get("source_type")),
            ("independence", independence), ("evidence_scope", source.get("evidence_scope")),
            ("published_at", source.get("published_at")), ("url", url),
        ):
            if not isinstance(value, str) or not value.strip() or value == "unknown":
                missing.append(field)
        if not parse_date(source.get("published_at")):
            if "published_at" not in missing:
                missing.append("valid_published_at")
        if not missing:
            provenance_complete += 1
        else:
            flags.append("incomplete_source_provenance")

        if independence not in DECLARED_INDEPENDENCE:
            flags.append("unrecognized_independence_label")
            independence_counts["unrecognized_or_missing"] += 1
        else:
            independence_counts[independence] += 1

        evidence_class = claim.get("evidence_class") or "unclassified_source"
        if evidence_class not in EVIDENCE_CLASSES:
            evidence_class = "unclassified_source"
            flags.append("unrecognized_evidence_class")
        evidence_counts[evidence_class] += 1
        assertion_class = claim.get("assertion_class") or "unclassified"
        assertion_counts[assertion_class] += 1

        excerpt = clean(candidate.get("excerpt") or candidate.get("body_excerpt") or "")
        quote = clean(claim.get("evidence_quote") or "")
        statement = clean(claim.get("statement") or "")
        grounded = bool(quote and excerpt and quote in excerpt)
        if grounded:
            quote_grounded += 1
        else:
            flags.append("evidence_quote_not_found_in_candidate_excerpt")
        if not statement or statement != quote:
            flags.append("claim_statement_quote_mismatch")

        for flag in flags:
            flag_counts[flag] += 1
        claim_rows.append({
            "claim_id": claim_id,
            "candidate_id": candidate_id,
            "publisher": publisher,
            "source_type": source.get("source_type"),
            "independence_label": independence,
            "evidence_class": evidence_class,
            "assertion_class": assertion_class,
            "quote_grounded": grounded,
            "source_metadata_mismatch_fields": mismatched,
            "missing_provenance_fields": missing,
            "review_status": "unverified_candidate",
            "flags": flags,
        })

    if graph.get("summary", {}).get("unreviewed_claims") != len(claims):
        raise ValueError("evidence graph unreviewed claim count mismatch")

    graph_edges = graph.get("edges", [])
    graph_nodes = graph.get("nodes", [])
    if not isinstance(graph_edges, list) or not isinstance(graph_nodes, list):
        raise ValueError("evidence graph nodes and edges must be arrays")
    origin_ids = {node.get("id") for node in graph_nodes
                  if isinstance(node, dict) and node.get("type") == "reviewer_assigned_evidence_origin"}
    annotated_origin_edges = [
        edge for edge in graph_edges
        if isinstance(edge, dict) and edge.get("relation") == "reviewer_assigned_origin"
        and edge.get("to") in origin_ids
    ]
    origin_keys = {
        node.get("origin_key") for node in graph_nodes
        if isinstance(node, dict) and node.get("type") == "reviewer_assigned_evidence_origin"
        and isinstance(node.get("origin_key"), str)
    }
    duplicate_clusters = graph.get("duplicate_clusters", [])
    if not isinstance(duplicate_clusters, list):
        raise ValueError("duplicate_clusters must be an array")
    duplicate_summary = {
        "cluster_count": len(duplicate_clusters),
        "multi_document_cluster_count": sum(
            row.get("distinct_source_document_count", 0) > 1
            for row in duplicate_clusters if isinstance(row, dict)
        ),
        "independent_corroboration_claimed": False,
    }

    total = len(claims)
    summary = {
        "claim_count": total,
        "quote_grounded_claims": quote_grounded,
        "quote_grounding_rate": round(quote_grounded / total, 4) if total else 0.0,
        "provenance_complete_claims": provenance_complete,
        "provenance_completeness_rate": round(provenance_complete / total, 4) if total else 0.0,
        "claims_with_source_metadata_mismatch": metadata_mismatch,
        "distinct_source_documents": len(source_docs),
        "distinct_publishers": len(publishers),
        "independence_label_counts": dict(sorted(independence_counts.items())),
        "evidence_class_counts": dict(sorted(evidence_counts.items())),
        "assertion_class_counts": dict(sorted(assertion_counts.items())),
        "reviewer_assigned_origin_count": len(origin_keys),
        "source_documents_with_reviewer_origin_annotation": len({edge.get("from") for edge in annotated_origin_edges}),
        "duplicate_statement_clusters": duplicate_summary,
        "claims_remaining_unverified": total,
        "flag_counts": dict(sorted(flag_counts.items())),
    }
    return {
        "schema_version": "1.0",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": summary,
        "publishers": [
            {"publisher": name, "claim_count": count}
            for name, count in sorted(publisher_claim_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "source_documents": [
            {"url": url, "claim_count": source_claim_counts[url],
             "independence_label": source_independence[url]}
            for url in sorted(source_docs)
        ],
        "claim_audits": claim_rows,
        "policy": (
            "This report measures provenance completeness and quote traceability only. "
            "Publisher diversity, source classes and declared independence labels are metadata, "
            "not proof of independent corroboration, peer review, measurement validity or factual truth. "
            "All Claim candidates remain unverified."
        ),
    }


def markdown_report(report):
    s = report["summary"]
    lines = [
        "# Intelligence Evidence Quality Audit", "",
        f"- Claim candidates: **{s['claim_count']}**",
        f"- Exact excerpt-grounded quotes: **{s['quote_grounded_claims']} / {s['claim_count']}** ({s['quote_grounding_rate']:.1%})",
        f"- Complete source provenance records: **{s['provenance_complete_claims']} / {s['claim_count']}** ({s['provenance_completeness_rate']:.1%})",
        f"- Claim/candidate metadata mismatches: **{s['claims_with_source_metadata_mismatch']}**",
        f"- Source documents / publishers: **{s['distinct_source_documents']} / {s['distinct_publishers']}**",
        f"- Reviewer-assigned evidence origins: **{s['reviewer_assigned_origin_count']}**",
        f"- Duplicate wording clusters: **{s['duplicate_statement_clusters']['cluster_count']}**",
        "",
        "## Declared source independence labels", "",
        "| Label | Claim rows |", "|---|---:|",
    ]
    for label, count in s["independence_label_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines += ["", "## Evidence classes", "", "| Class | Claim rows |", "|---|---:|"]
    for label, count in s["evidence_class_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines += ["", "## Audit flags", ""]
    if s["flag_counts"]:
        for flag, count in s["flag_counts"].items():
            lines.append(f"- {flag}: **{count}**")
    else:
        lines.append("- None")
    lines += [
        "", "## Interpretation limits", "",
        "These are provenance and traceability diagnostics, not a composite quality score. "
        "A quote appearing in a fetched excerpt does not establish that it supports the extracted interpretation. "
        "Publisher diversity and an 'independent' metadata label do not establish independent corroboration. "
        "A research preprint is not necessarily peer reviewed. All claims remain unverified until human review.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    try:
        discovery = json.loads(args.discovery.read_text(encoding="utf-8"))
        claims = json.loads(args.claims.read_text(encoding="utf-8"))
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        report = audit_evidence_quality(discovery, claims, graph)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(markdown_report(report) + "\n", encoding="utf-8")
        print(markdown_report(report))
    except (OSError, json.JSONDecodeError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
