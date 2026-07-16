<header class="page-header" align="center">
<h1 class="site-brand">AI Chip (ICs and IPs)</h1>
<div class="hero-art"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AI-chips.png" loading="lazy" alt="AI chips illustration" /></div>
<p class="editor-line">Editor <a href="https://www.linkedin.com/in/shan-tang-27342510/"><strong>S.T.</strong></a> (LinkedIn)</p>
<p class="wechat-line"><strong>WeChat / 微信公众号</strong> · <a href="https://mp.weixin.qq.com/mp/appmsgalbum?action=getalbum&amp;__biz=MzI3MDQ2MjA3OA==&amp;scene=1&amp;album_id=1374108991751782402&amp;count=3#wechat_redirect">StarryHeavensAbove</a> — AI chip articles</p>
<div class="wechat-qr"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/qrcode_for_weichat_258.jpg" height="100" loading="lazy" alt="WeChat QR code" /></div>
<div class="landscape-map"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AI_Chip_Landscape_v0p7.png" loading="lazy" alt="AI Chip Landscape map" /></div>
<p class="page-intro">A living directory of AI accelerators (ICs &amp; IPs) — hyperscaler custom silicon, GPU/NPU vendors, IP houses, startups, and China domestic accelerators. Prefer official / primary sources; performance claims are often vendor-reported.</p>
</header>

 
<div align="center" class="section-title"><h2>Latest updates</h2></div>
<p class="refresh-note" align="center"><em>Last refreshed: July 2026 — major vendor coverage updated for the generative-AI / LLM accelerator era.</em></p>
<hr class="section-rule" />

<ul class="updates-list">
<li><strong>NVIDIA</strong>: <a href="#Nvidia">Vera Rubin</a> platform (CES/GTC 2026) and <a href="#Nvidia">Blackwell</a> (B200 / GB200 NVL72).</li>
<li><strong>AMD</strong>: <a href="#AMD">Instinct MI350</a> series (CDNA 4) and Meta partnership for Helios / MI450-class GPUs.</li>
<li><strong>Intel</strong>: <a href="#Habana">Gaudi 3</a> AI accelerator for enterprise GenAI training and inference.</li>
<li><strong>Google</strong>: Cloud TPU <a href="#Google">Trillium (v6e)</a> and <a href="#Google">Ironwood (TPU7x)</a>.</li>
<li><strong>Amazon AWS</strong>: <a href="#Amazon_AWS">Trainium2</a> / Trn2 UltraServers and Inferentia2.</li>
<li><strong>Microsoft</strong>: <a href="#Microsoft">Azure Maia 100</a> custom AI accelerator.</li>
<li><strong>Meta</strong>: <a href="#Facebook">MTIA</a> custom training &amp; inference accelerators (multi-generation roadmap).</li>
<li><strong>Cerebras</strong>: <a href="#Cerebras">WSE-3 / CS-3</a> wafer-scale engine.</li>
<li><strong>Groq</strong>: LPU inference focus; technology licensed / team joined <a href="#Groq">NVIDIA</a> (late 2025).</li>
<li><strong>Benchmarks</strong>: Links updated to <a href="#AIChipBenchmarks">MLPerf Inference v6.0</a> and <a href="#AIChipBenchmarks">Training v6.0</a>.</li>
<li><strong>Compilers</strong>: Refreshed <a href="#AIChipCompilers">AI Chip Compilers</a> list (Triton, IREE, TensorRT-LLM, etc.).</li>
<li><strong>Apple</strong>: <a href="#Apple">M4 / M5</a> Apple silicon Neural Engine &amp; GPU Neural Accelerators.</li>
<li><strong>Samsung</strong>: <a href="#Samsung">Exynos 2500</a> on-device NPU (3nm GAA).</li>
<li><strong>Qualcomm</strong>: <a href="#Qualcomm">Snapdragon 8 Elite</a> Hexagon NPU for on-device GenAI.</li>
<li><strong>China accelerators</strong>: <a href="#China_AI_Chips">Huawei Ascend</a>, Cambricon, Biren, Moore Threads, <a href="#MetaX">MetaX</a>, <a href="#Hygon">Hygon DCU</a>, <a href="#Iluvatar">Iluvatar CoreX</a>, Enflame, Horizon.</li>
<li><strong>Alibaba</strong>: T-Head <a href="#Alibaba">PPU / Zhenwu</a> cloud AI chips.</li>
<li><strong>Startups</strong>: added <a href="#Etched">Etched</a> (transformer ASIC / Sohu).</li>
<li><strong>MediaTek</strong>: <a href="#MediaTek">Dimensity 9400</a> NPU 890 / agentic on-device AI.</li>
<li><strong>Broadcom / OpenAI</strong>: custom AI <a href="#Broadcom">XPU</a> partner; <a href="#OpenAI">Jalapeño</a> inference ASIC.</li>
<li><strong>Marvell</strong>: noted role as custom AI ASIC partner (Trainium / Maia class programs).</li>
<li><strong>Anthropic</strong>: multi-cloud compute on <a href="#Anthropic">TPU / Trainium / GPU</a> (Google–Broadcom GW-scale deals).</li>
<li><strong>Graphcore</strong>: <a href="#Graphcore">acquired by SoftBank</a> (2024); continues IPU / next-gen work inside SoftBank.</li>
<li><strong>Edge / ADAS</strong>: <a href="#SiMa">SiMa Modalix</a> Physical AI; <a href="#BlackSesame">Black Sesame Huashan</a> automotive SoCs.</li>
<li><strong>Tesla</strong>: <a href="#Tesla">AI5 tape-out</a> (2026); Dojo / AI4 lineage retained as historical context.</li>
<li><strong>FuriosaAI</strong>: <a href="#Furiosa">RNGD</a> mass production + Broadcom next-gen partnership; Equinix Europe deploy.</li>
<li><strong>Hailo</strong>: <a href="#Hailo">Hailo-10H</a> edge GenAI accelerator (LLM/VLM) generally available.</li>
<li><strong>Arm</strong>: <a href="#ARM">Ethos-U85</a> micro-NPU with native transformer support (edge / IoT GenAI).</li>
<li><strong>SambaNova</strong>: <a href="#SambaNova">SN50 RDU</a> agentic inference chip + Intel collaboration / Series E.</li>
<li><strong>Mythic</strong>: <a href="#Mythic">$125M Series D</a> + Videantis acquisition for hybrid analog/digital AI platform.</li>
<li><strong>Pages UX</strong>: HTML structure cleanup + custom CSS on GitHub Pages (section chrome, shortcut table, vendor logo blocks).</li>
</ul>

<div align="center" class="section-title"><h2>Shortcut</h2></div>
<hr class="section-rule" />
<table class="shortcut-table">
  <tr>
    <th><a href="#IC_Vendors">IC Vendors</a></th><td><a href="#Intel">Intel</a>, <a href="#Qualcomm">Qualcomm</a>, <a href="#Nvidia">Nvidia</a>, <a href="#Samsung">Samsung</a>, <a href="#AMD">AMD</a>, <a href="#MediaTek">MediaTek</a>, <a href="#IBM">IBM</a>, <a href="#Marvell">Marvell</a>, <a href="#Broadcom">Broadcom</a></td>
  </tr>
  <tr>
    <th><a href="#Tech_Giants">Tech Giants & HPC Vendors</a></th><td><a href="#Google">Google</a>, <a href="#Amazon_AWS">Amazon_AWS</a>, <a href="#Microsoft">Microsoft</a>, <a href="#Apple">Apple</a>, <a href="#OpenAI">OpenAI</a>, <a href="#Anthropic">Anthropic</a>, <a href="#Alibaba">Alibaba Group</a>, <a href="#Tencent_Cloud">Tencent Cloud</a>, <a href="#Baidu">Baidu</a>, <a href="#Fujitsu">Fujitsu</a>, <a href="#Nokia">Nokia</a>, <a href="#Facebook">Meta (Facebook)</a>, <a href="#Tesla">Tesla</a></td>
  </tr>
  <tr>
    <th><a href="#IP_Vendors">IP Vendors</a></th><td><a href="#ARM">ARM</a>, <a href="#Synopsys">Synopsys</a>, <a href="#Imagination">Imagination</a>, <a href="#CEVA">CEVA</a>, <a href="#Cadence">Cadence</a>, <a href="#VeriSilicon">VeriSilicon</a></td>
  </tr>
  <tr>  
    <th><a href="#Startups">Startups</a></th>
    <td><a href="#Cerebras">Cerebras</a>, <a href="#Graphcore">Graphcore</a>, <a href="#Tenstorrent">Tenstorrent</a>, <a href="#Etched">Etched</a>, <a href="#Groq">Groq</a>, <a href="#SambaNova">SambaNova</a>, <a href="#Mythic">Mythic</a>, <a href="#Hailo">Hailo</a>, <a href="#Furiosa">FuriosaAI</a>, <a href="#d-matrix">d-Matrix</a>, <a href="#SiMa">SiMa</a>, … (full list in section IV)</td>
  </tr>
  <tr>
    <th><a href="#China_AI_Chips">China AI Accelerators</a></th>
    <td><a href="#HuaweiAscend">Huawei Ascend</a>, <a href="#Cambricon">Cambricon</a>, <a href="#Biren">Biren</a>, <a href="#MooreThreads">Moore Threads</a>, <a href="#MetaX">MetaX</a>, <a href="#Hygon">Hygon</a>, <a href="#Iluvatar">Iluvatar CoreX</a>, <a href="#Enflame">Enflame</a>, <a href="#Horizon">Horizon Robotics</a>, <a href="#BlackSesame">Black Sesame</a>, <a href="#Alibaba">Alibaba T-Head</a>, <a href="#Baidu">Baidu Kunlun</a></td>
  </tr>
</table>

<div align="center" class="section-title"><h2><a name="IC_Vendors"></a>I. IC Vendors</h2></div>
<hr class="section-rule" />

<a name="Nvidia"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Nvidia_logo.png" height="50" loading="lazy" alt="NVIDIA" /> </div>
<div align="center"><h3>GPU</h3></div>

<p><strong><a href="https://nvidianews.nvidia.com/news/rubin-platform-ai-supercomputer">NVIDIA Kicks Off the Next Generation of AI With Rubin</a></strong></p>
<blockquote>
  <p>CES 2026 — NVIDIA launched the Rubin platform: Vera CPU, Rubin GPU, NVLink 6 Switch, ConnectX-9, BlueField-4 and Spectrum-6, codesigned for agentic AI and large MoE models. vs. Blackwell, NVIDIA claims up to 10x lower inference token cost and 4x fewer GPUs to train MoE models. Partner availability is targeted for H2 2026.</p>
</blockquote>

<p><strong><a href="https://nvidianews.nvidia.com/news/nvidia-blackwell-platform-arrives-to-power-a-new-era-of-computing">NVIDIA Blackwell Platform Arrives to Power a New Era of Computing</a></strong></p>
<blockquote>
  <p>GTC 2024 — Blackwell succeeds Hopper for trillion-parameter generative AI. The B200 Tensor Core GPU and GB200 Grace Blackwell Superchip power rack-scale GB200 NVL72 systems with fifth-generation NVLink, targeting large-scale training and real-time LLM inference.</p>
</blockquote>

<p><a href="https://nvidianews.nvidia.com/news/nvidia-microsoft-accelerate-cloud-enterprise-ai">NVIDIA Teams With Microsoft to Build Massive Cloud AI Computer</a></p>
<blockquote>
  <p>Tens of Thousands of NVIDIA GPUs, NVIDIA Quantum-2 InfiniBand and Full Stack of NVIDIA AI Software Coming to Azure; NVIDIA, Microsoft and Global Enterprises to Use Platform for Rapid, Cost-Effective AI Development and Deployment</p>
</blockquote> 

<p><strong><a href="https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth">NVIDIA Hopper Architecture In-Depth</a></strong></p>
<blockquote>
  <p>Today during the 2022 NVIDIA GTC Keynote address, NVIDIA CEO Jensen Huang introduced the new NVIDIA H100 Tensor Core GPU based on the new NVIDIA Hopper GPU architecture. This post gives you a look inside the new H100 GPU and describes important new features of NVIDIA Hopper architecture GPUs.</p>
</blockquote> 
 
<p><a href="https://www.anandtech.com/show/16610/nvidia-unveils-grace-a-highperformance-arm-server-cpu-for-use-in-ai-systems">NVIDIA Unveils Grace: A High-Performance Arm Server CPU For Use In Big AI Systems</a></p>
<blockquote>
  <p>Kicking off another busy Spring GPU Technology Conference for NVIDIA, this morning the graphics and accelerator designer is announcing that they are going to once again design their own Arm-based CPU/SoC. Dubbed Grace – after Grace Hopper, the computer programming pioneer and US Navy rear admiral – the CPU is NVIDIA’s latest stab at more fully vertically integrating their hardware stack by being able to offer a high-performance CPU alongside their regular GPU wares. According to NVIDIA, the chip is being designed specifically for large-scale neural network workloads, and is expected to become available in NVIDIA products in 2023.</p>
</blockquote>

<a name="Intel"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Intel_logo.png" height="60" loading="lazy" alt="Intel" /></div>

<a name="Mobileye"></a>
<div align="center"><h3>Mobileye EyeQ</h3></div>
> Mobileye is currently developing its fifth generation SoC, the <a href="https://www.mobileye.com/our-technology/evolution-eyeq-chip/">EyeQ®5</a>, to act as the vision central computer performing sensor fusion for Fully Autonomous Driving (Level 5) vehicles that will hit the road in 2020. To meet power consumption and performance targets, EyeQ® SoCs are designed in most advanced VLSI process technology nodes – down to 7nm FinFET in the 5th generation. 

<a name="Loihi 2"></a>
<div align="center"><h3>Loihi</h3></div>
<p><a href="https://www.intel.com/content/www/us/en/newsroom/news/intel-unveils-neuromorphic-loihi-2-lava-software.html">Intel Advances Neuromorphic with Loihi 2, New Lava Software Framework and New Partners</a></p>
<blockquote>
  <p>Second-generation research chip uses pre-production Intel 4 process, grows to 1 million neurons. Intel adds open software framework to accelerate developer innovation and path to commercialization.</p>
</blockquote>

