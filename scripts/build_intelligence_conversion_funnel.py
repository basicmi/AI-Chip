#!/usr/bin/env python3
"""Build a read-only Claim-to-database conversion funnel from one discovery run.

A human decision of accepted_for_evidence_attachment is eligibility to prepare
an attachment, not factual verification or permission for automatic writes.
Only explicit, reviewed integration receipts for existing registry records
count as tracked database integrations.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from validate_intelligence_review_ledger import load_decisions

REGISTRIES = {
    "data/company-profiles.json",
    "data/benchmark-results.json",
    "data/compatibility.json",
    "data/model-support.json",
    "data/workloads.json",
}
ID_KEYS = {
    "id", "claim_id", "company_id", "product_id", "result_id",
    "platform_id", "workload_id", "model_id", "evidence_id",
    "benchmark_id", "project_id", "integration_id",
}
STATES = ("pending", "needs_more_evidence", "rejected", "accepted_for_evidence_attachment")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def stamp(value, label):
    if not isinstance(value, str):
        raise ValueError(label + " timestamp is missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(label + " timestamp is invalid") from error
    if parsed.utcoffset() is None:
        raise ValueError(label + " timestamp requires a timezone")
    return parsed.astimezone(timezone.utc)


def nonnegative(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(label + " must be a nonnegative integer")
    return value


def find_record_id(value, wanted):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ID_KEYS and child == wanted:
                return True
            if find_record_id(child, wanted):
                return True
    elif isinstance(value, list):
        return any(find_record_id(child, wanted) for child in value)
    return False


def validate_manifest(manifest, decisions, review_ids, registry_root):
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "integrations", "policy"}:
        raise ValueError("integration manifest must contain exactly schema_version, integrations and policy")
    if manifest.get("schema_version") != "1.0" or not isinstance(manifest.get("integrations"), list):
        raise ValueError("integration manifest must use schema 1.0 and an integrations array")
    policy = manifest.get("policy")
    if not isinstance(policy, dict) or policy.get("manual_only") is not True or policy.get("automatic_registry_writes") is not False:
        raise ValueError("integration manifest must prohibit automatic registry writes")
    rows = manifest["integrations"]
    seen = set()
    integrated_claims = set()
    normalized = []
    registry_cache = {}
    for row in rows:
        required = {
            "claim_id", "target_registry", "target_record_id", "merged_pr_url",
            "merge_commit_sha", "integrated_at", "reviewer", "notes",
        }
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError("integration receipt must contain exactly the required audit fields")
        cid = row["claim_id"]
        if not isinstance(cid, str) or cid not in review_ids:
            raise ValueError("integration receipt references an unknown Claim ID")
        if decisions.get(cid, {}).get("decision") != "accepted_for_evidence_attachment":
            raise ValueError("only accepted_for_evidence_attachment Claims may have integration receipts")
        registry = row["target_registry"]
        record_id = row["target_record_id"]
        if registry not in REGISTRIES:
            raise ValueError("integration receipt targets a non-allowlisted registry")
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("integration receipt requires a target record ID")
        key = (cid, registry, record_id)
        if key in seen:
            raise ValueError("duplicate Claim-to-record integration receipt")
        seen.add(key)
        parsed = urlparse(row["merged_pr_url"]) if isinstance(row["merged_pr_url"], str) else None
        if (parsed is None or parsed.scheme != "https" or parsed.netloc != "github.com"
                or not re.fullmatch(r"/basicmi/AI-Chip/pull/[1-9][0-9]*", parsed.path)
                or parsed.query or parsed.fragment):
            raise ValueError("integration receipt requires a canonical merged AI-Chip pull request URL")
        if not isinstance(row["merge_commit_sha"], str) or not SHA40.fullmatch(row["merge_commit_sha"]):
            raise ValueError("integration receipt requires a full 40-character merge commit SHA")
        integrated_at = stamp(row["integrated_at"], "integration")
        reviewer = row["reviewer"]
        notes = row["notes"]
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("integration receipt requires a reviewer")
        if not isinstance(notes, str) or len(notes.strip()) < 30:
            raise ValueError("integration receipt notes must contain at least 30 characters")
        if registry not in registry_cache:
            path = registry_root / registry
            try:
                registry_cache[registry] = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ValueError("cannot read target registry " + registry) from error
        if not find_record_id(registry_cache[registry], record_id):
            raise ValueError("target record ID does not exist in " + registry)
        integrated_claims.add(cid)
        normalized.append({
            "claim_id": cid, "target_registry": registry,
            "target_record_id": record_id, "merged_pr_url": row["merged_pr_url"],
            "merge_commit_sha": row["merge_commit_sha"],
            "integrated_at": integrated_at.isoformat().replace("+00:00", "Z"),
            "reviewer": reviewer.strip(),
        })
    return normalized, integrated_claims


def build_funnel(discovery, claims, triage, review_state, ledger, manifest, registry_root):
    for name, data, version in (
        ("discovery", discovery, "1.1"), ("claims", claims, "1.0"),
        ("triage", triage, "1.0"), ("review-state", review_state, "1.0"),
    ):
        if not isinstance(data, dict) or data.get("schema_version") != version:
            raise ValueError(name + " has an unsupported schema version")
    if discovery.get("read_only") is not True:
        raise ValueError("discovery report must be read-only")
    if review_state.get("observation_state") != "cache_persisted" or review_state.get("state_is_approval") is not False:
        raise ValueError("review state must be a persisted observation, not approval")
    dtime = stamp(discovery.get("generated_at"), "discovery")
    ctime = stamp(claims.get("generated_at"), "claims")
    ttime = stamp(triage.get("generated_at"), "triage")
    rtime = stamp(review_state.get("generated_at"), "review-state")
    if triage.get("claim_report_generated_at") != claims.get("generated_at"):
        raise ValueError("triage and Claim extraction reports do not match")
    candidate_count = nonnegative(discovery.get("candidate_count"), "discovery candidate_count")
    if nonnegative(claims.get("input_candidate_count"), "extraction input_candidate_count") != candidate_count:
        raise ValueError("discovery and extraction candidate counts disagree")
    extracted = nonnegative(claims.get("claim_count"), "extracted Claim count")
    if not isinstance(claims.get("claims"), list) or len(claims["claims"]) != extracted:
        raise ValueError("extracted Claim count does not match Claim rows")
    triage_summary = triage.get("summary")
    if not isinstance(triage_summary, dict) or nonnegative(triage_summary.get("input_claims"), "triage input_claims") != extracted:
        raise ValueError("triage input count does not match extracted Claims")
    triage_groups = nonnegative(triage_summary.get("triage_groups"), "triage groups")
    collapsed = nonnegative(triage_summary.get("collapsed_duplicate_claims"), "collapsed duplicate Claims")
    if triage_groups + collapsed != extracted:
        raise ValueError("triage groups plus collapsed duplicates must reconcile to extracted Claims")

    state_summary = review_state.get("summary")
    items = review_state.get("items")
    if not isinstance(state_summary, dict) or not isinstance(items, dict):
        raise ValueError("review-state summary and items are required")
    backlog = nonnegative(state_summary.get("tracked_backlog_claims"), "tracked backlog")
    current = nonnegative(state_summary.get("tracked_current_claims"), "tracked current Claims")
    if backlog != len(items) or current != extracted:
        raise ValueError("review-state counts do not match tracked Claim IDs")
    review_ids = set(items)
    if any(not isinstance(cid, str) or not cid for cid in review_ids):
        raise ValueError("review-state contains an invalid Claim ID")
    decisions = load_decisions(ledger, review_ids, now=datetime.now(timezone.utc))
    states = state_summary.get("review_states")
    if not isinstance(states, dict):
        raise ValueError("review-state decision counts are missing")
    counts = {key: nonnegative(states.get(key), "review-state " + key) for key in STATES}
    if sum(counts.values()) != backlog:
        raise ValueError("review-state statuses do not reconcile to backlog")
    actual = {key: 0 for key in STATES}
    for decision in decisions.values():
        actual[decision["decision"]] += 1
    if any(actual[key] != counts[key] for key in STATES if key != "pending"):
        raise ValueError("review-state decisions do not match the committed human decision ledger")
    if counts["pending"] != backlog - len(decisions):
        raise ValueError("pending review count does not match unreviewed backlog")
    normalized, integrated_claims = validate_manifest(manifest, decisions, review_ids, registry_root)
    accepted_ids = {cid for cid, row in decisions.items()
                    if row["decision"] == "accepted_for_evidence_attachment"}
    if not integrated_claims.issubset(accepted_ids):
        raise ValueError("integrated Claims must be accepted for evidence attachment")
    candidates_with_claims = nonnegative(claims.get("candidate_count_with_claims"), "candidates with Claims")
    if candidates_with_claims > candidate_count:
        raise ValueError("candidates with Claims exceed discovered candidates")
    decisions_count = len(decisions)

    def rate(n, d):
        return round(n / d, 4) if d else None

    metrics = {
        "discovery_candidates": candidate_count,
        "candidates_with_claims": candidates_with_claims,
        "claims_extracted": extracted,
        "triage_groups": triage_groups,
        "duplicate_claims_collapsed": collapsed,
        "persistent_review_backlog": backlog,
        "human_decisions_recorded": decisions_count,
        "review_states": counts,
        "decision_coverage": {"numerator": decisions_count, "denominator": backlog, "rate": rate(decisions_count, backlog)},
        "accepted_for_evidence_attachment": counts["accepted_for_evidence_attachment"],
        "acceptance_rate_among_decisions": {"numerator": counts["accepted_for_evidence_attachment"], "denominator": decisions_count, "rate": rate(counts["accepted_for_evidence_attachment"], decisions_count)},
        "eligible_claims_not_integrated": len(accepted_ids - integrated_claims),
        "integrated_claims": len(integrated_claims),
        "integration_receipts": len(normalized),
        "integration_coverage": {"numerator": len(integrated_claims), "denominator": len(accepted_ids), "rate": rate(len(integrated_claims), len(accepted_ids))},
    }
    stages = [
        {"key": "discovery_candidates", "label": "Discovery candidates", "count": candidate_count},
        {"key": "candidates_with_claims", "label": "Candidates yielding Claims", "count": candidates_with_claims},
        {"key": "claims_extracted", "label": "Extracted Claim candidates", "count": extracted},
        {"key": "triage_groups", "label": "Triage groups", "count": triage_groups},
        {"key": "human_decisions_recorded", "label": "Human decisions", "count": decisions_count},
        {"key": "accepted_for_evidence_attachment", "label": "Eligible for evidence attachment", "count": counts["accepted_for_evidence_attachment"]},
        {"key": "integrated_claims", "label": "Claims with merged integration receipts", "count": len(integrated_claims)},
    ]
    return {
        "schema_version": "1.0",
        "generated_at": rtime.isoformat().replace("+00:00", "Z"),
        "source_timestamps": {
            "discovery": dtime.isoformat().replace("+00:00", "Z"),
            "claims": ctime.isoformat().replace("+00:00", "Z"),
            "triage": ttime.isoformat().replace("+00:00", "Z"),
            "review_state": rtime.isoformat().replace("+00:00", "Z"),
        },
        "metrics": metrics,
        "stages": stages,
        "integration_receipts": normalized,
        "policy": {
            "read_only": True,
            "formal_factual_verification_performed": False,
            "automatic_registry_writes": False,
            "accepted_for_evidence_attachment_is_final_approval": False,
            "integration_count_basis": "Unique Claim IDs with a manually recorded receipt referencing an existing allowlisted registry record and a merged AI-Chip PR.",
            "interpretation": "Stage counts use different denominators and are not a single monotonic conversion funnel. Rates are shown only for explicitly defined denominators. Discovery and extraction are operational counts, not measures of technical truth.",
        },
    }


def markdown_report(report):
    m = report["metrics"]
    def pct(item):
        return "N/A" if item["rate"] is None else f'{item["rate"]:.1%}'
    lines = [
        "# AI Chip — Evidence-to-Database Conversion Funnel", "",
        f"- Generated: {report['generated_at']}",
        f"- Discovery candidates: {m['discovery_candidates']}",
        f"- Candidates yielding Claims: {m['candidates_with_claims']}",
        f"- Extracted Claim candidates: {m['claims_extracted']}",
        f"- Triage groups: {m['triage_groups']} (exact-text duplicates collapsed: {m['duplicate_claims_collapsed']})",
        f"- Persistent review backlog: {m['persistent_review_backlog']}",
        f"- Human decisions recorded: {m['human_decisions_recorded']} ({pct(m['decision_coverage'])} of backlog)",
        f"- Accepted for evidence attachment: {m['accepted_for_evidence_attachment']} ({pct(m['acceptance_rate_among_decisions'])} of decisions)",
        f"- Claims with merged integration receipts: {m['integrated_claims']}",
        f"- Integration coverage of eligible Claims: {pct(m['integration_coverage'])}",
        f"- Eligible Claims not integrated: {m['eligible_claims_not_integrated']}",
        f"- Integration receipts: {m['integration_receipts']}",
        "", "## Review-state breakdown", "",
    ]
    for key in STATES:
        lines.append(f"- {key}: {m['review_states'][key]}")
    lines.extend(["", "## Interpretation and guardrails", "",
        "- accepted_for_evidence_attachment is not factual verification or final registry approval.",
        "- Integration counts require a manual receipt, a merged AI-Chip PR reference and an existing target record ID.",
        "- This report reads registries but never writes to them.",
        "- No automated factual verification or composite confidence score is produced.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("discovery", "claims", "triage", "review-state", "ledger", "integrations", "repo-root", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    try:
        inputs = [json.loads(path.read_text(encoding="utf-8")) for path in (
            args.discovery, args.claims, args.triage, args.review_state, args.ledger, args.integrations)]
        report = build_funnel(*inputs, args.repo_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(markdown_report(report) + "\n", encoding="utf-8")
        print(f"Conversion funnel: {report['metrics']['claims_extracted']} Claims; {report['metrics']['integrated_claims']} with merged integration receipts")
        return 0
    except (OSError, json.JSONDecodeError, ValueError, TypeError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
