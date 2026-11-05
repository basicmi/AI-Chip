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
python3 scripts/validate_company_profiles.py
```

The benchmark validator checks catalogue structure, category references, required descriptive fields and source URLs. It does not run experiments or validate the truth of vendor claims; reviewers should inspect primary sources.

## Company profiles and evidence registry

- `company-profiles.json`: structured identity index for the company profiles in `directory.md`, including category, stable directory anchor, logo, summary and carried-over source links.
- `schemas/company-profiles.schema.json`: JSON Schema for company, product, claim, reference and evidence records.
- `scripts/validate_company_profiles.py`: validates profile IDs, directory anchors, source URLs, freshness metadata and claim-to-evidence relationships.

### Evidence policy

A link copied from the directory is a **reference**, not automatically evidence for every statement in a company summary. References begin as `unreviewed`; they become evidence only after a reviewer checks the source, records its publisher/type and review date, and links it to one or more explicit claims.

Products are separate records. Technical specifications and status statements belong in claim records scoped to a specific product or company. Every structured claim must cite at least one evidence record. A claim may be marked `independently_verified` only when at least one linked source is classified as independent.

Freshness is computed from `checked_at`: fresh within 90 days, review due after 90 days, stale after 180 days. Missing dates mean unreviewed, never fresh. Staleness means a source needs rechecking; it does not by itself prove a claim is false.

The registry carries over the 50 existing directory summaries and 126 source links without upgrading them to verified facts. The first audited wave covers eight companies and 16 products: NVIDIA B200 / GB200 NVL72; AMD MI350X / MI355X; Intel Gaudi 2 / Gaudi 3; Google TPU v6e / TPU7x; AWS Trainium2 / Trainium3; Microsoft Maia 100 / Maia 200; Meta MTIA v2 / MTIA 300; and Cerebras WSE-2 / WSE-3. The registry currently contains 70 structured claims linked to 17 reviewed source records. Claims are explicitly classified as vendor-reported or derived from a stated vendor specification; they are not independent benchmark measurements. The other 42 company profiles remain unreviewed at claim level. Missing specifications are not inferred or fabricated.

## Comparison metadata (schema v1.1)

Numeric claims may carry a `metric_context` object describing:
- `metric_type`: specification, theoretical peak, vendor-measured, independently measured, production-observed, or derived.
- `precision` and `sparsity`: required for numeric compute claims so FP4/FP8/BF16 and dense/sparse figures remain distinct.
- `measurement_scope`: die, chip, package, module, board, server, rack, pod, cluster, or system.
- `operation` and optional `directionality`, `configuration`, `workload_id`, and `benchmark_project_id`.

The root `comparison_policy` requires precision, sparsity, measurement scope, and measurement type to match before comparing values. System-level aggregates must not be compared with per-chip values. Original source units are preserved; display-layer unit conversion must retain the original value and unit.
