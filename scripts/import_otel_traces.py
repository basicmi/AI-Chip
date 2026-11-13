#!/usr/bin/env python3
"""Import OpenTelemetry OTLP JSON exports into AI-Chip runtime-trace records.

Offline file importer only. It does not receive OTLP or synthesize missing events.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_benchmark_results import validate_runtime_trace

DERIVER = "scripts/import_otel_traces.py"
CATEGORIES = {
    "queue_wait", "batch_wait", "prefill", "decode", "kernel",
    "communication", "host_runtime", "other", "cpu_scheduling",
    "communication_wait",
}


def _value(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    for key in ("stringValue", "intValue", "doubleValue", "boolValue"):
        if key in item:
            raw = item[key]
            if key == "intValue":
                try:
                    return int(raw)
                except (TypeError, ValueError):
                    return raw
            if key == "doubleValue":
                try:
                    return float(raw)
                except (TypeError, ValueError):
                    return raw
            return raw
    if "arrayValue" in item:
        return [_value(v.get("value")) for v in item["arrayValue"].get("values", []) if isinstance(v, dict)]
    if "kvlistValue" in item:
        return _attrs(item["kvlistValue"].get("values", []))
    return None


def _attrs(items: Any) -> dict:
    if isinstance(items, dict):
        return items
    result = {}
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("key"), str):
                result[item["key"]] = _value(item.get("value"))
    return result


def _nano(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if number > 0 else None


def _utc(ns: int) -> str:
    seconds, nanos = divmod(ns, 1_000_000_000)
    instant = datetime.fromtimestamp(seconds, timezone.utc) + timedelta(microseconds=nanos // 1000)
    return instant.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _groups(resource_spans):
    for group in resource_spans:
        if not isinstance(group, dict):
            continue
        resource = _attrs((group.get("resource") or {}).get("attributes", []))
        scopes = group.get("scopeSpans", group.get("instrumentationLibrarySpans", []))
        for scope_group in scopes if isinstance(scopes, list) else []:
            if not isinstance(scope_group, dict):
                continue
            scope = scope_group.get("scope") or scope_group.get("instrumentationLibrary") or {}
            for span in scope_group.get("spans", []):
                if isinstance(span, dict):
                    yield resource, scope, span


def _is_server(span, attrs):
    kind = span.get("kind")
    return kind == 2 or kind == "SPAN_KIND_SERVER" or str(attrs.get("span.kind", "")).lower() in {
        "server", "span_kind_server"
    }


def _category(span, attrs, mapping):
    for key in ("ai_chip.runtime.category", "runtime.category", "vllm.runtime.category"):
        value = attrs.get(key)
        if isinstance(value, str) and value.strip().lower() in CATEGORIES:
            return value.strip().lower(), "explicit_attribute"
    name = str(span.get("name", "")).strip()
    if name in mapping:
        return mapping[name], "exact_name_map"
    name = name.lower().replace("-", "_").replace(" ", "_")
    rules = (
        (r"communication[_ .:-]*wait|nccl.*wait", "communication_wait"),
        (r"queue|wait_in_queue", "queue_wait"),
        (r"batch.*wait|wait.*batch", "batch_wait"),
        (r"prefill", "prefill"), (r"decode", "decode"),
        (r"kernel|cuda.*launch|gpu.*kernel", "kernel"),
        (r"nccl|all_reduce|all_gather|reduce_scatter|collective|communication|nvlink", "communication"),
        (r"cpu.*sched|sched.*cpu", "cpu_scheduling"),
        (r"host.*runtime|api_server|engine.*step", "host_runtime"),
    )
    for pattern, category in rules:
        if re.search(pattern, name):
            return category, "span_name_heuristic"
    return "other", "unclassified"


def _identity(attrs, keys):
    for key in keys:
        value = attrs.get(key)
        if isinstance(value, (str, int)) and not isinstance(value, bool) and str(value).strip():
            return str(value).strip()
    return None


def import_otlp_json(payload, *, source_url, artifact_sha256=None, collected_at=None,
                      service_name=None, root_span_name=None, category_map=None):
    if not isinstance(payload, dict) or not isinstance(payload.get("resourceSpans"), list):
        raise ValueError("input must be OTLP JSON with resourceSpans[]")
    if not isinstance(source_url, str) or not re.match(r"^https?://", source_url):
        raise ValueError("--source-url must be an HTTP(S) trace/artifact URL")
    mapping = category_map or {}
    if any(not isinstance(k, str) or not isinstance(v, str) or v not in CATEGORIES for k, v in mapping.items()):
        raise ValueError("category map must map exact span names to supported runtime categories")

    counts, category_counts = Counter(), Counter()
    traces = defaultdict(dict)
    services = set()
    for resource, scope, span in _groups(payload["resourceSpans"]):
        counts["spans_seen"] += 1
        trace_id, span_id = span.get("traceId"), span.get("spanId")
        if not isinstance(trace_id, str) or not trace_id or not isinstance(span_id, str) or not span_id:
            counts["spans_missing_identity"] += 1
            continue
        trace_id, span_id = trace_id.lower(), span_id.lower()
        if span_id in traces[trace_id]:
            counts["duplicate_span_ids"] += 1
            continue
        start, end = _nano(span.get("startTimeUnixNano")), _nano(span.get("endTimeUnixNano"))
        if start is None or end is None or end <= start:
            counts["spans_missing_or_nonpositive_timing"] += 1
            continue
        attrs = _attrs(span.get("attributes", []))
        traces[trace_id][span_id] = {
            "span": span, "attrs": attrs, "start": start, "end": end,
            "parent": str(span.get("parentSpanId", "")).lower(),
            "resource": resource, "service": resource.get("service.name"),
        }
        if isinstance(resource.get("service.name"), str):
            services.add(resource["service.name"])

    root_re = re.compile(root_span_name) if root_span_name else None
    records = []
    for trace_id, span_map in sorted(traces.items()):
        selected = [
            sid for sid, item in span_map.items()
            if (not service_name or item["service"] == service_name)
            and (bool(root_re.search(str(item["span"].get("name", ""))) if root_re else _is_server(item["span"], item["attrs"])))
        ]
        selected_set = set(selected)
        roots = []
        for sid in selected:
            parent, seen, nested = span_map[sid]["parent"], set(), False
            while parent in span_map and parent not in seen:
                if parent in selected_set:
                    nested = True
                    break
                seen.add(parent)
                parent = span_map[parent]["parent"]
            if not nested:
                roots.append(sid)

        children = defaultdict(list)
        for sid, item in span_map.items():
            if item["parent"] in span_map:
                children[item["parent"]].append(sid)

        for root_id in roots:
            root = span_map[root_id]
            start, end = root["start"], root["end"]
            descendants, stack, visited = [], [root_id], set()
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                descendants.append(current)
                stack.extend(reversed(children.get(current, [])))
            included = set()
            for sid in descendants:
                item = span_map[sid]
                if item["start"] < start or item["end"] > end:
                    counts["spans_outside_request_window"] += 1
                else:
                    included.add(sid)
            if root_id not in included:
                continue
            if len(included) > 100000:
                raise ValueError(f"trace {trace_id} request {root_id} exceeds 100000 spans")

            correlation = f"{trace_id}:{root_id}"
            event_ids = {sid: f"otel-{trace_id}-{sid}" for sid in included}
            events = []
            ordered = sorted(included, key=lambda sid: (span_map[sid]["start"], 0 if sid == root_id else 1, sid))
            for sid in ordered:
                item, span, attrs = span_map[sid], span_map[sid]["span"], span_map[sid]["attrs"]
                is_root = sid == root_id
                category, method = ("request", "root_span") if is_root else _category(span, attrs, mapping)
                event = {
                    "event_id": event_ids[sid], "name": str(span.get("name") or "unnamed OpenTelemetry span"),
                    "category": category, "started_at": _utc(item["start"]), "ended_at": _utc(item["end"]),
                    "correlation_id": correlation,
                }
                if not is_root and item["parent"] in included:
                    parent = span_map[item["parent"]]
                    if parent["start"] <= item["start"] and parent["end"] >= item["end"]:
                        event["parent_event_id"] = event_ids[item["parent"]]
                    else:
                        counts["parent_links_omitted_for_noncontainment"] += 1
                entity = _identity(attrs, ("ai_chip.entity_id", "device.id", "gpu.id", "cuda.device_id", "device.uuid"))
                stream = _identity(attrs, ("ai_chip.stream_id", "cuda.stream.id", "gpu.stream.id"))
                if entity:
                    event["entity_id"] = entity
                if stream:
                    event["stream_id"] = stream
                if not is_root:
                    category_counts[f"{category}:{method}"] += 1
                events.append(event)

                for index, span_event in enumerate(span.get("events", []) if isinstance(span.get("events", []), list) else []):
                    if not isinstance(span_event, dict):
                        continue
                    event_attrs = _attrs(span_event.get("attributes", []))
                    name = str(span_event.get("name", "")).strip()
                    if event_attrs.get("ai_chip.event.category", event_attrs.get("event.category")) != "token_emit" and name.lower() not in {
                        "token_emit", "gen_ai.token.emit"
                    }:
                        continue
                    token_index = event_attrs.get("ai_chip.token_index", event_attrs.get("token_index"))
                    if isinstance(token_index, bool) or not isinstance(token_index, int) or token_index < 1:
                        counts["token_events_skipped_without_valid_index"] += 1
                        continue
                    token_ns = _nano(span_event.get("timeUnixNano"))
                    if token_ns is None or token_ns < start or token_ns > end:
                        counts["token_events_skipped_outside_request_window"] += 1
                        continue
                    stamp = _utc(token_ns)
                    events.append({
                        "event_id": f"{event_ids[sid]}-event-{index}", "name": name or "token_emit",
                        "category": "token_emit", "started_at": stamp, "ended_at": stamp,
                        "token_index": token_index, "correlation_id": correlation,
                        "parent_event_id": event_ids[sid],
                    })
                    counts["token_emit_markers_imported"] += 1

            events.sort(key=lambda e: (e["started_at"], 0 if e["category"] == "request" else 1, e["event_id"]))
            trace = {
                "schema_version": "1.0",
                "collector": {
                    "name": "OpenTelemetry OTLP JSON importer",
                    "version": str(root["resource"]["service.version"]) if root["resource"].get("service.version") is not None else None,
                    "type": "runtime_trace",
                },
                "clock_domain": "utc_wall_clock",
                "sampling": {"started_at": _utc(start), "ended_at": _utc(end)},
                "provenance": {
                    "source_type": "runtime_trace_export", "source_url": source_url,
                    "collected_at": collected_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    **({"artifact_sha256": artifact_sha256} if artifact_sha256 else {}),
                },
                "events": events,
                "notes": "Imported from OTLP JSON. Nanosecond timestamps are normalized to UTC at microsecond precision. Span-name categories may be heuristic. No dependency edges or token markers are synthesized.",
            }
            errors = validate_runtime_trace(trace, f"records[{trace_id}:{root_id}]")
            if errors:
                raise ValueError("generated trace failed validation: " + "; ".join(errors[:8]))
            records.append({"id": f"otel-{trace_id}-{root_id}", "runtime_trace": trace})
            counts["request_roots_imported"] += 1
            counts["events_imported"] += len(events)

    if not records:
        selector = f"root span regex {root_span_name!r}" if root_span_name else "OTel SPAN_KIND_SERVER spans"
        raise ValueError(f"no request roots found using {selector}; check export or pass --root-span-name")
    return {
        "schema_version": "1.0", "generated_by": DERIVER, "source_format": "opentelemetry_otlp_json",
        "source_url": source_url, "service_filter": service_name, "root_span_name_regex": root_span_name,
        "records": records,
        "diagnostics": {
            "counts": dict(sorted(counts.items())), "category_assignment": dict(sorted(category_counts.items())),
            "services_seen": sorted(services),
            "limitations": [
                "Offline OTLP JSON file importer; not a live OTLP receiver.",
                "Request roots are server-kind spans unless --root-span-name is supplied.",
                "Name-based categories are heuristics unless an explicit category attribute or exact-name map is used.",
                "No dependency edges are inferred from parentSpanId, timestamps or nesting.",
                "Token markers are imported only from explicit token_emit span events with positive token_index values.",
                "Aggregate completion-token counts and TTFT attributes do not create token timestamps or phase intervals.",
                "Timestamps are normalized from nanoseconds to UTC at microsecond precision.",
                "Without explicit token markers, trace-derived TTFT and TPOT remain unavailable.",
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="OTLP JSON export file")
    parser.add_argument("--output", required=True, type=Path, help="Normalized trace records JSON")
    parser.add_argument("--source-url", required=True, help="HTTP(S) source trace or trace UI URL")
    parser.add_argument("--service-name", help="Exact resource service.name to select request roots")
    parser.add_argument("--root-span-name", help="Regex selecting request roots instead of SpanKind.SERVER")
    parser.add_argument("--category-map", type=Path, help="JSON object mapping exact span names to runtime categories")
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("input and output paths must differ")
        raw = args.input.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        mapping = json.loads(args.category_map.read_text(encoding="utf-8")) if args.category_map else {}
        if not isinstance(mapping, dict):
            raise ValueError("--category-map must contain a JSON object")
        result = import_otlp_json(
            payload, source_url=args.source_url, artifact_sha256=hashlib.sha256(raw).hexdigest(),
            service_name=args.service_name, root_span_name=args.root_span_name, category_map=mapping,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    counts = result["diagnostics"]["counts"]
    print(
        f"PASS: imported {counts.get('request_roots_imported', 0)} request roots, "
        f"{counts.get('events_imported', 0)} events and "
        f"{counts.get('token_emit_markers_imported', 0)} explicit token markers; no dependencies inferred."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
