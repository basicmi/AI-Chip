#!/usr/bin/env python3
"""Append explicit human decisions to an evidence-version-bound review ledger."""
import argparse
from copy import deepcopy
import json
from datetime import datetime
from pathlib import Path
from review_performance_experiment_evidence import digest, require, nonempty, build_review

VERDICTS = {"supported", "refuted", "inconclusive", "revision_required"}
CHECKS = {"source_verified", "baseline_reproduced", "controls_verified",
          "measurement_alignment_verified", "mechanism_evidence_reviewed",
          "run_completeness_reviewed"}


def identity(report):
    return {k: report[k] for k in ("record_id", "plan_id", "experiment_id",
                                   "record_sha256", "plan_sha256", "submission_sha256")}


def validate_ledger(ledger):
    require(isinstance(ledger, dict) and ledger.get("schema_version") == "1.0", "Invalid ledger version")
    require(isinstance(ledger.get("entries"), list), "Entries must be a list")
    previous = None
    latest = {}
    ids = set()
    for entry in ledger["entries"]:
        require(isinstance(entry, dict), "Invalid entry")
        payload = {k:v for k,v in entry.items() if k != "entry_sha256"}
        require(entry.get("entry_sha256") == digest(payload), "Entry digest mismatch")
        require(entry.get("previous_entry_sha256") == previous, "Broken ledger chain")
        decision = entry.get("decision", {})
        require(nonempty(decision.get("decision_id")) and decision["decision_id"] not in ids, "Duplicate or missing decision ID")
        ids.add(decision["decision_id"])
        key = digest(entry["evidence_identity"])
        require(decision.get("supersedes") == latest.get(key), "Invalid supersession")
        latest[key] = decision["decision_id"]
        previous = entry["entry_sha256"]
    return latest, previous


def append_decision(ledger, record, plan, submission, decision):
    latest, previous = validate_ledger(ledger)
    report = build_review(record, plan, submission)
    ident = identity(report)
    require(isinstance(decision, dict), "Decision must be an object")
    require(decision.get("review_sha256") == digest(report), "Review digest mismatch")
    require(nonempty(decision.get("decision_id")), "Decision ID required")
    require(nonempty(decision.get("reviewer")), "Reviewer required")
    require(nonempty(decision.get("reviewed_at")), "Review time required")
    try:
        timestamp = datetime.fromisoformat(decision["reviewed_at"].replace("Z", "+00:00"))
        require(timestamp.utcoffset() is not None, "Review time requires timezone")
    except ValueError:
        raise ValueError("Review time must be ISO 8601 with timezone")
    require(decision.get("verdict") in VERDICTS, "Unknown verdict")
    require(nonempty(decision.get("rationale")), "Rationale required")
    require(nonempty(decision.get("applicability")), "Applicability required")
    require(nonempty(decision.get("limitations")), "Limitations required")
    require(decision.get("supersedes") == latest.get(digest(ident)), "Must supersede latest decision for exact evidence version")
    if decision.get("supersedes") is not None:
        require(nonempty(decision.get("revision_reason")), "Revision reason required")
    checks = decision.get("checks")
    require(isinstance(checks, dict) and set(checks) == CHECKS and all(type(v) is bool for v in checks.values()), "Explicit review checks required")
    refs = decision.get("evidence_run_ids")
    require(isinstance(refs, list) and all(nonempty(x) for x in refs) and len(set(refs)) == len(refs), "Unique evidence run IDs required")
    known = {r["run_id"]:r for r in report["runs"]}
    require(set(refs) <= set(known), "Unknown evidence run ID")
    if decision["verdict"] in {"supported", "refuted"}:
        require(report["review_status"] == "needs_review", "Blocked report cannot support a definitive decision")
        require(all(checks.values()), "Definitive decision requires all human checks")
        require({known[x]["condition"] for x in refs if known[x]["status"] == "valid"} == {"baseline","treatment"}, "Both conditions require valid cited runs")
    entry = {"evidence_identity":ident, "review_sha256":digest(report),
             "decision":deepcopy(decision), "previous_entry_sha256":previous}
    entry["entry_sha256"] = digest(entry)
    result = {"schema_version":"1.0","entries":[*deepcopy(ledger["entries"]),entry]}
    validate_ledger(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("ledger","record","plan","submission","decision","output"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    paths = [args.ledger,args.record,args.plan,args.submission,args.decision]
    require(args.output.resolve() not in {p.resolve() for p in paths}, "Output must not overwrite inputs")
    result = append_decision(*[json.loads(p.read_text(encoding="utf-8")) for p in paths])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+chr(10),encoding="utf-8")


if __name__ == "__main__":
    main()
