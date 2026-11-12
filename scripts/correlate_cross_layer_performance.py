#!/usr/bin/env python3
"""Build strict-workload, cross-layer performance comparison reports.

This tool matches benchmark records by the same workload contract, then compares
hardware/runtime configurations. It reports measured differences and evidence
coverage; it does not infer causal hardware bottlenecks or statistical correlation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from diagnose_hardware_performance import diagnose_record

DERIVER = "scripts/correlate_cross_layer_performance.py"
MAX_COMPARISONS_PER_COHORT = 100
PERFORMANCE_METRICS = {
    "median_ttft": ("s", "lower", "latency"),
    "p99_ttft": ("s", "lower", "latency"),
    "median_tpot": ("s", "lower", "latency"),
    "p99_tpot": ("s", "lower", "latency"),
    "p99_itl": ("s", "lower", "latency"),
    "output_throughput_per_gpu": ("tok/s/GPU", "higher", "throughput"),
    "median_interactivity": ("tok/s/user", "higher", "interactivity"),
    "energy_per_output_token": ("J/output token", "lower", "energy"),
    "energy_per_total_token": ("J/total token", "lower", "energy"),
    "energy_per_successful_query": ("J/query", "lower", "energy"),
    "prefill_energy_per_input_token": ("J/input token", "lower", "energy"),
    "decode_energy_per_output_token": ("J/output token", "lower", "energy"),
}
IDENTITY_FIELDS = (
    "accelerator_vendor", "platform_id", "product_id", "system_type",
    "system_name", "system_hardware", "nodes", "total_accelerators",
    "accelerators_per_node", "is_multinode", "physical_prefill_gpus",
    "physical_decode_gpus", "framework", "image", "recipe_fingerprint",
    "configuration", "workers",
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _present(value: Any) -> bool:
    return value is not None and value != ""


def _signature(record: dict, source_versions: dict) -> tuple[dict | None, str | None]:
    """Mirror the site's strict InferenceX workload identity, including source version fallback."""
    if record.get("source_id") != "inferencex":
        return None, "source is not InferenceX"
    workload = record.get("workload") if isinstance(record.get("workload"), dict) else {}
    version = record.get("benchmark_version") or source_versions.get("inferencex")
    model = record.get("model_display_name") or record.get("model")
    workload_type = workload.get("benchmark_type") or record.get("scenario")
    serving_mode = workload.get("disaggregated")
    signature = {
        "source_id": record.get("source_id"),
        "benchmark_suite": record.get("benchmark_suite"),
        "benchmark_version": version,
        "model_display_name": model,
        "model_id": record.get("model"),
        "workload_type": workload_type,
        "scenario": record.get("scenario"),
        "division": record.get("division"),
        "availability": record.get("availability"),
        "system_type": record.get("system_type"),
        "isl": workload.get("isl"),
        "osl": workload.get("osl"),
        "concurrency": workload.get("concurrency"),
        "precision": workload.get("precision") or record.get("weight_data_types"),
        "speculative_method": workload.get("speculative_method"),
        "disaggregated": serving_mode,
    }
    missing = [key for key, value in signature.items() if not _present(value)]
    if missing:
        return None, "missing strict workload identity fields: " + ", ".join(missing)
    if not isinstance(serving_mode, bool):
        return None, "workload.disaggregated must be an explicit boolean"
    return signature, None


def _execution_identity(record: dict) -> tuple[dict, bool]:
    system = record.get("system") if isinstance(record.get("system"), dict) else {}
    software = record.get("software") if isinstance(record.get("software"), dict) else {}
    identity = {
        "accelerator_vendor": record.get("accelerator_vendor"),
        "platform_id": record.get("platform_id"),
        "product_id": record.get("product_id"),
        "system_type": record.get("system_type"),
        "system_name": record.get("system_name"),
        "system_hardware": system.get("hardware"),
        "nodes": system.get("nodes"),
        "total_accelerators": system.get("total_accelerators"),
        "accelerators_per_node": system.get("accelerators_per_node"),
        "is_multinode": system.get("is_multinode"),
        "physical_prefill_gpus": system.get("physical_prefill_gpus"),
        "physical_decode_gpus": system.get("physical_decode_gpus"),
        "framework": software.get("framework"),
        "image": software.get("image"),
        "recipe_fingerprint": software.get("recipe_fingerprint"),
        "configuration": record.get("configuration") if isinstance(record.get("configuration"), dict) else {},
        "workers": system.get("workers") if isinstance(system.get("workers"), list) else [],
    }
    hardware_identified = any(_present(identity[key]) for key in (
        "product_id", "system_name", "system_hardware", "platform_id"
    ))
    runtime_identified = any(_present(identity[key]) for key in (
        "framework", "image", "recipe_fingerprint"
    ))
    return identity, hardware_identified and runtime_identified


