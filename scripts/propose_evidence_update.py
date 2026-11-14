#!/usr/bin/env python3
"""Build a narrow, reviewable company-profile evidence patch from a human-approved claim.

This tool never approves claims, never changes claim status/value/scope, and
does not perform network fetches. GitHub PR creation is a separate gated step.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
EVIDENCE_TYPES = {
    "company_primary", "vendor_primary", "official_project", "research_paper",
    "independent_media", "government_or_regulatory", "repository", "other",
}
INDEPENDENCE = {"vendor", "project", "independent", "official"}


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint_claim(claim):
    return hashlib.sha256(canonical_json(claim).encode("utf-8")).hexdigest()


def valid_https(url):
    if not isinstance(url, str):
        return False
    try:
        parsed = urlsplit(url)
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def valid_date(value):
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_approval(approval):
    if not isinstance(approval, dict) or set(approval) != {
        "schema_version", "approval_id", "reviewer", "reviewed_at", "decision",
        "company_id", "existing_claim_id", "expected_claim_sha256",
        "extracted_claim_id", "evidence", "review_notes"
    }:
        raise ValueError("approval must contain exactly the documented evidence-attachment fields")
    if approval["schema_version"] != "1.0" or approval["decision"] != "approved_evidence_attachment":
        raise ValueError("requires explicit approved_evidence_attachment decision")
    for field in ("approval_id", "company_id", "existing_claim_id", "extracted_claim_id"):
        value = approval[field]
        if not isinstance(value, str) or not ID_RE.fullmatch(value):
            raise ValueError(field + " must be a slug ID")
    if not isinstance(approval["reviewer"], str) or not approval["reviewer"].strip():
        raise ValueError("human reviewer identity is required")
    if not valid_date(approval["reviewed_at"]):
        raise ValueError("reviewed_at must be a valid ISO date")
    if not isinstance(approval["review_notes"], str) or len(approval["review_notes"].strip()) < 30:
        raise ValueError("review_notes must describe the independent review in at least 30 characters")
    if not isinstance(approval["expected_claim_sha256"], str) or not SHA_RE.fullmatch(approval["expected_claim_sha256"]):
        raise ValueError("expected_claim_sha256 must be a lowercase SHA256 of the existing claim")
    evidence = approval["evidence"]
    fields = {"id", "title", "url", "publisher", "source_type", "independence",
              "published_at", "checked_at", "review_status", "notes"}
    if not isinstance(evidence, dict) or set(evidence) != fields:
        raise ValueError("evidence must contain exactly the company-profile evidence fields")
    if not isinstance(evidence["id"], str) or not ID_RE.fullmatch(evidence["id"]):
        raise ValueError("evidence.id must be a slug")
    if not valid_https(evidence["url"]):
        raise ValueError("evidence.url must be HTTPS")
    if evidence["source_type"] not in EVIDENCE_TYPES or evidence["independence"] not in INDEPENDENCE:
        raise ValueError("evidence source type/independence is invalid")
    if evidence["review_status"] != "reviewed":
        raise ValueError("evidence must have a human-reviewed status")
    for key in ("title", "publisher", "notes"):
        if not isinstance(evidence[key], str) or not evidence[key].strip():
            raise ValueError("evidence." + key + " must not be empty")
    if not valid_date(evidence["checked_at"]):
        raise ValueError("evidence.checked_at must be ISO date")
    if evidence["published_at"] is not None and not valid_date(evidence["published_at"]):
        raise ValueError("evidence.published_at must be ISO date or null")
    if evidence["checked_at"] > approval["reviewed_at"]:
        raise ValueError("evidence cannot be checked after review date")


def create_patch(database, claim_report, approval):
    validate_approval(approval)
    if claim_report.get("schema_version") != "1.0" or not isinstance(claim_report.get("claims"), list):
        raise ValueError("expected PR #90 claim extraction report")
    source_claims = [x for x in claim_report["claims"] if x.get("claim_id") == approval["extracted_claim_id"]]
    if len(source_claims) != 1 or source_claims[0].get("review_status") != "unverified_candidate":
        raise ValueError("approval must reference exactly one unverified extracted claim")
    source = source_claims[0].get("source", {})
    if not isinstance(source, dict) or source.get("url") != approval["evidence"]["url"]:
        raise ValueError("reviewed evidence URL must exactly match extracted claim source URL")
    if not isinstance(source_claims[0].get("evidence_quote"), str) or not source_claims[0]["evidence_quote"].strip():
        raise ValueError("original excerpt evidence must be present")
    companies = database.get("companies")
    if not isinstance(companies, list):
        raise ValueError("company profiles database must contain companies array")
    matches = [c for c in companies if c.get("id") == approval["company_id"]]
    if len(matches) != 1:
        raise ValueError("company ID must match exactly one existing company")
    company = matches[0]
    match_claims = [c for c in company.get("claims", []) if c.get("id") == approval["existing_claim_id"]]
    if len(match_claims) != 1:
        raise ValueError("existing claim ID must match exactly one claim in the company")
    existing = match_claims[0]
    if fingerprint_claim(existing) != approval["expected_claim_sha256"]:
        raise ValueError("existing claim changed since human approval (SHA256 mismatch)")
    if approval["evidence"]["id"] in {e.get("id") for e in company.get("evidence", [])}:
        raise ValueError("evidence ID already exists")
    if approval["evidence"]["url"] in {e.get("url") for e in company.get("evidence", [])}:
        raise ValueError("evidence URL already exists")
    if approval["evidence"]["id"] in existing.get("evidence_ids", []):
        raise ValueError("evidence already linked to claim")
    # Never silently equate a new observation with the existing formal claim.
    # Human reviewer explicitly chooses the existing claim and records rationale.
    updated = copy.deepcopy(database)
    target = next(c for c in updated["companies"] if c["id"] == approval["company_id"])
    target["evidence"].append(copy.deepcopy(approval["evidence"]))
    target_claim = next(c for c in target["claims"] if c["id"] == approval["existing_claim_id"])
    target_claim["evidence_ids"].append(approval["evidence"]["id"])
    audit = {
        "schema_version": "1.0",
        "approval_id": approval["approval_id"], "reviewer": approval["reviewer"],
        "reviewed_at": approval["reviewed_at"],
        "decision": approval["decision"], "source_claim_id": approval["extracted_claim_id"],
        "company_id": approval["company_id"], "target_claim_id": approval["existing_claim_id"],
        "original_claim_sha256": approval["expected_claim_sha256"],
        "new_evidence_id": approval["evidence"]["id"],
        "source_url": approval["evidence"]["url"],
        "review_notes": approval["review_notes"],
        "changed_fields": [
            "companies[" + approval["company_id"] + "].evidence append",
            "companies[" + approval["company_id"] + "].claims[" + approval["existing_claim_id"] + "].evidence_ids append"
        ],
        "unchanged": [
            "company and product identities", "claim statement", "claim status",
            "claim value", "claim unit", "claim scope", "claim metric context",
            "published benchmark observations", "model support levels"
        ],
        "provenance_policy": "Human-approved evidence attachment only. The extracted claim remains unverified; adding a source does not upgrade the formal claim status."
    }
    return updated, audit


def build_diff(original, updated, *, path="data/company-profiles.json"):
    before = (json.dumps(original, indent=2, ensure_ascii=False) + "\n").splitlines(keepends=True)
    after = (json.dumps(updated, indent=2, ensure_ascii=False) + "\n").splitlines(keepends=True)
    return "".join(difflib.unified_diff(before, after, fromfile="a/" + path, tofile="b/" + path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company-profiles", type=Path, default=Path("data/company-profiles.json"))
    parser.add_argument("--claim-report", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--diff-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        source = json.loads(args.company_profiles.read_text(encoding="utf-8"))
        claims = json.loads(args.claim_report.read_text(encoding="utf-8"))
        approval = json.loads(args.approval.read_text(encoding="utf-8"))
        updated, audit = create_patch(source, claims, approval)
        diff = build_diff(source, updated)
        if not diff:
            raise ValueError("no changes found")
        for path in (args.output, args.audit_output, args.diff_output):
            path.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        args.audit_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        args.diff_output.write_text(diff, encoding="utf-8")
        print("PASS: generated reviewed evidence attachment proposal " + approval["approval_id"])
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
