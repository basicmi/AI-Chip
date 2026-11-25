#!/usr/bin/env python3
"""Analyze published InferenceX prefill/decode GPU-count sensitivity."""
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

PHASE_METRICS = {
    "prefill": {
        "median_ttft": ("s", "latency", "lower"),
        "p99_ttft": ("s", "latency", "lower"),
    },
    "decode": {
        "median_tpot": ("s", "latency", "lower"),
        "p99_tpot": ("s", "latency", "lower"),
        "p99_itl": ("s", "latency", "lower"),
        "output_throughput_per_gpu": ("tok/s/GPU", "throughput", "higher"),
    },
}


def positive_integer(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value > 0 and value == int(value))


def valid_metric(record, name, definition):
    metric = (record.get("normalized_metrics") or {}).get(name)
    if not isinstance(metric, dict):
        return None
    value = metric.get("value")
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0
            or (metric.get("unit"), metric.get("family"), metric.get("direction")) != definition):
        return None
    return value


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
        software = row["software"]
        config = stable_configuration(row)
        hardware = system.get("hardware")
        fingerprint = software.get("recipe_fingerprint")
        if not isinstance(hardware, str) or not hardware.strip() or not isinstance(fingerprint, str) or not fingerprint.strip():
            excluded["missing_hardware_or_recipe_fingerprint"] += 1
            continue
        if not config or any(value is None for value in config.values()):
            excluded["incomplete_execution_configuration"] += 1
            continue
        prefill = system.get("physical_prefill_gpus")
        decode = system.get("physical_decode_gpus")
        if not positive_integer(decode) or not isinstance(prefill, (int, float)) or isinstance(prefill, bool) or not math.isfinite(prefill) or prefill < 0 or prefill != int(prefill):
            excluded["invalid_gpu_role_counts"] += 1
            continue

        protocol = protocol_signature(row)
        for phase, gpu_count in (("prefill", int(prefill)), ("decode", int(decode))):
            if gpu_count <= 0:
                excluded[phase + "_phase_not_present"] += 1
                continue
            other_phase_count = decode if phase == "prefill" else prefill
            context = {
                "protocol": protocol,
                "phase": phase,
                "hardware": hardware,
                "system_type": row.get("system_type"),
                "is_multinode": system.get("is_multinode"),
                "other_phase_gpu_count": other_phase_count,
                "software": software,
                "configuration": config,
                "source_class": row.get("source_class"),
                "evidence_level": row.get("evidence_level"),
            }
            key = canonical(context)
            for metric_name, definition in PHASE_METRICS[phase].items():
                value = valid_metric(row, metric_name, definition)
                if value is None:
                    continue
                buckets[(phase, key, metric_name)][gpu_count].append({
                    "record_id": row["id"], "value": value,
                    "source_url": row.get("detail_url") or row.get("source_url"),
                    "publication_date": row.get("publication_date"),
                })

    series = []
    for (phase, key, metric_name), levels in sorted(buckets.items()):
        if len(levels) < 2:
            continue
        context = json.loads(key)
        metric_definition = PHASE_METRICS[phase][metric_name]
        points = []
        for gpu_count, observations in sorted(levels.items()):
            observations.sort(key=lambda item: item["record_id"])
            values = [item["value"] for item in observations]
            points.append({
                "phase_gpu_count": gpu_count,
                "observations": observations,
                "count": len(values),
                "min": min(values),
                "median_of_published_values": median(values),
                "max": max(values),
                "unit": metric_definition[0],
            })
        baseline = points[0]["median_of_published_values"]
        for point in points:
            current = point["median_of_published_values"]
            point["change_from_smallest_observed_gpu_count_percent"] = (
                (current - baseline) / abs(baseline) * 100 if baseline != 0 else None
            )
        series.append({
            "id": digest({"context": context, "metric": metric_name})[:20],
            "phase": phase,
            "metric": metric_name,
            "direction": metric_definition[2],
            "context": context,
            "baseline_gpu_count": points[0]["phase_gpu_count"],
            "points": points,
        })

    return {
        "schema_version": "1.0",
        "report_type": "inferencex_prefill_decode_gpu_count_sensitivity",
        "summary": {
            "inferencex_records_seen": seen,
            "series_count": len(series),
            "prefill_series": sum(item["phase"] == "prefill" for item in series),
            "decode_series": sum(item["phase"] == "decode" for item in series),
            "exclusion_reason_counts": dict(sorted(excluded.items())),
        },
        "series": series,
        "method": {
            "prefill_metrics": sorted(PHASE_METRICS["prefill"]),
            "decode_metrics": sorted(PHASE_METRICS["decode"]),
            "comparison": "Only the GPU count for the named phase varies. The other phase GPU count, serving mode, workload, hardware, topology, software, recipe fingerprint and stable configuration are held equal in recorded metadata.",
            "change": "100 × (median metric at N - median metric at baseline) / abs(baseline median metric).",
        },
        "limitations": [
            "This reports descriptive metric changes, not scaling efficiency or causal attribution.",
            "Prefill GPU count zero is not a prefill scaling point; decode GPU count must be positive.",
            "Prefill uses TTFT metrics; decode uses TPOT, ITL and source-published output throughput/GPU. No phase-specific throughput metric is inferred.",
            "TP/EP and other stable configuration fields are held fixed; this does not measure scaling strategies that change parallelism with GPU count.",
            "The other phase GPU count and disaggregation flag remain fixed, so mixed and disaggregated serving cohorts are not silently combined.",
            "No aggregate throughput is synthesized from per-GPU throughput.",
            "Repeated published values are summarized by their median; this is not a pooled request-level statistic.",
            "Unreported topology and runtime details may still confound comparisons. No interpolation, extrapolation, cost/power inference or benchmark execution.",
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
    print("PASS: InferenceX prefill/decode GPU sensitivity", json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
