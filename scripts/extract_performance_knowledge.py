#!/usr/bin/env python3
"""Extract bounded, human-reviewed performance knowledge from an exact evidence chain."""
import argparse
import json
from copy import deepcopy
from pathlib import Path

from review_performance_experiment_evidence import build_review, digest, require, nonempty
from append_performance_review_decision import validate_ledger, identity, CHECKS

VERDICTS = {"supported", "refuted"}


def latest_decision(ledger, ident, review_hash):
    validate_ledger(ledger)
    key = digest(ident)
    matches = [entry for entry in ledger["entries"]
               if digest(entry.get("evidence_identity")) == key]
    if not matches:
        raise ValueError("No human decision exists for this exact evidence version")
    entry = matches[-1]
    decision = entry["decision"]
    require(entry.get("review_sha256") == review_hash, "Decision references a different review packet")
    require(decision.get("verdict") in VERDICTS, "Only Supported or Refuted decisions can become reusable knowledge")
    require(isinstance(decision.get("checks"), dict)
            and set(decision["checks"]) == CHECKS
            and all(value is True for value in decision["checks"].values()),
            "All six human review attestations must be true")
    require(nonempty(decision.get("rationale")), "Decision rationale required")
    require(nonempty(decision.get("applicability")), "Applicability boundary required")
    require(nonempty(decision.get("limitations")), "Limitations required")
    return decision


def extract_knowledge(record, plan, submission, ledger):
    report = build_review(record, plan, submission)
    ident = identity(report)
    decision = latest_decision(ledger, ident, digest(report))
    require(report["review_status"] == "needs_review", "Blocked evidence cannot become reusable knowledge")
    runs_by_id = {run["run_id"]: run for run in report["runs"]}
    run_ids = decision.get("evidence_run_ids")
    require(isinstance(run_ids, list) and run_ids and len(set(run_ids)) == len(run_ids),
            "Knowledge decision must cite unique run IDs")
    require(set(run_ids) <= set(runs_by_id), "Knowledge decision cites unknown runs")
    cited = [runs_by_id[run_id] for run_id in run_ids]
    require(all(run.get("status") == "valid" for run in cited),
            "Knowledge cannot cite failed or invalid runs")
    conditions = {run.get("condition") for run in cited}
    require(conditions == {"baseline", "treatment"},
            "Knowledge must cite valid baseline and treatment runs")
    exp = next(item for item in plan["experiments"]
               if item["experiment_id"] == submission["experiment_id"])
    protocol = report["protocol"]
    metric = protocol["primary_metric"]
    scope = {
        "fixed_context": deepcopy(protocol["fixed_context"]),
        "intervention": {
            "parameter": protocol["parameter"],
            "baseline_value": protocol["baseline_value"],
            "treatment_value": protocol["treatment_value"],
        },
        "metric": deepcopy(metric),
    }
    scope_hash = digest(scope)
    content = {
        "schema_version": "1.0",
        "record_id": record["id"],
        "plan_id": plan["plan_id"],
        "experiment_id": exp["experiment_id"],
        "evidence_identity": ident,
        "review_sha256": digest(report),
        "decision_id": decision["decision_id"],
        "verdict": decision["verdict"],
        "knowledge_status": "human_reviewed_claim",
        "topic": exp.get("mechanism", "unspecified"),
        "hypothesis": exp.get("hypothesis", ""),
        "reviewer_interpretation": decision["rationale"],
        "applicability": decision["applicability"],
        "limitations": decision["limitations"],
        "scope": scope,
        "observations": {
            "baseline": report["statistics"]["baseline"],
            "treatment": report["statistics"]["treatment"],
            "relative_improvement_percent": report["relative_improvement_percent"],
            "practical_effect_threshold_percent": protocol["practical_effect_percent"],
            "effect_threshold_met": report["effect_threshold_met"],
        },
        "evidence": [{
            "run_id": run["run_id"],
            "condition": run["condition"],
            "source_url": run["source_url"],
            "value": run["value"],
            "unit": run["unit"],
        } for run in cited],
        "reviewer": decision["reviewer"],
        "reviewed_at": decision["reviewed_at"],
        "scope_sha256": scope_hash,
    }
    content["knowledge_id"] = "pk-" + digest(content)[:20]
    return content


def build_catalog(item, existing=None):
    existing = existing or {"schema_version": "1.0", "entries": []}
    require(isinstance(existing, dict) and existing.get("schema_version") == "1.0"
            and isinstance(existing.get("entries"), list), "Invalid existing knowledge catalog")
    entries = deepcopy(existing["entries"])
    conflicts = deepcopy(existing.get("potential_contradictions", []))
    require(isinstance(conflicts, list), "Existing contradiction list must be an array")
    require(all(isinstance(x, dict) and x.get("knowledge_id") for x in entries),
            "Existing catalog contains invalid knowledge entries")
    if any(x["knowledge_id"] == item["knowledge_id"] for x in entries):
        raise ValueError("Knowledge entry already exists")
    known_pairs = {(x.get("knowledge_id_a"), x.get("knowledge_id_b")) for x in conflicts}
    for prior in entries:
        if (prior.get("topic") == item["topic"]
                and prior.get("scope_sha256") == item["scope_sha256"]
                and prior.get("verdict") in VERDICTS
                and prior.get("verdict") != item["verdict"]):
            pair = (prior["knowledge_id"], item["knowledge_id"])
            if pair not in known_pairs:
                conflicts.append({
                "knowledge_id_a": prior["knowledge_id"],
                "knowledge_id_b": item["knowledge_id"],
                "type": "opposing_human_verdict_same_declared_scope",
                "resolution": "unresolved_human_review_required",
                })
                known_pairs.add(pair)
    entries.append(item)
    return {"schema_version": "1.0", "entries": entries,
            "potential_contradictions": conflicts,
            "policy": {
                "automatic_truth_claims": False,
                "only_human_reviewed_supported_or_refuted": True,
                "contradictions_auto_resolved": False,
            }}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("record", "plan", "submission", "review", "ledger", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--existing", type=Path)
    args = parser.parse_args()
    inputs = [args.record, args.plan, args.submission, args.review, args.ledger]
    if args.existing:
        inputs.append(args.existing)
    require(args.output.resolve() not in {p.resolve() for p in inputs},
            "Output must not overwrite an input")
    record, plan, submission, supplied_review, ledger = [
        json.loads(path.read_text(encoding="utf-8")) for path in inputs[:5]]
    report = build_review(record, plan, submission)
    require(supplied_review == report, "Supplied review packet does not match regenerated report")
    item = extract_knowledge(record, plan, submission, ledger)
    existing = json.loads(args.existing.read_text(encoding="utf-8")) if args.existing else None
    catalog = build_catalog(item, existing)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False,
                                      allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
