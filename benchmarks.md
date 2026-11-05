---
layout: default
title: AI Accelerator Benchmarks
permalink: /benchmarks/
---

# AI Accelerator Benchmarks

> A curated map of benchmarks for AI chips and systems, from model training and LLM serving to kernels, memory, interconnect, power, and cost.

**Last reviewed: 2026-11-05** · A benchmark name alone is not a comparable result. Always preserve its workload, software stack, hardware configuration, measurement method, and source.

## 1. Benchmark taxonomy

| Category | What it measures | Typical questions |
|---|---|---|
| Training | Time-to-quality, throughput, scaling efficiency | How quickly can the system reach a target quality? |
| Offline / server inference | Throughput and latency under a defined request distribution | How many requests or tokens can be served under an SLO? |
| Interactive LLM serving | TTFT, TPOT, inter-token latency, goodput | How responsive is generation under concurrency? |
| Agentic / multi-turn inference | End-to-end task latency, tool cycles, long-context and cache behavior | Does the system sustain multi-step workloads? |
| Kernel / operator | Correctness, latency, throughput, memory traffic | How well are GEMM, attention, MoE and collectives implemented? |
| Memory / interconnect | Bandwidth, latency, collectives, all-to-all | Where does data movement limit scaling? |
| Edge / client | Task latency, accuracy, memory, energy | Can the device run the workload within power and memory limits? |
| Power / cost | Performance per watt, energy per token, cost per token, TCO | What does useful output cost at the system level? |

## 2. Training and standardized inference

### MLPerf / MLCommons

