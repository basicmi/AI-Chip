# Hardware Bottleneck Evidence Contract

This document defines an optional, source-linked evidence format for low-level accelerator measurements in data/benchmark-results.json. It is a data contract and interpretation policy, not a profiler, benchmark runner, hardware certification, or automatic bottleneck classifier.

The registry must preserve missing evidence as missing. Aggregate throughput, TTFT, TPOT, GPU utilization, or allocated memory alone do not establish a compute-, HBM-, KV-cache-, or communication-bound workload.

## Goals

- Preserve the exact counter/telemetry name and the tool or publisher that produced it.
- Keep measurement scope, aggregation, units, sampling window, and source artifact attached to every evidence bundle.
- Distinguish raw hardware counters, telemetry, and derived values.
- Permit records to omit low-level evidence entirely.
- Make future cross-run analysis possible without inventing counters or silently converting unlike system boundaries.

## Record shape

A benchmark record may contain an optional hardware_evidence object. Its schema is defined in schemas/benchmark-results.schema.json under $defs.hardwareEvidence. Version 1.0 contains:

| Field | Meaning |
|---|---|
| collector | Collector name, version, and class: profiler, device/runtime/network telemetry, publisher export, or other |
| system_scope | Per-GPU, per-link, per-node, per-system, or per-process boundary and device count |
| sampling | Timezone-aware start/end, sample interval, and sample count |
| provenance | Source class, HTTP(S) evidence URL, collection timestamp, optional artifact SHA-256 |
| metrics[] | Canonical metric ID, value/unit, raw-vs-derived kind, aggregation, scope, exact source name, and optional derivation formula |

A metric's source_name is the exact counter/telemetry field name emitted by the collector. metric_id is the normalized semantic identity. Compute FLOP metrics must also carry precision and sparsity metadata. Do not replace the source name with a guessed alias.

## Canonical metric vocabulary

| Domain | Metric IDs | Unit |
|---|---|---|
| Compute | sm_active_pct, tensor_active_pct | % |
| Compute | compute_flop_count | FLOP |
| Compute | achieved_flops, theoretical_peak_flops | FLOP/s |
| HBM traffic | dram_read_bytes, dram_write_bytes, hbm_used_bytes, hbm_capacity_bytes | byte |
| HBM bandwidth | dram_bandwidth_bytes_per_s, dram_peak_bandwidth_bytes_per_s | byte/s |
| KV cache | kv_cache_used_bytes, kv_cache_capacity_bytes | byte |
| KV cache | kv_cache_tokens, kv_cache_token_capacity | token |
| KV cache | kv_cache_hit_rate_pct | % |
| Fabric traffic | nvlink_tx_bytes, nvlink_rx_bytes, pcie_tx_bytes, pcie_rx_bytes, network_tx_bytes, network_rx_bytes | byte |
| Fabric bandwidth | link_bandwidth_bytes_per_s, link_peak_bandwidth_bytes_per_s | byte/s |
| Fabric utilization | link_utilization_pct | % |
| Power / thermal | gpu_power_w | W |
| Power / thermal | gpu_clock_hz, memory_clock_hz | Hz |
| Power / thermal | temperature_c | °C |
| Power / thermal | throttle_active_pct | % |

link_type is required for all NVLink, PCIe, generic link_*, and network_* metrics (nvlink, pcie, infiniband, roce, ethernet, or other). A per-link counter must not be compared with a per-GPU or per-system rate without an explicit aggregation procedure.

## Measurement and normalization rules

1. Units are canonical. The validator enforces the unit for each metric ID. Convert source units only in a documented transformation and preserve the exact source field name.
2. Scope is mandatory. Metrics may be per-kernel, per-GPU, per-link, per-node, per-system, or per-process; the evidence bundle's system_scope remains a hardware/system boundary. Never silently multiply a per-GPU value into a system total.
3. Aggregation is mandatory. Instantaneous, mean, max, percentiles, sum, and rate are not interchangeable. Byte counters require a measurement window before a rate is derived.
4. Sampling is mandatory. Record a timezone-aware measurement interval, sample cadence, and sample count. Do not compare measurements from materially different windows as if they were simultaneous.
5. Raw vs derived is explicit. hardware_counter and telemetry entries carry the collector's source name. A derived entry must include a formula and references to inputs present in the same evidence bundle.
6. Percentages are bounded. Percent-valued metrics must be in [0, 100]. Do not treat a percentage as a ratio unless the transformation is explicit.
7. Provenance is required. Every evidence bundle links to a source artifact or publisher record. An optional SHA-256 digest pins the exported artifact; it does not prove that the measurement is correct.
8. No evidence is not zero. An absent counter means unavailable/unknown, not zero activity, zero traffic, or an idle device.

## Counter mapping catalog and metric derivation

The source-aware catalog lives in `data/hardware-counter-mappings.json`, validated by `schemas/hardware-counter-mappings.schema.json` and `scripts/validate_hardware_counter_mappings.py`. Each mapping records the exact source field or profiler label, collector family, source field ID where documented, canonical metric ID, units, conversion, default scope/aggregation, mapping quality, and caveats.

