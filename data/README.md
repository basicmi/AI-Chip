# Data directory

This directory contains curated public information datasets used by the AI Chip landscape.

- `compatibility.json`: version-scoped public evidence for software/platform integrations, with optional exact product links when sources name a specific SKU or generation.
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
- `/products/` (`products.md` + `assets/js/product-explorer.js`): searchable product catalogue and source-linked comparison workspace powered by `company-profiles.json`, `compatibility.json` and `workloads.json`.
- `schemas/company-profiles.schema.json`: JSON Schema for company, product, claim, reference and evidence records.
- `scripts/validate_company_profiles.py`: validates profile IDs, directory anchors, source URLs, freshness metadata and claim-to-evidence relationships.

### Evidence policy

A link copied from the directory is a **reference**, not automatically evidence for every statement in a company summary. References begin as `unreviewed`; they become evidence only after a reviewer checks the source, records its publisher/type and review date, and links it to one or more explicit claims.

Products are separate records. Technical specifications and status statements belong in claim records scoped to a specific product or company. Every structured claim must cite at least one evidence record. A claim may be marked `independently_verified` only when at least one linked source is classified as independent.

Freshness is computed from `checked_at`: fresh within 90 days, review due after 90 days, stale after 180 days. Missing dates mean unreviewed, never fresh. Staleness means a source needs rechecking; it does not by itself prove a claim is false.

The registry carries over the 50 existing directory summaries and 126 inherited source links without upgrading them to verified facts. The structured product catalogue is maintained in `company-profiles.json`; counts are computed from the current registry rather than hard-coded in this guide. Software integration records distinguish platform-level support from product-specific mappings. Recent additions include NVIDIA Rubin GPU, Vera Rubin NVL72, Groq 3 LPU and LPX; AMD MI455X and Helios; Microsoft Maia 300; Intel GPU D270 (Crescent Island); Meta MTIA 300; and Cerebras WSE-3 Turbo / CS-4. Google TPU7x (Ironwood) and AWS Trainium3 source records were refreshed against current official product documentation. Claims are explicitly classified as vendor-reported unless independent evidence is present; they are not independent benchmark measurements. 33 company profiles remain explicitly unreviewed; review status is tracked per profile and claim, and should be read from the live registry rather than inferred from the historical carry-over count. Missing specifications are not inferred or fabricated.

## Comparison metadata (schema v1.2)

Numeric claims may carry a `metric_context` object describing:
- `metric_type`: specification, theoretical peak, vendor-measured, independently measured, production-observed, or derived.
- `precision` and `sparsity`: required for numeric compute claims so FP4/FP8/BF16 and dense/sparse figures remain distinct.
- `measurement_scope`: die, chip, package, module, board, server, rack, pod, cluster, or system.
- `operation` and optional `directionality`, `configuration`, `workload_id`, and `benchmark_project_id`.

The root `comparison_policy` requires precision, sparsity, measurement scope, and measurement type to match before comparing values. System-level aggregates must not be compared with per-chip values. Original source units are preserved; display-layer unit conversion must retain the original value and unit. The Product Explorer uses these fields to align only like-for-like rows; it keeps unmatched scopes and units separate and does not produce a composite ranking.

## Product-to-system relationships

Product records may reference `compatibility_platform_ids`. These IDs connect product cards to the platform-level entries in `compatibility.json`; the explorer then displays the software integrations and workload paths associated with that platform. These are platform-level relationships, not a guarantee that every SKU, model, precision or feature is supported. Always read the integration's version and limitation notes.

The The current product registry contains 53 company profiles and 40 structured accelerator products. The compatibility catalogue contains 17 platforms and 29 software integration records; the workload catalogue contains 28 paths. The model-support catalogue currently includes 7 model families and 12 evidence-backed model-to-hardware paths. Paths marked `integration_only` document a public software entry point only. They do not imply a completed workload test or benchmark.

The benchmark catalogue remains a directory of benchmark projects and tools. No product-specific benchmark result is inferred from a platform integration; a product result must be added only with a concrete model/configuration, system boundary, measurement and source.


## Weekly evidence maintenance

The repository runs `.github/workflows/data-maintenance.yml` weekly and on manual dispatch. It:

1. Re-validates compatibility, workload, benchmark and company-profile registries.
2. Publishes a human-readable review queue to the GitHub Actions run summary.
3. Checks source URLs and uploads an advisory link-audit report as a 30-day artifact.

The link checker does not edit source data or promote references to evidence. HTTP 403/429 responses are classified as blocked rather than broken, since publishers may apply bot protection. A reachable URL does not prove that its content supports a technical claim. Review dates and claim status must be updated only after a human has opened the source and verified the relevant statement.


