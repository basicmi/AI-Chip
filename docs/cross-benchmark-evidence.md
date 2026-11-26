# Cross-benchmark metric evidence crosswalk

## Purpose

The `/cross-benchmark/` page discovers candidate relationships between normalized metric definitions used by different benchmark suites. It is a human-review aid for metric semantics and provenance. It does not compare score values across suites.

## Candidate construction

The page reads the existing compressed benchmark registry and extracts finite numeric observations with an explicit normalized metric key, unit, family and direction. Suite/metric definitions are grouped by:

- benchmark suite and reported version;
- normalized metric key;
- unit;
- metric family;
- optimization direction.

A pair is considered only when it belongs to two different benchmark suites and has the same metric family and direction. Candidate relationship labels are:

1. **Same normalized signature** — key, unit, family and direction all match.
2. **Same family, unit and direction** — unit/family/direction match, but normalized keys differ.
3. **Same family and direction; unit differs** — a unit-conversion review may be relevant, but no conversion is performed.

Definitions without an explicit normalized unit/family/direction, non-numeric values, generic suite-scalar fallbacks and unspecified optimization direction are not used to create candidate links.

## What is intentionally not inferred

A matching normalized signature is not proof that two suites measure the same thing. The crosswalk does not assume equivalence of:

- workload shape, arrival process, concurrency, prompt/output length or sequence distribution;
- accuracy target, model variant, quantization or precision;
- statistic (mean, median, percentile), aggregation window or measurement boundary;
- system boundary, host, accelerator count, topology or software stack;
- benchmark rules, submission division, compliance or evidence quality.

No score values are combined, converted, rescaled, ranked or plotted across suites. Source class and evidence level are retained as provenance, not as a quality upgrade. A candidate must be checked against the original suite documentation and source record before any downstream comparison policy is changed.

## Data and execution

- Reads `data/benchmark-results.json.gz` through the existing site data route.
- Does not create a second registry or modify source records.
- Does not execute benchmarks or generate synthetic performance data.
- The inspection panel shows metric-definition metadata and a small set of source-linked example records; it deliberately omits metric values.

## Validation

Browser smoke tests use a deterministic in-memory fixture to verify exact-signature candidates, unit-review candidates, filters and source metadata inspection. The test fixture is not production benchmark evidence.