<p><a name="Habana"></a></p>
<div align="center"><h3>Habana</h3></div>
<p><strong><a href="https://newsroom.intel.com/artificial-intelligence/vision-2024-enterprise-ai-gaudi-3-open-systems-strategy">Intel Unleashes Enterprise AI with Gaudi 3</a></strong></p>
<blockquote>
  <p>Intel Vision 2024 — Gaudi 3 targets generative AI training and inference with Ethernet scale-out. Intel positions Gaudi 3 for enterprise GenAI price/performance vs. GPU alternatives, with OEM availability through Dell, HPE, Lenovo, Supermicro and cloud partners.</p>
</blockquote>

<p><strong><a href="https://www.intel.com/content/www/us/en/newsroom/news/vision-2022-habana-gaudi2-greco.html">Intel’s Habana Labs Launches Second-Generation AI Processors for Training and Inferencing</a></strong></p>
<blockquote>
  <p>Today at Intel Vision, Intel announced that Habana Labs, its data center team focused on AI deep learning processor technologies, launched its second-generation deep learning processors for training and inference: Habana® Gaudi®2 and Habana® Greco™. These new processors address an industry gap by providing customers with high-performance, high-efficiency deep learning compute choices for both training workloads and inference deployments in the data center while lowering the AI barrier to entry for companies of all sizes.</p>
</blockquote>
 
<p><a href="https://habana.ai/aws-launches-ec2-dl1-instances/">Habana Gaudi debuts in the Amazon EC2 cloud</a></p>
<blockquote>
  <p>The primary motivation to create this new training instance class was presented by Andy Jassy in the 2020 re:Invent: “To provide our end-customers with up to 40% better price-performance than the current generation of GPU-based instances.”</p>
</blockquote>

<a name="Qualcomm"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Qualcomm_logo.png" height="40" loading="lazy" alt="Qualcomm" /></div>

<p><strong><a href="https://www.androidauthority.com/snapdragon-8-elite-3491805/">Snapdragon 8 Elite — Hexagon NPU for on-device GenAI</a></strong></p>
<blockquote>
  <p>Snapdragon Summit 2024 — custom Oryon CPU plus a redesigned Hexagon NPU (fused scalar/vector/tensor accelerators). Qualcomm cites ~45% faster NPU performance and better perf/W vs. Snapdragon 8 Gen 3 for multimodal on-device generative AI.</p>
</blockquote>

<p><a href="https://www.qualcomm.com/products/technology/processors/cloud-artificial-intelligence/cloud-ai-100">Qualcomm Cloud AI 100</a></p>
<blockquote>
  <p>Cloud/edge inference accelerator focused on power-efficient deployment outside traditional GPU clusters.</p>
</blockquote>

<a href="https://www-forbes-com.cdn.ampproject.org/c/s/www.forbes.com/sites/karlfreund/2022/11/16/qualcomm-ups-the-snapgragon-ai-game/amp/">Qualcomm Ups The Snapgragon AI Game</a>
<blockquote>
  <p>The leader in premium mobile SoCs has applied AI across the entire platform.</p>
</blockquote>

<strong><a href="https://www.qualcomm.com/products/technology/processors/cloud-artificial-intelligence/cloud-ai-100">Qualcomm Cloud AI 100</a></strong>
<blockquote>
  <p>The Qualcomm Cloud AI 100, designed for AI inference acceleration, addresses unique requirements in the cloud, including power efficiency, scale, process node advancements, and signal processing—facilitating the ability of datacenters to run inference on the edge cloud faster and more efficiently. Qualcomm Cloud AI 100 is designed to be a leading solution for datacenters who increasingly rely on infrastructure at the edge-cloud.</p>
</blockquote>

<a name="Samsung"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Samsung_logo.png" height="35" loading="lazy" alt="Samsung" /></div>
<p><strong><a href="https://semiconductor.samsung.com/processor/mobile-processor/exynos-2500/">Samsung Exynos 2500</a></strong></p>
<blockquote>
  <p>Flagship mobile SoC on Samsung 3nm GAA process with a substantially upgraded NPU (Samsung cites up to ~59 TOPS and ~39% better on-device AI vs. Exynos 2400) for generative AI and privacy-preserving on-device inference.</p>
</blockquote>

<p><a href="https://news.samsung.com/global/samsung-brings-on-device-ai-processing-for-premium-mobile-devices-with-exynos-9-series-9820-processor">Samsung Brings On-device AI Processing… Exynos 9 Series 9820</a> (historical)</p>
<blockquote>
  <p>Earlier on-device AI messaging around Exynos 9820 / 9810-era NPU features for AR/VR and mobile deep learning.</p>
</blockquote>   

<a name="MediaTek"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/MediaTek_logo.png" height="40" loading="lazy" alt="MediaTek" /></div>

<p><strong><a href="https://www.mediatek.com/press-room/mediateks-dimensity-9400-flagship-soc-offers-extreme-performance-and-efficiency-for-the-latest-ai-experiences">MediaTek Dimensity 9400 — 8th Gen NPU for agentic AI</a></strong></p>
<blockquote>
  <p>Oct 2024 — Flagship Dimensity 9400 (TSMC 3nm) pairs an all-big-core CPU with MediaTek’s 8th-generation NPU 890. MediaTek highlights on-device LoRA training, high-quality video generation, MoE LLM support, and the Dimensity Agentic AI Engine (DAE), with claimed large gains in LLM prompt / diffusion performance vs. Dimensity 9300.</p>
</blockquote>

<p><a href="https://www.mediatek.com/products/smartphones/mediatek-dimensity-9400">Dimensity 9400 product page</a></p>

<a name="AMD"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AMD_logo.png" height="35" loading="lazy" alt="AMD" /></div>
<p><strong><a href="https://www.amd.com/en/products/accelerators/instinct/mi350.html">AMD Instinct™ MI350 Series GPUs</a></strong></p>
<blockquote>
  <p>Built on 4th Gen AMD CDNA™ architecture, MI350X / MI355X deliver large HBM3E capacity (up to 288GB) and high bandwidth for generative AI training and inference, with expanded low-precision datatype support (including MXFP6 / MXFP4). MI400-series / Helios rack-scale systems are on AMD’s 2026 roadmap.</p>
</blockquote>

<p><strong><a href="https://www.amd.com/en/newsroom/press-releases/2026-2-24-amd-and-meta-announce-expanded-strategic-partnersh.html">AMD and Meta Announce Expanded Strategic Partnership to Deploy 6 Gigawatts of AMD GPUs</a></strong></p>
<blockquote>
  <p>Feb 2026 — AMD and Meta expanded their partnership for multi-generation Instinct GPU deployments, including custom MI450-class GPUs on the Helios rack architecture with ROCm software.</p>
</blockquote>

<p><a href="https://www.amd.com/en/products/accelerators/instinct.html">AMD Instinct™ MI Series Accelerators</a></p>
<blockquote>
  <p>AMD Instinct accelerators target data-center HPC and AI, combining CDNA architecture, Infinity Fabric interconnect, and the open ROCm software stack for training and inference at scale.</p>
</blockquote>

<p><a name="IBM"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/IBM_logo.png" height="40" loading="lazy" alt="IBM" /></div>

<p><a href="https://www.ibm.com/blogs/systems/ibm-telum-processor-the-next-gen-microprocessor-for-ibm-z-and-ibm-linuxone/">Meet the IBM Artificial Intelligence Unit</a></p>

<blockquote>
  <p>It’s our first complete system-on-chip designed to run and train deep learning models faster and more efficiently than a general-purpose CPU.</p>
</blockquote>

<p><a href="https://www.ibm.com/blogs/systems/ibm-telum-processor-the-next-gen-microprocessor-for-ibm-z-and-ibm-linuxone/">IBM Telum Processor: the next-gen microprocessor for IBM Z and IBM LinuxONE</a></p>

<blockquote>
  <p>The 7 nm microprocessor is engineered to meet the demands our clients face for gaining AI-based insights from their data without compromising response time for high volume transactional workloads. </p>
</blockquote>

<p><a href="https://www.ibm.com/blogs/research/tag/truenorth/">TrueNorth</a> is IBM's Neuromorphic CMOS ASIC developed in conjunction with the DARPA <a href="https://en.wikipedia.org/wiki/SyNAPSE">SyNAPSE</a> program.</p>

<blockquote>
  <p>It is a manycore processor network on a chip design, with 4096 cores, each one simulating 256 programmable silicon "neurons" for a total of just over a million neurons. In turn, each neuron has 256 programmable "synapses" that convey the signals between them. Hence, the total number of programmable synapses is just over 268 million (228). In terms of basic building blocks, its transistor count is 5.4 billion. Since memory, computation, and communication are handled in each of the 4096 neurosynaptic cores, TrueNorth circumvents the von-Neumann-architecture bottlenecks and is very energy-efficient, consuming 70 milliwatts, about 1/10,000th the power density of conventional microprocessors. <a href="https://en.wikipedia.org/wiki/TrueNorth">Wikipedia</a></p>
</blockquote>

<p><a href="https://www.research.ibm.com/artificial-intelligence/ai-hardware-center/">AI Hardware Center</a></p>
<blockquote>
  <p>"The IBM Research AI Hardware Center is a global research hub headquartered in Albany, New York. The center is focused on enabling next-generation chips and systems that support the tremendous processing power and unprecedented speed that AI requires to realize its full potential.</p>
</blockquote>

<p><a name="Marvell"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Marvell_logo.png" height="60" loading="lazy" alt="Marvell" /></div>

<p><strong><a href="https://www.marvell.com/products/data-processing-units.html">Custom AI ASICs + DPUs</a></strong></p>
<blockquote>
  <p>Beyond OCTEON / ARMADA DPUs for networking infrastructure, Marvell is a major custom AI accelerator design partner for hyperscalers (widely reported programs include AWS Trainium/Inferentia-class and Microsoft Maia-class silicon), complementing Broadcom’s XPU franchise.</p>
</blockquote>

<p><a href="https://www.marvell.com/products/data-processing-units.html">Data Processing Units</a></p>
<blockquote>
  <p>Marvell’s OCTEON™, OCTEON™ Fusion and ARMADA® platforms target wireless infrastructure, carrier networks, enterprise and cloud data centers.</p>
</blockquote>

<p><a name="Broadcom"></a></p>
<div align="center"><h3>Broadcom</h3></div>

<p><strong><a href="https://openai.com/index/openai-and-broadcom-announce-strategic-collaboration/">OpenAI and Broadcom announce strategic collaboration for custom AI accelerators</a></strong></p>
<blockquote>
  <p>Oct 2025 — Multi-year plan to deploy ~10 GW of OpenAI-designed accelerators co-developed with Broadcom (Ethernet scale-up/scale-out), with rack deployments targeted from H2 2026 through 2029.</p>
</blockquote>

<p><strong><a href="https://www.nasdaq.com/press-release/broadcom-announces-extended-partnership-meta-deploy-technology-support-multi">Broadcom extends partnership with Meta on MTIA custom silicon</a></strong></p>
<blockquote>
  <p>Apr 2026 — Broadcom’s XPU platform continues as the co-design / implementation backbone for Meta’s multi-generation MTIA accelerators and supporting Ethernet AI networking fabric.</p>
</blockquote>

<p><a href="https://www.hpcwire.com/2025/09/09/broadcom-steps-up-to-challenge-nvidia-in-ai-chip-arms-race/">Broadcom custom XPUs for hyperscaler AI</a></p>
<blockquote>
  <p>Broadcom co-designs customer-specific AI accelerators (XPUs) and pairs them with Tomahawk / Jericho Ethernet switching — a long-running model that began with Google TPU generations and now spans multiple frontier labs and cloud providers.</p>
</blockquote>

<div align="center" class="section-title"><h2><a name="Tech_Giants"></a>II. Tech Giants & HPC Vendors</h2></div>

<hr class="section-rule" />

<p><a name="Google"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Google_logo.png" height="40" loading="lazy" alt="Google" /></div>

<p><strong><a href="https://cloud.google.com/blog/products/compute/introducing-trillium-6th-gen-tpus">Introducing Trillium, sixth-generation TPUs</a></strong></p>
<blockquote>
  <p>Google Cloud’s TPU v6e (Trillium) delivers up to 4.7× peak compute per chip vs. TPU v5e, with doubled HBM capacity/bandwidth and improved energy efficiency for foundation-model training and serving.</p>
</blockquote>

<p><strong><a href="https://docs.cloud.google.com/tpu/docs/release-notes">Cloud TPU Ironwood (TPU7x) generally available</a></strong></p>
<blockquote>
  <p>Ironwood is Google Cloud’s seventh-generation TPU family for large-scale training and inference (LLMs, MoEs, diffusion). See Cloud TPU docs / release notes for TPU7x availability and configurations.</p>
</blockquote>

<p><a href="https://docs.cloud.google.com/tpu/docs/v6e">TPU v6e (Trillium) architecture documentation</a></p>

<p><strong><a href="https://www.zdnet.com/article/google-tensor-everything-you-need-to-know-about-the-pixel-6-chip/">Google Tensor: Everything you need to know about the Pixel 6 chip</a></strong></p>
<blockquote>
  <p>Google has taken the wraps off its latest Pixel smartphones and, among the changes, the one with the biggest long-term impact is the switch to in-house silicon for the search giant.</p>
</blockquote>
 
<p><a href="https://www.hpcwire.com/2021/05/20/google-launches-tpu-v4-ai-chips/">Google Launches TPU v4 AI Chips</a></p>
<blockquote>
  <p>Google CEO Sundar Pichai spoke for only one minute and 42 seconds about the company’s latest TPU v4 Tensor Processing Units during his keynote at the Google I/O virtual conference this week, but it may have been the most important and awaited news from the event.</p>
</blockquote>
 
<p><a href="https://cloud.google.com/tpu">Cloud TPU</a></p>
<blockquote>
  <p>Machine learning has produced business and research breakthroughs ranging from network security to medical diagnoses. We built the Tensor Processing Unit (TPU) in order to make it possible for anyone to achieve similar breakthroughs. Cloud TPU is the custom-designed machine learning ASIC that powers Google products like Translate, Photos, Search, Assistant, and Gmail. Here’s how you can put the TPU and machine learning to work accelerating your company’s success, especially at scale.</p>
</blockquote>
 
