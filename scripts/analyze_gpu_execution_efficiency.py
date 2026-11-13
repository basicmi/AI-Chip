#!/usr/bin/env python3
"""Evidence-constrained GPU activity and compute/communication overlap analysis.

This module reports measured activity counters and timestamp overlap. It does
not infer GPU idle time, critical paths, or causal bottleneck verdicts.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import math
from typing import Any

from validate_benchmark_results import (
    _parse_runtime_trace_timestamp,
    validate_hardware_evidence,
    validate_runtime_trace,
)

ACTIVITY_METRICS = {
    "sm_active_pct",
    "tensor_active_pct",
    "dram_active_pct",
    "sm_throughput_pct",
    "valu_active_pct",
    "mfma_active_pct",
    "vmem_active_pct",
    "compute_peak_utilization_pct",
    "dram_bandwidth_utilization_pct",
    "gpu_clock_hz",
    "memory_clock_hz",
    "gpu_power_w",
    "temperature_c",
    "throttle_active_pct",
}
KERNEL_METRICS = {
    "sm_throughput_pct",
    "valu_active_pct",
    "mfma_active_pct",
    "vmem_active_pct",
    "compute_peak_utilization_pct",
}
TRACE_PHASES = {
    "prefill", "decode", "kernel", "communication", "communication_wait",
    "queue_wait", "batch_wait", "host_runtime", "cpu_scheduling", "other",
}


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _metric_window(metric: dict, evidence: dict):
    window = metric.get("sampling_window") or evidence.get("sampling")
    if not isinstance(window, dict):
        return None
    start, end = _parse_utc(window.get("started_at")), _parse_utc(window.get("ended_at"))
    if start is None or end is None or end <= start:
        return None
    return start, end


def _seconds(interval) -> float:
    return max(0.0, (interval[1] - interval[0]).total_seconds())


def _union(intervals):
    ordered = sorted((start, end) for start, end in intervals if end > start)
    if not ordered:
        return []
    result = []
    start, end = ordered[0]
    for next_start, next_end in ordered[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            result.append((start, end))
            start, end = next_start, next_end
    result.append((start, end))
    return result


def _union_seconds(intervals) -> float:
    return sum(_seconds(item) for item in _union(intervals))


def _intersection(left, right):
    intersections = []
    for left_start, left_end in _union(left):
        for right_start, right_end in _union(right):
            start, end = max(left_start, right_start), min(left_end, right_end)
            if end > start:
                intersections.append((start, end))
    return _union(intersections)


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * p
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] * (1 - (position - lower)) + ordered[upper] * (position - lower)


def _distribution(values: list[float]) -> dict:
    return {
        "sample_count": len(values),
        "mean": round(sum(values) / len(values), 6) if values else None,
        "p50": round(_percentile(values, 0.5), 6) if values else None,
        "p95": round(_percentile(values, 0.95), 6) if values else None,
    }


def _resolve_correlation(event_id: str, event_map: dict, cache: dict, visiting=None):
    if event_id in cache:
        return cache[event_id]
    if visiting is None:
        visiting = set()
    if event_id in visiting:
        return None
    visiting.add(event_id)
    event = event_map[event_id]
    direct = event.get("correlation_id")
    if direct:
        result = direct
    else:
        parent_id = event.get("parent_event_id")
        result = (
            _resolve_correlation(parent_id, event_map, cache, visiting)
            if parent_id in event_map else None
        )
    cache[event_id] = result
    visiting.remove(event_id)
    return result


def _trace_interval(event: dict, trace: dict):
    start = _parse_runtime_trace_timestamp(
        event.get("started_at"), trace.get("clock_domain"), trace.get("clock_mapping")
    )
    end = _parse_runtime_trace_timestamp(
        event.get("ended_at"), trace.get("clock_domain"), trace.get("clock_mapping")
    )
    if start is None or end is None or end <= start:
        return None
    return start, end


def _request_overlap(record: dict) -> dict:
    trace = record.get("runtime_trace")
    if trace is None:
        return {
            "status": "missing_runtime_trace",
            "request_count": 0,
            "requests": [],
            "communication_overlap_pct": _distribution([]),
            "kernel_prefill_coverage_pct": _distribution([]),
            "kernel_decode_coverage_pct": _distribution([]),
            "communication_wait_decode_pct": _distribution([]),
        }
    errors = validate_runtime_trace(trace, "record")
    if errors:
        raise ValueError("; ".join(errors))

    events = trace["events"]
    event_map = {event["event_id"]: event for event in events}
    cache = {}
    resolved = {
        event["event_id"]: _resolve_correlation(event["event_id"], event_map, cache)
        for event in events
    }
    roots = [
        event for event in events
        if event.get("category") == "request" and event.get("correlation_id")
    ]
    roots_by_id = defaultdict(list)
    for root in roots:
        roots_by_id[root["correlation_id"]].append(root)
    duplicates = sorted(key for key, values in roots_by_id.items() if len(values) > 1)
    if duplicates:
        return {
            "status": "ambiguous_request_roots",
            "request_count": 0,
            "requests": [],
            "communication_overlap_pct": _distribution([]),
            "kernel_prefill_coverage_pct": _distribution([]),
            "kernel_decode_coverage_pct": _distribution([]),
            "communication_wait_decode_pct": _distribution([]),
            "warnings": ["Duplicate request-root correlation IDs: " + ", ".join(duplicates)],
        }

    requests = []
    overlap_values, prefill_values, decode_values, wait_values = [], [], [], []
    for root in roots:
        request_window = _trace_interval(root, trace)
        if request_window is None:
            continue
        request_id = root["correlation_id"]
        child_events = []
        for event in events:
            if event["event_id"] == root["event_id"] or resolved[event["event_id"]] != request_id:
                continue
            interval = _trace_interval(event, trace)
            if interval and interval[0] >= request_window[0] and interval[1] <= request_window[1]:
                child_events.append((event, interval))

        def intervals_for(category):
            return [interval for event, interval in child_events if event.get("category") == category]

        kernel = _union(intervals_for("kernel"))
        communication = _union(intervals_for("communication"))
        communication_wait = _union(intervals_for("communication_wait"))
        prefill = _union(intervals_for("prefill"))
        decode = _union(intervals_for("decode"))

        communication_ms = _union_seconds(communication) * 1000
        overlap_ms = _union_seconds(_intersection(kernel, communication)) * 1000
        prefill_ms = _union_seconds(prefill) * 1000
        decode_ms = _union_seconds(decode) * 1000
        kernel_prefill_ms = _union_seconds(_intersection(kernel, prefill)) * 1000
        kernel_decode_ms = _union_seconds(_intersection(kernel, decode)) * 1000
        wait_ms = _union_seconds(communication_wait) * 1000
        wait_decode_ms = _union_seconds(_intersection(communication_wait, decode)) * 1000

        overlap_pct = overlap_ms / communication_ms * 100 if communication_ms else None
        prefill_pct = kernel_prefill_ms / prefill_ms * 100 if prefill_ms else None
        decode_pct = kernel_decode_ms / decode_ms * 100 if decode_ms else None
        wait_pct = wait_decode_ms / decode_ms * 100 if decode_ms else None
        if overlap_pct is not None:
            overlap_values.append(overlap_pct)
        if prefill_pct is not None:
            prefill_values.append(prefill_pct)
        if decode_pct is not None:
            decode_values.append(decode_pct)
        if wait_pct is not None:
            wait_values.append(wait_pct)

        requests.append({
            "correlation_id": request_id,
            "request_duration_ms": round(_seconds(request_window) * 1000, 6),
            "kernel_union_ms": round(_union_seconds(kernel) * 1000, 6),
            "communication_union_ms": round(communication_ms, 6),
            "kernel_communication_overlap_ms": round(overlap_ms, 6),
            "communication_overlap_pct": round(overlap_pct, 6) if overlap_pct is not None else None,
            "prefill_union_ms": round(prefill_ms * 1000, 6),
            "kernel_prefill_coverage_pct": round(prefill_pct, 6) if prefill_pct is not None else None,
            "decode_union_ms": round(decode_ms * 1000, 6),
            "kernel_decode_coverage_pct": round(decode_pct, 6) if decode_pct is not None else None,
            "communication_wait_union_ms": round(wait_ms, 6),
            "communication_wait_decode_pct": round(wait_pct, 6) if wait_pct is not None else None,
        })

    return {
        "status": "available" if requests else "no_request_events",
        "request_count": len(requests),
        "requests": requests,
        "communication_overlap_pct": _distribution(overlap_values),
        "kernel_prefill_coverage_pct": _distribution(prefill_values),
        "kernel_decode_coverage_pct": _distribution(decode_values),
        "communication_wait_decode_pct": _distribution(wait_values),
        "interpretation": (
            "Interval overlap is a same-request, same-clock-domain temporal observation. It does not prove "
            "device-side concurrency, communication hiding, synchronization completion, or critical-path impact."
        ),
    }


def _hardware_activity(evidence: dict, trace: dict | None) -> dict:
    metrics = evidence.get("metrics", [])
    grouped = defaultdict(list)
    for metric in metrics:
        if metric.get("metric_id") not in ACTIVITY_METRICS:
            continue
        window = _metric_window(metric, evidence)
        if window is None:
            continue
        key = (
            metric.get("scope"),
            metric.get("entity_id"),
            window[0].isoformat(),
            window[1].isoformat(),
        )
        grouped[key].append(metric)

    groups = []
    for (scope, entity_id, start, end), observations in sorted(grouped.items(), key=lambda item: str(item[0])):
        values = {}
        for item in observations:
            values.setdefault(item["metric_id"], []).append({
                "value": item["value"],
                "unit": item["unit"],
                "aggregation": item["aggregation"],
                "measurement_kind": item["measurement_kind"],
                "source_name": item["source_name"],
                "precision": item.get("precision"),
                "sparsity": item.get("sparsity"),
            })
        first_values = {
            metric_id: samples[0]["value"]
            for metric_id, samples in values.items() if len(samples) == 1
        }
        contrasts = {}
        if "sm_active_pct" in first_values:
            contrasts["sm_inactive_cycle_complement_pct"] = round(100 - first_values["sm_active_pct"], 6)
        if {"sm_active_pct", "sm_throughput_pct"} <= first_values.keys():
            contrasts["sm_active_minus_throughput_pp"] = round(
                first_values["sm_active_pct"] - first_values["sm_throughput_pct"], 6
            )
        if {"dram_active_pct", "dram_bandwidth_utilization_pct"} <= first_values.keys():
            contrasts["dram_active_minus_bandwidth_utilization_pp"] = round(
                first_values["dram_active_pct"] - first_values["dram_bandwidth_utilization_pct"], 6
            )
        if {"tensor_active_pct", "sm_active_pct"} <= first_values.keys():
            contrasts["tensor_active_minus_sm_active_pp"] = round(
                first_values["tensor_active_pct"] - first_values["sm_active_pct"], 6
            )
        groups.append({
            "scope": scope,
            "entity_id": entity_id,
            "sampling_window": {"started_at": start, "ended_at": end},
            "metrics": values,
            "descriptive_contrasts": contrasts,
        })

    joins = []
    join_warnings = []
    if trace is not None:
        trace_errors = validate_runtime_trace(trace, "record")
        if trace_errors:
            raise ValueError("; ".join(trace_errors))
        events = trace["events"]
        mapping_error = (
            timedelta(microseconds=trace.get("clock_mapping", {}).get("max_error_ns", 0) / 1000)
            if trace.get("clock_domain") == "monotonic_ns" else timedelta(0)
        )
        for metric in metrics:
            if metric.get("scope") not in {"per_gpu", "per_kernel", "per_link", "per_process"}:
                continue
            metric_window = metric.get("sampling_window")
            entity_id = metric.get("entity_id")
            if not isinstance(metric_window, dict) or not entity_id:
                continue
            start, end = _parse_utc(metric_window.get("started_at")), _parse_utc(metric_window.get("ended_at"))
            if start is None or end is None or end <= start:
                continue
            containing = []
            for event in events:
                interval = _trace_interval(event, trace)
                if interval is None:
                    continue
                if interval[0] + mapping_error <= start and interval[1] - mapping_error >= end:
                    containing.append(event)
            containing_ids = {event["event_id"] for event in containing}
            parents = {
                event.get("parent_event_id") for event in containing
                if event.get("parent_event_id") in containing_ids
            }
            leaves = [event for event in containing if event["event_id"] not in parents]
            if len(leaves) != 1:
                continue
            event = leaves[0]
            if event.get("entity_id") != entity_id:
                continue
            expected = {"per_kernel": "kernel", "per_link": "communication"}
            if metric["scope"] in expected and event.get("category") != expected[metric["scope"]]:
                continue
            if metric["scope"] == "per_gpu" and event.get("category") not in TRACE_PHASES:
                continue
            joins.append({
                "metric_id": metric["metric_id"],
                "scope": metric["scope"],
                "entity_id": entity_id,
                "event_id": event["event_id"],
                "event_name": event["name"],
                "event_category": event["category"],
                "sampling_window": metric_window,
                "join_rule": "metric-specific window fully contained by one leaf event; exact entity match",
            })
        if not joins:
            join_warnings.append(
                "No metric-specific hardware sampling window uniquely joined to a containing trace event with exact entity identity."
            )

    return {
        "status": "available" if groups else "insufficient_evidence",
        "activity_groups": groups,
        "metric_to_runtime_joins": joins,
        "missing_inputs": [] if groups else [
            "SM/tensor/DRAM activity or throughput counters with explicit scope, entity and sampling window"
        ],
        "join_warnings": join_warnings,
        "interpretation": [
            "SM inactive-cycle complement is 100% minus the measured SM-active ratio; it is not a whole-GPU idle-time estimate.",
            "SM active-cycle ratio and SM throughput are different metrics. A difference is descriptive only, not an occupancy or instruction-issue diagnosis.",
            "DRAM interface activity is not achieved bandwidth. Compare it with bandwidth utilization only when scope, entity and sampling window match exactly.",
            "Kernel duration is not GPU-active time. Kernel-scoped throughput counters require a matching kernel event and exact entity/window alignment.",
            "Clock, power and throttle telemetry are contextual signals; they do not independently establish a thermal or power bottleneck.",
        ],
    }


def analyze_gpu_execution_efficiency(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    evidence = record.get("hardware_evidence")
    if evidence is None:
        activity = {
            "status": "insufficient_evidence",
            "activity_groups": [],
            "metric_to_runtime_joins": [],
            "missing_inputs": ["hardware_evidence bundle"],
            "interpretation": [
                "Missing evidence is unknown, never zero.",
                "No GPU idle, compute efficiency, bandwidth saturation or communication bottleneck is inferred.",
            ],
        }
    else:
        errors = validate_hardware_evidence({"hardware_evidence": evidence}, "record")
        if errors:
            raise ValueError("; ".join(errors))
        activity = _hardware_activity(evidence, record.get("runtime_trace"))
    overlap = _request_overlap(record)
    has_activity = activity["status"] == "available"
    has_overlap = overlap.get("status") == "available"
    return {
        "record_id": record.get("id"),
        "status": "evidence_available" if has_activity or has_overlap else "insufficient_evidence",
        "hardware_activity": activity,
        "runtime_overlap": overlap,
        "overall_verdict": "undetermined",
        "limitations": [
            "No fixed utilization threshold or numeric confidence score is used.",
            "Temporal overlap does not prove device-side concurrency, causal latency impact or critical-path membership.",
            "Profiler kernel time, SM activity, SM throughput, DRAM activity and DRAM bandwidth utilization have distinct semantics.",
            "A whole-GPU idle estimate requires a validated device-level definition and sampling methodology; SM inactive-cycle complement is not substituted for it.",
            "A phase-level counter join requires an explicit metric sampling window, mapped trace clock, one containing leaf event and exact entity identity.",
        ],
    }
