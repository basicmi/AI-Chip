#!/usr/bin/env python3
"""Conservative, deterministic claim-candidate extraction; no truth verification or registry writes."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

METHOD = "deterministic_rules_v1"
TOPICS = {
 "interconnect": ("nvlink", "infiniband", "ethernet", "ualink", "interconnect", "fabric"),
 "memory_bandwidth": ("memory bandwidth", "hbm bandwidth", "bandwidth", "tb/s", "gb/s"),
 "memory_capacity": ("memory", "hbm", "dram", "sram", "kv cache"),
 "power": ("power", "watt", "energy", "tdp"),
 "compute": ("flops", "tops", "tensor core", "fp8", "fp4", "bf16", "compute"),
 "process_node": ("process node", "nm process", "nanometer"),
 "packaging": ("chiplet", "2.5d", "3d stack", "co-packaged", "packaging"),
 "software_support": ("supports", "support for", "compatibility", "backend", "kernel", "compiler", "runtime"),
 "availability": ("shipping", "available now", "sampling", "production", "launches", "announced"),
 "performance": ("tokens/s", "tokens per second", "ttft", "tpot", "throughput", "latency", "speedup", "performance"),
 "architecture": ("architecture", "expert parallel", "mixture of experts", "transformer"),
}
SIGNALS = tuple(term for terms in TOPICS.values() for term in terms) + ("gpu", "accelerator", "tpu", "npu", "asic", "robotics", "agent", "inference", "training", "serving", "prefill", "decode", "benchmark")
UNITS = r"tokens?\s*/\s*s|tokens?\s+per\s+second|TB\s*/\s*s|GB\s*/\s*s|MB\s*/\s*s|PFLOPS?|TFLOPS?|GFLOPS?|TOPS|TB|GB|MB|PB|kW|MW|W|nm|ms|us|µs|μs|GPUs?|accelerators?|chips?|nodes?|[MB]\s+parameters?|%"
METRIC_RE = re.compile(r"(?<![\w.])(?P<value>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?P<unit>" + UNITS + r")(?![\w])", re.I)
SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
SCOPES = [
 (re.compile(r"\bper\s+(?:GPU|accelerator|chip|die|package|board|server|rack|node|system)\b", re.I), "explicit_per_unit"),
 (re.compile(r"\b(?:rack|pod|cluster|system|server|board|module|package|chip|GPU)-level\b", re.I), "explicit_level"),
 (re.compile(r"\b(?:aggregate|total|combined)\b", re.I), "explicit_aggregate"),
]
QUALIFIERS = ("up to", "peak", "maximum", "dense", "sparse", "theoretical", "measured", "vendor-reported")

def clean(value):
 value=unescape(str(value or "")); value=re.sub(r"<[^>]+>"," ",value)
 value=re.sub(r"!\[[^\]]*\]\([^)]*\)"," ",value); value=re.sub(r"\[([^\]]+)\]\([^)]*\)",r"\1",value)
 value=re.sub(r"\x60+","",value)
 return " ".join(value.split())

def stable_id(*parts):
 raw="\x1f".join(str(x or "") for x in parts)
 return "claim-"+hashlib.sha256(raw.encode()).hexdigest()[:20]

def topic_for(sentence):
 text=sentence.lower()
 for topic,terms in TOPICS.items():
  if any(term in text for term in terms): return topic
 return "other"

def scope_for(sentence):
 for pattern,label in SCOPES:
  match=pattern.search(sentence)
  if match: return {"status":label,"text":match.group(0)}
 return {"status":"not_explicitly_stated","text":None}

def source_for(candidate):
 keys=("candidate_id","source_id","source_name","publisher","source_type","independence","url","published_at","evidence_scope")
 return {key:candidate.get(key,"unknown" if key in ("source_type","independence","evidence_scope") else None) for key in keys}

def extract_candidate_claims(candidate):
 title=clean(candidate.get("title")); excerpt=clean(candidate.get("excerpt") or candidate.get("body_excerpt"))
 combined=". ".join(x for x in (title,excerpt) if x)
 url=candidate.get("url")
 if not combined or not isinstance(url,str): return []
 parsed=urlparse(url)
 if parsed.scheme not in ("http","https") or not parsed.netloc: return []
 output=[]; seen=set()
 for sentence in (x.strip(" \t\r-•") for x in SPLIT_RE.split(combined)):
  if len(sentence)<18: continue
  lower=sentence.lower(); signals=[x for x in SIGNALS if x in lower]
  metrics=list(METRIC_RE.finditer(sentence))
  if not signals and not metrics: continue
  if metrics and any(x in lower for x in TOPICS["performance"]): claim_type="performance_result"
  elif any(x in lower for x in TOPICS["availability"]): claim_type="availability_or_lifecycle"
  elif candidate.get("candidate_type")=="research_preprint": claim_type="research_finding"
  elif any(x in lower for x in ("support","supports","compatible","backend","kernel","compiler","runtime")): claim_type="software_or_capability"
  else: claim_type="quantitative_specification" if metrics else "qualitative_capability"
  matches=metrics if metrics else [None]
  for match in matches:
   value=float(match.group("value").replace(",","")) if match else None
   if value is not None and value.is_integer(): value=int(value)
   unit=match.group("unit").strip() if match else None
   identity=(candidate.get("candidate_id"),sentence,value,unit)
   if identity in seen: continue
   seen.add(identity)
   output.append({
    "claim_id":stable_id(*identity),"candidate_id":candidate.get("candidate_id"),
    "claim_type":claim_type,"topic":topic_for(sentence),"statement":sentence[:1200],
    "value":value,"unit":unit,"scope":scope_for(sentence),
    "qualifiers":[x for x in QUALIFIERS if x in lower],
    "source":source_for(candidate),"evidence_quote":sentence[:1200],
    "extraction":{"method":METHOD,"confidence":"low","matched_signals":signals[:12],"requires_semantic_review":True},
    "review_status":"unverified_candidate",
    "review_gates":[
     "Verify that the quoted text actually asserts this claim.",
     "Resolve company, product, architecture and generation; do not infer identity from publisher alone.",
     "Confirm units, precision, sparsity, measurement scope and configuration before recording numeric values.",
     "Classify source as vendor-reported, research-reported or independently measured.",
     "Seek independent corroboration before treating performance, compatibility or availability as verified."
    ]
   })
 return output

def validate_claim(claim):
 errors=[]
 for key in ("claim_id","candidate_id","claim_type","topic","statement","scope","source","evidence_quote","extraction","review_status","review_gates"):
  if key not in claim: errors.append("missing "+key)
 if not isinstance(claim.get("statement"),str) or not claim["statement"].strip(): errors.append("statement must be nonempty")
 if claim.get("review_status")!="unverified_candidate": errors.append("claim must remain unverified")
 extraction=claim.get("extraction",{})
 if extraction.get("method")!=METHOD: errors.append("unsupported extraction method")
 if extraction.get("confidence") not in ("low","medium"): errors.append("invalid extraction confidence")
 if not isinstance(claim.get("review_gates"),list) or not claim["review_gates"]: errors.append("review_gates must be nonempty")
 source=claim.get("source",{}); url=source.get("url") if isinstance(source,dict) else None
 parsed=urlparse(url or "")
 if parsed.scheme not in ("http","https") or not parsed.netloc: errors.append("source URL must be HTTP(S)")
 value=claim.get("value")
 if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float))): errors.append("value must be numeric or null")
 if value is not None and not isinstance(claim.get("unit"),str): errors.append("numeric value requires unit")
 return errors

def extract_report(discovery,generated_at=None,max_claims=1000):
 now=generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
 candidates=discovery.get("review_queue",[]); claims=[]; errors=[]
 for candidate in candidates:
  for claim in extract_candidate_claims(candidate):
   problems=validate_claim(claim)
   if problems: errors.append({"candidate_id":candidate.get("candidate_id"),"errors":problems})
   else: claims.append(claim)
   if len(claims)>=max_claims: break
  if len(claims)>=max_claims: break
 return {"schema_version":"1.0","generated_at":now,"input_candidate_count":len(candidates),
  "claim_count":len(claims),"extraction_method":METHOD,"claims":claims,"errors":errors,
  "policy":"Extracted claims are unverified candidates. This deterministic first-stage extractor does not establish truth, infer product identity, verify compatibility, or modify production registries."}

def markdown_summary(report):
 lines=["# AI Chip Intelligence — Claim Extraction","",f"- Generated: {report['generated_at']}",
  f"- Input candidates: {report['input_candidate_count']}",f"- Extracted claim candidates: {report['claim_count']}",
  f"- Extraction method: {report['extraction_method']}","","## Claim candidates",""]
 if not report["claims"]: lines.append("No claim candidates met the extraction rules.")
 for i,claim in enumerate(report["claims"][:100],1):
  value=f" · {claim['value']} {claim['unit']}" if claim.get("value") is not None else ""
  lines.extend([f"### {i}. [{claim['topic']}] {claim['statement']}",
   f"- Type: {claim['claim_type']}{value}",
   f"- Source: {claim['source'].get('publisher') or claim['source'].get('source_name')} · {claim['source']['url']}",
   f"- Scope: {claim['scope']['status']} · {claim['scope'].get('text') or 'not stated'}",
   f"- Extraction: {claim['extraction']['method']} · confidence {claim['extraction']['confidence']} · human review required",""])
 lines.extend(["## Guardrails","","- These are candidate claims, not verified facts.",
  "- Pattern extraction can miss claims and produce false positives.",
  "- Product identity, units, measurement conditions, lifecycle and evidence independence require human review.",
  "- No production registry is modified and no compatibility or benchmark status is inferred."])
 if report["errors"]: lines.extend(["","## Rejected extraction records",""]+[f"- {x['candidate_id']}: {', '.join(x['errors'])}" for x in report["errors"]])
 return "\n".join(lines)+"\n"

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--input",type=Path,required=True); parser.add_argument("--output",type=Path,required=True)
 parser.add_argument("--summary-path",type=Path); parser.add_argument("--max-claims",type=int,default=1000)
 args=parser.parse_args()
 if not 1<=args.max_claims<=10000: parser.error("--max-claims must be between 1 and 10000")
 try:
  discovery=json.loads(args.input.read_text(encoding="utf-8"))
  report=extract_report(discovery,max_claims=args.max_claims)
  args.output.parent.mkdir(parents=True,exist_ok=True)
  args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
  if args.summary_path:
   args.summary_path.parent.mkdir(parents=True,exist_ok=True)
   args.summary_path.write_text(markdown_summary(report),encoding="utf-8")
  print(f"PASS: {report['input_candidate_count']} source candidates; {report['claim_count']} unverified claim candidates.")
 except (OSError,ValueError,TypeError) as error:
  print("FAIL: "+str(error),file=sys.stderr); return 1
 return 0

if __name__=="__main__": raise SystemExit(main())
