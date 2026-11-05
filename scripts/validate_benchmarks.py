#!/usr/bin/env python3
"""Validate the public benchmark information catalogue (not experiment results)."""
import json,re,sys
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
errors=[]
def valid_url(value):
 if value is None: return True
 try:
  u=urlparse(value); return u.scheme in {"http","https"} and bool(u.netloc)
 except (TypeError,ValueError): return False
def main():
 try: db=json.loads((ROOT/"data/benchmark-projects.json").read_text(encoding="utf-8"))
 except Exception as e:
  print(f"FAIL: cannot parse benchmark catalogue: {e}",file=sys.stderr); return 2
 categories={x.get("id") for x in db.get("categories",[])}
 ids=set(); projects=db.get("projects",[])
 if not projects: errors.append("projects must be non-empty")
 for i,p in enumerate(projects):
  pid=p.get("id")
  if not isinstance(pid,str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",pid): errors.append(f"projects[{i}]: invalid id")
  if pid in ids: errors.append(f"projects[{i}]: duplicate id {pid}")
  ids.add(pid)
  for field in ("name","category","kind","maintainer","description","official_url","metrics","comparability"):
   if not p.get(field): errors.append(f"projects[{i}]: missing {field}")
  if p.get("category") not in categories: errors.append(f"projects[{i}]: unknown category")
  for field in ("official_url","repository_url","results_url"):
   if not valid_url(p.get(field)): errors.append(f"projects[{i}]: invalid {field}")
  if not isinstance(p.get("metrics"),list) or not p.get("metrics"): errors.append(f"projects[{i}]: metrics must be a non-empty list")
 if errors:
  print(f"FAIL: {len(errors)} issue(s)"); print("\n".join("- "+e for e in errors)); return 1
 print(f"PASS: {len(projects)} public benchmark entries across {len(categories)} categories.")
 return 0
if __name__=="__main__": raise SystemExit(main())
