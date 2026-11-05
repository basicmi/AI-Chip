#!/usr/bin/env python3
"""Validate workload taxonomy and evidence-scoped hardware/software paths."""
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "workloads.json"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STATUSES = {"integration_only", "vendor_reported", "workload_tested", "benchmark_reported", "independently_benchmarked"}
CATEGORIES = {"llm_inference", "llm_training", "model_porting", "multimodal_inference", "retrieval", "generative_inference", "edge_inference"}
ERRORS = []

def check(ok, message):
    if not ok:
        ERRORS.append(message)

def valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False

def valid_url(value):
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except (TypeError, ValueError):
        return False

def main():
    try:
        db = json.loads(DATA.read_text(encoding="utf-8"))
        compatibility = json.loads((ROOT / "data" / "compatibility.json").read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot parse workload or compatibility data: {exc}", file=sys.stderr)
        return 2
    check(db.get("schema_version") == "1.0", "schema_version must be 1.0")
    check(valid_date(db.get("last_reviewed")), "invalid last_reviewed date")
    workloads = db.get("workloads", [])
    paths = db.get("paths", [])
    check(isinstance(workloads, list) and bool(workloads), "workloads must be a non-empty array")
    check(isinstance(paths, list), "paths must be an array")
    wids, pids, iids = set(), {p.get("id") for p in compatibility.get("platforms", [])}, {i.get("id") for i in compatibility.get("integrations", [])}
    for index, w in enumerate(workloads):
        wid = w.get("id")
        check(isinstance(wid, str) and bool(ID_RE.fullmatch(wid)), f"workloads[{index}]: invalid id")
        check(wid not in wids, f"workloads[{index}]: duplicate id {wid}")
        wids.add(wid)
        check(w.get("category") in CATEGORIES, f"workloads[{index}]: invalid category")
        for field in ("representative_models", "key_dimensions", "metrics_to_report"):
            check(isinstance(w.get(field), list) and bool(w[field]), f"workloads[{index}]: {field} must be non-empty")
    pathids = set()
    for index, path in enumerate(paths):
        pid = path.get("id")
        check(isinstance(pid, str) and bool(ID_RE.fullmatch(pid)), f"paths[{index}]: invalid id")
        check(pid not in pathids, f"paths[{index}]: duplicate id {pid}")
        pathids.add(pid)
        check(path.get("platform_id") in pids, f"paths[{index}]: unknown platform")
        check(path.get("workload_id") in wids, f"paths[{index}]: unknown workload")
        check(path.get("status") in STATUSES, f"paths[{index}]: invalid evidence status")
        check(bool(path.get("integration_ids")), f"paths[{index}]: integration_ids must be non-empty")
        for iid in path.get("integration_ids", []):
            check(iid in iids, f"paths[{index}]: unknown integration {iid}")
        check(isinstance(path.get("metrics"), list), f"paths[{index}]: metrics must be an array")
        check(valid_date(path.get("last_checked")), f"paths[{index}]: invalid last_checked")
        for metric in path.get("metrics", []):
            check(isinstance(metric.get("value"), (int, float)), f"paths[{index}]: metric value must be numeric")
            check(valid_url(metric.get("source_url")), f"paths[{index}]: invalid metric source URL")
            check(valid_date(metric.get("checked_at")), f"paths[{index}]: invalid metric date")
            check(metric.get("evidence_type") in {"independent", "vendor", "project", "community"}, f"paths[{index}]: invalid metric evidence type")
        if path.get("status") == "integration_only":
            check(not path.get("metrics"), f"paths[{index}]: integration-only path must not imply metrics")
    if ERRORS:
        print(f"FAIL: {len(ERRORS)} validation error(s)")
        for error in ERRORS:
            print("- " + error)
        return 1
    print(f"PASS: {len(workloads)} workloads, {len(paths)} execution paths; references, IDs, statuses and metric evidence are valid.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