## Benchmark results registry

- `benchmark-results.json`: normalized, source-linked result submissions and observations.
- `schemas/benchmark-results.schema.json`: JSON Schema for the registry.
- `scripts/import_benchmark_results.py`: imports official MLPerf Inference v6.1 summary rows and, optionally, public SemiAnalysis InferenceX API rows.
- `scripts/validate_benchmark_results.py`: checks source references, IDs, product/platform links, summary counts, strict power-validity semantics, and optional low-level hardware evidence.
- `docs/hardware-bottleneck-evidence.md`: versioned counter vocabulary, measurement boundaries, provenance and bottleneck-evidence requirements.
- `hardware-counter-mappings.json` + `schemas/hardware-counter-mappings.schema.json`: source-aware mappings for NVIDIA DCGM, Nsight Compute and AMD ROCm Compute Profiler.
- `scripts/normalize_hardware_counters.py`: normalizes a structured raw-counter JSON export while retaining unmapped fields and refusing cumulative counters without an explicit delta.
- `scripts/derive_hardware_metrics.py`: derives FLOP/s, DRAM bandwidth, peak-utilization ratios, KV-cache occupancy and link utilization from compatible evidence inputs.
- `scripts/diagnose_hardware_performance.py`: generates evidence-constrained roofline, per-link communication, serving-runtime and candidate-attribution reports; it never emits an automatic bottleneck verdict.
- `/results/`: searchable result explorer with source, vendor, model, scenario, division, availability and system-type filters, plus strict-cohort hardware evidence coverage.

### Current snapshot

The initial snapshot contains **492 MLPerf Inference v6.1 records** from the official MLCommons `summary.json`: 480 Available, 8 Preview and 4 RDI; 476 Closed and 16 Open; 468 datacenter and 24 edge records. 125 rows are marked inferred by the source. The summary extract contains no measured power records. A design-power field must never be presented as measured power.

MLPerf Power is listed separately as a methodology source with no imported result rows yet. The current Inference v6.1 summary's zero power rows must not be interpreted as a zero-watt result or as evidence that MLPerf Power has no published work.

The submitter and accelerator vendor are separate fields: a system integrator or cloud submitter is not necessarily the accelerator manufacturer. Product/platform links are populated only when the accelerator model maps clearly to a reviewed product record. CPU-only submissions and unknown accelerators remain unlinked.

### Import and update

From the repository root:

```bash
# Refresh the official MLPerf v6.1 snapshot
python3 scripts/import_benchmark_results.py --source mlperf

# Import all currently available InferenceX model rows from its public API
python3 scripts/import_benchmark_results.py --source inferencex

# Or import selected InferenceX display models
python3 scripts/import_benchmark_results.py --source inferencex --model DeepSeek-R1-0528 --model DeepSeek-V4-Pro

# Preview changes without writing the JSON file
python3 scripts/import_benchmark_results.py --source all --dry-run

# Validate the result registry and its links to products/platforms
python3 scripts/validate_benchmark_results.py
python3 -m unittest discover -s tests -p "test_benchmark_results.py"
```

The InferenceX importer discovers model availability from /api/v1/availability, then maps its raw database model keys (for example, dsr1) to the display names required by /api/v1/benchmarks (for example, DeepSeek-R1-0528) through /api/v1/views/options and models[].dbKeys. It verifies that every available raw model key is mapped and that every returned result row belongs to the queried model's mapped key set. Identical rows returned through display-name aliases are stored once; conflicting duplicate IDs, unmapped keys, empty model responses and partial API failures abort the refresh. Each successful source snapshot records the API endpoints, retrieval timestamp, raw model-key coverage, display-name mapping and per-model row counts.

The InferenceX importer uses the documented unauthenticated read API. It preserves the raw scalar metric map and separately emits a small normalized metric view with explicit units and optimization direction. Unknown metric keys remain in the raw map and are not silently interpreted. In particular, `median_intvty` is interactivity in `tok/s/user` (higher is better), not inter-token latency; `p99_itl` and `p99_tpot` are latency metrics in seconds. Throughput fields are tokens/s per physical GPU unless the source key states otherwise. For disaggregated rows, the API defines distinct denominators for total, prefill and decode pools; do not mix them.

