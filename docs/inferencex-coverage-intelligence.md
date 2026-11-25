# InferenceX registry coverage intelligence

Run from the repository root:

```bash
python3 scripts/analyze_inferencex_coverage.py --output /tmp/inferencex-coverage.json
```

This report answers two distinct questions:

1. **What is actually recorded?** Field coverage reports present/missing counts,
   percentages and distinct values for model, hardware, software framework,
   recipe fingerprint, benchmark version, workload dimensions, GPU role counts,
   topology, source/evidence metadata and stable configuration. Metric coverage
   validates the numeric value, unit, family and direction for each supported
   normalized metric.
2. **What analyses could the recorded evidence support?** Readiness counts
   multi-point concurrency, ISL, OSL and two-dimensional ISL×OSL series. A
   candidate requires a matching recorded context, a recipe fingerprint,
   stable configuration and at least two observed levels (two values on each
   axis for the two-dimensional matrix).

The analysis-readiness section is a data coverage diagnostic, not a performance
report. It does not calculate or rank performance. Its context equality is
limited to recorded metadata; hidden runtime differences can remain.

Missing-field blocker counts are overlapping: one record may contribute several
blockers. Field coverage counts explicit false booleans as present, because
"single-node" and "not disaggregated" are meaningful reported values. Unknown,
empty and "not reported" strings are treated as missing.

The denominator is the current registry's InferenceX record count, not all
results published by the benchmark provider. Distinct-value counts are not
evidence of useful sample size or balanced coverage. A populated field may
still be inaccurate or inconsistently normalized. No missing values are
inferred, and no benchmark is executed.
