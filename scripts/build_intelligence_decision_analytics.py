#!/usr/bin/env python3
"""Summarize human Claim decisions, explicit reason codes and review latency.

Free-text notes are never classified automatically. This report is operational
analytics only; it does not infer factual correctness or reviewer agreement.
"""
from __future__ import annotations
import argparse, json, math, sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

OUTCOMES=("needs_more_evidence","rejected","accepted_for_evidence_attachment")
REASONS=(
 "source_not_supporting_claim","source_unavailable","insufficient_technical_detail",
 "missing_configuration_or_version","missing_measurement_conditions",
 "contradictory_evidence","duplicate_or_syndicated","out_of_scope",
 "stale_or_superseded","unclear_attribution","independent_corroboration_needed","other"
)

def parse_time(value,field):
    if not isinstance(value,str): raise ValueError(field+" must be timezone-aware ISO-8601")
    try: dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise ValueError("invalid "+field) from exc
    if dt.utcoffset() is None: raise ValueError(field+" requires timezone")
    return dt

def count(value,field):
    if type(value) is not int or value<0: raise ValueError(field+" must be a nonnegative integer")
    return value

def percentile(values,p):
    if not values:return None
    ordered=sorted(values)
    return ordered[max(0,math.ceil(p*len(ordered))-1)]

def stats(values):
    ordered=sorted(values)
    if not ordered:return {"samples":0,"median_days":None,"p90_days":None,"max_days":None}
    mid=len(ordered)//2
    median=ordered[mid] if len(ordered)%2 else (ordered[mid-1]+ordered[mid])/2
    return {"samples":len(ordered),"median_days":round(median,2),
            "p90_days":round(percentile(ordered,.90),2),"max_days":round(ordered[-1],2)}

def build(review,ledger,reasons):
    if not isinstance(review,dict) or review.get("schema_version")!="1.0" or review.get("observation_state")!="cache_persisted" or review.get("state_is_approval") is not False:
        raise ValueError("review state must be persisted observation, not approval")
    generated=parse_time(review.get("generated_at"),"review generated_at")
    summary=review.get("summary")
    if not isinstance(summary,dict):raise ValueError("review-state summary missing")
    backlog=count(summary.get("tracked_backlog_claims"),"tracked_backlog_claims")
    current=count(summary.get("tracked_current_claims"),"tracked_current_claims")
    states=summary.get("review_states")
    if not isinstance(states,dict):raise ValueError("review-state outcome counts missing")
    expected={key:count(states.get(key),key) for key in ("pending",)+OUTCOMES}
    if sum(expected.values())!=backlog:raise ValueError("review-state counts do not reconcile with backlog")
    aging=review.get("claim_aging")
    if not isinstance(aging,list):raise ValueError("claim_aging array missing")
    first_seen={}
    unresolved_age={"within_7d":0,"7_to_13d":0,"14_to_29d":0,"30d_plus":0}
    for row in aging:
        if not isinstance(row,dict) or not isinstance(row.get("claim_id"),str) or not row["claim_id"] or row["claim_id"] in first_seen:
            raise ValueError("duplicate or malformed Claim aging row")
        first_seen[row["claim_id"]]=parse_time(row.get("first_seen_at"),"first_seen_at")
        age=count(row.get("days_since_first_seen"),"days_since_first_seen")
        if row.get("review_state") in ("pending","needs_more_evidence"):
            bucket="within_7d" if age<7 else "7_to_13d" if age<14 else "14_to_29d" if age<30 else "30d_plus"
            unresolved_age[bucket]+=1
    if len(aging)!=backlog:raise ValueError("Claim aging rows do not match persistent backlog")
    if not isinstance(ledger,dict) or set(ledger)!={"schema_version","decisions"} or ledger.get("schema_version")!="1.0" or not isinstance(ledger.get("decisions"),list):
        raise ValueError("decision ledger schema mismatch")
    decisions={}
    for row in ledger["decisions"]:
        required={"claim_id","decision","reviewer","decided_at","notes"}
        if not isinstance(row,dict) or set(row)!=required:raise ValueError("decision row fields mismatch")
        cid=row["claim_id"]
        if not isinstance(cid,str) or not cid or cid in decisions:raise ValueError("duplicate or invalid decision Claim ID")
        if cid not in first_seen:raise ValueError("decision references Claim missing from persisted aging state: "+cid)
        if row["decision"] not in OUTCOMES:raise ValueError("unsupported decision outcome")
        if not isinstance(row["reviewer"],str) or not row["reviewer"].strip():raise ValueError("decision reviewer missing")
        if not isinstance(row["notes"],str) or len(row["notes"].strip())<30:raise ValueError("decision rationale too short")
        decided=parse_time(row["decided_at"],"decided_at")
        if decided>generated:raise ValueError("decision timestamp is later than analytics snapshot")
        decisions[cid]={**row,"_decided":decided}
    outcome_counts={key:sum(row["decision"]==key for row in decisions.values()) for key in OUTCOMES}
    if any(outcome_counts[key]>expected[key] for key in OUTCOMES):raise ValueError("ledger decisions exceed persisted review-state outcomes")
    if not isinstance(reasons,dict) or set(reasons)!={"schema_version","records"} or reasons.get("schema_version")!="1.0" or not isinstance(reasons["records"],list):
        raise ValueError("reason-code registry schema mismatch")
    coded={}
    for row in reasons["records"]:
        required={"claim_id","primary_reason","secondary_reasons","coded_by","coded_at","rationale"}
        if not isinstance(row,dict) or set(row)!=required:raise ValueError("reason-code row fields mismatch")
        cid=row["claim_id"]
        if not isinstance(cid,str) or cid not in decisions or cid in coded:raise ValueError("reason code must uniquely reference a decided Claim")
        primary=row["primary_reason"]
        secondary=row["secondary_reasons"]
        if primary not in REASONS:raise ValueError("unsupported primary reason code")
        if not isinstance(secondary,list) or len(secondary)>4 or any(x not in REASONS for x in secondary) or len(set(secondary))!=len(secondary) or primary in secondary:
            raise ValueError("invalid secondary reason codes")
        if not isinstance(row["coded_by"],str) or not row["coded_by"].strip():raise ValueError("reason-code reviewer missing")
        rationale=row["rationale"]
        if not isinstance(rationale,str) or len(rationale.strip())<30:raise ValueError("reason-code rationale must have at least 30 characters")
        coded_at=parse_time(row["coded_at"],"coded_at")
        if coded_at<decisions[cid]["_decided"] or coded_at>generated:raise ValueError("reason-code timestamp must follow decision and precede snapshot")
        coded[cid]=row
    latency=defaultdict(list)
    unavailable_latency=0
    for cid,row in decisions.items():
        days=(row["_decided"]-first_seen[cid]).total_seconds()/86400
        if days<0:unavailable_latency+=1
        else:latency[row["decision"]].append(days)
    all_latency=[v for values in latency.values() for v in values]
    primary_counts=Counter()
    secondary_counts=Counter()
    by_outcome={key:Counter() for key in OUTCOMES}
    for cid,row in coded.items():
        code=row["primary_reason"];primary_counts[code]+=1;by_outcome[decisions[cid]["decision"]][code]+=1
        secondary_counts.update(row["secondary_reasons"])
    unresolved=sum(unresolved_age.values())
    return {
      "schema_version":"1.0","generated_at":review["generated_at"],
      "read_only":True,"factual_verification_performed":False,
      "metrics":{
        "current_claims":current,"persistent_backlog":backlog,
        "decisions_recorded":len(decisions),
        "decision_coverage":round(len(decisions)/backlog,4) if backlog else None,
        "outcome_counts":outcome_counts,
        "reason_coded_decisions":len(coded),
        "reason_code_coverage":round(len(coded)/len(decisions),4) if decisions else None,
        "uncoded_decision_claim_ids":sorted(set(decisions)-set(coded)),
        "primary_reason_counts":dict(sorted(primary_counts.items())),
        "secondary_reason_counts":dict(sorted(secondary_counts.items())),
        "reason_counts_by_outcome":{key:dict(sorted(value.items())) for key,value in by_outcome.items()},
        "review_latency_days":{"overall":stats(all_latency),
          "by_outcome":{key:stats(latency[key]) for key in OUTCOMES},
          "unavailable_due_to_cache_reset_or_clock_order":unavailable_latency},
        "unresolved_claims":unresolved,"unresolved_age_buckets":unresolved_age,
        "overdue_14d_or_more":unresolved_age["14_to_29d"]+unresolved_age["30d_plus"]
      },
      "taxonomy":{"version":"1.0","allowed_reason_codes":list(REASONS),
        "reason_codes_are_explicit_human_labels":True,"free_text_notes_auto_classified":False},
      "policy":{"decision_is_factual_verification":False,"reason_codes_are_human_assertions":True,
        "latency_starts_at_first_observed_in_persistent_cache_not_publication":True,
        "reviewer_identity_independently_authenticated":False},
      "interpretation":"Decision outcomes and reason codes are operational metadata. Reason coverage counts explicit human-coded records only; free-text notes are never classified. Review latency starts at first observation in the persisted cache, not publication. Neither a decision nor its reason code verifies technical truth."
    }

