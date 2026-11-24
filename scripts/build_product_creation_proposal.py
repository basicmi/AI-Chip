#!/usr/bin/env python3
"""Build and independently verify a human-approved new-product proposal.

This adapter supports one existing company, one new product, one initial
vendor-reported product-identity Claim, and one reviewed Evidence record.
It does not modify the repository checkout.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from build_database_integration_proposal import (
    REGISTRY_PATH, canonical, sha256_bytes, sha256_json, parse_aware
)

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRODUCT_TYPES = {"gpu", "npu", "asic", "dpu", "ip", "system", "compute_in_memory", "other"}
AVAILABILITY = {"announced", "sampling", "shipping", "production", "roadmap", "discontinued", "unknown"}
SOURCE_TYPES = {"company_primary", "vendor_primary", "official_project"}
INDEPENDENCE = {"vendor", "project", "official"}
PRODUCT_FIELDS = {
    "id", "name", "product_type", "availability", "claim_ids", "architecture",
    "generation", "process_node", "market_segment", "notes", "family", "form_factor",
    "package", "system_configuration", "die_count", "announced_at", "first_available_at",
    "availability_history",
}
CLAIM_FIELDS = {
    "id", "subject_type", "subject_id", "topic", "statement", "scope",
    "claim_status", "evidence_ids", "last_reviewed", "notes",
}
EVIDENCE_FIELDS = {
    "id", "title", "url", "publisher", "source_type", "independence",
    "published_at", "checked_at", "review_status", "notes",
}
APPROVAL_FIELDS = {
    "schema_version", "approval_id", "reviewer", "reviewed_at", "decision",
    "company_id", "extracted_claim_id", "product", "claim", "evidence", "review_notes",
}


def require_slug(value, field):
    if not isinstance(value, str) or not SLUG.fullmatch(value):
        raise ValueError(field + " must be a lowercase slug ID")


def require_text(value, field, minimum=1):
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ValueError(field + " must contain at least " + str(minimum) + " characters")


def require_date(value, field, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str):
        raise ValueError(field + " must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(field + " must be an ISO date") from exc


def validate_evidence(evidence, approval_date):
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_FIELDS:
        raise ValueError("evidence must contain exactly the company-profile evidence fields")
    require_slug(evidence["id"], "evidence.id")
    for field in ("title", "publisher", "notes"):
        require_text(evidence[field], "evidence." + field)
    try:
        parsed = urlsplit(evidence["url"])
    except (TypeError, ValueError) as exc:
        raise ValueError("evidence.url must be HTTPS") from exc
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("evidence.url must be HTTPS without embedded credentials")
    if evidence["source_type"] not in SOURCE_TYPES or evidence["independence"] not in INDEPENDENCE:
        raise ValueError("new-product Evidence must use company/vendor primary or official project sources")
    if evidence["review_status"] != "reviewed":
        raise ValueError("new-product Evidence must be human reviewed")
    require_date(evidence["published_at"], "evidence.published_at", nullable=True)
    require_date(evidence["checked_at"], "evidence.checked_at")
    if evidence["checked_at"] > approval_date:
        raise ValueError("evidence cannot be checked after human review")
    if evidence["published_at"] is not None and evidence["published_at"] > evidence["checked_at"]:
        raise ValueError("evidence publication date cannot follow its checked date")


def validate_approval(approval):
    if not isinstance(approval, dict) or set(approval) != APPROVAL_FIELDS:
        raise ValueError("Approval Manifest does not match the exact product-creation schema")
    if approval["schema_version"] != "1.0" or approval["decision"] != "approved_new_product_with_identity_claim":
        raise ValueError("requires approved_new_product_with_identity_claim decision")
    for field in ("approval_id", "company_id", "extracted_claim_id"):
        require_slug(approval[field], field)
    require_text(approval["reviewer"], "reviewer")
    require_date(approval["reviewed_at"], "reviewed_at")
    require_text(approval["review_notes"], "review_notes", 30)
    if date.fromisoformat(approval["reviewed_at"]) > datetime.now(timezone.utc).date():
        raise ValueError("human review date cannot be in the future")

    product = approval["product"]
    if not isinstance(product, dict) or not {"id", "name", "product_type", "availability", "claim_ids", "availability_history"} <= set(product) or not set(product) <= PRODUCT_FIELDS:
        raise ValueError("product must use the supported product schema fields")
    require_slug(product["id"], "product.id")
    require_text(product["name"], "product.name")
    if product["product_type"] not in PRODUCT_TYPES or product["availability"] not in AVAILABILITY:
        raise ValueError("product_type or availability is not supported")
    if product["claim_ids"] != [approval["claim"]["id"]]:
        raise ValueError("new product must reference exactly its one initial identity Claim")
    for field in ("architecture", "generation", "process_node", "market_segment", "notes",
                  "family", "form_factor", "package", "system_configuration"):
        if field in product:
            require_text(product[field], "product." + field)
    if "die_count" in product and (not isinstance(product["die_count"], int) or isinstance(product["die_count"], bool) or product["die_count"] < 1):
        raise ValueError("product.die_count must be a positive integer")
    for field in ("announced_at", "first_available_at"):
        if field in product:
            require_date(product[field], "product." + field, nullable=True)
    if product.get("announced_at") and product.get("first_available_at") and product["first_available_at"] < product["announced_at"]:
        raise ValueError("first_available_at cannot precede announced_at")
    history = product["availability_history"]
    if not isinstance(history, list) or len(history) != 1:
        raise ValueError("new product requires exactly one initial availability-history event")
    event = history[0]
    if not isinstance(event, dict) or set(event) != {"status", "effective_at", "evidence_id", "notes"}:
        raise ValueError("availability-history event must contain exactly status, effective_at, evidence_id and notes")
    if event["status"] != product["availability"] or event["status"] not in AVAILABILITY:
        raise ValueError("initial availability event must match product availability")
    require_date(event["effective_at"], "availability_history.effective_at")
    require_text(event["notes"], "availability_history.notes")

    claim = approval["claim"]
    if not isinstance(claim, dict) or not {"id", "subject_type", "subject_id", "topic", "statement", "scope",
                                          "claim_status", "evidence_ids", "last_reviewed"} <= set(claim) or not set(claim) <= CLAIM_FIELDS:
        raise ValueError("initial Claim must use the supported product-identity Claim fields")
    require_slug(claim["id"], "claim.id")
    if claim["subject_type"] != "product" or claim["subject_id"] != product["id"]:
        raise ValueError("initial Claim subject must reference the new product")
    if claim["topic"] != "product_identity" or claim["claim_status"] != "vendor_reported":
        raise ValueError("initial Claim must be product_identity with conservative vendor_reported status")
    require_text(claim["statement"], "claim.statement")
    require_text(claim["scope"], "claim.scope")
    if claim["evidence_ids"] != [approval["evidence"]["id"]]:
        raise ValueError("initial Claim must reference exactly the reviewed Evidence record")
    if claim["last_reviewed"] != approval["reviewed_at"]:
        raise ValueError("initial Claim last_reviewed must equal the human review date")
    if "notes" in claim:
        require_text(claim["notes"], "claim.notes")

    validate_evidence(approval["evidence"], approval["reviewed_at"])
    if event["evidence_id"] != approval["evidence"]["id"]:
        raise ValueError("availability-history event must reference the reviewed Evidence record")


def build_package(database, claim_report, approval, registry_bytes, created_at=None):
    validate_approval(approval)
    if not isinstance(database, dict) or database.get("schema_version") != "1.3":
        raise ValueError("company profile registry must use schema_version 1.3")
    companies = database.get("companies")
    if not isinstance(companies, list):
        raise ValueError("company profile registry companies must be an array")
    if not isinstance(claim_report, dict) or claim_report.get("schema_version") != "1.0":
        raise ValueError("Claim report must use schema_version 1.0")
    rows = claim_report.get("claims")
    if not isinstance(rows, list) or claim_report.get("claim_count") != len(rows):
        raise ValueError("Claim report count does not match its claims array")
    matches = [row for row in rows if isinstance(row, dict) and row.get("claim_id") == approval["extracted_claim_id"]]
    if len(matches) != 1 or matches[0].get("review_status") != "unverified_candidate":
        raise ValueError("approval must reference exactly one unverified extracted Claim")
    source_claim = copy.deepcopy(matches[0])
    require_text(source_claim.get("statement"), "source Claim statement")
    require_text(source_claim.get("evidence_quote"), "source Claim evidence_quote")
    source = source_claim.get("source")
    if not isinstance(source, dict) or source.get("url") != approval["evidence"]["url"]:
        raise ValueError("source Claim URL and reviewed Evidence URL differ")
    if source_claim["statement"] != approval["claim"]["statement"]:
        raise ValueError("initial product Claim statement must exactly match the reviewed extracted Claim")

    company_matches = [(i, row) for i, row in enumerate(companies) if isinstance(row, dict) and row.get("id") == approval["company_id"]]
    if len(company_matches) != 1:
        raise ValueError("target company must resolve exactly once in the existing registry")
    company_index, company = company_matches[0]
    if not all(isinstance(company.get(field), list) for field in ("products", "claims", "evidence")):
        raise ValueError("target company products, claims and evidence must be arrays")
    product, claim, evidence = approval["product"], approval["claim"], approval["evidence"]
    if any(item.get("id") == product["id"] for item in company["products"]):
        raise ValueError("product ID already exists in target company")
    if any(item.get("id") == claim["id"] for item in company["claims"]):
        raise ValueError("Claim ID already exists in target company")
    if any(item.get("id") == evidence["id"] or item.get("url") == evidence["url"] for item in company["evidence"]):
        raise ValueError("Evidence ID or URL already exists in target company")
    all_company_ids = {row.get("id") for row in companies if isinstance(row, dict)}
    if len(all_company_ids) != len(companies):
        raise ValueError("base registry contains duplicate or invalid company rows")

    created_at = created_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    created = parse_aware(created_at, "created_at")
    if created > datetime.now(timezone.utc):
        raise ValueError("created_at cannot be in the future")
    if created.date() < date.fromisoformat(approval["reviewed_at"]):
        raise ValueError("proposal cannot predate the human review")

    updated = copy.deepcopy(database)
    target = updated["companies"][company_index]
    target["evidence"].append(copy.deepcopy(evidence))
    target["products"].append(copy.deepcopy(product))
    target["claims"].append(copy.deepcopy(claim))
    operations = [
        {"op": "add", "path": f"/companies/{company_index}/evidence/-", "value": copy.deepcopy(evidence)},
        {"op": "add", "path": f"/companies/{company_index}/products/-", "value": copy.deepcopy(product)},
        {"op": "add", "path": f"/companies/{company_index}/claims/-", "value": copy.deepcopy(claim)},
    ]
    base_hash = sha256_bytes(registry_bytes)
    proposed_hash = sha256_json(updated)
    body = {
        "schema_version": "1.0",
        "proposal_id": approval["approval_id"],
        "proposal_type": "company_profile_product_creation",
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "target_registry": {"path": REGISTRY_PATH, "schema_version": "1.3", "base_sha256": base_hash},
        "source_claim": source_claim,
        "approval": copy.deepcopy(approval),
        "target": {
            "company_id": company["id"], "company_display_name": company.get("display_name", company["id"]),
            "company_index": company_index, "product_id": product["id"], "product_name": product["name"],
            "claim_id": claim["id"], "source_claim_id": source_claim["claim_id"],
        },
        "operations": operations,
        "audit": {
            "verification_status": "exact_three_record_append",
            "unapproved_changes": 0, "source_truth_verified": False,
            "claim_status_changed": False, "new_claim_status": "vendor_reported",
            "approval_id": approval["approval_id"], "reviewer": approval["reviewer"],
            "reviewed_at": approval["reviewed_at"], "source_claim_id": source_claim["claim_id"],
            "source_url": evidence["url"], "evidence_quote_sha256": sha256_bytes(source_claim["evidence_quote"].encode("utf-8")),
            "base_registry_sha256": base_hash, "proposed_registry_sha256": proposed_hash,
        },
        "proposed_registry_sha256": proposed_hash,
        "policy": {
            "human_approval_required": True, "source_truth_verified": False,
            "claim_status_changed": False, "new_claim_status": "vendor_reported",
            "automatic_merge": False,
            "allowed_changes": ["append one reviewed Evidence", "append one new Product",
                                "append one initial vendor_reported product_identity Claim"],
        },
    }
    package = {**body, "package_sha256": sha256_json(body)}
    patch = {"schema": "https://json.schemastore.org/json-patch.json",
             "base_registry_sha256": base_hash, "operations": operations}
    before = (json.dumps(database, indent=2, ensure_ascii=False) + "\n").splitlines(keepends=True)
    after = (json.dumps(updated, indent=2, ensure_ascii=False) + "\n").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(before, after, fromfile="a/data/company-profiles.json",
                                        tofile="b/data/company-profiles.json"))
    audit = copy.deepcopy(package["audit"])
    return package, patch, audit, diff, updated


def verify_package(database, package, registry_bytes, claim_report, approval):
    if not isinstance(package, dict) or package.get("proposal_type") != "company_profile_product_creation":
        raise ValueError("unsupported product proposal type")
    if package.get("target_registry", {}).get("base_sha256") != sha256_bytes(registry_bytes):
        raise ValueError("proposal base SHA256 does not match current registry")
    if package.get("approval") != approval:
        raise ValueError("separate Approval Manifest does not exactly match proposal")
    if not isinstance(claim_report, dict):
        raise ValueError("original Claim report is required")
    source_id = package.get("source_claim", {}).get("claim_id")
    rows = [row for row in claim_report.get("claims", []) if isinstance(row, dict) and row.get("claim_id") == source_id]
    if claim_report.get("claim_count") != len(claim_report.get("claims", [])) or len(rows) != 1 or rows[0] != package.get("source_claim"):
        raise ValueError("separate original Claim report does not exactly match proposal")
    expected, patch, audit, diff, updated = build_package(
        database, claim_report, approval, registry_bytes, package.get("created_at"))
    if canonical(expected) != canonical(package):
        raise ValueError("proposal package, operation set or audit hash does not match deterministic rebuild")
    return updated, patch, audit, diff


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "verify"):
        item = sub.add_parser(command)
        item.add_argument("--company-profiles", type=Path, default=Path("data/company-profiles.json"))
        item.add_argument("--claim-report", type=Path, required=True)
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
        raw = args.company_profiles.read_bytes()
        database = json.loads(raw)
        report = json.loads(args.claim_report.read_text(encoding="utf-8"))
        approval = json.loads(args.approval.read_text(encoding="utf-8"))
        if args.command == "build":
            package, patch, audit, diff, updated = build_package(database, report, approval, raw)
            write_json(args.proposal_output, package)
        else:
            package = json.loads(args.proposal.read_text(encoding="utf-8"))
            updated, patch, audit, diff = verify_package(database, package, raw, report, approval)
        write_json(args.database_output, updated)
        write_json(args.patch_output, patch)
        write_json(args.audit_output, audit)
        args.diff_output.parent.mkdir(parents=True, exist_ok=True)
        args.diff_output.write_text(diff, encoding="utf-8")
        print("PASS: verified product creation proposal " + approval["approval_id"])
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
