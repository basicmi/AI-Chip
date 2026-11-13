#!/usr/bin/env python3
"""Align runtime trace events with hardware-counter sampling windows.

Only explicit UTC wall-clock timestamps are joined. A metric can be eligible
for a phase join only when its own capture window is contained by one leaf
runtime event and the event/counter entity identities are compatible.
Temporal overlap is not causal attribution.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_benchmark_results import validate_hardware_evidence, validate_runtime_trace

DERIVER = "scripts/align_runtime_hardware_traces.py"
ENTITY_REQUIRED_SCOPES = {"per_gpu", "per_link", "per_kernel", "per_process"}
SCOPE_EVENT_CATEGORIES = {
    "per_kernel": {"kernel"},
    "per_link": {"communication"},
}


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _seconds(start: datetime, end: datetime) -> float:
    return max(0.0, (end - start).total_seconds())


def _overlap(left_start: datetime, left_end: datetime,
             right_start: datetime, right_end: datetime) -> float:
    return _seconds(max(left_start, right_start), min(left_end, right_end))


def _union_seconds(intervals: list[tuple[datetime, datetime]]) -> float:
    if not intervals:
        return 0.0
    ordered = sorted(intervals)
    start, end = ordered[0]
    total = 0.0
    for next_start, next_end in ordered[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += _seconds(start, end)
            start, end = next_start, next_end
    return total + _seconds(start, end)


def _entity_status(metric: dict, event: dict) -> str:
    metric_entity = metric.get("entity_id")
    event_entity = event.get("entity_id")
    if metric_entity is not None and event_entity is not None:
        return "exact_match" if metric_entity == event_entity else "mismatch"
    if metric_entity is None and event_entity is None:
        return "both_unscoped"
    return "not_established"


def _scope_compatible(metric: dict, event: dict, entity_status: str) -> tuple[bool, str | None]:
    scope = metric.get("scope")
    expected_categories = SCOPE_EVENT_CATEGORIES.get(scope)
    if expected_categories and event.get("category") not in expected_categories:
        return False, "event_category_does_not_match_metric_scope"
    if scope in ENTITY_REQUIRED_SCOPES and entity_status != "exact_match":
        return False, "exact_entity_identity_required_for_" + str(scope)
    if entity_status == "mismatch":
        return False, "metric_and_event_entity_ids_differ"
    if entity_status == "not_established":
        return False, "entity_identity_is_incomplete"
    return True, None


def _event_overlap_summary(metric_start: datetime, metric_end: datetime,
                           events: list[dict]) -> tuple[list[dict], dict, float]:
    matches = []
    by_category: dict[str, list[tuple[datetime, datetime]]] = {}
    all_intervals = []
    duration = _seconds(metric_start, metric_end)
    for event in events:
        start, end = _time(event["started_at"]), _time(event["ended_at"])
        overlap = _overlap(metric_start, metric_end, start, end)
        if overlap <= 0:
            continue
        interval = (max(metric_start, start), min(metric_end, end))
        all_intervals.append(interval)
        by_category.setdefault(event["category"], []).append(interval)
        matches.append({
            "event_id": event["event_id"],
            "name": event["name"],
            "category": event["category"],
            "overlap_seconds": round(overlap, 9),
            "overlap_pct": round(overlap / duration * 100, 6) if duration else 0,
            "fully_contains_metric_window": start <= metric_start and end >= metric_end,
            "entity_id": event.get("entity_id"),
            "parent_event_id": event.get("parent_event_id"),
        })
    category_coverage = {
        category: {
            "overlap_seconds": round(_union_seconds(intervals), 9),
            "overlap_pct": round(_union_seconds(intervals) / duration * 100, 6) if duration else 0,
        }
        for category, intervals in sorted(by_category.items())
    }
    total_coverage = min(duration, _union_seconds(all_intervals))
    return matches, category_coverage, total_coverage


def _metric_alignment(metric: dict, evidence: dict, trace: dict) -> dict:
    sampling = metric.get("sampling_window")
    metric_window_source = "metric_specific"
    if sampling is None:
        sampling = evidence["sampling"]
        metric_window_source = "bundle_level_fallback"
    start, end = _time(sampling["started_at"]), _time(sampling["ended_at"])
    duration = _seconds(start, end)
    events = trace["events"]
    matches, category_coverage, total_coverage = _event_overlap_summary(start, end, events)
    full_events = [
        event for event in events
        if _time(event["started_at"]) <= start and _time(event["ended_at"]) >= end
    ]
    full_ids = {event["event_id"] for event in full_events}
    parent_ids = {
        event.get("parent_event_id") for event in full_events
        if event.get("parent_event_id") in full_ids
    }
    leaf_candidates = [event for event in full_events if event["event_id"] not in parent_ids]

    selected_event = None
    entity_status = "not_established"
    eligible = False
    reason = "metric_specific_sampling_window_required"
    alignment_status = "metric_window_missing" if metric_window_source == "bundle_level_fallback" else "no_temporal_overlap"

    if metric_window_source == "metric_specific":
        if total_coverage <= 0:
            alignment_status = "no_temporal_overlap"
            reason = "no_runtime_event_overlaps_metric_capture_window"
        elif not leaf_candidates:
            alignment_status = "partial_or_multiple_event_overlap"
            reason = "no_single_leaf_event_contains_the_complete_metric_capture_window"
        elif len(leaf_candidates) > 1:
            alignment_status = "ambiguous_multiple_leaf_events"
            reason = "multiple_leaf_events_contain_the_complete_metric_capture_window"
        else:
            selected_event = leaf_candidates[0]
            entity_status = _entity_status(metric, selected_event)
            scope_ok, scope_reason = _scope_compatible(metric, selected_event, entity_status)
            if scope_ok:
                alignment_status = "fully_contained_single_leaf_event"
                eligible = True
                reason = None
            else:
                alignment_status = "identity_or_scope_mismatch"
                reason = scope_reason

    return {
        "metric_id": metric.get("metric_id"),
        "scope": metric.get("scope"),
        "entity_id": metric.get("entity_id"),
        "value": metric.get("value"),
        "unit": metric.get("unit"),
        "measurement_kind": metric.get("measurement_kind"),
        "aggregation": metric.get("aggregation"),
        "source_name": metric.get("source_name"),
        "metric_window_source": metric_window_source,
        "metric_window_seconds": round(duration, 9),
        "runtime_event_coverage_pct": round(total_coverage / duration * 100, 6) if duration else 0,
        "category_overlap": category_coverage,
        "overlapping_events": matches,
        "alignment_status": alignment_status,
        "selected_event": ({
            "event_id": selected_event["event_id"],
            "name": selected_event["name"],
            "category": selected_event["category"],
            "entity_id": selected_event.get("entity_id"),
        } if selected_event else None),
        "entity_identity_status": entity_status,
        "eligible_for_phase_join": eligible,
        "phase_join_reason": reason,
        "causal_attribution": "not_claimed",
    }


def align_record(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    record_id = record.get("id")
    evidence = record.get("hardware_evidence")
    trace = record.get("runtime_trace")
    errors = []
    if evidence is not None:
        errors.extend(validate_hardware_evidence({"hardware_evidence": evidence}, "record"))
    if trace is not None:
        errors.extend(validate_runtime_trace(trace, "record"))
    if errors:
        raise ValueError("; ".join(errors))

    if evidence is None and trace is None:
        status = "missing_hardware_evidence_and_runtime_trace"
    elif evidence is None:
        status = "missing_hardware_evidence"
    elif trace is None:
        status = "missing_runtime_trace"
    else:
        status = "no_temporal_overlap"

    report = {
        "record_id": record_id,
        "status": status,
        "hardware_evidence_available": evidence is not None,
        "runtime_trace_available": trace is not None,
        "metric_alignments": [],
        "eligible_metric_phase_join_count": 0,
        "limitations": [
            "Only UTC wall-clock timestamps are supported; monotonic clocks require an explicit clock-domain mapping before alignment.",
            "Bundle-level hardware sampling windows are coarse and are never used to attribute an individual counter to a runtime phase.",
            "A phase join requires a metric-specific sampling window, one containing leaf event, and compatible entity/scope identity.",
            "Temporal overlap is descriptive and does not establish causality or prove that a counter caused a runtime delay.",
            "Aggregate counters may include activity outside the selected event unless the collector guarantees the metric-specific window and scope.",
        ],
    }
    if evidence is None or trace is None:
        return report

    hw_start, hw_end = _time(evidence["sampling"]["started_at"]), _time(evidence["sampling"]["ended_at"])
    trace_start, trace_end = _time(trace["sampling"]["started_at"]), _time(trace["sampling"]["ended_at"])
    hardware_duration = _seconds(hw_start, hw_end)
    trace_duration = _seconds(trace_start, trace_end)
    capture_overlap = _overlap(hw_start, hw_end, trace_start, trace_end)
    report["status"] = "overlapping_capture_windows" if capture_overlap > 0 else "no_temporal_overlap"
    report["capture_alignment"] = {
        "clock_domain": trace["clock_domain"],
        "hardware_window_seconds": round(hardware_duration, 9),
        "trace_window_seconds": round(trace_duration, 9),
        "overlap_seconds": round(capture_overlap, 9),
        "hardware_window_coverage_by_trace_pct": round(capture_overlap / hardware_duration * 100, 6) if hardware_duration else 0,
        "trace_window_coverage_by_hardware_pct": round(capture_overlap / trace_duration * 100, 6) if trace_duration else 0,
    }
    report["trace_event_count"] = len(trace["events"])
    report["trace_event_categories"] = sorted({event["category"] for event in trace["events"]})
    report["metric_alignments"] = [
        _metric_alignment(metric, evidence, trace)
        for metric in evidence["metrics"]
    ]
    report["eligible_metric_phase_join_count"] = sum(
        1 for item in report["metric_alignments"] if item["eligible_for_phase_join"]
    )
    return report


def align_database(database: dict | list) -> dict:
    if isinstance(database, list):
        records = database
    elif isinstance(database, dict):
        records = database.get("records")
    else:
        raise ValueError("input must be a benchmark database object or record array")
    if not isinstance(records, list):
        raise ValueError("input must contain a records array")
    reports = [align_record(record) for record in records]
    return {
        "schema_version": "1.0",
        "generated_by": DERIVER,
        "source_scope": "benchmark_record_runtime_trace_alignment",
        "input_record_count": len(records),
        "records_with_hardware_evidence": sum(item["hardware_evidence_available"] for item in reports),
        "records_with_runtime_trace": sum(item["runtime_trace_available"] for item in reports),
        "records_with_overlapping_capture_windows": sum(
            item["status"] == "overlapping_capture_windows" for item in reports
        ),
        "records_with_eligible_phase_joins": sum(
            item["eligible_metric_phase_join_count"] > 0 for item in reports
        ),
        "eligible_metric_phase_join_count": sum(
            item["eligible_metric_phase_join_count"] for item in reports
        ),
        "records": reports,
        "global_limitations": [
            "A timestamp overlap is not a causal attribution.",
            "The report does not interpolate hardware counters, synthesize missing samples, or infer activity during unmeasured intervals.",
            "No phase-level performance-loss score, bottleneck ranking, confidence score, or statistical significance is produced.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Benchmark database JSON or record array")
    parser.add_argument("--output", required=True, type=Path, help="Destination alignment report JSON; input is never overwritten")
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("input and output paths must be different")
        source = json.loads(args.input.read_text(encoding="utf-8"))
        report = align_database(source)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: {report['input_record_count']} records; "
        f"{report['records_with_runtime_trace']} with runtime traces; "
        f"{report['records_with_overlapping_capture_windows']} overlapping captures; "
        f"{report['eligible_metric_phase_join_count']} metric/event joins. "
        "No causal attribution was generated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
