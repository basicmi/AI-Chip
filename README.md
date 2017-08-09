## Nvidia
### GPU
- [Nvidia's latest GPU](https://www.nvidia.com/en-us/data-center/tesla-v100/) can do 15 TFlops of SP or 120 TFlops with its new Tensor core architecture which is a FP16 multiply and FP32 accumulate or add to suit ML.
- Nvidia is packing up 8 boards into their [DGX-1](https://www.nvidia.com/en-us/data-center/dgx-server/)for 960 Tensor TFlops.
- [Nvidia Volta - 架构看点](https://mp.weixin.qq.com/s/tEX4H7OEbZF4dKMI0ZOPmw) gives some insights of Volta architecture.

### SoC

### Open Source DLA from Nvidia

## AMD
### GPU
- The soon to be released [AMD Radeon Instinct MI25](https://instinct.radeon.com/en-us/product/mi/radeon-instinct-mi25/) is promising 12.3 TFlops of SP or 24.6 TFlops of FP16. If your calculations are amenable to Nvidia's Tensors, then AMD can't compete. Nvidia also does twice the bandwidth with 900GB/s versus AMD's 484 GB/s.

## Intel
### CPU

### FPGA

## Xilinx

## Google TPU
- Google's original [TPU](https://www.nextplatform.com/2017/04/05/first-depth-look-googles-tpu-architecture/) had a big lead over GPUs and helped power DeepMind's AlphaGo victory over Lee Sedol in a Go tournament. The original 700MHz TPU is described as having 95 TFlops for 8-bit calculations or 23 TFlops for 16-bit whilst drawing only 40W. This was much faster than GPUs on release but is now slower than Nvidia's V100, but not on a per W basis. The new [TPU2](https://www.nextplatform.com/2017/05/22/hood-googles-tpu2-machine-learning-clusters/) is referred to as a TPU device with four chips and can do around 180 TFlops. Each chip's performance has been doubled to 45 TFlops for 16-bits. You can see the gap to Nvidia's V100 is closing. You can't buy a TPU or TPU2. Google is making them available for use in their [cloud](https://www.blog.google/topics/google-cloud/google-cloud-offer-tpus-machine-learning/) with TPU pods containing 64 devices for up to 11.5 PetaFlops of performance. The giant heatsinks on the TPU2 are some cause for speculation, but the market is changing from devices to units with groups of devices and also such groups within the cloud.

Other references are:

- [Google TPU 揭密](https://mp.weixin.qq.com/s/Kf_L4u7JRxJ8kF3Pi8M5iw)

- [Google的神经网络处理器专利](https://mp.weixin.qq.com/s/lBQyNSNa6-joeLZ_Kq2W8A)

- [脉动阵列 - 因Google TPU获得新生](https://mp.weixin.qq.com/s/g-BDlvSy-cx4AKItcWF7jQ)

## Qualcomm

## Apple

## ARM

## IBM TrueNorth

## HiSilicon(华为海思）

## Cambricon（寒武纪）

## Horizon Robotics（地平线机器人）

## Deephi（深鉴科技）

## Bitmain（比特大陆）

## IntelliFusion（云天励飞）

## Wave Computing
Wave’s Compute Appliance is capable to run TensorFlow at 2.9 PetaOPS/sec on their 3RU appliance. Wave refers to their processors at DPUs and an appliance has 16 DPUs. Wave uses processing elements it calls Coarse Grained Reconfigurable Arrays (CGRAs). It is unclear what bit width the 2.9 PetaOPS/s is referring to. From their [white paper](http://wavecomp.ai/technology/), the ALUs can do 1b, 8b, 16b and 32b,  

>"The arithmetic units are partitioned. They can perform 8-b operations in parallel (ideal for DNN inferencing) as well as 16-b and 32-b operations (or any combination of the above). Some 64-b operations are also available and these can be extended to arbitrary precision using software." 

Here is a bit more on one of the 16 DPUs included in the appliance,

>"The Wave Computing DPU is an SoC that contains a 16,384 PEs, configured as a CGRA of 32x32 clusters. It includes four Hybrid Memory Cube (HMC) Gen 2 interfaces, two DDR4 interfaces, a PCIe Gen3 16-lane interface and an embedded 32-b RISC microcontroller for SoC resource management. The Wave DPU is designed to execute autonomously without a host CPU."

On TensorFlow ops, 

>"The Wave DNN Library team creates pre-compiled, relocatable kernels for common DNN functions used by workflows like TensorFlow. These can be assembled into Agents and instantiated into the machine to form a large data flow graph of tensors and DNN kernels."
"...a session manager that interfaces with machine learning workflows like TensorFlow, CNTK, Caffe and MXNet as a worker process for both training and inferencing. These workflows provide data flow graphs of tensors to worker processes. At runtime, the Wave session manager analyzes data flow graphs and places the software agents into DPU chips and connects them together to form the data flow graphs. The software agents are assigned regions of global memory for input buffers and local storage. The static nature of the CGRA kernels and distributed memory architecture enables a performance model to accurately estimate agent latency. The session manager uses the performance model to insert FIFO buffers between the agents to facilitate the overlap of communication and computation in the DPUs. The variable agents support software pipelining of data flowing through the graph to further increase the concurrency and performance. The session manager monitors the performance of the data flow graph at runtime (by monitoring stalls, buffer underflow and/or overflow) and dynamically tunes the sizes of the FIFO buffers to maximize throughput. A distributed runtime management system in DPU-attached processors mounts and unmounts sections of the data flow graph at run time to balance computation and memory usage. This type of runtime reconfiguration of a data flow graph in a data flow computer is the first of its kind."

Some more details can be fund in [AI芯片\|浅析Yann LeCun提到的两款Dataflow Chip](https://zhuanlan.zhihu.com/p/26594188)

## Graphcore

## KnuEdge's KnuPath

## PEZY Computing K.K.

## KnuEdge's KnuPath

## Tenstorrent

## Cerebras

## Thinci

## Koniku

## Adapteva

## Knowm

## Mythic

## Kalray

## Groq

## Aimotive

## Deep Vision

## Deep Scale

## REM

## Leepmind

## KAIST DNPU

## MIT A Scalable Speech Recognizer

## Synopsys Embedded Vision

## CEVA XM6

## VeriSilicon VIP8000

## Cadence P5/P6/C5

### Reference
1. [FPGAs and AI processors: DNN and CNN for all](https://meanderful.blogspot.jp/2017/06/fpgas-and-ai-processors-dnn-and-cnn-for.html)