The primary references are the [NVIDIA DCGM field identifiers](https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html), [Nsight Compute Profiling Guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/), and [AMD ROCm Compute Profiler pipeline metrics](https://rocm.docs.amd.com/projects/rocprofiler-compute/en/develop/conceptual/cdna/pipeline-metrics.html).

The first catalog covers:

- **NVIDIA DCGM:** SM/Tensor/DRAM activity ratios; PCIe and NVLink traffic; per-link NVLink L0-L17 fields; SM/memory clocks; GPU temperature and board power.
- **NVIDIA Nsight Compute:** the documented SM throughput metric `sm__throughput.avg.pct_of_peak_sustained_elapsed`, retained as a kernel-scoped peak-throughput percentage rather than relabeled as SM active time.
- **AMD ROCm Compute Profiler:** kernel-scoped VALU, MFMA and VMEM utilization labels. The cited 3.11.0 development page is marked as proposed future changes, so these entries are preview mappings, not a production compatibility guarantee.

Ratios are multiplied by 100; MHz is multiplied by 1,000,000 to obtain Hz. Identity mappings preserve the source unit. Cumulative PCIe byte counters are not treated as interval traffic: the normalizer requires an explicit `counter_delta`. NVLink aggregate-per-GPU fields remain per-GPU; L0-L17 fields retain a per-link `entity_id`. The AMD `FLOPs (Total)` display is retained as reference-only because it is expressed per normalization unit and the documentation warns about execution-mask semantics; it is not silently converted into absolute FLOPs.

The normalizer accepts a JSON wrapper with `source_id`, collector, system scope, sampling window, provenance and a `counters[]` list:

```bash
python3 scripts/normalize_hardware_counters.py --input raw-counters.json --output normalized-evidence.json
```

Unrecognized and reference-only fields are returned in `unmapped_counters`; they are not discarded or guessed. Per-link metrics keep their entity identity.

### Derived metrics

`scripts/derive_hardware_metrics.py` operates on a validated evidence object (or a record containing one) and writes a separate output file:

```bash
python3 scripts/derive_hardware_metrics.py --input normalized-evidence.json --output derived-evidence.json
```

It derives only when the required inputs are present and compatible:

| Derived metric | Formula / required inputs |
|---|---|
| `achieved_flops` | `compute_flop_count / sampling_window_seconds`; precision and sparsity are retained |
| `compute_peak_utilization_pct` | achieved FLOP/s divided by theoretical peak with matching precision, sparsity and scope |
| `dram_bandwidth_bytes_per_s` | (DRAM read bytes + DRAM write bytes) divided by the sampling window |
| `dram_bandwidth_utilization_pct` | measured DRAM bandwidth divided by matching peak bandwidth |
| `kv_cache_occupancy_pct` | KV bytes used / capacity, or token count / token capacity |
| `link_bandwidth_bytes_per_s` | (same-link TX bytes + RX bytes) divided by the sampling window |
| `link_utilization_pct` | measured link bandwidth divided by peak for the same link entity and fabric |

Out-of-range ratios are skipped with an explicit note, never clamped. Missing inputs remain missing. The script does not make a bottleneck classification or apply arbitrary utilization thresholds. These metrics are descriptive evidence; diagnosis still needs workload phase, precision, device SKU, topology, worker mapping and counter collection context.

Run the catalog validator and the two focused test suites:

```bash
python3 scripts/validate_hardware_counter_mappings.py
python3 -m unittest discover -s tests -p "test_hardware_counter_mappings.py"
python3 -m unittest discover -s tests -p "test_hardware_metric_derivation.py"
```

## What is needed before making a bottleneck claim

| Candidate bottleneck | Minimum evidence to investigate | Important caveats |
|---|---|---|
| Compute saturation | Achieved FLOP/s and comparable peak FLOP/s with matching precision, sparsity and scope, plus SM/Tensor activity | Utilization alone is not achieved compute; peak specs must match SKU, clock, precision and sparsity |
| HBM bandwidth | DRAM read/write traffic or measured bandwidth, plus a matching device/system peak bandwidth | Memory-used bytes and GPU utilization do not measure HBM bandwidth |
| KV-cache pressure | KV bytes or token occupancy and corresponding capacity, ideally with allocator/eviction/reuse evidence | Total GPU memory use is not KV-cache occupancy; cache hit rate requires a defined denominator |
| Communication | Directional bytes/rates or link utilization, link type, topology and matching link capacity | PCIe/NVLink/NIC aggregate traffic cannot be conflated; link counters may double-count both endpoints |
| Power / thermal | Validated power, GPU and memory clocks, temperature, and throttle state over the same window | Power alone does not prove throttling or a performance bottleneck |

These are evidence requirements, not an automatic decision tree. A system can be limited by several resources at once, and utilization values are not mutually exclusive.

## Current source limitations

The current InferenceX importer preserves its documented aggregate latency, throughput, utilization, memory-used, and power/energy fields. It does not currently synthesize low-level counters from those aggregates. hardware_evidence is optional and will remain absent unless a source provides a provenance-bearing block in this contract.

The Results Explorer should therefore report evidence coverage and missing categories, not label a record compute-bound or memory-bound. A future diagnostic should additionally account for precision, theoretical peak definition, device clocks, link topology, worker mapping, counter multiplexing, sampling loss, and measurement overhead.

## Validation

Run:

python3 scripts/validate_benchmark_results.py
python3 -m unittest discover -s tests -p "test_benchmark_results.py"

The validator checks structure, exact units, finite non-negative values, percentage bounds, unique metric tuples, timezone-aware sampling windows, provenance URLs, derived-metric inputs, and link-type metadata. It does not certify the counter's correctness or the publisher's methodology.
