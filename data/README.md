# Data directory

This directory contains curated public information datasets used by the AI Chip landscape.

- `compatibility.json`: version-scoped public evidence for software/platform integrations.
- `workloads.json`: descriptive workload taxonomy and public software-path references.
- `benchmark-projects.json`: directory of public benchmark suites, result portals, measurement tools and microbenchmarks.

## Editorial scope

AI Chip is an information and research directory. It does not run benchmark experiments, host a benchmark runner, certify hardware, or generate performance scores. All published benchmark results must link to their original public source and retain the publisher's attribution and methodology.

A benchmark suite, a measurement harness, a vendor-reported result and an independently published result are different kinds of resources. Do not combine them into one ranking. When comparing public results, preserve the exact model, workload, hardware, software versions, measurement definition and system boundary.

## Validate

From the repository root:

```bash
python3 scripts/validate_compatibility.py
python3 scripts/validate_workloads.py
python3 scripts/validate_benchmarks.py
```

The benchmark validator checks catalogue structure, category references, required descriptive fields and source URLs. It does not run experiments or validate the truth of vendor claims; reviewers should inspect primary sources.
