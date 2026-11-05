---
layout: default
title: AI Accelerator Software Ecosystem
permalink: /software-ecosystem/
---

# AI Accelerator Software Ecosystem

> A curated map of the software stack required to program, compile, execute, serve, and operate AI accelerators. This page is complementary to the [hardware and vendor landscape](/AI-Chip/).

**Last reviewed: 2026-11-05** · Links point to upstream projects or vendor-maintained documentation. Support status is workload-, device-, and release-specific; a project appearing here does not imply production support on every listed accelerator.

Explore the [interactive Compatibility Explorer](/AI-Chip/compatibility/) to filter platform × software integrations, version pins, support status and source evidence. The underlying [machine-readable dataset](/AI-Chip/data/compatibility.json) is maintained with a JSON Schema and automated validation.

## Release and license snapshot

The following is a dated snapshot of selected upstream releases checked on **2026-11-05**. It is not a compatibility guarantee; pin the exact device, framework, driver, and runtime versions before deployment.

| Project | Latest GitHub release checked | Release date | Repository-level license |
|---|---:|---:|---|
| [Triton](https://github.com/triton-lang/triton/releases/tag/v3.9.0) | v3.9.0 | 2026-10-27 | MIT |
| [TileLang](https://github.com/tile-ai/tilelang/releases/tag/v0.1.15) | v0.1.15 | 2026-09-30 | MIT; see historical collaboration note in LICENSE |
| [Apache TVM](https://github.com/apache/tvm/releases/tag/v0.27.0.post1) | v0.27.0.post1 | 2026-09-29 | Apache-2.0 |
| [Helion](https://github.com/pytorch/helion/releases/tag/v1.5.2) | v1.5.2 | 2026-11-01 | BSD-3-Clause |
| [FlashInfer](https://github.com/flashinfer-ai/flashinfer/releases/tag/v0.7.3) | v0.7.3 | 2026-11-04 | Apache-2.0 |
| [vLLM](https://github.com/vllm-project/vllm/releases/tag/v0.33.0rc3) | v0.33.0rc3 (release candidate) | 2026-11-02 | Apache-2.0 |
| [SGLang](https://github.com/sgl-project/sglang/releases/tag/v0.5.23) | v0.5.23 | 2026-11-02 | Apache-2.0 |
| [FlagGems](https://github.com/flagos-ai/FlagGems/releases/tag/v5.4.0) | v5.4.0 | 2026-09-28 | Apache-2.0 |
| [NVIDIA Dynamo](https://github.com/ai-dynamo/dynamo/releases/tag/v1.6.1) | v1.6.1 | 2026-10-27 | Apache-2.0 base; bundled test data has separate notices |
| [llm-d](https://github.com/llm-d/llm-d/releases/tag/v1.0.0) | v1.0.0 | 2026-10-20 | Apache-2.0 |
| [Mooncake](https://github.com/kvcache-ai/Mooncake/releases/tag/v0.3.14) | v0.3.14 | 2026-11-03 | Apache-2.0 |
| [NIXL](https://github.com/ai-dynamo/nixl/releases/tag/v1.5.2) | v1.5.2 | 2026-10-29 | Apache-2.0 base; bundled DeepEP example has a separate MIT notice |
| [llama.cpp](https://github.com/ggml-org/llama.cpp/releases/tag/v0.9.0) | v0.9.0 | 2026-11-04 | MIT |
| [AITer](https://github.com/ROCm/aiter/releases/tag/v0.1.27) | v0.1.27 | 2026-10-26 | MIT |
| [vLLM Ascend](https://github.com/vllm-project/vllm-ascend/releases/tag/v0.30.0) | v0.30.0 | 2026-10-29 | Apache-2.0 |
| [DeepSparkInference](https://github.com/Deep-Spark/DeepSparkInference/releases/tag/26.09) | 26.09 | 2026-09-22 | Apache-2.0 |
| [torch-gcu](https://github.com/EnflameTechnology/torch-gcu/releases/tag/v2.10.0) | v2.10.0 | 2026-08-07 | BSD-style 3-Clause terms |

**License caution:** repository metadata sometimes reports `NOASSERTION` even when a root LICENSE exists. The checked files show, for example, that TileLang's MIT license includes a dated collaboration-terms note for 2024-12-01 through 2025-03-14; TensorRT-LLM and NCCL include third-party license notices; Dynamo and NIXL identify separate licenses for some bundled test / example material. The Enflame `torch-gcu` and Ascend `pytorch` LICENSE files retain PyTorch-derived BSD 3-Clause terms. A repository-level label is not a substitute for reviewing individual files and dependencies before redistribution.

Projects without a tagged GitHub release at the audit date (including TritonBench and MLC-LLM) should be tracked by commit / tag rather than assigned an invented version.

## 1. How to read the software stack

| Layer | Main responsibility | Representative projects |
|---|---|---|
| Framework and graph capture | Model authoring, graph capture, graph-level transformations | PyTorch, JAX, TensorFlow, ONNX |
| Compiler and IR | Graph lowering, scheduling, code generation, target-specific optimization | MLIR, OpenXLA/XLA, TVM, IREE, TorchInductor |
| Kernel programming | Express tiled operations, memory movement, synchronization, and pipelines | Triton, TileLang, TIRx, CuTe DSL, Helion, Pallas, Mojo |
| Kernel and operator libraries | Hand-tuned primitives for GEMM, attention, MoE, collectives, quantization | CUTLASS, Composable Kernel, FlashAttention, FlashInfer, AITER, FlagGems |
| Runtime and inference engine | Load models, execute graphs, manage memory and batching | TensorRT-LLM, vLLM, SGLang, ONNX Runtime, OpenVINO, MLC-LLM, llama.cpp |
| Distributed serving and data movement | Scheduling, disaggregation, KV-cache movement, collectives, cluster integration | Dynamo, llm-d, Mooncake, NIXL, NCCL, RCCL |
| Vendor platform SDK | Driver, runtime, compiler, libraries, profiler, framework integration | CUDA, ROCm, Neuron, CANN, Neuware, DTK, BIRENSUPA, CoreX SDK, TopsRider |

These layers overlap in practice. For example, a serving engine may bundle kernels and runtime components, while a vendor SDK may provide its own compiler, operator libraries, and distributed communication stack.

## 2. Compiler, graph IR, and code generation

| Project | Layer / role | Hardware or ecosystem | Notes |
|---|---|---|---|
| [MLIR](https://mlir.llvm.org/) | Compiler infrastructure and extensible IR | Multi-target compiler infrastructure | Useful for representing and lowering computation across abstraction levels; not a ready-made AI accelerator backend by itself. |
| [OpenXLA / XLA](https://openxla.org/) | Graph compiler | TPU, GPU, CPU and framework integrations | Important in JAX and TensorFlow; also provides compiler infrastructure used by other projects. |
| [Apache TVM](https://tvm.apache.org/) | End-to-end compiler stack | Multiple CPU/GPU/accelerator targets | Includes graph and tensor IR infrastructure, scheduling, runtime, and the newer TIRx work. |
| [IREE](https://iree.dev/) | MLIR-based compiler and runtime | CPU, GPU, and selected accelerator backends | Focuses on deployable, end-to-end ML execution across devices. |
| [PyTorch TorchInductor](https://pytorch.org/docs/stable/torch.compiler.html) | PyTorch graph compiler | CUDA, CPU and supported backend integrations | The default compiler path behind `torch.compile`; backend coverage depends on the PyTorch release and device integration. |
| [Glow](https://github.com/pytorch/glow) | Historical graph compiler | Research / historical | Retain as background reading rather than a current default compiler recommendation. |

## 3. Kernel DSLs and low-level programming

This layer is strategically important: it defines the abstraction boundary between model developers, compiler optimization, and hardware-specific control.

| Project | Programming model | Why it matters | Status / caveat |
|---|---|---|---|
| [Triton](https://github.com/triton-lang/triton) | Python-based GPU kernel DSL | Widely used for custom GPU kernels; supports NVIDIA and AMD backends with architecture-dependent features. | Active upstream project. Check the release compatibility matrix before pinning PyTorch/Triton versions. |
| [TileLang](https://github.com/tile-ai/tilelang) | Tile-based kernel DSL and compiler | Makes tile layouts, memory scopes, pipelining, and hardware mapping more explicit than a purely high-level tensor API. | Multi-backend project. Its README distinguishes primary, supported, experimental, and ecosystem-adapter backends; do not treat them as equally mature. |
| [TIRx](https://tvm.apache.org/docs/tirx/overview.html) | Hardware-native kernel DSL and compiler built on TVM | Exposes pipeline structure, synchronization, role assignment, memory placement, and backend intrinsics for frontier kernels and agentic kernel programming. | An evolving low-level IR in the TVM ecosystem. TileLang's 2026 project notes record migration to TVM TIRx; treat TIRx as a compiler representation / programming substrate, not simply another standalone Python DSL. |
| [Helion](https://github.com/pytorch/helion) | PyTorch-oriented kernel authoring and tuning | Provides a higher-level way to author and tune kernels while targeting lower-level implementations. | Active research-to-engineering project; backend and feature coverage should be checked per release. |
| [CuTe / CUTLASS DSL](https://github.com/NVIDIA/cutlass) | Hardware-aware tiled programming | Exposes detailed control over layouts, data movement, and execution on NVIDIA GPUs. | NVIDIA-specific programming path; not a cross-vendor abstraction. |
| [JAX Pallas](https://docs.jax.dev/en/latest/pallas/index.html) | Kernel programming within JAX | Provides a lower-level kernel authoring model for GPU and TPU workloads. | Backend capabilities and semantics differ by target. |
| [Mojo](https://www.modular.com/mojo) | Systems and AI programming language | Aims to combine high-level productivity with low-level control. | Evolving language and toolchain; evaluate maturity and compatibility for each use case. |

**Recent direction:** TileLang v0.1.15 is the latest checked release. Its project notes document a native Ascend 950 backend and migration toward TVM TIRx. This makes TileLang relevant to multi-vendor kernel development, but individual backends still have different levels of maturity and should be tested independently.

## 4. Kernel and operator libraries

| Project | Main workload | Notes |
|---|---|---|
| [CUTLASS](https://github.com/NVIDIA/cutlass) | GEMM, convolution, tensor-core building blocks | Core NVIDIA library and foundation for multiple higher-level kernels. |
| [Composable Kernel](https://github.com/ROCm/composable_kernel) | AMD GPU GEMM and composable kernels | Important AMD kernel-library ecosystem. |
| [FlashAttention](https://github.com/Dao-AILab/flash-attention) | Memory-efficient attention | Algorithm and kernel family; hardware and architecture support varies by branch and release. |
| [FlashInfer](https://github.com/flashinfer-ai/flashinfer) | LLM serving kernels | Attention, KV-cache, GEMM, MoE, sampling, and communication-related kernels; used by multiple serving stacks. |
| [DeepGEMM](https://github.com/deepseek-ai/DeepGEMM) | Low-precision GEMM for MoE / LLM workloads | A useful reference for specialized GEMM and low-precision kernel engineering. |
| [AITer](https://github.com/ROCm/aiter) | AMD inference and training kernels | Optimized operator library within the ROCm ecosystem. |
| [oneDNN](https://github.com/uxlfoundation/oneDNN) | CPU and accelerator primitives | Cross-platform performance library with hardware-specific optimizations. |
| [Liger Kernel](https://github.com/linkedin/Liger-Kernel) | Fused LLM training kernels | PyTorch-oriented fused kernels intended to reduce memory use and improve training efficiency. |
| [FlagGems](https://github.com/flagos-ai/FlagGems) | Generic Triton operator library | FlagOS project with PyTorch ATen integration and a multi-backend kernel collection; its README reports more than ten backend integrations. Backend maturity is not uniform. |

## 5. Runtime and inference engines

| Project | Primary role | Hardware / integration notes |
|---|---|---|
| [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM) | Optimized LLM inference runtime | NVIDIA-oriented; integrates with CUDA, TensorRT, and NVIDIA networking / serving components. |
| [vLLM](https://github.com/vllm-project/vllm) | General-purpose LLM serving engine | Main project documents NVIDIA CUDA, AMD ROCm, Intel XPU, and CPU paths. Other accelerators use separately maintained hardware plugins. |
| [SGLang](https://github.com/sgl-project/sglang) | High-performance LLM and multimodal serving | Upstream README lists NVIDIA, AMD, Google TPU, Intel, Apple Silicon, Huawei Ascend, and Moore Threads; several other vendor integrations are explicitly marked in progress. |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) | Cross-framework inference runtime | Execution providers determine the actual hardware support and operator coverage. |
| [OpenVINO](https://github.com/openvinotoolkit/openvino) | Intel inference and deployment toolkit | CPU, GPU, and NPU deployment path in the Intel ecosystem. |
| [MLC-LLM](https://github.com/mlc-ai/mlc-llm) | Universal LLM deployment | Compiler-based deployment across supported GPU, mobile, and edge targets. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Lightweight local inference | Broad hardware backends; performance and operator coverage differ substantially by backend. |
| [LMDeploy](https://github.com/InternLM/lmdeploy) | LLM serving and compression | Includes TurboMind and PyTorch engine paths; verify model and accelerator compatibility by release. |

### Serving-engine support: important distinction

A hardware backend can be in one of several states:

- **Upstream supported:** documented and maintained in the main project.
- **Official plugin:** maintained in a separate repository under the project's hardware-plugin mechanism.
- **Vendor integration:** maintained by the hardware vendor or ecosystem partner.
- **In progress / experimental:** code exists or work is announced, but broad production support is not established.

For example, vLLM's main installation documentation distinguishes core GPU support from third-party hardware plugins. SGLang's current support table separately identifies supported hardware and integrations in progress. Always consult the live compatibility pages before claiming that a chip is supported.

### Hardware-plugin status: distinguish official from out-of-tree

vLLM explicitly supports out-of-tree platform plugins. Its current plugin-design documentation separates official device plugins from non-official / community plugins.

| vLLM plugin class | Public examples | Interpretation |
|---|---|---|
| Official device plugins | [vLLM Ascend](https://github.com/vllm-project/vllm-ascend), [vLLM Gaudi](https://github.com/vllm-project/vllm-gaudi), [vLLM Neuron](https://github.com/vllm-project/vllm-neuron), [vLLM Spyre](https://github.com/vllm-project/vllm-spyre), [vLLM Metal](https://github.com/vllm-project/vllm-metal) | Maintained / recognized in the upstream vLLM documentation; still version- and device-specific. |
| Non-official / community plugins | [vLLM-MUSA](https://github.com/MooreThreads/vllm-musa), [vLLM-MetaX](https://github.com/MetaX-MACA/vLLM-metax), [vLLM-Kunlun](https://github.com/baidu/vLLM-Kunlun), [vLLM-Iluvatar](https://github.com/Deep-Spark/vllm-iluvatar) | Separate projects; verify maintainer, supported vLLM range, device generation, model coverage, and test evidence. |

The Iluvatar plugin's current README specifies `vLLM >=0.27.1,<0.28.0`, CoreX runtime / driver `>=5.0.0`, CoreX PyTorch `>=2.10.0`, and ixformer `>=0.7.0`. Its repository's default branch is `release/v0.27.1`. This is evidence of a working plugin path, **not evidence of compatibility with the current vLLM 0.33.0rc3 release**.

### SGLang hardware status from its upstream README

SGLang's upstream README currently lists the following as supported representative platforms:

- NVIDIA GPUs; AMD Instinct MI300 / MI325 / MI350 families.
- Google TPU v6e / v7; Intel Arc / Arc Pro B-series GPUs and Xeon CPUs.
- Apple Silicon; Huawei Ascend A2 / A3 / 950PR / DT; Moore Threads MTT S5000.

It separately marks AWS Trainium, Alibaba T-Head PPU, Cambricon MLU, Qualcomm QAIC, MetaX, Hygon HCU / DCU, and Iluvatar CoreX as **integrations in progress**. These must not be placed in the same "supported" category until the upstream status changes and the relevant release / device matrix is published.

## 6. Distributed inference, KV cache, and communication

| Project | Main role | Why it matters |
|---|---|---|
| [NVIDIA Dynamo](https://github.com/ai-dynamo/dynamo) | Distributed inference serving framework | Coordinates disaggregated prefill/decode, KV-aware routing, cache management, and autoscaling; supports multiple inference engines. |
| [llm-d](https://github.com/llm-d/llm-d) | Kubernetes-native distributed LLM serving | Connects inference scheduling and serving to cloud-native orchestration. |
| [Mooncake](https://github.com/kvcache-ai/Mooncake) | KV-cache-centric serving and transfer infrastructure | Separates prefill and decode resources and pools KV cache across CPU memory, DRAM, SSD, and accelerator nodes. |
| [NIXL](https://github.com/ai-dynamo/nixl) | Inference data-transfer library | Provides a common interface for moving data among GPU memory, CPU memory, and storage/network tiers. |
| [NCCL](https://developer.nvidia.com/nccl) | NVIDIA collective communication | Essential for multi-GPU and multi-node training / inference. |
| [RCCL](https://github.com/ROCm/rccl) | AMD collective communication | AMD's collective communication library. |
| [MSCCL++](https://github.com/microsoft/mscclpp) | Programmable collective communication | Research and systems infrastructure for optimizing collective communication. |
| [OSU Micro-Benchmarks](https://mvapich.cse.ohio-state.edu/benchmarks/) | MPI and network microbenchmarks | Useful for isolating network latency and bandwidth from model execution. |

**System-level observation:** for MoE and long-context inference, communication and KV-cache movement can dominate end-to-end performance. A software comparison should therefore include collectives, All-to-All, prefill/decode disaggregation, cache transfer, and routing—not only compiler speed or isolated GEMM throughput.

## 7. Vendor software platforms

| Vendor | Platform | Public software entry points | Notes |
|---|---|---|---|
| NVIDIA | CUDA, TensorRT, TensorRT-LLM, NCCL | [CUDA](https://developer.nvidia.com/cuda-zone) · [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM) | Most mature integrated GPU software ecosystem in this list. |
| AMD | ROCm, HIP, RCCL, MIGraphX | [ROCm](https://rocm.docs.amd.com/) · [GitHub](https://github.com/ROCm) | Open software stack; feature maturity varies by GPU generation and library. |
| Intel | oneAPI, oneDNN, OpenVINO, Gaudi software | [oneAPI](https://www.intel.com/content/www/us/en/developer/tools/oneapi/overview.html) · [OpenVINO](https://github.com/openvinotoolkit/openvino) | Distinguish Gaudi HPU software from Intel GPU / CPU software paths. |
| AWS | Neuron SDK | [Neuron documentation](https://awsdocs-neuron.readthedocs-hosted.com/) | Compiler, runtime, profiling, and framework integration for Trainium / Inferentia. |
| Huawei | CANN, MindSpore, torch-npu | [CANN](https://www.hiascend.com/software/cann) · [torch-npu](https://github.com/Ascend/pytorch) | Ascend-specific compiler, runtime, operator, and framework stack. |
| Cambricon | Neuware, CNToolkit, torch_mlu | [Neuware](https://www.cambricon.com/) · [torch_mlu](https://github.com/Cambricon/torch_mlu) | Vendor SDK and PyTorch integration; check supported MLU generation and framework versions. |
| Hygon | DTK, torch-dcu | [Hygon](https://www.hygon.cn/) | DCU software stack; public compatibility depends on release and model. |
| Biren | BIRENSUPA | [Biren official site](https://www.birentech.com/) | Vendor describes BIRENSUPA as its software development platform. Publicly available third-party framework and operator coverage should be verified per product. |
| Iluvatar CoreX | 天数智算软件栈 / IXUCA SDK, ixRT, IGIE, DeepSparkInference | [ixRT](https://github.com/Deep-Spark/iluvatar-corex-ixrt) · [DeepSparkInference](https://github.com/Deep-Spark/DeepSparkInference) · [Developer portal](https://developer.iluvatar.com/) | Public examples include ixRT / IGIE and selected vLLM deployments; check the exact IXUCA SDK, CoreX runtime, and model matrix. |
| Enflame | TopsRider, TopsRuntime, TopsAten, ECCL, torch-gcu | [torch-gcu](https://github.com/EnflameTechnology/torch-gcu) | Public `torch-gcu` v2.10.0 pairs with PyTorch 2.10.0 / TopsRider 3.7.1 and lists S60 as its hardware target; do not generalize to all GCU products. |
| Moore Threads | MUSA | [MUSA](https://github.com/MooreThreads) | Vendor software stack for MTT GPUs; backend coverage varies across upstream projects. |
| MetaX | MACA, MXMACA | [MetaX](https://www.metax-tech.com/) | Vendor GPU software ecosystem; upstream integration should be checked by framework and release. |

## 8. China vendor software: public evidence and integration status

The following are useful concrete entry points rather than a claim that all frameworks are equally mature.

### Biren Technology — BIRENSUPA and AIModelMaster

Biren's official material identifies BIRENSUPA as its software platform and documents model adaptation on the BR166 family. In April 2026 it reported DeepSeek-V4 preview adaptation and inference validation on BR166; a separate official case describes SenseNova U1 adaptation using `br_pytorch`, BIRENSUPA, and the AIModelMaster full-stack GPU agent.

- [Biren official site](https://www.birentech.com/)
- [DeepSeek-V4 adaptation on BR166 — 2026-04-28](https://www.birentech.com/news/lo81mr3idb49bsdjf8hdd2bb/)
- [SenseNova U1 adaptation / AIModelMaster](https://www.birentech.com/news/otr0bf5evzdwwivrjt6h3322/)

These are vendor-reported model-adaptation examples. Public evidence for a maintained upstream vLLM or SGLang device plugin was not found in this review; record BIRENSUPA / `br_pytorch` support by exact SKU, SDK, model, and release instead of inferring upstream compatibility.

### Iluvatar CoreX — 天垓 / 智铠 / 彤央, IXUCA SDK, ixRT, IGIE

Iluvatar's official product pages list the TianGai training family (including TianGai 100 / 150 / 300), ZhiKai 100 inference product, and TongYang edge family. The official TianGai 150 page lists 64GB HBM and a 350W board power figure; treat these as vendor-published specifications.

- [Official product-series overview](https://www.iluvatar.com/serias)
- [TianGai 150 product page](https://www.iluvatar.com/productDetails?fullCode=cpjs-yj-xlxl-tg150)
- [Official developer portal](https://developer.iluvatar.com/)
- [ixRT open-source components](https://github.com/Deep-Spark/iluvatar-corex-ixrt)
- [DeepSparkInference model library](https://github.com/Deep-Spark/DeepSparkInference)

DeepSparkInference contains model deployment examples for vLLM, ixRT, and IGIE, with SDK versions recorded per model. The separate [vLLM-Iluvatar plugin](https://github.com/Deep-Spark/vllm-iluvatar) documents a vLLM 0.27.1 compatibility range; it should be considered a version-pinned out-of-tree plugin, not broad upstream support.

### Enflame — TopsRider and torch-gcu

- [torch-gcu source and documentation](https://github.com/EnflameTechnology/torch-gcu)
- [Chinese README](https://github.com/EnflameTechnology/torch-gcu/blob/main/README_zh.md)

The public README currently pairs torch-gcu 2.10.0 with PyTorch 2.10.0 and TopsRider 3.7.1. It lists CloudBlazer inference S60 as the supported hardware model and documents ATen operator dispatch, CPU fallback, `torch.compile` / Inductor, AMP, profiler, GCU Graph, ECCL collectives / P2P, LibTorch, and CUDA migration. The public repository does not establish vLLM or SGLang production support for the full Enflame product family.

## 9. Compatibility and maturity matrix

This is a navigation aid, not a certification matrix. "Upstream" means the project itself documents the path; "vendor / plugin" means a separate vendor-maintained integration; "verify" means public evidence is not sufficient to make a broad claim.

| Platform | Compiler / SDK | Serving ecosystem | Public status to record |
|---|---|---|---|
| NVIDIA GPU | CUDA, Triton, TileLang, CuTe, TensorRT | vLLM, SGLang, TensorRT-LLM, MLC-LLM | Broad upstream and vendor support; still version / architecture dependent. |
| AMD GPU | ROCm, HIP, Triton, TileLang, Composable Kernel | vLLM, SGLang | Upstream support; feature coverage varies by architecture and ROCm release. |
| Intel GPU | oneAPI / XPU stack, OpenVINO | vLLM, SGLang | Upstream or vendor-supported paths; confirm device generation and feature coverage. |
| Huawei Ascend | CANN, torch-npu, TileLang Ascend backend | vLLM-Ascend; SGLang supported | Public plugin / upstream paths exist; check the exact CANN, PyTorch, vLLM, model, and Ascend generation matrix. |
| Moore Threads | MUSA | vLLM-MUSA community plugin; SGLang supported for MTT S5000 | Separate plugin and upstream support; validate exact MUSA / vLLM / SGLang versions. |
| Hygon DCU / HCU | DTK | SGLang integration in progress | Do not label as generally supported; verify vendor plugin and release evidence before use. |
| Cambricon MLU | Neuware, CNToolkit, torch_mlu | SGLang integration in progress | Track model / device-specific vendor integration; do not infer upstream production support. |
| MetaX GPU | MACA / MXMACA | vLLM-MetaX community plugin; SGLang integration in progress | Separate plugin exists; SGLang README still marks its integration in progress. |
| Iluvatar CoreX | IXUCA SDK, CoreX runtime, ixRT, IGIE | DeepSparkInference examples; vLLM-Iluvatar out-of-tree plugin; SGLang integration in progress | The public vLLM plugin specifies vLLM 0.27.1 only; compatibility with vLLM 0.33.0rc3 is not established. |
| Enflame GCU | TopsRider 3.7.1, torch-gcu 2.10.0 | No current upstream vLLM / SGLang support verified | Public torch-gcu README lists PyTorch 2.10.0 and S60; do not extrapolate to other GCU models. |
| Biren GPU | BIRENSUPA, br_pytorch, AIModelMaster | Vendor model-adaptation examples; no upstream plugin verified | Official BR166 DeepSeek-V4 and SenseNova U1 examples are vendor-reported; record exact software and SKU. |

## 10. Machine-readable compatibility database

The curated compatibility matrix is also maintained as structured data:

- [Compatibility database (JSON)](https://github.com/basicmi/AI-Chip/blob/master/data/compatibility.json)
- [JSON Schema](https://github.com/basicmi/AI-Chip/blob/master/schemas/compatibility.schema.json)
- [Validation script](https://github.com/basicmi/AI-Chip/blob/master/scripts/validate_compatibility.py)
- [Dataset contribution guide](https://github.com/basicmi/AI-Chip/blob/master/data/README.md)

The dataset separates platform records from integration records. Each integration is scoped to a project, platform, software layer, version range, support status, and dated evidence. The status is intentionally more precise than a binary supported / unsupported flag.

To validate locally, run:

```bash
python3 scripts/validate_compatibility.py
```

The script uses only the Python standard library. It checks JSON structure, unique identifiers, platform references, controlled vocabularies, dates, URLs, and evidence records. It does not automatically certify technical claims.

## 11. How to maintain this page

For every project, record:

1. **Upstream URL** — canonical source code or official documentation.
2. **Last checked** — date the repository, release, or compatibility page was reviewed.
3. **License** — use the repository's current LICENSE file; do not infer from a project name.
4. **Supported hardware** — exact device generation and backend, not just vendor name.
5. **Framework / runtime versions** — PyTorch, CUDA / ROCm / CANN / SDK versions where applicable.
6. **Maturity** — upstream supported, official plugin, vendor-maintained, community, experimental, or archived.
7. **Evidence** — official docs, tagged release, CI, benchmark result, or production case study.

**Rule:** A project listing is not proof of production readiness. Record the exact supported version and device, and distinguish "code exists", "CI tested", "vendor validated", and "deployed in production".
