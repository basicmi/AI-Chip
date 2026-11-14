#!/usr/bin/env python3
"""Rank unverified intelligence claims for human review, never factual verification.

Inputs are the discovery, claim extraction and evidence graph JSON outputs from
one weekly run. Ranking is transparent and rule-based. Deduplication is only
by exact normalized statement, not semantic or independent-source agreement.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HIGH_TOPICS={"compute","memory_bandwidth","memory_capacity","interconnect","power","performance","availability"}
HIGH_TYPES={"performance_result","availability_or_lifecycle"}
HIGH_RISK={"performance_result","software_or_capability","availability_or_lifecycle"}
SOURCE_VALUES={"vendor_primary","company_primary","official_project","research_paper",
               "independent_media","repository","government_or_regulatory"}
MAX_AGE_DAYS=3650

def norm(text):
    return " ".join(str(text or "").casefold().split()).rstrip(" .;:")

def parse_time(value):
    if not isinstance(value,str): return None
    try:
        dt=datetime.fromisoformat(value.replace("Z","+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except ValueError:
        return None

def score_claim(claim, candidate, *, now):
    source=claim["source"]
    date=parse_time(source.get("published_at"))
    age=max(0,(now-date).days) if date else None
    age_stale=age is None or age>30
    factors={
        "new_or_changed":18 if candidate.get("change_status")=="new" else 12 if candidate.get("change_status")=="updated" else 0,
        "high_impact_topic":18 if claim.get("topic") in HIGH_TOPICS else 0,
        "critical_claim_type":14 if claim.get("claim_type") in HIGH_TYPES else 0,
        "recent_source":14 if age is not None and age<=7 else 8 if age is not None and age<=30 else 0,
        "requires_context_review":10 if claim.get("claim_type") in HIGH_RISK else 0,
        "numeric_claim":8 if type(claim.get("value")) in (float,int) else 0,
        "source_with_provenance":8 if source.get("url") and source.get("source_type") in SOURCE_VALUES else 0,
    }
    score=sum(factors.values())
    return score,factors,age,age_stale

def build_queue(discovery,claims,graph,*,now=None,top=100):
    now=now or datetime.now(timezone.utc)
    if now.utcoffset() is None: raise ValueError("now must be timezone-aware")
    if not 1<=top<=1000: raise ValueError("top must be 1..1000")
    if not isinstance(claims,dict) or claims.get("schema_version")!="1.0" or not isinstance(claims.get("claims"),list):
        raise ValueError("expected claim extraction schema v1.0")
    if not isinstance(graph,dict) or graph.get("schema_version")!="1.0" or not isinstance(graph.get("nodes"),list):
        raise ValueError("expected evidence graph schema v1.0")
    if not isinstance(discovery,dict) or not isinstance(discovery.get("review_queue"),list):
        raise ValueError("expected discovery review queue")
    rows=claims["claims"]
    if claims.get("claim_count")!=len(rows) or graph.get("input_claim_count")!=len(rows):
        raise ValueError("input claim counts mismatch")
    if graph.get("summary",{}).get("independently_verified_claims")!=0:
        raise ValueError("cannot triage a graph claiming automated verification")
    ids=[c.get("claim_id") for c in rows]
    if len(ids)!=len(set(ids)) or any(not isinstance(x,str) or not x for x in ids):
        raise ValueError("duplicate or invalid claim IDs")
    if any(c.get("review_status")!="unverified_candidate" for c in rows):
        raise ValueError("only unverified claims can enter triage")
    graph_claims={n.get("claim_id") for n in graph["nodes"] if n.get("type")=="claim_candidate"}
    if graph_claims!=set(ids): raise ValueError("graph claim membership mismatch")
    candidate_map={x["candidate_id"]:x for x in discovery["review_queue"] if isinstance(x,dict) and isinstance(x.get("candidate_id"),str)}
    groups=defaultdict(list)
    scored=[]
    for claim in rows:
        cid=claim["claim_id"]
        if claim.get("candidate_id") not in candidate_map:
            raise ValueError("claim missing from discovery candidates: "+cid)
        candidate=candidate_map[claim["candidate_id"]]
        score,factors,age,stale=score_claim(claim,candidate,now=now)
        key=norm(claim.get("statement"))
        if not key: raise ValueError("claim statement cannot be empty")
        groups[key].append(cid)
        scored.append({"claim_id":cid,"candidate_id":claim["candidate_id"],
            "score":score,"score_factors":factors,"source_age_days":age,"source_stale_or_undated":stale,
            "topic":claim.get("topic"),"claim_type":claim.get("claim_type"),
            "publisher":claim["source"].get("publisher"),"source_url":claim["source"].get("url"),
            "review_status":"unverified_candidate","risk_flags":[]})
    duplicate_ids=set()
    cluster_by_claim={}
    for members in groups.values():
        if len(members)<2: continue
        cluster_id="exact-"+hashlib.sha256(norm(next(c["statement"] for c in rows if c["claim_id"]==members[0])).encode()).hexdigest()[:16]
        for cid in members:
            cluster_by_claim[cid]={"cluster_id":cluster_id,"claim_ids":sorted(members)}
            duplicate_ids.add(cid)
    conflicts=set()
    for group in graph.get("scoped_comparisons",[]):
        if not isinstance(group,dict) or not isinstance(group.get("claim_ids"),list) or not set(group["claim_ids"])<=set(ids):
            raise ValueError("invalid scoped comparison group")
        if group.get("status")=="possible_specification_conflict":
            conflicts.update(group["claim_ids"])
    for row in scored:
        if row["claim_id"] in duplicate_ids: row["risk_flags"].append("exact_text_duplicate_not_independent")
        if row["claim_id"] in conflicts:
            row["risk_flags"].append("reviewer_scoped_possible_specification_conflict")
            row["score"]+=12
            row["score_factors"]["reviewer_scoped_conflict"]=12
        if row["source_stale_or_undated"]: row["risk_flags"].append("source_old_or_undated")
        if row["claim_type"] in HIGH_RISK: row["risk_flags"].append("claim_requires_configuration_evidence")
    scored.sort(key=lambda x:(-x["score"],x["claim_id"]))
    by_id={x["claim_id"]:x for x in scored}
    queue=[]
    collapsed=set()
    for row in scored:
        cid=row["claim_id"]
        if cid in collapsed: continue
        cluster=cluster_by_claim.get(cid)
        if cluster:
            members=cluster["claim_ids"]
            representative=sorted(members,key=lambda x:(-by_id[x]["score"],x))[0]
            if cid!=representative: continue
            collapsed.update(members)
            queue.append({**by_id[representative],"related_claim_ids":members,
                "duplicate_collapsed_count":len(members)-1,
                "note":"Same normalized text only; no independent corroboration implied"})
        else:
            queue.append({**row,"related_claim_ids":[cid],"duplicate_collapsed_count":0})
    queue.sort(key=lambda x:(-x["score"],x["claim_id"]))
    summary={
        "input_claims":len(rows),"triage_groups":len(queue),
        "exact_text_duplicate_groups":sum(len(v)>1 for v in groups.values()),
        "collapsed_duplicate_claims":len(rows)-len(queue),
        "stale_or_undated_claims":sum(x["source_stale_or_undated"] for x in scored),
        "possible_conflict_claims":len(conflicts),
        "needs_human_review":len(rows),"automatically_verified":0
    }
    return {"schema_version":"1.0","generated_at":now.astimezone(timezone.utc).isoformat().replace("+00:00","Z"),
        "claim_report_generated_at":claims.get("generated_at"),
        "evidence_graph_generated_at":graph.get("generated_at"),
        "ranking_method":"transparent_rule_based_v1","score_is_truth_confidence":False,
        "summary":summary,"queue":queue[:top],"total_queue_groups":len(queue),
        "policy":"Ranking and exact-text collapse are for review workload only; no approvals, corroboration or production writes."}

def markdown(report):
    s=report["summary"]
    out=["# Intelligence Review Triage","",
         f"- Source claims: {s['input_claims']}; triage groups: {s['triage_groups']}",
         f"- Collapsed exact-text duplicates: {s['collapsed_duplicate_claims']}",
         f"- Old/undated sources: {s['stale_or_undated_claims']}",
         f"- Reviewer-scoped possible conflict claims: {s['possible_conflict_claims']}",
         "- **Priority score is not confidence in truth. All claims remain unverified.**","",
         "## Review first",""]
    for index,item in enumerate(report["queue"],1):
        out.extend([f"### {index}. Priority {item['score']} · {item['topic']} · {item['claim_id']}",
                    f"- Source: {item['source_url']}",
                    f"- Signals: {', '.join(k for k,v in item['score_factors'].items() if v) or 'none'}",
                    f"- Risk flags: {', '.join(item['risk_flags']) or 'none'}",
                    f"- Related claim IDs: {', '.join(item['related_claim_ids'])}",""])
    return "\n".join(out)+"\n"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("discovery","claims","graph","output"):
        p.add_argument("--"+key,required=True,type=Path)
    p.add_argument("--markdown",type=Path)
    p.add_argument("--top",type=int,default=100)
    args=p.parse_args()
    try:
        documents=[json.loads(getattr(args,key).read_text(encoding="utf-8"))
                   for key in ("discovery","claims","graph")]
        report=build_queue(*documents,top=args.top)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True,exist_ok=True)
            args.markdown.write_text(markdown(report),encoding="utf-8")
        print(f"PASS: {report['summary']['input_claims']} claims, {report['summary']['triage_groups']} review groups")
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print("FAIL: "+str(exc),file=sys.stderr)
        return 1
    return 0
if __name__=="__main__":
    raise SystemExit(main())
