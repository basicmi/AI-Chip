#!/usr/bin/env python3
"""Describe published InferenceX ISL/OSL sensitivity; never execute benchmarks."""
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

METRICS_BY_DIMENSION = {
    "isl": {
        "output_throughput_per_gpu": ("tok/s/GPU", "throughput", "higher"),
        "median_ttft": ("s", "latency", "lower"),
        "p99_ttft": ("s", "latency", "lower"),
    },
    "osl": {
        "output_throughput_per_gpu": ("tok/s/GPU", "throughput", "higher"),
        "median_tpot": ("s", "latency", "lower"),
        "p99_tpot": ("s", "latency", "lower"),
        "p99_itl": ("s", "latency", "lower"),
    },
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
        for dimension, metric_definitions in METRICS_BY_DIMENSION.items():
            protocol = protocol_signature(row)
            varying_value = int(protocol["workload"].pop(dimension))
            context = {
                "protocol": protocol, "hardware": hardware,
                "system_boundary": system_boundary(row), "software": software,
                "configuration": config, "source_class": row.get("source_class"),
                "evidence_level": row.get("evidence_level"),
            }
            for metric_name, definition in metric_definitions.items():
                metric = (row.get("normalized_metrics") or {}).get(metric_name)
                if not isinstance(metric, dict):
                    continue
                value = metric.get("value")
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or value < 0
                        or (metric.get("unit"), metric.get("family"), metric.get("direction")) != definition):
                    excluded["invalid_metric:" + metric_name] += 1
                    continue
                key = canonical({"dimension": dimension, "context": context, "metric": metric_name})
                buckets[key][varying_value].append({
                    "record_id": row["id"], "value": value,
                    "source_url": row.get("detail_url") or row.get("source_url"),
                    "publication_date": row.get("publication_date"),
                })
    sweeps = []
    for key, levels in sorted(buckets.items()):
        if len(levels) < 2:
            continue
        identity = json.loads(key)
        points = []
        for sequence_length, observations in sorted(levels.items()):
            observations.sort(key=lambda item: item["record_id"])
            values = [item["value"] for item in observations]
            points.append({
                "sequence_length": sequence_length, "observations": observations,
                "count": len(values), "min": min(values), "max": max(values),
                "median_of_published_values": median(values),
            })
        first, last = points[0], points[-1]
        baseline = first["median_of_published_values"]
        final = last["median_of_published_values"]
        relative_change = ((final - baseline) / abs(baseline) * 100) if baseline != 0 else None
        sweeps.append({
            "id": digest(identity)[:20], **identity,
            "unit": METRICS_BY_DIMENSION[identity["dimension"]][identity["metric"]][0],
            "points": points,
            "endpoint_change": {
                "baseline_sequence_length": first["sequence_length"],
                "final_sequence_length": last["sequence_length"],
                "baseline_median": baseline, "final_median": final,
                "relative_change_percent": relative_change,
            },
        })
    return {
        "schema_version": "1.0", "report_type": "inferencex_sequence_length_sensitivity",
        "summary": {
            "inferencex_records_seen": seen, "sensitivity_series": len(sweeps),
            "by_dimension": dict(sorted(Counter(s["dimension"] for s in sweeps).items())),
            "by_metric": dict(sorted(Counter(s["metric"] for s in sweeps).items())),
            "exclusion_reason_counts": dict(sorted(excluded.items())),
        },
        "sweeps": sweeps,
        "limitations": [
            "Only ISL or OSL varies in the recorded matching context; unreported variables may still differ.",
            "Recipe fingerprint equality is required, not proof of identical execution.",
            "Endpoint change is descriptive and is not a causal estimate or a fitted sensitivity coefficient.",
            "Median of published values is not a pooled request-level percentile.",
            "Different metric series may contain different records and must not be joined into synthetic runs.",
            "No interpolation, extrapolation, KV-cache estimate, saturation threshold, cost inference or benchmark execution.",
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
    print("PASS: InferenceX sequence-length sensitivity", json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