def _normalized_metrics(record: dict) -> dict:
    source = record.get("normalized_metrics")
    if not isinstance(source, dict):
        return {}
    result = {}
    for key, expected in PERFORMANCE_METRICS.items():
        item = source.get(key)
        if not isinstance(item, dict):
            continue
        unit, direction, family = expected
        value = item.get("value")
        if (
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or item.get("unit") != unit
            or item.get("direction") != direction or item.get("family") != family
        ):
            continue
        if family in {"energy"} and (
            record.get("power_measurement_valid") is not True
            or record.get("gpu_power_metrics_available") is not True
        ):
            continue
        result[key] = {
            "value": value, "unit": unit, "direction": direction, "family": family
        }
    return result


def _hardware_summary(record: dict) -> dict:
    evidence = record.get("hardware_evidence")
    if not isinstance(evidence, dict):
        return {
            "status": "missing",
            "metric_count": 0,
            "sampling_window_seconds": None,
            "temporal_alignment": "not_established",
            "roofline": "insufficient_evidence",
            "roofline_analyses": [],
            "communication": "insufficient_evidence",
            "observed_links": [],
            "kv_cache_observations": [],
            "throttle_observations": [],
        }
    diagnosis = diagnose_record(record)
    roofline = diagnosis["roofline"]
    communication = diagnosis["communication"]
    attribution = diagnosis["attribution"]
    return {
        "status": "available",
        "metric_count": len(evidence.get("metrics", [])),
        "sampling_window_seconds": diagnosis.get("sampling_window_seconds"),
        "collector": evidence.get("collector", {}).get("name"),
        "system_scope": evidence.get("system_scope", {}).get("scope_type"),
        "temporal_alignment": "not_established",
        "roofline": roofline.get("status"),
        "roofline_analyses": [
            {
                "entity_id": item.get("entity_id"),
                "precision": item.get("precision"),
                "arithmetic_intensity_flop_per_byte": item.get("arithmetic_intensity_flop_per_byte"),
                "achieved_flops_per_second": item.get("achieved_flops_per_second"),
                "roofline_ceiling_flops_per_second": item.get("roofline_ceiling_flops_per_second"),
                "lower_theoretical_ceiling": item.get("lower_theoretical_ceiling"),
                "roofline_attainment_pct": item.get("roofline_attainment_pct"),
                "status": item.get("status"),
                "missing_inputs": item.get("missing_inputs", []),
            }
            for item in roofline.get("analyses", [])
        ],
        "communication": communication.get("status"),
        "observed_links": [
            {
                "entity_id": item.get("entity_id"),
                "link_type": item.get("link_type"),
                "directionality": item.get("directionality"),
                "utilization_pct": item.get("utilization_pct"),
                "status": item.get("status"),
            }
            for item in communication.get("links", [])
        ],
        "kv_cache_observations": [
            {
                "entity_id": item.get("entity_id"),
                "scope": item.get("scope"),
                "occupancy_pct": item.get("occupancy_pct"),
                "unit": item.get("unit"),
            }
            for item in attribution.get("candidates", [])
            if item.get("mechanism") == "kv_cache_occupancy" and item.get("status") == "observed"
        ],
        "throttle_observations": [
            {
                "scope": item.get("scope"),
                "entity_id": item.get("entity_id"),
                "status": item.get("status"),
                "observation": item.get("observation"),
            }
            for item in attribution.get("candidates", [])
            if item.get("mechanism") == "thermal_or_power_throttling"
        ],
    }


