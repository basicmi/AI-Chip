#!/usr/bin/env python3
"""Build conservative, provenance-preserving benchmark comparability groups.

This tool identifies records that share an exact published test definition and
system boundary. It never equates different benchmark suites or infers missing
workload/system metadata. A group is a review aid, not a performance ranking.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "benchmark-results.json"
POLICY_VERSION = "1.0"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def metric_observations(record):
    normalized = record.get("normalized_metrics")
    if isinstance(normalized, dict) and normalized:
        result = []
        for key, item in sorted(normalized.items()):
            if not isinstance(item, dict):
                continue
            value = item.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                continue
            result.append({
                "key": key, "value": value, "unit": item.get("unit"),
                "family": item.get("family"), "direction": item.get("direction"),
                "label": item.get("label"), "source_metric": item.get("source_metric"),
            })
        return result
    value = record.get("result_value")
    unit = record.get("result_unit")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return []
    if not nonempty(unit):
        return []
    return [{
        "key": "result_value", "value": value, "unit": unit,
        "family": "suite_scalar", "direction": "unspecified",
        "label": record.get("benchmark_suite", "Published result"),
        "source_metric": "result_value",
    }]


def observation_blockers(record):
    blockers = []
    source_id = record.get("source_id")
    suite = record.get("benchmark_suite")
    for field in ("id", "benchmark_suite", "model", "scenario", "division", "availability", "weight_data_types"):
        if not nonempty(record.get(field)):
            blockers.append("missing_" + field)
    if record.get("inferred") is not False:
        blockers.append("result_is_inferred_or_inference_status_unknown")
    if record.get("errors") != 0:
        blockers.append("nonzero_or_unknown_error_count")

    system = record.get("system")
    if not isinstance(system, dict):
        blockers.append("missing_system_definition")
        system = {}
    software = record.get("software")
    if not isinstance(software, dict) or not nonempty(software.get("framework")):
        blockers.append("missing_software_framework")
    if not (nonempty(record.get("product_id")) or nonempty(system.get("accelerator_model"))):
        blockers.append("missing_accelerator_identity")

    if source_id == "inferencex" or suite == "SemiAnalysis InferenceX":
        workload = record.get("workload")
        if not isinstance(workload, dict):
            blockers.append("missing_inferencex_workload")
            workload = {}
        for field in ("benchmark_type", "isl", "osl", "concurrency", "precision"):
            value = workload.get(field)
            if value is None or value == "" or value == "unknown":
                blockers.append("missing_inferencex_workload_" + field)
        if not isinstance(workload.get("disaggregated"), bool):
            blockers.append("missing_inferencex_serving_mode")
        if not nonempty(workload.get("speculative_method")):
            blockers.append("missing_inferencex_speculative_method")
        if not isinstance(record.get("configuration"), dict):
            blockers.append("missing_inferencex_configuration")
        for field in ("physical_prefill_gpus", "physical_decode_gpus"):
            value = system.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                blockers.append("missing_or_invalid_" + field)
        if not isinstance(system.get("is_multinode"), bool):
            blockers.append("missing_inferencex_topology")
        if not nonempty(record.get("model_display_name")):
            blockers.append("missing_model_display_name")
    elif source_id == "mlperf-inference-v6.1" or suite == "MLPerf Inference":
        for field in ("benchmark_version", "accuracy_text"):
            if not nonempty(record.get(field)):
                blockers.append("missing_" + field)
        for field in ("nodes", "total_accelerators", "accelerators_per_node"):
            value = system.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                blockers.append("missing_or_invalid_system_" + field)
        if not nonempty(system.get("host_processor_model")):
            blockers.append("missing_system_host_processor_model")
        if not nonempty(record.get("result_unit")):
            blockers.append("missing_result_unit")
    else:
        for field in ("benchmark_version", "accuracy_text"):
            if not nonempty(record.get(field)):
                blockers.append("missing_" + field)
        if not isinstance(record.get("workload"), dict) or not record["workload"]:
            blockers.append("missing_workload_definition")
        if not isinstance(record.get("configuration"), dict) or not record["configuration"]:
            blockers.append("missing_benchmark_configuration")
        for field in ("nodes", "total_accelerators", "accelerators_per_node"):
            value = system.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                blockers.append("missing_or_invalid_system_" + field)
        if not nonempty(system.get("host_processor_model")):
            blockers.append("missing_system_host_processor_model")

    if not metric_observations(record):
        blockers.append("missing_numeric_metric")
    return sorted(set(blockers))


def protocol_signature(record):
    source_id = record.get("source_id")
    suite = record.get("benchmark_suite")
    if source_id == "inferencex" or suite == "SemiAnalysis InferenceX":
        workload = record["workload"]
        return {
            "profile": "inferencex",
            "source_id": source_id,
            "benchmark_suite": suite,
            "benchmark_version": record.get("benchmark_version"),
            "model": record.get("model_display_name"),
            "raw_model_key": record.get("model"),
            "scenario": record.get("scenario"),
            "division": record.get("division"),
            "availability": record.get("availability"),
            "weight_data_types": record.get("weight_data_types"),
            "workload": {key: workload.get(key) for key in (
                "benchmark_type", "isl", "osl", "concurrency", "precision",
                "speculative_method", "disaggregated"
            )},
            "configuration": record.get("configuration") or {},
        }
    if source_id == "mlperf-inference-v6.1" or suite == "MLPerf Inference":
        return {
            "profile": "mlperf_inference",
            "benchmark_suite": suite,
            "benchmark_version": record.get("benchmark_version"),
            "model": record.get("model"),
            "scenario": record.get("scenario"),
            "division": record.get("division"),
            "availability": record.get("availability"),
            "accuracy_text": record.get("accuracy_text"),
            "weight_data_types": record.get("weight_data_types"),
            "result_unit": record.get("result_unit"),
        }
    return {
        "profile": "generic",
        "benchmark_suite": record["benchmark_suite"],
        "benchmark_version": record["benchmark_version"],
        "model": record["model"],
        "scenario": record["scenario"],
        "division": record["division"],
        "availability": record["availability"],
        "accuracy_text": record["accuracy_text"],
        "weight_data_types": record["weight_data_types"],
        "workload": record["workload"],
        "configuration": record["configuration"],
    }


def system_boundary(record):
    system = record["system"]
    if record.get("source_id") == "inferencex" or record.get("benchmark_suite") == "SemiAnalysis InferenceX":
        return {
            "system_type": record.get("system_type"),
            "physical_prefill_gpus": system["physical_prefill_gpus"],
            "physical_decode_gpus": system["physical_decode_gpus"],
            "is_multinode": system["is_multinode"],
            "workers": system.get("workers") or [],
        }
    return {
        "system_type": record.get("system_type"),
        "nodes": system["nodes"],
        "total_accelerators": system["total_accelerators"],
        "accelerators_per_node": system["accelerators_per_node"],
        "host_processor_model": system["host_processor_model"],
    }


def accelerator_identity(record):
    system = record.get("system") or {}
    return {
        "vendor": record.get("accelerator_vendor"),
        "platform_id": record.get("platform_id"),
        "product_id": record.get("product_id"),
        "model": system.get("accelerator_model"),
        "system_name": record.get("system_name"),
    }


def build_report(database):
    records = database.get("records") if isinstance(database, dict) else None
    if not isinstance(records, list):
        raise ValueError("benchmark registry records must be an array")

    buckets = defaultdict(list)
    excluded = []
    observation_count = 0

    for record in records:
        if not isinstance(record, dict):
            excluded.append({"record_id": None, "reasons": ["record_is_not_an_object"]})
            continue
        blockers = observation_blockers(record)
        observations = metric_observations(record)
        if blockers:
            excluded.append({"record_id": record.get("id"), "reasons": blockers})
            continue

        protocol = protocol_signature(record)
        boundary = system_boundary(record)
        for metric in observations:
            if (not nonempty(metric.get("unit")) or not nonempty(metric.get("family"))
                    or metric.get("direction") not in {"higher", "lower", "context", "unspecified"}):
                excluded.append({
                    "record_id": record.get("id"),
                    "reasons": ["metric_definition_incomplete:" + str(metric.get("key"))],
                })
                continue
            observation_count += 1
            key = {
                "protocol": protocol,
                "system_boundary": boundary,
                "metric": {k: metric.get(k) for k in ("key", "unit", "family", "direction")},
            }
            buckets[digest(key)].append({
                "record": record,
                "metric": metric,
                "key": key,
            })

    groups = []
    direct_pairs = 0
    conditional_pairs = 0
    for key_hash, members in sorted(buckets.items()):
        # A useful hardware comparison requires at least two distinct
        # accelerator identities; repeated records for one exact system alone
        # are not presented as cross-hardware comparisons.
        unique_accelerators = {
            canonical(accelerator_identity(item["record"])) for item in members
        }
        if len(members) < 2 or len(unique_accelerators) < 2:
            continue

        entries = []
        software_fingerprints = set()
        evidence_classes = set()
        for item in sorted(members, key=lambda x: x["record"].get("id", "")):
            record, metric = item["record"], item["metric"]
            software = record.get("software") or {}
            software_fingerprints.add(canonical(software))
            evidence_classes.add(record.get("evidence_level") or record.get("source_class") or "unknown")
            entries.append({
                "record_id": record["id"],
                "source_id": record.get("source_id"),
                "source_class": record.get("source_class"),
                "evidence_level": record.get("evidence_level"),
                "accelerator": accelerator_identity(record),
                "software": software,
                "value": metric["value"],
                "unit": metric["unit"],
                "source_url": record.get("source_url"),
            })

        status = "directly_comparable" if len(software_fingerprints) == 1 else "conditionally_comparable"
        pairs = len(entries) * (len(entries) - 1) // 2
        if status == "directly_comparable":
            direct_pairs += pairs
        else:
            conditional_pairs += pairs
        groups.append({
            "comparison_group_id": key_hash[:16],
            "status": status,
            "pair_count": pairs,
            "protocol": members[0]["key"]["protocol"],
            "system_boundary": members[0]["key"]["system_boundary"],
            "metric": members[0]["key"]["metric"],
            "records": entries,
            "review_notes": [
                "Exact workload, configuration, benchmark version, accuracy statement and system boundary matched.",
                "Different accelerator identities are retained as the comparison axis.",
                "Direct comparability requires identical software metadata; differing software is conditional.",
                "Evidence class and source provenance remain visible and are not upgraded by this assessment.",
                "A matching test definition does not prove source truth or eliminate measurement uncertainty.",
            ],
            "evidence_classes": sorted(evidence_classes),
        })

    summary = {
        "records_seen": len(records),
        "eligible_metric_observations": observation_count,
        "excluded_records": len(excluded),
        "comparison_groups": len(groups),
        "direct_comparison_pairs": direct_pairs,
        "conditional_comparison_pairs": conditional_pairs,
        "unmatched_or_single_hardware_groups": max(0, len(buckets) - len(groups)),
    }
    return {
        "schema_version": "1.0",
        "policy_version": POLICY_VERSION,
        "report_type": "benchmark_comparability_assessment",
        "summary": summary,
        "groups": groups,
        "excluded_records": sorted(excluded, key=lambda x: str(x.get("record_id"))),
        "limitations": [
            "Suite-specific profiles preserve MLPerf Inference and InferenceX workload semantics; other suites require explicit generic workload/configuration metadata.",
            "System boundary must match exactly within each suite profile: MLPerf/generic node and accelerator counts plus host CPU, or InferenceX prefill/decode GPU counts and topology.",
            "Software metadata differences downgrade a group to conditional comparability.",
            "Missing context is excluded rather than inferred. InferenceX publishes no benchmark version in this registry; comparisons remain within its source and model/workload signature.",
            "Cross-suite normalization, score conversion, causal attribution and leaderboard ranking are out of scope.",
            "Source class/evidence level describe provenance, not measurement correctness.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-results", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        database = json.loads(args.benchmark_results.read_text(encoding="utf-8"))
        report = build_report(database)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("PASS: built benchmark comparability assessment")
        print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