The importer also preserves model display name and raw model key, physical prefill/decode GPU counts, worker pools, topology, software image, recipe fingerprint, run URL and parallelism. GPU power/energy requires both `power_valid=1` and `power_metric_schema_version=2`. The importer preserves the GPU verdict as valid, failed, schema-incomplete or unreported. CPU-side and compute-module telemetry uses the independent `cpu_power_valid` verdict: valid, failed or not present. A failed or absent GPU verdict does not invalidate a separately validated CPU-side leg. `power_metrics_available` indicates that at least one measured GPU or CPU/module power/energy field is present and passes its own validation. Missing metrics remain unavailable.

The GitHub Actions workflow `.github/workflows/refresh-benchmark-results.yml` supports manual refreshes of MLPerf, InferenceX or both and a weekly InferenceX refresh. It opens a pull request rather than writing benchmark data directly to the default branch. Empty availability responses, missing rows for an advertised model, malformed rows, duplicate result IDs or partial API failures abort the import and preserve the existing snapshot.

### Comparability rules

1. Keep benchmark suite and version fixed.
2. Keep model/task, scenario, division, system type and accuracy/quality target fixed.
3. Keep metric units and measurement boundaries fixed. Do not compare system throughput with per-accelerator throughput.
4. Keep Available, Preview, RDI and inferred submissions visibly distinct.
5. Separate submitter from accelerator vendor.
6. Do not interpret design power as measured power or missing power as zero.
7. Preserve the source row and producer run link. A published submission is not automatically an independent replication.
8. Do not rank different suites or workload families on one composite score.

The Results Explorer's “Show strict cohort” action uses source-specific matching keys. InferenceX cohorts require the same API/source version, model checkpoint, workload type, ISL, OSL, concurrency, precision, speculative mode, serving mode and normalized metric/unit. MLPerf Inference cohorts require the same suite/version, model, scenario, division, availability, system type, accuracy target, precision, inferred status and result unit. Missing critical metadata blocks strict cohort creation rather than treating unknown values as equal. Hardware, system size, framework, image and parallelism remain visible comparison variables, not implicit equality requirements.


## Product Explorer comparison workspace

The Product Explorer supports side-by-side comparison of up to **six products**. Rows align only when topic, precision, sparsity, measurement scope, metric type and source unit match. Missing or non-comparable values remain separate; chip, module, rack and system specifications are never silently mixed. The six-product limit is a display/workflow limit, not a recommendation to compare unlike architectures or workloads.


## Product registry v3 coverage and lifecycle tracking

The 2026-11-06 v3 review wave adds structured profiles for Broadcom, Marvell, Tenstorrent, Etched, d-Matrix, SambaNova, FuriosaAI, Rebellions, Huawei Ascend and Cambricon. Platform-level custom-XPU records are used when a vendor has not disclosed a merchant SKU; missing chip-level specifications remain blank rather than inferred.

Product records may include availability_history, a chronological list of dated status events (announced, sampling, shipping, production, roadmap, discontinued, or unknown). Each event links to a reviewed evidence record. Dates preserve source precision: use YYYY-MM when only a month is known and YYYY-MM-DD when the source gives a day. The latest event must match the product's current availability. This is a source-backed event log, not a claim that every transition is independently audited.


## Product-specific software compatibility links

Compatibility records may optionally include `product_ids`. Each ID must exist in `data/company-profiles.json`. Use this field only when the cited integration evidence explicitly names the product or generation. If the evidence names only a vendor platform or backend, omit `product_ids` and retain the platform-level record. The Product Explorer displays these two scopes separately; it must never copy a platform-level support statement onto every SKU as if each SKU were individually validated.


## Corporate ownership and operating status

Company profiles may include an optional corporate_status object. It records whether the company remains independent, operates as a wholly owned subsidiary, has been integrated as a business unit, or has ceased operations. The object links to reviewed evidence records and distinguishes an equity acquisition from an acqui-hire or technology license. An acqui-hire must not be represented as an acquisition of the whole company or its IP unless the source says so. The Directory groups acquired and discontinued companies separately from independent startups; searchable company cards show the ownership status.


## Model support registry

model-support.json links exact model checkpoints to accelerator products, software integration records, precision/quantization modes, execution modes and source-backed deployment evidence. Support levels distinguish documented recipes, upstream verification, vendor-reported claims, independent tests and integration-only paths. The validator cross-checks model IDs, product IDs, platform IDs and software integration IDs against the existing registries. A documented recipe is not an AI-Chip independent benchmark; measured performance belongs in benchmark-results.json.

The first reviewed wave includes Llama 3.1 405B on AWS Trainium2 and Google TPU v6e, Llama 3.3 70B on Trainium2/Trainium3, and upstream vLLM FLY model/hardware verification for selected Llama 3.1 and Qwen3 models on AMD MI355X. Coverage is intentionally narrow and source-driven rather than extrapolated from platform-level support.
