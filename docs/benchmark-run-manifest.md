# Benchmark run manifest template

Copy this file for each local or hosted benchmark run. Replace every placeholder before execution and archive the final manifest with logs and raw measurements.

## Identity
- Run ID:
- Suite ID:
- Workload ID:
- Date/time (UTC):
- Operator:
- Source / recipe URL:
- Recipe commit:

## Hardware
- Accelerator model and SKU:
- Device count:
- Host CPU / NUMA:
- Host RAM:
- Accelerator memory:
- Interconnect:
- Power limit / clocks:
- Cooling / thermal conditions:

## Software
- OS / kernel:
- Driver:
- Runtime:
- Framework:
- Serving engine / compiler:
- Kernel library:
- Container image digest:

## Model and workload
- Model name and exact revision:
- Dataset / prompt set and revision:
- Precision / quantization:
- Input and output token distributions:
- Batch size / concurrency:
- Arrival pattern (open-loop / closed-loop):
- Parallelism (TP / PP / DP / EP):
- KV-cache / prefix-cache policy:
- Scheduler / speculative decoding settings:

## Measurement protocol
- Warm-up iterations:
- Measurement iterations / duration:
- Synchronization and timing boundary:
- Percentiles:
- Correctness / quality criteria:
- Power measurement boundary:
- Cost assumptions:

## Results
| Metric | Value | Unit | Percentile / aggregation | Raw artifact |
|---|---:|---|---|---|
| TTFT | | ms | P50 / P95 / P99 | |
| TPOT / ITL | | ms | P50 / P95 / P99 | |
| Output throughput | | tokens/s | system aggregate | |
| Goodput | | requests/s | stated SLO | |
| Peak accelerator memory | | GiB | max | |
| Average system power | | W | stated boundary | |

## Provenance and reproduction
- Evidence class: vendor_reported / upstream_ci / independently_reproduced
- Public run URL:
- Raw logs / artifacts URL:
- Reproduction status:
- Deviations from upstream recipe:
- Known limitations:
