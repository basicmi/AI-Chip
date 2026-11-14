#!/usr/bin/env python3
"""Persist review-queue first-seen timestamps and emit aging alerts.

The state is a cache of observations, not a source of factual verification.
Only a committed human decision ledger can mark a candidate handled/deferred.
"""
from __future__ import annotations
import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REVIEW_STATUSES={"pending","needs_more_evidence","rejected","accepted_for_evidence_attachment"}
DECISION_STATUSES=REVIEW_STATUSES-{"pending"}
ALERT_THRESHOLDS=(7,14,30)

def parse_utc(value):
    if not isinstance(value,str): raise ValueError("timestamp must be an ISO 8601 string")
    try:
        dt=datetime.fromisoformat(value.replace("Z","+00:00"))
        if dt.tzinfo is None: raise ValueError("timezone required")
        return dt.astimezone(timezone.utc)
    except ValueError as exc: raise ValueError("invalid UTC timestamp: "+value) from exc

def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00","Z")

def load_decisions(ledger, allowed_ids, now):
    if ledger is None: return {}
    if not isinstance(ledger,dict) or set(ledger)!={"schema_version","decisions"} or ledger.get("schema_version")!="1.0" or not isinstance(ledger.get("decisions"),list):
        raise ValueError("human review decision ledger must be schema 1.0")
    result={}
    for decision in ledger["decisions"]:
        if not isinstance(decision,dict) or set(decision)!={"claim_id","decision","reviewer","decided_at","notes"}:
            raise ValueError("human decision must have exactly claim_id, decision, reviewer, decided_at and notes")
        cid=decision["claim_id"]
        if not isinstance(cid,str) or cid not in allowed_ids or cid in result:
            raise ValueError("human decision references unknown or duplicate Claim ID")
        if decision["decision"] not in DECISION_STATUSES:
            raise ValueError("invalid human decision outcome")
        if not isinstance(decision["reviewer"],str) or not decision["reviewer"].strip():
            raise ValueError("human reviewer identity required")
        if not isinstance(decision["notes"],str) or len(decision["notes"].strip())<30:
            raise ValueError("human review notes must have at least 30 characters")
        decided=parse_utc(decision["decided_at"])
        if decided>now: raise ValueError("human decision cannot be future-dated")
        result[cid]={**decision,"decided_at":iso(decided)}
    return result

def update_state(triage, claims, previous=None, ledger=None, *, now=None, retention_days=180):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError("now must be timezone-aware")
    now=now.astimezone(timezone.utc)
    if not isinstance(triage,dict) or triage.get("schema_version")!="1.0" or not isinstance(triage.get("queue"),list):
        raise ValueError("expected triage schema 1.0")
    if not isinstance(claims,dict) or claims.get("schema_version")!="1.0" or not isinstance(claims.get("claims"),list):
        raise ValueError("expected Claim Extraction schema 1.0")
    ids={c.get("claim_id") for c in claims["claims"]}
    if len(ids)!=len(claims["claims"]) or any(not isinstance(cid,str) or not cid for cid in ids):
        raise ValueError("Claim IDs must be unique and non-empty")
    if any(c.get("review_status")!="unverified_candidate" for c in claims["claims"]):
        raise ValueError("only unverified extracted Claims may be tracked")
    if triage.get("summary",{}).get("input_claims")!=len(ids) or triage.get("summary",{}).get("automatically_verified")!=0:
        raise ValueError("triage count or verification policy mismatch")
    covered=set()
    for item in triage["queue"]:
        for cid in item.get("related_claim_ids",[]):
            if cid not in ids or cid in covered: raise ValueError("triage has invalid or duplicated Claim references")
            covered.add(cid)
    # A priority-only top-N queue is permitted; every claim remains tracked
    # even if it was not included in the truncated review presentation.
    previous=previous if previous is not None else {"schema_version":"1.0","items":{}}
    if not isinstance(previous,dict) or previous.get("schema_version")!="1.0" or not isinstance(previous.get("items"),dict):
        raise ValueError("invalid persisted review state")
    items=copy.deepcopy(previous["items"])
    # Preserve the original review priority and source even when the candidate
    # is absent from later *change-only* weekly discovery reports.
    priority_by_id={}
    for group in triage["queue"]:
        for cid in group["related_claim_ids"]:
            priority_by_id[cid]={"score":group.get("score",0),"source_url":group.get("source_url"),"topic":group.get("topic")}
    for cid in ids:
        row=items.get(cid)
        if row is None:
            row={"first_seen_at":iso(now),"last_seen_at":iso(now)}
        else:
            if not isinstance(row,dict): raise ValueError("invalid persisted claim record")
            first=parse_utc(row.get("first_seen_at"))
            last=parse_utc(row.get("last_seen_at"))
            if first>now or last>now or first>last: raise ValueError("persisted claim timestamps are inconsistent")
            row={"first_seen_at":iso(first),"last_seen_at":iso(now)}
        meta=priority_by_id.get(cid)
        if meta:
            row.update(meta)
        items[cid]=row
    # Keep historical IDs long enough to survive temporary source-feed gaps;
    # do not assert that absent Claims have been reviewed or rejected.
    for cid,row in list(items.items()):
        if cid in ids: continue
        if (now-parse_utc(row["last_seen_at"])).days>retention_days: del items[cid]
    decisions=load_decisions(ledger,set(items),now)
    aging=[]
    for cid in sorted(items):
        first=parse_utc(items[cid]["first_seen_at"])
        waiting=max(0,(now-first).days)
        decision=decisions.get(cid)
        state=decision["decision"] if decision else "pending"
        level="overdue_30d" if waiting>=30 else "overdue_14d" if waiting>=14 else "overdue_7d" if waiting>=7 else "within_7d"
        if state=="rejected" or state=="accepted_for_evidence_attachment": level="handled"
        elif state=="needs_more_evidence" and waiting>=14: level="follow_up_needed"
        aging.append({"claim_id":cid,"first_seen_at":items[cid]["first_seen_at"],"last_seen_at":items[cid]["last_seen_at"],
            "observed_this_run":cid in ids,"days_since_first_seen":waiting,
            "last_priority_score":items[cid].get("score"),
            "source_url":items[cid].get("source_url"),
            "topic":items[cid].get("topic"),
            "review_state":state,"alert_level":level,
            "decision_recorded_at":decision["decided_at"] if decision else None,
            "decision_reviewer":decision["reviewer"] if decision else None,
            "review_is_factual_verification":False})
    lookup={x["claim_id"]:x for x in aging}
    presentation=[]
    for group in triage["queue"]:
        attached=[lookup[cid] for cid in group["related_claim_ids"]]
        pending=[row for row in attached if row["review_state"] in ("pending","needs_more_evidence")]
        presentation.append({**group,
            "oldest_unhandled_days":max((x["days_since_first_seen"] for x in pending),default=None),
            "review_state_counts":{key:sum(x["review_state"]==key for x in attached) for key in sorted(REVIEW_STATUSES)},
            "aging_alerts":sorted({x["alert_level"] for x in pending if x["alert_level"]!="within_7d"})})
    counts={key:sum(x["review_state"]==key for x in aging) for key in sorted(REVIEW_STATUSES)}
    alert_counts={level:sum(x["alert_level"]==level for x in aging) for level in
                  ("overdue_7d","overdue_14d","overdue_30d","follow_up_needed")}
    output={"schema_version":"1.0","generated_at":iso(now),"observation_state":"cache_persisted",
        "state_is_approval":False,"summary":{"tracked_current_claims":len(ids),"tracked_backlog_claims":len(items),
        "backlog_not_observed_this_run":len(items)-len(ids),"review_states":counts,
        "aging_alerts":alert_counts,"unknown_first_seen_if_cache_reset":True},
        "claim_aging":aging,"queue":presentation,
        "aging_backlog":sorted(
            [row for row in aging if row["review_state"] in ("pending","needs_more_evidence")],
            key=lambda x:(-x["days_since_first_seen"],-(x["last_priority_score"] or 0),x["claim_id"])),
        "policy":"First-seen time is when this cache first observed a Claim, not its publication date. Missing cache resets age. Only committed explicit review decisions change review state. None of these decisions verifies factual claims."}
    state={"schema_version":"1.0","last_run_at":iso(now),"items":items}
    return output,state

