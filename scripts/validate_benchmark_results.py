#!/usr/bin/env python3
"""Validate the normalized public benchmark results registry."""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "benchmark-results.json"
COMPATIBILITY = ROOT / "data" / "compatibility.json"
PROFILES = ROOT / "data" / "company-profiles.json"


def is_http_url(value):
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def summarize(records):
    def count(field):
        values = Counter(str(row.get(field) or "unknown") for row in records)
        return dict(sorted(values.items()))
    return {
        "total_records": len(records),
        "by_source": count("source_id"),
        "by_availability": count("availability"),
        "by_division": count("division"),
        "by_system_type": count("system_type"),
        "inferred_records": sum(1 for row in records if row.get("inferred") is True),
        "power_records": sum(1 for row in records if row.get("power_metrics_available") is True),
        "submitters": len({row.get("submitter") for row in records}),
        "models": len({row.get("model") for row in records}),
    }


def validate_database(db, platform_ids=None, product_ids=None):
    errors = []
    if db.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    records = db.get("records")
    sources = db.get("sources")
    if not isinstance(records, list):
        errors.append("records must be an array")
        records = []
    if not isinstance(sources, list):
        errors.append("sources must be an array")
        sources = []

    source_map = {}
    for index, source in enumerate(sources):
        sid = source.get("id") if isinstance(source, dict) else None
        if not isinstance(sid, str) or not sid:
            errors.append(f"sources[{index}]: missing id")
            continue
        if sid in source_map:
            errors.append(f"sources[{index}]: duplicate source id {sid}")
        source_map[sid] = source
        if not is_http_url(source.get("results_url")) or not is_http_url(source.get("dataset_url")):
            errors.append(f"sources[{index}]: invalid source URL")
        if not isinstance(source.get("record_count"), int) or source["record_count"] < 0:
            errors.append(f"sources[{index}]: record_count must be a non-negative integer")

    ids = set()
    source_keys = set()
    counts = Counter()
    for index, row in enumerate(records):
        where = f"records[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{where}: must be an object")
            continue
        rid = row.get("id")
        if not isinstance(rid, str) or not rid:
            errors.append(f"{where}: missing id")
        elif rid in ids:
            errors.append(f"{where}: duplicate id {rid}")
        else:
            ids.add(rid)

        sid = row.get("source_id")
        counts[sid] += 1
        if sid not in source_map:
            errors.append(f"{where}: unknown source_id {sid}")
        elif row.get("source_class") != source_map[sid].get("source_class"):
            errors.append(f"{where}: source_class does not match source registry for {sid}")

        source_key = (sid, str(row.get("source_record_key")))
        if source_key in source_keys:
            errors.append(f"{where}: duplicate source record key {source_key}")
        source_keys.add(source_key)

        for field in ("benchmark_suite", "submitter", "system_name", "model", "scenario",
                      "system_type", "division", "availability", "source_class", "evidence_level"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{where}: {field} must be a non-empty string")
        for field in ("source_url", "detail_url", "dataset_url", "release_url"):
            if not is_http_url(row.get(field)):
                errors.append(f"{where}: invalid {field}")
        if row.get("platform_id") and platform_ids is not None and row["platform_id"] not in platform_ids:
            errors.append(f"{where}: unknown platform_id {row['platform_id']}")
        if row.get("product_id") and product_ids is not None and row["product_id"] not in product_ids:
            errors.append(f"{where}: unknown product_id {row['product_id']}")
        value = row.get("result_value")
        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
            errors.append(f"{where}: result_value must be finite or null")
        if not isinstance(row.get("inferred"), bool):
            errors.append(f"{where}: inferred must be boolean")
        if not isinstance(row.get("power_metrics_available"), bool):
            errors.append(f"{where}: power_metrics_available must be boolean")
        if not isinstance(row.get("system"), dict) or not isinstance(row.get("software"), dict):
            errors.append(f"{where}: system and software must be objects")
        if sid == "mlperf-inference-v6.1":
            if value is None or not row.get("result_unit"):
                errors.append(f"{where}: MLPerf result must include a value and unit")
            if row.get("power_metrics_available") is True and row.get("system_type") not in {"datacenter", "edge"}:
                errors.append(f"{where}: unexpected MLPerf power record system_type")
        if sid == "inferencex":
            metrics = row.get("metrics")
            if not isinstance(metrics, dict):
                errors.append(f"{where}: InferenceX metrics must be an object")
                metrics = {}
            for metric_key, metric_value in metrics.items():
                if isinstance(metric_value, bool) or not isinstance(metric_value, (int, float)) or not math.isfinite(metric_value):
                    errors.append(f"{where}: raw InferenceX metric {metric_key} must be a finite number")
            if not isinstance(row.get("model_display_name"), str) or not row["model_display_name"].strip():
                errors.append(f"{where}: model_display_name must be a non-empty string")
            if not isinstance(row.get("power_measurement_valid"), bool):
                errors.append(f"{where}: power_measurement_valid must be boolean")
            normalized = row.get("normalized_metrics")
            if not isinstance(normalized, dict):
                errors.append(f"{where}: normalized_metrics must be an object")
                normalized = {}
            for metric_key, metric in normalized.items():
                if not isinstance(metric, dict):
                    errors.append(f"{where}: normalized metric {metric_key} must be an object")
                    continue
                value = metric.get("value")
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    errors.append(f"{where}: normalized metric {metric_key} must have a finite numeric value")
                if not isinstance(metric.get("label"), str) or not metric["label"].strip():
                    errors.append(f"{where}: normalized metric {metric_key} must have a label")
                if not isinstance(metric.get("unit"), str) or not metric["unit"].strip():
                    errors.append(f"{where}: normalized metric {metric_key} must have a unit")
                if metric.get("direction") not in {"higher", "lower", "context"}:
                    errors.append(f"{where}: normalized metric {metric_key} has an invalid direction")
                if metric.get("family") not in {"interactivity", "throughput", "latency", "energy", "power", "telemetry"}:
                    errors.append(f"{where}: normalized metric {metric_key} has an invalid family")
                source_metric = metric.get("source_metric")
                if source_metric not in metrics:
                    errors.append(f"{where}: normalized metric {metric_key} references a missing raw metric")
                elif isinstance(value, (int, float)) and not isinstance(value, bool) and metrics[source_metric] != value:
                    errors.append(f"{where}: normalized metric {metric_key} differs from its raw source metric")
                if metric.get("family") in {"energy", "power"} and row.get("power_measurement_valid") is not True:
                    errors.append(f"{where}: power/energy metric {metric_key} lacks strict schema-v2 validation")
            has_raw_power = any(key in metrics for key in {
                "avg_power_w", "avg_total_gpu_power_w", "total_gpu_energy_j",
                "p75_power_w", "p75_total_gpu_power_w", "p90_power_w", "p90_total_gpu_power_w",
                "joules_per_successful_query", "joules_per_output_token", "joules_per_total_token",
                "prefill_avg_power_w", "decode_avg_power_w", "joules_per_input_token",
                "prefill_joules_per_input_token", "decode_joules_per_output_token",
                "avg_cpu_socket_power_w", "avg_total_cpu_power_w", "total_cpu_energy_j",
                "avg_total_module_power_w", "total_module_energy_j",
                "avg_total_cpu_rail_power_w", "total_cpu_rail_energy_j",
                "avg_total_cpu_sysio_power_w", "total_cpu_sysio_energy_j",
            })
            if row.get("power_measurement_valid") is True and (
                metrics.get("power_valid") != 1 or metrics.get("power_metric_schema_version") != 2
            ):
                errors.append(f"{where}: power_measurement_valid requires power_valid=1 and schema_version=2")
            if row.get("power_metrics_available") is not has_raw_power:
                errors.append(f"{where}: power_metrics_available must reflect present raw power/energy fields")
            if row.get("power_metrics_available") is True and row.get("power_measurement_valid") is not True:
                errors.append(f"{where}: strict power record must pass schema-v2 validation")

    for sid, source in source_map.items():
        if source.get("record_count") != counts.get(sid, 0):
            errors.append(f"source {sid}: record_count does not match registry rows")

    expected_summary = summarize(records)
    if db.get("summary") != expected_summary:
        errors.append("summary does not match records")

    return errors


def main():
    try:
        db = json.loads(RESULTS.read_text(encoding="utf-8"))
        compatibility = json.loads(COMPATIBILITY.read_text(encoding="utf-8"))
        profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"FAIL: cannot load benchmark registry dependencies: {error}", file=sys.stderr)
        return 2

    platform_ids = {item.get("id") for item in compatibility.get("platforms", [])}
    product_ids = {
        product.get("id")
        for company in profiles.get("companies", [])
        for product in company.get("products", [])
    }
    errors = validate_database(db, platform_ids, product_ids)
    if errors:
        print(f"FAIL: {len(errors)} benchmark registry issue(s)")
        print("\n".join("- " + error for error in errors))
        return 1
    sources = len(db.get("sources", []))
    print(f"PASS: {len(db.get('records', []))} benchmark result records across {sources} sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
