#!/usr/bin/env python3
"""Measure published InferenceX registry coverage and analysis readiness."""
import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from assess_benchmark_comparability import (
    canonical, observation_blockers, protocol_signature, stable_configuration,
)

WORKLOAD_FIELDS = (
    "benchmark_type", "isl", "osl", "concurrency", "precision",
    "speculative_method", "disaggregated",
)
METRIC_DEFINITIONS = {
    "output_throughput_per_gpu": ("tok/s/GPU", "throughput", "higher"),
    "median_interactivity": ("tok/s/user", "interactivity", "higher"),
    "median_ttft": ("s", "latency", "lower"),
    "p99_ttft": ("s", "latency", "lower"),
    "median_tpot": ("s", "latency", "lower"),
    "p99_tpot": ("s", "latency", "lower"),
    "p99_itl": ("s", "latency", "lower"),
}


def present(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "unknown", "not reported", "n/a", "none"}
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    return True


def positive_integer(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value > 0 and value == int(value))


def metric_valid(record, name, definition):
    metric = (record.get("normalized_metrics") or {}).get(name)
    if not isinstance(metric, dict):
        return False
    value = metric.get("value")
    return (
        not isinstance(value, bool) and isinstance(value, (int, float))
        and math.isfinite(value) and value >= 0
        and (metric.get("unit"), metric.get("family"), metric.get("direction")) == definition
    )


def field_coverage(records, getter):
    values = [getter(record) for record in records]
    present_values = [value for value in values if present(value)]
    unique = {canonical(value) for value in present_values}
    return {
        "present_records": len(present_values),
        "missing_records": len(records) - len(present_values),
        "coverage_percent": round(100 * len(present_values) / len(records), 2) if records else 0,
        "distinct_values": len(unique),
    }


def build_report(database):
    rows = [row for row in database["records"] if row.get("source_id") == "inferencex"]
    total = len(rows)
    blockers = Counter()
    for row in rows:
        blockers.update(observation_blockers(row))

    fields = {
        "model_display_name": lambda r: r.get("model_display_name"),
        "hardware": lambda r: (r.get("system") or {}).get("hardware"),
        "framework": lambda r: (r.get("software") or {}).get("framework"),
        "recipe_fingerprint": lambda r: (r.get("software") or {}).get("recipe_fingerprint"),
        "benchmark_version": lambda r: r.get("benchmark_version"),
        "source_url": lambda r: r.get("detail_url") or r.get("source_url"),
        "source_class": lambda r: r.get("source_class"),
        "evidence_level": lambda r: r.get("evidence_level"),
        "system_type": lambda r: r.get("system_type"),
        "physical_prefill_gpus": lambda r: (r.get("system") or {}).get("physical_prefill_gpus"),
        "physical_decode_gpus": lambda r: (r.get("system") or {}).get("physical_decode_gpus"),
        "is_multinode": lambda r: (r.get("system") or {}).get("is_multinode"),
        "configuration": lambda r: stable_configuration(r) or None,
    }
    fields.update({name: (lambda r, key=key: (r.get("workload") or {}).get(key))
                   for name, key in ((f"workload.{field}", field) for field in WORKLOAD_FIELDS)})
    field_stats = {name: field_coverage(rows, getter) for name, getter in fields.items()}

    metric_stats = {}
    for name, definition in METRIC_DEFINITIONS.items():
        valid = sum(metric_valid(row, name, definition) for row in rows)
        metric_stats[name] = {
            "valid_records": valid,
            "missing_or_invalid_records": total - valid,
            "coverage_percent": round(100 * valid / total, 2) if total else 0,
            "unit": definition[0],
        }

    # Potential multi-point series counts: exact context, with only the named
    # workload dimension removed. This is a coverage signal, not a performance claim.
    analysis = {}
    for analysis_name, varying_fields in {
        "concurrency_sweeps": ("concurrency",),
        "isl_sensitivity": ("isl",),
        "osl_sensitivity": ("osl",),
        "isl_osl_interaction": ("isl", "osl"),
    }.items():
        groups = defaultdict(lambda: defaultdict(set))
        for row in rows:
            blockers_for_row = observation_blockers(row)
            workload = row.get("workload") or {}
            if blockers_for_row or not all(positive_integer(workload.get(k)) for k in ("isl", "osl", "concurrency")):
                continue
            system = row["system"]
            software = row["software"]
            config = stable_configuration(row)
            if not present(system.get("hardware")) or not present(software.get("recipe_fingerprint")) or not config or any(v is None for v in config.values()):
                continue
            protocol = protocol_signature(row)
            for field in varying_fields:
                protocol["workload"].pop(field, None)
            context = {
                "protocol": protocol, "hardware": system.get("hardware"),
                "system_type": row.get("system_type"),
                "system_boundary": {
                    "physical_prefill_gpus": system.get("physical_prefill_gpus"),
                    "physical_decode_gpus": system.get("physical_decode_gpus"),
                    "is_multinode": system.get("is_multinode"),
                    "workers": system.get("workers"),
                },
                "software": software, "configuration": config,
                "source_class": row.get("source_class"),
                "evidence_level": row.get("evidence_level"),
            }
            key = canonical(context)
            value = tuple(workload[field] for field in varying_fields)
            for metric_name, definition in METRIC_DEFINITIONS.items():
                if metric_valid(row, metric_name, definition):
                    groups[(key, metric_name)][value].add(row["id"])
        candidate_groups = 0
        observed_cells = 0
        metric_groups = Counter()
        for (_, metric_name), cells in groups.items():
            if len(cells) < (2 if len(varying_fields) == 1 else 2):
                continue
            if len(varying_fields) == 2 and (
                len({cell[0] for cell in cells}) < 2 or len({cell[1] for cell in cells}) < 2
            ):
                continue
            candidate_groups += 1
            observed_cells += len(cells)
            metric_groups[metric_name] += 1
        analysis[analysis_name] = {
            "candidate_metric_series": candidate_groups,
            "observed_distinct_points_or_cells": observed_cells,
            "by_metric": dict(sorted(metric_groups.items())),
            "qualification": "At least two observed levels (and, for ISL×OSL, two values on each axis) within an exact recorded context. No claim that points are evenly spaced or causally comparable beyond recorded fields.",
        }

    return {
        "schema_version": "1.0",
        "report_type": "inferencex_registry_coverage_intelligence",
        "summary": {
            "inferencex_records": total,
            "records_without_any_comparability_blocker": sum(not observation_blockers(row) for row in rows),
            "records_with_hardware_and_recipe_fingerprint": sum(
                present((r.get("system") or {}).get("hardware"))
                and present((r.get("software") or {}).get("recipe_fingerprint")) for r in rows
            ),
        },
        "field_coverage": field_stats,
        "metric_coverage": metric_stats,
        "comparability_blockers": dict(sorted(blockers.items())),
        "analysis_readiness": analysis,
        "limitations": [
            "Coverage is measured against records currently present in the registry, not the universe of all published InferenceX results.",
            "A populated field may still be inaccurate, inconsistently normalized, or insufficiently specific.",
            "Distinct values do not imply a useful distribution or a comparable cohort.",
            "Candidate series counts are based on exact recorded metadata and do not prove identical hidden execution conditions.",
            "Coverage does not imply performance, ranking, scaling, or causal conclusions.",
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
    print("PASS: InferenceX registry coverage", json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