<p><a href="https://cloud.google.com/edge-tpu/">Edge TPU</a></p>
<blockquote>
  <p>AI is pervasive today, from consumer to enterprise applications. With the explosive growth of connected devices, combined with a demand for privacy/confidentiality, low latency, and bandwidth constraints, AI models trained in the cloud increasingly need to be run at the edge. Edge TPU is Google’s purpose-built ASIC designed to run AI at the edge. It delivers high performance in a small physical and power footprint, enabling the deployment of high-accuracy AI at the edge.</p>
</blockquote>
 
<p>Other references are:<br>
<a href="https://mp.weixin.qq.com/s/b22p26_delWfSpy9kDJKhA">Google TPU3 看点</a><br><br>
<a href="https://mp.weixin.qq.com/s/Kf_L4u7JRxJ8kF3Pi8M5iw">Google TPU 揭密</a><br><br>
<a href="https://mp.weixin.qq.com/s/lBQyNSNa6-joeLZ_Kq2W8A">Google的神经网络处理器专利</a><br><br>
<a href="https://mp.weixin.qq.com/s/g-BDlvSy-cx4AKItcWF7jQ">脉动阵列 - 因Google TPU获得新生</a><br><br>
<a href="https://www.linkedin.com/pulse/should-we-all-embrace-systolic-arrays-chien-ping-lu">Should We All Embrace Systolic Arrays?</a><br></p>

<p><a name="Amazon_AWS"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Amazon_AWS.png" height="50" loading="lazy" alt="Amazon AWS" /></div>

<p><strong><a href="https://aws.amazon.com/blogs/aws/amazon-ec2-trn2-instances-and-trn2-ultraservers-for-aiml-training-and-inference-is-now-available/">Amazon EC2 Trn2 Instances and Trn2 UltraServers</a></strong></p>
<blockquote>
  <p>Powered by AWS Trainium2, Trn2 instances target generative AI training and inference with large HBM capacity and NeuronLink chip-to-chip interconnect. AWS positions Trn2 for strong price/performance vs. GPU instances; UltraServers scale to dozens of Trainium2 chips.</p>
</blockquote>

<p><a href="https://aws.amazon.com/ec2/instance-types/inf2/">Amazon EC2 Inf2 (Inferentia2)</a></p>
<blockquote>
  <p>Inferentia2-powered Inf2 instances improve throughput and latency for large-model inference vs. first-generation Inferentia, with multi-chip scale-out via NeuronLink.</p>
</blockquote>

<p><strong><a href="https://aws.amazon.com/cn/machine-learning/trainium/">AWS Trainium</a></strong></p>
<blockquote>
  <p>AWS Trainium is the second custom machine learning (ML) chip designed by AWS that provides the best price performance for training deep learning models in the cloud.  Trainium offers the highest performance with the most teraflops (TFLOPS) of compute power for the fastest ML training in Amazon EC2 and enables a broader set of ML applications. The Trainium chip is specifically optimized for deep learning training workloads for applications including image classification, semantic search, translation, voice recognition, natural language processing and recommendation engines.</p>
</blockquote>

<p><a href="https://aws.amazon.com/cn/machine-learning/inferentia/">AWS Inferentia. High performance machine learning inference chip, custom designed by AWS.</a></p>
<blockquote>
  <p>AWS Inferentia provides high throughput, low latency inference performance at an extremely low cost. Each chip provides hundreds of TOPS (tera operations per second) of inference throughput to allow complex models to make fast predictions. For even more performance, multiple AWS Inferentia chips can be used together to drive thousands of TOPS of throughput. AWS Inferentia will be available for use with Amazon SageMaker, Amazon EC2, and Amazon Elastic Inference.</p>
</blockquote>

<p><a name="Microsoft"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Microsoft_logo.png" height="60" loading="lazy" alt="Microsoft" /></div>

<p><strong><a href="https://azure.microsoft.com/en-us/blog/azure-maia-for-the-era-of-ai-from-silicon-to-software-to-systems/">Azure Maia for the era of AI: From silicon to software to systems</a></strong></p>
<blockquote>
  <p>Microsoft’s first in-house AI accelerator, Azure Maia 100 (5nm, advanced packaging), is co-designed for Azure AI / Copilot-class cloud workloads, with a software stack integrating PyTorch and ONNX Runtime.</p>
</blockquote>

<p><a name="OpenAI"></a></p>
<div align="center"><h3>OpenAI</h3></div>

<p><strong><a href="https://openai.com/index/openai-broadcom-jalapeno-inference-chip/">OpenAI and Broadcom unveil Jalapeño LLM inference chip</a></strong> · <a href="https://techcrunch.com/2026/06/24/openai-unveils-its-first-custom-chip-built-by-broadcom/">TechCrunch coverage</a></p>
<blockquote>
  <p>Jun 2026 — OpenAI’s first custom “Intelligence Processor,” Jalapeño, is an inference-optimized ASIC co-developed with Broadcom (networking + silicon implementation) for lower-cost, higher-utilization LLM serving. First step in a multi-generation platform with initial deployments targeted by end of 2026.</p>
</blockquote>

<p><a href="https://openai.com/index/openai-and-broadcom-announce-strategic-collaboration/">OpenAI–Broadcom 10 GW accelerator collaboration</a></p>

<p><a name="Anthropic"></a></p>
<div align="center"><h3>Anthropic</h3></div>

<p><strong><a href="https://www.anthropic.com/news/google-broadcom-partnership-compute">Anthropic expands partnership with Google and Broadcom for next-generation compute</a></strong></p>
<blockquote>
  <p>Apr 2026 — Expanded agreement for multiple gigawatts of next-generation Google TPU capacity (Broadcom SEC filings cite ~3.5 GW), expected online from 2027, on top of prior &gt;1 GW TPU commitments. Anthropic emphasizes a multi-hardware strategy: AWS Trainium (incl. Project Rainier), Google TPUs, and NVIDIA GPUs.</p>
</blockquote>

<p><a href="https://techcrunch.com/2026/04/07/anthropic-compute-deal-google-broadcom-tpus/">TechCrunch: Anthropic ups compute deal with Google and Broadcom</a> ·
<a href="https://www.cnbc.com/2025/10/23/anthropic-google-cloud-deal-tpu.html">CNBC: Oct 2025 Google TPU cloud deal</a></p>

<p><a name="Apple"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Apple_logo.png" height="60" loading="lazy" alt="Apple" /></div>

<p><strong><a href="https://www.apple.com/newsroom/2025/10/apple-unleashes-m5-the-next-big-leap-in-ai-performance-for-apple-silicon/">Apple unleashes M5, the next big leap in AI performance for Apple silicon</a></strong></p>
<blockquote>
  <p>Oct 2025 — M5 (3nm) adds Neural Accelerators in each GPU core and a faster 16-core Neural Engine, targeting on-device Apple Intelligence and local AI workloads across MacBook Pro, iPad Pro, and Vision Pro.</p>
</blockquote>

<p><strong><a href="https://www.apple.com/newsroom/2026/03/apple-debuts-m5-pro-and-m5-max-to-supercharge-the-most-demanding-pro-workflows/">Apple debuts M5 Pro and M5 Max</a></strong></p>
<blockquote>
  <p>Mar 2026 — Fusion Architecture scales GPU AI compute and unified memory bandwidth (up to 128GB / ~614GB/s on M5 Max) for local LLM prompt processing and pro creative AI workflows.</p>
</blockquote>

<p><a href="https://www.apple.com/newsroom/2024/05/apple-introduces-m4-chip/">Apple introduces M4 chip</a></p>
<blockquote>
  <p>May 2024 — M4 Neural Engine up to ~38 TOPS, with CPU ML accelerators and high-bandwidth unified memory for on-device AI on iPad Pro and later Macs.</p>
</blockquote>

<p><a name="Alibaba"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/alibaba_logo.png" height="60" loading="lazy" alt="Alibaba" /></div>

<p><strong><a href="https://www.eetimes.com/alibaba-unveils-own-ai-chip-mounting-direct-challenge-to-nvidia/">Alibaba Unveils Own AI Chip, Mounting Direct Challenge to Nvidia</a></strong></p>
<blockquote>
  <p>Sep 2025 — Alibaba’s T-Head Parallel Processing Unit (PPU / Zhenwu family) targets cloud AI training and inference as a domestic alternative under export-control constraints. Reports cite ~96GB HBM2e-class memory and high chip-to-chip bandwidth; deployed in large China Unicom / Alibaba Cloud clusters.</p>
</blockquote>

<p><a href="https://www.alibabacloud.com/blog/alibaba-unveils-new-ai-chip-flagship-model-and-rebuilt-cloud-stack-ai-for-agentic-era_603151">Alibaba Cloud Summit: Zhenwu M890 and agentic AI stack</a></p>
<blockquote>
  <p>T-Head’s newer Zhenwu-class accelerators (e.g. M890 messaging) emphasize larger on-package memory, low-precision formats (down to FP4), and cluster interconnect / SAIL software for agentic cloud workloads.</p>
</blockquote>

<p><a href="https://medium.com/syncedreview/alibabas-new-ai-chip-can-process-nearly-80k-images-per-second-63412dec22a3">Alibaba’s Hanguang 800</a> (historical, 2019)</p>
<blockquote>
  <p>Pingtouge / T-Head’s first AI inference ASIC, highlighted for high images-per-second inference throughput at Apsara Conference 2019.</p>
</blockquote>

<p><a name="Tencent_Cloud"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tencent_Cloud_logo.png" height="30" loading="lazy" alt="Tencent Cloud" /></div>

<p><a href="https://www.datacenterdynamics.com/en/news/tencent-reveals-three-data-center-chips-for-ai-video-transcoding-and-networking/">Tencent reveals three data center chips - for AI, video transcoding, and networking</a></p>
<blockquote>
  <p>The company claims that the Zixiao AI chip is twice as good as comparable competing products, video transcoding chip Canghai was 30 percent better, and SmartNIC Xuanling was apparently four times as good. It did not provide external benchmarks or specific product details.</p>
</blockquote>

<p><br />
<a name="Baidu"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Baidu_logo.png" height="40" loading="lazy" alt="Baidu" /></div>

<p><strong><a href="https://www.reuters.com/technology/baidu-says-2nd-gen-kunlun-ai-chips-enter-mass-production-2021-08-18/">Baidu Kunlun / Kunlunxin AI accelerators</a></strong></p>
<blockquote>
  <p>Baidu’s Kunlunxin line (Kunlun chips) continues as a domestic cloud/training &amp; inference option alongside hyperscaler custom silicon. 2nd-gen Kunlun entered mass production in 2021; later generations target large-model clusters inside China.</p>
</blockquote>

<p><a href="https://www.reuters.com/technology/baidu-says-2nd-gen-kunlun-ai-chips-enter-mass-production-2021-08-18/">Baidu says 2nd-gen Kunlun AI chips enter mass production</a> (2021)</p>
<blockquote>
  <p>Early mass-production milestone for Baidu’s second-generation Kunlun AI chips.</p>
</blockquote>

<p><a name="Fujitsu"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Fujitsu_logo.png" height="40" loading="lazy" alt="Fujitsu" /></div>

<blockquote>
  <p>This <a href="https://www.nextplatform.com/2017/08/09/fujitsu-bets-deep-leaning-hpc-divergence/">DLU that Fujitsu is creating</a> is done from scratch, and it is not based on either the Sparc or ARM instruction set and, in fact, it has its own instruction set and a new data format specifically for deep learning, which were created from scratch. 
  Japanese computing giant Fujitsu. Which knows a thing or two about making a very efficient and highly scalable system for HPC workloads, as evidenced by the K supercomputer, does not believe that the HPC and AI architectures will converge. Rather, the company is banking on the fact that these architectures will diverge and will require very specialized functions. </p>
</blockquote>

<p><a name="Nokia"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Nokia_logo.png" height="30" loading="lazy" alt="Nokia" /></div>

<blockquote>
  <p>Nokia has developed the <a href="https://networks.nokia.com/5g/reefshark">ReefShark chipsets</a> for its 5G network solutions. AI is implemented in the ReefShark design for radio and embedded in the baseband to use augmented deep learning to trigger smart, rapid actions by the autonomous, cognitive network, enhancing network optimization and increasing business opportunities.</p>
</blockquote>

<p><a name="Facebook"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/facebook_logo.png" height="50" loading="lazy" alt="Meta" /></div>

<p><strong><a href="https://ai.meta.com/blog/next-generation-meta-training-inference-accelerator-AI-MTIA/">Our next generation Meta Training and Inference Accelerator (MTIA)</a></strong></p>
<blockquote>
  <p>Meta’s custom MTIA family targets ranking/recommendation and broader AI workloads. Newer generations expand coverage toward GenAI inference and training, complementing GPU capacity in Meta’s AI infrastructure.</p>
</blockquote>

<p><strong><a href="https://ai.meta.com/blog/meta-mtia-scale-ai-chips-for-billions/">Four MTIA Chips in Two Years: Scaling AI Experiences for Billions</a></strong></p>
<blockquote>
  <p>Meta describes a multi-generation MTIA roadmap (including MTIA 300–500 class chips) with modular chiplet designs and accelerating deployment cadence through 2026–2027.</p>
</blockquote>

<p><a href="https://www.reuters.com/technology/facebook-developing-machine-learning-chip-information-2021-09-09/">Facebook developing machine learning chip - The Information</a> (historical, 2021)</p>
<blockquote>
  <p>Early reporting on Meta/Facebook’s in-house ML chip efforts for recommendation workloads.</p>
</blockquote>

<p><a name="Tesla"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tesla_logo.png" height="60" loading="lazy" alt="Tesla" /></div>

<p><strong><a href="https://electrek.co/2026/04/15/tesla-ai5-chip-taped-out-musk-ai6-dojo3/">Tesla AI5 chip taped out</a></strong></p>
<blockquote>
  <p>Apr 2026 — Elon Musk announced Tesla’s next-generation AI5 inference/training SoC has taped out, with AI6 / Dojo3 also mentioned as in progress. Volume production and broad vehicle deployment remain gated (reports point to mid–late 2027+); near-term vehicles continue on AI4 / interim upgrades, while AI5 is also positioned for Optimus and internal clusters.</p>
</blockquote>

<p><a href="https://www.trendforce.com/news/2026/07/13/news-samsung-reportedly-completes-tesla-ai5-tape-out-paving-the-way-for-2nm-ramp-at-taylor-fab/">TrendForce: Samsung foundry path for AI5 / Taylor 2nm messaging</a></p>

