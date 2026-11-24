#!/usr/bin/env python3
"""Build and verify a human-approved append-only benchmark result proposal.

The first adapter accepts one result for an already registered source. It never
imports data from the network, infers missing measurements, or edits a checkout.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import math
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = "data/benchmark-results.json"
RECORD_REQUIRED = {
    "id", "source_id", "source_class", "evidence_level", "benchmark_suite",
    "benchmark_version", "publication_date", "submitter", "accelerator_vendor",
    "platform_id", "product_id", "system_type", "system_name", "division",
    "availability", "model", "scenario", "result_value", "result_unit",
    "accuracy_text", "inferred", "power_metrics_available", "design_power_watts",
    "system", "software", "notes", "compliance", "errors", "weight_data_types",
    "source_record_key", "source_location", "source_url", "dataset_url", "release_url",
}
OPTIONAL_RECORD_FIELDS = {
    "detail_url", "model_display_name", "workload", "configuration", "metrics",
    "power_measurement_valid", "normalized_metrics", "cpu_power_measurement_valid",
    "gpu_power_metrics_available", "cpu_power_metrics_available",
    "power_measurement_status", "cpu_power_measurement_status",
    "hardware_evidence", "runtime_trace",
}
APPROVAL_FIELDS = {
    "schema_version", "approval_id", "reviewer", "reviewed_at", "decision",
    "source_id", "record", "review_notes",
}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_CLASSES = {
    "standardized_public_submission", "third_party_public_benchmark",
    "vendor_reported", "independent_measurement", "research_evaluation",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_json(value):
    return digest_bytes(canonical(value).encode("utf-8"))


def require_text(value, field, minimum=1):
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ValueError(field + " must contain at least " + str(minimum) + " characters")


def require_slug(value, field):
    if not isinstance(value, str) or not SLUG.fullmatch(value):
        raise ValueError(field + " must be a lowercase slug")


def require_url(value, field):
    try:
        parsed = urlsplit(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(field + " must be an HTTPS URL") from exc
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(field + " must be an HTTPS URL without embedded credentials")


def require_date(value, field, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str):
        raise ValueError(field + " must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(field + " must be an ISO date") from exc


def validate_approval(approval):
    if not isinstance(approval, dict) or set(approval) != APPROVAL_FIELDS:
        raise ValueError("Approval Manifest does not match the exact benchmark-result schema")
    if approval["schema_version"] != "1.0" or approval["decision"] != "approved_new_benchmark_result":
        raise ValueError("requires approved_new_benchmark_result decision")
    require_slug(approval["approval_id"], "approval_id")
    require_slug(approval["source_id"], "source_id")
    require_text(approval["reviewer"], "reviewer")
    require_text(approval["review_notes"], "review_notes", 30)
    require_date(approval["reviewed_at"], "reviewed_at")
    reviewed = date.fromisoformat(approval["reviewed_at"])
    if reviewed > datetime.now(timezone.utc).date():
        raise ValueError("reviewed_at cannot be in the future")

    record = approval["record"]
    if not isinstance(record, dict) or not RECORD_REQUIRED <= set(record) or not set(record) <= RECORD_REQUIRED | OPTIONAL_RECORD_FIELDS:
        raise ValueError("record does not match the supported benchmark-result fields")
    require_slug(record["id"], "record.id")
    if record["source_id"] != approval["source_id"]:
        raise ValueError("record.source_id must equal Approval Manifest source_id")
    if record["source_class"] not in SOURCE_CLASSES:
        raise ValueError("record.source_class is invalid")
    if record["evidence_level"] != record["source_class"]:
        raise ValueError("evidence_level must preserve the source class; no evidence promotion is allowed")
    for field in ("benchmark_suite", "submitter", "system_type", "system_name", "division",
                  "availability", "model", "scenario", "source_record_key"):
        require_text(record[field], "record." + field)
    if record["publication_date"] is not None:
        require_date(record["publication_date"], "record.publication_date")
    if record["publication_date"] and date.fromisoformat(record["publication_date"]) > reviewed:
        raise ValueError("publication_date cannot follow human review")
    if record["result_value"] is not None and (
        isinstance(record["result_value"], bool) or not isinstance(record["result_value"], (int, float))
        or not math.isfinite(record["result_value"])
    ):
        raise ValueError("result_value must be a finite number or null")
    if not isinstance(record["inferred"], bool):
        raise ValueError("inferred must be boolean")
    if record["power_metrics_available"] is not False or record["design_power_watts"] is not None:
        raise ValueError("v1 adapter does not accept power claims; use the dedicated power validation path")
    if not isinstance(record["system"], dict) or not isinstance(record["software"], dict):
        raise ValueError("system and software must be objects")
    for field in ("source_url", "dataset_url", "release_url"):
        if record[field] is not None:
            require_url(record[field], "record." + field)
    if record["source_url"] is None:
        raise ValueError("record.source_url is required for a reviewed result")
    for field in ("metrics", "configuration", "workload"):
        if field in record and not isinstance(record[field], dict):
            raise ValueError("record." + field + " must be an object")
    if "metrics" in record:
        for key, value in record["metrics"].items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("raw metric " + key + " must be numeric")
    for field in ("hardware_evidence", "runtime_trace", "normalized_metrics",
                  "power_measurement_valid", "cpu_power_measurement_valid",
                  "gpu_power_metrics_available", "cpu_power_metrics_available",
                  "power_measurement_status", "cpu_power_measurement_status"):
        if field in record and record[field] not in (None, False, {}, []):
            raise ValueError("v1 adapter does not accept " + field)


def build_package(database, registry_bytes, approval, created_at=None):
    validate_approval(approval)
    if not isinstance(database, dict) or database.get("schema_version") != "1.0":
        raise ValueError("benchmark results registry must use schema_version 1.0")
    if set(database) != {"schema_version", "database_version", "last_imported_at", "scope", "sources", "summary", "records"}:
        raise ValueError("benchmark results registry has unexpected top-level fields")
    sources, records = database["sources"], database["records"]
    if not isinstance(sources, list) or not isinstance(records, list):
        raise ValueError("sources and records must be arrays")
    source_matches = [(i, x) for i, x in enumerate(sources) if isinstance(x, dict) and x.get("id") == approval["source_id"]]
    if len(source_matches) != 1:
        raise ValueError("source_id must resolve exactly once in the existing source registry")
    source_index, source = source_matches[0]
    record = copy.deepcopy(approval["record"])
    if record["source_class"] != source.get("source_class"):
        raise ValueError("record.source_class must match the existing source registry")
    source_urls = {source.get(k) for k in ("results_url", "release_url", "dataset_url", "repository_url", "api_url")}
    source_urls.discard(None)
    if record["source_url"] not in source_urls:
        raise ValueError("record.source_url must match a URL already registered for the source")
    if any(x.get("id") == record["id"] for x in records if isinstance(x, dict)):
        raise ValueError("benchmark result ID already exists")
    if any(x.get("source_id") == record["source_id"] and x.get("source_record_key") == record["source_record_key"]
           for x in records if isinstance(x, dict)):
        raise ValueError("source_record_key already exists for this source")

    created_at = created_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("created_at must be an ISO timestamp") from exc
    if created.tzinfo is None or created > datetime.now(timezone.utc):
        raise ValueError("created_at must be timezone-aware and not in the future")
    if created.date() < date.fromisoformat(approval["reviewed_at"]):
        raise ValueError("proposal cannot predate human review")

    updated = copy.deepcopy(database)
    updated["records"].append(record)
    updated["sources"][source_index]["record_count"] += 1
    updated["last_imported_at"] = approval["reviewed_at"]
    updated["database_version"] = str(database["database_version"]) + "+reviewed-" + approval["approval_id"]
    from validate_benchmark_results import summarize
    updated["summary"] = summarize(updated["records"])
    from validate_benchmark_results import validate_database
    errors = validate_database(updated)
    if errors:
        raise ValueError("proposed registry fails benchmark validation: " + "; ".join(errors[:8]))

    operations = [
        {"op": "add", "path": "/records/-", "value": record},
        {"op": "replace", "path": f"/sources/{source_index}/record_count", "value": updated["sources"][source_index]["record_count"]},
        {"op": "replace", "path": "/last_imported_at", "value": updated["last_imported_at"]},
        {"op": "replace", "path": "/database_version", "value": updated["database_version"]},
        {"op": "replace", "path": "/summary", "value": updated["summary"]},
    ]
    base_hash = digest_bytes(registry_bytes)
    proposed_hash = digest_json(updated)
    body = {
        "schema_version": "1.0", "proposal_id": approval["approval_id"],
        "proposal_type": "benchmark_result_creation", "created_at": created.isoformat().replace("+00:00", "Z"),
        "target_registry": {"path": DB_PATH, "schema_version": "1.0", "base_sha256": base_hash},
        "source_snapshot": copy.deepcopy(source), "approval": copy.deepcopy(approval),
        "target": {"source_id": source["id"], "record_id": record["id"], "source_record_key": record["source_record_key"]},
        "operations": operations,
        "audit": {"verification_status": "exact_one_result_append", "unapproved_changes": 0,
                  "source_truth_verified": False, "evidence_level_promoted": False,
                  "source_id": source["id"], "source_class": source["source_class"],
                  "reviewer": approval["reviewer"], "reviewed_at": approval["reviewed_at"],
                  "base_registry_sha256": base_hash, "proposed_registry_sha256": proposed_hash},
        "proposed_registry_sha256": proposed_hash,
        "policy": {"human_approval_required": True, "source_truth_verified": False,
                   "evidence_level_promoted": False, "automatic_merge": False,
                   "power_claims_supported": False, "allowed_changes": [
                       "append one result for an existing registered source",
                       "reconcile source record_count, database_version, last_imported_at and summary"]},
    }
    package = {**body, "package_sha256": digest_json(body)}
    patch = {"schema": "https://json.schemastore.org/json-patch.json",
             "base_registry_sha256": base_hash, "operations": operations}
    before = (json.dumps(database, indent=2, ensure_ascii=False) + "\n").splitlines(keepends=True)
    after = (json.dumps(updated, indent=2, ensure_ascii=False) + "\n").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(before, after, fromfile="a/data/benchmark-results.json",
                                        tofile="b/data/benchmark-results.json"))
    return package, patch, copy.deepcopy(package["audit"]), diff, updated


def verify_package(database, package, registry_bytes, approval):
    if not isinstance(package, dict) or package.get("proposal_type") != "benchmark_result_creation":
        raise ValueError("unsupported benchmark result proposal type")
    if package.get("approval") != approval:
        raise ValueError("separate Approval Manifest does not exactly match proposal")
    binding = package.get("target_registry")
    if not isinstance(binding, dict) or binding.get("base_sha256") != digest_bytes(registry_bytes):
        raise ValueError("proposal base SHA256 does not match current registry")
    expected, patch, audit, diff, updated = build_package(database, registry_bytes, approval, package.get("created_at"))
    if canonical(expected) != canonical(package):
        raise ValueError("proposal package, operations or audit hash differs from deterministic rebuild")
    return updated, patch, audit, diff


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "verify"):
        item = sub.add_parser(command)
        item.add_argument("--benchmark-results", type=Path, default=Path("data/benchmark-results.json"))
        item.add_argument("--approval", type=Path, required=True)
        if command == "build":
            item.add_argument("--proposal-output", type=Path, required=True)
        else:
            item.add_argument("--proposal", type=Path, required=True)
        item.add_argument("--database-output", type=Path, required=True)
        item.add_argument("--patch-output", type=Path, required=True)
        item.add_argument("--audit-output", type=Path, required=True)
        item.add_argument("--diff-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = args.benchmark_results.read_bytes()
        database = json.loads(raw)
        approval = json.loads(args.approval.read_text(encoding="utf-8"))
        if args.command == "build":
            package, patch, audit, diff, updated = build_package(database, raw, approval)
            write_json(args.proposal_output, package)
        else:
            package = json.loads(args.proposal.read_text(encoding="utf-8"))
            updated, patch, audit, diff = verify_package(database, package, raw, approval)
        write_json(args.database_output, updated)
        write_json(args.patch_output, patch)
        write_json(args.audit_output, audit)
        args.diff_output.parent.mkdir(parents=True, exist_ok=True)
        args.diff_output.write_text(diff, encoding="utf-8")
        print("PASS: verified benchmark result proposal " + approval["approval_id"])
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
