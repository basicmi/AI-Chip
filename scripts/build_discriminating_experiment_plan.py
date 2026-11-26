#!/usr/bin/env python3
"""Plan a compact set of measurements that separates competing hypotheses."""
import argparse
import json
from itertools import combinations
from pathlib import Path

from review_performance_experiment_evidence import require, digest

LOW = ("counter", "telemetry", "bytes", "utilization", "occupancy", "queue", "timestamp", "trace")
HIGH = ("intervention", "change ", "treatment", "tune ", "vary ")


def estimate_cost(text):
    value = text.casefold()
    if any(term in value for term in HIGH):
        return {"band": "high", "relative_units": 3,
                "basis": "Likely requires a controlled intervention or configuration change."}
    if any(term in value for term in LOW):
        return {"band": "low", "relative_units": 1,
                "basis": "Likely obtainable from existing telemetry or traces; availability is not guaranteed."}
    return {"band": "medium", "relative_units": 2,
            "basis": "Likely requires targeted profiling, instrumentation or data alignment."}


def build_plan(comparison, catalog, limit=12):
    require(isinstance(comparison, dict)
            and comparison.get("report_type") == "performance_hypothesis_comparison",
            "Invalid hypothesis comparison report")
    require(comparison.get("overall_verdict") == "undetermined"
            and comparison.get("ranking") == "none",
            "Planner requires an unranked, undetermined comparison")
    require(isinstance(catalog, dict) and catalog.get("schema_version") == "1.0"
            and isinstance(catalog.get("hypotheses"), list), "Invalid hypothesis catalog")
    require(type(limit) is int and 1 <= limit <= 50, "Limit must be between 1 and 50")
    catalog_by_id = {h.get("hypothesis_id"): h for h in catalog["hypotheses"] if isinstance(h, dict)}
    comparison_by_id = {h.get("hypothesis_id"): h for h in comparison.get("hypotheses", []) if isinstance(h, dict)}
    require(len(catalog_by_id) == len(catalog["hypotheses"]), "Hypothesis catalog IDs must be unique")
    active = [h for h in comparison.get("hypotheses", [])
              if h.get("hypothesis_id") in catalog_by_id]
    require(len(active) >= 2, "At least two catalogued hypotheses are required")
    pairs = list(combinations(active, 2))
    pair_ids = [tuple(sorted((a["hypothesis_id"], b["hypothesis_id"]))) for a, b in pairs]

    ownership = {}
    descriptions = {}
    for hypothesis in active:
        hid = hypothesis["hypothesis_id"]
        source = catalog_by_id[hid]
        for item in source.get("discriminating_measurements", []):
            require(isinstance(item, str) and item.strip(), "Measurement descriptions must be non-empty strings")
            key = " ".join(item.casefold().split())
            ownership.setdefault(key, set()).add(hid)
            descriptions.setdefault(key, item)

    discriminators = {}
    for key, owners in ownership.items():
        covered = set()
        for pair in pair_ids:
            left, right = pair
            if (left in owners) != (right in owners):
                covered.add(pair)
        if covered:
            discriminators[key] = covered

    # Greedy weighted set cover: deterministic and explainable, not an information-gain model.
    uncovered = set(pair_ids)
    selected = []
    while uncovered and len(selected) < limit:
        options = []
        for key, covered in discriminators.items():
            if key in selected:
                continue
            newly = covered & uncovered
            if newly:
                cost = estimate_cost(descriptions[key])["relative_units"]
                options.append((cost / len(newly), cost, key, newly))
        if not options:
            break
        _, cost, key, newly = min(options, key=lambda x: (x[0], x[1], x[2]))
        selected.append(key)
        uncovered -= newly

    measurements = []
    for index, key in enumerate(selected, 1):
        cost = estimate_cost(descriptions[key])
        separates = [list(pair) for pair in sorted(discriminators[key])]
        measurements.append({
            "measurement_id": f"DM-{index:02d}",
            "description": descriptions[key],
            "relative_cost": cost,
            "distinguishes_hypothesis_pairs": separates,
            "required_controls": [
                "Align device/process/entity scope and sampling window to the serving symptom.",
                "Record units, aggregation, clock domain, provenance and collection overhead.",
                "Keep workload, model, software recipe and offered load fixed unless explicitly part of the comparison."
            ],
            "interpretation": "A measurement can distinguish hypotheses only when its result has predeclared, mechanism-specific meaning; mere presence or correlation is not causal proof."
        })

    pair_plans = []
    selected_keys = set(selected)
    for (a, b), pair in zip(pairs, pair_ids):
        common = set(x.casefold() for x in catalog_by_id[a["hypothesis_id"]].get("discriminating_measurements", [])) & set(
            x.casefold() for x in catalog_by_id[b["hypothesis_id"]].get("discriminating_measurements", []))
        pair_measurements = [m["measurement_id"] for m, key in zip(measurements, selected)
                             if key in discriminators and pair in discriminators[key]]
        pair_plans.append({
            "hypothesis_pair": list(pair),
            "titles": [a.get("title"), b.get("title")],
            "selected_discriminating_measurements": pair_measurements,
            "shared_measurement_descriptions": sorted(common),
            "status": "covered_by_selected_measurements" if pair_measurements else "not_separated_by_selected_measurements",
            "contrast": {
                a["hypothesis_id"]: {
                    "what_would_support": catalog_by_id[a["hypothesis_id"]].get("what_would_support", []),
                    "what_would_weaken": catalog_by_id[a["hypothesis_id"]].get("what_would_weaken", [])
                },
                b["hypothesis_id"]: {
                    "what_would_support": catalog_by_id[b["hypothesis_id"]].get("what_would_support", []),
                    "what_would_weaken": catalog_by_id[b["hypothesis_id"]].get("what_would_weaken", [])
                }
            },
            "outcome_rule": "Predeclare the expected direction and measurement boundary for both hypotheses before collection; inconclusive or mixed results preserve both hypotheses."
        })

    return {
        "schema_version": "1.0",
        "report_type": "discriminating_experiment_plan",
        "record_id": comparison.get("record_id"),
        "comparison_sha256": digest(comparison),
        "hypothesis_catalog_sha256": digest(catalog),
        "hypothesis_count": len(active),
        "hypothesis_pair_count": len(pair_ids),
        "measurement_count": len(measurements),
        "measurements": measurements,
        "pairwise_discrimination": pair_plans,
        "uncovered_pairs": [list(pair) for pair in sorted(uncovered)],
        "coverage_complete": not uncovered,
        "selection_method": "Deterministic greedy weighted set cover over explicitly declared hypothesis measurement lists; relative cost bands are heuristic.",
        "relative_cost_total": sum(m["relative_cost"]["relative_units"] for m in measurements),
        "execution": {"performed": False, "automatic_execution": False, "status": "proposal_only"},
        "decision": {"hypothesis_verdict": "undetermined", "automatic_hypothesis_selection": False,
                     "causal_attribution": False, "configuration_recommendations": False},
        "guardrails": [
            "A selected measurement is not a result; no experiment or telemetry collection was performed.",
            "Only explicitly declared measurement differences count as discriminators; absence from a list is not proof of physical irrelevance.",
            "Cost bands are qualitative planning heuristics, not measured engineering hours or risk estimates.",
            "If a pair remains uncovered, request expert-designed measurements rather than inventing a discriminator.",
            "Keep failed, missing and inconclusive measurements visible; do not convert missing evidence into a negative result."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--hypotheses", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(args.output.resolve() not in {args.comparison.resolve(), args.hypotheses.resolve()},
            "Output must not overwrite an input")
    comparison = json.loads(args.comparison.read_text(encoding="utf-8"))
    catalog = json.loads(args.hypotheses.read_text(encoding="utf-8"))
    report = build_plan(comparison, catalog, args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