def markdown(report):
    s=report["summary"]
    lines=["# Persistent Intelligence Review State","",
           f"- Current run Claim IDs: {s['tracked_current_claims']}",
           f"- Persistent review backlog: {s['tracked_backlog_claims']} (absent from this run: {s['backlog_not_observed_this_run']})",
           f"- Pending: {s['review_states']['pending']}",
           f"- Needs more evidence: {s['review_states']['needs_more_evidence']}",
           f"- Overdue 7/14/30 days: {s['aging_alerts']['overdue_7d']} / {s['aging_alerts']['overdue_14d']} / {s['aging_alerts']['overdue_30d']}",
           "- **Age is based on first discovery in the persistent cache, not paper publication.**",
           "- Decisions do not establish independent factual verification.","","## Unhandled high-priority items",""]
    for item in report["aging_backlog"][:40]:
        lines.append(f"- {item['claim_id']} · wait {item['days_since_first_seen']}d · latest score {item.get('last_priority_score')} · alert {item['alert_level']} · observed this run {item['observed_this_run']}")
    return "\n".join(lines)+"\n"

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage",type=Path,required=True)
    parser.add_argument("--claims",type=Path,required=True)
    parser.add_argument("--state",type=Path,required=True)
    parser.add_argument("--ledger",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--markdown",type=Path)
    args=parser.parse_args()
    try:
        triage=json.loads(args.triage.read_text(encoding="utf-8"))
        claims=json.loads(args.claims.read_text(encoding="utf-8"))
        previous=json.loads(args.state.read_text(encoding="utf-8")) if args.state.exists() else None
        ledger=json.loads(args.ledger.read_text(encoding="utf-8")) if args.ledger else None
        result,state=update_state(triage,claims,previous,ledger)
        for path in (args.output,args.state):
            path.parent.mkdir(parents=True,exist_ok=True)
        # Only write cache state after successful validation.
        args.state.write_text(json.dumps(state,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True,exist_ok=True)
            args.markdown.write_text(markdown(result),encoding="utf-8")
        print(f"PASS: {result['summary']['tracked_current_claims']} Claims; aging alert counts {result['summary']['aging_alerts']}")
    except (OSError,ValueError,TypeError,KeyError) as error:
        print("FAIL: "+str(error),file=sys.stderr)
        return 1
    return 0
if __name__=="__main__": raise SystemExit(main())
