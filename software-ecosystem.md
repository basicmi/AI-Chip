---
layout: default
title: AI Accelerator Software Ecosystem
permalink: /software-ecosystem/
---

# AI Accelerator Software Ecosystem

> A curated map of the software stack required to program, compile, execute, serve, and operate AI accelerators. This page is complementary to the [hardware and vendor landscape](/AI-Chip/).

**Last reviewed: 2026-11-05** · Links point to upstream projects or vendor-maintained documentation. Support status is workload-, device-, and release-specific; a project appearing here does not imply production support on every listed accelerator.

## 1. How to read the software stack

| Layer | Main responsibility | Representative projects |
|---|---|---|
| Framework and graph capture | Model authoring, graph capture, graph-level transformations | PyTorch, JAX, TensorFlow, ONNX |
| Compiler and IR | Graph lowering, scheduling, code generation, target-specific optimization | MLIR, OpenXLA/XLA, TVM, IREE, TorchInductor |
| Kernel programming | Express tiled operations, memory movement, synchronization, and pipelines | Triton, TileLang, TIRx, CuTe DSL, Helion, Pallas, Mojo |
| Kernel and operator libraries | Hand-tuned primitives for GEMM, attention, MoE, collectives, quantization | CUTLASS, Composable Kernel, FlashAttention, FlashInfer, AITER |
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
| [TIRx](https://tvm.apache.org/docs/tirx/overview.html) | Hardware-native kernel DSL and compiler built on TVM | Exposes pipeline structure, synchronization, role assignment, memory placement, and backend intrinsics for frontier kernels and agentic kernel programming. | Introduced by the Apache TVM community in June 2026; evolving compiler foundation, not a drop-in replacement for every existing DSL. |
| [Helion](https://github.com/pytorch/helion) | PyTorch-oriented kernel authoring and tuning | Provides a higher-level way to author and tune kernels while targeting lower-level implementations. | Active research-to-engineering project; backend and feature coverage should be checked per release. |
| [CuTe / CUTLASS DSL](https://github.com/NVIDIA/cutlass) | Hardware-aware tiled programming | Exposes detailed control over layouts, data movement, and execution on NVIDIA GPUs. | NVIDIA-specific programming path; not a cross-vendor abstraction. |
| [JAX Pallas](https://docs.jax.dev/en/latest/pallas/index.html) | Kernel programming within JAX | Provides a lower-level kernel authoring model for GPU and TPU workloads. | Backend capabilities and semantics differ by target. |
| [Mojo](https://www.modular.com/mojo) | Systems and AI programming language | Aims to combine high-level productivity with low-level control. | Evolving language and toolchain; evaluate maturity and compatibility for each use case. |

**Recent direction:** TileLang's repository documents a modular multi-backend architecture, including CUDA, HIP, Ascend, Metal, and experimental LLVM CPU / CuTe DSL paths. TIRx takes a more hardware-native approach, deliberately exposing low-level orchestration and compiler IR for expert- and agent-written kernels. These are complementary design points, not simply competing versions of Triton.

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
| Iluvatar CoreX | CoreX SDK, ixRT, IGIE, DeepSpark | [ixRT source](https://github.com/Deep-Spark/iluvatar-corex-ixrt) · [DeepSpark](https://github.com/Deep-Spark/DeepSpark) | Public OSS components include ixRT plugins, deployment tools, examples, and model-inference projects. |
| Enflame | TopsRider, TopsRuntime, TopsAten, ECCL, torch-gcu | [torch-gcu](https://github.com/EnflameTechnology/torch-gcu) | Public PyTorch extension documents `torch.compile`, AMP, profiler, GCU Graph, ECCL, and CUDA migration helpers; current README lists S60 hardware support. |
| Moore Threads | MUSA | [MUSA](https://github.com/MooreThreads) | Vendor software stack for MTT GPUs; backend coverage varies across upstream projects. |
| MetaX | MACA, MXMACA | [MetaX](https://www.metax-tech.com/) | Vendor GPU software ecosystem; upstream integration should be checked by framework and release. |

## 8. China vendor software: public evidence and integration status

The following are useful concrete entry points rather than a claim that all frameworks are equally mature.

### Biren Technology — BIRENSUPA

Biren's official site identifies BIRENSUPA as its proprietary software development platform and describes software/hardware co-optimization. The company also highlights GPU-to-OCS optical interconnect work. Publicly visible software artifacts and third-party framework support are less transparent than CUDA / ROCm; the landscape should therefore link to vendor documentation and avoid inferring broad upstream compatibility.

- [Biren official platform and products](https://www.birentech.com/)
- [Biren optical-interconnect / LightSphere X announcement](https://www.birentech.com/news/uk3x1bhhagcrtf5bqkurbnsa/)

### Iluvatar CoreX — CoreX SDK, ixRT, IGIE, DeepSpark

- [Official software-stack overview](https://www.iluvatar.com/software?fullCode=cpjs-rj-rjz)
- [ixRT open-source components](https://github.com/Deep-Spark/iluvatar-corex-ixrt)
- [DeepSparkInference](https://github.com/Deep-Spark/DeepSparkInference)
- [DeepSpark open-source ecosystem](https://github.com/Deep-Spark/DeepSpark)

The public DeepSpark materials distinguish ixRT (Iluvatar's inference runtime) from IGIE (an inference engine based on TVM). DeepSparkInference includes examples using ixRT / IGIE and mainstream inference engines such as vLLM. This is a useful basis for tracking actual model coverage, not just SDK naming.

### Enflame — TopsRider and torch-gcu

- [torch-gcu source and documentation](https://github.com/EnflameTechnology/torch-gcu)
- [Chinese README](https://github.com/EnflameTechnology/torch-gcu/blob/main/README_zh.md)

The public repository documents dependencies on TopsRider, TopsRuntime, TopsAten, and ECCL. It also documents PyTorch integration, `torch.compile`, AMP, profiling, GCU Graph, LibTorch, and CUDA-code migration. Its current public hardware-support table names the S60 inference product; do not extrapolate this exact open-source support table to every Enflame card or system.

## 9. Compatibility and maturity matrix

This is a navigation aid, not a certification matrix. "Upstream" means the project itself documents the path; "vendor / plugin" means a separate vendor-maintained integration; "verify" means public evidence is not sufficient to make a broad claim.

| Platform | Compiler / SDK | Serving ecosystem | Public status to record |
|---|---|---|---|
| NVIDIA GPU | CUDA, Triton, TileLang, CuTe, TensorRT | vLLM, SGLang, TensorRT-LLM, MLC-LLM | Broad upstream and vendor support; still version / architecture dependent. |
| AMD GPU | ROCm, HIP, Triton, TileLang, Composable Kernel | vLLM, SGLang | Upstream support; feature coverage varies by architecture and ROCm release. |
| Intel GPU | oneAPI / XPU stack, OpenVINO | vLLM, SGLang | Upstream or vendor-supported paths; confirm device generation and feature coverage. |
| Huawei Ascend | CANN, torch-npu, TileLang Ascend backend | vLLM-Ascend, SGLang | Vendor and upstream/plugin integrations; verify model, kernel, and device-generation coverage. |
| Moore Threads | MUSA | SGLang; selected kernel-generation ecosystem | Vendor integration and selected upstream projects; verify release compatibility. |
| Hygon DCU | DTK | Selected vLLM / SGLang integrations | Vendor and community integrations; verify exact branch and feature status. |
| Iluvatar CoreX | CoreX SDK, ixRT, IGIE | DeepSparkInference; selected vLLM examples | Vendor ecosystem and selected open-source projects; not equivalent to full upstream vLLM support. |
| Enflame GCU | TopsRider, torch-gcu | Vendor examples and selected serving integrations | Public torch-gcu currently documents S60; verify other devices and engines separately. |
| Biren GPU | BIRENSUPA | Verify by product and framework | Vendor platform is publicly described; avoid asserting upstream vLLM / SGLang support without a maintained backend and tested release. |

## 10. How to maintain this page

For every project, record:

1. **Upstream URL** — canonical source code or official documentation.
2. **Last checked** — date the repository, release, or compatibility page was reviewed.
3. **License** — use the repository's current LICENSE file; do not infer from a project name.
4. **Supported hardware** — exact device generation and backend, not just vendor name.
5. **Framework / runtime versions** — PyTorch, CUDA / ROCm / CANN / SDK versions where applicable.
6. **Maturity** — upstream supported, official plugin, vendor-maintained, community, experimental, or archived.
7. **Evidence** — official docs, tagged release, CI, benchmark result, or production case study.

**Rule:** A project listing is not proof of production readiness. Record the exact supported version and device, and distinguish "code exists", "CI tested", "vendor validated", and "deployed in production".
