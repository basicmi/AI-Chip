#!/usr/bin/env python3
"""Review externally supplied experiment observations; never execute experiments."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from urllib.parse import urlsplit


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def valid_number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def source_ref(value):
    if not nonempty(value):
        return False
    u = urlsplit(value)
    return u.scheme in ("https", "http") and bool(u.hostname)


def build_review(record, plan, submission):
    require(all(isinstance(x, dict) for x in (record, plan, submission)), "Inputs must be objects")
    require(nonempty(record.get("id")), "Record ID required")
    require(plan.get("schema_version") == "1.0", "Unsupported plan version")
    require(submission.get("schema_version") == "1.0", "Unsupported submission version")
    require(plan.get("record_context", {}).get("record_id") == record["id"], "Record ID mismatch")
    require(plan.get("diagnosis_verdict") == "undetermined" and plan.get("automatic_experiment_execution") is False, "Expected non-executing undetermined plan")
    require(submission.get("plan_sha256") == digest(plan), "Plan digest mismatch")
    require(submission.get("record_sha256") == digest(record), "Record digest mismatch")
    require(submission.get("plan_id") == plan.get("plan_id"), "Plan ID mismatch")
    matches = [x for x in plan.get("experiments", []) if x.get("experiment_id") == submission.get("experiment_id")]
    require(len(matches) == 1, "Unknown or ambiguous experiment ID")
    exp = matches[0]
    require(exp.get("baseline", {}).get("source_record_id") == record["id"], "Experiment baseline mismatch")
    require(exp.get("execution", {}).get("performed") is False, "Expected unexecuted proposal")
    protocol = submission.get("protocol")
    require(isinstance(protocol, dict), "Protocol required")
    parameter = protocol.get("parameter")
    require(nonempty(parameter), "Intervention parameter required")
    require("baseline_value" in protocol and "treatment_value" in protocol and protocol["baseline_value"] != protocol["treatment_value"], "Distinct intervention values required")
    metric = protocol.get("primary_metric")
    require(isinstance(metric, dict) and all(nonempty(metric.get(k)) for k in ("key", "unit")), "Primary metric definition required")
    require(metric.get("direction") in ("higher", "lower"), "Metric direction required")
    effect = protocol.get("practical_effect_percent")
    require(valid_number(effect) and effect > 0, "Positive practical effect threshold required")
    require(source_ref(protocol.get("protocol_source_url")), "External protocol source URL required")
    controls = protocol.get("fixed_context")
    require(isinstance(controls, dict) and bool(controls), "Fixed context required")
    require(parameter not in controls, "Intervention must not be in fixed context")
    runs = submission.get("runs")
    require(isinstance(runs, list) and bool(runs), "Run observations required")
    seen = set()
    values = {"baseline": [], "treatment": []}
    reasons = []
    for run in runs:
        require(isinstance(run, dict), "Run must be object")
        rid = run.get("run_id")
        require(nonempty(rid) and rid not in seen, "Run IDs must be unique")
        seen.add(rid)
        condition = run.get("condition")
        require(condition in values, "Unknown run condition")
        require(source_ref(run.get("source_url")), "Run source URL required")
        require(run.get("status") in ("valid", "failed", "invalid"), "Unknown run status")
        if run["status"] != "valid":
            require(nonempty(run.get("reason")), "Failed or invalid run requires reason")
            reasons.append("failed_or_invalid_run:" + rid)
            continue
        require(run.get("fixed_context") == controls, "Run fixed context mismatch")
        require("parameter_value" in run and run["parameter_value"] == protocol[condition + "_value"], "Run intervention mismatch")
        require(run.get("metric_key") == metric["key"] and run.get("unit") == metric["unit"], "Run metric definition mismatch")
        require(valid_number(run.get("value")), "Run metric value invalid")
        values[condition].append(run["value"])
    minimum = exp.get("repetitions_per_condition")
    require(type(minimum) is int and minimum >= 2, "Invalid repetition requirement")
    stats = {k: {"valid_runs": len(v), "min": min(v) if v else None, "max": max(v) if v else None, "median": median(v) if v else None} for k,v in values.items()}
    if any(len(v) < minimum for v in values.values()):
        reasons.append("insufficient_valid_repetitions")
    baseline, treatment = stats["baseline"]["median"], stats["treatment"]["median"]
    change = None
    if baseline is not None and treatment is not None and baseline > 0:
        change = (treatment - baseline) / baseline * 100 * (1 if metric["direction"] == "higher" else -1)
        require(math.isfinite(change), "Nonfinite relative change")
    else:
        reasons.append("relative_change_unavailable")
    # A reported effect is not an attribution verdict, even if the threshold is met.
    return {
        "schema_version": "1.0",
        "report_type": "performance_evidence_review",
        "record_id": record["id"],
        "plan_id": plan["plan_id"],
        "experiment_id": exp["experiment_id"],
        "hypothesis": exp["hypothesis"],
        "record_sha256": digest(record),
        "plan_sha256": digest(plan),
        "submission_sha256": digest(submission),
        "protocol": protocol,
        "runs": runs,
        "statistics": stats,
        "relative_improvement_percent": change,
        "effect_threshold_met": change >= effect if change is not None and not reasons else None,
        "review_blockers": reasons,
        "review_status": "needs_review" if not reasons else "blocked",
        "hypothesis_verdict": "undetermined",
        "automatic_execution": False,
        "limitations": [
            "External source URLs and protocol declarations are supplied by the submitter and are not independently verified.",
            "Exact declared context equality is not proof of physical experimental control.",
            "Median differences and practical thresholds are descriptive, not statistical significance or causal attribution.",
            "Failed and invalid runs remain visible; no automatic hypothesis approval is issued.",
            "Review mechanism-specific measurements, baseline reproduction, timing and measurement boundaries before drawing conclusions."
        ]
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("record", "plan", "submission", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    require(args.output.resolve() not in {args.record.resolve(), args.plan.resolve(), args.submission.resolve()}, "Output must not overwrite inputs")
    report = build_review(*[json.loads(path.read_text(encoding="utf-8")) for path in (args.record, args.plan, args.submission)])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
