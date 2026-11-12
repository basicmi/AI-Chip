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



HARDWARE_EVIDENCE_UNITS = {
    "sm_active_pct": "%", "tensor_active_pct": "%",
    "achieved_flops": "FLOP/s", "theoretical_peak_flops": "FLOP/s",
    "dram_read_bytes": "byte", "dram_write_bytes": "byte",
    "dram_bandwidth_bytes_per_s": "byte/s", "dram_peak_bandwidth_bytes_per_s": "byte/s",
    "hbm_used_bytes": "byte", "hbm_capacity_bytes": "byte",
    "kv_cache_used_bytes": "byte", "kv_cache_capacity_bytes": "byte",
    "kv_cache_tokens": "token", "kv_cache_token_capacity": "token",
    "kv_cache_hit_rate_pct": "%",
    "nvlink_tx_bytes": "byte", "nvlink_rx_bytes": "byte",
    "pcie_tx_bytes": "byte", "pcie_rx_bytes": "byte",
    "network_tx_bytes": "byte", "network_rx_bytes": "byte",
    "link_bandwidth_bytes_per_s": "byte/s", "link_peak_bandwidth_bytes_per_s": "byte/s",
    "link_utilization_pct": "%",
    "gpu_power_w": "W", "gpu_clock_hz": "Hz", "memory_clock_hz": "Hz",
    "temperature_c": "°C", "throttle_active_pct": "%",
}
HARDWARE_EVIDENCE_SCOPES = {"per_gpu", "per_link", "per_node", "per_system", "per_process"}
HARDWARE_EVIDENCE_AGGREGATIONS = {
    "instantaneous", "mean", "max", "min", "p50", "p95", "p99", "sum", "rate"
}
HARDWARE_EVIDENCE_COLLECTOR_TYPES = {
    "profiler", "device_telemetry", "runtime_telemetry",
    "network_telemetry", "publisher_export", "other"
}
HARDWARE_EVIDENCE_SOURCE_TYPES = {
    "publisher_api", "profiler_export", "telemetry_export",
    "independent_measurement", "vendor_report", "other"
}
HARDWARE_EVIDENCE_LINK_TYPES = {"nvlink", "pcie", "infiniband", "roce", "ethernet", "other"}


def _parse_iso_datetime(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def validate_hardware_evidence(row, where):
    """Validate optional, provenance-backed low-level hardware measurements."""
    errors = []
    evidence = row.get("hardware_evidence")
    if evidence is None:
        return errors
    if not isinstance(evidence, dict):
        return [f"{where}: hardware_evidence must be an object or null"]

    if evidence.get("schema_version") != "1.0":
        errors.append(f"{where}: hardware_evidence.schema_version must be 1.0")

    collector = evidence.get("collector")
    if not isinstance(collector, dict):
        errors.append(f"{where}: hardware_evidence.collector must be an object")
    else:
        if not isinstance(collector.get("name"), str) or not collector["name"].strip():
            errors.append(f"{where}: hardware_evidence.collector.name must be non-empty")
        if not isinstance(collector.get("type"), str) or collector.get("type") not in HARDWARE_EVIDENCE_COLLECTOR_TYPES:
            errors.append(f"{where}: hardware_evidence.collector.type is invalid")
        version = collector.get("version")
        if version is not None and not isinstance(version, str):
            errors.append(f"{where}: hardware_evidence.collector.version must be a string or null")

    system_scope = evidence.get("system_scope")
    if not isinstance(system_scope, dict):
        errors.append(f"{where}: hardware_evidence.system_scope must be an object")
    else:
        if not isinstance(system_scope.get("scope_type"), str) or system_scope.get("scope_type") not in HARDWARE_EVIDENCE_SCOPES:
            errors.append(f"{where}: hardware_evidence.system_scope.scope_type is invalid")
        count = system_scope.get("device_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            errors.append(f"{where}: hardware_evidence.system_scope.device_count must be a positive integer")
        for field in ("device_model", "topology"):
            if system_scope.get(field) is not None and not isinstance(system_scope[field], str):
                errors.append(f"{where}: hardware_evidence.system_scope.{field} must be a string")

    sampling = evidence.get("sampling")
    if not isinstance(sampling, dict):
        errors.append(f"{where}: hardware_evidence.sampling must be an object")
    else:
        start = _parse_iso_datetime(sampling.get("started_at"))
        end = _parse_iso_datetime(sampling.get("ended_at"))
        if start is None or end is None:
            errors.append(f"{where}: hardware_evidence sampling timestamps must be ISO date-times")
        elif start.utcoffset() is None or end.utcoffset() is None or end <= start:
            errors.append(f"{where}: hardware_evidence sampling window must be positive and timezone-aware")
        interval = sampling.get("sample_interval_ms")
        if isinstance(interval, bool) or not isinstance(interval, (int, float)) or not math.isfinite(interval) or interval <= 0:
            errors.append(f"{where}: hardware_evidence.sample_interval_ms must be a positive finite number")
        count = sampling.get("sample_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            errors.append(f"{where}: hardware_evidence.sample_count must be a positive integer")

    provenance = evidence.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{where}: hardware_evidence.provenance must be an object")
    else:
        if not isinstance(provenance.get("source_type"), str) or provenance.get("source_type") not in HARDWARE_EVIDENCE_SOURCE_TYPES:
            errors.append(f"{where}: hardware_evidence.provenance.source_type is invalid")
        if not is_http_url(provenance.get("source_url")) or not provenance.get("source_url"):
            errors.append(f"{where}: hardware_evidence.provenance.source_url must be an HTTP(S) URL")
        if _parse_iso_datetime(provenance.get("collected_at")) is None:
            errors.append(f"{where}: hardware_evidence.provenance.collected_at must be an ISO date-time")
        digest = provenance.get("artifact_sha256")
        if digest is not None and (not isinstance(digest, str) or len(digest) != 64 or
                                   any(char not in "0123456789abcdefABCDEF" for char in digest)):
            errors.append(f"{where}: hardware_evidence.provenance.artifact_sha256 must be a SHA-256 hex digest")

    metrics = evidence.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        errors.append(f"{where}: hardware_evidence.metrics must be a non-empty array")
        return errors

    seen = set()
    metric_ids = set()
    for index, metric in enumerate(metrics):
        item_where = f"{where}.hardware_evidence.metrics[{index}]"
        if not isinstance(metric, dict):
            errors.append(f"{item_where}: must be an object")
            continue
        metric_id = metric.get("metric_id")
        if not isinstance(metric_id, str) or metric_id not in HARDWARE_EVIDENCE_UNITS:
            errors.append(f"{item_where}: unknown metric_id {metric_id}")
            continue
        metric_ids.add(metric_id)
        unit = metric.get("unit")
        if unit != HARDWARE_EVIDENCE_UNITS[metric_id]:
            errors.append(f"{item_where}: {metric_id} unit must be {HARDWARE_EVIDENCE_UNITS[metric_id]}")
        value = metric.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            errors.append(f"{item_where}: value must be a non-negative finite number")
        if metric_id.endswith("_pct") and isinstance(value, (int, float)) and not isinstance(value, bool) and not 0 <= value <= 100:
            errors.append(f"{item_where}: percentage value must be between 0 and 100")
        if metric_id in {"achieved_flops", "theoretical_peak_flops"}:
            precision = metric.get("precision")
            sparsity = metric.get("sparsity")
            if not isinstance(precision, str) or not precision.strip():
                errors.append(f"{item_where}: compute FLOP metrics require precision")
            if sparsity not in {"dense", "structured_sparse", "unstructured_sparse", "unknown"}:
                errors.append(f"{item_where}: compute FLOP metrics require an explicit sparsity mode")
        kind = metric.get("measurement_kind")
        aggregation = metric.get("aggregation")
        scope = metric.get("scope")
        if not isinstance(kind, str) or kind not in {"hardware_counter", "telemetry", "derived"}:
            errors.append(f"{item_where}: measurement_kind is invalid")
        if not isinstance(aggregation, str) or aggregation not in HARDWARE_EVIDENCE_AGGREGATIONS:
            errors.append(f"{item_where}: aggregation is invalid")
        if not isinstance(scope, str) or scope not in HARDWARE_EVIDENCE_SCOPES:
            errors.append(f"{item_where}: scope is invalid")
        if not isinstance(metric.get("source_name"), str) or not metric["source_name"].strip():
            errors.append(f"{item_where}: source_name must be non-empty")
        key = (metric_id, scope if isinstance(scope, str) else repr(scope),
               aggregation if isinstance(aggregation, str) else repr(aggregation))
        if key in seen:
            errors.append(f"{item_where}: duplicate metric_id/scope/aggregation tuple {key}")
        seen.add(key)

        link_type = metric.get("link_type")
        if metric_id.startswith("network_") or metric_id.startswith("link_"):
            if not isinstance(link_type, str) or link_type not in HARDWARE_EVIDENCE_LINK_TYPES:
                errors.append(f"{item_where}: {metric_id} requires a valid link_type")
        elif link_type is not None and (not isinstance(link_type, str) or link_type not in HARDWARE_EVIDENCE_LINK_TYPES):
            errors.append(f"{item_where}: link_type is invalid")

        kind = metric.get("measurement_kind")
        formula = metric.get("formula")
        inputs = metric.get("input_metric_ids")
        if kind == "derived":
            if not isinstance(formula, str) or not formula.strip():
                errors.append(f"{item_where}: derived metric requires a formula")
            if not isinstance(inputs, list) or not inputs or any(
                not isinstance(item, str) or item not in HARDWARE_EVIDENCE_UNITS for item in inputs
            ):
                errors.append(f"{item_where}: derived metric requires valid input_metric_ids")
        elif formula is not None or inputs is not None:
            errors.append(f"{item_where}: raw counter/telemetry metric cannot declare a derived formula")

    for index, metric in enumerate(metrics):
        if not isinstance(metric, dict) or metric.get("measurement_kind") != "derived":
            continue
        inputs = metric.get("input_metric_ids")
        if not isinstance(inputs, list):
            continue
        for input_id in inputs:
            if isinstance(input_id, str) and input_id not in metric_ids:
                errors.append(f"{where}.hardware_evidence.metrics[{index}]: derived input {input_id} is absent from this evidence block")

    return errors


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

        errors.extend(validate_hardware_evidence(row, where))

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
            if row.get("power_measurement_status") not in {"valid", "failed", "schema_incomplete", "unreported", "invalid_verdict"}:
                errors.append(f"{where}: invalid power_measurement_status")
            if not isinstance(row.get("cpu_power_measurement_valid"), bool):
                errors.append(f"{where}: cpu_power_measurement_valid must be boolean")
            if row.get("cpu_power_measurement_status") not in {"valid", "failed", "not_present", "invalid_verdict"}:
                errors.append(f"{where}: invalid cpu_power_measurement_status")
            if not isinstance(row.get("gpu_power_metrics_available"), bool):
                errors.append(f"{where}: gpu_power_metrics_available must be boolean")
            if not isinstance(row.get("cpu_power_metrics_available"), bool):
                errors.append(f"{where}: cpu_power_metrics_available must be boolean")
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
                if metric.get("family") not in {"interactivity", "throughput", "latency", "energy", "power", "cpu_energy", "cpu_power", "telemetry"}:
                    errors.append(f"{where}: normalized metric {metric_key} has an invalid family")
                source_metric = metric.get("source_metric")
                if source_metric not in metrics:
                    errors.append(f"{where}: normalized metric {metric_key} references a missing raw metric")
                elif isinstance(value, (int, float)) and not isinstance(value, bool) and metrics[source_metric] != value:
                    errors.append(f"{where}: normalized metric {metric_key} differs from its raw source metric")
                if metric.get("family") in {"energy", "power"} and row.get("power_measurement_valid") is not True:
                    errors.append(f"{where}: GPU power/energy metric {metric_key} lacks strict schema-v2 validation")
                if metric.get("family") in {"cpu_energy", "cpu_power"} and row.get("cpu_power_measurement_valid") is not True:
                    errors.append(f"{where}: CPU/module power metric {metric_key} lacks cpu_power_valid=1")
            gpu_power_keys = {
                "avg_power_w", "avg_total_gpu_power_w", "total_gpu_energy_j",
                "p75_power_w", "p75_total_gpu_power_w", "p90_power_w", "p90_total_gpu_power_w",
                "joules_per_successful_query", "joules_per_output_token", "joules_per_total_token",
                "prefill_avg_power_w", "decode_avg_power_w", "joules_per_input_token",
                "prefill_joules_per_input_token", "decode_joules_per_output_token",
            }
            cpu_power_keys = {
                "avg_cpu_socket_power_w", "avg_total_cpu_power_w", "total_cpu_energy_j",
                "avg_total_module_power_w", "total_module_energy_j",
                "avg_total_cpu_rail_power_w", "total_cpu_rail_energy_j",
                "avg_total_cpu_sysio_power_w", "total_cpu_sysio_energy_j",
            }
            has_gpu_power = row.get("power_measurement_valid") is True and any(key in metrics for key in gpu_power_keys)
            has_cpu_power = row.get("cpu_power_measurement_valid") is True and any(key in metrics for key in cpu_power_keys)
            power_flag = metrics.get("power_valid")
            power_schema = metrics.get("power_metric_schema_version")
            if isinstance(power_flag, (int, float)) and not isinstance(power_flag, bool):
                if power_flag == 0:
                    expected_power_status = "failed"
                elif power_flag == 1 and power_schema == 2:
                    expected_power_status = "valid"
                elif power_flag == 1:
                    expected_power_status = "schema_incomplete"
                else:
                    expected_power_status = "invalid_verdict"
            else:
                expected_power_status = "unreported"
            if row.get("power_measurement_status") != expected_power_status:
                errors.append(f"{where}: power_measurement_status does not match the source verdict")
            if row.get("power_measurement_valid") is not (expected_power_status == "valid"):
                errors.append(f"{where}: power_measurement_valid does not match the source verdict")

            cpu_power_flag = metrics.get("cpu_power_valid")
            if isinstance(cpu_power_flag, (int, float)) and not isinstance(cpu_power_flag, bool):
                expected_cpu_status = "valid" if cpu_power_flag == 1 else "failed" if cpu_power_flag == 0 else "invalid_verdict"
            else:
                expected_cpu_status = "not_present"
            if row.get("cpu_power_measurement_status") != expected_cpu_status:
                errors.append(f"{where}: cpu_power_measurement_status does not match the source verdict")
            if row.get("cpu_power_measurement_valid") is not (expected_cpu_status == "valid"):
                errors.append(f"{where}: cpu_power_measurement_valid does not match the source verdict")
            if row.get("gpu_power_metrics_available") is not has_gpu_power:
                errors.append(f"{where}: gpu_power_metrics_available must reflect valid GPU power/energy fields")
            if row.get("cpu_power_metrics_available") is not has_cpu_power:
                errors.append(f"{where}: cpu_power_metrics_available must reflect valid CPU/module power/energy fields")
            if row.get("power_metrics_available") is not (has_gpu_power or has_cpu_power):
                errors.append(f"{where}: power_metrics_available must reflect validated GPU or CPU/module power data")
            if row.get("power_metrics_available") is True and not (row.get("power_measurement_valid") or row.get("cpu_power_measurement_valid")):
                errors.append(f"{where}: strict power record must pass the applicable GPU or CPU validation")

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
