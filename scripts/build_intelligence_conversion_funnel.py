#!/usr/bin/env python3
"""Build a conservative Claim-to-database conversion funnel.

Operational review decisions are not factual verification. Database integration
is counted only from an explicit, human-maintained merged-PR manifest.
"""
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path

SHA=re.compile(r"^[0-9a-f]{40}$")
DATASET=re.compile(r"^[a-z0-9][a-z0-9_-]{1,79}$")

def stamp(value, field):
    if not isinstance(value,str): raise ValueError(field+" must be timezone-aware ISO-8601")
    try: d=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as e: raise ValueError("invalid "+field) from e
    if d.utcoffset() is None: raise ValueError(field+" requires timezone")
    return d

def nonnegative(value, field):
    if type(value) is not int or value<0: raise ValueError(field+" must be a nonnegative integer")
    return value

def build(review, ledger, integration):
    if not isinstance(review,dict) or review.get("schema_version")!="1.0" or review.get("observation_state")!="cache_persisted" or review.get("state_is_approval") is not False:
        raise ValueError("review state must be persisted observation, not approval")
    summary=review.get("summary")
    if not isinstance(summary,dict): raise ValueError("review-state summary missing")
    current=nonnegative(summary.get("tracked_current_claims"),"tracked_current_claims")
    backlog=nonnegative(summary.get("tracked_backlog_claims"),"tracked_backlog_claims")
    states=summary.get("review_states")
    keys=("pending","needs_more_evidence","rejected","accepted_for_evidence_attachment")
    if not isinstance(states,dict): raise ValueError("review-state counts missing")
    counts={k:nonnegative(states.get(k),k) for k in keys}
    if sum(counts.values())!=backlog: raise ValueError("review-state counts do not reconcile with backlog")
    if not isinstance(ledger,dict) or set(ledger)!={"schema_version","decisions"} or ledger.get("schema_version")!="1.0" or not isinstance(ledger.get("decisions"),list):
        raise ValueError("decision ledger schema mismatch")
    decisions={}
    for row in ledger["decisions"]:
        if not isinstance(row,dict): raise ValueError("malformed decision row")
        cid=row.get("claim_id")
        if not isinstance(cid,str) or not cid or cid in decisions: raise ValueError("duplicate or invalid decision Claim ID")
        if row.get("decision") not in keys[1:]: raise ValueError("unsupported decision")
        if not isinstance(row.get("reviewer"),str) or not row["reviewer"].strip(): raise ValueError("decision reviewer missing")
        if not isinstance(row.get("notes"),str) or len(row["notes"].strip())<30: raise ValueError("decision rationale too short")
        stamp(row.get("decided_at"),"decided_at")
        decisions[cid]=row
    if not isinstance(integration,dict) or set(integration)!={"schema_version","records"} or integration.get("schema_version")!="1.0" or not isinstance(integration.get("records"),list):
        raise ValueError("database integration manifest schema mismatch")
    records={}
    for row in integration["records"]:
        if not isinstance(row,dict) or set(row)!={"claim_id","target_dataset","pull_request","merged_commit","integrated_at","reviewer","notes"}:
            raise ValueError("integration record fields mismatch")
        cid=row["claim_id"]
        if not isinstance(cid,str) or not cid or cid in records: raise ValueError("duplicate or invalid integrated Claim ID")
        if cid not in decisions or decisions[cid]["decision"]!="accepted_for_evidence_attachment":
            raise ValueError("only explicitly accepted Claims may be recorded as integrated")
        if not isinstance(row["target_dataset"],str) or not DATASET.fullmatch(row["target_dataset"]): raise ValueError("invalid target dataset")
        if type(row["pull_request"]) is not int or row["pull_request"]<1: raise ValueError("invalid merged pull request number")
        if not isinstance(row["merged_commit"],str) or not SHA.fullmatch(row["merged_commit"]): raise ValueError("merged commit must be a full Git SHA")
        stamp(row["integrated_at"],"integrated_at")
        if not isinstance(row["reviewer"],str) or not row["reviewer"].strip(): raise ValueError("integration reviewer missing")
        if not isinstance(row["notes"],str) or len(row["notes"].strip())<30: raise ValueError("integration notes too short")
        records[cid]=row
    accepted_ids={cid for cid,row in decisions.items() if row["decision"]=="accepted_for_evidence_attachment"}
    if not set(records).issubset(accepted_ids): raise ValueError("integration records must be a subset of accepted Claims")
    decision_counts={k:sum(row["decision"]==k for row in decisions.values()) for k in keys[1:]}
    if any(decision_counts[k]>counts[k] for k in keys[1:]): raise ValueError("ledger decisions exceed persisted review-state counts")
    integrated=len(records)
    return {
      "schema_version":"1.0","generated_at":review.get("generated_at"),
      "read_only":True,"factual_verification_performed":False,
      "metrics":{
        "current_discovered_claims":current,"persistent_backlog_claims":backlog,
        "decisions_recorded":len(decisions),"decision_coverage":round(len(decisions)/backlog,4) if backlog else None,
        "pending":counts["pending"],"needs_more_evidence":counts["needs_more_evidence"],
        "rejected":counts["rejected"],"accepted_for_evidence_attachment":counts["accepted_for_evidence_attachment"],
        "accepted_decisions_recorded":decision_counts["accepted_for_evidence_attachment"],
        "database_integrated_claims":integrated,
        "accepted_to_integrated_rate":round(integrated/decision_counts["accepted_for_evidence_attachment"],4) if decision_counts["accepted_for_evidence_attachment"] else None,
        "integrated_by_dataset":{k:sum(r["target_dataset"]==k for r in records.values()) for k in sorted({r["target_dataset"] for r in records.values()})}
      },
      "availability":{"database_integration":"measured_from_explicit_merged_pr_manifest" if integration["records"] else "no_integration_records"},
      "policy":{
        "review_decisions_are_factual_verification":False,
        "accepted_for_evidence_attachment_is_database_integration":False,
        "integration_requires_explicit_merged_pr_record":True,
        "manifest_records_are_human_assertions_not_independent_authentication":True
      },
      "interpretation":"Counts describe workflow throughput only. An accepted Claim is not integrated until an explicit merged-PR record exists. Neither review nor integration proves technical truth."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review-state",type=Path,required=True);p.add_argument("--ledger",type=Path,required=True)
    p.add_argument("--integration-manifest",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--markdown",type=Path)
    a=p.parse_args()
    try:
        data=build(*(json.loads(x.read_text(encoding="utf-8")) for x in (a.review_state,a.ledger,a.integration_manifest)))
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        if a.markdown:
            m=data["metrics"]; lines=["# Claim-to-Database Conversion Funnel","",f"- Current discovered Claims: {m['current_discovered_claims']}",f"- Persistent backlog: {m['persistent_backlog_claims']}",f"- Explicit human decisions: {m['decisions_recorded']}",f"- Accepted for evidence attachment: {m['accepted_for_evidence_attachment']}",f"- Database-integrated Claims (merged PR manifest): {m['database_integrated_claims']}","", "These are workflow counts, not factual verification."]
            a.markdown.parent.mkdir(parents=True,exist_ok=True);a.markdown.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("PASS: conversion funnel generated; factual verification remains false.");return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        print("FAIL: "+str(e),file=sys.stderr);return 1
if __name__=="__main__": raise SystemExit(main())