def _record_profile(record: dict) -> dict:
    identity, identity_complete = _execution_identity(record)
    metrics = _normalized_metrics(record)
    return {
        "record_id": record.get("id"),
        "source_url": record.get("source_url"),
        "publication_date": record.get("publication_date"),
        "execution_identity": identity,
        "execution_identity_complete": identity_complete,
        "normalized_metrics": metrics,
        "hardware_evidence": _hardware_summary(record),
    }


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _aggregate_execution_group(profiles: list[dict], fingerprint: str) -> dict:
    metric_keys = sorted(set.union(*[
        set(profile["normalized_metrics"]) for profile in profiles
    ])) if profiles else []
    metrics = {}
    for key in metric_keys:
        items = [profile["normalized_metrics"][key] for profile in profiles if key in profile["normalized_metrics"]]
        if len({(item["unit"], item["direction"], item["family"]) for item in items}) != 1:
            continue
        metrics[key] = {
            "value": _median([item["value"] for item in items]),
            "unit": items[0]["unit"],
            "direction": items[0]["direction"],
            "family": items[0]["family"],
            "aggregation": "median_across_available_records",
            "record_count": len(items),
            "group_record_count": len(profiles),
        }
    evidence_profiles = [profile for profile in profiles if profile["hardware_evidence"]["status"] == "available"]
    return {
        "execution_fingerprint": fingerprint,
        "execution_identity": profiles[0]["execution_identity"],
        "execution_identity_complete": all(p["execution_identity_complete"] for p in profiles),
        "record_ids": [p["record_id"] for p in profiles],
        "record_count": len(profiles),
        "normalized_metrics": metrics,
        "hardware_evidence_coverage": {
            "records_with_evidence": len(evidence_profiles),
            "records_without_evidence": len(profiles) - len(evidence_profiles),
            "evidence_metric_count": sum(p["hardware_evidence"]["metric_count"] for p in evidence_profiles),
            "temporal_alignment": "not_established",
        },
        "hardware_evidence_profiles": [
            {"record_id": p["record_id"], **p["hardware_evidence"]}
            for p in evidence_profiles
        ],
    }


def _compare_groups(left: dict, right: dict) -> dict:
    left_metrics, right_metrics = left["normalized_metrics"], right["normalized_metrics"]
    common = sorted(set(left_metrics) & set(right_metrics))
    deltas = []
    for key in common:
        a, b = left_metrics[key], right_metrics[key]
        if (a["unit"], a["direction"], a["family"]) != (b["unit"], b["direction"], b["family"]):
            continue
        baseline, candidate = a["value"], b["value"]
        if not _valid_comparison_value(baseline) or not _valid_comparison_value(candidate):
            continue
        delta = (candidate - baseline) / baseline * 100
        improvement = -delta if a["direction"] == "lower" else delta if a["direction"] == "higher" else None
        deltas.append({
            "metric": key,
            "left_value": baseline,
            "right_value": candidate,
            "unit": a["unit"],
            "direction": a["direction"],
            "right_vs_left_change_pct": delta,
            "right_vs_left_improvement_pct": improvement,
        })
    left_id, right_id = left["execution_identity"], right["execution_identity"]
    changed_dimensions = [
        key for key in IDENTITY_FIELDS if left_id.get(key) != right_id.get(key)
    ]
    return {
        "left_execution_fingerprint": left["execution_fingerprint"],
        "right_execution_fingerprint": right["execution_fingerprint"],
        "left_record_ids": left["record_ids"],
        "right_record_ids": right["record_ids"],
        "changed_dimensions": changed_dimensions,
        "metric_deltas": deltas,
        "left_hardware_evidence_records": left["hardware_evidence_coverage"]["records_with_evidence"],
        "right_hardware_evidence_records": right["hardware_evidence_coverage"]["records_with_evidence"],
        "temporal_alignment": "not_established",
        "causal_attribution": "not_claimed",
    }


def _valid_comparison_value(value: Any) -> bool:
    return (
        not isinstance(value, bool) and isinstance(value, (int, float))
        and math.isfinite(value) and value > 0
    )


