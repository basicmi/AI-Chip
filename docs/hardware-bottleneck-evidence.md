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

link_type is required for generic link_* and network_* metrics (nvlink, pcie, infiniband, roce, ethernet, or other). A per-link counter must not be compared with a per-GPU or per-system rate without an explicit aggregation procedure.

## Measurement and normalization rules

1. Units are canonical. The validator enforces the unit for each metric ID. Convert source units only in a documented transformation and preserve the exact source field name.
2. Scope is mandatory. Per-GPU, per-link, per-node, per-system, and per-process are different measurement boundaries. Never silently multiply a per-GPU value into a system total.
3. Aggregation is mandatory. Instantaneous, mean, max, percentiles, sum, and rate are not interchangeable. Byte counters require a measurement window before a rate is derived.
4. Sampling is mandatory. Record a timezone-aware measurement interval, sample cadence, and sample count. Do not compare measurements from materially different windows as if they were simultaneous.
5. Raw vs derived is explicit. hardware_counter and telemetry entries carry the collector's source name. A derived entry must include a formula and references to inputs present in the same evidence bundle.
6. Percentages are bounded. Percent-valued metrics must be in [0, 100]. Do not treat a percentage as a ratio unless the transformation is explicit.
7. Provenance is required. Every evidence bundle links to a source artifact or publisher record. An optional SHA-256 digest pins the exported artifact; it does not prove that the measurement is correct.
8. No evidence is not zero. An absent counter means unavailable/unknown, not zero activity, zero traffic, or an idle device.

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
