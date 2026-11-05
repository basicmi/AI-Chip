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

## Company profiles and evidence registry

- `company-profiles.json`: structured identity index for the company profiles in `directory.md`, including category, stable directory anchor, logo, summary and carried-over source links.
- `schemas/company-profiles.schema.json`: JSON Schema for company, product, claim, reference and evidence records.
- `scripts/validate_company_profiles.py`: validates profile IDs, directory anchors, source URLs, freshness metadata and claim-to-evidence relationships.

### Evidence policy

A link copied from the directory is a **reference**, not automatically evidence for every statement in a company summary. References begin as `unreviewed`; they become evidence only after a reviewer checks the source, records its publisher/type and review date, and links it to one or more explicit claims.

Products are separate records. Technical specifications and status statements belong in claim records scoped to a specific product or company. Every structured claim must cite at least one evidence record. A claim may be marked `independently_verified` only when at least one linked source is classified as independent.

Freshness is computed from `checked_at`: fresh within 90 days, review due after 90 days, stale after 180 days. Missing dates mean unreviewed, never fresh. Staleness means a source needs rechecking; it does not by itself prove a claim is false.

The initial registry carries over the 50 existing directory summaries and 126 source links without upgrading them to verified facts. Three first-pass examples now demonstrate the full product → claim → evidence relationship: NVIDIA B200, AMD Instinct MI355X and Google TPU7x (Ironwood). They contain 14 structured claims linked to three reviewed primary vendor documents. These remain explicitly `vendor_reported` specifications, not independent benchmark measurements. The other 47 company profiles have no audited evidence or structured claims yet. This is deliberate: no chip specifications, process nodes, bandwidth figures or performance claims are invented to fill the schema.
