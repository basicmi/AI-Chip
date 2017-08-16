## Nvidia
### GPU
- [Nvidia's latest GPU](https://www.nvidia.com/en-us/data-center/tesla-v100/) can do 15 TFlops of SP or 120 TFlops with its new Tensor core architecture which is a FP16 multiply and FP32 accumulate or add to suit ML.
- Nvidia is packing up 8 boards into their [DGX-1](https://www.nvidia.com/en-us/data-center/dgx-server/)for 960 Tensor TFlops.
- [Nvidia Volta - 架构看点](https://mp.weixin.qq.com/s/tEX4H7OEbZF4dKMI0ZOPmw) gives some insights of Volta architecture.

### SoC
- On edge, Nvidia provide NVIDIA DRIVE™ PX, [The AI Car Computer for Autonomous Driving](http://www.nvidia.com/object/drive-px.html) and JETSON TX1/TX2 MODULE "[The embedded platform for autonomous everything](http://www.nvidia.com/object/embedded-systems-dev-kits-modules.html)"

### Open Source DLA from Nvidia
- Nvidia anouced "XAVIER DLA NOW OPEN SOURCE" on GTC2017. We did not see Early Access verion yet. Hopefully, the general release will be avaliable on Sep. as promised. For more analysis, you may want to read [从Nvidia开源深度学习加速器说起](http://mp.weixin.qq.com/s/XEb5xNeSV_oPs08kDgQg8Q).

## AMD
### GPU
- The soon to be released [AMD Radeon Instinct MI25](https://instinct.radeon.com/en-us/product/mi/radeon-instinct-mi25/) is promising 12.3 TFlops of SP or 24.6 TFlops of FP16. If your calculations are amenable to Nvidia's Tensors, then AMD can't compete. Nvidia also does twice the bandwidth with 900GB/s versus AMD's 484 GB/s.

## Intel
### Nervana
- Intel purchased Nervana Systems who was developing both a GPU/software approach in addition to their Nervana Engine ASIC. Comparable performance is unclear. Intel is also planning in integrating into the Phi platform via a [Knights Crest](https://www.nextplatform.com/2016/11/22/inside-intels-strategy-integrate-nervana-deep-learning-assets/) project. [NextPlatform](https://www.nextplatform.com/2016/08/08/deep-learning-chip-upstart-set-take-gpus-task/) suggested the 2017 target on 28nm may be 55 TOPS/s for some width of OP. There is a NervanaCon Intel has scheduled for December, so perhaps we'll see the first fruits then.

### Mobileye EyeQ
> Mobileye is currently developing its fifth generation SoC, the [EyeQ®5](https://www.mobileye.com/our-technology/evolution-eyeq-chip/), to act as the vision central computer performing sensor fusion for Fully Autonomous Driving (Level 5) vehicles that will hit the road in 2020. To meet power consumption and performance targets, EyeQ® SoCs are designed in most advanced VLSI process technology nodes – down to 7nm FinFET in the 5th generation. 

### Movidius
- [Movidius VPU](https://www.movidius.com/technology) is basicly an array of vector processor.

### FPGA
- Intel [FPGA OpenCL](https://www.altera.com/products/design-software/embedded-software-developers/opencl/overview.html) and [Solutions](https://www.altera.com/solutions/technology/artificial-intelligence/solutions.html).

## Google TPU
- Google's original [TPU](https://www.nextplatform.com/2017/04/05/first-depth-look-googles-tpu-architecture/) had a big lead over GPUs and helped power DeepMind's AlphaGo victory over Lee Sedol in a Go tournament. The original 700MHz TPU is described as having 95 TFlops for 8-bit calculations or 23 TFlops for 16-bit whilst drawing only 40W. This was much faster than GPUs on release but is now slower than Nvidia's V100, but not on a per W basis. The new [TPU2](https://www.nextplatform.com/2017/05/22/hood-googles-tpu2-machine-learning-clusters/) is referred to as a TPU device with four chips and can do around 180 TFlops. Each chip's performance has been doubled to 45 TFlops for 16-bits. You can see the gap to Nvidia's V100 is closing. You can't buy a TPU or TPU2. Google is making them available for use in their [cloud](https://www.blog.google/topics/google-cloud/google-cloud-offer-tpus-machine-learning/) with TPU pods containing 64 devices for up to 11.5 PetaFlops of performance. 

Other references are:

- [Google TPU 揭密](https://mp.weixin.qq.com/s/Kf_L4u7JRxJ8kF3Pi8M5iw)

- [Google的神经网络处理器专利](https://mp.weixin.qq.com/s/lBQyNSNa6-joeLZ_Kq2W8A)

- [脉动阵列 - 因Google TPU获得新生](https://mp.weixin.qq.com/s/g-BDlvSy-cx4AKItcWF7jQ)

## Xilinx
Xilinx provide "[Machine Learning Inference Solutions from Edge to Cloud](https://www.xilinx.com/applications/megatrends/machine-learning.html)" and naturally claim their FPGA's are best for INT8 with one of their [white papers](https://www.xilinx.com/support/documentation/white_papers/wp486-deep-learning-int8.pdf).
> Whilst performance per Watt is impressive for FPGAs, the vendors' larger chips have long had earth shatteringly high chip prices for the larger chips. Finding a balance between price and capability is the main challenge with the FPGAs.

## Microsoft FPGA
- Microsoft has thrown its hat into the FPGA ring, "[Microsoft Goes All in for FPGAs to Build Out AI Cloud](https://www.top500.org/news/microsoft-goes-all-in-for-fpgas-to-build-out-cloud-based-ai/)." 
- Wired did a nice story on the MSFT use of FPGAs too, "[Microsoft Bets Its Future on a Reprogrammable Computer Chip](https://www.wired.com/2016/09/microsoft-bets-future-chip-reprogram-fly/)"
- [Inside the Microsoft FPGA-based configurable cloud](https://channel9.msdn.com/Events/Build/2017/B8063) is also a good reference if want to know Microsoft's vision on FPGA in cloud.

## Qualcomm
> Qualcomm has been fussing around ML for a while with the Zeroth SDK and [Snapdragon Neural Processing Engine](https://developer.qualcomm.com/software/snapdragon-neural-processing-engine). The NPE certainly works reasonably well on the [Hexagon DSP](https://en.wikipedia.org/wiki/Qualcomm_Hexagon) that Qualcomm use. 
> The [Hexagon DSP](https://www.bdti.com/InsideDSP/2015/09/30/Qualcomm) is far from a very wide parallel platform and it has been confirmed by Yann LeCun that Qualcomm and Facebook are working together on a better way in Wired's "[The Race To Build An AI Chip For Everything Just Got Real](https://www.wired.com/2017/04/race-make-ai-chips-everything-heating-fast/)",
> "And more recently, Qualcomm has started building chips specifically for executing neural networks, according to LeCun, who is familiar with Qualcomm's plans because Facebook is helping the chip maker develop technologies related to machine learning. Qualcomm vice president of technology Jeff Gehlhaar confirms the project. "We're very far along in our prototyping and development," he says."
Perhaps we'll see something soon beyond the Kryo CPU, Adreno GPU, Hexagon DSP, and Hexagon Vector Extensions. It is going to be hard to be a start-up in this space if you're competing against Qualcomm's machine learning.

## Apple
> Will it or won't it?  [Bloomberg](https://www.bloomberg.com/news/articles/2017-05-26/apple-said-to-plan-dedicated-chip-to-power-ai-on-devices) is reporting it will as a secondary processor but there is little detail. Not only is it an important area for Apple, but it helps avoid and compete with Qualcomm.

[Core ML](https://developer.apple.com/machine-learning/) is Apple's current sulotion for machine learning application.

## ARM
[DynamIQ](http://pages.arm.com/dynamiq-technology.html) is embedded IP giant's answer to AI age. It may not be a revolutionary design but is important for sure.

ARM also provide a open source [Compute Library](https://developer.arm.com/technologies/compute-library) contains a comprehensive collection of software functions implemented for the Arm Cortex-A family of CPU processors and the Arm Mali family of GPUs.

## IBM TrueNorth
[TrueNorth](http://www.research.ibm.com/articles/brain-chip.shtml) is IBM's Neuromorphic CMOS ASIC developed in conjunction with the DARPA [SyNAPSE](https://en.wikipedia.org/wiki/SyNAPSE) program.
> It is a manycore processor network on a chip design, with 4096 cores, each one simulating 256 programmable silicon "neurons" for a total of just over a million neurons. In turn, each neuron has 256 programmable "synapses" that convey the signals between them. Hence, the total number of programmable synapses is just over 268 million (228). In terms of basic building blocks, its transistor count is 5.4 billion. Since memory, computation, and communication are handled in each of the 4096 neurosynaptic cores, TrueNorth circumvents the von-Neumann-architecture bottlenecks and is very energy-efficient, consuming 70 milliwatts, about 1/10,000th the power density of conventional microprocessors. [Wikipedia](https://en.wikipedia.org/wiki/TrueNorth)

## HiSilicon(华为海思）
> Yu Chengdong, Huawei CEO, recently announced at the 2017 China Internet Conference that Huawei is developing an AI processor. 

### Kirin for Smart Phone
Kirin 970 may have an embedded deep learning accelerator.

### Mobile Camera SoC
According to a Brief Data Sheet of [Hi3559A V100ESultra-HD Mobile Camera SoC](http://www.hisilicon.com/cn/-/media/Hisilicon/pdf/Surveillance_mobilecam/Hi3559A%20V100.pdf), it has:
> Dual-core CNN@700 MHz neural network acceleration engine

## Cambricon（寒武纪）
[Cambricon](http://www.cambricon.com/scheme/#sol_c) is working on IP License, Chip Service, Smart Card and Intelligent Platform.

## Horizon Robotics（地平线机器人）
[Horizon Robotics](http://www.horizon.ai/) has a [Brain Processing Unit](http://www.horizon.ai/programme.php) (BPU) in the works. 

> Chinese startup Horizon Robotics joined forces with Intel to showcase an Advanced Driver Assistance System (ADAS) at CES 2017 which is a single camera that can see stuff and identify it. They also teamed up with Midea and launched an intelligent [air conditioner](http://www.midea.com/global/products/air_conditioning/residential_air_conditioner/ac_split/201403/t20140309_70731.shtml) that no doubt solves loads of first world problems including home security. No news yet on when we can expect their Brain Processing Unit (BPU) to debut but it was supposed to be “[in early 2017](http://www.scmp.com/tech/article/1921396/chinese-start-track-deliver-artificial-intelligence-chip)“. The founder and CEO of Horizon Robotics, Dr. Kai YU, used to be the Head of Baidu Institute of Deep Learning so we’re expecting some great things from this startup which has taken in an undisclosed amount of funding so far.

## Deephi（深鉴科技）
[DeePhi Tech](http://www.deephi.com/) has the cutting-edge technologies in deep compression, compiling toolchain, deep learning processing unit (DPU) design, FPGA development, and system-level optimization. 

## Bitmain（比特大陆）
Bitcoin Mining Giant [Bitmain](https://www.bitmain.com/) is developing processors for AI. 

## Wave Computing
Wave’s Compute Appliance is capable to run TensorFlow at 2.9 PetaOPS/sec on their 3RU appliance. Wave refers to their processors at DPUs and an appliance has 16 DPUs. Wave uses processing elements it calls Coarse Grained Reconfigurable Arrays (CGRAs). It is unclear what bit width the 2.9 PetaOPS/s is referring to. Some details can be fund in their  [white paper](http://wavecomp.ai/technology/).

Some more details can be fund in this article: [AI芯片 浅析Yann LeCun提到的两款Dataflow Chip](https://zhuanlan.zhihu.com/p/26594188)

## Graphcore
[Graphcore](https://www.graphcore.ai/) raised $30M of Series-A late last year to support the development of their Intelligence Processing Unit, or IPU. Resently, co-founder and Chief Technology Officer, Simon Knowles, was invited to give [a talk](https://youtu.be/T8DvHnb3Y9g) at the 3rd Research and Applied AI Summit (RAAIS) in London, showing [interesting ideas](https://www.graphcore.ai/posts/how-to-build-a-processor-for-machine-intelligence-part-2) behind their processor. 

[解密又一个xPU：Graphcore的IPU](https://mp.weixin.qq.com/s/CH9h8dUtoNK_2ZfkK5YU0g) give some analysis on its IPU architecture.

## PEZY Computing K.K.
Pezy-SC and Pezy-SC2 are the 1024 core and 2048 core processors that [Pezy](http://pezy.co.jp/en/index.html) develop. The Pezy-SC 1024 core chip powered the top 3 systems on the Green500 list of supercomputers back in 2015. The [Pezy-SC2](https://en.wikichip.org/wiki/pezy/pezy-sc2) is the follow up chip that is meant to be delivered by now, but details are scarce yet intriguing,
> "PEZY-SC2 HPC Brick: 32 of PEZY-SC2 module card with 64GB DDR4 DIMM (2.1 PetaFLOPS (DP) in single tank with 6.4Tb/s"
It will be interesting to see what  2,048 MIMD MIPS Warrior 64-bit cores can do. In the [June 2017 Green500 list](https://www.top500.org/green500/list/2017/06/), a Nvidia P100 system took the number one spot and there is a Pezy-SC2 system at number 7. So the chip seems alive but details are thin on the ground. [Motoaki Saito](https://wired.jp/special/2016/motoaki-saito/) is certainly worth watching.

## KnuEdge's KnuPath
Their product page has since June 2016 gone missing in action. Not sure what they are up to with the $100M they put into their [MIMD architecture](https://www.hpcwire.com/2016/12/15/knupath-hermosa-chip-expected-first-half-2017/). It was described at the time as having 256 tiny DSP, or tDSP, cores on each ASIC along with an ARM controller suitable for sparse matrix processing in a 35W envelope. 

> The performance is unknown, but they compared their chip to a current NVIDIA, at that time, and said they had 2.5 times the performance. We know Nvidia is now more than ten times faster with their Tensor cores so KnuEdge will have a tough job keeping up. A MIMD or DSP approach will have to execute awfully well to take some share in this space.

> Since KnuEdge “emerged from stealth” last year, the company has gone quiet and not offered up any additional information about what they’ve been up to. According to an [article in VentureBeat](https://venturebeat.com/2016/06/06/former-nasa-chief-unveils-100-million-neural-computing-chip-company-knuedge/), we know that KnuEdge has already been generating revenue and that they were considering raising more funding this year in addition to the $100 million in “patient money” they have already raised. Their website contains next to no information aside from employee profiles. At an [Xconomy conference](http://www.xconomy.com/san-diego/2017/05/02/smarr-others-talk-healthtech-ai-at-xconomys-impact-of-innovation/) a few weeks ago, the Company talked about “cloud-based machine intelligence as a service” that is “supposed to be rolled out sometime this year“.

## Tenstorrent
[Tenstorrent](http://tenstorrent.com/index.html) is a small Canadian start-up in Toronto claiming an order of magnitude improvement in efficiency for deep learning, like most. No real public details but they're are on the [Cognitive 300 list](http://www.cogniteventures.com/the-cognitive-computing-startup-list/).

## Cerebras
[Cerebras](https://www.cerebras.net/) is notable due to its backing from Benchmark and that its founder was the CEO of SeaMicro. It appears to have [raised $25M](https://techcrunch.com/2016/12/19/a-stealthy-startup-called-cerebras-raised-around-25-million-to-build-deep-learning-hardware/) and remains in stealth mode.

## Thinci
[Thinci](http://thinci.com/index.html) is [developing vision processors](https://venturebeat.com/2016/10/06/thinci-teams-with-denso-to-create-vision-processors-with-100x-performance-improvements/) from Sacremento with employees in India too. They claim to be at the point of first silicon, Thinci-tc500, along with benchmarking and winning of customers already happening. Apart from "doing everything in parallel" we have little to go on.

> Founded in 2010, Eldorado Hills, California startup ThinCI has taken in an undisclosed amount of funding to develop a technology that will bring vision processing to all devices. The ability for smart devices to have functionality like computer vision that doesn’t require regular communication to the cloud is referred to as “edge computing” or “fog computing”. That’s where ThinCI wants to play.

## Koniku
[Koniku's web site](http://koniku.io/) is counting down to "your new reality". They have raised very little money and after watching their Youtube clip embedded in this [Forbes page](https://www.forbes.com/sites/federicoguerrini/2016/05/22/neuron-based-chips-will-soon-become-commonplace-this-startup-founder-says/2/#299122784f1f), you too will not likely not be convinced, but you never know. Harnessing biological cells is certainly different. It sounds like [a science project](https://motherboard.vice.com/en_us/article/d7ypqw/komiku-neuron-computer-agabi), but, then this,
> "We are a business. We are not a science project," Agabi, who is scheduled to speak at the Pioneers Festival in Vienna, next week, says, "There are demands that silicon cannot offer today, that we can offer with our systems."
> The core of the Koniku offer is the so-called neuron-shell, inside which the startup says it can control how neurons communicate with each other, combined with a patent-pending electrode which allows to read and write information inside the neurons. All this packed in a device as large as an iPad, which they hope to reduce to the size of a nickel by 2018.

## Adapteva
[Adapteva](http://www.adapteva.com/): "[Adapteva tapes out Epiphany-V: A 1024-core 64-bit RISC processor](https://meanderful.blogspot.jp/2016/10/adapteva-tapes-out-epiphany-v-1024-core.html)." Andreas Olofsson taped out his 1024 core chip late last year and we await news of its performance. [Epiphany-V](http://www.parallella.org/docs/e5_1024core_soc.pdf) has new instructions for deep learning and we'll have to see if this memory-controller-less design with 64MB of on-chip memory will have appropriate scalability. The impressive efficiency of Andrea's design and build may make this a chip we can all actually afford, so let's hope it performs well.

## Knowm
- [Knowm](http://knowm.org/) is actually setup as a .ORG but they appear to be pursuing a for-profit enterprise. The New Mexcio startup has taken in an undisclosed amount of seed funding so far to develop a new computational framework called [AHaH Computing](http://knowm.org/ahah-computing/) (Anti-Hebbian and Hebbian). The gory details can be found in [this publication](http://journals.plos.org/plosone/article?id=10.1371/journal.pone.0085175), but the short story is that this technology aims to reduce the size and power consumption of intelligent machine learning applications by up to 9 orders of magnitude.


## Mythic
A battery powered neural chip from [Mythic](https://www.mythic-ai.com/technology/) with 50x lower power.
> Founded in 2012, Texas-based startup Mythic (formerly known as Isocline) has taken in $9.5 million in funding with Draper Fisher Jurvetson as the lead investor. Prior to receiving any funding, the startup has taken in [$2.5 million in grants](https://techcrunch.com/2017/03/22/mythic-launches-a-chip-to-enable-computer-vision-and-voice-control-on-any-device/). Mythic is developing an AI chip that “puts desktop GPU compute capabilities and deep neural networks onto a button-sized chip – with 50x higher battery life and far more data processing capabilities than competitors“. Essentially, that means you can give voice control and computer vision to any device locally without needing cloud connectivity.

## Kalray
Despite many promises,[Kalray](http://www.kalrayinc.com/) has not progressed their chip offering beyond the 256 core beast covered back in 2015, "[Kalray - new product meander](https://meanderful.blogspot.jp/2015/06/kalray-new-product-meander.html)." Kalray is advertising their product as suitable for embedded self-driving car applications. Kalray has a [Kalray Neural Network](http://www.eenewseurope.com/news/kalray-turns-neural-networks) (KaNN) software package and claims better efficiency than GPUs with up to 1 TFlop/s on chip.
Kalrays NN fortunes may improve with an imminent product refresh and just this month Kalray completed a new funding that raised $26M. The new [Coolidge processor]((http://www.eenewseurope.com/news/kalray-turns-neural-networks)) is due in mid-2018 with 80 or 160 cores along with 80 or 160 co-processors optimised for vision and deep learning.

## Brainchip
Brainchip's [Spiking Neuron Adaptive Processor](http://www.brainchipinc.com/technology) (SNAP) will not do deep learning and is a curiosity without being a practical drop in CNN engineering solution, yet. IBM's [stochastic phase-change neurons](http://www.nature.com/nnano/journal/v11/n8/full/nnano.2016.70.html?foxtrotcallback=true) seem more interesting if that is a path you wish to tread.

## Groq
[Groq](https://www.cnbc.com/2017/04/20/ex-googlers-left-secretive-ai-unit-to-form-groq-with-palihapitiya.html) is founded by Ex-googlers, who designed Google TPU.

## Aimotive
[This BDTi artical](https://www.bdti.com/InsideDSP/2017/07/27/AImotive) shows some information of aiWare IP of [Aimotive](https://aimotive.com/what-we-do/#aiware) .
> Speaking of chips, AImotive and partner VeriSilicon are in the process of designing a 22 nm FD-SOI test chip, which is forecast to come out of GlobalFoundries' fab in Q1 2018 (Figure 4). It will feature a 1 TMAC/sec aiWare core, consuming approximately 25 mm2 of silicon area; a Vivante VIP8000-derivative processor core will inhabit the other half of the die, and between 2-4 GBytes of DDR4 SDRAM will also be included in the multi-die package. The convolution-tailored LAM in this test chip, according to Feher, will have the following specifications (based on preliminary synthesis results):
> 2,048 8x8 MACs
> Logic area (including input/output buffering logic, LAM control and MACs): 3.45mm2
> Memory (on-chip buffer): in the range of 5-25mm2 depending on configuration (10-50 Mbits).

Another interesting activity of Aimotive is [Neural Network Exchange Format (NNEF)](https://www.khronos.org/nnef).
## Deep Vision
[Deep Vision](http://deepvision.io/) is bulding low-power chips for deep learning. Perhaps one of these papers by the founders have clues, "[Convolution Engine: Balancing Efficiency & Flexibility in Specialized Computing](http://csl.stanford.edu/~christos/publications/2013.convolution.isca.pdf)" [2013] and "[Convolution Engine: Balancing Efficiency and Flexibility in Specialized Computing](http://csl.stanford.edu/~christos/publications/2015.convolution_engine.cacm.pdf)" [2015].

## Deep Scale
[DeepScale raises $3 million for perception AI to make self-driving cars safe](https://techcrunch.com/2017/03/21/deepscale-raises-3-million-for-perception-ai-to-make-self-driving-cars-safe/)

## REM
[Reduced Energy Microsystems](http://www.remicro.com/) are developing lower power asynchronous chips to suit CNN inference. REM was Y Combinator's first ASIC venture according to [TechCrunch](https://techcrunch.com/2017/03/16/reduced-energy-microsystems-pits-startup-chip-chops-against-industry-giants/).

## Leepmind
[Leepmind](http://www.leapmind.io/products.php)
> We are carrying out research on original chip architectures in order to implement Neural Networks on a circuit enabling low power DeepLearning

## Krtkl
[krtkl](http://krtkl.com/). 

> This crowdfunding effort made its way into our original article on AI chips so it’s only fair we include it in this one. While it is not actually possible to pick a worse name for your startup than “krtkl”, at least the product name is manageable. Snickerdoodle is “reconfigurable hardware for building intelligent systems” (think Raspberry Pi). A crowdfunding effort for Snickerdoodle raised $224,876 and they’re currenty shipping. If you pre-order one, they’ll deliver it by summer. The palm-sized unit uses the Zynq “System on Chip” (SoC) from Xilinix.

## TeraDeep 
[TeraDeep](https://www.teradeep.com/) is building an AI Appliance using its deep learning FPGA’s acceleration. The company claims image recognition performance on AlexNet to achieve a 2X performance advantage compared with large GPUs, while consuming 5X less power. When compared to Intel’s Xeon processor, TeraDeep’s Accel technology delivers 10X the performance while consuming 5X less power.

## KAIST DNPU
- [Face Recognition System “K-Eye” Presented by KAIST](http://www.kaist.ac.kr/_prog/_board/?code=ed_news&mode=V&no=65402&upr_ntt_no=65402&site_dvs_cd=en&menu_dvs_cd=)

- [从ISSCC Deep Learning处理器论文到人脸识别产品](https://zhuanlan.zhihu.com/p/28328046)

## Synopsys Embedded Vision
- [DesignWare EV6x Embedded Vision Processors](https://www.synopsys.com/company/newsroom/mnr/ev6x-processors-news-release.html)

- [处理器IP厂商的机器学习方案 - Synopsys](http://mp.weixin.qq.com/s/Y4BvzmH67OaTWc_2SXIVGg)

## CEVA XM6
- [CEVA-XM6 Fifth-generation computer vision and deep learning embedded platform](http://www.ceva-dsp.com/product/ceva-xm6/)

- [处理器IP厂商的机器学习方案 - CEVA](http://mp.weixin.qq.com/s/rosyXJew4B0NvzY73uHz5w)

## VeriSilicon VIP8000
- [VeriSilicon’s Vivante VIP8000 Neural Network Processor IP Delivers Over 3 Tera MACs Per Second](http://www.verisilicon.com/newsdetail_499_VivanteVIP8000.html)

- [神经网络DSP核的一桌麻将终于凑齐了](https://mp.weixin.qq.com/s/1W8mAMR9xaljZPLyEW0Xmw)

## Cadence P5/P6/C5
- [Tensilica Vision DSPs for Imaging, Computer Vision, and Neural Networks](https://ip.cadence.com/vision&CMP=TIP_BB_CDN_Vis_0501_C5_PP)

## Reference
1. [FPGAs and AI processors: DNN and CNN for all](https://meanderful.blogspot.jp/2017/06/fpgas-and-ai-processors-dnn-and-cnn-for.html)
2. [12 AI Hardware Startups Building New AI Chips](http://www.nanalyze.com/2017/05/12-ai-hardware-startups-new-ai-chips/)
3. [Tutorial on Hardware Architectures for Deep Neural Networks](http://eyeriss.mit.edu/tutorial.html)
4. [Neural Network Accelerator Inference](https://nicsefc.ee.tsinghua.edu.cn/projects/neural-network-accelerator/)

