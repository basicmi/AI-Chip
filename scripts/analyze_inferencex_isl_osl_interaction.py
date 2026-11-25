#!/usr/bin/env python3
"""Describe observed InferenceX ISL x OSL interactions without executing benchmarks."""
import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from assess_benchmark_comparability import (
    canonical, digest, observation_blockers, protocol_signature, system_boundary,
    stable_configuration,
)

METRICS = {
    "output_throughput_per_gpu": ("tok/s/GPU", "throughput", "higher"),
    "median_ttft": ("s", "latency", "lower"),
    "p99_ttft": ("s", "latency", "lower"),
    "median_tpot": ("s", "latency", "lower"),
    "p99_tpot": ("s", "latency", "lower"),
    "p99_itl": ("s", "latency", "lower"),
}


def positive_integer(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value > 0 and value == int(value))


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
        workload = row["workload"]
        if not all(positive_integer(workload.get(k)) for k in ("isl", "osl", "concurrency")):
            excluded["invalid_workload_dimensions"] += 1
            continue
        hardware = row["system"].get("hardware")
        software = row["software"]
        config = stable_configuration(row)
        if not isinstance(hardware, str) or not hardware.strip() or not isinstance(software.get("recipe_fingerprint"), str) or not software["recipe_fingerprint"].strip():
            excluded["missing_hardware_or_recipe_fingerprint"] += 1
            continue
        if not config or any(v is None for v in config.values()):
            excluded["incomplete_execution_configuration"] += 1
            continue
        protocol = protocol_signature(row)
        isl = int(protocol["workload"].pop("isl"))
        osl = int(protocol["workload"].pop("osl"))
        context = {
            "protocol": protocol, "hardware": hardware,
            "system_boundary": system_boundary(row), "software": software,
            "configuration": config, "source_class": row.get("source_class"),
            "evidence_level": row.get("evidence_level"),
        }
        for name, definition in METRICS.items():
            metric = (row.get("normalized_metrics") or {}).get(name)
            if not isinstance(metric, dict):
                continue
            value = metric.get("value")
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or value < 0
                    or (metric.get("unit"), metric.get("family"), metric.get("direction")) != definition):
                excluded["invalid_metric:" + name] += 1
                continue
            key = canonical({"context": context, "metric": name})
            buckets[key][(isl, osl)].append({
                "record_id": row["id"], "value": value,
                "source_url": row.get("detail_url") or row.get("source_url"),
                "publication_date": row.get("publication_date"),
            })

    matrices = []
    for key, cells in sorted(buckets.items()):
        isl_values = sorted({pair[0] for pair in cells})
        osl_values = sorted({pair[1] for pair in cells})
        if len(isl_values) < 2 or len(osl_values) < 2:
            continue
        identity = json.loads(key)
        observed_cells = []
        for (isl, osl), observations in sorted(cells.items()):
            observations.sort(key=lambda item: item["record_id"])
            values = [item["value"] for item in observations]
            observed_cells.append({
                "isl": isl, "osl": osl, "observations": observations,
                "count": len(values), "min": min(values), "max": max(values),
                "median_of_published_values": median(values),
            })
        matrices.append({
            "id": digest(identity)[:20], **identity,
            "unit": METRICS[identity["metric"]][0],
            "isl_values": isl_values, "osl_values": osl_values,
            "expected_grid_cells": len(isl_values) * len(osl_values),
            "observed_grid_cells": len(observed_cells),
            "coverage_fraction": len(observed_cells) / (len(isl_values) * len(osl_values)),
            "cells": observed_cells,
        })
    return {
        "schema_version": "1.0",
        "report_type": "inferencex_observed_isl_osl_interaction_matrices",
        "summary": {
            "inferencex_records_seen": seen, "interaction_matrices": len(matrices),
            "by_metric": dict(sorted(Counter(m["metric"] for m in matrices).items())),
            "exclusion_reason_counts": dict(sorted(excluded.items())),
        },
        "matrices": matrices,
        "limitations": [
            "Only recorded ISL and OSL vary in the matching context; unreported variables may still differ.",
            "Recipe fingerprint equality is required, not proof of identical execution.",
            "Sparse cells remain missing; no interpolation or extrapolation is performed.",
            "Coverage is observed cell count divided by the rectangular grid size, not statistical confidence.",
            "Median of published values is not a pooled request-level percentile.",
            "Different metric matrices may contain different records and must not be joined into synthetic runs.",
            "No causal interaction estimate, KV-cache estimate, saturation threshold, cost inference or benchmark execution.",
            "InferenceX benchmark version may be unreported."
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-results", type=Path, default=Path("data/benchmark-results.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(json.loads(args.benchmark_results.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\\n", encoding="utf-8")
    print("PASS: InferenceX ISL/OSL interaction matrices", json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
