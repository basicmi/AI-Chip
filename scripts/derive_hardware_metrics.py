#!/usr/bin/env python3
"""Derive unit-safe hardware rates and occupancy from a validated evidence bundle.

This script derives metrics only. It deliberately does not label a workload
compute-bound, memory-bound, communication-bound, or otherwise bottlenecked.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_benchmark_results import validate_hardware_evidence

DERIVER = "scripts/derive_hardware_metrics.py"


def _datetime(value):
    if not isinstance(value, str):
        raise ValueError("sampling timestamps must be ISO date-times")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("sampling timestamps must include a timezone")
    return parsed


def _window_seconds(evidence):
    sampling = evidence.get("sampling", {})
    start = _datetime(sampling.get("started_at"))
    end = _datetime(sampling.get("ended_at"))
    seconds = (end - start).total_seconds()
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("sampling window must have positive duration")
    return seconds


def _group(metric):
    return metric.get("scope"), metric.get("entity_id")


def _find(metrics, metric_id, group=None):
    return [
        metric for metric in metrics
        if metric.get("metric_id") == metric_id and (group is None or _group(metric) == group)
    ]


def _exists(metrics, metric_id, group, aggregation):
    return any(
        metric.get("metric_id") == metric_id and _group(metric) == group
        and metric.get("aggregation") == aggregation
        for metric in metrics
    )


def _derived(metric_id, value, unit, aggregation, scope, inputs, formula, *,
             entity_id=None, precision=None, sparsity=None, link_type=None):
    metric = {
        "metric_id": metric_id,
        "value": value,
        "unit": unit,
        "measurement_kind": "derived",
        "aggregation": aggregation,
        "scope": scope,
        "source_name": DERIVER,
        "formula": formula,
        "input_metric_ids": list(dict.fromkeys(inputs)),
    }
    if entity_id:
        metric["entity_id"] = entity_id
    if precision:
        metric["precision"] = precision
    if sparsity:
        metric["sparsity"] = sparsity
    if link_type:
        metric["link_type"] = link_type
    return metric


def derive_metrics(evidence):
    """Return a copied evidence bundle, added metrics, and explicit skip warnings."""
    if not isinstance(evidence, dict) or not isinstance(evidence.get("metrics"), list):
        raise ValueError("evidence must be an object containing a metrics array")
    result = copy.deepcopy(evidence)
    metrics = result["metrics"]
    seconds = _window_seconds(result)
    added, warnings = [], []

    def append(metric):
        if not _exists(metrics, metric["metric_id"], _group(metric), metric["aggregation"]):
            metrics.append(metric)
            added.append(metric)

    groups = sorted({_group(metric) for metric in metrics if isinstance(metric, dict)}, key=str)

    # FLOP count is a total over the exact evidence window, not an instantaneous rate.
    for group in groups:
        counts = _find(metrics, "compute_flop_count", group)
        for count in counts:
            if count.get("aggregation") != "sum":
                warnings.append("compute_flop_count skipped: input aggregation must be sum")
                continue
            precision, sparsity = count.get("precision"), count.get("sparsity")
            if not precision or not sparsity:
                warnings.append("compute_flop_count skipped: precision and sparsity are required")
                continue
            rate = count["value"] / seconds
            append(_derived(
                "achieved_flops", rate, "FLOP/s", "rate", group[0],
                ["compute_flop_count"], "compute_flop_count / sampling_window_seconds",
                entity_id=group[1], precision=precision, sparsity=sparsity,
            ))

    # Compute peak utilization is comparable only when precision, sparsity and scope match.
    for group in groups:
        achieved = _find(metrics, "achieved_flops", group)
        peaks = _find(metrics, "theoretical_peak_flops", group)
        for actual in achieved:
            for peak in peaks:
                if (actual.get("precision"), actual.get("sparsity")) != (
                    peak.get("precision"), peak.get("sparsity")
                ):
                    continue
                if peak.get("value", 0) <= 0:
                    warnings.append("compute_peak_utilization_pct skipped: peak FLOP/s must be positive")
                    continue
                value = actual["value"] / peak["value"] * 100
                if not 0 <= value <= 100:
                    warnings.append("compute_peak_utilization_pct skipped: ratio is outside [0, 100]; check peak definition and precision")
                    continue
                append(_derived(
                    "compute_peak_utilization_pct", value, "%", "mean", group[0],
                    ["achieved_flops", "theoretical_peak_flops"],
                    "achieved_flops / theoretical_peak_flops * 100",
                    entity_id=group[1], precision=actual.get("precision"),
                    sparsity=actual.get("sparsity"),
                ))

    # DRAM byte counters must both be interval totals over the same scope.
    for group in groups:
        reads, writes = _find(metrics, "dram_read_bytes", group), _find(metrics, "dram_write_bytes", group)
        for read in reads:
            for write in writes:
                if read.get("aggregation") != "sum" or write.get("aggregation") != "sum":
                    warnings.append("dram_bandwidth_bytes_per_s skipped: read/write byte inputs must use sum aggregation")
                    continue
                value = (read["value"] + write["value"]) / seconds
                append(_derived(
                    "dram_bandwidth_bytes_per_s", value, "byte/s", "rate", group[0],
                    ["dram_read_bytes", "dram_write_bytes"],
                    "(dram_read_bytes + dram_write_bytes) / sampling_window_seconds",
                    entity_id=group[1],
                ))

    # A bandwidth ratio is valid only for the same measurement boundary.
    for group in groups:
        bandwidths = _find(metrics, "dram_bandwidth_bytes_per_s", group)
        peaks = _find(metrics, "dram_peak_bandwidth_bytes_per_s", group)
        for bandwidth in bandwidths:
            for peak in peaks:
                if peak.get("value", 0) <= 0:
                    warnings.append("dram_bandwidth_utilization_pct skipped: peak bandwidth must be positive")
                    continue
                value = bandwidth["value"] / peak["value"] * 100
                if not 0 <= value <= 100:
                    warnings.append("dram_bandwidth_utilization_pct skipped: ratio is outside [0, 100]; check peak and aggregation semantics")
                    continue
                append(_derived(
                    "dram_bandwidth_utilization_pct", value, "%", "mean", group[0],
                    ["dram_bandwidth_bytes_per_s", "dram_peak_bandwidth_bytes_per_s"],
                    "dram_bandwidth_bytes_per_s / dram_peak_bandwidth_bytes_per_s * 100",
                    entity_id=group[1],
                ))

    # Prefer byte occupancy; use token occupancy only when byte occupancy is unavailable.
    for group in groups:
        pairs = [
            ("kv_cache_used_bytes", "kv_cache_capacity_bytes", "byte"),
            ("kv_cache_tokens", "kv_cache_token_capacity", "token"),
        ]
        for used_id, capacity_id, unit in pairs:
            if any(metric.get("metric_id") == "kv_cache_occupancy_pct" and _group(metric) == group
                   for metric in metrics):
                break
            used_values, capacities = _find(metrics, used_id, group), _find(metrics, capacity_id, group)
            derived_for_pair = False
            for used in used_values:
                for capacity in capacities:
                    if used.get("aggregation") != capacity.get("aggregation"):
                        continue
                    if capacity.get("value", 0) <= 0:
                        warnings.append("kv_cache_occupancy_pct skipped: capacity must be positive")
                        continue
                    value = used["value"] / capacity["value"] * 100
                    if not 0 <= value <= 100:
                        warnings.append("kv_cache_occupancy_pct skipped: occupancy is outside [0, 100]; check allocator/capacity semantics")
                        continue
                    append(_derived(
                        "kv_cache_occupancy_pct", value, "%", used["aggregation"], group[0],
                        [used_id, capacity_id], f"{used_id} / {capacity_id} * 100",
                        entity_id=group[1],
                    ))
                    derived_for_pair = True
                    break
                if derived_for_pair:
                    break
            if derived_for_pair:
                break

    # Directional byte totals can be combined only for the same link entity/fabric.
    link_pairs = [
        ("nvlink_tx_bytes", "nvlink_rx_bytes", "nvlink"),
        ("pcie_tx_bytes", "pcie_rx_bytes", "pcie"),
        ("network_tx_bytes", "network_rx_bytes", None),
    ]
    for group in groups:
        for tx_id, rx_id, fixed_link_type in link_pairs:
            for tx in _find(metrics, tx_id, group):
                for rx in _find(metrics, rx_id, group):
                    if tx.get("aggregation") != "sum" or rx.get("aggregation") != "sum":
                        warnings.append("link_bandwidth_bytes_per_s skipped: directional byte inputs must use sum aggregation")
                        continue
                    link_type = fixed_link_type or tx.get("link_type")
                    if not link_type or link_type != rx.get("link_type"):
                        continue
                    value = (tx["value"] + rx["value"]) / seconds
                    append(_derived(
                        "link_bandwidth_bytes_per_s", value, "byte/s", "rate", group[0],
                        [tx_id, rx_id],
                        f"({tx_id} + {rx_id}) / sampling_window_seconds",
                        entity_id=group[1], link_type=link_type,
                    ))

    # Link bandwidth and peak must refer to the same link entity and fabric.
    for group in groups:
        bandwidths = _find(metrics, "link_bandwidth_bytes_per_s", group)
        peaks = _find(metrics, "link_peak_bandwidth_bytes_per_s", group)
        for bandwidth in bandwidths:
            for peak in peaks:
                link_type = bandwidth.get("link_type")
                if not link_type or link_type != peak.get("link_type"):
                    continue
                if peak.get("value", 0) <= 0:
                    warnings.append("link_utilization_pct skipped: peak link bandwidth must be positive")
                    continue
                value = bandwidth["value"] / peak["value"] * 100
                if not 0 <= value <= 100:
                    warnings.append("link_utilization_pct skipped: ratio is outside [0, 100]; check direction and link capacity")
                    continue
                append(_derived(
                    "link_utilization_pct", value, "%", "mean", group[0],
                    ["link_bandwidth_bytes_per_s", "link_peak_bandwidth_bytes_per_s"],
                    "link_bandwidth_bytes_per_s / link_peak_bandwidth_bytes_per_s * 100",
                    entity_id=group[1], link_type=link_type,
                ))

    return result, added, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Hardware evidence object or benchmark record containing hardware_evidence")
    parser.add_argument("--output", required=True, type=Path, help="Destination JSON file; input is never overwritten")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        is_record = isinstance(payload, dict) and "hardware_evidence" in payload
        evidence = payload.get("hardware_evidence") if is_record else payload
        if evidence is None:
            raise ValueError("input does not contain hardware_evidence")
        errors = validate_hardware_evidence({"hardware_evidence": evidence}, "input")
        if errors:
            raise ValueError("; ".join(errors))
        derived, added, warnings = derive_metrics(evidence)
        errors = validate_hardware_evidence({"hardware_evidence": derived}, "output")
        if errors:
            raise ValueError("; ".join(errors))
        if is_record:
            payload["hardware_evidence"] = derived
            output = payload
        else:
            output = {"hardware_evidence": derived}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: added {len(added)} derived metrics; wrote {args.output}.")
    for warning in warnings:
        print(f"NOTE: {warning}")
    print("No bottleneck classification is produced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
