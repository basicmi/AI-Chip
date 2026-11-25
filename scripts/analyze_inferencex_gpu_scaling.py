#!/usr/bin/env python3
"""Describe published decode-only InferenceX GPU scaling; never execute benchmarks."""
import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from assess_benchmark_comparability import (
    canonical, digest, observation_blockers, protocol_signature,
    stable_configuration,
)


def positive_integer(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value > 0 and value == int(value))


def nonnegative_integer(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value >= 0 and value == int(value))


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
        system = row["system"]
        prefill = system.get("physical_prefill_gpus")
        decode = system.get("physical_decode_gpus")
        if not nonnegative_integer(prefill) or not positive_integer(decode):
            excluded["invalid_gpu_role_counts"] += 1
            continue
        # Initial version intentionally restricts to decode-only systems:
        # the per-GPU throughput denominator is then unambiguous.
        if prefill != 0:
            excluded["prefill_decode_disaggregated_or_mixed_system"] += 1
            continue
        hardware = system.get("hardware")
        software = row["software"]
        config = stable_configuration(row)
        fingerprint = software.get("recipe_fingerprint")
        if not isinstance(hardware, str) or not hardware.strip() or not isinstance(fingerprint, str) or not fingerprint.strip():
            excluded["missing_hardware_or_recipe_fingerprint"] += 1
            continue
        if not config or any(value is None for value in config.values()):
            excluded["incomplete_execution_configuration"] += 1
            continue
        metric = (row.get("normalized_metrics") or {}).get("output_throughput_per_gpu")
        if not isinstance(metric, dict):
            excluded["missing_output_throughput_per_gpu"] += 1
            continue
        value = metric.get("value")
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0
                or (metric.get("unit"), metric.get("family"), metric.get("direction"))
                != ("tok/s/GPU", "throughput", "higher")):
            excluded["invalid_output_throughput_per_gpu"] += 1
            continue
        protocol = protocol_signature(row)
        context = {
            "protocol": protocol,
            "hardware": hardware,
            "system_type": row.get("system_type"),
            "is_multinode": system.get("is_multinode"),
            "worker_roles": sorted({
                worker.get("role") for worker in (system.get("workers") or [])
                if isinstance(worker, dict) and isinstance(worker.get("role"), str)
            }),
            "software": software,
            "configuration": config,
            "source_class": row.get("source_class"),
            "evidence_level": row.get("evidence_level"),
        }
        key = canonical(context)
        buckets[key][int(decode)].append({
            "record_id": row["id"], "output_throughput_per_gpu": value,
            "source_url": row.get("detail_url") or row.get("source_url"),
            "publication_date": row.get("publication_date"),
        })

    series = []
    for key, levels in sorted(buckets.items()):
        if len(levels) < 2:
            continue
        context = json.loads(key)
        baseline_gpus = min(levels)
        baseline_values = [item["output_throughput_per_gpu"] for item in levels[baseline_gpus]]
        baseline_per_gpu = median(baseline_values)
        baseline_aggregate = baseline_per_gpu * baseline_gpus
        points = []
        for gpu_count, observations in sorted(levels.items()):
            observations.sort(key=lambda item: item["record_id"])
            values = [item["output_throughput_per_gpu"] for item in observations]
            per_gpu = median(values)
            aggregate = per_gpu * gpu_count
            efficiency = aggregate / (baseline_aggregate * gpu_count / baseline_gpus) * 100
            points.append({
                "decode_gpu_count": gpu_count,
                "observations": observations,
                "count": len(values),
                "throughput_per_gpu": {
                    "min": min(values), "median_of_published_values": per_gpu, "max": max(values),
                    "unit": "tok/s/GPU",
                },
                "estimated_aggregate_throughput": {
                    "value": aggregate, "unit": "tok/s",
                    "formula": "median published tok/s/GPU × decode GPU count",
                    "not_directly_measured": True,
                },
                "relative_scaling_efficiency_percent": efficiency,
            })
        series.append({
            "id": digest(context)[:20],
            "context": context,
            "baseline_decode_gpu_count": baseline_gpus,
            "points": points,
        })
    return {
        "schema_version": "1.0",
        "report_type": "inferencex_observed_decode_gpu_scaling_efficiency",
        "summary": {
            "inferencex_records_seen": seen,
            "scaling_series": len(series),
            "scaling_points": sum(len(item["points"]) for item in series),
            "exclusion_reason_counts": dict(sorted(excluded.items())),
        },
        "series": series,
        "method": {
            "scope": "Decode-only systems with physical_prefill_gpus=0.",
            "baseline": "Lowest observed decode GPU count within each exact matching context.",
            "formula": "100 × (median throughput/GPU at N × N) / (baseline median throughput/GPU × baseline N × N / baseline N).",
            "interpretation": "Relative scaling efficiency compares estimated aggregate throughput growth with ideal linear growth from the smallest observed GPU count.",
        },
        "limitations": [
            "Only published observations are analyzed; no benchmark is executed.",
            "Aggregate throughput is estimated from published per-GPU throughput multiplied by decode GPU count; it is not a directly reported system total.",
            "Efficiency is relative to the smallest observed point, not an absolute hardware efficiency or utilization measure.",
            "Exact workload, hardware, system type, single/multinode flag, worker roles, software recipe and stable configuration must match.",
            "TP/EP and other stable configuration fields are held fixed; this does not analyze tensor-parallel scaling when TP changes with GPU count.",
            "Single-node and multinode series are kept separate; node count and topology details may remain unreported.",
            "Repeated published values are summarized by their median; this is not a pooled request-level statistic.",
            "No interpolation, extrapolation, causal attribution, cost/power efficiency or prefill/decode mixed-system inference.",
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
    print("PASS: InferenceX decode GPU scaling", json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