<p><strong><a href="https://www.forbes.com/sites/jamesmorris/2022/10/06/teslas-biggest-news-at-ai-day-was-the-dojo-supercomputer-not-the-optimus-robot/">Tesla AI Day — Dojo supercomputer</a></strong> (historical)</p>
<blockquote>
  <p>Elon Musk played AI Day to the crowd with the focus on the Optimus humanoid robot. But while this could have a huge impact on our lives and society if it does enter mass production at the price Musk suggested ($20,000), another part of the presentation will have more immediate effects. That was the status report on the Dojo supercomputer. It could really change the world much more quickly than a bipedal bot.</p>
</blockquote>

<p><a href="https://semianalysis.com/tesla-dojo-ai-super-computer-unique-packaging-and-chip-design-allow-an-order-magnitude-advantage-over-competing-ai-hardware/">Tesla Dojo – Unique Packaging and Chip Design Allow An Order Magnitude Advantage Over Competing AI Hardware</a></p>
<blockquote>
  <p>Tesla hosted their AI Day and revealed the innerworkings of their software and hardware infrastructure. Part of this reveal was the previously teased Dojo AI training chip. Tesla claims their D1 Dojo chip has a GPU level compute, CPU level flexibility, with networking switch IO. </p>
</blockquote>

<div align="center" class="section-title"><h2><a name="IP_Vendors"></a>III. Traditional IP Vendors</h2></div>

<hr class="section-rule" />

<p><a name="ARM"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/ARM_logo.png" height="30" loading="lazy" alt="Arm" /></div>

<p><strong><a href="https://www.arm.com/products/silicon-ip-cpu/ethos/ethos-u85">Arm Ethos-U85</a></strong> — third-generation Ethos-U micro-NPU</p>
<blockquote>
  <p>Scales from 128–2048 MACs (up to ~4 TOPS @ 1 GHz) with native transformer operator support for edge / IoT generative and vision models; ~20% more energy efficient than Ethos-U65 and pairs with Cortex-M or Cortex-A hosts (Corstone-320 reference). Same Ethos toolchain / Vela compiler path as prior U-series.</p>
</blockquote>

<p><a href="https://newsroom.arm.com/news/iot-reference-design-platform-2024">Arm newsroom: Ethos-U85 + Corstone-320 IoT reference platform</a></p>

<p><strong><a href="https://www.arm.com/products/silicon-ip-cpu/ethos/ethos-n78">Ethos-N78</a></strong> (legacy application-class NPU)</p>
<blockquote>
  <p>Second-generation Ethos-N series for immersive edge inference; single-core performance scalable from ~1 to 10+ TOPS via many-core configurations (historical product line still referenced in many SoCs).</p>
</blockquote>

<p><a href="https://www.anandtech.com/show/12791/arm-details-project-trillium-mlp-architecture">ARM Details "Project Trillium" Machine Learning Processor Architecture</a> (historical)</p>

<p><a name="Synopsys"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Synopsys_logo.png" height="40" loading="lazy" alt="Synopsys" /></div>

<p><strong><a href="https://news.synopsys.com/2022-04-19-Synopsys-Introduces-Industrys-Highest-Performance-Neural-Processor-IP">Synopsys Introduces Industry's Highest Performance Neural Processor IP</a></strong></p>
<blockquote>
  <p>New DesignWare ARC NPX6 NPU IP Delivers Up to 3,500 TOPS Performance for Automotive, Consumer and Data Center Chip Designs</p>
</blockquote>

<p><a name="Imagination"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Imagination_logo.png" height="60" loading="lazy" alt="Imagination" /></div>

<p><a href="https://www.imaginationtech.com/products/ai/">AI Processors</a></p>
<blockquote>
  <p>Whether you want smartness residing in the palm of your hand, consumer products or industrial robots, or enabled by powerful servers in the cloud, we can help you achieve your vision. We enable the smartness in your products with our PowerVR Neural Network Accelerators (NNA) and GPUs. Our NC-SDK enables seamless deployment of AI acceleration on either our hardware IP either in isolation or combined. Our NNA provides maximum efficiency with a scalable architecture which enables a wide range of smart edge and end point devices from low performance IoT to high performance RoboTaxi.</p>
</blockquote>

<p><a name="CEVA"></a></p>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/CEVA_logo.png" height="40" loading="lazy" alt="CEVA" /></div>

<p><a href="https://www.ceva-dsp.com/app/deep-learning/">Deep learning for the real-time embedded world</a></p>
<blockquote>
  <p>One solution lies in supplying a dedicated low power AI processor for Deep Learning at the edge, combined with a deep neural network (DNN) graph compiler</p>
</blockquote>

<p><a name="Cadence"></a></p>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cadence_logo.png" height="40" loading="lazy" alt="Cadence" /></div>

<p><a href="https://www.cadence.com/en_US/home/tools/ip/tensilica-ip/tensilica-ai-platform.html">Tensilica AI Platform</a></p>

<p><a name="VeriSilicon"></a></p>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/VeriSilicon_logo.png" height="40" loading="lazy" alt="VeriSilicon" /></div>

<p><a href="https://www.verisilicon.com/en/IPPortfolio/VivanteNPUIP">Vivante® NPU IP</a></p>
<blockquote>
  <p>VeriSilicon's Neural Network Processor (NPU) IP is a highly scalable, programmable computer vision and artificial intelligence processor that supports AI operations upgrades for endpoints, edge devices, and cloud devices. Designed to meet a variety of chip sizes and power budgets, the Vivante NPU IP is a cost-effective, high-quality neural network acceleration engine solution.</p>
</blockquote>

<div align="center" class="section-title"><h2><a name="Startups"></a>IV. Startups</h2></div>

<hr class="section-rule" />

<p><a name="Cerebras"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.cerebras.net/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cerebras_logo.png" height="50" loading="lazy" alt="Cerebras" /></a></div>

<p><strong><a href="https://www.cerebras.net/press-release/cerebras-announces-third-generation-wafer-scale-engine">Cerebras Systems Unveils World’s Fastest AI Chip with 4 Trillion Transistors (WSE-3)</a></strong></p>
<blockquote>
  <p>March 2024 — WSE-3 (5nm) powers the CS-3 system with ~900,000 AI-optimized cores and 125 petaflops peak AI performance, doubling WSE-2 performance at the same power/price point for large-model training and high-throughput inference.</p>
</blockquote>

<p><strong><a href="https://www.cerebras.net/press-release/cerebras-unveils-andromeda-a-13.5-million-core-ai-supercomputer-that-delivers-near-perfect-linear-scaling-for-large-language-models">Cerebras Unveils Andromeda, a 13.5 Million Core AI Supercomputer that Delivers Near-Perfect Linear Scaling for Large Language Models</a></strong></p>
<blockquote>
  <p>Delivering more than 1 Exaflop of AI compute and 120 Petaflops of dense compute, Andromeda is one of the largest AI supercomputers ever built, and is dead simple to use</p>
</blockquote> 

<p><a href="https://www.cerebras.net/blog/cerebras-sets-record-for-largest-ai-models-ever-trained-on-single-device">Cerebras Sets Record for Largest AI Models Ever Trained on Single Device</a></p>
<blockquote>
  <p>We are announcing the largest models ever trained on a single device. Using the Cerebras Software Platform (CSoft), our customers can easily train state-of-the-art GPT language models (such as GPT-3[i] and GPT-J[ii]) with up to 20 billion parameters on a single CS-2 system. Running on a single CS-2, these models take minutes to set up and users can quickly move between models with just a few keystrokes. With clusters of GPUs, this takes months of engineering work.</p>
</blockquote> 
 
<p><a href="https://www.anandtech.com/show/17061/cerebras-completes-series-f-funding-another-250m-for-4b-valuation">Cerebras Completes Series F Funding, Another $250M for $4B Valuation</a></p>
<blockquote>
  <p>The new Series F funding round nets the company another $250m in capital, bringing the total raised through venture capital up to $720 million.</p>
</blockquote> 
 
<p><a href="https://www.anandtech.com/show/16626/cerebras-unveils-wafer-scale-engine-two-wse2-26-trillion-transistors-100-yield">Cerebras Unveils Wafer Scale Engine Two (WSE2): 2.6 Trillion Transistors, 100% Yield</a></p>
<blockquote>
  <p>Two years ago Cerebras unveiled a revolution in silicon design: a processor as big as your head, using as much area on a 12-inch wafer as a rectangular design would allow, built on 16nm, focused on both AI as well as HPC workloads. Today the company is launching its second generation product, built on TSMC 7nm, with more than double the cores and more than double of everything.</p>
</blockquote>

<p><a href="https://techcrunch.com/2019/11/19/the-cerebras-cs-1-computes-deep-learning-ai-problems-by-being-bigger-bigger-and-bigger-than-any-other-chip/">The Cerebras CS-1 computes deep learning AI problems by being bigger, bigger, and bigger than any other chip</a></p>
<blockquote>
  <p>Today, the company announced the launch of its end-user compute product, the Cerebras CS-1, and also announced its first customer of Argonne National Laboratory.</p>
</blockquote>

<p><a name="Graphcore"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.graphcore.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Graphcore_logo.png" height="70" loading="lazy" alt="Graphcore" /></a></div>

<p><strong><a href="https://www.graphcore.ai/posts/graphcore-joins-softbank-group-to-build-next-generation-of-ai-compute">Graphcore joins SoftBank Group to build next generation of AI compute</a></strong></p>
<blockquote>
  <p>Jul 2024 — SoftBank acquired Graphcore as a wholly owned subsidiary (terms undisclosed; press estimates ~$500M). Graphcore continues under its own brand, with SoftBank backing next-generation IPU / AI compute development (including SoftBank-ecosystem follow-on investment reporting into 2026).</p>
</blockquote>

<p><a href="https://www.reuters.com/technology/artificial-intelligence/japans-softbank-acquires-british-ai-chipmaker-graphcore-2024-07-11/">Reuters: SoftBank acquires Graphcore</a></p>

<p><strong><a href="https://www.eetimes.com/graphcore-supercharges-ipu-with-wafer-on-wafer/">Graphcore Supercharges IPU with Wafer-on-Wafer</a></strong> (historical)</p>
<blockquote>
  <p>Graphcore unveiled its third-generation intelligence processing unit (IPU), the first processor to be built using 3D wafer-on-wafer (WoW) technology.</p>
</blockquote>
 
<p><a href="https://www.graphcore.ai/mk2-benchmarks">MK2 PERFORMANCE BENCHMARKS</a></p>

<p><a href="https://techcrunch.com/2020/02/24/graphcore-the-ai-chipmaker-raises-another-150m-at-a-1-95b-valuation/">Graphcore, the AI chipmaker, raises another $150M at a $1.95B valuation</a></p>
<blockquote>
  <p>Graphcore, the Bristol-based startup that designs processors specifically for artificial intelligence applications, announced it has raised another $150 million in funding for R&D and to continue bringing on new customers. It’s valuation is now $1.95 billion.</p>
</blockquote>

<p><a href="https://mp.weixin.qq.com/s/CH9h8dUtoNK_2ZfkK5YU0g">解密又一个xPU：Graphcore的IPU</a> give some analysis on its IPU architecture.</p>
<p><a href="https://mp.weixin.qq.com/s/AMuqeaShqEv3DnibH3scEA">Graphcore AI芯片：更多分析</a> More analysis.</p>
<p><a href="https://mp.weixin.qq.com/s/qP0zsSA7SQWXDqWGEAXmOg">深度剖析AI芯片初创公司Graphcore的IPU</a> In-depth analysis after more information was disclosed.</p>

<p><a name="Tenstorrent"></a></p>

<div align="center" class="vendor-logo"><a href="http://tenstorrent.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tenstorrent_logo.png" height="100" loading="lazy" alt="Tenstorrent" /></a></div>

<p><strong><a href="https://tenstorrent.com/">Tenstorrent Blackhole / Wormhole AI processors</a></strong></p>
<blockquote>
  <p>Tenstorrent builds RISC-V based AI computers (Wormhole, Blackhole) with an open software stack, targeting datacenter and edge deployments under Jim Keller’s architecture leadership.</p>
</blockquote>

<p><a href="https://www.prnewswire.com/news-releases/tenstorrent-raises-over-200-million-at-1-billion-valuation-to-create-programmable-high-performance-ai-computers-301295913.html">Tenstorrent Raises over $200 million at $1 billion Valuation to Create Programmable, High Performance AI Computers</a></p>
<blockquote>
  <p>TORONTO, May 20, 2021 /PRNewswire/ - Tenstorrent, a hardware start-up developing next generation computers, announced today that it has raised over $200 million in a recent funding round that values the company at $1 billion. The round was led by Fidelity Management and Research Company and includes additional investments from Eclipse Ventures, Epic CG and Moore Capital. </p>
</blockquote> 
 
<p><a href="https://www.anandtech.com/show/16709/an-interview-with-tenstorrent-ceo-ljubisa-bajic-and-cto-jim-keller">An Interview with Tenstorrent: CEO Ljubisa Bajic and CTO Jim Keller</a></p>
 

<p><a name="Blaize"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.blaize.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Blaize_logo.png" height="40" loading="lazy" alt="Blaize" /></a></div>

<p><a href="https://www.eetimes.com/automotive-ai-startup-blaize-closes-71-million-funding-round/">Automotive AI Startup Blaize Closes $71 Million Funding Round</a></p>
<blockquote>
  <p>Blaize, formerly ThinCI, has closed a Series D round of funding at $71 million. New investor Franklin Templeton and existing investor Temasek led the round, along with participation from Denso and other new and existing investors. This round brings Blaize’s total funding to around $155 million total.</p>
</blockquote>

<p><a name="Koniku"></a></p>

<div align="center" class="vendor-logo"><a href="http://koniku.io/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Koniku_logo.png" height="50" loading="lazy" alt="Koniku" /></a></div>

<blockquote>
  <p>Founded in 2014, Newark, California startup <a href="http://koniku.io/">Koniku</a> has taken in $1.65 million in funding so far to become “the world’s first neurocomputation company“. The idea is that since the brain is the most powerful computer ever devised, why not reverse engineer it? Simple, right? Koniku is actually integrating biological neurons onto chips and has made enough progress that they claim to have AstraZeneca as a customer. Boeing has also signed on with a letter of intent to use the technology in chemical-detecting drones.</p>
