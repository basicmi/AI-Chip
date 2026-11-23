#!/usr/bin/env python3
"""Prepare and evaluate human source-lineage review for exact-text duplicate clusters.

This is an origin-annotation worksheet, not automatic corroboration.
Different origin keys never establish independent evidence or factual truth.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

RELATIONSHIPS = (
    "original_material", "syndicated_reprint", "secondary_analysis",
    "independent_measurement_claim", "unknown",
)
KEY = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,119}$")


def prepare(graph, *, max_clusters=25):
    if type(max_clusters) is not int or not 1 <= max_clusters <= 100:
        raise ValueError("max_clusters must be between 1 and 100")
    if not isinstance(graph, dict) or graph.get("schema_version") != "1.0":
        raise ValueError("expected evidence graph schema 1.0")
    if graph.get("summary", {}).get("independently_verified_claims") != 0:
        raise ValueError("graph may not contain automatically verified Claims")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    clusters = graph.get("duplicate_clusters")
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(clusters, list):
        raise ValueError("evidence graph nodes/edges/duplicate_clusters must be arrays")
    source_nodes = {}
    claim_nodes = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("malformed evidence graph node")
        if node.get("type") == "source_document":
            sid = node.get("id")
            if not isinstance(sid, str) or sid in source_nodes:
                raise ValueError("duplicate or invalid graph source ID")
            url = node.get("url")
            if not isinstance(url, str) or not url.startswith("https://"):
                raise ValueError("source document must have HTTPS URL")
            source_nodes[sid] = node
        elif node.get("type") == "claim_candidate":
            claim_nodes.add(node.get("id"))
    claim_sources = {}
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("malformed evidence graph edge")
        if edge.get("relation") == "extracted_from":
            cid, sid = edge.get("from"), edge.get("to")
            if cid not in claim_nodes or sid not in source_nodes or cid in claim_sources:
                raise ValueError("invalid or duplicate extracted_from edge")
            claim_sources[cid] = sid

    candidates = []
    seen = set()
    for cluster in clusters:
        if not isinstance(cluster, dict) or cluster.get("relationship") != "exact_normalized_statement_match":
            raise ValueError("unexpected duplicate cluster relationship")
        cluster_id = cluster.get("cluster_id")
        cids = cluster.get("claim_ids")
        if not isinstance(cluster_id, str) or not cluster_id or cluster_id in seen:
            raise ValueError("invalid or duplicate duplicate-cluster ID")
        seen.add(cluster_id)
        if not isinstance(cids, list) or len(cids) < 2 or len(set(cids)) != len(cids):
            raise ValueError("duplicate cluster must contain unique Claim IDs")
        if cluster.get("independent_corroboration") is not False:
            raise ValueError("duplicate cluster must not assert independent corroboration")
        source_ids = set()
        for cid in cids:
            sid = claim_sources.get("claim:" + cid)
            if sid is None:
                raise ValueError("duplicate cluster references Claim without a source")
            source_ids.add(sid)
        if len(source_ids) != cluster.get("distinct_source_document_count"):
            raise ValueError("duplicate cluster source count inconsistent with graph")
        if len(source_ids) < 2:
            continue
        docs = [source_nodes[sid] for sid in sorted(source_ids)]
        candidates.append({
            "cluster_id": cluster_id,
            "claim_ids": sorted(cids),
            "distinct_source_document_count": len(docs),
            "sources": [{
                "source_id": node["id"], "url": node["url"],
                "publisher": node.get("publisher"),
                "declared_independence": node.get("independence"),
                "origin_key": "", "relationship": "",
                "reviewer": "", "rationale": "", "source_checked": False,
            } for node in docs],
            "review_status": "pending",
            "independently_verified": False,
        })
    candidates.sort(key=lambda c: (-c["distinct_source_document_count"], c["cluster_id"]))
    selected = candidates[:max_clusters]
    return {
        "schema_version": "1.0", "review_type": "source_lineage",
        "generated_at": graph.get("generated_at"),
        "status": "human_review_required",
        "summary": {
            "multi_document_duplicate_clusters": len(candidates),
            "selected_clusters": len(selected),
            "remaining_unselected_clusters": len(candidates) - len(selected),
        },
        "clusters": selected,
        "allowed_relationships": list(RELATIONSHIPS),
        "policy": {
            "read_only": True,
            "origin_labels_are_human_assertions": True,
            "independent_corroboration_automatically_verified": False,
            "note": "Exact wording identifies review candidates; different publishers, URLs or origin keys do not establish independent verification.",
        },
    }


def evaluate(packet):
    if not isinstance(packet, dict) or packet.get("schema_version") != "1.0" or packet.get("review_type") != "source_lineage":
        raise ValueError("source-lineage packet schema mismatch")
    if packet.get("allowed_relationships") != list(RELATIONSHIPS) or packet.get("policy", {}).get("independent_corroboration_automatically_verified") is not False:
        raise ValueError("source-lineage policy mismatch")
    clusters = packet.get("clusters")
    if not isinstance(clusters, list) or len(clusters) > 100:
        raise ValueError("bounded source-lineage clusters required")
    seen = set()
    complete = []
    pending = []
    origin_counts = Counter()
    relationship_counts = Counter()
    same_origin_cluster_count = 0
    distinct_origin_cluster_count = 0
    for cluster in clusters:
        if not isinstance(cluster, dict):
            raise ValueError("malformed lineage cluster")
        cid = cluster.get("cluster_id")
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ValueError("duplicate lineage cluster ID")
        seen.add(cid)
        if cluster.get("independently_verified") is not False:
            raise ValueError("lineage review cannot assert verification")
        docs = cluster.get("sources")
        if not isinstance(docs, list) or len(docs) < 2 or cluster.get("distinct_source_document_count") != len(docs):
            raise ValueError("invalid lineage source count")
        source_ids = set()
        filled = 0
        origins = set()
        for source in docs:
            if not isinstance(source, dict):
                raise ValueError("invalid source review")
            sid = source.get("source_id")
            if not isinstance(sid, str) or not sid or sid in source_ids:
                raise ValueError("duplicate lineage source ID")
            source_ids.add(sid)
            if not isinstance(source.get("url"), str) or not source["url"].startswith("https://"):
                raise ValueError("invalid source URL")
            fields = ("origin_key", "relationship", "reviewer", "rationale")
            if any(not isinstance(source.get(name), str) for name in fields) or type(source.get("source_checked")) is not bool:
                raise ValueError("lineage review fields have invalid types")
            origin = source["origin_key"].strip()
            relation = source["relationship"]
            reviewer = source["reviewer"].strip()
            note = source["rationale"].strip()
            blank = not origin and not relation and not reviewer and not note and not source["source_checked"]
            if blank:
                continue
            if not KEY.fullmatch(origin) or relation not in RELATIONSHIPS or not reviewer or len(note) < 30:
                raise ValueError("completed lineage annotation requires valid origin, relationship, reviewer and >=30-character rationale")
            if not source["source_checked"] and relation != "unknown":
                raise ValueError("uninspected source cannot receive a definitive relationship annotation")
            filled += 1
            origins.add(origin)
            origin_counts[origin] += 1
            relationship_counts[relation] += 1
        if filled == len(docs):
            complete.append({"cluster_id": cid, "distinct_reviewer_assigned_origin_keys": len(origins)})
            same_origin_cluster_count += int(len(origins) == 1)
            distinct_origin_cluster_count += int(len(origins) > 1)
        else:
            pending.append(cid)
    return {
        "schema_version": "1.0", "review_type": "source_lineage",
        "status": "complete" if not pending else "pending",
        "cluster_count": len(clusters),
        "fully_reviewed_clusters": len(complete),
        "pending_cluster_ids": pending,
        "same_reviewer_assigned_origin_clusters": same_origin_cluster_count,
        "different_reviewer_assigned_origin_clusters": distinct_origin_cluster_count,
        "relationship_label_counts": dict(sorted(relationship_counts.items())),
        "completed_clusters": complete,
        "automatically_verified_independent_evidence": 0,
        "interpretation_limits": [
            "Origin keys and relationships are reviewer assertions; they are not independent verification.",
            "Multiple distinct source URLs or different origin keys do not prove independent measurements.",
            "Only exact-normalized-quote duplicate clusters are sampled; semantic paraphrases may be missed.",
            "No record is promoted to a formal benchmark, company or hardware registry.",
        ],
    }


def markdown_report(report):
    return "\n".join([
        "# Cross-source Lineage Review", "",
        f"- Reviewed clusters: {report['fully_reviewed_clusters']}/{report['cluster_count']}",
        f"- Same reviewer-assigned origin clusters: {report['same_reviewer_assigned_origin_clusters']}",
        f"- Different reviewer-assigned origin clusters: {report['different_reviewer_assigned_origin_clusters']}",
        f"- Pending clusters: {len(report['pending_cluster_ids'])}",
        "- Automatically independently verified evidence: 0",
        "", "## Interpretation limits", "",
        *("- " + line for line in report["interpretation_limits"]), "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--max-clusters", type=int, default=25)
    parser.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    try:
        packet = json.loads(args.graph.read_text(encoding="utf-8"))
        report = evaluate(packet) if args.evaluate else prepare(packet, max_clusters=args.max_clusters)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.markdown:
            if not args.evaluate:
                raise ValueError("--markdown requires --evaluate")
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(markdown_report(report) + "\n", encoding="utf-8")
        print("Lineage " + ("evaluated" if args.evaluate else "template created") + ": " +
              str(report.get("cluster_count", report.get("summary", {}).get("selected_clusters", 0))) + " clusters")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
