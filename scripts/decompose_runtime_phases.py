#!/usr/bin/env python3
"""Decompose request-level runtime traces into TTFT/TPOT, phase coverage and explicit dependency paths.

A controlling dependency chain is emitted only when the collector attests a complete
graph and the first token has a fully rooted completion-dependency path. This tool
does not infer causality, serialize concurrent work, or produce a bottleneck verdict.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_benchmark_results import _parse_runtime_trace_timestamp, validate_runtime_trace

DERIVER = "scripts/decompose_runtime_phases.py"
PRIMARY_PHASES = ("queue_wait", "batch_wait", "prefill", "decode", "host_runtime", "other")
SUBPHASES = ("kernel", "communication", "cpu_scheduling", "communication_wait")
ALL_PHASES = PRIMARY_PHASES + SUBPHASES


def _trace_time(value: Any, trace: dict) -> datetime:
    parsed = _parse_runtime_trace_timestamp(
        value, trace.get("clock_domain"), trace.get("clock_mapping")
    )
    if parsed is None:
        raise ValueError("runtime trace timestamp cannot be mapped into UTC")
    return parsed


def _seconds(start: datetime, end: datetime) -> float:
    return max(0.0, (end - start).total_seconds())


def _union_seconds(intervals: list[tuple[datetime, datetime]]) -> float:
    ordered = sorted((start, end) for start, end in intervals if end > start)
    if not ordered:
        return 0.0
    start, end = ordered[0]
    total = 0.0
    for next_start, next_end in ordered[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += _seconds(start, end)
            start, end = next_start, next_end
    return total + _seconds(start, end)


def _clip(interval: tuple[datetime, datetime], window: tuple[datetime, datetime]):
    start = max(interval[0], window[0])
    end = min(interval[1], window[1])
    return (start, end) if end > start else None


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _distribution(values: list[float]) -> dict:
    return {
        "sample_count": len(values),
        "mean": round(sum(values) / len(values), 6) if values else None,
        "p50": round(_percentile(values, 0.50), 6) if values else None,
        "p90": round(_percentile(values, 0.90), 6) if values else None,
        "p95": round(_percentile(values, 0.95), 6) if values else None,
        "p99": round(_percentile(values, 0.99), 6) if values else None,
        "min": round(min(values), 6) if values else None,
        "max": round(max(values), 6) if values else None,
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
        result = _resolve_correlation(parent_id, event_map, cache, visiting) if parent_id in event_map else None
    cache[event_id] = result
    visiting.remove(event_id)
    return result


def _phase_coverage(events: list[dict], window: tuple[datetime, datetime], trace: dict) -> dict:
    duration = _seconds(*window)
    by_category = {category: [] for category in ALL_PHASES}
    all_intervals = []
    for item in events:
        category = item["category"]
        if category not in by_category:
            continue
        interval = _clip(
            (_trace_time(item["started_at"], trace), _trace_time(item["ended_at"], trace)),
            window,
        )
        if interval is not None:
            by_category[category].append(interval)
            all_intervals.append(interval)

    primary_intervals = [
        interval for category in PRIMARY_PHASES for interval in by_category[category]
    ]
    primary_union = _union_seconds(primary_intervals)
    category_seconds = {
        category: _union_seconds(intervals)
        for category, intervals in by_category.items()
    }
    total_event_union = _union_seconds(all_intervals)
    return {
        "window_ms": round(duration * 1000, 6),
        "primary_phase_coverage": {
            category: round(category_seconds[category] * 1000, 6)
            for category in PRIMARY_PHASES
        },
        "subphase_coverage": {
            category: round(category_seconds[category] * 1000, 6)
            for category in SUBPHASES
        },
        "primary_phase_union_ms": round(primary_union * 1000, 6),
        "primary_phase_overlap_ms": round(
            max(0.0, sum(category_seconds[key] for key in PRIMARY_PHASES) - primary_union) * 1000, 6
        ),
        "all_event_union_ms": round(total_event_union * 1000, 6),
        "unclassified_gap_ms": round(max(0.0, duration - primary_union) * 1000, 6),
        "primary_phase_coverage_pct": round(primary_union / duration * 100, 6) if duration else 0,
    }




def _critical_path_analysis(
    request_event: dict, events: list[dict], trace: dict,
    event_map: dict, ttft_ms: float | None,
) -> dict:
    """Follow explicit completion dependencies to the first token; never infer edges."""
    attestation = request_event.get("dependency_graph_complete")
    if attestation is not True:
        return {
            "status": "incomplete_graph" if attestation is False else "not_attested",
            "completeness_attested": attestation is True,
            "dependency_path": [],
            "reason": "Collector marked the dependency graph incomplete."
                if attestation is False else
                "The request root does not attest that first-token dependencies are complete.",
        }
    if ttft_ms is None:
        return {"status":"ttft_unavailable","completeness_attested":True,
                "dependency_path":[],"reason":"A valid trace-derived TTFT is required."}
    first_tokens = [e for e in events if e.get("category") == "token_emit" and e.get("token_index") == 1]
    if not first_tokens:
        return {"status":"missing_first_token","completeness_attested":True,
                "dependency_path":[],"reason":"No token_index 1 marker exists for this request."}
    if len(first_tokens) != 1:
        return {"status":"ambiguous_first_token","completeness_attested":True,
                "dependency_path":[],"reason":"Multiple token_index 1 markers exist for this request."}

    root_id = request_event["event_id"]
    root_start = _trace_time(request_event["started_at"], trace)
    memo, visiting = {}, set()

    def visit(event_id: str):
        if event_id == root_id:
            return {"events":[],"event_duration_ms":0.0,
                    "unclassified_dependency_gap_ms":0.0,"controlling_predecessor_ties":0}
        if event_id in memo:
            return memo[event_id]
        if event_id in visiting or len(visiting) >= 900:
            return None
        event = event_map.get(event_id)
        dependencies = event.get("depends_on_event_ids") if isinstance(event, dict) else None
        if not isinstance(dependencies, list) or not dependencies:
            return None
        start, end = _trace_time(event["started_at"], trace), _trace_time(event["ended_at"], trace)
        if start is None or end is None or end < start:
            return None
        visiting.add(event_id)
        candidates = []
        for dependency_id in dependencies:
            predecessor = event_map.get(dependency_id)
            previous = visit(dependency_id)
            if predecessor is None or previous is None:
                visiting.remove(event_id)
                return None
            predecessor_start = _trace_time(predecessor["started_at"], trace)
            predecessor_end = predecessor_start if predecessor.get("category") == "request" else _trace_time(predecessor["ended_at"], trace)
            if predecessor_end is None or predecessor_end > start:
                visiting.remove(event_id)
                return None
            candidates.append((predecessor_end, previous, dependency_id))
        latest = max(item[0] for item in candidates)
        controlling = [item for item in candidates if item[0] == latest]
        controlling.sort(key=lambda item: (
            -item[1]["event_duration_ms"],
            tuple(node["event_id"] for node in item[1]["events"]),
            item[2],
        ))
        predecessor_end, previous, _ = controlling[0]
        duration_ms, gap_ms = _seconds(start, end) * 1000, _seconds(predecessor_end, start) * 1000
        result = {
            "events": previous["events"] + [{
                "event_id":event_id,"name":event["name"],"category":event["category"],
                "duration_ms":round(duration_ms,6),"gap_before_ms":round(gap_ms,6)
            }],
            "event_duration_ms":previous["event_duration_ms"] + duration_ms,
            "unclassified_dependency_gap_ms":previous["unclassified_dependency_gap_ms"] + gap_ms,
            "controlling_predecessor_ties":previous["controlling_predecessor_ties"] + (1 if len(controlling)>1 else 0),
        }
        visiting.remove(event_id)
        memo[event_id]=result
        return result

    path = visit(first_tokens[0]["event_id"])
    if path is None:
        return {
            "status":"missing_dependency_path","completeness_attested":True,
            "first_token_event_id":first_tokens[0]["event_id"],"dependency_path":[],
            "reason":"The first token has no complete dependency chain rooted at request start.",
        }
    reconstructed = path["event_duration_ms"] + path["unclassified_dependency_gap_ms"]
    matches = abs(reconstructed - ttft_ms) <= 0.001
    return {
        "status":"available" if matches else "path_time_mismatch",
        "completeness_attested":True,
        "first_token_event_id":first_tokens[0]["event_id"],
        "ttft_ms":round(ttft_ms,6),
        "dependency_path":path["events"],
        "dependency_path_event_ids":[item["event_id"] for item in path["events"]],
        "event_duration_ms":round(path["event_duration_ms"],6),
        "unclassified_dependency_gap_ms":round(path["unclassified_dependency_gap_ms"],6),
        "reconstructed_elapsed_ms":round(reconstructed,6),
        "reconstruction_matches_ttft":matches,
        "controlling_predecessor_ties":path["controlling_predecessor_ties"],
        "selection_rule":"Follow the declared prerequisite with the latest observed completion; break ties by accumulated event duration, then event ID.",
        "reason":None if matches else "The explicit dependency path does not reconcile to trace-derived TTFT.",
    }


def _request_decomposition(request_event: dict, events: list[dict], trace: dict, event_map: dict) -> dict:
    request_start = _trace_time(request_event["started_at"], trace)
    request_end = _trace_time(request_event["ended_at"], trace)
    request_window = (request_start, request_end)
    request_id = request_event["correlation_id"]
    tokens = sorted(
        (event for event in events if event["category"] == "token_emit"),
        key=lambda event: (event["token_index"], _trace_time(event["started_at"], trace)),
    )
    token_indexes = [event["token_index"] for event in tokens]
    token_times = [_trace_time(event["started_at"], trace) for event in tokens]
    warnings = []
    first_token_time = None
    ttft_ms = None
    tpot_ms = None
    token_sequence_complete = False

    if tokens:
        if token_indexes[0] == 1:
            first_token_time = token_times[0]
            if request_start <= first_token_time <= request_end:
                ttft_ms = _seconds(request_start, first_token_time) * 1000
            else:
                warnings.append("first token timestamp falls outside request envelope")
        else:
            warnings.append("token trace does not start at token_index 1")
        if len(set(token_indexes)) != len(token_indexes):
            warnings.append("duplicate token_index values prevent TPOT calculation")
        elif token_indexes == list(range(1, len(token_indexes) + 1)):
            token_sequence_complete = True
        else:
            warnings.append("token_index sequence has gaps; TPOT is not calculated")
        if any(right <= left for left, right in zip(token_times, token_times[1:])):
            warnings.append("token emission timestamps are not strictly increasing")
            token_sequence_complete = False
        if (
            token_sequence_complete and len(token_times) >= 2
            and token_times[0] >= request_start and token_times[-1] <= request_end
        ):
            tpot_ms = _seconds(token_times[0], token_times[-1]) * 1000 / (len(token_times) - 1)
    else:
        warnings.append("no token_emit markers; TTFT and TPOT cannot be measured from this trace")

    ttft_coverage = None
    tpot_coverage = None
    if first_token_time is not None and request_start <= first_token_time <= request_end:
        ttft_coverage = _phase_coverage(events, (request_start, first_token_time), trace)
    if token_sequence_complete and len(token_times) >= 2 and token_times[-1] > token_times[0]:
        tpot_coverage = _phase_coverage(events, (token_times[0], token_times[-1]), trace)

    request_coverage = _phase_coverage(events, request_window, trace)
    return {
        "correlation_id": request_id,
        "request_duration_ms": round(_seconds(request_start, request_end) * 1000, 6),
        "output_token_markers": len(tokens),
        "token_index_complete": token_sequence_complete,
        "ttft_ms": round(ttft_ms, 6) if ttft_ms is not None else None,
        "tpot_ms": round(tpot_ms, 6) if tpot_ms is not None else None,
        "first_token_at": first_token_time.isoformat() if first_token_time else None,
        "last_token_at": token_times[-1].isoformat() if token_times else None,
        "request_phase_coverage": request_coverage,
        "ttft_phase_coverage": ttft_coverage,
        "tpot_phase_coverage": tpot_coverage,
        "critical_path": _critical_path_analysis(request_event, events, trace, event_map, ttft_ms),
        "warnings": warnings,
    }


def decompose_record(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    trace = record.get("runtime_trace")
    if trace is None:
        return {
            "record_id": record.get("id"),
            "status": "missing_runtime_trace",
            "request_count": 0,
            "requests": [],
            "limitations": ["No runtime trace is attached; no phase decomposition is inferred."],
        }
    errors = validate_runtime_trace(trace, "record")
    if errors:
        raise ValueError("; ".join(errors))

    events = trace["events"]
    event_map = {event["event_id"]: event for event in events}
    correlation_cache = {}
    resolved = {
        event["event_id"]: _resolve_correlation(event["event_id"], event_map, correlation_cache)
        for event in events
    }
    requests = [
        event for event in events
        if event["category"] == "request" and event.get("correlation_id")
    ]
    requests_by_id = {}
    for event in requests:
        requests_by_id.setdefault(event["correlation_id"], []).append(event)

    duplicate_request_ids = sorted(
        request_id for request_id, matches in requests_by_id.items() if len(matches) != 1
    )
    if duplicate_request_ids:
        raise ValueError("duplicate request root correlation_id values: " + ", ".join(duplicate_request_ids))

    decompositions = []
    for request_event in requests:
        request_id = request_event["correlation_id"]
        request_events = [
            event for event in events
            if resolved[event["event_id"]] == request_id
            and event["event_id"] != request_event["event_id"]
        ]
        request_events = [
            event for event in request_events
            if _trace_time(event["started_at"], trace) >= _trace_time(request_event["started_at"], trace)
            and _trace_time(event["ended_at"], trace) <= _trace_time(request_event["ended_at"], trace)
        ]
        decompositions.append(_request_decomposition(request_event, request_events, trace, event_map))

    ttft_values = [item["ttft_ms"] for item in decompositions if item["ttft_ms"] is not None]
    tpot_values = [item["tpot_ms"] for item in decompositions if item["tpot_ms"] is not None]
    phase_summary = {}
    for window_key in ("request_phase_coverage", "ttft_phase_coverage", "tpot_phase_coverage"):
        eligible = [item[window_key] for item in decompositions if item[window_key] is not None]
        if not eligible:
            phase_summary[window_key] = {"sample_count": 0, "phases": {}}
            continue
        categories = {}
        for category in ALL_PHASES:
            key = "primary_phase_coverage" if category in PRIMARY_PHASES else "subphase_coverage"
            values = [coverage[key][category] for coverage in eligible]
            categories[category] = {
                "mean_ms": round(sum(values) / len(values), 6),
                "p50_ms": round(_percentile(values, 0.50), 6),
                "p95_ms": round(_percentile(values, 0.95), 6),
            }
        phase_summary[window_key] = {
            "sample_count": len(eligible),
            "phases": categories,
            "mean_primary_phase_union_ms": round(
                sum(item["primary_phase_union_ms"] for item in eligible) / len(eligible), 6
            ),
            "mean_primary_phase_overlap_ms": round(
                sum(item["primary_phase_overlap_ms"] for item in eligible) / len(eligible), 6
            ),
            "mean_unclassified_gap_ms": round(
                sum(item["unclassified_gap_ms"] for item in eligible) / len(eligible), 6
            ),
        }

    return {
        "record_id": record.get("id"),
        "status": "decomposed" if decompositions else "no_request_events",
        "clock_domain": trace["clock_domain"],
        "clock_mapping_method": trace.get("clock_mapping", {}).get("method") if isinstance(trace.get("clock_mapping"), dict) else None,
        "clock_mapping_max_error_ns": trace.get("clock_mapping", {}).get("max_error_ns") if isinstance(trace.get("clock_mapping"), dict) else None,
        "request_count": len(decompositions),
        "requests_with_ttft": len(ttft_values),
        "requests_with_tpot": len(tpot_values),
        "requests_with_critical_path": sum(item["critical_path"]["status"] == "available" for item in decompositions),
        "ttft_ms": _distribution(ttft_values),
        "tpot_ms": _distribution(tpot_values),
        "phase_summary": phase_summary,
        "requests": decompositions,
        "limitations": [
            "TTFT is request-root start to token_index 1 emission; TPOT is the mean interval between consecutive token emission markers.",
            "Token-index gaps, missing first tokens, or fewer than two token markers make the affected metric unavailable rather than inferred.",
            "Phase coverage is wall-clock interval union. Nested and parallel events can overlap, so phase durations are not necessarily additive.",
            "Kernel and communication are reported as subphases and may overlap prefill/decode; they are not added to the primary phase total.",
            "Unclassified gap means no primary phase event covers that wall-clock interval; it is not automatically GPU idle time.",
            "A first-token controlling dependency chain is reported only when the request root attests a complete graph and every dependency path is explicit and rooted; dependency gaps remain unclassified.",
            "The controlling chain is a trace-derived dependency observation, not proof of hardware causality or a bottleneck; trace sample percentiles are not substitutes for published benchmark percentiles.",
        ],
    }


def decompose_database(database: dict | list) -> dict:
    if isinstance(database, list):
        records = database
    elif isinstance(database, dict):
        records = database.get("records")
    else:
        raise ValueError("input must be a benchmark database object or record array")
    if not isinstance(records, list):
        raise ValueError("input must contain a records array")
    reports = [decompose_record(record) for record in records]
    decomposed = [report for report in reports if report["status"] == "decomposed"]
    return {
        "schema_version": "1.0",
        "generated_by": DERIVER,
        "source_scope": "request_level_runtime_phase_decomposition",
        "input_record_count": len(records),
        "records_with_runtime_traces": sum(report["status"] != "missing_runtime_trace" for report in reports),
        "records_with_request_events": len(decomposed),
        "request_count": sum(report["request_count"] for report in reports),
        "requests_with_ttft": sum(report["requests_with_ttft"] for report in decomposed),
        "requests_with_tpot": sum(report["requests_with_tpot"] for report in decomposed),
        "requests_with_critical_path": sum(report.get("requests_with_critical_path",0) for report in decomposed),
        "records": reports,
        "global_limitations": [
            "Trace-derived TTFT/TPOT are request-sample statistics, not substitutes for the benchmark's published aggregate metrics.",
            "Phase wall-clock coverage is non-additive when events overlap or execute concurrently.",
            "Unclassified time is not proof of GPU idle. A controlling dependency chain requires collector-attested completeness and explicit completion-dependency edges; timestamps and parent/child nesting alone are insufficient.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Benchmark database JSON or record array")
    parser.add_argument("--output", required=True, type=Path, help="Destination phase decomposition JSON; input is never overwritten")
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("input and output paths must be different")
        source = json.loads(args.input.read_text(encoding="utf-8"))
        report = decompose_database(source)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: {report['input_record_count']} records; "
        f"{report['records_with_request_events']} with request events; "
        f"{report['request_count']} requests; "
        f"{report['requests_with_ttft']} TTFT samples; "
        f"{report['requests_with_tpot']} TPOT samples. "
        "Phase overlap is retained; no causal or critical-path attribution was generated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