</blockquote>

<p><a name="Adapteva"></a></p>

<div align="center" class="vendor-logo"><a href="http://www.adapteva.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Adapteva_logo.png" height="70" loading="lazy" alt="Adapteva" /></a></div>

<p><a href="http://www.adapteva.com/">Adapteva</a> has taken in $5.1 million in funding from investors that include mobile giant Ericsson. <a href="http://www.parallella.org/docs/e5_1024core_soc.pdf">The paper "Epiphany-V: A 1024 processor 64-bit RISC System-On-Chip"</a> describes the design of Adapteva's 1024-core processor chip in 16nm FinFet technology. </p>

<p><a name="Mythic"></a></p>

<div align="center" class="vendor-logo"><a href="https://mythic.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Mythic_logo.png" height="20" loading="lazy" alt="Mythic" /></a></div>

<p><strong><a href="https://www.businesswire.com/news/home/20251217546249/en/Mythic-to-Challenge-AIs-GPU-Pantheon-with-100x-Energy-Advantage-and-Oversubscribed-%24125M-Raise">Mythic raises $125M Series D for analog AI compute</a></strong></p>
<blockquote>
  <p>Dec 2025 — Oversubscribed round led by DCVC (strategic participation including Honda and Lockheed Martin) to scale Mythic’s Analog Processing Units (APUs) — flash-based compute-in-memory for energy-efficient inference at the edge and in data centers. Roadmap emphasizes chiplet-based next-gen APUs for robotics, automotive, and defense.</p>
</blockquote>

<p><strong><a href="https://mythic.ai/whats-new/mythic-acquires-videantis-one-of-europes-leading-digital-processor-ip-companies-to-build-the-worlds-most-energy-efficient-ai-compute-platform/">Mythic acquires Videantis for hybrid analog/digital AI platform</a></strong></p>
<blockquote>
  <p>May 2026 — Acquisition of Videantis GmbH adds a production digital processor IP + software stack alongside Mythic’s analog in-memory compute, targeting a hybrid platform with large claimed efficiency gains vs. conventional GPU inference.</p>
</blockquote>

<p><a href="https://mythic.ai/products/m1076-analog-matrix-processor/">M1076 Analog Matrix Processor</a> (shipping product context) ·
<a href="https://venturebeat.com/2021/06/07/mythic-launches-analog-ai-processor-that-consumes-10-times-less-power/">VentureBeat: M1076 launch</a> (historical)</p>

<p><a name="Brainchip"></a></p>

<div align="center" class="vendor-logo"><a href="http://www.brainchipinc.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Brainchip_logo.png" height="40" loading="lazy" alt="BrainChip" /></a></div>

<p><a href="https://venturebeat.com/2022/01/18/brainchip-launches-neuromorphic-process-for-ai-at-the-edge/">BrainChip launches neuromorphic process for AI at the edge</a> </p>
<blockquote>
  <p>BrainChip today announced the commercialization of its Akida neural networking processor. Aimed at a variety of edge and internet of things (IoT) applications, BrainChip claims to be the first commercial producer of neuromorphic AI chips, which could deliver benefits in ultra-low power and performance over conventional approaches.</p>
</blockquote>

<p><a name="Deepvision"></a></p>

<div align="center" class="vendor-logo"><a href="https://deepvision.io/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Deepvision_logo.png" height="40" loading="lazy" alt="Deep Vision" /></a></div>

<p><a href="https://www.businesswire.com/news/home/20210928005270/en/AI-Processor-Chipmaker-Deep-Vision-Raises-35-Million-in-Series-B-Funding">AI Processor Chipmaker Deep Vision Raises $35 Million in Series B Funding</a></p>
<blockquote>
  <p>Tiger Global Leads Series B Financing, Enabling Deep Vision to Expand Video Analytics and Natural Language Processing Capabilities in Edge Computing Applications</p>
</blockquote>

<p><a name="Groq"></a></p>

<div align="center" class="vendor-title"><h3><a href="https://groq.com/">Groq</a></h3></div>

<p><strong><a href="https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Vera-Rubin-Opens-Agentic-AI-Frontier/default.aspx">NVIDIA Vera Rubin Opens Agentic AI Frontier (includes Groq LPU)</a></strong></p>
<blockquote>
  <p>In late 2025 NVIDIA licensed Groq’s LPU technology and brought on key engineering talent. At GTC 2026, NVIDIA described integrating Groq-class LPU engines into the Vera Rubin AI factory stack for low-latency / high-efficiency token generation alongside Rubin GPUs.</p>
</blockquote>

<p><strong><a href="https://www.eetimes.com/groq-demos-fast-llms-on-4-year-old-silicon/">Groq Demonstrates Fast LLMs on 4-Year-Old Silicon</a></strong></p>
<blockquote>
  <p>MOUNTAIN VIEW, CALIF. — Groq has repositioned its first-generation AI inference chip as a language processing unit (LPU), and demonstrated Meta’s Llama-2 70-billion–parameter large language model (LLM) running inference at 240 tokens per second per user. Groq CEO Jonathan Ross told EE Times that the company had Llama-2 up and running on the company’s 10-rack (64-chip) cloud-based dev system in “a couple of days.” This system is based on the company’s first gen AI silicon, released four years ago.</p>
</blockquote>

<p><a href="https://www.forbes.com/sites/amyfeldman/2021/04/14/ai-chip-startup-groq-founded-by-ex-googlers-raises-300-million-to-power-autonomous-vehicles-and-data-centers/">AI Chip Startup Groq, Founded By Ex-Googlers, Raises $300 Million To Power Autonomous Vehicles And Data Centers</a></p>
<blockquote>
  <p>Jonathan Ross left Google to launch next-generation semiconductor startup Groq in 2016. Today, the Mountain View, California-based firm said that it had raised $300 million led by Tiger Global Management and billionaire investor Dan Sundheim’s D1 Capital as it officially launched into public view. </p>
</blockquote>

<p><a name="Kneron"></a></p>

<div align="center" class="vendor-logo"><a href="http://www.kneron.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Kneron_logo.png" height="60" loading="lazy" alt="Kneron" /></a></div>

<p><a href="https://www.prnewswire.com/news-releases/kneron-to-accelerate-edge-ai-development-with-more-than-10-million-usd-series-a-financing-300556674.html">Kneron to Accelerate Edge AI Development with more than 10 Million USD Series A Financing</a></p>

<p><a name="GTI"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.gyrfalcontech.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/GTI_Logo.png" height="40" loading="lazy" alt="Gyrfalcon" /></a></div>

<p>According to this article, <a href="https://www.prnewswire.com/news-releases/gyrfalcon-offers-automotive-ai-chip-technology-300860069.html">"Gyrfalcon offers Automotive AI Chip Technology"</a></p>

<blockquote>
  <p>Gyrfalcon Technology Inc. (GTI), has been promoting matrix-based application specific chips for all forms of AI since offering their production versions of AI accelerator chips in September 2017. Through the licensing of its proprietary technology, the company is confident it can help automakers bring highly competitive AI chips to production for use in vehicles within 18 months, along with significant gains in AI performance, improvements in power dissipation and cost advantages.</p>
</blockquote>

<p><a name="SambaNova"></a></p>

<div align="center" class="vendor-logo"><a href="https://sambanova.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/SambaNova_logo.png" height="40" loading="lazy" alt="SambaNova" /></a></div>

<p><strong><a href="https://sambanova.ai/press/sambanova-unveils-fastest-chip-for-agentic-ai-collaborates-with-intel-and-raises-350m">SambaNova unveils SN50 RDU for agentic AI, Intel collaboration, $350M+ Series E</a></strong></p>
<blockquote>
  <p>Feb 2026 — Fifth-generation Reconfigurable Dataflow Unit (SN50) targets large-scale agentic inference (vendor claims up to ~5× compute and ~4× network bandwidth vs. SN40L; scales toward 256 accelerators). SoftBank named as an early deploy partner; shipping targeted for H2 2026. Planned multi-year collaboration with Intel for heterogeneous inference stacks; oversubscribed Series E led with Vista / Cambium participation including Intel Capital.</p>
</blockquote>

<p><a href="https://sambanova.ai/blog/introducing-the-sn50-rdu-purpose-built-for-agentic-inference">Introducing the SN50 RDU</a> ·
<a href="https://sambanova.ai/products/rdu-ai-chips">RDU product page</a></p>

<p><strong><a href="https://venturebeat.com/ai/sambanova-unveils-new-ai-chip-to-power-full-stack-ai-platform/">SN40L RDU powers SambaNova Suite</a></strong> (prior gen)</p>
<blockquote>
  <p>Fourth-generation SN40L RDU with three-tier memory (SRAM / HBM / DRAM) for full-stack LLM platforms — still the primary shipping generation ahead of SN50.</p>
</blockquote>

<p><a href="https://techcrunch.com/2021/04/13/sambanova-raises-676m-at-a-5-1b-valuation-to-double-down-on-cloud-based-ai-software-for-enterprises/">Series D funding context</a> (historical) ·
<a href="https://sambanova.ai/articles/introducing-sambanova-systems-datascale-a-new-era-of-computing/">DataScale systems</a></p>

<p><a name="GreenWaves"></a></p>
<div align="center" class="vendor-logo"><a href="https://greenwaves-technologies.com/en/greenwaves-technologies-2/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/GreenWaves_logo.png" height="50" loading="lazy" alt="GreenWaves" /></a></div>

<p><a href="https://www.eetimes.eu/greenwaves-shows-off-advanced-audio-demos/">GreenWaves Shows Off Advanced Audio Demos</a></p>
<blockquote>
  <p>The Gap9 processor, a successor to Gap8 which targets computer vision in IoT devices, is an ultra-low power neural network processor suitable for battery-powered devices. GreenWaves’ vice president of marketing Martin Croome told EE Times Europe that the company decided to focus Gap9 on the hearables market after receiving traction from this sector for Gap8.</p>
</blockquote>

<p><a name="Lightelligence"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.lightelligence.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Lightelligence_logo.png" height="60" loading="lazy" alt="Lightelligence" /></a></div>

<p><strong><a href="https://www.eetimes.com/optical-computing-chip-runs-hardest-math-problems-100x-faster-than-gpus/">Optical Chip Solves Hardest Math Problems Faster than GPUs</a></strong></p>
<blockquote>
  <p>Optical computing startup Lightelligence has demonstrated a silicon photonics accelerator running the Ising problem more than 100 times faster than a typical GPU setup.</p>
</blockquote>

<p><a name="Lightmatter"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.lightmatter.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Lightmatter_logo.png" height="50" loading="lazy" alt="Lightmatter" /></a></div>

<p><a href="https://www.eetimes.com/lightmatter-raises-more-funding-for-photonic-ai-chip/">Lightmatter Raises More Funding for Photonic AI Chip</a></p>
<blockquote>
  <p>ightmatter, the MIT spinout building AI accelerators with a silicon photonics computing engine, announced a Series B funding round, raising an additional $80 million. The company’s technology is based on proprietary silicon photonics technology which manipulates coherent light inside a chip to perform calculations very quickly while using very little power</p>
</blockquote>

<p><a name="Hailo"></a></p>

<div align="center" class="vendor-logo"><a href="https://hailo.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Hailo_logo.png" height="60" loading="lazy" alt="Hailo" /></a></div>

<p><strong><a href="https://hailo.ai/company-overview/newsroom/news/hailo-announces-general-availability-of-hailo-10h-edge-ai-accelerator-with-generative-ai-capabilities/">Hailo-10H generally available for edge generative AI</a></strong></p>
<blockquote>
  <p>Jul 2025 — Second-generation Hailo-10H brings on-device LLM / VLM / GenAI capabilities to the edge (~40 TOPS INT4 class, ~2.5W typical), while retaining vision workloads from the Hailo-8 generation. Automotive-qualified (AEC-Q100 Grade 2) with 2026 SOP targeting for some designs.</p>
</blockquote>

<p><a href="https://hailo.ai/products/ai-accelerators/hailo-10h-ai-accelerator/">Hailo-10H product page</a> ·
<a href="https://hailo.ai/products/ai-accelerators/hailo-8-ai-accelerator/">Hailo-8</a></p>

<p><a href="https://www.eetimes.com/unicorn-ai-chipmaker-hailo-raises-136-million/">‘Unicorn’ AI Chipmaker Hailo Raises $136 Million</a> (historical)</p>
<blockquote>
  <p>Israeli AI chip startup Hailo has raised $136 million in a Series C funding round, bringing the company’s total to $224 million. The company has also reportedly reached “unicorn” status.</p>
</blockquote>

<p><a name="Tachyum"></a></p>

<div align="center" class="vendor-logo"><a href="http://www.tachyum.com"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tachyum_logo.png" height="40" loading="lazy" alt="Tachyum" /></a></div>

<p><a href="https://www.hpcwire.com/off-the-wire/tachyum-launches-prodigy-universal-processor/">Tachyum Launches Prodigy Universal Processor</a></p>
<blockquote>
  <p>May 11, 2021 — Tachyum today launched the world’s first universal processor, Prodigy, which unifies the functionality of a CPU, GPU and TPU in a single processor, creating a homogeneous architecture, while delivering massive performance improvements at a cost many times less than competing products</p>
</blockquote>

<p><a name="Alphaics"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.alphaics.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Alphaics_logo.png" height="50" loading="lazy" alt="AlphaICs" /></a></div>

<p><a href="https://www.eetimes.com/alphaics-begins-sampling-its-deep-learning-co-processor/">AlphaICs Begins Sampling Its Deep Learning Co-Processor</a></p>
<blockquote>
  <p>AlphaICs, a startup developing edge AI and learning silicon aimed at smart vision applications, is sampling its deep learning co-processor, Gluon, that also comes with a software development kit.</p>
</blockquote>

<p><a name="Syntiant"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.syntiant.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Syntiant_logo.png" height="30" loading="lazy" alt="Syntiant" /></a></div>

<p><a href="https://semiengineering.com/syntiant-analog-deep-learning-chips/">Syntiant: Analog Deep Learning Chips</a></p>

<blockquote>
  <p>Startup Syntiant Corp. is an Irvine, Calif. semiconductor company led by former top Broadcom engineers with experience in both innovative design and in producing chips designed to be produced in the billions, according to company CEO Kurt Busch.</p>
