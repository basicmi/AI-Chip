#!/usr/bin/env python3
"""Evaluate human-adjudicated relevance labels for a sampled retrieval run."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

LABELS = {"direct_ai_compute", "adjacent_ai_systems", "out_of_scope"}
RELEVANT = {"direct_ai_compute", "adjacent_ai_systems"}


def wilson_interval(successes, total, z=1.959963984540054):
    if total <= 0:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def evaluate(packet):
    if packet.get("schema_version") != "1.0":
        raise ValueError("Unsupported review packet schema_version")
    rows = packet.get("candidates")
    groups = packet.get("groups")
    if not isinstance(rows, list) or not isinstance(groups, list):
        raise ValueError("Review packet requires candidates and groups lists")
    by_id = {}
    for row in rows:
        pid = row.get("paper_id")
        if not isinstance(pid, str) or not pid or pid in by_id:
            raise ValueError("Missing or duplicate review paper_id")
        by_id[pid] = row

    results = []
    for group in groups:
        group_id = group["group_id"]
        sample_ids = group.get("sampled_paper_ids", [])
        if len(sample_ids) != group.get("sample_count"):
            raise ValueError("Sample count mismatch for " + group_id)
        judged, relevant, uncertain, pending = 0, 0, 0, 0
        for pid in sample_ids:
            if pid not in by_id:
                raise ValueError("Sample references missing candidate: " + pid)
            row = by_id[pid]
            if group_id not in row.get("sampled_for_groups", []):
                raise ValueError("Candidate/group sample membership mismatch: " + pid)
            adjudication = row.get("adjudication") or {}
            label = adjudication.get("label", "")
            reviewer = adjudication.get("reviewer", "")
            if label == "uncertain":
                if reviewer:
                    uncertain += 1
                else:
                    pending += 1
            elif label in LABELS:
                if reviewer:
                    judged += 1
                    relevant += int(label in RELEVANT)
                else:
                    pending += 1
            elif label in ("", None):
                pending += 1
            else:
                raise ValueError("Invalid adjudication label for " + pid + ": " + str(label))

        sample_count = len(sample_ids)
        resolved = judged == sample_count and sample_count > 0
        census = sample_count == group.get("population_count") and sample_count > 0
        precision = relevant / judged if resolved else None
        interval = wilson_interval(relevant, judged) if resolved and not census else None
        partial_precision = relevant / judged if judged else None
        results.append({
            "group_id": group_id,
            "group_name": group.get("group_name", group_id),
            "population_count": group.get("population_count", 0),
            "sample_count": sample_count,
            "reviewed_count": judged,
            "uncertain_count": uncertain,
            "pending_count": pending,
            "precision": round(precision, 4) if precision is not None else None,
            "wilson_95_interval": [round(x, 4) for x in interval] if interval else None,
            "exact_for_returned_set": bool(resolved and census),
            "reviewed_subset_precision_descriptive_only": round(partial_precision, 4) if judged and not resolved else None,
            "status": "complete" if resolved else ("pending" if pending else "needs_adjudication"),
        })

    scorable_groups = [row for row in results if row["precision"] is not None]
    return {
        "schema_version": "1.0",
        "experiment_id": packet.get("experiment_id"),
        "status": "complete" if results and len(scorable_groups) == len(results) else "pending",
        "scorable_group_count": len(scorable_groups),
        "group_count": len(results),
        "groups": results,
        "interpretation_limits": [
            "Precision is estimated separately for each query group from a simple-random sample of its returned candidates.",
            "Wilson intervals describe sampling uncertainty for a single bounded run; they do not include query, date-window or publication-indexing uncertainty.",
            "If the full returned set was sampled and every row adjudicated, precision is exact only for that returned set.",
            "Partially reviewed subsets are descriptive only and are not reported as precision estimates.",
            "Uncertain or missing labels are never silently counted as out of scope.",
            "Results do not measure relevance among papers that the query failed to retrieve.",
        ],
    }


def markdown_report(report):
    lines = [
        "# AI Chip — human-adjudicated retrieval precision",
        "",
        f"- Experiment: `{report.get('experiment_id')}`",
        f"- Evaluation status: **{report.get('status')}**",
        "",
        "| Query group | Population | Sample | Reviewed | Pending | Precision | 95% Wilson interval |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in report.get("groups", []):
        precision = f"{row['precision']:.1%}" if row["precision"] is not None else "not scorable"
        if row["exact_for_returned_set"]:
            interval = "exact for returned set"
        elif row["wilson_95_interval"]:
            low, high = row["wilson_95_interval"]
            interval = f"{low:.1%}–{high:.1%}"
        else:
            interval = "—"
        lines.append(
            f"| {row['group_name']} | {row['population_count']} | {row['sample_count']} | "
            f"{row['reviewed_count']} | {row['pending_count']} | {precision} | {interval} |"
        )
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend("- " + note for note in report.get("interpretation_limits", []))
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    try:
        packet = json.loads(args.input.read_text(encoding="utf-8"))
        report = evaluate(packet)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        summary = markdown_report(report)
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(summary, encoding="utf-8")
        print(summary)
        return 0
    except (OSError, ValueError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
