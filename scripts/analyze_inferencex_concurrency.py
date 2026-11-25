#!/usr/bin/env python3
"""Describe published InferenceX concurrency sweeps without running experiments."""
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
    "median_interactivity": ("tok/s/user", "interactivity", "higher"),
    "median_ttft": ("s", "latency", "lower"),
    "p99_ttft": ("s", "latency", "lower"),
    "median_tpot": ("s", "latency", "lower"),
    "p99_tpot": ("s", "latency", "lower"),
    "p99_itl": ("s", "latency", "lower"),
}


def present(value):
    return isinstance(value, str) and value.strip().lower() not in {
        "", "unknown", "not reported", "n/a", "none"
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
            excluded["invalid_workload_lengths_or_concurrency"] += 1
            continue
        hardware = row["system"].get("hardware")
        software = row["software"]
        config = stable_configuration(row)
        # A recipe fingerprint is required to avoid mixing unrelated execution recipes.
        if not present(hardware) or not present(software.get("recipe_fingerprint")):
            excluded["missing_hardware_or_recipe_fingerprint"] += 1
            continue
        if not config or any(v is None for v in config.values()):
            excluded["incomplete_execution_configuration"] += 1
            continue
        protocol = protocol_signature(row)
        concurrency = int(protocol["workload"].pop("concurrency"))
        context = {
            "protocol": protocol,
            "hardware": hardware,
            "system_boundary": system_boundary(row),
            "software": software,
            "configuration": config,
            "source_class": row.get("source_class"),
            "evidence_level": row.get("evidence_level"),
        }
        for name, (unit, family, direction) in METRICS.items():
            metric = (row.get("normalized_metrics") or {}).get(name)
            if not isinstance(metric, dict):
                continue
            v = metric.get("value")
            if (isinstance(v, bool) or not isinstance(v, (int, float))
                    or not math.isfinite(v) or v < 0
                    or (metric.get("unit"), metric.get("family"), metric.get("direction"))
                    != (unit, family, direction)):
                excluded["invalid_metric:" + name] += 1
                continue
            key = canonical({"context": context, "metric": name})
            buckets[key][concurrency].append({
                "record_id": row["id"], "value": v,
                "source_url": row.get("detail_url") or row.get("source_url"),
                "publication_date": row.get("publication_date"),
            })
    sweeps = []
    for key, levels in sorted(buckets.items()):
        if len(levels) < 2:
            continue
        identity = json.loads(key)
        points = []
        for concurrency, observations in sorted(levels.items()):
            observations.sort(key=lambda item: item["record_id"])
            values = [item["value"] for item in observations]
            points.append({
                "concurrency": concurrency, "observations": observations,
                "count": len(values), "min": min(values), "max": max(values),
                "median_of_published_values": median(values),
            })
        sweeps.append({
            "id": digest(identity)[:20], **identity,
            "unit": METRICS[identity["metric"]][0],
            "points": points,
        })
    return {
        "schema_version": "1.0",
        "report_type": "inferencex_observed_concurrency_sweeps",
        "summary": {
            "inferencex_records_seen": seen, "metric_sweeps": len(sweeps),
            "by_metric": dict(sorted(Counter(s["metric"] for s in sweeps).items())),
            "exclusion_reason_counts": dict(sorted(excluded.items())),
        },
        "sweeps": sweeps,
        "limitations": [
            "Only concurrency varies in recorded matching context; unreported variables may differ.",
            "Recipe fingerprint equality is required, not proof of identical execution.",
            "Median of published values is not a pooled request-level percentile.",
            "Different metric series may contain different records; do not join their medians into synthetic runs.",
            "No interpolation, saturation threshold, causal attribution, cost estimate or new benchmark experiment.",
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
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("PASS: InferenceX concurrency sweeps", json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
