#!/usr/bin/env python3
"""Conservatively assess whether reviewed performance knowledge applies to a target context."""
import argparse
import json
from pathlib import Path
from copy import deepcopy

from review_performance_experiment_evidence import require, nonempty, digest

DIMENSIONS = {
    "hardware": {"hardware", "gpu", "accelerator", "device", "chip", "architecture", "sku"},
    "model": {"model", "model_name", "model_family", "model_size", "parameters", "quantization", "precision"},
    "workload": {"workload", "isl", "osl", "input_length", "output_length", "sequence_length",
                 "context_length", "batch_size", "concurrency", "request_rate", "traffic_shape"},
    "parallelism": {"parallelism", "tp", "pp", "dp", "ep", "cp", "world_size", "num_gpus",
                    "tensor_parallel", "pipeline_parallel", "expert_parallel"},
    "software": {"software", "runtime", "serving_engine", "compiler", "kernel", "driver",
                 "firmware", "cuda", "rocm", "version", "library"},
    "topology": {"topology", "interconnect", "network", "fabric", "link_bandwidth",
                 "num_nodes", "nodes", "placement"},
    "measurement": {"metric", "metric_key", "unit", "aggregation", "sampling_window",
                    "measurement_boundary", "scope", "entity_id"},
}


def flatten(value, prefix=""):
    result = {}
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten(child, path))
    else:
        result[prefix] = value
    return result


def dimension(path):
    parts = {p.lower() for p in path.replace("-", "_").split(".")}
    for name, keys in DIMENSIONS.items():
        if parts & keys:
            return name
    return "other"


def canonical(value):
    if isinstance(value, str):
        return value.strip().casefold()
    return value


def assess_entry(entry, target):
    require(isinstance(entry, dict) and entry.get("knowledge_status") == "human_reviewed_claim",
            "Entry is not a human-reviewed knowledge claim")
    require(isinstance(target, dict), "Target context must be an object")
    scope = entry.get("scope")
    require(isinstance(scope, dict) and isinstance(scope.get("fixed_context"), dict),
            "Knowledge entry has no structured fixed context")
    source = flatten(scope["fixed_context"])
    requested = flatten(target)
    require(bool(requested), "Target context cannot be empty")
    comparisons = []
    for path, expected in source.items():
        group = dimension(path)
        if path not in requested:
            state, actual = "unknown", None
        elif canonical(expected) == canonical(requested[path]):
            state, actual = "match", requested[path]
        else:
            state, actual = "mismatch", requested[path]
        comparisons.append({"field": path, "dimension": group, "status": state,
                            "knowledge_value": expected, "target_value": actual})
    for path, actual in requested.items():
        if path not in source:
            comparisons.append({"field": path, "dimension": dimension(path),
                                "status": "target_only_unassessed",
                                "knowledge_value": None, "target_value": actual})
    counts = {name: {"match": 0, "mismatch": 0, "unknown": 0}
              for name in [*DIMENSIONS, "other"]}
    for item in comparisons:
        if item["status"] in ("match", "mismatch", "unknown"):
            counts[item["dimension"]][item["status"]] += 1
    mismatch = [x for x in comparisons if x["status"] == "mismatch"]
    unknown = [x for x in comparisons if x["status"] == "unknown"]
    if mismatch:
        status = "not_applicable_under_declared_context"
    elif unknown:
        status = "insufficient_context"
    else:
        status = "declared_context_match"
    return {
        "knowledge_id": entry["knowledge_id"],
        "topic": entry.get("topic"),
        "knowledge_verdict": entry.get("verdict"),
        "applicability_status": status,
        "human_review_required": True,
        "automatic_transfer_approval": False,
        "match_count": sum(x["status"] == "match" for x in comparisons),
        "mismatch_count": len(mismatch),
        "unknown_count": len(unknown),
        "dimension_summary": counts,
        "comparisons": comparisons,
        "unassessed_target_fields": [x["field"] for x in comparisons
                                     if x["status"] == "target_only_unassessed"],
        "metric_compatibility": "not_assessed",
        "intervention_transferability": "not_assessed",
        "limitations": [
            "Exact declared-context comparison only; no physical or semantic equivalence is inferred.",
            "A mismatch means the target differs from the reviewed conditions, not that the underlying mechanism is impossible.",
            "Missing fields are unknown, never assumed equal.",
            "Metric definition, measurement boundaries and intervention transferability require separate review.",
            "A full context match is necessary for direct reuse, not sufficient to recommend or guarantee an outcome."
        ]
    }


def assess_catalog(catalog, target, metric=None):
    require(isinstance(catalog, dict) and catalog.get("schema_version") == "1.0"
            and isinstance(catalog.get("entries"), list), "Invalid knowledge catalog")
    results = [assess_entry(entry, target) for entry in catalog["entries"]]
    if metric is not None:
        require(isinstance(metric, dict), "Metric filter must be an object")
        for result, entry in zip(results, catalog["entries"]):
            source_metric = entry.get("scope", {}).get("metric", {})
            result["metric_compatibility"] = (
                "exact_match" if all(source_metric.get(k) == metric.get(k)
                                     for k in ("key", "unit", "direction"))
                and all(k in metric for k in ("key", "unit", "direction"))
                else "mismatch_or_unknown"
            )
    order = {"declared_context_match": 0, "insufficient_context": 1,
             "not_applicable_under_declared_context": 2}
    results.sort(key=lambda x: (order[x["applicability_status"]],
                                x["unknown_count"], x["mismatch_count"],
                                x["knowledge_id"]))
    return {
        "schema_version": "1.0",
        "report_type": "knowledge_applicability_assessment",
        "target_context": deepcopy(target),
        "target_context_sha256": digest(target),
        "results": results,
        "policy": {"missing_context_is_unknown": True,
                   "context_mismatch_blocks_direct_reuse": True,
                   "human_review_required": True,
                   "automatic_recommendations": False}
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--metric", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = [args.catalog, args.target] + ([args.metric] if args.metric else [])
    require(args.output.resolve() not in {p.resolve() for p in inputs},
            "Output must not overwrite an input")
    catalog, target = [json.loads(p.read_text(encoding="utf-8"))
                       for p in (args.catalog, args.target)]
    metric = json.loads(args.metric.read_text(encoding="utf-8")) if args.metric else None
    result = assess_catalog(catalog, target, metric)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False,
                                      allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
