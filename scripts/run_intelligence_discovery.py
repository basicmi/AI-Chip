#!/usr/bin/env python3
"""Discover official AI systems releases and model changes; never edits production registries."""
from __future__ import annotations
import argparse, hashlib, json, sys, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "AI-Chip-Intelligence-Discovery/1.0 (+https://github.com/basicmi/AI-Chip)"

def parse_time(value):
    if not isinstance(value, str): return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.utcoffset() is not None else None
    except ValueError: return None

def fetch_json(url, *, opener=urllib.request.urlopen, timeout=15):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with opener(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        if status < 200 or status >= 300: raise RuntimeError("unexpected HTTP status")
        return json.loads(response.read().decode("utf-8"))

def release_fingerprint(release):
    payload = {key: release.get(key) for key in ("tag_name","name","body","published_at","html_url","prerelease")}
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

def collect_releases(source, *, since, fetcher=fetch_json):
    repo = source["repo"]
    payload = fetcher(f"https://api.github.com/repos/{repo}/releases?per_page=20")
    if not isinstance(payload, list): raise ValueError("GitHub releases API did not return a list")
    candidates = []
    for release in payload:
        if not isinstance(release, dict) or release.get("draft") is True: continue
        published = parse_time(release.get("published_at") or release.get("created_at"))
        if published is None or published < since: continue
        tag, link = release.get("tag_name"), release.get("html_url")
        if not isinstance(tag, str) or not tag or not isinstance(link, str) or not link.startswith("https://github.com/"): continue
        body = release.get("body") if isinstance(release.get("body"), str) else ""
        candidates.append({
            "candidate_id":f"github-release:{repo}:{tag}","fingerprint":release_fingerprint(release),
            "candidate_type":"project_release","source_id":source["id"],"source_name":source["name"],
            "category":source["category"],"repo":repo,"title":release.get("name") or tag,"tag_name":tag,
            "published_at":published.isoformat().replace("+00:00","Z"),"updated_at":release.get("updated_at"),
            "url":link,"prerelease":bool(release.get("prerelease")),"body_excerpt":" ".join(body.split())[:700],
            "evidence_scope":"official_project_release_metadata","review_status":"requires_human_review"})
    return sorted(candidates,key=lambda x:(x["published_at"],x["candidate_id"]),reverse=True)

def candidate_from_hf(model):
    model_id=model["model_id"]
    payload={key:model.get(key) for key in ("model_id","repo_sha","last_modified","gated","private")}
    fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    return {"candidate_id":"hf-model:"+model_id,"fingerprint":fingerprint,"candidate_type":"model_repository",
            "source_id":"huggingface-model-catalog","source_name":"Hugging Face model repository","category":"model",
            "title":model_id,"model_id":model_id,"published_at":model.get("last_modified"),
            "url":"https://huggingface.co/"+model_id,"repo_sha":model.get("repo_sha"),
            "evidence_scope":"model_repository_metadata_only","review_status":"requires_human_review"}

def apply_change_detection(candidates,state,*,now):
    records=state.setdefault("items",{}); changes=[]
    for candidate in candidates:
        cid,fp=candidate["candidate_id"],candidate["fingerprint"]; previous=records.get(cid)
        if previous is None: status,first="new",now
        elif previous.get("fingerprint")!=fp: status,first="updated",previous.get("first_seen_at",now)
        else: status,first="unchanged",previous.get("first_seen_at",now)
        records[cid]={"fingerprint":fp,"first_seen_at":first,"last_seen_at":now}
        changes.append({**candidate,"change_status":status,"first_seen_at":first,"last_seen_at":now})
    cutoff=parse_time(now)-timedelta(days=180)
    for key,value in list(records.items()):
        seen=parse_time(value.get("last_seen_at"))
        if seen is None or seen<cutoff: del records[key]
    return changes

def run_discovery(registry,catalog,*,now=None,days=45,release_fetcher=fetch_json,model_report=None,state=None):
    now_dt=now or datetime.now(timezone.utc)
    if now_dt.utcoffset() is None: raise ValueError("now must be timezone-aware")
    now_text=now_dt.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
    since=now_dt.astimezone(timezone.utc)-timedelta(days=days)
    source_results,candidates,errors=[],[],[]
    for source in registry["sources"]:
        if not source.get("active"): continue
        if source["kind"]!="github_releases":
            errors.append({"source_id":source["id"],"error":"unsupported_source_kind"}); continue
        try:
            found=collect_releases(source,since=since,fetcher=release_fetcher); candidates.extend(found)
            source_results.append({"source_id":source["id"],"repo":source["repo"],"status":"observed","recent_release_count":len(found)})
        except (urllib.error.URLError,TimeoutError,ValueError,RuntimeError) as error:
            errors.append({"source_id":source["id"],"error":type(error).__name__})
            source_results.append({"source_id":source["id"],"repo":source["repo"],"status":"unavailable","recent_release_count":0})
    if model_report is not None:
        for item in model_report.get("models",[]):
            if item.get("status")=="observed": candidates.append(candidate_from_hf(item))
        for item in model_report.get("new_publisher_candidates",[]):
            candidates.append(candidate_from_hf({**item,"gated":None,"private":None}))
        errors.extend({"source_id":"huggingface-model-catalog","error":item.get("error","publisher_listing_unavailable")}
                      for item in model_report.get("publisher_discovery_errors",[]))
    state=state if state is not None else {"schema_version":"1.0","items":{}}
    changes=apply_change_detection(candidates,state,now=now_text)
    counts={key:sum(item["change_status"]==key for item in changes) for key in ("new","updated","unchanged")}
    actionable=[item for item in changes if item["change_status"] in {"new","updated"}]
    actionable.sort(key=lambda x:(x.get("published_at") or "",x["candidate_id"]),reverse=True)
    return {"schema_version":"1.0","generated_at":now_text,"lookback_days":days,"read_only":True,
            "source_count":len(source_results),"sources_observed":sum(x["status"]=="observed" for x in source_results),
            "sources_unavailable":len(errors),"candidate_count":len(candidates),"change_counts":counts,
            "review_queue":actionable,"all_observations":changes,"source_results":source_results,"errors":errors,
            "model_catalog_summary":{"known_models_checked":(model_report or {}).get("model_count",0),
            "known_model_repositories_observed":(model_report or {}).get("observed",0),
            "new_publisher_candidates":len((model_report or {}).get("new_publisher_candidates",[]))},
            "policy":"Discovery metadata is an investigation lead only. It does not update formal product, company, model or hardware-support registries and does not establish benchmark results or accelerator compatibility."}

def markdown_summary(report):
    lines=["# AI Chip Intelligence Discovery","",f"- Generated: {report['generated_at']}",
    f"- Lookback: {report['lookback_days']} days",f"- Sources observed: {report['sources_observed']}/{report['source_count']}",
    f"- Candidates: {report['candidate_count']} · new: {report['change_counts']['new']} · updated: {report['change_counts']['updated']} · unchanged: {report['change_counts']['unchanged']}",
    f"- Model repositories checked: {report['model_catalog_summary']['known_models_checked']} · observed: {report['model_catalog_summary']['known_model_repositories_observed']} · new publisher candidates: {report['model_catalog_summary']['new_publisher_candidates']}","","## Review queue",""]
    if not report["review_queue"]: lines.append("No new or changed candidates in this run.")
    for item in report["review_queue"][:100]:
        lines.extend([f"### [{item['change_status'].upper()}] {item['title']}",
        f"- Category: {item['category']} · Type: {item['candidate_type']}",f"- Source: {item['source_name']}",
        f"- Published/modified: {item.get('published_at') or 'not provided'}",f"- URL: {item['url']}",
        f"- Candidate ID: `{item['candidate_id']}`",""])
    if report["errors"]:
        lines.extend(["## Source errors",""]+[f"- {x['source_id']}: {x['error']}" for x in report["errors"]])
    lines.extend(["","> Discovery leads require human review. No production registry is changed automatically."])
    return "\n".join(lines)+"\n"

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry",type=Path,default=ROOT/"data/intelligence-sources.json")
    parser.add_argument("--catalog",type=Path,default=ROOT/"data/model-catalog.json")
    parser.add_argument("--state-file",type=Path,default=ROOT/".cache/ai-chip-intelligence-state.json")
    parser.add_argument("--output",type=Path,required=True); parser.add_argument("--summary-path",type=Path)
    parser.add_argument("--days",type=int,default=45); args=parser.parse_args()
    if args.days<1 or args.days>180: parser.error("--days must be between 1 and 180")
    try:
        registry=json.loads(args.registry.read_text(encoding="utf-8")); catalog=json.loads(args.catalog.read_text(encoding="utf-8"))
        from validate_intelligence_sources import validate_registry
        errors=validate_registry(registry)
        if errors: raise ValueError("; ".join(errors))
        state={"schema_version":"1.0","items":{}}
        if args.state_file.exists():
            state=json.loads(args.state_file.read_text(encoding="utf-8"))
            if state.get("schema_version")!="1.0" or not isinstance(state.get("items"),dict): raise ValueError("invalid discovery state file")
        from discover_model_catalog import discover,discover_publisher_candidates
        model_report=discover(catalog,publisher_search=discover_publisher_candidates)
        report=run_discovery(registry,catalog,days=args.days,model_report=model_report,state=state)
        args.state_file.parent.mkdir(parents=True,exist_ok=True); args.output.parent.mkdir(parents=True,exist_ok=True)
        args.state_file.write_text(json.dumps(state,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        summary=markdown_summary(report)
        if args.summary_path:
            args.summary_path.parent.mkdir(parents=True,exist_ok=True); args.summary_path.write_text(summary,encoding="utf-8")
        print(f"PASS: {report['candidate_count']} observations; {len(report['review_queue'])} new/updated review leads; {len(report['errors'])} source errors.")
    except (OSError,ValueError,KeyError) as error:
        print("FAIL: "+str(error),file=sys.stderr); return 1
    return 0
if __name__=="__main__": raise SystemExit(main())
