#!/usr/bin/env python3
"""Validate benchmark suite catalog and result record references."""
import json,re,sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
errors=[]
def valid_date(v):
 try: date.fromisoformat(v); return True
 except (TypeError,ValueError): return False
def valid_url(v):
 try:
  u=urlparse(v); return u.scheme in {"http","https"} and bool(u.netloc)
 except (TypeError,ValueError): return False
def load(name):
 try: return json.loads((ROOT/"data"/name).read_text(encoding="utf-8"))
 except Exception as e: errors.append(f"{name}: {e}"); return {}
def main():
 c=load("benchmark-suites.json"); d=load("benchmark-results.json"); w=load("workloads.json"); h=load("compatibility.json")
 suites=c.get("suites",[]); ids=set()
 for i,s in enumerate(suites):
  sid=s.get("id")
  if not isinstance(sid,str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",sid): errors.append(f"suites[{i}]: invalid id")
  if sid in ids: errors.append(f"suites[{i}]: duplicate id {sid}")
  ids.add(sid)
  if not valid_url(s.get("url")) or not valid_url(s.get("repository")): errors.append(f"suites[{i}]: invalid URL")
 wids={x.get("id") for x in w.get("workloads",[])}; pids={x.get("id") for x in h.get("platforms",[])}
 rids=set()
 for i,r in enumerate(d.get("results",[])):
  rid=r.get("id")
  if rid in rids: errors.append(f"results[{i}]: duplicate id {rid}")
  rids.add(rid)
  for key,allowed in [("suite_id",ids),("workload_id",wids),("platform_id",pids)]:
   if r.get(key) not in allowed: errors.append(f"results[{i}]: unknown {key}")
  for section,keys in [("hardware_configuration",["accelerator","device_count"]),("software_stack",["os","driver","framework"]),("model_configuration",["model","revision","precision"]),("measurement",["metrics","warmup_iterations","measurement_iterations","method"]),("source",["url","source_type"]),("reproduction",["status","recipe_url"])]:
   obj=r.get(section,{})
   for key in keys:
    if key not in obj or obj[key] is None or obj[key]=="": errors.append(f"results[{i}]: missing {section}.{key}")
  if not valid_url(r.get("source",{}).get("url")): errors.append(f"results[{i}]: invalid source URL")
  if not valid_url(r.get("reproduction",{}).get("recipe_url")): errors.append(f"results[{i}]: invalid recipe URL")
  if not valid_date(r.get("measured_at")): errors.append(f"results[{i}]: invalid measured_at")
 if errors:
  print("FAIL:",len(errors)); print("\n".join("- "+e for e in errors)); return 1
 print(f"PASS: {len(suites)} benchmark suites, {len(d.get('results',[]))} result records; references and required metadata valid.")
 return 0
if __name__=="__main__": raise SystemExit(main())
