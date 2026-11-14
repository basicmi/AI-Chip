#!/usr/bin/env python3
"""Independently verify that an evidence update changed exactly the approved append-only fields."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from propose_evidence_update import validate_approval, fingerprint_claim


def verify_patch(original, updated, approval, audit):
    validate_approval(approval)
    if not isinstance(original, dict) or not isinstance(updated, dict):
        raise ValueError("original/updated databases must be objects")
    if not isinstance(audit, dict) or audit.get("approval_id") != approval["approval_id"]:
        raise ValueError("audit approval ID mismatch")
    if audit.get("new_evidence_id") != approval["evidence"]["id"] or audit.get("source_claim_id") != approval["extracted_claim_id"]:
        raise ValueError("audit source or new evidence does not match approval")
    before = copy.deepcopy(original)
    after = copy.deepcopy(updated)
    old_companies, new_companies = before.get("companies"), after.get("companies")
    if not isinstance(old_companies, list) or not isinstance(new_companies, list):
        raise ValueError("companies must be arrays")
    if len(old_companies) != len(new_companies):
        raise ValueError("company list changed")
    selected = [(i, company) for i, company in enumerate(old_companies) if company.get("id") == approval["company_id"]]
    if len(selected) != 1:
        raise ValueError("approval company must resolve exactly once")
    idx, old_company = selected[0]
    new_company = new_companies[idx]
    if new_company.get("id") != approval["company_id"]:
        raise ValueError("company order or identity changed")
    old_claims, new_claims = old_company.get("claims"), new_company.get("claims")
    old_evidence, new_evidence = old_company.get("evidence"), new_company.get("evidence")
    if not all(isinstance(value, list) for value in (old_claims, new_claims, old_evidence, new_evidence)):
        raise ValueError("claims and evidence must be arrays")
    if len(new_claims) != len(old_claims) or len(new_evidence) != len(old_evidence) + 1:
        raise ValueError("only one evidence record may be appended")
    if new_evidence[-1] != approval["evidence"]:
        raise ValueError("appended evidence does not exactly match approval")
    if new_evidence[:-1] != old_evidence:
        raise ValueError("existing evidence must remain unchanged")
    candidates = [i for i, c in enumerate(old_claims) if c.get("id") == approval["existing_claim_id"]]
    if len(candidates) != 1:
        raise ValueError("target claim must resolve exactly once")
    ci = candidates[0]
    old_claim, new_claim = old_claims[ci], new_claims[ci]
    if fingerprint_claim(old_claim) != approval["expected_claim_sha256"]:
        raise ValueError("approval fingerprint does not match existing claim")
    expected = copy.deepcopy(old_claim)
    if not isinstance(expected.get("evidence_ids"), list):
        raise ValueError("target evidence_ids must be an array")
    expected["evidence_ids"].append(approval["evidence"]["id"])
    if new_claim != expected:
        raise ValueError("target claim changed beyond approved evidence_ids append")
    for i, old in enumerate(old_claims):
        if i != ci and new_claims[i] != old:
            raise ValueError("an unrelated claim changed")
    # Remove only the explicitly approved changes. The resulting database must
    # be identical to the original, including order, metadata, nested values.
    new_claims[ci] = copy.deepcopy(old_claim)
    new_evidence.pop()
    if after != before:
        raise ValueError("unapproved database fields changed")
    return {
        "verification_status": "exact_append_only_change",
        "company_id": approval["company_id"], "claim_id": approval["existing_claim_id"],
        "new_evidence_id": approval["evidence"]["id"],
        "unapproved_changes": 0,
        "claim_status_changed": False,
        "source_truth_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--updated", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        inputs = [json.loads(p.read_text(encoding="utf-8")) for p in
                  (args.original, args.updated, args.approval, args.audit)]
        verified = verify_patch(*inputs)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(verified, indent=2) + "\n", encoding="utf-8")
        print("PASS: exact evidence-only update; no unapproved database fields changed.")
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
