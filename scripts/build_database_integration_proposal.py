#!/usr/bin/env python3
"""Build and verify a review-only, provenance-bound company database proposal.

The only supported write set is the append-only attachment of one reviewed
Evidence record and its ID to one existing Claim. This tool never approves
Claims, changes claim values/status, or writes to the repository checkout.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from propose_evidence_update import create_patch, build_diff, fingerprint_claim
from verify_evidence_patch import verify_patch

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REGISTRY_PATH = "data/company-profiles.json"
PROPOSAL_TYPE = "company_profile_evidence_attachment"
PACKAGE_KEYS = {
    "schema_version", "proposal_id", "proposal_type", "created_at",
    "target_registry", "source_claim", "approval", "target",
    "operations", "audit", "proposed_registry_sha256", "policy",
    "package_sha256",
}


def _js_number(value):
    if value == 0:
        return "0"
    magnitude = abs(value)
    if 1e-6 <= magnitude < 1e21:
        from decimal import Decimal
        rendered = format(Decimal(repr(value)), "f")
        if "." in rendered:
            rendered = rendered.rstrip("0").rstrip(".")
        return rendered
    rendered = repr(value).lower()
    if "e" not in rendered:
        return rendered[:-2] if rendered.endswith(".0") else rendered
    mantissa, exponent = rendered.split("e", 1)
    if mantissa.endswith(".0"):
        mantissa = mantissa[:-2]
    number = int(exponent)
    return mantissa + "e" + ("+" if number >= 0 else "-") + str(abs(number))


def canonical(value):
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _js_number(value)
    if isinstance(value, list):
        return "[" + ",".join(canonical(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(
            json.dumps(key, ensure_ascii=False) + ":" + canonical(value[key])
            for key in sorted(value)
        ) + "}"
    raise TypeError("unsupported JSON value in canonical serializer")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value) -> str:
    return sha256_bytes(canonical(value).encode("utf-8"))


def parse_aware(value, field):
    if not isinstance(value, str):
        raise ValueError(field + " must be timezone-aware ISO-8601")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid " + field) from exc
    if parsed.utcoffset() is None:
        raise ValueError(field + " must include a timezone")
    return parsed


def build_package(database, claim_report, approval, registry_bytes, created_at=None):
    if not isinstance(approval, dict):
        raise ValueError("approval manifest must be an object")
    if not isinstance(database, dict) or database.get("schema_version") != "1.3":
        raise ValueError("company profile registry must use schema_version 1.3")
    if not isinstance(database.get("companies"), list):
        raise ValueError("company profile registry companies must be an array")
    if not isinstance(claim_report, dict) or claim_report.get("schema_version") != "1.0":
        raise ValueError("Claim report must use schema_version 1.0")
    claims = claim_report.get("claims")
    if not isinstance(claims, list) or claim_report.get("claim_count") != len(claims):
        raise ValueError("Claim report count does not match its claims array")
    source_matches = [row for row in claims if isinstance(row, dict) and
                      row.get("claim_id") == approval.get("extracted_claim_id")]
    if len(source_matches) != 1:
        raise ValueError("proposal must reference exactly one extracted source Claim")
    source_claim = copy.deepcopy(source_matches[0])
    updated, generated_audit = create_patch(database, claim_report, approval)
    verification = verify_patch(database, updated, approval, generated_audit)
    company_indexes = [i for i, row in enumerate(database["companies"])
                       if row.get("id") == approval["company_id"]]
    if len(company_indexes) != 1:
        raise ValueError("target company must resolve exactly once")
    company_index = company_indexes[0]
    company = database["companies"][company_index]
    claim_indexes = [i for i, row in enumerate(company.get("claims", []))
                     if row.get("id") == approval["existing_claim_id"]]
    if len(claim_indexes) != 1:
        raise ValueError("target Claim must resolve exactly once")
    claim_index = claim_indexes[0]
    target_claim = company["claims"][claim_index]
    source_url = source_claim.get("source", {}).get("url")
    if source_url != approval["evidence"]["url"]:
        raise ValueError("source Claim URL and approval evidence URL differ")
    created_at = created_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    created = parse_aware(created_at, "created_at")
    if created > datetime.now(timezone.utc):
        raise ValueError("created_at cannot be in the future")
    target = {
        "company_id": company["id"],
        "company_display_name": company.get("display_name", company["id"]),
        "company_index": company_index,
        "claim_id": target_claim["id"],
        "claim_statement": target_claim.get("statement", ""),
        "claim_index": claim_index,
        "subject_type": target_claim.get("subject_type"),
        "subject_id": target_claim.get("subject_id"),
        "original_claim_sha256": fingerprint_claim(target_claim),
        "evidence_ids_before": copy.deepcopy(target_claim.get("evidence_ids", [])),
        "evidence_ids_after": copy.deepcopy(updated["companies"][company_index]["claims"][claim_index]["evidence_ids"]),
    }
    operations = [
        {"op": "add", "path": f"/companies/{company_index}/evidence/-",
         "value": copy.deepcopy(approval["evidence"])},
        {"op": "add", "path": f"/companies/{company_index}/claims/{claim_index}/evidence_ids/-",
         "value": approval["evidence"]["id"]},
    ]
    body = {
        "schema_version": "1.0",
        "proposal_id": approval["approval_id"],
        "proposal_type": PROPOSAL_TYPE,
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "target_registry": {
            "path": REGISTRY_PATH,
            "schema_version": database["schema_version"],
            "base_sha256": sha256_bytes(registry_bytes),
        },
        "source_claim": source_claim,
        "approval": copy.deepcopy(approval),
        "target": target,
        "operations": operations,
        "audit": {
            **verification,
            "approval_id": approval["approval_id"],
            "reviewer": approval["reviewer"],
            "reviewed_at": approval["reviewed_at"],
            "decision": approval["decision"],
            "source_claim_id": source_claim["claim_id"],
            "source_url": source_url,
            "evidence_quote_sha256": sha256_bytes(source_claim["evidence_quote"].encode("utf-8")),
            "original_claim_sha256": target["original_claim_sha256"],
            "base_registry_sha256": sha256_bytes(registry_bytes),
            "proposed_registry_sha256": sha256_json(updated),
        },
        "proposed_registry_sha256": sha256_json(updated),
        "policy": {
            "human_approval_required": True,
            "source_truth_verified": False,
            "claim_status_changed": False,
            "claim_value_or_scope_changed": False,
            "product_identity_changed": False,
            "automatic_merge": False,
            "allowed_changes": [
                "append one reviewed evidence object to the selected company",
                "append that evidence ID to the selected existing Claim",
            ],
        },
    }
    package = {**body, "package_sha256": sha256_json(body)}
    patch = {
        "schema": "https://json.schemastore.org/json-patch.json",
        "base_registry_sha256": body["target_registry"]["base_sha256"],
        "operations": operations,
    }
    audit = copy.deepcopy(body["audit"])
    diff = build_diff(database, updated)
    return package, patch, audit, diff, updated


def verify_package(database, package, registry_bytes):
    if not isinstance(package, dict) or set(package) != PACKAGE_KEYS:
        raise ValueError("proposal package must contain exactly the documented fields")
    if package.get("schema_version") != "1.0" or package.get("proposal_type") != PROPOSAL_TYPE:
        raise ValueError("unsupported proposal package schema or type")
    claimed_hash = package.get("package_sha256")
    body = {key: value for key, value in package.items() if key != "package_sha256"}
    if not isinstance(claimed_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", claimed_hash):
        raise ValueError("invalid package SHA256")
    if sha256_json(body) != claimed_hash:
        raise ValueError("proposal package SHA256 mismatch")
    created = parse_aware(package.get("created_at"), "created_at")
    if created > datetime.now(timezone.utc):
        raise ValueError("proposal package timestamp cannot be in the future")
    approval = package.get("approval")
    source_claim = package.get("source_claim")
    if not isinstance(approval, dict) or not isinstance(source_claim, dict):
        raise ValueError("proposal approval or source Claim snapshot is missing")
    report = {"schema_version": "1.0", "claim_count": 1, "claims": [source_claim]}
    expected, patch, audit, diff, updated = build_package(
        database, report, approval, registry_bytes, package["created_at"])
    if expected != package:
        raise ValueError("proposal package does not match current registry, approval or source Claim")
    if package.get("proposal_id") != approval.get("approval_id"):
        raise ValueError("proposal ID does not match approval manifest")
    return updated, patch, audit, diff


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_command(args):
    raw = args.company_profiles.read_bytes()
    database = json.loads(raw.decode("utf-8"))
    claim_report = json.loads(args.claim_report.read_text(encoding="utf-8"))
    approval = json.loads(args.approval.read_text(encoding="utf-8"))
    package, patch, audit, diff, updated = build_package(
        database, claim_report, approval, raw, args.created_at)
    write_json(args.proposal_output, package)
    write_json(args.patch_output, patch)
    write_json(args.audit_output, audit)
    write_json(args.database_output, updated)
    args.diff_output.parent.mkdir(parents=True, exist_ok=True)
    args.diff_output.write_text(diff, encoding="utf-8")
    print(json.dumps({"status":"proposal_generated","proposal_id":package["proposal_id"],
                      "company_id":package["target"]["company_id"],
                      "claim_id":package["target"]["claim_id"],
                      "package_sha256":package["package_sha256"]}))
    return 0


def verify_command(args):
    raw = args.company_profiles.read_bytes()
    database = json.loads(raw.decode("utf-8"))
    package = json.loads(args.proposal.read_text(encoding="utf-8"))
    updated, patch, audit, diff = verify_package(database, package, raw)
    write_json(args.database_output, updated)
    write_json(args.patch_output, patch)
    write_json(args.audit_output, audit)
    args.diff_output.parent.mkdir(parents=True, exist_ok=True)
    args.diff_output.write_text(diff, encoding="utf-8")
    print(json.dumps({"status":"proposal_verified","proposal_id":package["proposal_id"],
                      "company_id":package["target"]["company_id"],
                      "claim_id":package["target"]["claim_id"],
                      "base_registry_sha256":package["target_registry"]["base_sha256"],
                      "proposed_registry_sha256":package["proposed_registry_sha256"]}))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="generate a review-only integration package")
    build.add_argument("--company-profiles", type=Path, default=Path(REGISTRY_PATH))
    build.add_argument("--claim-report", type=Path, required=True)
    build.add_argument("--approval", type=Path, required=True)
    build.add_argument("--proposal-output", type=Path, required=True)
    build.add_argument("--patch-output", type=Path, required=True)
    build.add_argument("--audit-output", type=Path, required=True)
    build.add_argument("--diff-output", type=Path, required=True)
    build.add_argument("--database-output", type=Path, required=True)
    build.add_argument("--created-at")
    verify = sub.add_parser("verify", help="rebuild and verify a committed proposal against master")
    verify.add_argument("--company-profiles", type=Path, default=Path(REGISTRY_PATH))
    verify.add_argument("--proposal", type=Path, required=True)
    verify.add_argument("--database-output", type=Path, required=True)
    verify.add_argument("--patch-output", type=Path, required=True)
    verify.add_argument("--audit-output", type=Path, required=True)
    verify.add_argument("--diff-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        return build_command(args) if args.command == "build" else verify_command(args)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
