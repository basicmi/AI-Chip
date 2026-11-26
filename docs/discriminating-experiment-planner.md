# Discriminating experiment planner

Build a compact measurement plan from a hypothesis comparison report and the
same versioned hypothesis catalog.

## Example

```bash
python3 scripts/compare_performance_hypotheses.py \
  --diagnosis diagnosis.json \
  --hypotheses data/performance-hypothesis-catalog.json \
  --output comparison.json

python3 scripts/build_discriminating_experiment_plan.py \
  --comparison comparison.json \
  --hypotheses data/performance-hypothesis-catalog.json \
  --limit 12 \
  --output discriminating-plan.json
```

## Method

1. Enumerate every pair of competing hypotheses in the comparison.
2. Read each hypothesis' explicitly declared discriminating measurements.
3. A measurement is considered pair-discriminating only if it appears in one
   hypothesis' list and not the other's. Shared measurements are retained as
   context but do not by themselves distinguish that pair.
4. Deduplicate measurement descriptions across hypotheses.
5. Apply deterministic greedy weighted set cover to select a compact set
   covering as many hypothesis pairs as possible.
6. Return uncovered pairs explicitly when the requested measurement limit
   prevents complete coverage.

Relative cost bands are transparent heuristics: likely existing telemetry,
targeted profiling/instrumentation, or controlled intervention. They are not
engineering-hour estimates, risk measurements or information-gain scores.
The greedy algorithm is deterministic and explainable, but does not claim a
globally optimal experimental design.

For each pair the plan includes both hypotheses' predeclared supporting and
weakening outcomes. Engineers must still predeclare expected directions,
sampling boundaries, practical effect sizes, workload controls and acceptable
measurement overhead before collecting data.

The tool does not collect telemetry, execute experiments, rank hypotheses,
assign confidence, infer causality or recommend a configuration. If two
hypotheses share all declared measurements, the pair remains uncovered and
requires an expert-designed discriminator rather than an invented test.
