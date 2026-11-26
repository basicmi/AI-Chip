# Performance knowledge applicability and transfer boundaries

The applicability assessor compares a reviewed knowledge entry's declared
fixed context against a new target context. It is deliberately conservative:
missing fields are unknown, exact declared-value mismatches block direct reuse,
and target-only fields are surfaced rather than silently ignored.

## Example

```bash
python3 scripts/assess_performance_knowledge_applicability.py \
  --catalog data/performance-knowledge.json \
  --target target-context.json \
  --metric target-metric.json \
  --output applicability-report.json
```

Target context should describe the hardware, model, workload, parallelism,
software stack and topology relevant to the question. Supply only fields that
are actually known; do not fill gaps with assumptions. Optional metric JSON
uses key, unit and direction.

## Status meanings

- `declared_context_match`: every field declared by the knowledge entry is
  present and exactly matches. This is necessary for direct reuse, not proof
  that the mechanism transfers or that an outcome will repeat.
- `insufficient_context`: no mismatch was found, but at least one declared
  field is absent. Missing information is not treated as a match.
- `not_applicable_under_declared_context`: one or more declared values differ.
  This blocks direct reuse under the original evidence scope; it does not prove
  that the underlying physical mechanism is impossible on the target system.

Dimension summaries group fields into hardware, model, workload, parallelism,
software, topology, measurement and other. Current comparisons use exact
canonical values (trimmed, case-folded strings); there is no fuzzy similarity
score or learned transfer function. Nested values are flattened by dotted path.
Target-only fields are flagged for review.

Metric compatibility and intervention transferability are separate questions.
Even an exact context match does not establish compatible metric sampling
windows, measurement boundaries, instrumentation or counter semantics. Nor
does it prove that changing the same parameter has the same effect on a new
architecture. These require explicit human review and, where appropriate, a
new controlled experiment.

The tool ranks entries by declared-context match status for triage only. It
does not automatically recommend a configuration, predict performance or
approve knowledge transfer. Hashes identify the submitted target context; they
are not signatures or proof of truth.