def markdown(report):
    m=report["metrics"];lat=m["review_latency_days"]["overall"]
    lines=["# Intelligence Decision Analytics","",
      f"- Current Claims: {m['current_claims']}",
      f"- Persistent backlog: {m['persistent_backlog']}",
      f"- Explicit decisions: {m['decisions_recorded']} ({'N/A' if m['decision_coverage'] is None else format(m['decision_coverage'],'.1%')} coverage)",
      f"- Reason-coded decisions: {m['reason_coded_decisions']} ({'N/A' if m['reason_code_coverage'] is None else format(m['reason_code_coverage'],'.1%')} coverage)",
      f"- Unresolved Claims overdue 14+ days: {m['overdue_14d_or_more']}",
      f"- Median decision latency: {'N/A' if lat['median_days'] is None else str(lat['median_days'])+' days'}",
      "","## Decision outcomes",""]
    lines += [f"- {key}: {value}" for key,value in m["outcome_counts"].items()]
    lines += ["","## Explicit primary reason codes",""]
    lines += [f"- {key}: {value}" for key,value in m["primary_reason_counts"].items()] or ["- No human reason codes recorded."]
    lines += ["","Free-text reviewer notes are not automatically classified. These metrics do not measure factual accuracy."]
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review-state",type=Path,required=True);p.add_argument("--ledger",type=Path,required=True)
    p.add_argument("--reason-codes",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--markdown",type=Path)
    a=p.parse_args()
    try:
        result=build(*(json.loads(path.read_text(encoding="utf-8")) for path in (a.review_state,a.ledger,a.reason_codes)))
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        if a.markdown:
            a.markdown.parent.mkdir(parents=True,exist_ok=True);a.markdown.write_text(markdown(result),encoding="utf-8")
        print("PASS: decision analytics generated; no factual verification inferred.");return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FAIL: "+str(exc),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