def correlate_records(database: dict | list, max_comparisons: int = MAX_COMPARISONS_PER_COHORT) -> dict:
    if isinstance(database, list):
        records, sources = database, []
    elif isinstance(database, dict):
        records = database.get("records")
        sources = database.get("sources", [])
    else:
        raise ValueError("input must be a benchmark database object or record array")
    if not isinstance(records, list):
        raise ValueError("input must contain a records array")
    if not isinstance(sources, list):
        raise ValueError("sources must be an array")
    if isinstance(max_comparisons, bool) or not isinstance(max_comparisons, int) or max_comparisons < 0:
        raise ValueError("max_comparisons must be a non-negative integer")

    source_versions = {
        item.get("id"): item.get("version")
        for item in sources if isinstance(item, dict) and _present(item.get("id"))
    }
    cohorts: dict[str, list[dict]] = {}
    excluded = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            excluded.append({"index": index, "reason": "record is not an object"})
            continue
        signature, reason = _signature(record, source_versions)
        if signature is None:
            excluded.append({"record_id": record.get("id"), "reason": reason})
            continue
        key = _canonical(signature)
        cohorts.setdefault(key, []).append(record)

    output_cohorts = []
    total_pairs_omitted = 0
    for signature_json, cohort_records in sorted(cohorts.items()):
        signature = json.loads(signature_json)
        profiles = [_record_profile(record) for record in cohort_records]
        by_execution: dict[str, list[dict]] = {}
        for profile in profiles:
            identity_key = _canonical(profile["execution_identity"])
            # Incomplete identities are kept separate; they must not create false peers.
            fingerprint_payload = (
                identity_key if profile["execution_identity_complete"]
                else identity_key + "|record:" + str(profile["record_id"])
            )
            fingerprint = hashlib.sha256(fingerprint_payload.encode("utf-8")).hexdigest()[:16]
            by_execution.setdefault(fingerprint, []).append(profile)
        execution_groups = [
            _aggregate_execution_group(group, fingerprint)
            for fingerprint, group in sorted(by_execution.items())
        ]
        comparable_groups = [group for group in execution_groups if group["execution_identity_complete"]]
        comparisons = []
        for left, right in combinations(comparable_groups, 2):
            if len(comparisons) >= max_comparisons:
                total_pairs_omitted += (
                    len(comparable_groups) * (len(comparable_groups) - 1) // 2 - len(comparisons)
                )
                break
            comparisons.append(_compare_groups(left, right))
        output_cohorts.append({
            "workload_signature": signature,
            "workload_fingerprint": hashlib.sha256(signature_json.encode("utf-8")).hexdigest()[:16],
            "record_count": len(cohort_records),
            "execution_group_count": len(execution_groups),
            "comparable_execution_group_count": len(comparable_groups),
            "records": profiles,
            "execution_groups": execution_groups,
            "pairwise_comparisons": comparisons,
            "pairwise_comparisons_truncated": (
                len(comparable_groups) * (len(comparable_groups) - 1) // 2 > len(comparisons)
            ),
            "interpretation": (
                "Records share the strict workload signature. Execution groups differ in one or more hardware, "
                "software, topology or configuration fields. Metric deltas are descriptive; they do not isolate "
                "a hardware effect or establish causality."
            ),
        })

    return {
        "schema_version": "1.0",
        "generated_by": DERIVER,
        "source_scope": "inferencex_strict_workload_cohorts",
        "input_record_count": len(records),
        "matched_record_count": sum(item["record_count"] for item in output_cohorts),
        "excluded_record_count": len(excluded),
        "cohort_count": len(output_cohorts),
        "total_pairwise_comparisons_omitted": total_pairs_omitted,
        "cohorts": output_cohorts,
        "excluded_records": excluded,
        "limitations": [
            "Only records with a complete strict InferenceX workload signature are grouped; missing fields are not wildcard matches.",
            "The strict workload signature follows the Results Explorer cohort contract and does not imply identical benchmark execution conditions beyond those fields.",
            "Execution groups include hardware, system topology, software identity, workers and full configuration; a comparison may change several dimensions at once.",
            "Normalized runtime metrics and profiler/telemetry evidence may come from different collection windows. Temporal alignment is not established unless separately instrumented.",
            "Median aggregation across repeated records is descriptive and does not imply statistical significance or equivalent run variance.",
            "Hardware evidence is summarized per record; unlike counter values are not averaged across devices, scopes, collectors or sampling windows.",
            "No Pearson/Spearman correlation, causal effect, bottleneck ranking, confidence score or automatic verdict is produced.",
            "Only positive left/right values are used for relative percentage deltas; zero or missing values remain unavailable.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Benchmark database JSON or a record array")
    parser.add_argument("--output", required=True, type=Path, help="Destination report JSON; input is never overwritten")
    parser.add_argument("--max-comparisons-per-cohort", type=int, default=MAX_COMPARISONS_PER_COHORT)
    args = parser.parse_args()
    try:
        source = json.loads(args.input.read_text(encoding="utf-8"))
        report = correlate_records(source, args.max_comparisons_per_cohort)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: {report['matched_record_count']}/{report['input_record_count']} records matched "
        f"into {report['cohort_count']} strict workload cohorts; "
        f"{sum(len(item['pairwise_comparisons']) for item in report['cohorts'])} descriptive comparisons. "
        "No causal attribution was generated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
