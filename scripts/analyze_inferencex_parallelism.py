#!/usr/bin/env python3
"""Observed InferenceX parallelism sensitivity, with separate review candidates."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from assess_benchmark_comparability import (
    canonical, digest, observation_blockers, protocol_signature,
    stable_configuration, system_boundary,
)
from analyze_inferencex_prefill_decode_scaling import (
    PHASE_METRICS, positive_integer, valid_metric,
)
from analyze_inferencex_concurrency import present

AXES = ("prefill_tp", "prefill_ep", "decode_tp", "decode_ep")


def build_report(database):
    buckets = defaultdict(lambda: defaultdict(list))
    excluded = Counter()
    seen = 0
    for row in database["records"]:
        if row.get("source_id") != "inferencex":
            continue
        seen += 1
        blockers = observation_blockers(row)
        if blockers:
            excluded.update(blockers)
            continue
        w, s, sw = row["workload"], row["system"], row["software"]
        if not all(positive_integer(w.get(k)) for k in ("isl", "osl", "concurrency")):
            excluded["invalid_workload_dimensions"] += 1
            continue
        if not present(s.get("hardware")):
            excluded["missing_hardware"] += 1
            continue
        config = stable_configuration(row)
        for axis in AXES:
            phase = axis.split("_")[0]
            if not positive_integer(config.get(axis)) or not positive_integer(s.get("physical_" + phase + "_gpus")):
                excluded["missing_or_invalid_axis:" + axis] += 1
                continue
            rest = {k: v for k, v in config.items() if k != axis}
            if not rest or any(v is None for v in rest.values()):
                excluded["incomplete_other_configuration:" + axis] += 1
                continue
            # Recipe fingerprints may encode the changed axis itself.
            # Keep them as evidence, never silently treat differences as equality.
            fingerprint = sw.get("recipe_fingerprint")
            context = {
                "protocol": protocol_signature(row),
                "hardware": s["hardware"],
                "system_boundary": system_boundary(row),
                "software_without_recipe_fingerprint": {k: v for k, v in sw.items() if k != "recipe_fingerprint"},
                "other_configuration": rest,
                "source_class": row.get("source_class"),
                "evidence_level": row.get("evidence_level"),
            }
            for name, definition in PHASE_METRICS[phase].items():
                value = valid_metric(row, name, definition)
                if value is None:
                    continue
                key = (axis, canonical(context), name)
                buckets[key][int(config[axis])].append({
                    "record_id": row["id"], "value": value,
                    "recipe_fingerprint": fingerprint if present(fingerprint) else None,
                    "source_url": row.get("detail_url") or row.get("source_url"),
                    "publication_date": row.get("publication_date"),
                })
    strict, candidates = [], []
    for (axis, key, name), levels in sorted(buckets.items()):
        if len(levels) < 2:
            continue
        context = json.loads(key)
        # Build strict subgroups separately, so incomplete records cannot
        # downgrade or contaminate an otherwise matching recipe cohort.
        recipes = defaultdict(lambda: defaultdict(list))
        for level, observations in levels.items():
            for item in observations:
                if item["recipe_fingerprint"] is not None:
                    recipes[item["recipe_fingerprint"]][level].append(item)
        phase = axis.split("_")[0]
        unit = PHASE_METRICS[phase][name][0]
        identity = {"axis": axis, "context": context, "metric": name}
        for recipe, points in sorted(recipes.items()):
            if len(points) < 2:
                continue
            summaries = []
            for level, observations in sorted(points.items()):
                observations.sort(key=lambda item: item["record_id"])
                values = [item["value"] for item in observations]
                summaries.append({
                    "parallelism_degree": level, "count": len(values),
                    "min": min(values), "max": max(values),
                    "median_of_published_values": median(values),
                    "observations": observations,
                })
            strict.append({
                "id": digest({**identity, "recipe": recipe})[:20],
                **identity, "recipe_fingerprint": recipe, "unit": unit,
                "points": summaries,
            })
        fingerprints = {item["recipe_fingerprint"] for obs in levels.values() for item in obs}
        if len(fingerprints) > 1 or None in fingerprints:
            candidates.append({
                "id": digest(identity)[:20], **identity, "unit": unit,
                "review_reasons": [
                    reason for condition, reason in (
                        (None in fingerprints, "recipe_fingerprint_missing"),
                        (len(fingerprints - {None}) > 1, "recipe_fingerprints_differ"),
                    ) if condition
                ],
                "levels": [
                    {"parallelism_degree": level, "observations": sorted(obs, key=lambda item: item["record_id"])}
                    for level, obs in sorted(levels.items())
                ],
            })
    return {
        "schema_version": "1.0",
        "report_type": "inferencex_parallelism_sensitivity",
        "summary": {
            "inferencex_records_seen": seen,
            "strict_series": len(strict),
            "review_candidate_groups": len(candidates),
            "strict_by_axis": dict(sorted(Counter(s["axis"] for s in strict).items())),
            "candidates_by_axis": dict(sorted(Counter(s["axis"] for s in candidates).items())),
            "exclusion_reason_counts": dict(sorted(excluded.items())),
        },
        "strict_series": strict,
        "review_candidates": candidates,
        "limitations": [
            "Only one recorded TP or EP degree varies; GPU counts and recorded workload/system boundary remain fixed.",
            "Strict groups require an identical nonempty recipe fingerprint and matching other recorded configuration.",
            "Candidates with different or missing fingerprints retain raw observations only; no aggregated comparisons or rankings.",
            "Candidate groups can overlap strict groups and counts are metric-level, not unique experiments.",
            "The fingerprint may encode the changed parallelism axis; strict groups may therefore be empty.",
            "Unknown unrecorded configuration can confound even strict groups. TTFT and TPOT are end-to-end observations, not isolated kernel times.",
            "No causal attribution, interpolation, extrapolation or benchmark execution."
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-results", type=Path, default=Path("data/benchmark-results.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(json.loads(args.benchmark_results.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("PASS: InferenceX parallelism sensitivity", json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
