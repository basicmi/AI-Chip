#!/usr/bin/env python3
"""Offline, human-labelled relevance and Claim extraction evaluation."""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from extract_intelligence_claims import METHOD, extract_candidate_claims, relevance_for

LABELS = ("direct_ai_compute", "adjacent_ai_systems", "out_of_scope")


def normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip().casefold()
    return re.sub(r"[\s\.,;:!?]+$", "", text)


def build_candidate(example: dict) -> dict:
    return {
        "candidate_id": example["candidate_id"],
        "candidate_type": "research_preprint",
        "source_id": "arxiv-ai-systems",
        "source_name": "arXiv AI Systems",
        "publisher": "arXiv",
        "source_type": "research_paper",
        "independence": "unknown",
        "url": example["url"],
        "published_at": "2026-11-16T00:00:00Z",
        "evidence_scope": "arxiv_preprint_title_and_abstract",
        "title": example["title"],
        "excerpt": example["excerpt"],
    }


def score_classification(examples: list[dict]) -> dict:
    confusion = {expected: {predicted: 0 for predicted in LABELS} for expected in LABELS}
    false_positives, false_negatives, class_mismatches = [], [], []
    correct = 0
    for example in examples:
        text = " ".join((example["title"], example.get("excerpt", "")))
        predicted, signals = relevance_for(text)
        predicted = predicted or "out_of_scope"
        expected = example["expected_relevance"]
        confusion[expected][predicted] += 1
        correct += predicted == expected
        item = {
            "candidate_id": example["candidate_id"],
            "title": example["title"],
            "expected": expected,
            "predicted": predicted,
            "signals": signals[:8],
            "rationale": example.get("rationale", ""),
        }
        if expected == "out_of_scope" and predicted != "out_of_scope":
            false_positives.append(item)
        elif expected != "out_of_scope" and predicted == "out_of_scope":
            false_negatives.append(item)
        elif expected != predicted:
            class_mismatches.append(item)

    class_metrics = {}
    f1_values = []
    total = len(examples)
    for label in LABELS:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in LABELS if other != label)
        fn = sum(confusion[label][other] for other in LABELS if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        class_metrics[label] = {
            "support": sum(confusion[label].values()),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
        f1_values.append(f1)

    expected_relevant = sum(x["expected_relevance"] != "out_of_scope" for x in examples)
    predicted_relevant = sum(
        confusion[expected][predicted]
        for expected in LABELS for predicted in LABELS if predicted != "out_of_scope"
    )
    true_relevant = sum(
        confusion[expected][predicted]
        for expected in LABELS if expected != "out_of_scope"
        for predicted in LABELS if predicted != "out_of_scope"
    )
    binary_precision = true_relevant / predicted_relevant if predicted_relevant else 0.0
    binary_recall = true_relevant / expected_relevant if expected_relevant else 0.0
    binary_f1 = (
        2 * binary_precision * binary_recall / (binary_precision + binary_recall)
        if binary_precision + binary_recall else 0.0
    )
    return {
        "sample_count": total,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "macro_f1": round(sum(f1_values) / len(f1_values), 4) if f1_values else 0.0,
        "relevant_vs_out_of_scope": {
            "precision": round(binary_precision, 4),
            "recall": round(binary_recall, 4),
            "f1": round(binary_f1, 4),
            "expected_relevant": expected_relevant,
            "predicted_relevant": predicted_relevant,
            "true_positive": true_relevant,
        },
        "per_class": class_metrics,
        "confusion_matrix": confusion,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "class_mismatches": class_mismatches,
    }


def score_claim_extraction(examples: list[dict]) -> dict:
    tp = fp = fn = duplicate_rows = quote_failures = 0
    evaluated = []
    for example in examples:
        if "expected_claim_fragments" not in example:
            continue
        candidate = build_candidate(example)
        claims = extract_candidate_claims(candidate)
        statements = [normalize(x.get("statement")) for x in claims if normalize(x.get("statement"))]
        unique_statements = list(dict.fromkeys(statements))
        duplicate_rows += max(0, len(statements) - len(unique_statements))
        expected = [normalize(x) for x in example.get("expected_claim_fragments", [])]
        matched_expected = set()
        unmatched_predictions = []
        matched_predictions = 0
        for statement in unique_statements:
            match_index = next(
                (i for i, fragment in enumerate(expected)
                 if i not in matched_expected and fragment and fragment in statement),
                None,
            )
            if match_index is None:
                unmatched_predictions.append(statement)
            else:
                matched_expected.add(match_index)
                matched_predictions += 1
        missed = [fragment for i, fragment in enumerate(expected) if i not in matched_expected]
        tp += matched_predictions
        fp += len(unmatched_predictions)
        fn += len(missed)
        for claim in claims:
            quote = claim.get("evidence_quote") or ""
            if not quote or quote not in candidate["excerpt"]:
                quote_failures += 1
        evaluated.append({
            "candidate_id": example["candidate_id"],
            "title": example["title"],
            "expected_sentence_count": len(expected),
            "predicted_unique_sentence_count": len(unique_statements),
            "true_positive": matched_predictions,
            "false_positive": len(unmatched_predictions),
            "false_negative": len(missed),
            "unexpected_statements": unmatched_predictions[:5],
            "missed_fragments": missed[:5],
            "duplicate_rows": max(0, len(statements) - len(unique_statements)),
        })

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "evaluated_candidate_count": len(evaluated),
        "true_positive_sentences": tp,
        "false_positive_sentences": fp,
        "false_negative_sentences": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "duplicate_claim_rows_collapsed_for_sentence_scoring": duplicate_rows,
        "evidence_quote_failures": quote_failures,
        "per_candidate": evaluated,
    }


def evaluate(golden: dict) -> dict:
    if golden.get("schema_version") != "1.0":
        raise ValueError("Unsupported golden-set schema_version")
    examples = golden.get("examples")
    if not isinstance(examples, list) or not examples:
        raise ValueError("Golden set must contain a non-empty examples array")
    seen = set()
    for example in examples:
        candidate_id = example.get("candidate_id")
        if not candidate_id or candidate_id in seen:
            raise ValueError(f"Missing or duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)
        if example.get("expected_relevance") not in LABELS:
            raise ValueError(f"Invalid expected_relevance for {candidate_id}")
        if not example.get("title") or not example.get("url"):
            raise ValueError(f"Missing title or URL for {candidate_id}")
        if not isinstance(example.get("excerpt"), str):
            raise ValueError(f"Missing excerpt for {candidate_id}")
        if "expected_claim_fragments" in example and not isinstance(example["expected_claim_fragments"], list):
            raise ValueError(f"expected_claim_fragments must be a list for {candidate_id}")

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_id": golden.get("dataset_id"),
        "extractor_method": METHOD,
        "curation": golden.get("curation"),
        "evaluation_limits": golden.get("evaluation_limits", []),
        "candidate_relevance": score_classification(examples),
        "claim_extraction": score_claim_extraction(examples),
    }


def markdown_report(report: dict) -> str:
    c = report["candidate_relevance"]
    b = c["relevant_vs_out_of_scope"]
    q = report["claim_extraction"]
    lines = [
        "# AI Chip intelligence quality evaluation",
        "",
        f"- Dataset: {report.get('dataset_id')}",
        f"- Extractor: {report.get('extractor_method')}",
        f"- Generated: {report.get('generated_at')}",
        "",
        "## Candidate relevance",
        "",
        f"- Judged examples: **{c['sample_count']}**",
        f"- Accuracy: **{c['accuracy']:.1%}**",
        f"- Macro-F1: **{c['macro_f1']:.1%}**",
        f"- Relevant-vs-out-of-scope precision: **{b['precision']:.1%}**",
        f"- Relevant-vs-out-of-scope recall: **{b['recall']:.1%}**",
        f"- False positives: **{len(c['false_positives'])}**",
        f"- False negatives: **{len(c['false_negatives'])}**",
        "",
        "| Expected / Predicted | Direct | Adjacent | Out of scope |",
        "|---|---:|---:|---:|",
    ]
    names = {
        "direct_ai_compute": "Direct",
        "adjacent_ai_systems": "Adjacent",
        "out_of_scope": "Out of scope",
    }
    for expected in LABELS:
        row = c["confusion_matrix"][expected]
        lines.append(
            f"| {names[expected]} | {row['direct_ai_compute']} | "
            f"{row['adjacent_ai_systems']} | {row['out_of_scope']} |"
        )
    lines += [
        "",
        "## Claim sentence extraction",
        "",
        f"- Evaluated candidates: **{q['evaluated_candidate_count']}**",
        f"- Sentence precision: **{q['precision']:.1%}**",
        f"- Sentence recall: **{q['recall']:.1%}**",
        f"- Sentence F1: **{q['f1']:.1%}**",
        f"- TP / FP / FN: **{q['true_positive_sentences']} / {q['false_positive_sentences']} / {q['false_negative_sentences']}**",
        f"- Repeated metric rows collapsed for sentence scoring: **{q['duplicate_claim_rows_collapsed_for_sentence_scoring']}**",
        f"- Evidence-quote failures: **{q['evidence_quote_failures']}**",
        "",
        "## Claim extraction mismatches",
        "",
    ]
    mismatches = [item for item in q["per_candidate"] if item["false_positive"] or item["false_negative"]]
    if mismatches:
        for item in mismatches:
            lines.append(
                f"- {item['candidate_id']} — {item['title']}: "
                f"{item['false_positive']} unexpected, {item['false_negative']} missed"
            )
            for fragment in item["missed_fragments"]:
                lines.append(f"  - Missed: {fragment}")
            for statement in item["unexpected_statements"]:
                lines.append(f"  - Unexpected: {statement}")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Relevance false positives",
        "",
    ]
    if c["false_positives"]:
        for item in c["false_positives"]:
            lines.append(f"- {item['candidate_id']} — {item['title']} (signals: {', '.join(item['signals']) or 'none'})")
    else:
        lines.append("- None")
    lines += ["", "## Relevance false negatives", ""]
    if c["false_negatives"]:
        for item in c["false_negatives"]:
            lines.append(f"- {item['candidate_id']} — {item['title']} (expected: {item['expected']})")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Interpretation limits",
        "",
        "This is a small, human-curated calibration set, not a statistically representative production estimate. "
        "It evaluates candidate classification and sentence extraction only. It does not measure recall over "
        "papers that the upstream arXiv query never retrieved, and it does not verify the truth of extracted claims.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    golden = json.loads(args.golden.read_text(encoding="utf-8"))
    report = evaluate(golden)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    summary = markdown_report(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
