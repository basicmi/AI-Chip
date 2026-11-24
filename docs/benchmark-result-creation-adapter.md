# Benchmark Result Creation Adapter (Typed Adapter 2)

## Scope

The first benchmark-result adapter appends exactly one result to an **already
registered source** in `data/benchmark-results.json`. It does not create or
edit source definitions, import remote data, alter existing records, or change
company/product/model registries.

The adapter is deliberately narrower than the benchmark schema:
- one existing `source_id` and one new result record;
- source class must exactly match the existing source registry;
- `evidence_level` must equal `source_class`; no evidence promotion;
- `source_url` must exactly match a URL already registered for that source;
- record ID and source-scoped `source_record_key` must be unique;
- raw metric values must be numeric; the existing registry validator remains
  authoritative for semantic and structural checks;
- power claims, hardware-counter evidence, runtime traces and normalized
  derived metrics are excluded from v1 and require their dedicated validation
  paths.

A vendor-reported result remains vendor-reported. Human approval means only
that the reviewer inspected the supplied source and approves adding this row;
it does not establish factual truth, independent measurement, reproducibility
or cross-suite comparability.

## Approval Manifest

The manifest has schema version 1.0 and exactly these fields:
- `approval_id`, `reviewer`, `reviewed_at` and explicit decision
  `approved_new_benchmark_result`;
- an existing `source_id`;
- one complete `record` using the required fields in
  `schemas/benchmark-results.schema.json`;
- review notes of at least 30 characters.

The record must retain the original benchmark suite/version, model, scenario,
system boundary, accelerator count, software context, division/availability,
result value and unit, accuracy text, inference flag and source record key.
Unknown values should use the registry's explicit null/empty/unknown convention;
they must not be guessed. The adapter does not accept power fields or
hardware/runtime evidence in this first version.

## Build and verify locally

From the repository root:

```bash
python3 scripts/build_benchmark_result_proposal.py build \
  --benchmark-results data/benchmark-results.json \
  --approval /path/to/benchmark-result-approval.json \
  --proposal-output /tmp/benchmark-proposal.json \
  --database-output /tmp/benchmark-results-proposed.json \
  --patch-output /tmp/benchmark-patch.json \
  --audit-output /tmp/benchmark-audit.json \
  --diff-output /tmp/benchmark-results.diff
```

Verification uses the separate Approval Manifest and exact base registry:

```bash
python3 scripts/build_benchmark_result_proposal.py verify \
  --benchmark-results data/benchmark-results.json \
  --proposal /tmp/benchmark-proposal.json \
  --approval /path/to/benchmark-result-approval.json \
  --database-output /tmp/benchmark-results-proposed.json \
  --patch-output /tmp/benchmark-patch.json \
  --audit-output /tmp/benchmark-audit.json \
  --diff-output /tmp/benchmark-results.diff
```

The builder never edits the checkout. The package binds to the exact raw base
file SHA256 and deterministic proposed-registry SHA256. Its patch is limited
to appending one record and reconciling the source record count, registry
version, import date and summary.

## Review boundary

The builder runs the existing `validate_benchmark_results.py` database
validator against the proposed registry. A later integration workflow should
rebuild against current master, re-run validation and open a review-only PR.
There is no auto-merge or direct registry write in this adapter.

## Tests

```bash
python3 -m unittest discover -s tests -p "test_benchmark_result_proposal.py"
```

Tests cover exact append/replay, duplicate record IDs and source keys, source
URL binding, source-class preservation, excluded power claims, stale base
registry and tampered operations.
