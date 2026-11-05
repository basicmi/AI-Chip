#!/usr/bin/env python3
"""Validate data/compatibility.json with Python's standard library only."""
import json
import re
import sys
from pathlib import Path
from datetime import date
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "compatibility.json"
ALLOWED_STATUS = {
    "upstream_supported", "vendor_plugin_supported", "vendor_framework",
    "experimental", "in_progress", "needs_review", "vendor_reported",
}
ALLOWED_LAYERS = {
    "framework", "compiler", "kernel_dsl", "operator_library", "serving",
    "communication", "runtime", "model_porting", "benchmark", "other",
}
ALLOWED_MAINTAINERS = {
    "upstream_project", "project_community", "vendor_plugin",
    "vendor", "community", "research",
}
ALLOWED_EVIDENCE = {
    "upstream_docs", "repository_readme", "vendor_announcement",
    "release_note", "ci", "benchmark", "paper", "issue", "other",
}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
errors = []

def check(condition, message):
    if not condition:
        errors.append(message)

def valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False

def valid_url(value):
    try:
        p = urlparse(value)
        return p.scheme in {"https", "http"} and bool(p.netloc)
    except (TypeError, ValueError):
        return False

def require(obj, keys, where):
    check(isinstance(obj, dict), f"{where}: expected object")
    if not isinstance(obj, dict):
        return
    for key in keys:
        check(key in obj, f"{where}: missing required field {key}")

def main():
    try:
        db = json.loads(DATA.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot parse {DATA}: {exc}", file=sys.stderr)
        return 2

    require(db, ["schema_version", "database_version", "last_reviewed",
                 "scope", "status_definitions", "platforms", "integrations"], "root")
    if not isinstance(db, dict):
        return 2
    check(db.get("schema_version") == "1.0", "root: schema_version must be 1.0")
    check(valid_date(db.get("last_reviewed")), "root: invalid last_reviewed date")
    check(isinstance(db.get("status_definitions"), dict), "status_definitions must be object")
    check(isinstance(db.get("platforms"), list) and db["platforms"], "platforms must be non-empty array")
    check(isinstance(db.get("integrations"), list) and db["integrations"], "integrations must be non-empty array")

    platform_ids = set()
    for i, p in enumerate(db.get("platforms", [])):
        where = f"platforms[{i}]"
        require(p, ["id", "vendor", "name", "hardware_scope", "vendor_stack", "evidence_urls"], where)
        if not isinstance(p, dict):
            continue
        pid = p.get("id")
        check(isinstance(pid, str) and ID_RE.fullmatch(pid or "") is not None, f"{where}: invalid id")
        check(pid not in platform_ids, f"{where}: duplicate id {pid}")
        platform_ids.add(pid)
        check(isinstance(p.get("hardware_scope"), list) and bool(p["hardware_scope"]), f"{where}: hardware_scope must be non-empty")
        check(isinstance(p.get("vendor_stack"), list), f"{where}: vendor_stack must be array")
        urls = p.get("evidence_urls")
        check(isinstance(urls, list) and bool(urls), f"{where}: evidence_urls must be non-empty")
        if isinstance(urls, list):
            for u in urls:
                check(valid_url(u), f"{where}: invalid evidence URL {u!r}")

    integration_ids = set()
    for i, entry in enumerate(db.get("integrations", [])):
        where = f"integrations[{i}]"
        required = ["id", "platform_id", "layer", "project", "project_url",
                    "maintainer_type", "status", "confidence", "hardware_scope",
                    "versions", "limitations", "last_checked", "evidence"]
        require(entry, required, where)
        if not isinstance(entry, dict):
            continue
        iid = entry.get("id")
        check(isinstance(iid, str) and ID_RE.fullmatch(iid or "") is not None, f"{where}: invalid id")
        check(iid not in integration_ids, f"{where}: duplicate id {iid}")
        integration_ids.add(iid)
        check(entry.get("platform_id") in platform_ids, f"{where}: unknown platform_id {entry.get('platform_id')!r}")
        check(entry.get("status") in ALLOWED_STATUS, f"{where}: invalid status")
        check(entry.get("layer") in ALLOWED_LAYERS, f"{where}: invalid layer")
        check(entry.get("maintainer_type") in ALLOWED_MAINTAINERS, f"{where}: invalid maintainer_type")
        check(entry.get("confidence") in {"high", "medium", "low"}, f"{where}: invalid confidence")
        check(valid_url(entry.get("project_url")), f"{where}: invalid project_url")
        check(valid_date(entry.get("last_checked")), f"{where}: invalid last_checked")
        check(isinstance(entry.get("versions"), dict), f"{where}: versions must be object")
        check(isinstance(entry.get("limitations"), str) and bool(entry["limitations"].strip()), f"{where}: limitations must be non-empty")
        evidence = entry.get("evidence")
        check(isinstance(evidence, list) and bool(evidence), f"{where}: evidence must be non-empty")
        if isinstance(evidence, list):
            for j, ev in enumerate(evidence):
                ewhere = f"{where}.evidence[{j}]"
                require(ev, ["type", "url", "checked_at", "claim"], ewhere)
                if not isinstance(ev, dict):
                    continue
                check(ev.get("type") in ALLOWED_EVIDENCE, f"{ewhere}: invalid type")
                check(valid_url(ev.get("url")), f"{ewhere}: invalid URL")
                check(valid_date(ev.get("checked_at")), f"{ewhere}: invalid checked_at")
                check(isinstance(ev.get("claim"), str) and bool(ev["claim"].strip()), f"{ewhere}: claim must be non-empty")

    if errors:
        print(f"FAIL: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {len(platform_ids)} platforms, {len(integration_ids)} integrations; all IDs, references, dates, URLs, enums and evidence records are valid.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