</blockquote>

<p><a name="aiCTX"></a></p>

<div align="center" class="vendor-logo"><a href="https://aictx.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/aiCTX_logo.png" height="40" loading="lazy" alt="aiCTX" /></a></div>

<p><strong><a href="https://www.eetimes.com/document.asp?doc_id=1333983">Baidu Backs Neuromorphic IC Developer</a></strong></p>

<blockquote>
  <p>MUNICH — Swiss startup aiCTX has closed a $1.5 million pre-A funding round from Baidu Ventures to develop commercial applications for its low-power neuromorphic computing and processor designs and enable what it calls “neuromorphic intelligence.” It is targeting low-power edge-computing embedded sensory processing systems.</p>
</blockquote>

<p><a name="Flexlogix"></a></p>

<div align="center" class="vendor-logo"><a href="http://www.flex-logix.com/nmax"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/flexlogix_logo.png" height="40" loading="lazy" alt="Flex Logix" /></a></div>

<p><strong><a href="https://www.zdnet.com/article/flex-logix-has-two-paths-to-making-a-lot-of-money-challenging-nvidia-in-ai/">Flex Logix has two paths to making a lot of money challenging Nvidia in AI</a></strong></p>

<blockquote>
  <p>The programmable chip company scores $55 million in venture backing, bringing its total haul to $82 million</p>
</blockquote>

<p><a name="PFN"></a></p>

<div align="center" class="vendor-logo"><a href="https://projects.preferred.jp/mn-core/en/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/PFN_logo.png" height="40" loading="lazy" alt="Preferred Networks" /></a></div>

<p><strong><a href="https://www.preferred-networks.jp/en/news">Preferred Networks develops a custom deep learning processor MN-Core for use in MN-3, a new large-scale cluster, in spring 2020</a></strong></p>

<blockquote>
  <p>Dec. 12, 2018, Tokyo Japan – Preferred Networks, Inc. (“PFN”, Head Office: Tokyo, President & CEO: Toru Nishikawa) announces that it is developing MN-Core (TM), a processor dedicated to deep learning and will exhibit this independently developed hardware for deep learning, including the MN-Core chip, board, and server, at the SEMICON Japan 2018, held at Tokyo Big Site. 
 </p>
</blockquote>

<p><a name="Cornami"></a></p>

<div align="center" class="vendor-logo"><a href="http://cornami.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cornami_logo.jpg" height="30" loading="lazy" alt="Cornami" /></a></div>

<p><strong><a href="https://www.zdnet.com/article/ai-startup-cornami-reveals-details-of-neural-net-chip/">AI Startup Cornami reveals details of neural net chip</a></strong></p>

<blockquote>
  <p>Stealth startup Cornami on Thursday revealed some details of its novel approach to chip design to run neural networks. CTO Paul Masters says the chip will finally realize the best aspects of a technology first seen in the 1970s. 
 </p>
</blockquote>

<p><a name="Anaflash"></a></p>

<div align="center" class="vendor-logo"><a href="http://anaflash.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Anaflash_logo.png" height="40" loading="lazy" alt="Anaflash" /></a></div>

<p><strong><a href="https://www.smart2zero.com/news/ai-chip-startup-offers-new-edge-computing-solution">AI chip startup offers new edge computing solution</a></strong></p>

<blockquote>
  <p>Anaflash Inc. (San Jose, CA) is a startup company that has developed a test chip to demonstrate analog neurocomputing taking place inside logic-compatible embedded flash memory. 
 </p>
</blockquote>

<p><a name="Optalysys"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.optalysys.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Optalysys_logo.png" height="40" loading="lazy" alt="Optalysys" /></a></div>

<p><strong><a href="https://www.globenewswire.com/news-release/2019/03/07/1749510/0/en/Optalysys-launches-world-s-first-commercial-optical-processing-system-the-FT-X-2000.html">Optalysys launches world’s first commercial optical processing system, the FT:X 2000</a></strong></p>

<blockquote>
  <p>Optalysys develops Optical Co-processing technology which enables new levels of processing capability delivered with a vastly reduced energy consumption compared with conventional computers. Its first coprocessor is based on an established diffractive optical approach that uses the photons of low-power laser light instead of conventional electricity and its electrons. This inherently parallel technology is highly scalable and is the new paradigm of computing. 
 </p>
</blockquote>

<p><a name="etacompute"></a></p>

<div align="center" class="vendor-logo"><a href="https://etacompute.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/etacompute_logo.png" height="80" loading="lazy" alt="Eta Compute" /></a></div>

<p><a href="https://spectrum.ieee.org/tech-talk/semiconductors/processors/lowpower-ai-startup-eta-compute-delivers-first-commercial-chips">Low-Power AI Startup Eta Compute Delivers First Commercial Chips</a></p>
<blockquote>
  <p>The firm pivoted away from riskier spiking neural networks using a new power management scheme</p>
</blockquote>

<p><a href="https://spectrum.ieee.org/tech-talk/semiconductors/processors/eta-compute-debuts-spiking-neural-network-chip-for-edge-ai">Eta Compute Debuts Spiking Neural Network Chip for Edge AI</a></p>
<blockquote>
  <p>Chip can learn on its own and inference at 100-microwatt scale, says company at Arm TechCon.</p>
</blockquote>

<p><a name="Achronix"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.achronix.com/product/speedster7t/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Achronix_logo.png" height="30" loading="lazy" alt="Achronix" /></a></div>

<p><strong><a href="https://www.eetimes.com/document.asp?doc_id=1334717">Achronix Rolls 7-nm FPGAs for AI</a></strong></p>

<blockquote>
  <p>Achronix is back in the game of providing full-fledged FPGAs with a new high-end 7-nm family, joining the Gold Rush of silicon to accelerate deep learning. It aims to leverage novel design of its AI block, a new on-chip network, and use of GDDR6 memory to provide similar performance at a lower cost than larger rivals Intel and Xilinx.</p>
</blockquote>

<p><a name="Areanna"></a></p>

<div align="center" class="vendor-logo"><a href="https://areanna-ai.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Areanna_logo.png" height="60" loading="lazy" alt="Areanna" /></a></div>

<p><strong><a href="https://www.eetimes.com/document.asp?doc_id=1334947#">Startup Runs AI in Novel SRAM</a></strong></p>

<blockquote>
  <p>Areanna is the latest example of an explosion of new architectures spawned by the rise of deep learning. The debut of a whole new approach to computing has fired imaginations of engineers around the industry hoping to be the next Hewlett and Packard.</p>
</blockquote>

<p><a name="Neuroblade"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.neuroblade.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Neuroblade_logo.png" height="120" loading="lazy" alt="NeuroBlade" /></a></div>

<p><strong><a href="https://www.eetasia.com/news/article/NeuroBlade-Preps-Inference-Chip">NeuroBlade Preps Inference Chip</a></strong></p>

<blockquote>
  <p>Add NeuroBlade to the dozens of startups working on AI silicon. The Israeli company just closed a $23 million Series A, led by the founder of Check Point Software and with participation from Intel Capital.</p>
</blockquote>

<p><a name="Luminous"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.luminouscomputing.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Luminous_logo.png" height="90" loading="lazy" alt="Luminous" /></a></div>

<p><strong><a href="https://www.technologyreview.com/s/613668/ai-chips-uses-optical-semiconductor-machine-learning/">Bill Gates just backed a chip startup that uses light to turbocharge AI</a></strong></p>

<blockquote>
  <p>Luminous Computing has developed an optical microchip that runs AI models much faster than other semiconductors while using less power.</p>
</blockquote>

<p><a name="Efinix"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.efinixinc.com"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Efinix_logo.png" height="25" loading="lazy" alt="Efinix" /></a></div>

<p><strong><a href="https://www.zdnet.com/article/chip-startup-efinix-hopes-to-bootstrap-ai-efforts-in-iot/">Chip startup Efinix hopes to bootstrap AI efforts in IoT</a></strong></p>

<blockquote>
  <p>Six-year-old startup Efinix has created an intriguing twist on the FPGA technology dominated by Intel and Xiliinx; the company hopes its energy-efficient chips will bootstrap the market for embedded AI in the Internet of Things.</p>
</blockquote>

<p><a name="AIstorm"></a></p>

<div align="center" class="vendor-logo"><a href="https://aistorm.ai"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AIstorm_logo.png" height="60" loading="lazy" alt="AIstorm" /></a></div>

<p><strong><a href="https://venturebeat.com/2019/02/11/aistorm-raises-13-2-million-for-ai-edge-computing-chips/">AIStorm raises $13.2 million for AI edge computing chips</a></strong></p>

<blockquote>
  <p>David Schie, a former senior executive at Maxim, Micrel, and Semtech, thinks both markets are ripe for disruption. He — along with WSI, Toshiba, and Arm veterans Robert Barker, Andreas Sibrai, and Cesar Matias — in 2011 cofounded AIStorm, a San Jose-based artificial intelligence (AI) startup that develops chipsets that can directly process data from wearables, handsets, automotive devices, smart speakers, and other internet of things (IoT) devices. </p>
</blockquote>

<p><a name="SiMa"></a></p>

<div align="center" class="vendor-logo"><a href="https://sima.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/SiMa_logo.png" height="40" loading="lazy" alt="SiMa.ai" /></a></div>

<p><strong><a href="https://sima.ai/press-release/sima-ai-next-gen-platform-for-physical-ai-in-production/">SiMa.ai Modalix platform for Physical AI in production</a></strong></p>
<blockquote>
  <p>Aug 2025 — Second-generation MLSoC Modalix ships for edge / Physical AI (robots, industrial, automotive, vision), targeting CNNs + Transformers/LLMs/GenAI under ~10W, with SoM/devkits and the LLiMa framework for on-device LLM deployment.</p>
</blockquote>

<p><a href="https://sima.ai/press-release/sima-ai-expands-one-platform-for-edge-ai-with-mlsoc-modalix/">MLSoC Modalix product family announcement</a> (2024) ·
<a href="https://sima.ai/press-release/sima-ai-launches-modalix-pcie-card-for-industrial-edge-ai-llms/">Modalix PCIe card for industrial edge LLMs</a> (2026)</p>

<p><a href="https://www.businesswire.com/news/home/20200512005313/en/SiMa.ai-Raises-30-Million-Series-Investment-Led">SiMa.ai Raises $30 Million in Series A</a> (historical)</p>
<blockquote>
  <p>SAN JOSE, Calif.--(BUSINESS WIRE)--SiMa.ai, the company enabling high performance machine learning to go green, today announced its Machine Learning SoC (MLSoC) platform – the industry’s first unified solution to support traditional compute with high performance, lowest power, safe and secure machine learning inference. Delivering the highest frames per second per watt, SiMa.ai’s MLSoC is the first machine learning platform to break the 1000 FPS/W barrier for ResNet-501. In customer engagements, the company has demonstrated 10-30x improvement in FPS/W through its automated software flow across a wide range of embedded edge applications, over today’s competing solutions. The platform will provide machine learning solutions that range from 50 TOPs@5W to 200 TOPs@20W, delivering an industry first of 10 TOPs/W for high performance inference.</p>
</blockquote>

<p><a href="https://www.businesswire.com/news/home/20191022005079/en/SiMa.ai%E2%84%A2-Introduces-MLSoC%E2%84%A2">SiMa.ai™ Introduces MLSoC™ – First Machine Learning Platform to Break 1000 FPS/W Barrier with 10-30x Improvement over Alternative Solutions</a></p>
<blockquote>
  <p>SiMa.ai, the company enabling high performance machine learning to go green, today announced its Machine Learning SoC (MLSoC) platform – the industry’s first unified solution to support traditional compute with high performance, lowest power, safe and secure machine learning inference. Delivering the highest frames per second per watt, SiMa.ai’s MLSoC is the first machine learning platform to break the 1000 FPS/W barrier for ResNet-501. In customer engagements, the company has demonstrated 10-30x improvement in FPS/W through its automated software flow across a wide range of embedded edge applications, over today’s competing solutions. The platform will provide machine learning solutions that range from 50 TOPs@5W to 200 TOPs@20W, delivering an industry first of 10 TOPs/W for high performance inference.</p>
</blockquote>

<p><a name="Untether"></a></p>

<div align="center" class="vendor-logo"><a href="https://untether.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Untether_logo.png" height="40" loading="lazy" alt="Untether AI" /></a></div>

<p><strong><a href="https://venturebeat.com/2021/07/20/untether-ai-nabs-125m-for-ai-acceleration-chips/">Untether AI nabs $125M for AI acceleration chips</a></strong></p>
<blockquote>
  <p>Untether AI, a startup developing custom-built chips for AI inferencing workloads, today announced it has raised $125 million from Tracker Capital Management and Intel Capital. The round, which was oversubscribed and included participation from Canada Pension Plan Investment Board and Radical Ventures, will be used to support customer expansion.</p>
</blockquote>

<p><a name="GrAI"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.graimatterlabs.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/GrAI_logo.png" height="40" loading="lazy" alt="GrAI Matter Labs" /></a></div>

<p><strong><a href="https://venturebeat.com/2019/09/18/grai-matter-labs-reveals-neuronflow-technology-and-announces-graiflow-sdk/">GrAI Matter Labs Reveals NeuronFlow Technology and Announces GrAIFlow SDK</a></strong></p>

<blockquote>
  <p>GrAI Matter Labs (aka GML), a neuromorphic computing pioneer today revealed NeuronFlow – a new programmable processor technology – and announced an early access program to its GrAIFlow software development kit.</p>
</blockquote>

<p><a name="Rain"></a></p>

<div align="center" class="vendor-logo"><a href="http://rain-neuromorphics.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Rain_logo.png" height="40" loading="lazy" alt="Rain" /></a></div>

<p><strong><a href="https://www.crunchbase.com/organization/rain-neuromorphics">Rain Neuromorphics on Crunchbase</a></strong></p>
<blockquote>
  <p>We build artificial intelligence processors, inspired by the brain. Our mission is to enable brain-scale intelligence.</p>
</blockquote>

<p><a name="ABR"></a></p>

<div align="center" class="vendor-logo"><a href="https://appliedbrainresearch.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/ABR_logo.png" height="40" loading="lazy" alt="Applied Brain Research" /></a></div>

