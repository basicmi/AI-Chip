#!/usr/bin/env python3
"""Build a deterministic, stratified human-review packet for retrieval candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

RELEVANT = {"direct_ai_compute", "adjacent_ai_systems"}


def build_review_packet(experiment, *, sample_per_group=12):
    if type(sample_per_group) is not int or not 1 <= sample_per_group <= 50:
        raise ValueError("sample_per_group must be 1..50")
    experiment_id = experiment.get("experiment_id")
    if not isinstance(experiment_id, str) or not experiment_id:
        raise ValueError("Experiment report requires experiment_id")
    groups = experiment.get("groups", [])
    if not isinstance(groups, list):
        raise ValueError("Experiment groups must be a list")

    candidates_by_id = {}
    group_reports = []
    for group in groups:
        group_id = group.get("id")
        if not isinstance(group_id, str) or not group_id:
            raise ValueError("Every query group requires an id")
        rows = group.get("candidate_results", [])
        if not isinstance(rows, list):
            raise ValueError("candidate_results must be a list for " + group_id)
        unique = {}
        for candidate in rows:
            pid = candidate.get("paper_id")
            if not isinstance(pid, str) or not pid:
                raise ValueError("Candidate requires canonical paper_id")
            unique.setdefault(pid, candidate)
            stored = candidates_by_id.setdefault(pid, {
                "paper_id": pid,
                "candidate_id": candidate.get("candidate_id"),
                "title": candidate.get("title", ""),
                "url": candidate.get("url", ""),
                "published_at": candidate.get("published_at"),
                "excerpt": candidate.get("excerpt", ""),
                "categories": candidate.get("categories", []),
                "authors": candidate.get("authors", []),
                "predicted_relevance": candidate.get("predicted_relevance", "out_of_scope"),
                "screening_signals": candidate.get("screening_signals", []),
                "observed_position_by_group": {},
                "sampled_for_groups": [],
                "returned_by_groups": [],
                "adjudication": {
                    "label": "",
                    "reviewer": "",
                    "reviewed_at": "",
                    "rationale": "",
                },
            })
            stored["returned_by_groups"].append(group_id)
            stored["observed_position_by_group"][group_id] = candidate.get("observed_position")

        sample_ids = []
        if group.get("status") == "observed" and unique:
            ordered = sorted(unique.values(), key=lambda row: row["paper_id"])
            seed_text = experiment_id + ":" + group_id
            seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
            selected = random.Random(seed).sample(ordered, min(sample_per_group, len(ordered)))
            sample_ids = [row["paper_id"] for row in selected]
            for pid in sample_ids:
                candidates_by_id[pid]["sampled_for_groups"].append(group_id)

        group_reports.append({
            "group_id": group_id,
            "group_name": group.get("name", group_id),
            "status": group.get("status", "unknown"),
            "population_count": len(unique),
            "sample_count": len(sample_ids),
            "sampled_paper_ids": sample_ids,
            "sampling_method": "simple_random_without_replacement",
        })

    candidates = sorted(candidates_by_id.values(), key=lambda row: row["paper_id"])
    for row in candidates:
        row["returned_by_groups"] = sorted(set(row["returned_by_groups"]))
        row["sampled_for_groups"] = sorted(set(row["sampled_for_groups"]))
    sampled = [row for row in candidates if row["sampled_for_groups"]]
    status = "ready" if sampled else ("skipped" if experiment.get("status") == "skipped" else "empty")
    return {
        "schema_version": "1.0",
        "experiment_id": experiment_id,
        "discovery_generated_at": experiment.get("discovery_generated_at"),
        "experiment_status": experiment.get("status", "unknown"),
        "status": status,
        "sampling": {
            "method": "simple_random_without_replacement_per_query_group",
            "sample_per_group": sample_per_group,
            "seed_rule": "first 8 bytes of SHA-256(experiment_id + ':' + group_id)",
            "deduplicate_review_rows": True,
        },
        "label_guide": {
            "direct_ai_compute": "Direct AI chip, accelerator, hardware, memory/interconnect, compiler/kernel, training, inference/serving or concrete AI system/runtime contribution.",
            "adjacent_ai_systems": "Agent, robotics, world-model or physical-AI workload relevance without a direct hardware/system contribution.",
            "out_of_scope": "No material AI chip/system contribution.",
            "uncertain": "Insufficient abstract evidence to make a defensible relevance judgement.",
            "relevant_for_precision": sorted(RELEVANT),
            "review_rule": "Read the title and abstract excerpt; do not copy predicted_relevance as the adjudicated label without independent judgement.",
        },
        "groups": group_reports,
        "candidates": sampled,
        "interpretation_limits": [
            "The sample is random within each observed query group's returned, date-filtered candidate set; it does not sample papers the query failed to retrieve.",
            "The sample is for one bounded run and does not establish corpus-wide precision or recall.",
            "A paper selected in multiple groups is reviewed once and contributes to each group in which it was sampled.",
            "Rule-based predicted_relevance is a triage hint, not ground truth.",
            "Groups with failed queries or no candidates have no precision result.",
        ],
    }


def markdown_report(packet):
    lines = [
        "# AI Chip — targeted retrieval human-review packet",
        "",
        f"- Experiment: `{packet.get('experiment_id')}`",
        f"- Experiment status: **{packet.get('experiment_status')}**",
        f"- Review packet status: **{packet.get('status')}**",
        f"- Unique papers to review: **{len(packet.get('candidates', []))}**",
        "",
        "| Query group | Returned population | Random sample | Status |",
        "|---|---:|---:|---|",
    ]
    for group in packet.get("groups", []):
        lines.append(
            f"| {group['group_name']} | {group['population_count']} | "
            f"{group['sample_count']} | {group['status']} |"
        )
    lines.extend([
        "",
        "## Review instructions",
        "",
        "Edit the `adjudication` fields in the JSON artifact. Use one of "
        "`direct_ai_compute`, `adjacent_ai_systems`, `out_of_scope`, or "
        "`uncertain`; add a reviewer identifier. Do not treat the heuristic "
        "prediction as a gold label.",
        "",
        "The sample is simple random without replacement within each successful "
        "query group. A paper sampled in multiple groups appears once and is "
        "counted for each sampled group.",
        "",
    ])
    lines.extend("- " + note for note in packet.get("interpretation_limits", []))
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--sample-per-group", type=int, default=12)
    args = parser.parse_args()
    try:
        experiment = json.loads(args.input.read_text(encoding="utf-8"))
        packet = build_review_packet(experiment, sample_per_group=args.sample_per_group)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        summary = markdown_report(packet)
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(summary, encoding="utf-8")
        print(summary)
        return 0
    except (OSError, ValueError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
