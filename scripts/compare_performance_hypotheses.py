#!/usr/bin/env python3
"""Compare competing performance hypotheses without assigning causal verdicts."""
import argparse
import json
from pathlib import Path

from review_performance_experiment_evidence import require, digest

ALLOWED = {"observed", "not_observed_in_window", "insufficient_evidence", "not_attributed"}


def compare(diagnosis, hypotheses, retrieval=None):
    require(isinstance(diagnosis, dict) and diagnosis.get("schema_version") == "1.0",
            "Invalid diagnosis report")
    require(diagnosis.get("overall_verdict") == "undetermined",
            "Comparison requires an undetermined diagnosis report")
    attribution = diagnosis.get("attribution", {})
    require(isinstance(attribution, dict) and isinstance(attribution.get("candidates"), list),
            "Diagnosis attribution candidates are required")
    require(isinstance(hypotheses, dict) and hypotheses.get("schema_version") == "1.0"
            and isinstance(hypotheses.get("hypotheses"), list), "Invalid hypothesis catalog")
    observed = attribution["candidates"]
    by_mechanism = {}
    for item in observed:
        require(isinstance(item, dict) and item.get("status") in ALLOWED,
                "Invalid attribution candidate")
        by_mechanism.setdefault(item.get("mechanism"), []).append(item)

    retrieved = []
    if retrieval is not None:
        require(isinstance(retrieval, dict)
                and retrieval.get("report_type") == "performance_knowledge_retrieval"
                and isinstance(retrieval.get("results"), list),
                "Invalid knowledge retrieval report")
        retrieved = retrieval["results"]

    results = []
    seen = set()
    for hypothesis in hypotheses["hypotheses"]:
        require(isinstance(hypothesis, dict), "Hypothesis must be an object")
        hid = hypothesis.get("hypothesis_id")
        require(isinstance(hid, str) and hid and hid not in seen, "Hypothesis IDs must be unique")
        seen.add(hid)
        rules = hypothesis.get("evidence_rules", [])
        require(isinstance(rules, list) and rules, "Each hypothesis requires evidence rules")
        matches = []
        missing = []
        for rule in rules:
            mechanism = rule.get("mechanism")
            require(isinstance(mechanism, str) and mechanism, "Evidence rule mechanism required")
            entries = by_mechanism.get(mechanism, [])
            if not entries:
                missing.append({"mechanism": mechanism, "state": "not_supplied"})
                continue
            for entry in entries:
                matches.append({
                    "mechanism": mechanism,
                    "diagnostic_state": entry["status"],
                    "observation": entry.get("observation"),
                    "evidence": entry.get("evidence", []),
                    "not_proven": entry.get("not_proven"),
                    "rule_interpretation": rule.get("interpretation", ""),
                })
        states = {item["diagnostic_state"] for item in matches}
        if "observed" in states:
            evidence_state = "supporting_signal_observed"
        elif "not_observed_in_window" in states:
            evidence_state = "not_observed_in_sampled_window"
        elif matches:
            evidence_state = "insufficient_or_unattributed"
        else:
            evidence_state = "no_direct_diagnostic_evidence"
        knowledge = []
        terms = set(hypothesis.get("knowledge_query", "").casefold().split())
        for item in retrieved:
            text = " ".join(str(item.get(k, "")) for k in
                            ("topic", "reviewer_interpretation", "applicability", "limitations")).casefold()
            overlap = sorted(term for term in terms if len(term) > 2 and term in text)
            if overlap:
                knowledge.append({
                    "knowledge_id": item.get("knowledge_id"),
                    "verdict": item.get("verdict"),
                    "retrieval_tier": item.get("retrieval_tier"),
                    "matched_query_terms": overlap,
                    "applicability_status": item.get("applicability_status"),
                    "metric_compatibility": item.get("metric_compatibility"),
                    "evidence_refs": item.get("evidence_refs", []),
                })
        results.append({
            "hypothesis_id": hid,
            "title": hypothesis.get("title"),
            "mechanism": hypothesis.get("mechanism"),
            "statement": hypothesis.get("statement"),
            "evidence_state": evidence_state,
            "observations": matches,
            "missing_diagnostic_channels": missing,
            "discriminating_measurements": hypothesis.get("discriminating_measurements", []),
            "what_would_support": hypothesis.get("what_would_support", []),
            "what_would_weaken": hypothesis.get("what_would_weaken", []),
            "historical_knowledge": knowledge,
            "interpretation": (
                "A signal associated with this mechanism was observed; contribution to the end-to-end symptom is not established."
                if evidence_state == "supporting_signal_observed" else
                "No matched observation in the supplied diagnostic window; this does not exclude unmeasured or out-of-window effects."
                if evidence_state == "not_observed_in_sampled_window" else
                "Evidence is absent, incomplete or not attributed; do not treat missing data as a negative result."
            ),
        })
    return {
        "schema_version": "1.0",
        "report_type": "performance_hypothesis_comparison",
        "record_id": diagnosis.get("record_id"),
        "diagnosis_sha256": digest(diagnosis),
        "retrieval_report_sha256": digest(retrieval) if retrieval is not None else None,
        "hypothesis_catalog_sha256": digest(hypotheses),
        "hypothesis_count": len(results),
        "hypotheses": results,
        "overall_verdict": "undetermined",
        "ranking": "none",
        "policy": {
            "observed_signal_is_not_causal_attribution": True,
            "missing_evidence_is_not_negative_evidence": True,
            "historical_knowledge_is_context_bounded": True,
            "no_automatic_hypothesis_selection": True,
            "no_automatic_experiment_execution": True,
        },
        "next_step": "Select a discriminating measurement or controlled experiment through human review; preserve competing explanations until evidence separates them.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnosis", type=Path, required=True)
    parser.add_argument("--hypotheses", type=Path, required=True)
    parser.add_argument("--retrieval", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = [args.diagnosis, args.hypotheses] + ([args.retrieval] if args.retrieval else [])
    require(args.output.resolve() not in {path.resolve() for path in inputs},
            "Output must not overwrite an input")
    diagnosis, hypotheses = [json.loads(path.read_text(encoding="utf-8"))
                             for path in (args.diagnosis, args.hypotheses)]
    retrieval = json.loads(args.retrieval.read_text(encoding="utf-8")) if args.retrieval else None
    report = compare(diagnosis, hypotheses, retrieval)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