<p><strong><a href="https://www.crunchbase.com/organization/applied-brain-research">Applied Brain Research on Crunchbase</a></strong></p>
<blockquote>
  <p>ABR makes the world's most advanced neuromoprhic compiler, runtime and libraries for the emerging space of neuromorphic computing.</p>
</blockquote>

<p><a name="Xmos"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.xmos.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Xmos_logo.png" height="40" loading="lazy" alt="XMOS" /></a></div>

<p><strong><a href="https://www.eetimes.com/xmos-adapts-xcore-into-aiot-crossover-processor/">XMOS adapts Xcore into AIoT ‘crossover processor’</a></strong></p>
<blockquote>
  <p>EE Times exclusive! The new chip targets AI-powered voice interfaces in IoT devices — “the most important AI workload at the endpoint.”</p>
</blockquote>

<p><a href="https://venturebeat.com/2020/02/12/xmos-unveils-xcore-ai-a-powerful-chip-designed-for-ai-processing-at-the-edge/">XMOS unveils Xcore.ai, a powerful chip designed for AI processing at the edge</a></p>
<blockquote>
  <p>The latest xcore.ai is a crossover chip designed to deliver high-performance AI, digital signal processing, control, and input/output in a single device with prices from $1.</p>
</blockquote>

<p><a name="DinoplusAI"></a></p>

<div align="center" class="vendor-logo"><a href="http://dinoplus.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/DinoplusAI_logo.png" height="60" loading="lazy" alt="DinoplusAI" /></a></div>

<blockquote>
  <p>We design and produce AI processors and the software to run them in data centers. Our unique approach optimizes for inference with the focus on performance, power efficiency, and ease of use; and at the same time our approach enables cost-effective training. </p>
</blockquote>

<p><a name="Furiosa"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.furiosa.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Furiosa_logo.png" height="60" loading="lazy" alt="FuriosaAI" /></a></div>

<p><strong><a href="https://furiosa.ai/blog/rngd-enters-mass-production-the-high-performance-ai-accelerator-for-any-data-center">RNGD enters mass production for data-center AI inference</a></strong></p>
<blockquote>
  <p>Jan 2026 — FuriosaAI’s RNGD (Tensor Contraction Processor, TSMC 5nm, ~180W PCIe) entered volume shipment for LLM / agentic inference; NXT RNGD servers pack multiple cards into air-cooled, ~3kW-class systems.</p>
</blockquote>

<p><strong><a href="https://furiosa.ai/blog/furiosaai-partners-with-broadcom-to-build-next-generation-inference-platform-for-the-agentic-era">FuriosaAI partners with Broadcom on next-generation inference platform</a></strong></p>
<blockquote>
  <p>May 2026 — Strategic collaboration to evolve TCP into a scale-up multi-die inference platform with Broadcom Ethernet/PCIe switching for hyperscale agentic workloads.</p>
</blockquote>

<p><a href="https://furiosa.ai/blog/furiosaai-equinixs-lisbon-data-center-press-release">Equinix Lisbon RNGD deployment</a> (Jul 2026)</p>

<p><a name="Corerain"></a></p>

<div align="center" class="vendor-logo"><a href="http://www.corerain.com/en"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Corerain_logo.png" height="60" loading="lazy" alt="Corerain" /></a></div>

<blockquote>
  <p>Corerain provides ultra-high performance AI acceleration chips and the world's first streaming engine-based AI development platform.</p>
</blockquote>

<p><a name="Perceive"></a></p>

<div align="center" class="vendor-logo"><a href="https://perceive.io/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Perceive_logo.png" height="60" loading="lazy" alt="Perceive" /></a></div>

<p><a href="https://venturebeat.com/2020/03/31/perceive-emerges-from-stealth-with-ergo-edge-ai-chip/">Perceive emerges from stealth with Ergo edge AI chip</a></p>
<blockquote>
  <p>On-device computing solutions startup Perceive emerged from stealth today with its first product: the Ergo edge processor for AI inference. CEO Steve Teig claims the chip, which is designed for consumer devices like security cameras, connected appliances, and mobile phones, delivers “breakthrough” accuracy and performance in its class.</p>
</blockquote>

<p><a name="SimpleMachines"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.simplemachines.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/SimpleMachines_logo.png" height="60" loading="lazy" alt="SimpleMachines" /></a></div>

<p><a href="https://www.design-reuse.com/news/49012/simplemachines-ai-chip-tsmc-16nm.html">SimpleMachines, Inc. Debuts First-of-its-Kind High Performance Chip</a></p>
<blockquote>
  <p>As traditional chip makers struggle to embrace the challenges presented by the rapidly evolving AI software landscape, a San Jose startup has announced it has working silicon and a whole new future-proof chip paradigm to address these issues.

The SimpleMachines, Inc. (SMI) team – which includes leading research scientists and industry heavyweights formerly of Qualcomm, Intel and Sun Microsystems – has created a first-of-its-kind easily programmable, high-performance chip that will accelerate a wide variety of AI and machine-learning applications. </p>
</blockquote>

<p><a name="Neureality"></a></p>

<div align="center" class="vendor-logo"><a href="https://www.neureality.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Neureality_logo.png" height="60" loading="lazy" alt="NeuReality" /></a></div>

<p><strong><a href="https://techcrunch.com/2022/12/06/neureality-ai-accelerator-chips-startup-raises-35m/">NeuReality lands $35M to bring AI accelerator chips to market</a></strong></p>
<blockquote>
  <p>NeuReality, a startup developing AI inferencing accelerator chips, has raised $35 million in new venture capital.</p>
</blockquote>

<p><a href="https://www.electronicsmedia.info/2021/05/06/neureality-unveiled-nr1-p-a-novel-ai-centric-inference-platform/">NeuReality unveiled NR1-P, A novel AI-centric inference platform</a></p>
<blockquote>
  <p>NeuReality has unveiled NR1-P, a novel AI-centric inference platform. NeuReality has already started demonstrating its AI-centric platform to customers and partners. NeuReality has redefined today’s outdated AI system architecture by developing an AI-centric inference platform based on a new type of System-on-Chip (SoC). </p>
</blockquote>

<p><a href="https://techcrunch.com/2021/02/10/neureality-raises-8m-for-its-novel-ai-inferencing-platform/">NeuReality raises $8M for its novel AI inferencing platform</a></p>
<blockquote>
  <p>NeuReality, an Israeli AI hardware startup that is working on a novel approach to improving AI inferencing platforms by doing away with the current CPU-centric model, is coming out of stealth today and announcing an $8 million seed round. </p>
</blockquote>
 
<p><a name="AnalogInference"></a></p>
<div align="center" class="vendor-logo"><a href="https://www.analog-inference.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AnalogInference_logo.png" height="60" loading="lazy" alt="Analog Inference" /></a></div>

<p><strong><a href="https://www.eenewsanalog.com/news/analog-inference-startup-raises-106-million">Analog inference startup raises $10.6 million</a></strong></p>
<blockquote>
  <p>The company is backed by Khosla Ventures and is developing its first generation of products for AI computing at the edge. The company raised $4.5 million shortly after its formation in March 2018, so the latest tranche brings the total raised to-date to $15.1 million</p>
</blockquote>

<p><a name="Quadric"></a></p>
<div align="center" class="vendor-logo"><a href="https://www.quadric.io/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Quatric_logo.png" height="60" loading="lazy" alt="Quadric" /></a></div>

<p><strong><a href="https://www.hpcwire.com/off-the-wire/quadric-announces-unified-silicon-and-software-platform-optimized-for-on-device-ai/">Quadric Announces Unified Silicon and Software Platform Optimized for On-Device AI</a></strong></p>
<blockquote>
  <p>BURLINGAME, Calif., June 22, 2021 — Quadric (quadric.io), an innovator in high-performance edge processing, has introduced a unified silicon and software platform that unlocks the power of on-device AI. </p>
</blockquote> 

<p><a name="EdgeQ"></a></p>
<div align="center" class="vendor-logo"><a href="https://edgeq.io/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/EdgeQ_logo.png" height="60" loading="lazy" alt="EdgeQ" /></a></div>

<p><strong><a href="https://techcrunch.com/2021/01/26/edgeq-reveals-more-details-behind-its-next-gen-5g-ai-chip/">EdgeQ reveals more details behind its next-gen 5G/AI chip</a></strong></p>
<blockquote>
  <p>5G is the current revolution in wireless technology, and every chip company old and new is trying to burrow their way into this ultra-competitive — but extremely lucrative — market. One of the most interesting new players in the space is EdgeQ, a startup with a strong technical pedigree via Qualcomm that we covered last year after it raised a nearly $40 million Series A.</p>
</blockquote> 
 
<p><a name="Innatera"></a></p>
<div align="center" class="vendor-logo"><a href="http://www.innatera.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Innatera_logo.png" height="60" loading="lazy" alt="Innatera" /></a></div>

<p><strong><a href="https://www.eetimes.com/innatera-unveils-neuromorphic-ai-chip-to-accelerate-spiking-networks/">Innatera Unveils Neuromorphic AI Chip to Accelerate Spiking Networks</a></strong></p>
<blockquote>
  <p>Innatera, the Dutch startup making neuromorphic AI accelerators for spiking neural networks, has produced its first chips, gauged their performance, and revealed details of their architecture.</p>
</blockquote> 
 
<p><a name="Ceremorphic"></a></p>
<div align="center" class="vendor-logo"><a href="https://ceremorphic.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Ceremorphic_logo.png" height="60" loading="lazy" alt="Ceremorphic" /></a></div>

<p><strong><a href="https://www.eetimes.com/redpine-founder-launches-ai-processor-startup/">Redpine Founder Launches AI Processor Startup</a></strong></p>
<blockquote>
  <p>Ceremorphic, an AI chip startup emerging from stealth mode this week, is readying a heterogeneous AI processor aimed at model training in data centers, automotive, high-performance computing, robotics and other emerging applications.</p>
</blockquote> 
 
<p><a name="Aspinity"></a></p>
<div align="center" class="vendor-logo"><a href="https://www.aspinity.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Aspinity_logo.png" height="60" loading="lazy" alt="Aspinity" /></a></div>

<p><strong><a href="https://embeddedcomputing.com/technology/analog-and-power/analog-semicundoctors-sensors/aspinity-analog-ml-chip-allows-battery-powered-always-on">Aspinity Analog ML Chip Allows Battery-Powered “Always On”</a></strong></p>
<blockquote>
  <p>Machine learning (ML) is all about massive amounts of processing, DSP, etc., right? Maybe not, according to the team at Aspinity. The company continues to push ahead on the analog front. The latest member of the company’s analogML family, the AML100, operates completely in the analog domain. As a result, it can reduce always-on system power by 95% (for the record, we had to walk through this a couple of times before I believed them).</p>
</blockquote> 
 
<p><a name="Teramem"></a></p>
<div align="center" class="vendor-logo"><a href="https://www.tetramem.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Teramem_logo.png" height="60" loading="lazy" alt="TetraMem" /></a></div>

<p><strong><a href="https://www.tetramem.com/posts/TetraMem-Technology-Debut-at-Linley">TetraMem enjoyed an exciting public debut of our analog in-memory compute technology at the Linley Spring 2022 Processor Conference.</a></strong></p>
<blockquote>
  <p></p>
</blockquote> 
 
<p><a name="d-matrix"></a></p>
<div align="center" class="vendor-logo"><a href="https://www.d-matrix.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/d-matrix_logo.png" height="60" loading="lazy" alt="d-Matrix" /></a></div>

<p><strong><a href="https://www.reuters.com/technology/ai-chip-startup-d-matrix-raises-110-mln-with-backing-microsoft-2023-09-06/">Exclusive: AI chip startup d-Matrix raises $110 million with backing from Microsoft</a></strong></p>
<blockquote>
  <p>Sept 6 (Reuters) - Silicon Valley-based artificial intelligence chip startup d-Matrix has raised $110 million from investors that include Microsoft Corp (MSFT.O) at a time when many chip companies are struggling to raise cash.</p>
</blockquote> 

<p><a href="https://www.forbes.com/sites/karlfreund/2022/06/21/d-matrix-ai-chip-promises-efficient-transformer-processing/">D-Matrix AI chip promises efficient transformer processing</a></p>
<blockquote>
  <p>The startup combines digital in-memory compute and chiplet implementations for data-center-grade inference.</p>
</blockquote> 
 

<p><a name="Etched"></a></p>
<div align="center"><h3><a href="https://www.etched.com/">Etched</a></h3></div>

<p><strong><a href="https://techcrunch.com/2026/06/30/nvidia-competitor-etched-hits-5b-valuation-1b-in-sales-for-ai-chip/">Nvidia competitor Etched hits $5B valuation, $1B in sales for AI chip</a></strong></p>
<blockquote>
  <p>Jun 2026 — Etched reports TSMC-manufactured transformer-specialized ASICs powering “frontier inference clusters,” with ~$800M raised to date (including a $500M round at a $5B valuation) and ~$1B in booked system orders.</p>
</blockquote>

<p><a href="https://techcrunch.com/2024/06/25/etched-is-building-an-ai-chip-that-only-runs-transformer-models/">Etched is building an AI chip that only runs one type of model</a></p>
<blockquote>
  <p>2024 Series A coverage of Sohu: an ASIC purpose-built for Transformer inference (rather than general-purpose GPU programmability), aiming for higher tokens/sec and better energy efficiency on LLM serving.</p>
</blockquote>

<div align="center" class="section-title"><h2><a name="China_AI_Chips"></a>V. China AI Accelerator Vendors</h2></div>
<hr class="section-rule" />
<p>Domestic training/inference accelerators have become central under export-control and procurement policies. Coverage below highlights widely reported product lines; treat performance claims as vendor-/press-reported unless independently benchmarked.</p>

<p><a name="HuaweiAscend"></a></p>
<div align="center" class="vendor-logo"><a href="https://www.huawei.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/HUAWEI_logo.png" height="40" loading="lazy" alt="HUAWEI logo" /></a>
&nbsp;&nbsp;
<a href="https://www.hisilicon.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/HiSilicon_logo.png" height="40" loading="lazy" alt="HiSilicon logo" /></a></div>
<div align="center"><h3>Huawei Ascend / HiSilicon</h3></div>

