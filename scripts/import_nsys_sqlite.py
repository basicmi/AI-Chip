#!/usr/bin/env python3
"""Import Nsight Systems SQLite CUDA events without inventing clock alignment.

Nsight SQLite timestamps are exporter/session nanoseconds, NOT UTC. CUDA runtime
correlationId links API launch records to kernel records but does not imply a
completed synchronization dependency or a request-level causal attribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_benchmark_results import validate_runtime_trace

DERIVER = "scripts/import_nsys_sqlite.py"
KERNEL_TABLE = "CUPTI_ACTIVITY_KIND_KERNEL"
RUNTIME_TABLE = "CUPTI_ACTIVITY_KIND_RUNTIME"
MAX_EVENTS = 100000
NCCL_PATTERN = re.compile(r"(^|[^a-z])nccl|ncclkernel|nccldev|ncclfunc", re.I)


def _columns(db, table):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
        return set()
    return {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}


def _read_rows(db, table, required, optional):
    cols = _columns(db, table)
    if not cols:
        return [], False
    missing = set(required) - cols
    if missing:
        raise ValueError(f"{table} missing required SQLite columns: {sorted(missing)}")
    select = list(required) + [col for col in optional if col in cols and col not in required]
    query = "SELECT " + ", ".join(f'"{col}"' for col in select) + f' FROM "{table}" ORDER BY start, end'
    return [dict(zip(select, row)) for row in db.execute(query)], True


def _strings(db):
    if not {"id", "value"}.issubset(_columns(db, "StringIds")):
        return {}
    return {key: value for key, value in db.execute('SELECT id, value FROM "StringIds"')}


def _valid_interval(row):
    s, e = row.get("start"), row.get("end")
    return (type(s) is int and type(e) is int and s >= 0 and e > s)


def _name(row, string_ids, fields, fallback):
    for field in fields:
        key = row.get(field)
        if isinstance(key, str) and key.strip():
            return key
        if key in string_ids and isinstance(string_ids[key], str) and string_ids[key].strip():
            return string_ids[key]
    return fallback


def _identity(row):
    device, context, stream = row["deviceId"], row["contextId"], row["streamId"]
    return f"cuda:gpu{device}:ctx{context}:stream{stream}"


def _source_anchor_mapping(value, lo, hi):
    if not isinstance(value, dict):
        raise ValueError("clock anchors file must be an object")
    if value.get("method") != "piecewise_linear":
        raise ValueError("clock mapping method must be piecewise_linear")
    anchors = value.get("anchors")
    if not isinstance(anchors, list) or len(anchors) < 2 or len(anchors) > 64:
        raise ValueError("provide 2..64 verified monotonic_ns/UTC anchors")
    if not isinstance(value.get("max_error_ns"), (int, float)) or isinstance(value["max_error_ns"], bool):
        raise ValueError("max_error_ns is required")
    # Validation additionally checks ordering, dates, uncertainty and no extrapolation.
    if any(type(a.get("monotonic_ns")) is not int for a in anchors if isinstance(a, dict)):
        raise ValueError("monotonic_ns anchors must be integers")
    if not all(isinstance(a, dict) for a in anchors):
        raise ValueError("all anchors must be objects")
    if anchors[0]["monotonic_ns"] > lo or anchors[-1]["monotonic_ns"] < hi:
        raise ValueError("verified clock anchors must contain every exported event")
    return value


def import_nsys(db_path, *, source_url, anchors=None, collected_at=None, max_events=MAX_EVENTS):
    if not isinstance(source_url, str) or not re.match(r"^https?://", source_url):
        raise ValueError("source_url must be a real HTTP(S) profiler artifact URL")
    path = Path(db_path).resolve()
    if not path.is_file():
        raise ValueError("SQLite export does not exist")
    # Read-only SQLite connection; do not modify profiler artifacts or create WAL.
    uri = "file:" + quote(str(path)) + "?mode=ro&immutable=1"
    db = sqlite3.connect(uri, uri=True)
    try:
        strings = _strings(db)
        kernels, kernel_table_present = _read_rows(
            db, KERNEL_TABLE, ("start", "end", "deviceId", "contextId", "streamId"),
            ("correlationId", "globalPid", "shortName", "demangledName", "mangledName")
        )
        runtimes, runtime_table_present = _read_rows(
            db, RUNTIME_TABLE, ("start", "end"),
            ("correlationId", "globalTid", "nameId")
        )
    finally:
        db.close()
    if not kernel_table_present:
        raise ValueError("Nsight SQLite export has no CUPTI_ACTIVITY_KIND_KERNEL table")
    if len(kernels) + len(runtimes) > max_events:
        raise ValueError(f"trace has more than {max_events} events; use a smaller profiling window")
    skipped = Counter()
    observed = []
    kernel_keys = defaultdict(list)
    for index, row in enumerate(kernels):
        if not _valid_interval(row):
            skipped["kernel_invalid_timing"] += 1
            continue
        if any(type(row[field]) is not int for field in ("deviceId", "contextId", "streamId")):
            skipped["kernel_invalid_device_identity"] += 1
            continue
        name = _name(row, strings, ("demangledName", "shortName", "mangledName"), "unresolved CUDA kernel")
        is_nccl = bool(NCCL_PATTERN.search(name))
        # Explicitly label this heuristic: not every communication kernel has NCCL in its name.
        event = {
            "event_id": f"nsys-kernel-{index}", "name": name,
            "category": "communication" if is_nccl else "kernel",
            "started_at": row["start"], "ended_at": row["end"],
            "entity_id": f"gpu{row['deviceId']}", "stream_id": _identity(row),
        }
        observed.append({
            "event": event, "source_table": KERNEL_TABLE, "source_row_index": index,
            "device_id": row["deviceId"], "context_id": row["contextId"],
            "stream_id": row["streamId"], "global_pid": row.get("globalPid"),
            "correlation_id": row.get("correlationId"),
            "communication_label_basis": "kernel_name_nccl_heuristic" if is_nccl else "not_classified_as_communication",
        })
        corr = row.get("correlationId")
        if type(corr) is int:
            kernel_keys[(corr, row.get("globalPid"))].append(event["event_id"])

    for index, row in enumerate(runtimes):
        if not _valid_interval(row):
            skipped["runtime_invalid_timing"] += 1
            continue
        name = _name(row, strings, ("nameId",), "unresolved CUDA API")
        corr, tid = row.get("correlationId"), row.get("globalTid")
        # A runtime correlation may match multiple kernels or processes.
        # Only retain a launch correlation as candidate, never as dependency.
        candidates = []
        if type(corr) is int and type(tid) is int:
            # Nsight serialized globalTid stores PID in bits 24..47.
            pid = (tid >> 24) & 0xffffff
            for (key_corr, key_pid), ids in kernel_keys.items():
                if key_corr == corr and type(key_pid) is int:
                    kernel_pid = (key_pid >> 24) & 0xffffff
                    if pid == kernel_pid:
                        candidates.extend(ids)
        elif type(corr) is int:
            # no process identity: report as unscoped, no guessed match
            skipped["runtime_correlation_missing_process_scope"] += 1
        observed.append({
            "event": {
                "event_id": f"nsys-runtime-{index}", "name": name,
                "category": "host_runtime", "started_at": row["start"], "ended_at": row["end"],
            },
            "source_table": RUNTIME_TABLE, "source_row_index": index,
            "global_tid": tid, "correlation_id": corr,
            "candidate_kernel_event_ids": sorted(set(candidates)),
            "association_basis": "same_process_cupti_correlation_id" if candidates else "no_scoped_match",
        })
    observed.sort(key=lambda item: (item["event"]["started_at"], item["event"]["ended_at"], item["event"]["event_id"]))
    if not observed:
        raise ValueError("no valid CUDA kernel or runtime API events")
    lo = min(x["event"]["started_at"] for x in observed)
    hi = max(x["event"]["ended_at"] for x in observed)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    diagnostics = {
        "kernel_rows": len(kernels), "runtime_api_rows": len(runtimes),
        "kernel_events": sum(x["source_table"] == KERNEL_TABLE for x in observed),
        "cuda_api_events": sum(x["source_table"] == RUNTIME_TABLE for x in observed),
        "nccl_name_heuristic_events": sum(x["communication_label_basis"] == "kernel_name_nccl_heuristic"
                                           for x in observed if x["source_table"] == KERNEL_TABLE),
        "cuda_api_records_with_scoped_kernel_candidates": sum(bool(x.get("candidate_kernel_event_ids"))
                                                                for x in observed),
        "skipped": dict(skipped),
    }
    report = {
        "schema_version": "1.0", "generated_by": DERIVER,
        "input_format": "nsight_systems_sqlite",
        "source_url": source_url, "artifact_sha256": sha,
        "source_timestamp_domain": "nsight_session_nanoseconds_not_utc",
        "time_window_ns": {"started_at": lo, "ended_at": hi},
        "events": observed, "diagnostics": diagnostics,
        "limitations": [
            "Nsight SQLite nanoseconds do not establish UTC without independently measured clock anchors.",
            "CUPTI correlationId identifies candidate API-to-kernel launch associations, not completion dependencies.",
            "NCCL communication classification uses name matching only and may miss other communication kernels.",
            "An NVTX range or timestamp overlap alone does not assign a GPU kernel to a request.",
            "No kernel-to-request correlation_id, token timestamps, or critical-path dependencies are invented.",
            "Per-GPU entity_id gpuN is a local Nsight device index, not a globally stable GPU UUID.",
        ],
    }
    if anchors is not None:
        mapping = _source_anchor_mapping(anchors, lo, hi)
        trace = {
            "schema_version": "1.0",
            "collector": {"name": "NVIDIA Nsight Systems SQLite", "type": "profiler_export"},
            "clock_domain": "monotonic_ns",
            "sampling": {"started_at": lo, "ended_at": hi},
            "clock_mapping": mapping,
            "provenance": {
                "source_type": "profiler_export", "source_url": source_url,
                "collected_at": collected_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "artifact_sha256": sha,
            },
            "events": [item["event"] for item in observed],
            "notes": "Profiler-only events. Anchors are user supplied, not inferred. No request, dependencies or causal attribution assigned.",
        }
        errors = validate_runtime_trace(trace, "nsys")
        if errors:
            raise ValueError("calibrated trace is invalid: " + "; ".join(errors[:6]))
        report["records"] = [{"id": "nsys-" + sha[:16], "runtime_trace": trace}]
        report["clock_alignment_status"] = "verified_anchors_supplied_by_caller"
    else:
        report["clock_alignment_status"] = "unavailable_no_verified_anchors"
        report["records"] = []
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="nsys export --type sqlite output")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-url", required=True, help="Actual HTTP(S) profiler artifact URL")
    parser.add_argument("--clock-anchors", type=Path, help="Verified clock mapping JSON; omit to keep raw session clock")
    parser.add_argument("--max-events", type=int, default=MAX_EVENTS)
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("input and output paths cannot be the same")
        mapping = json.loads(args.clock_anchors.read_text(encoding="utf-8")) if args.clock_anchors else None
        result = import_nsys(args.input, source_url=args.source_url, anchors=mapping, max_events=args.max_events)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, sqlite3.DatabaseError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {len(result['events'])} CUDA events; alignment={result['clock_alignment_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
