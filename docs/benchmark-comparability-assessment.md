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

The engine uses source-specific profiles for the two benchmark feeds already normalized by this repository, plus a conservative generic profile for future sources. A record is eligible only when all required fields for its profile are available:

- benchmark suite and version (InferenceX currently publishes no version in this registry; its profile therefore remains scoped to the InferenceX source and exact workload signature);
- model, scenario, division, availability, accuracy statement and weight data type;
- explicit non-inferred result and zero reported errors;
- explicit workload/configuration fields appropriate to the source profile;
- a complete source-appropriate system boundary;
- accelerator identity, software metadata and a numeric metric with a unit.

Records are grouped only when the following match exactly:

1. benchmark suite and version (or the same source-scoped version-unknown profile for InferenceX);
2. model, scenario, division and availability;
3. accuracy statement and weight data type where that suite defines one;
4. the complete source-specific workload signature;
5. metric key, unit, family and direction.

System size/topology and execution configuration are retained as comparison
dimensions rather than silently used to split every group. This allows the report
to show same-workload comparisons across different accelerator counts or
parallelism layouts, but those differences downgrade the group to conditional
comparability.

Accelerator identity is intentionally the comparison axis, not a matching
requirement. A group must contain at least two distinct accelerator identities.

### Direct vs conditional

- **Directly comparable**: the exact protocol signature, software metadata,
  system boundary and applicable stable configuration match.
- **Conditionally comparable**: the test protocol matches, but software,
  system scale/topology or applicable parallelism configuration differs or is
  incomplete. Results are shown together with those differences visible; they
  may explain part of the observed performance gap.

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
For InferenceX, run IDs and timestamps are excluded from the stable configuration
signature; TP/EP, worker counts and offload mode remain comparison dimensions.

## Tests

```bash
python3 -m unittest discover -s tests -p "test_benchmark_comparability.py"
```

Tests cover exact-match direct groups, software-difference downgrade,
workload/version mismatch, missing system context, inferred results, repeated
same-hardware records and missing metric units.


## Descriptive performance-gap summary (v1.1)

Each comparison group now includes `observed_metric_spread`:

- minimum, maximum and absolute range for the published metric;
- relative spread as a percentage of the absolute midpoint between minimum and maximum;
- best/worst record IDs only when the metric direction is explicitly `higher` or `lower`;
- dimensions that vary across the records: accelerator identity, software, system boundary,
  configuration and evidence class.

The spread is descriptive, not causal. Varying dimensions are candidate confounders;
the report does not estimate how much of the performance difference is caused by
the accelerator, software, scale or parallelism. Context metrics with no ranking
direction deliberately have no best/worst result.

Pair counts now count only pairs with distinct accelerator identities. Multiple
records for the same accelerator no longer inflate cross-hardware comparison
counts. Every record retains its own system-boundary fields so reviewers can see
scale/topology differences rather than inheriting a group-level boundary.