<p><strong><a href="https://www.huawei.com/en/news/2025/9/hc-xu-keynote-speech">Huawei Atlas 900 A3 SuperPoD / Ascend 910C</a></strong></p>
<blockquote>
  <p>2025 — Huawei scaled Ascend 910B/910C deployments and launched Atlas 900 A3 SuperPoD (up to 384× Ascend 910C), also referred to in cloud form as CloudMatrix384-class supernodes, for large-model training and serving. Ascend 950-class follow-ons are on Huawei’s roadmap.</p>
</blockquote>

<p><a href="https://arxiv.org/abs/2506.12708">Serving Large Language Models on Huawei CloudMatrix384</a> (technical paper)</p>

<p><a name="Cambricon"></a></p>
<div align="center" class="vendor-logo"><a href="https://www.cambricon.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cambricon_logo.png" height="50" loading="lazy" alt="Cambricon" /></a></div>
<div align="center"><h3>Cambricon (寒武纪)</h3></div>

<p><strong><a href="https://www.tomshardware.com/tech-industry/semiconductors/cambricon-targets-500000-ai-chips-in-2026-as-china-accelerates-domestic-hardware-push">Cambricon targets 500,000 AI chips in 2026</a></strong></p>
<blockquote>
  <p>Reports describe aggressive 2026 volume plans for Siyuan / MLU-class accelerators (including Siyuan 590 and next-gen 690 messaging), serving Chinese internet/cloud customers as a leading pure-play domestic AI-chip vendor.</p>
</blockquote>

<p><a href="https://awesomeagents.ai/hardware/cambricon-mlu590/">Cambricon MLU590 overview</a></p>
<blockquote>
  <p>MLU500-series cloud accelerator commonly cited for China data-center training/inference deployments with MLU-Link multi-card interconnect and Cambricon’s NeuWare / BANG software stack.</p>
</blockquote>

<p><a name="Biren"></a></p>
<div align="center"><h3><a href="https://www.birentech.com/">Biren Technology (壁仞)</a></h3></div>

<p><strong><a href="https://www.reuters.com/world/asia-pacific/china-ai-chipmaker-biren-surges-82-hong-kong-debut-kicking-off-2026-listings-2026-01-02/">China AI chipmaker Biren soars in Hong Kong debut</a></strong></p>
<blockquote>
  <p>Jan 2026 — Shanghai Biren Technology listed in Hong Kong (6082.HK), raising ~HK$5.58B. Best known for BR100-class GPGPU / AI accelerators positioned as high-performance domestic alternatives.</p>
</blockquote>

<p><a name="MooreThreads"></a></p>
<div align="center"><h3><a href="https://www.mthreads.com/">Moore Threads (摩尔线程)</a></h3></div>

<p><strong><a href="https://www.cnbc.com/2025/12/05/china-nvidia-moore-threads-trading-debut-1-billion-listing-ipo-shanghai-gpu-enflame-biren.html">Moore Threads surges over 400% on Shanghai trading debut</a></strong></p>
<blockquote>
  <p>Dec 2025 — Full-function GPU vendor (MTT S4000 / S5000 class AI cards, MUSA software stack) completed a ~$1.1B STAR Market IPO amid China’s domestic GPU push.</p>
</blockquote>

<p><a name="Enflame"></a></p>
<div align="center" class="vendor-logo"><a href="https://github.com/EnflameTechnology"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Enflame_logo.png" height="50" loading="lazy" alt="Enflame" /></a></div>
<div align="center"><h3>Enflame (燧原)</h3></div>

<p><strong><a href="https://www.hpcwire.com/off-the-wire/enflame-technology-announces-cloudblazer-with-dtu-chip-on-globalfoundries-12lp-finfet-platform-for-data-center-training/">Enflame CloudBlazer / DTU AI accelerators</a></strong></p>
<blockquote>
  <p>Shanghai-based accelerator vendor offering CloudBlazer training/inference products (DTU architecture) for domestic intelligent-computing centers; frequently grouped with China’s “GPU dragons” alongside Biren, Moore Threads, and MetaX. Open-source ecosystem links: <a href="https://github.com/EnflameTechnology">EnflameTechnology on GitHub</a>.</p>
</blockquote>

<p><a name="Horizon"></a></p>
<div align="center" class="vendor-logo"><a href="https://www.horizon.auto/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Horizon_Robotics_logo.png" height="50" loading="lazy" alt="Horizon Robotics" /></a></div>
<div align="center"><h3>Horizon Robotics (地平线)</h3></div>

<p><strong><a href="https://www.horizon.auto/en/solutions/horizon-journey/horizon-journey6">Horizon Journey 6 / BPU Nash automotive AI processors</a></strong></p>
<blockquote>
  <p>Leading China ADAS / autonomous-driving compute vendor with Journey-series BPU SoCs (Journey 6 adds BPU Nash with stronger Transformer support) widely designed into passenger vehicles; focuses on efficient vision/transformer perception at the edge rather than datacenter LLM training.</p>
</blockquote>

<p><a name="BlackSesame"></a></p>
<div align="center" class="vendor-logo"><a href="https://www.blacksesame.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Blacksesame_logo.png" height="50" loading="lazy" alt="Black Sesame" /></a></div>
<div align="center"><h3>Black Sesame Technologies (黑芝麻智能)</h3></div>

<p><strong><a href="https://www.blacksesame.com/en/huashan-a1000/">Huashan A1000 automotive-grade ADAS / AD SoCs</a></strong></p>
<blockquote>
  <p>Hong Kong-listed (02533.HK, Aug 2024) automotive AI SoC vendor. Huashan A1000-family chips target L2+/L3 assisted driving with automotive-grade safety certifications and are reported in mass-production vehicle models; Huashan A2000 messaging extends toward higher-performance / cross-domain AI inference.</p>
</blockquote>

<p><a href="https://www.caixinglobal.com/2024-08-01/chinese-auto-chip-maker-black-sesame-to-raise-143-million-in-hong-kong-ipo-102222110.html">Caixin: Black Sesame Hong Kong IPO</a></p>

<p><a name="MetaX"></a></p>
<div align="center" class="vendor-title"><h3><a href="https://www.metax-tech.com/en/about/about.html">MetaX (沐曦)</a></h3></div>

<p><strong><a href="https://www.caixinglobal.com/2026-03-26/chinese-gpu-maker-metax-doubles-revenue-amid-push-for-domestic-chips-102427800.html">Chinese GPU Maker MetaX Doubles Revenue Amid Push for Domestic Chips</a></strong></p>
<blockquote>
  <p>Shanghai MetaX (STAR: 688802.SH, listed Dec 2025) ships C-series training/inference GPUs (C500 mass production; C600 domestic-process follow-on) with the MXMACA software stack for AI clusters and intelligent-computing centers.</p>
</blockquote>

<p><a href="https://www.chinadaily.com.cn/a/202607/09/WS6a4f3978a310986e2b4645f5.html">MetaX scales production to meet rising AI chip demand</a></p>

<p><a name="Hygon"></a></p>
<div align="center" class="vendor-title"><h3><a href="https://www.hygon.cn/">Hygon (海光) DCU</a></h3></div>

<p><strong><a href="https://www.trendforce.com/news/2026/04/29/news-huawei-ascend-cambricon-and-hygon-completed-day-0-adaptation-to-deepseek-v4/">Hygon DCU completes Day-0 adaptation for DeepSeek-V4</a></strong></p>
<blockquote>
  <p>Hygon’s Deep Computing Unit (DCU) GPGPU-class accelerators and DTK software stack are widely used in China for large-model training/inference; 2025–2026 coverage highlights same-day DeepSeek model adaptations alongside Ascend and Cambricon.</p>
</blockquote>

<p><a href="https://github.com/HYGON-AI/dcu-inference-cookbook">HYGON-AI DCU inference cookbook</a> (open deployment guides)</p>

<p><a name="Iluvatar"></a></p>
<div align="center" class="vendor-title"><h3><a href="https://www.iluvatar.com/">Iluvatar CoreX (天数智芯)</a></h3></div>

<p><strong><a href="https://www.scmp.com/tech/big-tech/article/3341368/iluvatar-corex-targets-nvidias-rubin-gpu-road-map-amid-china-chip-push">Iluvatar CoreX targets Nvidia’s Rubin with GPU road map</a></strong></p>
<blockquote>
  <p>Jan 2026 — Hong Kong-listed Iluvatar CoreX outlined a multi-generation GPU architecture roadmap (Tianshu / Tianxuan / Tianji / Tianquan messaging) aiming to close the gap with Nvidia Hopper→Blackwell→Rubin class platforms, with BI-V150-class products already in AI training/inference deployments.</p>
</blockquote>

<p><a name="AIChipCompilers"></a></p>

<div align="center" class="section-title"><h2 id="compilers-heading">AI Chip Compilers</h2></div>
<div class="resource-list">

<hr class="section-rule" />
<strong>Actively used / widely referenced (2024–2026)</strong><br>
1. <a href="https://mlir.llvm.org/">MLIR</a> — Multi-Level Intermediate Representation (LLVM)<br>
2. <a href="https://tvm.apache.org/">Apache TVM</a> — end-to-end ML compiler stack<br>
3. <a href="https://www.tensorflow.org/xla">XLA</a> — TensorFlow / JAX compiler<br>
4. <a href="https://github.com/triton-lang/triton">OpenAI Triton</a> — GPU kernel DSL widely used for LLM kernels<br>
5. <a href="https://iree.dev/">IREE</a> — MLIR-based end-to-end compiler &amp; runtime<br>
6. <a href="https://developer.nvidia.com/tensorrt">NVIDIA TensorRT</a> / <a href="https://github.com/NVIDIA/TensorRT-LLM">TensorRT-LLM</a><br>
7. <a href="https://awsdocs-neuron.readthedocs-hosted.com/">AWS Neuron</a> — Trainium / Inferentia compiler stack<br>
8. <a href="https://rocm.docs.amd.com/">AMD ROCm</a> / composable kernel ecosystem<br>
9. <a href="https://www.modular.com/max/mojo">Modular MAX / Mojo</a><br>
10. <a href="https://onnxruntime.ai/">ONNX Runtime</a> — cross-vendor inference<br>
<br>
<strong>Historical / research compilers</strong><br>
11. <a href="https://github.com/pytorch/glow">PyTorch Glow</a><br>
12. <a href="https://github.com/plaidml/plaidml">PlaidML</a><br>
13. <a href="https://github.com/Tiramisu-Compiler/tiramisu">MIT Tiramisu</a><br>
14. <a href="http://tensor-compiler.org/">TACO (Tensor Algebra Compiler)</a><br>
15. <a href="https://github.com/NervanaSystems/ngraph">Intel nGraph</a> (archived)<br>

</div>

<p><a name="AIChipBenchmarks"></a></p>

<div align="center" class="section-title"><h2 id="benchmarks-heading">AI Chip Benchmarks</h2></div>
<div class="resource-list">

<hr class="section-rule" />

1. <a href="https://mlcommons.org/benchmarks/">MLPerf (MLCommons)</a> — industry-standard training, inference, HPC, and client benchmarks.<br>
<strong>Latest results (2026):</strong>
<a href="https://mlcommons.org/2026/04/mlperf-inference-v6-0-results/">Inference v6.0</a> ·
<a href="https://mlcommons.org/2026/06/mlperf-training-v6-0-results/">Training v6.0</a> ·
<a href="https://mlcommons.org/visualizer">Results visualizer</a><br>
2. <a href="https://dawn.cs.stanford.edu/benchmark/index.html">DAWNBench</a> (historical end-to-end ImageNet benchmark)<br>
3. <a href="https://github.com/rdadolf/fathom">Fathom</a> — reference workloads for modern deep learning methods<br>
4. <a href="http://ai-benchmark.com/index.html">AI-Benchmark</a> — mobile / edge AI scores<br>
5. <a href="https://www.eembc.org/mlmark/">EEMBC MLMark</a><br>
6. <a href="https://github.com/AIIABenchmark/AIIA-DNN-benchmark">AIIA DNN Benchmark</a><br>

</div>

<p><a name="Reference"></a></p>

<div align="center" class="section-title"><h2>Reference</h2></div>

<hr class="section-rule" />

<div class="resource-list">
      
1. <a href="https://meanderful.blogspot.jp/2017/06/fpgas-and-ai-processors-dnn-and-cnn-for.html">FPGAs and AI processors: DNN and CNN for all</a><br>
2. <a href="http://www.nanalyze.com/2017/05/12-ai-hardware-startups-new-ai-chips/">12 AI Hardware Startups Building New AI Chips</a><br>
3. <a href="http://eyeriss.mit.edu/tutorial.html">Tutorial on Hardware Architectures for Deep Neural Networks</a><br>
4. <strong><a href="https://nicsefc.ee.tsinghua.edu.cn/projects/neural-network-accelerator/">Neural Network Accelerator Comparison</a></strong><br>
5. "White Paper on AI Chip Technologies 2018". You can download it from <a href="https://cloud.tsinghua.edu.cn/f/9aa0a4f0a5684cc48495/?dl=1">here</a>, or <a href="https://drive.google.com/open?id=1ieDm0bpjVWl5MnSESRs92EcmoSzG5vcm">Google drive.</a><br>
6. <strong>"What We Talk About When We Talk About AI Chip". <a href="https://mp.weixin.qq.com/s/SbX5yz5d3GXaLcl15DO6OQ">#1</a>,  <a href="https://mp.weixin.qq.com/s/zvgDgKpIMIRLFUEW0fFOeg">#2</a>,  <a href="https://mp.weixin.qq.com/s/CKHs5yblcMur4h2BwUBICw">#3</a>,  <a href="https://mp.weixin.qq.com/s/hFnHhaWWYTFRUsD3HlMbLw">#4</a></strong><br>
7. <strong><a href="https://birenresearch.github.io/AIChip_Paper_List/">AI Chip Paper List</a></strong><br>
8. <strong><a href="https://khairy2011.medium.com/tpu-vs-gpu-vs-cerebras-vs-graphcore-a-fair-comparison-between-ml-hardware-3f5a19d89e38">TPU vs GPU vs Cerebras vs Graphcore: A Fair Comparison between ML Hardware</a></strong><br>

</div>

<div align="center">
<a href="http://www.reliablecounter.com" target="_blank"><img src="http://www.reliablecounter.com/count.php?page=https://basicmi.github.io/AI-Chip/&digit=style/plain/3/&reloads=1" alt="laptop" title="laptop" border="0"></a>
</div>