- [MLPerf benchmark suite](https://mlcommons.org/benchmarks/)
- [MLPerf results and policies](https://mlcommons.org/)
- [MLPerf results visualizer](https://mlcommons.org/benchmarks/)

MLPerf is the most widely recognized industry benchmark family for standardized AI system evaluation. Keep separate entries for:

| Suite | Focus | What to record |
|---|---|---|
| MLPerf Training | Time to train to a target quality | Model, dataset, quality target, system size, time, scaling configuration |
| MLPerf Inference | Offline, server, and other defined inference scenarios | Scenario, latency constraint, throughput, accuracy, system configuration |
| MLPerf Client / Mobile | On-device and client inference | Device, model, latency, accuracy, memory, energy |
| MLPerf Power | Energy associated with benchmark workloads | Power measurement boundary, average / peak power, energy and performance |
| MLPerf HPC | Scientific computing workloads | Application, precision, scaling and time-to-solution |

**Version policy:** Link to the current MLCommons benchmark pages and result rounds instead of hard-coding a version number in the taxonomy. Result rounds change; keep dated result links in a changelog or release-specific subsection.

## 3. LLM serving and inference economics

### SemiAnalysis InferenceX

- [InferenceX](https://inferencex.semianalysis.com/)
- [SemiAnalysis](https://semianalysis.com/)

InferenceX is an important reference for comparing deployed inference configurations. Capture the published metric definitions and workload details for each result rather than assuming every entry uses the same request mix.

Recommended fields:

| Metric | Definition / interpretation |
|---|---|
| TTFT | Time to first generated token; user-visible initial response latency |
| TPOT | Average time per output token after the first token; report exact measurement convention |
| Inter-token latency | Distribution of gaps between consecutive output tokens |
| Output throughput | Generated tokens per second, with aggregation boundary stated |
| Goodput | Requests or tokens meeting a specified latency / quality SLO |
| Cost per token | Cost under the benchmark's hardware, utilization, pricing, and amortization assumptions |
| Energy per token | Measured energy divided by generated tokens, with system boundary stated |

**Important:** compare only matching model versions, quantization, input/output lengths, concurrency, arrival pattern, SLO, and pricing assumptions. A high aggregate tokens/s result does not by itself mean better interactive latency or lower cost.

### Other LLM serving workloads and harnesses

| Project / resource | Role | Use |
|---|---|---|
| [MLPerf Inference](https://mlcommons.org/benchmarks/) | Standardized inference suite | Comparable results under published rules and scenarios. |
| [GenAI-Perf](https://github.com/triton-inference-server/perf_analyzer) | LLM / GenAI serving performance measurement within NVIDIA Triton tooling | Latency and throughput measurements for supported serving endpoints. |
| [vLLM benchmark tools](https://docs.vllm.ai/) | Serving-engine benchmark utilities | Reproducible request, throughput, and latency measurements; pin vLLM version and workload. |
| [SGLang benchmark tools](https://docs.sglang.ai/) | Serving-engine benchmark utilities | Evaluate engine-specific features and workloads; retain exact configuration. |
| [llmperf](https://github.com/ray-project/llmperf) | LLM API load / performance testing | Useful for request-level latency and throughput; results depend on client and server setup. |
| [NVIDIA GenAI-Perf](https://github.com/triton-inference-server/perf_analyzer) | LLM endpoint benchmarking | Includes request-level and token-level metrics; verify version and endpoint mode. |

### Agentic and multi-turn inference

Agentic workloads add tool calls, multiple model turns, variable context, retrieval, and external waiting time. Report both model-serving metrics and end-to-end task metrics.

Suggested workload dimensions:

- Number of turns and tool calls.
- Input/output token distribution per turn.
- Context growth and cache reuse.
- Prefill/decode disaggregation.
- Tool execution time separated from model time.
- Success / quality criteria and deadline.
- Per-task cost and end-to-end latency.

[InferenceX / AgentX](https://inferencex.semianalysis.com/) can be tracked where published methodology and result data are available. Do not treat an agentic benchmark as directly comparable to fixed-prompt decode throughput.

## 4. Kernel and operator benchmarks

| Project | Focus | What it evaluates | Notes |
|---|---|---|---|
| [KernelBench](https://github.com/ScalingIntelligence/KernelBench) | AI-generated GPU kernels | Correctness and speed of generated kernels against reference implementations | Useful for measuring code-generation capability; pin tasks, baseline, hardware, and evaluator. |
| [TritonBench](https://github.com/FlagOpen/FlagGems) | Triton / operator workloads | Operator correctness and performance across representative workloads | Check the exact benchmark harness and task set in the repository. |
| [Triton tutorials and testing](https://github.com/triton-lang/triton) | DSL and compiler regression | Backend correctness and performance behavior | Compiler test suite is not a standalone cross-vendor leaderboard. |
| [FlashInfer](https://github.com/flashinfer-ai/flashinfer) | LLM inference kernels | Attention, KV cache, GEMM, MoE and related primitives | Use its benchmark scripts for kernel-level comparisons; record GPU, CUDA, compiler and shape. |
| [CUTLASS profiler](https://github.com/NVIDIA/cutlass) | NVIDIA GEMM / convolution kernels | Kernel configurations and measured performance | NVIDIA-specific; not a vendor-neutral benchmark. |
| [Composable Kernel](https://github.com/ROCm/composable_kernel) | AMD kernels | Kernel implementation and performance | AMD-specific; compare with matched operation, shape and precision. |

**Benchmark design recommendations:**

1. Separate exact numerical correctness from performance.
2. Include multiple shapes, dtypes, layouts, sequence lengths, and batch sizes.
3. Report warm-up, repetitions, variance, and clock / power state.
4. Report absolute latency and throughput, not only speedup.
5. Include memory footprint and launch overhead where material.
6. Distinguish single-kernel microbenchmarks from end-to-end model performance.

Kernel-generation benchmarks are especially sensitive to evaluator leakage, compilation time, timeout policy, and whether the generated code is actually executed on the target device. Record these policies.

## 5. Memory, interconnect, and distributed communication

| Tool / benchmark | Target | What to measure |
|---|---|---|
| [STREAM](https://www.cs.virginia.edu/stream/) | Host memory bandwidth | Sustainable read / write / copy bandwidth; document CPU and NUMA configuration. |
| [NVIDIA bandwidthTest](https://github.com/NVIDIA/cuda-samples) | CUDA memory and transfer paths | Host-device and device-device copy bandwidth / latency. |
| [NCCL Tests](https://github.com/NVIDIA/nccl-tests) | NVIDIA GPU collectives | AllReduce, AllGather, ReduceScatter, Broadcast, and related operations. |
| [RCCL](https://github.com/ROCm/rccl) and its tests | AMD GPU collectives | Collective performance on ROCm systems. |
| [OSU Micro-Benchmarks](https://mvapich.cse.ohio-state.edu/benchmarks/) | MPI / network | Point-to-point latency and bandwidth, collectives, and GPU-aware communication where configured. |
| [Intel MPI Benchmarks](https://github.com/intel/mpi-benchmarks) | MPI communication | Point-to-point and collective communication. |
| [NVSHMEM](https://github.com/NVIDIA/nvshmem) | GPU-initiated communication | GPU-centric communication primitives and latency / throughput. |

For modern AI clusters, explicitly add:

- All-to-All and All-to-All-v for MoE expert parallelism.
- AllGather / ReduceScatter for tensor and sequence parallelism.
- GPU-to-GPU P2P bandwidth and latency.
- Intra-node versus inter-node measurements.
- RDMA / RoCE behavior and congestion.
- KV-cache transfer between prefill and decode workers.
- Scale-up fabric topology, bisection bandwidth, and failure behavior.

A collective result is meaningful only when message size, number of ranks, topology, algorithm, transport, and concurrency are stated. Do not compare a vendor's best-case single-node result with a multi-node production result.

## 6. Edge, mobile, and embedded AI

| Benchmark | Focus | Notes |
|---|---|---|
| [MLPerf Tiny](https://mlcommons.org/benchmarks/) | TinyML / microcontrollers | Accuracy, latency, and energy under constrained conditions. |
| [MLPerf Client](https://mlcommons.org/benchmarks/) | Client / on-device AI | Useful for laptop and client-class AI workloads. |
| [MLPerf Mobile](https://mlcommons.org/benchmarks/) | Mobile inference | Use current MLCommons suite and published rules. |
| [AI-Benchmark](https://ai-benchmark.com/) | Android / mobile AI | Community benchmark; record device, software, and test version. |
| [EEMBC MLMark](https://www.eembc.org/mlmark/) | Embedded ML | Embedded workload evaluation; check current availability and licensing. |

## 7. Power, energy, and cost

Power and cost numbers are not portable unless measurement boundaries and assumptions match.

| Metric | Recommended definition | Required disclosure |
|---|---|---|
| Performance / Watt | Useful throughput divided by measured power | Device-only or full-system boundary; average / peak; workload and utilization |
| Joules / token | Energy consumed divided by generated tokens | Include CPU, memory, networking, cooling or explicitly exclude them |
| Tokens / second / Watt | Output throughput divided by power | Model, input/output lengths, concurrency, and power boundary |
| Cost / million tokens | Total serving cost divided by output tokens | Hardware price, depreciation, utilization, power, networking, and operations |
| TCO | Total cost over a defined period | CapEx, OpEx, software, facility, utilization, and refresh assumptions |
| SLO goodput / Watt | SLO-compliant throughput divided by power | SLO definition and rejected / failed requests |

Useful references:

- [MLCommons Power](https://mlcommons.org/benchmarks/)
- [SPECpower](https://www.spec.org/power_ssj2008/)
- [The Green500](https://www.top500.org/green500/)
- [SemiAnalysis InferenceX](https://inferencex.semianalysis.com/)

## 8. Recommended result schema

Every result in this landscape should be stored with enough metadata to reproduce or interpret it.

| Field | Example / requirement |
|---|---|
| Benchmark | MLPerf Inference, InferenceX, KernelBench, NCCL Tests |
| Result date | YYYY-MM-DD |
| Hardware | Exact accelerator model, count, CPU, memory, fabric |
| Model / operator | Model version or operator name and shape |
| Workload | Dataset, input/output lengths, batch, concurrency, arrival pattern |
| Precision | BF16, FP8, FP4, INT8, etc. |
| Software stack | Driver, firmware, compiler, runtime, serving engine and versions |
| Parallelism | TP / PP / DP / EP / CP, rank topology |
| Metric | TTFT, TPOT, throughput, latency, energy, cost, accuracy |
| Value and unit | Numeric result, unit, aggregation method |
| Power boundary | Chip, server, rack, or facility |
| Evidence class | Independent, official standardized submission, vendor-reported, community |
| Source | Result page, paper, repository commit, or reproducible script |
| Reproducibility | Public config / script, environment, logs, or not available |

### Evidence classes

- **Independent:** third-party test with disclosed methodology and reproducible configuration.
- **Standardized submission:** result submitted under a benchmark organization's rules; identify the submitter.
- **Vendor-reported:** vendor test or announcement; keep separate from independent results.
- **Community / research:** paper, repository, or community run; inspect task set and evaluator.

## 9. Hardware coverage matrix

The following is a tracking template, not a statement that every benchmark currently supports every accelerator.

| Platform family | Training / inference | LLM serving | Kernel | Memory / interconnect | Edge |
|---|---|---|---|---|---|
| NVIDIA GPU | MLPerf and vendor / independent suites | InferenceX, vLLM, SGLang, TensorRT-LLM | CUDA, Triton, CUTLASS, FlashInfer | NCCL Tests, NVSHMEM | MLPerf Client / Mobile where applicable |
| AMD GPU | MLPerf submissions and ROCm workloads | vLLM / SGLang on supported configurations | Triton, Composable Kernel, AITER | RCCL tests | Device-specific |
| Intel GPU / Gaudi | MLPerf / vendor workloads where submitted | OpenVINO, vLLM or Gaudi-specific serving paths | oneAPI / vendor libraries | MPI / vendor communication tests | OpenVINO / client |
| Huawei Ascend | Vendor and community model tests | vLLM-Ascend, MindIE | CANN / Ascend kernel tests | HCCL / cluster tests | Ascend edge products |
| Cambricon MLU | Vendor / community tests | Neuware ecosystem | CNToolkit / MLU operators | Vendor collective tests | Edge MLU products |
| Hygon DCU | Vendor / community tests | DTK ecosystem | DTK operators | DCU communication tests | Device-specific |
| Biren GPU | Vendor / community tests | Verify per release | BIRENSUPA libraries | Verify public test availability | Device-specific |
| Iluvatar CoreX | Vendor / community tests | ixRT / IGIE and documented integrations | Vendor libraries | Verify per release | Device-specific |
| Enflame GCU | Vendor / community tests | TopsRider ecosystem | TopsAten / GCU operators | ECCL / system tests | Device-specific |

## 10. What this project should track first

To keep the benchmark section useful rather than an unmaintainable list, prioritize:

1. **MLPerf:** new rounds, system submissions, accuracy and power.
2. **InferenceX:** TTFT, TPOT, throughput, cost and agentic workload results; retain exact published methodology.
3. **KernelBench and related kernel-generation evaluations:** correctness, performance, evaluator policy, and hardware coverage.
4. **Triton / TileLang / FlashInfer kernel suites:** track compiler and kernel evolution on real hardware.
5. **NCCL / RCCL / HCCL / ECCL and network microbenchmarks:** especially All-to-All, AllReduce and KV movement.
6. **Power and cost:** only where system boundary and pricing assumptions are disclosed.

**Editorial rule:** do not create a single universal accelerator ranking from heterogeneous benchmarks. Present workload-specific comparisons with explicit configuration and evidence class.
