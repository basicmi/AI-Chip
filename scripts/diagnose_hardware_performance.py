#!/usr/bin/env python3
"""Evidence-constrained diagnosis for accelerator and inference-serving records.

The engine reports comparable ceilings, observed link traffic, serving signals,
and missing measurements. It never emits an automatic bottleneck verdict.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_benchmark_results import validate_hardware_evidence
from analyze_gpu_execution_efficiency import analyze_gpu_execution_efficiency

DERIVER = "scripts/diagnose_hardware_performance.py"
PEAK_AGGREGATIONS = {"max", "mean", "instantaneous"}
RATE_AGGREGATIONS = {"rate", "mean", "p50", "p95", "p99", "instantaneous"}

RUNTIME_METRICS = {
    "median_ttft": ("s", "lower", "latency"),
    "p99_ttft": ("s", "lower", "latency"),
    "median_tpot": ("s", "lower", "latency"),
    "p99_tpot": ("s", "lower", "latency"),
    "p99_itl": ("s", "lower", "latency"),
    "output_throughput_per_gpu": ("tok/s/GPU", "higher", "throughput"),
    "median_interactivity": ("tok/s/user", "higher", "interactivity"),
    "mean_gpu_utilization": ("%", "context", "telemetry"),
    "mean_gpu_memory_used": ("MB", "context", "telemetry"),
    "prefill_gpu_power_per_gpu": ("W/GPU", "context", "power"),
    "decode_gpu_power_per_gpu": ("W/GPU", "context", "power"),
    "prefill_energy_per_input_token": ("J/input token", "lower", "energy"),
    "decode_energy_per_output_token": ("J/output token", "lower", "energy"),
}


def _parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _window_seconds(evidence):
    sampling = evidence.get("sampling") if isinstance(evidence, dict) else None
    if not isinstance(sampling, dict):
        return None
    start, end = _parse_time(sampling.get("started_at")), _parse_time(sampling.get("ended_at"))
    if start is None or end is None:
        return None
    seconds = (end - start).total_seconds()
    return seconds if math.isfinite(seconds) and seconds > 0 else None


def _valid_number(value, positive=False):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and (value > 0 if positive else value >= 0)
    )


def _same_boundary(left, right):
    return (
        left.get("scope") == right.get("scope")
        and left.get("entity_id") == right.get("entity_id")
    )


def _metrics(evidence, metric_id):
    return [
        item for item in (evidence or {}).get("metrics", [])
        if isinstance(item, dict) and item.get("metric_id") == metric_id
    ]


def _matching(evidence, metric_id, reference, *, aggregations=None,
              precision=False, directionality=False):
    found = []
    for item in _metrics(evidence, metric_id):
        if not _same_boundary(item, reference):
            continue
        if aggregations is not None and item.get("aggregation") not in aggregations:
            continue
        if precision and (
            item.get("precision") != reference.get("precision")
            or item.get("sparsity") != reference.get("sparsity")
        ):
            continue
        if directionality and item.get("directionality") != reference.get("directionality"):
            continue
        if _valid_number(item.get("value")):
            found.append(item)
    return found


def _first(items, positive=False):
    return next((item for item in items if _valid_number(item.get("value"), positive=positive)), None)


def _empty_roofline(missing):
    return {
        "status": "insufficient_evidence",
        "analyses": [],
        "missing_inputs": list(dict.fromkeys(missing)),
        "interpretation": "No roofline position is inferred from aggregate throughput or utilization alone.",
    }


def analyze_roofline(evidence):
    """Compute per-boundary roofline geometry from exact, compatible measurements."""
    seconds = _window_seconds(evidence)
    counts = _metrics(evidence, "compute_flop_count")
    if not counts:
        return _empty_roofline(["compute_flop_count with sum aggregation"])

    analyses, global_missing = [], []
    for count in counts:
        if count.get("aggregation") != "sum" or not _valid_number(count.get("value"), positive=True):
            global_missing.append("compute_flop_count must be a positive interval sum")
            continue
        missing = []
        read = _first(_matching(evidence, "dram_read_bytes", count, aggregations={"sum"}))
        write = _first(_matching(evidence, "dram_write_bytes", count, aggregations={"sum"}))
        peak_compute = _first(_matching(
            evidence, "theoretical_peak_flops", count,
            aggregations=PEAK_AGGREGATIONS, precision=True,
        ), positive=True)
        peak_bandwidth = _first(_matching(
            evidence, "dram_peak_bandwidth_bytes_per_s", count,
            aggregations=PEAK_AGGREGATIONS,
        ), positive=True)

        if read is None:
            missing.append("dram_read_bytes (sum, same scope/entity)")
        if write is None:
            missing.append("dram_write_bytes (sum, same scope/entity)")
        if peak_compute is None:
            missing.append("theoretical_peak_flops (same precision, sparsity, scope/entity)")
        if peak_bandwidth is None:
            missing.append("dram_peak_bandwidth_bytes_per_s (same scope/entity)")
        if seconds is None:
            missing.append("positive timezone-aware sampling window")

        total_bytes = read["value"] + write["value"] if read and write else None
        arithmetic_intensity = (
            count["value"] / total_bytes
            if total_bytes is not None and total_bytes > 0 else None
        )
        if total_bytes == 0:
            missing.append("non-zero DRAM read+write bytes")
        achieved = count["value"] / seconds if seconds else None
        memory_bandwidth = total_bytes / seconds if total_bytes is not None and seconds else None
        memory_ceiling = (
            arithmetic_intensity * peak_bandwidth["value"]
            if arithmetic_intensity is not None and peak_bandwidth else None
        )
        compute_ceiling = peak_compute["value"] if peak_compute else None
        roofline_ceiling = (
            min(compute_ceiling, memory_ceiling)
            if compute_ceiling is not None and memory_ceiling is not None else None
        )
        ceiling_type = None
        attainment = None
        warnings = []
        if roofline_ceiling is not None:
            if math.isclose(compute_ceiling, memory_ceiling, rel_tol=1e-12, abs_tol=0.0):
                ceiling_type = "balanced"
            elif compute_ceiling < memory_ceiling:
                ceiling_type = "compute"
            else:
                ceiling_type = "memory"
            ratio = achieved / roofline_ceiling * 100
            if ratio <= 100:
                attainment = ratio
            else:
                warnings.append(
                    "achieved FLOP/s exceeds the calculated roofline ceiling; inspect peak definition, counter coverage and measurement boundaries"
                )

        row_status = "complete" if not missing and roofline_ceiling is not None else "partial"
        analyses.append({
            "scope": count.get("scope"),
            "entity_id": count.get("entity_id"),
            "precision": count.get("precision"),
            "sparsity": count.get("sparsity"),
            "sampling_window_seconds": seconds,
            "compute_flop_count": count["value"],
            "dram_read_bytes": read["value"] if read else None,
            "dram_write_bytes": write["value"] if write else None,
            "arithmetic_intensity_flop_per_byte": arithmetic_intensity,
            "achieved_flops_per_second": achieved,
            "measured_dram_bandwidth_bytes_per_second": memory_bandwidth,
            "compute_ceiling_flops_per_second": compute_ceiling,
            "memory_ceiling_flops_per_second": memory_ceiling,
            "roofline_ceiling_flops_per_second": roofline_ceiling,
            "lower_theoretical_ceiling": ceiling_type,
            "roofline_attainment_pct": attainment,
            "status": row_status,
            "missing_inputs": missing,
            "warnings": warnings,
            "input_metric_ids": [
                "compute_flop_count",
                *(["dram_read_bytes"] if read else []),
                *(["dram_write_bytes"] if write else []),
                *(["theoretical_peak_flops"] if peak_compute else []),
                *(["dram_peak_bandwidth_bytes_per_s"] if peak_bandwidth else []),
            ],
        })
        global_missing.extend(missing)

    if not analyses:
        return _empty_roofline(global_missing or ["compatible compute FLOP count"])
    status = "complete" if all(item["status"] == "complete" for item in analyses) else "partial"
    return {
        "status": status,
        "analyses": analyses,
        "missing_inputs": list(dict.fromkeys(global_missing)),
        "interpretation": (
            "The lower theoretical ceiling identifies the limiting roofline bound for this arithmetic intensity; "
            "it is not, by itself, proof that the measured workload is bottlenecked by that resource."
        ),
    }


def _link_counter_ids(link_type):
    if link_type == "nvlink":
        return "nvlink_tx_bytes", "nvlink_rx_bytes"
    if link_type == "pcie":
        return "pcie_tx_bytes", "pcie_rx_bytes"
    if link_type in {"infiniband", "roce", "ethernet", "other"}:
        return "network_tx_bytes", "network_rx_bytes"
    return None, None


def analyze_communication(evidence):
    """Report per-link traffic and utilization without combining unlike links."""
    metrics = (evidence or {}).get("metrics", [])
    groups = sorted({
        (item.get("entity_id"), item.get("link_type"))
        for item in metrics
        if isinstance(item, dict) and item.get("scope") == "per_link"
        and isinstance(item.get("entity_id"), str) and item.get("entity_id")
        and item.get("link_type")
        and item.get("metric_id") in {
            "link_bandwidth_bytes_per_s", "link_peak_bandwidth_bytes_per_s",
            "link_utilization_pct", "nvlink_tx_bytes", "nvlink_rx_bytes",
            "pcie_tx_bytes", "pcie_rx_bytes", "network_tx_bytes", "network_rx_bytes",
        }
    }, key=lambda pair: (str(pair[1]), str(pair[0])))
    seconds = _window_seconds(evidence)
    links, missing = [], []
    for entity_id, link_type in groups:
        reference = {"scope": "per_link", "entity_id": entity_id, "link_type": link_type}
        rates = [
            item for item in _metrics(evidence, "link_bandwidth_bytes_per_s")
            if _same_boundary(item, reference) and item.get("link_type") == link_type
            and item.get("aggregation") in RATE_AGGREGATIONS
            and _valid_number(item.get("value"))
        ]
        peaks = [
            item for item in _metrics(evidence, "link_peak_bandwidth_bytes_per_s")
            if _same_boundary(item, reference) and item.get("link_type") == link_type
            and item.get("aggregation") in PEAK_AGGREGATIONS
            and _valid_number(item.get("value"), positive=True)
        ]
        reported_util = [
            item for item in _metrics(evidence, "link_utilization_pct")
            if _same_boundary(item, reference) and item.get("link_type") == link_type
            and _valid_number(item.get("value"))
        ]
        tx_id, rx_id = _link_counter_ids(link_type)
        tx = _first(_matching(evidence, tx_id, reference, aggregations={"sum"})) if tx_id else None
        rx = _first(_matching(evidence, rx_id, reference, aggregations={"sum"})) if rx_id else None
        measured = rates[0] if rates else None
        directionality = measured.get("directionality") if measured else None
        target_directionality = peaks[0].get("directionality") if peaks else None
        if measured is None and seconds:
            requested_direction = target_directionality
            if requested_direction == "bidirectional" and tx and rx:
                measured = {
                    "value": (tx["value"] + rx["value"]) / seconds,
                    "directionality": "bidirectional",
                    "aggregation": "rate",
                    "source": "derived_from_same_link_tx_rx_byte_sums",
                }
            elif requested_direction == "tx" and tx:
                measured = {
                    "value": tx["value"] / seconds,
                    "directionality": "tx",
                    "aggregation": "rate",
                    "source": "derived_from_same_link_tx_byte_sum",
                }
            elif requested_direction == "rx" and rx:
                measured = {
                    "value": rx["value"] / seconds,
                    "directionality": "rx",
                    "aggregation": "rate",
                    "source": "derived_from_same_link_rx_byte_sum",
                }
            elif requested_direction is None and tx and rx:
                measured = {
                    "value": (tx["value"] + rx["value"]) / seconds,
                    "directionality": "bidirectional",
                    "aggregation": "rate",
                    "source": "derived_from_same_link_tx_rx_byte_sums",
                }
            elif requested_direction is None and tx:
                measured = {
                    "value": tx["value"] / seconds,
                    "directionality": "tx",
                    "aggregation": "rate",
                    "source": "derived_from_same_link_tx_byte_sum",
                }
            elif requested_direction is None and rx:
                measured = {
                    "value": rx["value"] / seconds,
                    "directionality": "rx",
                    "aggregation": "rate",
                    "source": "derived_from_same_link_rx_byte_sum",
                }
        directionality = measured.get("directionality") if measured else None

        peak = next((
            item for item in peaks
            if measured is not None and item.get("directionality") == measured.get("directionality")
        ), None)
        utilization = None
        utilization_source = None
        warnings = []
        if measured is not None and peak is not None:
            if peak["value"] > 0:
                ratio = measured["value"] / peak["value"] * 100
                if 0 <= ratio <= 100:
                    utilization = ratio
                    utilization_source = "derived_from_measured_and_peak_bandwidth"
                else:
                    warnings.append(
                        "measured bandwidth exceeds peak; check directionality, full-duplex convention and counter coverage"
                    )
        direct = next((
            item for item in reported_util
            if item.get("directionality") in {"tx", "rx", "bidirectional", "aggregate"}
        ), None)
        if direct is not None:
            if utilization is not None and not math.isclose(
                utilization, direct["value"], rel_tol=1e-9, abs_tol=1e-9
            ):
                warnings.append("reported and recomputed link utilization differ; verify sampling window, counter definition and duplex semantics")
            utilization = direct["value"]
            utilization_source = "reported_link_utilization_pct"

        if measured is None:
            missing.append(f"{entity_id}: measured link bandwidth or directional byte counters")
        if peak is None and direct is None:
            missing.append(f"{entity_id}: matching per-link peak bandwidth/directionality or reported utilization")
        status = "complete" if utilization is not None else "partial"
        links.append({
            "entity_id": entity_id,
            "link_type": link_type,
            "directionality": direct.get("directionality") if direct else (
                peak.get("directionality") if peak else directionality
            ),
            "measured_bandwidth_bytes_per_second": measured.get("value") if measured else None,
            "peak_bandwidth_bytes_per_second": peak.get("value") if peak else None,
            "utilization_pct": utilization,
            "utilization_source": utilization_source,
            "status": status,
            "missing_inputs": [
                *([] if measured is not None else ["measured bandwidth"]),
                *([] if peak is not None or direct is not None else ["matching peak bandwidth or reported utilization"]),
            ],
            "warnings": warnings,
        })

    if not links:
        missing.append("per-link entity, fabric, traffic and directionality-matched capacity/utilization")
    return {
        "status": "complete" if links and all(item["status"] == "complete" for item in links)
            else "partial" if links else "insufficient_evidence",
        "links": links,
        "missing_inputs": missing,
        "interpretation": (
            "Link utilization is reported per entity and directionality. It does not establish that the link is on "
            "the critical path or that communication limits end-to-end performance."
        ),
    }


def _read_runtime_metric(record, key):
    normalized = record.get("normalized_metrics")
    if not isinstance(normalized, dict):
        return None
    entry = normalized.get(key)
    if not isinstance(entry, dict):
        return None
    expected = RUNTIME_METRICS.get(key)
    if expected is None:
        return None
    unit, direction, family = expected
    value = entry.get("value")
    if (
        not _valid_number(value)
        or (family in {"power", "energy"} and not (
            record.get("power_measurement_valid") is True
            and record.get("gpu_power_metrics_available") is True
        ))
        or entry.get("unit") != unit
        or entry.get("direction") != direction
        or entry.get("family") != family
    ):
        return None
    return {"value": value, "unit": unit, "direction": direction, "family": family}


def analyze_serving_runtime(record):
    """Extract publisher-normalized serving signals without inferring hidden timings."""
    available = {
        key: value
        for key in RUNTIME_METRICS
        if (value := _read_runtime_metric(record, key)) is not None
    }
    derived = {}
    for phase in ("ttft", "tpot"):
        median = available.get("median_" + phase)
        p99 = available.get("p99_" + phase)
        if median and p99 and median["value"] > 0:
            derived[phase + "_p99_to_median_ratio"] = p99["value"] / median["value"]

    workload = record.get("workload") if isinstance(record.get("workload"), dict) else {}
    configuration = record.get("configuration") if isinstance(record.get("configuration"), dict) else {}
    workload_fields = {
        key: workload[key] for key in ("isl", "osl", "concurrency", "batch_size")
        if key in workload and workload[key] is not None
    }
    config_keys = (
        "prefill_tp", "prefill_ep", "prefill_dp_attention", "prefill_num_workers",
        "decode_tp", "decode_ep", "decode_dp_attention", "decode_num_workers", "offload_mode",
    )
    parallelism = {key: configuration[key] for key in config_keys if key in configuration}

    return {
        "status": "available" if available else "insufficient_evidence",
        "metrics": available,
        "derived_descriptive_ratios": derived,
        "workload": workload_fields,
        "parallelism": parallelism,
        "gpu_power_validated": (
            record.get("power_measurement_valid") is True
            and record.get("gpu_power_metrics_available") is True
        ),
        "interpretation": (
            "TTFT, TPOT, ITL and throughput are end-to-end/runtime observations, not a measured hardware time breakdown. "
            "GPU utilization and memory-used are contextual signals; neither identifies the cause of latency."
        ),
    }


def _kv_observations(evidence):
    metrics = (evidence or {}).get("metrics", [])
    observations = []
    for used_id, capacity_id, unit in (
        ("kv_cache_used_bytes", "kv_cache_capacity_bytes", "byte"),
        ("kv_cache_tokens", "kv_cache_token_capacity", "token"),
    ):
        for used in _metrics(evidence, used_id):
            capacity = _first(_matching(evidence, capacity_id, used))
            if capacity is None or used.get("aggregation") != capacity.get("aggregation"):
                continue
            if not _valid_number(used.get("value")) or not _valid_number(capacity.get("value"), positive=True):
                continue
            pct = used["value"] / capacity["value"] * 100
            if 0 <= pct <= 100:
                observations.append({
                    "scope": used.get("scope"), "entity_id": used.get("entity_id"),
                    "unit": unit, "used": used["value"], "capacity": capacity["value"],
                    "occupancy_pct": pct, "input_metric_ids": [used_id, capacity_id],
                })
    for metric in _metrics(evidence, "kv_cache_occupancy_pct"):
        if not any(
            item["scope"] == metric.get("scope") and item["entity_id"] == metric.get("entity_id")
            for item in observations
        ) and _valid_number(metric.get("value")) and 0 <= metric["value"] <= 100:
            observations.append({
                "scope": metric.get("scope"), "entity_id": metric.get("entity_id"),
                "unit": "%", "used": None, "capacity": None,
                "occupancy_pct": metric["value"],
                "input_metric_ids": metric.get("input_metric_ids", ["kv_cache_occupancy_pct"]),
            })
    return observations


def _thermal_observations(evidence):
    metrics = (evidence or {}).get("metrics", [])
    throttles = _metrics(evidence, "throttle_active_pct")
    output = []
    for throttle in throttles:
        related = {}
        for metric_id in ("gpu_power_w", "gpu_clock_hz", "temperature_c"):
            related[metric_id] = _first(_matching(evidence, metric_id, throttle))
        output.append({
            "scope": throttle.get("scope"),
            "entity_id": throttle.get("entity_id"),
            "throttle_active_pct": throttle.get("value"),
            "gpu_power_w": related["gpu_power_w"].get("value") if related["gpu_power_w"] else None,
            "gpu_clock_hz": related["gpu_clock_hz"].get("value") if related["gpu_clock_hz"] else None,
            "temperature_c": related["temperature_c"].get("value") if related["temperature_c"] else None,
            "throttle_reported": _valid_number(throttle.get("value")) and throttle["value"] > 0,
        })
    return output


def attribute_candidates(evidence, roofline, communication, runtime):
    """Produce evidence observations and explicit non-attribution boundaries."""
    kv = _kv_observations(evidence)
    thermal = _thermal_observations(evidence)
    complete_roofline = [item for item in roofline.get("analyses", []) if item["status"] == "complete"]
    observed_links = [item for item in communication.get("links", []) if item["utilization_pct"] is not None]
    candidates = []

    if complete_roofline:
        for item in complete_roofline:
            candidates.append({
                "mechanism": "roofline_" + str(item["lower_theoretical_ceiling"]) + "_ceiling",
                "status": "observed",
                "scope": item["scope"],
                "entity_id": item["entity_id"],
                "observation": (
                    f"The {item['lower_theoretical_ceiling']} theoretical ceiling is lower at the measured arithmetic intensity."
                ),
                "evidence": [
                    "compute_flop_count", "dram_read_bytes", "dram_write_bytes",
                    "theoretical_peak_flops", "dram_peak_bandwidth_bytes_per_s",
                ],
                "not_proven": "This is a model ceiling comparison, not proof of the runtime bottleneck.",
            })
    else:
        candidates.append({
            "mechanism": "roofline",
            "status": "insufficient_evidence",
            "observation": "A comparable roofline position cannot be calculated.",
            "evidence": [],
            "not_proven": "No compute- or memory-bound label is emitted.",
        })

    for link in observed_links:
        candidates.append({
            "mechanism": "communication_link_utilization",
            "status": "observed",
            "scope": "per_link",
            "entity_id": link["entity_id"],
            "observation": f"{link['link_type']} {link['directionality']} utilization is {link['utilization_pct']:.3g}%.",
            "evidence": ["link_bandwidth_bytes_per_s", "link_peak_bandwidth_bytes_per_s"],
            "not_proven": "Link activity does not prove critical-path contention or end-to-end communication limitation.",
        })
    if not observed_links:
        candidates.append({
            "mechanism": "communication",
            "status": "insufficient_evidence",
            "observation": "No comparable per-link utilization observation is available.",
            "evidence": [],
            "not_proven": "Aggregate GPU utilization or multi-GPU configuration is not substituted for link telemetry.",
        })

    if kv:
        for item in kv:
            candidates.append({
                "mechanism": "kv_cache_occupancy",
                "status": "observed",
                "scope": item["scope"],
                "entity_id": item["entity_id"],
                "observation": f"KV-cache occupancy is {item['occupancy_pct']:.3g}% ({item['unit']} boundary).",
                "evidence": item["input_metric_ids"],
                "not_proven": "Occupancy alone does not establish allocator pressure, eviction, preemption or decode stalls.",
            })
    else:
        candidates.append({
            "mechanism": "kv_cache_capacity_pressure",
            "status": "insufficient_evidence",
            "observation": "No matched KV-cache used/capacity pair is available.",
            "evidence": [],
            "not_proven": "Missing KV-cache telemetry is unknown, not zero occupancy.",
        })

    if any(item["throttle_reported"] for item in thermal):
        candidates.append({
            "mechanism": "thermal_or_power_throttling",
            "status": "observed",
            "observation": "A throttle-active counter reports non-zero activity in the sampled window.",
            "evidence": ["throttle_active_pct"],
            "not_proven": "This does not identify the specific throttle reason or quantify its contribution to latency.",
        })
    elif thermal:
        candidates.append({
            "mechanism": "thermal_or_power_throttling",
            "status": "not_observed_in_window",
            "observation": "The supplied throttle-active counters report zero in this sampled window.",
            "evidence": ["throttle_active_pct"],
            "not_proven": "This does not rule out throttling outside the sampled window or unreported throttle reasons.",
        })
    else:
        candidates.append({
            "mechanism": "thermal_or_power_throttling",
            "status": "insufficient_evidence",
            "observation": "No throttle-active counter is attached.",
            "evidence": [],
            "not_proven": "Temperature or power alone would not establish active throttling.",
        })

    candidates.append({
        "mechanism": "runtime_scheduling_or_queueing",
        "status": "not_attributed",
        "observation": (
            "Serving latency/throughput signals are present."
            if runtime.get("metrics") else "No validated serving runtime signals are present."
        ),
        "evidence": list(runtime.get("metrics", {}).keys()),
        "not_proven": "TTFT/TPOT, throughput and aggregate GPU utilization do not isolate queueing, scheduler delay, kernel gaps or CPU/runtime overhead.",
        "additional_measurements": [
            "request arrival and queue-wait timestamps",
            "batch formation/wait time and active batch size by phase",
            "GPU kernel launch gaps and per-kernel active duration",
            "CPU thread scheduling, runtime dispatch and synchronization traces",
            "prefill/decode phase-aligned GPU and fabric counters",
        ],
    })
    return {
        "verdict": "undetermined",
        "automatic_bottleneck_classification": False,
        "candidates": candidates,
        "policy": "Report observations and missing evidence; do not rank or label bottlenecks using uncalibrated thresholds.",
    }


def diagnose_record(record):
    if not isinstance(record, dict):
        raise ValueError("input must be a benchmark record object")
    evidence = record.get("hardware_evidence")
    if evidence is not None:
        errors = validate_hardware_evidence({"hardware_evidence": evidence}, "input")
        if errors:
            raise ValueError("; ".join(errors))
    roofline = analyze_roofline(evidence) if evidence else _empty_roofline([
        "hardware_evidence bundle with compute FLOPs, DRAM bytes and matching peak definitions"
    ])
    communication = analyze_communication(evidence) if evidence else {
        "status": "insufficient_evidence", "links": [],
        "missing_inputs": ["provenance-backed per-link traffic and capacity"],
        "interpretation": "No link utilization is inferred from device count or topology labels.",
    }
    runtime = analyze_serving_runtime(record)
    gpu_execution = analyze_gpu_execution_efficiency(record)
    attribution = attribute_candidates(evidence, roofline, communication, runtime)
    window = _window_seconds(evidence) if evidence else None
    has_any = bool(
        (evidence and evidence.get("metrics")) or roofline.get("analyses")
        or communication.get("links") or runtime.get("metrics")
        or _kv_observations(evidence) or _thermal_observations(evidence)
        or gpu_execution.get("status") == "evidence_available"
    )
    next_measurements = [
        "Compute: interval FLOP count plus a precision/sparsity-matched device peak and SM/Tensor activity.",
        "Communication: per-link directional byte totals, directionality-matched peak bandwidth, and physical/logical topology.",
        "KV cache: used bytes/tokens and allocator capacity at the same scope and time window.",
        "GPU activity: SM active-cycle, Tensor activity, kernel-scoped throughput and synchronized sampling windows.",
        "Memory: achieved DRAM bytes/s and same-boundary peak bandwidth; DRAM activity alone is not saturation.",
        "Compute/communication overlap: request-correlated kernel and communication intervals on a mapped common clock.",
        "Scheduling: request queue, batch formation, dispatch and kernel-gap traces aligned to prefill/decode phases.",
    ]
    return {
        "schema_version": "1.0",
        "record_id": record.get("id"),
        "generated_by": DERIVER,
        "sampling_window_seconds": window,
        "system_scope": evidence.get("system_scope") if evidence else None,
        "roofline": roofline,
        "communication": communication,
        "serving_runtime": runtime,
        "gpu_execution_efficiency": gpu_execution,
        "attribution": attribution,
        "overall_status": "evidence_available" if has_any else "insufficient_evidence",
        "overall_verdict": "undetermined",
        "next_measurements": next_measurements,
        "limitations": [
            "A benchmark record may combine publisher runtime metrics and a separate profiler capture; temporal alignment is not assumed.",
            "The roofline model uses measured arithmetic intensity and declared peak definitions; it does not account for cache reuse, instruction mix, occupancy or kernel launch overhead unless separately measured.",
            "Per-link utilization is not a critical-path measurement; topology and collective algorithm details are still required.",
            "No numeric confidence score or fixed utilization threshold is used because the evidence contract does not calibrate either.",
            "Missing evidence is unknown, never zero.",
            "SM inactive-cycle complement is not a whole-GPU idle estimate; kernel time is not equivalent to SM-active time.",
            "Temporal kernel/communication overlap does not prove device-side concurrency or communication hiding.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="One benchmark record JSON object")
    parser.add_argument("--output", required=True, type=Path, help="Destination report JSON; input is never overwritten")
    args = parser.parse_args()
    try:
        record = json.loads(args.input.read_text(encoding="utf-8"))
        report = diagnose_record(record)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: diagnosis report for {report.get('record_id') or 'unnamed record'}; "
        f"roofline={report['roofline']['status']}, "
        f"links={len(report['communication']['links'])}, "
        f"runtime_signals={len(report['serving_runtime']['metrics'])}. "
        f"No bottleneck verdict was generated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
