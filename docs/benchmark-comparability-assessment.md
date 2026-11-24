# Benchmark Comparability Assessment

## Purpose

`scripts/assess_benchmark_comparability.py` builds a conservative, deterministic
assessment of which published result records are eligible for side-by-side
review. It is deliberately a comparability gate, not a ranking algorithm.

Run it from the repository root:

```bash
python3 scripts/assess_benchmark_comparability.py \
  --benchmark-results data/benchmark-results.json \
  --output /tmp/benchmark-comparability-report.json
```

The JSON report includes policy version, eligible/excluded record counts,
comparison groups, pair counts, system and workload signatures, metric
definitions, accelerator identities, software stacks, source provenance and
explicit limitations.

## V1 decision policy

A record is eligible only when all of the following are available:

- benchmark suite and version;
- model, scenario, division, availability, accuracy statement and weight data type;
- explicit non-inferred result and zero reported errors;
- non-empty workload and benchmark configuration objects;
- system type, node count, total accelerator count, accelerators per node and host processor model;
- accelerator identity, software metadata and a numeric metric with a unit.

Records are grouped only when the following match exactly:

1. benchmark suite and version;
2. model, scenario, division and availability;
3. accuracy statement and weight data type;
4. complete workload and configuration objects;
5. system boundary (system type, nodes, accelerator count, accelerators per node,
   host processor model, and any explicit prefill/decode GPU counts);
6. metric key, unit, family and direction.

Accelerator identity is intentionally the comparison axis, not a matching
requirement. A group must contain at least two distinct accelerator identities.

### Direct vs conditional

- **Directly comparable**: all protocol and system-boundary fields match and
  software metadata is identical.
- **Conditionally comparable**: protocol and system boundary match, but software
  metadata differs. Results are shown together with the difference visible;
  software differences may explain part of the observed performance gap.

Source class and evidence level remain attached to every record. Different
provenance classes do not automatically invalidate a technical comparison, but
must remain visible to the reviewer. A vendor-reported result does not become
independent evidence because it passes this policy.

### Excluded / not grouped

Missing context is not inferred. Records with missing workload, configuration,
system boundary, software, metric unit, accuracy or precision context are
excluded with machine-readable reason codes. Different suites, versions,
models, scenarios, workload definitions, metric definitions or system
boundaries form separate groups; the engine does not convert scores across
suites or silently normalize test conditions.

## Interpretation limits

A direct match means only that the registry's recorded test definition and
system boundary match under policy v1. It does not prove that two submitters
implemented the benchmark identically, that source claims are true, that
measurements are independently reproducible, or that the difference is caused
solely by the accelerator. It does not account for hidden firmware, cooling,
power limits, compiler flags or measurement uncertainty unless those are
captured in the explicit configuration/software fields.

The engine does not generate a leaderboard, composite score, cross-suite
normalization, causal explanation or investment recommendation. Pairwise
values should be inspected alongside original source links and evidence class.

## Tests

```bash
python3 -m unittest discover -s tests -p "test_benchmark_comparability.py"
```

Tests cover exact-match direct groups, software-difference downgrade,
workload/version mismatch, missing system context, inferred results, repeated
same-hardware records and missing metric units.
