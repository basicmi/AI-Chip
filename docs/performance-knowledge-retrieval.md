# Performance knowledge retrieval

Retrieve historical, human-reviewed performance claims for a new engineering
question. The tool is an evidence navigator, not a configuration recommender.

## Example

```bash
python3 scripts/retrieve_performance_knowledge.py \
  --catalog data/performance-knowledge.json \
  --query "decode TP queueing and TPOT regression" \
  --target target-context.json \
  --metric target-metric.json \
  --limit 20 \
  --output retrieval-report.json
```

Target context uses the same nested field conventions as the applicability
assessor. Optional metric JSON contains `key`, `unit` and `direction`.
The query is matched against topic, hypothesis, reviewer interpretation,
applicability and limitations using simple token overlap.

## Retrieval tiers

- `priority_human_review`: declared context matches and metric is exact or
  was not supplied. This is a review priority, not an approval or recommendation.
- `exploratory_only`: context is incomplete, metric differs/is unknown, or
  the human verdict is Refuted or is not a reusable Supported claim. Refuted
  claims remain visible as counter-evidence and are never promoted to best practices.
- `not_applicable_under_declared_context`: at least one declared source
  context field differs. Retained as a possible boundary/counterexample, not
  eligible for direct reuse.

The result exposes matched query terms, missing and mismatched context fields,
target-only fields, metric compatibility, reviewer interpretation, limitations
and cited run/source references. Potential contradictions connected to returned
knowledge IDs are included for human inspection.

## Ranking and limits

Ranking is deterministic and heuristic: context tier, topic token overlap,
technical-text overlap, number of matched terms and knowledge ID. It is not a
learned semantic search model, does not infer causal similarity, and does not
score predicted performance. Query overlap helps locate candidates but cannot
establish relevance by itself.

A Refuted claim remains useful as counter-evidence. A context mismatch blocks
direct reuse but does not prove a mechanism cannot exist on the target system.
A complete context match is necessary, not sufficient: measurement boundaries,
metric semantics, intervention transferability, source authenticity and
mechanism-specific evidence still require human review.

The retrieval report preserves exact evidence references and reviewer caveats.
It does not generate configuration changes, auto-run experiments or modify the
knowledge catalog.
