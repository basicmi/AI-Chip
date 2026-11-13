#!/usr/bin/env python3
"""Import time-stamped DCGM Exporter Prometheus snapshots as hardware evidence.

A scrape time is an observation timestamp, not a known instant of GPU execution.
Do not infer kernel/phase-level alignment, HBM bandwidth, or GPU bottlenecks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hardware_counter_mapping import load_catalog, normalize_counter
from validate_benchmark_results import validate_hardware_evidence

MAX_RESPONSE_BYTES = 4 * 1024 * 1024
METRIC_RE = re.compile(r'^([A-Za-z_:][A-Za-z0-9_:]*)(\{.*\})?\s+(\S+)(?:\s+(\S+))?$')
LABEL_RE = re.compile(r'\s*([a-zA-Z_][a-zA-Z0-9_]*)="((?:\\.|[^"\\])*)"\s*(?:,|$)')
SAMPLE_FIELDS = {"DCGM_FI_PROF_SM_UTIL_RATIO", "DCGM_FI_PROF_TENSOR_UTIL_RATIO",
                 "DCGM_FI_PROF_DRAM_UTIL_RATIO", "DCGM_FI_DEV_BOARD_POWER_WATTS",
                 "DCGM_FI_DEV_FB_USED", "DCGM_FI_DEV_SM_CLOCK", "DCGM_FI_DEV_MEM_CLOCK",
                 "DCGM_FI_DEV_GPU_TEMP_CELSIUS"}


def _labels(src):
    if not src:
        return {}
    inside = src[1:-1]
    result, offset = {}, 0
    while offset < len(inside):
        match = LABEL_RE.match(inside, offset)
        if not match:
            raise ValueError("invalid Prometheus label syntax")
        key, encoded = match.group(1), match.group(2)
        if key in result:
            raise ValueError("duplicate Prometheus label " + key)
        result[key] = encoded.replace(r'\"', '"').replace(r'\\', '\\').replace(r'\n', '\n')
        offset = match.end()
    return result


def parse_prometheus(body):
    """Only parse simple Prometheus text samples; fail on unsupported ambiguous rows."""
    records = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = METRIC_RE.fullmatch(line)
        if not match:
            raise ValueError("unsupported Prometheus sample row: " + line[:80])
        name, raw_labels, raw_value, sample_timestamp = match.groups()
        if sample_timestamp is not None:
            raise ValueError("exporter-supplied timestamps are unsupported; capture receipt UTC explicitly")
        try:
            value = float(raw_value)
        except ValueError:
            raise ValueError("invalid Prometheus numeric value in " + name)
        records.append({"name": name, "labels": _labels(raw_labels), "value": value})
    return records


def _dt(value):
    if not isinstance(value, str):
        raise ValueError("capture timestamp must be timezone-aware ISO 8601")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("capture timestamp must be timezone-aware ISO 8601")
    if dt.utcoffset() is None:
        raise ValueError("capture timestamp requires UTC offset")
    return dt.astimezone(timezone.utc)


def _utc(dt):
    return dt.isoformat(timespec="microseconds").replace("+00:00", "Z")


def capture(endpoint, *, count, interval_seconds, timeout_seconds=5, max_bytes=MAX_RESPONSE_BYTES):
    if not isinstance(endpoint, str) or not endpoint.startswith(("http://", "https://")):
        raise ValueError("endpoint must be HTTP(S)")
    if count < 2 or count > 10000 or interval_seconds <= 0 or timeout_seconds <= 0:
        raise ValueError("count must be 2..10000 and timeouts/intervals positive")
    snapshots = []
    for index in range(count):
        req = urllib.request.Request(endpoint, headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError("DCGM scrape payload exceeds byte limit")
            text = body.decode("utf-8")
        # Capture time is when the response was received, not device sampling instant.
        timestamp = _utc(datetime.now(timezone.utc))
        parse_prometheus(text)
        snapshots.append({"captured_at": timestamp, "body": text})
        if index + 1 < count:
            time.sleep(interval_seconds)
    return {"schema_version": "1.0", "source_format": "dcgm_exporter_prometheus_text",
            "endpoint": endpoint, "snapshots": snapshots,
            "capture_time_semantics": "response_receipt_utc_not_exact_device_sample_instant"}


def import_dcgm(capture_data, *, source_url, artifact_sha256=None, collected_at=None,
                device_model=None, catalog=None):
    if not isinstance(capture_data, dict) or capture_data.get("source_format") != "dcgm_exporter_prometheus_text":
        raise ValueError("expected DCGM exporter capture JSON")
    if not isinstance(source_url, str) or not source_url.startswith(("http://", "https://")):
        raise ValueError("source_url must be HTTP(S)")
    snapshots = capture_data.get("snapshots")
    if not isinstance(snapshots, list) or len(snapshots) < 2:
        raise ValueError("at least two time-stamped DCGM scrape snapshots are required")
    catalog = catalog or load_catalog()
    mapped = {m["source_metric"] for m in catalog["mappings"]
              if m["source_id"] == "nvidia-dcgm" and m["mapping_status"] != "reference_only"}
    previous = None
    per_device = defaultdict(lambda: defaultdict(list))
    observations = Counter()
    times = []
    for index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("body"), str):
            raise ValueError(f"snapshots[{index}]: body must be text")
        current = _dt(snapshot.get("captured_at"))
        if previous is not None and current <= previous:
            raise ValueError("snapshot timestamps must be strictly increasing")
        previous = current
        times.append(current)
        seen = set()
        for sample in parse_prometheus(snapshot["body"]):
            name, labels, value = sample["name"], sample["labels"], sample["value"]
            if name not in SAMPLE_FIELDS or name not in mapped:
                observations["unmapped_or_unsupported_samples"] += 1
                continue
            identity = labels.get("UUID") or labels.get("uuid")
            if not identity:
                # Local GPU index may reorder across runs; keep it distinct from UUID.
                gpu = labels.get("gpu")
                identity = "local-gpu:" + gpu if gpu is not None else None
            if not identity:
                observations["missing_gpu_identity"] += 1
                continue
            if not math.isfinite(value) or value < 0:
                observations["invalid_or_sentinel_value"] += 1
                continue
            key = (identity, name)
            if key in seen:
                raise ValueError(f"duplicate metric {name} for {identity} in snapshot {index}")
            seen.add(key)
            per_device[identity][name].append((index, value))
            observations["valid_source_samples"] += 1

    interval_ms = (times[-1] - times[0]).total_seconds() * 1000 / (len(times) - 1)
    records = []
    for entity, by_name in sorted(per_device.items()):
        metrics, excluded = [], []
        for name, samples in sorted(by_name.items()):
            # Missing samples must not be papered over as a complete time series.
            if len(samples) != len(snapshots) or [i for i, _ in samples] != list(range(len(snapshots))):
                excluded.append({"source_name": name, "reason": "missing_samples"})
                continue
            values = [v for _, v in samples]
            result = normalize_counter("nvidia-dcgm", name, sum(values) / len(values),
                                       entity_id=entity, aggregation="mean", catalog=catalog)
            if not result["mapped"]:
                excluded.append({"source_name": name, "reason": result["reason"]})
                continue
            metric = result["metric"]
            # No metric-specific sampling_window: scrape receipt times do not establish
            # phase-contained sampling windows, so phase joins must remain ineligible.
            metric["mapping_note"] += " Arithmetic mean of scrape observations; receipt timestamps are not GPU sample boundaries."
            metrics.append(metric)
        if not metrics:
            observations["devices_without_complete_supported_series"] += 1
            continue
        evidence = {
            "schema_version": "1.0",
            "collector": {"name": "NVIDIA DCGM Exporter", "type": "device_telemetry"},
            "system_scope": {"scope_type": "per_gpu", "device_count": 1,
                             **({"device_model": device_model} if device_model else {})},
            "sampling": {"started_at": _utc(times[0]), "ended_at": _utc(times[-1]),
                         "sample_interval_ms": interval_ms, "sample_count": len(snapshots)},
            "provenance": {"source_type": "telemetry_export", "source_url": source_url,
                           "collected_at": collected_at or _utc(datetime.now(timezone.utc)),
                           **({"artifact_sha256": artifact_sha256} if artifact_sha256 else {})},
            "metrics": metrics,
            "notes": "Scrape-observation arithmetic means; not time-weighted utilization. No exact device sample windows, GPU phase join or HBM bandwidth is inferred.",
        }
        errors = validate_hardware_evidence({"hardware_evidence": evidence}, entity)
        if errors:
            raise ValueError("generated hardware evidence failed validation: " + "; ".join(errors[:5]))
        records.append({"id": "dcgm-" + hashlib.sha256(entity.encode()).hexdigest()[:16],
                        "device_identity": entity, "hardware_evidence": evidence,
                        "excluded_series": excluded})
    if not records:
        raise ValueError("no complete supported DCGM metric series; no evidence was fabricated")
    return {"schema_version": "1.0", "generated_by": "scripts/import_dcgm_telemetry.py",
            "source_format": "dcgm_exporter_prometheus_text", "records": records,
            "observation_diagnostics": dict(observations),
            "limitations": [
                "Only cataloged DCGM gauges and activity ratios are normalized.",
                "No GPU memory bandwidth is inferred from DRAM activity ratio.",
                "Scrape receipt timestamps are not GPU sample times; no phase alignment is claimed.",
                "Arithmetic means of observed samples are not time-weighted workload averages.",
                "GPU UUID preferred; local gpu indices do not establish cross-collector identity.",
                "Missing series or sentinel values are excluded, not interpolated.",
                "No bottleneck verdict or benchmark performance claim is generated.",
            ]}


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, help="Captured DCGM JSON; required for import mode")
    p.add_argument("--endpoint", help="DCGM exporter /metrics endpoint for capture mode")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--interval-seconds", type=float, default=1)
    p.add_argument("--capture-output", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--source-url", help="Actual artifact URL for hardware evidence provenance")
    p.add_argument("--device-model")
    args = p.parse_args()
    try:
        if args.endpoint:
            if args.input or not args.capture_output:
                raise ValueError("capture mode requires --capture-output and excludes --input")
            result = capture(args.endpoint, count=args.count, interval_seconds=args.interval_seconds)
            _write_json(args.capture_output, result)
            print(f"PASS: captured {len(result['snapshots'])} DCGM snapshots to {args.capture_output}")
            return 0
        if not args.input or not args.output or not args.source_url:
            raise ValueError("import mode requires --input, --output, and --source-url")
        if args.input.resolve() == args.output.resolve():
            raise ValueError("input and output must differ")
        raw = args.input.read_bytes()
        result = import_dcgm(json.loads(raw), source_url=args.source_url,
                             artifact_sha256=hashlib.sha256(raw).hexdigest(),
                             device_model=args.device_model)
        _write_json(args.output, result)
    except (ValueError, OSError, UnicodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {len(result['records'])} devices with validated DCGM evidence; no phase attribution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
