<header class="page-header" id="top" align="center">
<h1 class="site-brand">AI Chip (ICs and IPs)</h1>
<div class="hero-art"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AI-chips.png" loading="lazy" alt="AI chips illustration" /></div>
<p class="editor-line">Editor <a href="https://www.linkedin.com/in/shan-tang-27342510/"><strong>S.T.</strong></a> (LinkedIn)</p>
<p class="wechat-line"><strong>WeChat / 微信公众号</strong> · <a href="https://mp.weixin.qq.com/mp/appmsgalbum?action=getalbum&amp;__biz=MzI3MDQ2MjA3OA==&amp;scene=1&amp;album_id=1374108991751782402&amp;count=3#wechat_redirect">StarryHeavensAbove</a> — AI chip articles</p>
<div class="wechat-qr"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/qrcode_for_weichat_258.jpg" height="100" loading="lazy" alt="WeChat QR code" /></div>
<div class="landscape-map"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AI_Chip_Landscape_v0p8.png" loading="lazy" alt="AI Chip Landscape v0.8 (2026)" /></div>
<p class="page-intro">A living directory of AI accelerators (ICs &amp; IPs) — each entry has a short field intro (plus lineage where relevant) and 1–2 latest updates. Prefer official / primary sources; performance claims are often vendor-reported.</p>
</header>

<div align="center" class="section-title"><h2>At a glance</h2></div>
<p class="refresh-note" align="center"><em>One-line latest status per company — updated periodically. Last refreshed: July 2026 (incl. Qualcomm Dragonfly data-center AI).</em></p>
<hr class="section-rule" />
<ul class="glance-list">
<li><a href="#Nvidia"><strong>NVIDIA</strong></a> — Vera Rubin platform in full production (GTC 2026); NVL72 partner shipments targeted H2 2026.</li>
<li><a href="#Intel"><strong>Intel / Habana</strong></a> — Gaudi 3 generally available on IBM Cloud and Dell AI Factory for enterprise GenAI inference/fine-tune.</li>
<li><a href="#AMD"><strong>AMD</strong></a> — Helios / MI455X rack-scale on track for H2 2026; Meta 6GW Instinct deal incl. custom MI450-class.</li>
<li><a href="#Qualcomm"><strong>Qualcomm</strong></a> — Dragonfly data-center AI: AI200/AI250 (2026–27) + AI300/HBC; Meta multi-gen deal for Dragonfly C1000 CPU.</li>
<li><a href="#Samsung"><strong>Samsung</strong></a> — Exynos 2600 (first 2nm GAA mobile SoC) ships in Galaxy S26 with large on-device GenAI NPU gains.</li>
<li><a href="#MediaTek"><strong>MediaTek</strong></a> — Dimensity 9500 (Sep 2025) NPU 990 + Super Efficient CIM NPU for agentic on-device GenAI.</li>
<li><a href="#Marvell"><strong>Marvell</strong></a> — Custom AI XPU partner for AWS Trainium / Microsoft Maia; 18+ custom projects and rising AI silicon revenue.</li>
<li><a href="#Broadcom"><strong>Broadcom</strong></a> — OpenAI Jalapeño Intelligence Processor unveiled; continues Google TPU + Meta MTIA XPU franchise.</li>
<li><a href="#Google"><strong>Google</strong></a> — Ironwood (TPU7x) generally available Mar 2026; Trillium (v6e) remains a volume Cloud TPU SKU.</li>
<li><a href="#Amazon_AWS"><strong>AWS</strong></a> — Trainium3 / Trn3 UltraServers GA (Dec 2025); Trainium4 previewed with NVLink Fusion path.</li>
<li><a href="#Microsoft"><strong>Microsoft</strong></a> — Maia 200 inference accelerator (Jan 2026) deploying in Azure for Copilot / Foundry token economics.</li>
<li><a href="#OpenAI"><strong>OpenAI</strong></a> — First custom inference ASIC “Jalapeño” with Broadcom; initial deployments targeted end of 2026.</li>
<li><a href="#Anthropic"><strong>Anthropic</strong></a> — Expanded Google TPU + Broadcom capacity (~3.5 GW from 2027) atop AWS Trainium and NVIDIA GPUs.</li>
<li><a href="#Apple"><strong>Apple</strong></a> — M5 / M5 Pro / M5 Max add GPU Neural Accelerators and a faster Neural Engine for Apple Intelligence.</li>
<li><a href="#Alibaba"><strong>Alibaba</strong></a> — Zhenwu M890 (144GB HBM3) in mass production; 560k+ Zhenwu shipments; roadmap to V900/J900.</li>
<li><a href="#Baidu"><strong>Baidu</strong></a> — Kunlunxin P800 10k-card clusters; key ERNIE 5.1 training on domestic stack; Tianchi 256-card supernode (2026).</li>
<li><a href="#Tencent_Cloud"><strong>Tencent</strong></a> — Zixiao / partner accelerators continue scaling LLM and recommendation serving on Tencent Cloud (2025–2026).</li>
<li><a href="#Facebook"><strong>Meta</strong></a> — MTIA “Iris” (v3) enters production Sep 2026 with Broadcom/TSMC; six-month chip cadence through 2027.</li>
<li><a href="#Tesla"><strong>Tesla</strong></a> — AI5 taped out (Apr 2026); AI6 / Dojo3 in progress; vehicles near-term stay on AI4.</li>
<li><a href="#ARM"><strong>Arm</strong></a> — Ethos-U85 + Corstone-320 IoT reference for edge transformer / GenAI; Armv9 SME path in mobile SoCs.</li>
<li><a href="#Synopsys"><strong>Synopsys</strong></a> — ARC NPX NPU IP scaled for auto/consumer GenAI SoCs with ongoing 2025–2026 toolchain releases.</li>
<li><a href="#Imagination"><strong>Imagination</strong></a> — PowerVR NNA + Continuum for edge/auto transformer networks; 2025–2026 licensee SoC ramps.</li>
<li><a href="#CEVA"><strong>CEVA</strong></a> — NeuPro-class NPU IP for embedded/auto/IoT transformers; 2025–2026 DNN compiler updates.</li>
<li><a href="#Cadence"><strong>Cadence</strong></a> — Tensilica AI Platform / NeuroWeave updates for on-device and automotive transformer SoCs (2025–2026).</li>
<li><a href="#VeriSilicon"><strong>VeriSilicon</strong></a> — VIP/Acuity NPU IP and turnkey services for China/global edge GenAI SoCs (2025–2026).</li>
<li><a href="#Cerebras"><strong>Cerebras</strong></a> — Nasdaq IPO (CBRS, May 2026); multi-year OpenAI inference capacity deal (&gt;$20B messaging).</li>
<li><a href="#Graphcore"><strong>Graphcore</strong></a> — SoftBank injects ~$457M (2026); Izanagi next-gen IPU+CPU path aimed at Stargate-scale 2026 deployments.</li>
<li><a href="#Tenstorrent"><strong>Tenstorrent</strong></a> — Galaxy Blackhole GA (Apr 2026): 32× Blackhole servers shipping for LLM inference and video gen.</li>
<li><a href="#Etched"><strong>Etched</strong></a> — ~$5B valuation / ~$1B booked orders for transformer-specialized Sohu inference ASICs.</li>
<li><a href="#Groq"><strong>Groq</strong></a> — LPU technology licensed into NVIDIA’s Vera Rubin AI-factory stack (GTC 2026).</li>
<li><a href="#SambaNova"><strong>SambaNova</strong></a> — SN50 RDU for agentic AI; $350M+ Series E; SoftBank early deploy; Intel collab; H2 2026 ship.</li>
<li><a href="#Mythic"><strong>Mythic</strong></a> — $125M Series D + Videantis acquisition for hybrid analog/digital energy-efficient inference.</li>
<li><a href="#Hailo"><strong>Hailo</strong></a> — Hailo-10H generally available for edge LLMs/VLMs (~40 TOPS INT4 class, ~2.5W).</li>
<li><a href="#Furiosa"><strong>FuriosaAI</strong></a> — RNGD in mass production; Broadcom partnership for next-gen multi-die inference platform.</li>
<li><a href="#Kinara"><strong>Kinara</strong></a> — NXP acquiring Kinara (ex–Deep Vision) for industrial/automotive edge NPU portfolio.</li>
<li><a href="#SiMa"><strong>SiMa.ai</strong></a> — Modalix MLSoC in production for Physical AI (robots/industrial) under ~10W with LLiMa LLMs.</li>
<li><a href="#d-matrix"><strong>d-Matrix</strong></a> — Corsair inference platform in full production (Jun 2026); $275M Series C / ~$2B valuation.</li>
<li><a href="#Blaize"><strong>Blaize</strong></a> — Nasdaq-listed (BZAI); GSP architecture for industrial/smart-city edge vision and GenAI.</li>
<li><a href="#SynSense"><strong>SynSense</strong></a> — Speck/Xylo neuromorphic + event-vision stack; 2025–2026 funding/collabs for ultra-low-power edge AI.</li>
<li><a href="#Sagence"><strong>Sagence AI</strong></a> — Analog CIM accelerators for efficient LLM/vision inference; active 2025–2026 AI-infra engagements post-rebrand.</li>
<li><a href="#HuaweiAscend"><strong>Huawei Ascend</strong></a> — Atlas 950 SuperPoD / Ascend 950DT (up to 8,192 NPUs) debuts globally at MWC 2026; WAIC hardware showcase.</li>
<li><a href="#Cambricon"><strong>Cambricon</strong></a> — Siyuan 690 in mass production/delivery; targets ~500k AI chips in 2026; Q1 profit surge on cloud demand.</li>
<li><a href="#Biren"><strong>Biren</strong></a> — Hong Kong IPO (6082.HK, Jan 2026); BR100-class GPGPU/AI accelerators.</li>
<li><a href="#MooreThreads"><strong>Moore Threads</strong></a> — STAR Market IPO Dec 2025; MTT S4000/S5000 AI GPUs with MUSA software stack.</li>
<li><a href="#MetaX"><strong>MetaX</strong></a> — STAR-listed (688802.SH); C500 in mass production, C600 domestic-process follow-on, MXMACA stack.</li>
<li><a href="#Hygon"><strong>Hygon</strong></a> — DCU GPGPUs + DTK stack; Day-0 DeepSeek-V4 adaptation alongside Ascend and Cambricon.</li>
<li><a href="#Iluvatar"><strong>Iluvatar CoreX</strong></a> — HK-listed; multi-gen GPU roadmap (Tianshu→Tianquan) aiming at Hopper–Rubin class gap; BI-V150 deployed.</li>
<li><a href="#Enflame"><strong>Enflame</strong></a> — CloudBlazer / iGCU GPUs in China ICC deployments; TopsRider LLM stack updates through 2025–2026.</li>
<li><a href="#Horizon"><strong>Horizon Robotics</strong></a> — Journey 6 / BPU Nash mass-designed into China L2+ vehicles; stronger Transformer / E2E driving support.</li>
<li><a href="#BlackSesame"><strong>Black Sesame</strong></a> — Huashan A1000 in mass-production vehicles; A2000 messaging for higher-perf / cross-domain AD (2025–2026).</li>
</ul>

<div align="center" class="section-title"><h2>Shortcut</h2></div>
<hr class="section-rule" />
<table class="shortcut-table">
  <tr>
    <th><a href="#IC_Vendors">IC Vendors</a></th>
    <td><a href="#Nvidia">NVIDIA</a>, <a href="#Intel">Intel</a>, <a href="#Habana">Gaudi</a>, <a href="#AMD">AMD</a>, <a href="#Qualcomm">Qualcomm</a>, <a href="#Samsung">Samsung</a>, <a href="#MediaTek">MediaTek</a>, <a href="#Marvell">Marvell</a>, <a href="#Broadcom">Broadcom</a></td>
  </tr>
  <tr>
    <th><a href="#Tech_Giants">Tech Giants &amp; HPC</a></th>
    <td><a href="#Google">Google</a>, <a href="#Amazon_AWS">AWS</a>, <a href="#Microsoft">Microsoft</a>, <a href="#Apple">Apple</a>, <a href="#OpenAI">OpenAI</a>, <a href="#Anthropic">Anthropic</a>, <a href="#Alibaba">Alibaba</a>, <a href="#Baidu">Baidu</a>, <a href="#Tencent_Cloud">Tencent</a>, <a href="#Facebook">Meta</a>, <a href="#Tesla">Tesla</a></td>
  </tr>
  <tr>
    <th><a href="#IP_Vendors">IP Vendors</a></th>
    <td><a href="#ARM">Arm</a>, <a href="#Synopsys">Synopsys</a>, <a href="#Imagination">Imagination</a>, <a href="#CEVA">CEVA</a>, <a href="#Cadence">Cadence</a>, <a href="#VeriSilicon">VeriSilicon</a></td>
  </tr>
  <tr>
    <th><a href="#Startups">Startups</a></th>
    <td><a href="#Cerebras">Cerebras</a>, <a href="#Graphcore">Graphcore</a>, <a href="#Tenstorrent">Tenstorrent</a>, <a href="#Etched">Etched</a>, <a href="#Groq">Groq</a>, <a href="#SambaNova">SambaNova</a>, <a href="#Mythic">Mythic</a>, <a href="#Hailo">Hailo</a>, <a href="#Furiosa">FuriosaAI</a>, <a href="#Kinara">Kinara</a>, <a href="#SiMa">SiMa</a>, <a href="#d-matrix">d-Matrix</a>, <a href="#Blaize">Blaize</a>, …</td>
  </tr>
  <tr>
    <th><a href="#China_AI_Chips">China AI Accelerators</a></th>
    <td><a href="#HuaweiAscend">Huawei Ascend</a>, <a href="#Cambricon">Cambricon</a>, <a href="#Biren">Biren</a>, <a href="#MooreThreads">Moore Threads</a>, <a href="#MetaX">MetaX</a>, <a href="#Hygon">Hygon</a>, <a href="#Iluvatar">Iluvatar</a>, <a href="#Enflame">Enflame</a>, <a href="#Horizon">Horizon</a>, <a href="#BlackSesame">Black Sesame</a></td>
  </tr>
</table>

<div align="center" class="section-title"><h2><a name="IC_Vendors"></a>I. IC Vendors</h2></div>
<hr class="section-rule" />
<a name="Nvidia"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Nvidia_logo.png" height="50" loading="lazy" alt="NVIDIA" /></div>
<div align="center" class="vendor-title"><h3>NVIDIA — GPU / AI accelerator lineage</h3></div>
<p class="vendor-blurb">NVIDIA turned GPUs into the default AI training/inference substrate via CUDA (2007) and successive datacenter architectures. From Pascal/Volta Tensor Cores through Ampere and Hopper, the stack evolved into rack-scale Grace+Blackwell systems; Rubin extends that AI-factory model into 2026.</p>

<p><strong>CUDA foundation (pre–Tensor Core)</strong></p>
<ul>
<li><strong>Tesla arch (2006) + CUDA (2007)</strong> — unified shaders / GPGPU; GPU becomes a general accelerator.</li>
<li><strong>Fermi (2010)</strong> — caches, ECC, stronger HPC path.</li>
<li><strong>Kepler (2012)</strong> — Hyper-Q / dynamic parallelism; datacenter Tesla K-series.</li>
<li><strong>Maxwell (2014)</strong> — major perf/W redesign.</li>
<li><strong>Pascal (2016) — P100</strong> — HBM2 + NVLink 1.0; first widely adopted datacenter GPU for deep learning at scale.</li>
</ul>

<p><strong>Tensor Core era</strong></p>
<ul>
<li><strong>Volta (2017) — V100</strong> — first Tensor Cores (FP16 mixed precision); DGX / early large-model workhorse.</li>
<li><strong>Turing (2018) — T4</strong> — inference-efficient datacenter SKUs; consumer RTX adds RT + Tensor Cores.</li>
<li><strong>Ampere (2020) — A100</strong> — TF32 / BF16, structured sparsity, MIG; A100 40/80GB HBM2e.</li>
<li><strong>Ada Lovelace (2022) — L40 / L4</strong> — inference / visual datacenter SKUs alongside Hopper.</li>
<li><strong>Hopper (2022) — H100 / H200</strong> — Transformer Engine, FP8, NVLink 4; H200 expands HBM3e for LLM train/serve.</li>
</ul>

<p><strong>Platform / rack-scale era (2024–2026)</strong></p>
<ul>
<li><strong>Blackwell (2024) — B200 / GB200 NVL72</strong> — multi-die GPU, FP4/FP6 datapaths, NVLink 5; Grace+Blackwell superchips and NVL72 racks.</li>
<li><strong>Rubin (CES/GTC 2026)</strong> — Vera CPU + Rubin GPU + NVLink 6 Switch + ConnectX-9 / BlueField-4 / Spectrum-6 for agentic / MoE; partner availability targeted H2 2026. NVIDIA also described integrating Groq-class LPU technology into the AI-factory stack.</li>
</ul>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Vera-Rubin-Opens-Agentic-AI-Frontier/default.aspx">Vera Rubin opens agentic AI frontier</a></strong> — GTC Mar 2026 — seven chips in full production (Vera CPU, Rubin GPU, NVLink 6, ConnectX-9, BlueField-4, Spectrum-6, Groq LPU); NVL72 on track for H2 2026 partner systems.</li>
<li><strong><a href="https://developer.nvidia.com/blog/nvidia-vera-rubin-pod-seven-chips-five-rack-scale-systems-one-ai-supercomputer/">Vera Rubin POD / rack-scale systems</a></strong> — Mar 2026 — POD-scale co-design across five rack systems; CEO later reiterated “giant amounts” of Vera Rubin production incoming for H2 2026.</li>
</ul>
<p><a href="https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth">Hopper in-depth</a> · <a href="https://www.nvidia.com/en-us/data-center/technologies/hopper-architecture/">Hopper</a> · <a href="https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/">Blackwell</a></p>

<a name="Intel"></a>
<a name="Habana"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Intel_logo.png" height="60" loading="lazy" alt="Intel / Habana" /></div>
<div align="center" class="vendor-title"><h3>Intel / Habana Gaudi</h3></div>
<p class="vendor-blurb">Intel’s AI accelerator path consolidated around Habana Labs after the 2019 acquisition. Gaudi (training) and Goya (inference) established Ethernet-centric scale-out as an alternative to proprietary GPU fabrics; Gaudi 2 broadened LLM training, and Gaudi 3 (2024) targets enterprise generative AI with OEM and cloud availability. Intel also folds AI into Xeon AMX and Arc/Flex GPUs, but Gaudi remains the dedicated datacenter accelerator brand.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://newsroom.intel.com/artificial-intelligence/ibm-cloud-first-service-provider-deploy-intel-gaudi-3">Gaudi 3 on IBM Cloud</a></strong> — Intel Vision 2025 — IBM Cloud is the first CSP with Gaudi 3 in production (Frankfurt, Washington D.C., Dallas) for enterprise GenAI price/performance.</li>
<li><strong><a href="https://newsroom.intel.com/artificial-intelligence/intel-gaudi-3-expands-availability-drive-ai-innovation-scale">Dell AI Factory with Gaudi 3</a></strong> — 2025 — Dell AI platform / AI Factory ships validated Gaudi 3 systems for scalable enterprise GenAI with open Ethernet networking.</li>
</ul>

<a name="AMD"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AMD_logo.png" height="35" loading="lazy" alt="AMD" /></div>
<div align="center" class="vendor-title"><h3>AMD — Instinct AI GPUs</h3></div>
<p class="vendor-blurb">AMD’s datacenter AI story runs through the Instinct line on CDNA architecture (distinct from RDNA gaming GPUs), with ROCm as the software stack. MI100/MI200 established HBM-heavy training SKUs; MI300A/X (CDNA 3, 2023) brought chiplet APU/GPU designs into large LLM clusters. MI350 (CDNA 4, 2025) pushes HBM3E capacity and low-precision datatypes; MI400 / Helios rack systems headline the 2026 roadmap alongside deep hyperscaler partnerships.</p>
<ul>
<li><strong>MI100 / MI200 (CDNA 1–2)</strong> — early Instinct training accelerators; MI250X widely used in HPC+AI.</li>
<li><strong>MI300A / MI300X (2023)</strong> — CDNA 3 chiplets; MI300X became a primary non-NVIDIA LLM training/inference GPU.</li>
<li><strong>MI350X / MI355X (2025)</strong> — CDNA 4, up to 288GB HBM3E, MXFP6/MXFP4 paths.</li>
<li><strong>MI400 / Helios (roadmap 2026)</strong> — rack-scale systems and custom SKUs for hyperscalers.</li>
</ul>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.amd.com/en/newsroom/press-releases/2026-2-24-amd-and-meta-announce-expanded-strategic-partnersh.html">AMD–Meta 6GW Instinct partnership</a></strong> — Feb 2026 — up to 6GW multi-generation Instinct GPUs; custom MI450-class on Helios with ROCm; first-GW shipments targeted H2 2026.</li>
<li><strong><a href="https://www.nextplatform.com/compute/2026/02/23/amd-says-helios-racks-and-mi400-series-gpus-on-track-for-2h-2026/4092199">Helios / MI400 series on track</a></strong> — 2026 — AMD says Helios racks and MI400/MI455X UALink systems remain on track for H2 2026 engineering/low-volume production alongside MI350 volume deployments.</li>
</ul>

<a name="Qualcomm"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Qualcomm_logo.png" height="40" loading="lazy" alt="Qualcomm" /></div>
<div align="center" class="vendor-title"><h3>Qualcomm — Hexagon NPU &amp; Dragonfly data-center AI</h3></div>
<p class="vendor-blurb">Qualcomm’s AI silicon now spans mobile Hexagon NPUs in Snapdragon SoCs and a full data-center Dragonfly portfolio for agentic inference. Hexagon evolved from DSP blocks into fused scalar/vector/tensor NPUs for on-device GenAI; Cloud AI 100 was an earlier inference SKU. In Oct 2025 Qualcomm launched rack-scale Dragonfly AI200/AI250 inference accelerators, then at Investor Day Jun 2026 added AI300 with High Bandwidth Compute (HBC), the Dragonfly C1000 server CPU (Meta multi-generation agreement), and a multi-year data-center revenue push.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://sg.finance.yahoo.com/news/qualcomm-unveils-comprehensive-data-center-193000894.html">Dragonfly AI300 / data-center roadmap</a></strong> — Jun 24, 2026 Investor Day — Dragonfly AI300 (3rd-gen rack inference with HBC Gen 2; sampling ~2028) joins AI200/AI250; Dragonfly C1000 CPU (250+ Oryon cores) with multi-generation Meta server deal; HBC near-memory compute for token efficiency.</li>
<li><strong><a href="https://www.datacenterdynamics.com/en/news/qualcomm-launches-ai200-and-ai250-chip-offering-targeting-inferencing-workloads-at-rack-scale/">Dragonfly AI200 / AI250 launch</a></strong> — Oct 2025 — Hexagon-based rack-scale inference accelerators: AI200 (~768GB LPDDR/card, commercial ~2026) and AI250 (HBC Gen 1 near-memory, ~2027); Humain among early large deploy partners.</li>
</ul>

<a name="Samsung"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Samsung_logo.png" height="35" loading="lazy" alt="Samsung" /></div>
<div align="center" class="vendor-title"><h3>Samsung — Exynos NPU</h3></div>
<p class="vendor-blurb">Samsung integrates NPUs into Exynos mobile SoCs and builds HBM that underpins datacenter AI GPUs. Exynos NPUs scaled with each flagship for vision and on-device GenAI; Exynos 2500 (3nm GAA) was followed by Exynos 2600 — Samsung’s first 2nm GAA mobile SoC — powering Galaxy S26 with substantially higher generative-AI NPU performance and AI graphics features (ENSS).</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://semiconductor.samsung.com/processor/mobile-processor/exynos-2600/">Exynos 2600</a></strong> — First 2nm GAA mobile SoC; Samsung cites ~113% generative-AI NPU gains vs. prior gen for larger on-device models; ships in Galaxy S26 / S26+.</li>
<li><strong><a href="https://www.asiae.co.kr/en/article/2026042810393630443">ENSS AI graphics on Exynos 2600</a></strong> — Apr 2026 — Exynos Neural Super Sampling (ENSS) commercialized for AI upscaling/frame generation to cut GPU load on flagship gaming/graphics.</li>
</ul>

<a name="MediaTek"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/MediaTek_logo.png" height="40" loading="lazy" alt="MediaTek" /></div>
<div align="center" class="vendor-title"><h3>MediaTek — Dimensity NPU</h3></div>
<p class="vendor-blurb">MediaTek’s Dimensity flagship line pairs Arm CPUs with successive in-house NPUs for Android on-device AI. The NPU roadmap (through 8th-gen NPU 890 on Dimensity 9400) emphasizes generative and agentic workloads—LoRA adaptation, diffusion video, and MoE LLMs—alongside the Dimensity Agentic AI Engine software path.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.mediatek.com/press-room/mediatek-dimensity-9500-unleashes-best-in-class-performance-ai-experiences-and-power-efficiency-for-the-next-generation-of-mobile-devices">Dimensity 9500 — NPU 990</a></strong> — Sep 2025 — 9th-gen NPU 990 with Generative AI Engine 2.0 (vendor: ~2× compute, 4K image gen, 128K-token LLM path) plus Super Efficient CIM NPU for always-on AI.</li>
</ul>

<a name="Marvell"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Marvell_logo.png" height="60" loading="lazy" alt="Marvell" /></div>
<div align="center" class="vendor-title"><h3>Marvell — custom AI ASICs &amp; DPUs</h3></div>
<p class="vendor-blurb">Marvell supplies DPUs (OCTEON / ARMADA) and, increasingly, co-designed custom AI accelerators for cloud providers. Alongside Broadcom’s XPU franchise, Marvell is widely reported as a design partner on AWS Trainium/Inferentia-class and Microsoft Maia-class silicon—making it a key “picks and shovels” vendor in the custom-ASIC wave.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.marvell.com/blogs/inside-marvell-expanding-custom-silicon-opportunity.html">Expanding custom silicon opportunity</a></strong> — Jul 2025 — Custom AI Investor Event: ~18 active custom projects (hyperscaler XPUs + attach) with TAM for custom XPUs growing into the tens of billions by 2028.</li>
<li><strong><a href="https://www.marvell.com/products/data-processing-units.html">Hyperscaler AI ASIC programs</a></strong> — 2025–2026 — widely reported design partner on AWS Trainium-class and Microsoft Maia-class accelerators, plus AI optics/DPU attach silicon.</li>
</ul>

<a name="Broadcom"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Broadcom_logo.png" height="45" loading="lazy" alt="Broadcom" /></div>
<div align="center" class="vendor-title"><h3>Broadcom — custom XPUs</h3></div>
<p class="vendor-blurb">Broadcom co-designs customer-specific AI accelerators (XPUs) and pairs them with Tomahawk/Jericho Ethernet switching. The model began with Google TPU generations and now spans Meta MTIA, OpenAI custom silicon, and other frontier/cloud programs—positioning Broadcom as the primary ASIC implementation partner opposite merchant GPUs.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://openai.com/index/openai-broadcom-jalapeno-inference-chip/">OpenAI Jalapeño with Broadcom</a></strong> — Jun 2026 — OpenAI’s first custom LLM inference ASIC co-developed with Broadcom (Tomahawk networking); initial deployments targeted end of 2026 within multi-GW platform.</li>
<li><strong><a href="https://www.nasdaq.com/press-release/broadcom-announces-extended-partnership-meta-deploy-technology-support-multi">Meta MTIA partnership extended</a></strong> — Apr 2026 — XPU platform continues as co-design backbone for multi-generation MTIA and Ethernet AI fabric.</li>
</ul>

<div align="center" class="section-title"><h2><a name="Tech_Giants"></a>II. Tech Giants &amp; HPC Vendors</h2></div>
<hr class="section-rule" />
<a name="Google"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Google_logo.png" height="40" loading="lazy" alt="Google" /></div>
<div align="center" class="vendor-title"><h3>Google — TPU lineage</h3></div>
<p class="vendor-blurb">Google invented the modern custom-AI-ASIC pattern with TPU v1 (2015) for production inference, then opened Cloud TPU for external training. Each generation scaled systolic MXUs, HBM, and pod interconnect; v4/v5 pods trained many Google foundation models, while Trillium (v6e) and Ironwood (v7) address GenAI train/serve economics. Edge TPU (Coral) and Pixel Tensor are related but separate product lines.</p>

<p><strong>Early generations</strong></p>
<ul>
<li><strong>TPU v1 (2015)</strong> — inference-only systolic MXU (INT8) in Google production services.</li>
<li><strong>TPU v2 (2017)</strong> — training + inference, bfloat16, HBM, first multi-chip pods.</li>
<li><strong>TPU v3 (2018)</strong> — higher compute, liquid cooling at pod scale.</li>
<li><strong>TPU v4 (2021)</strong> — denser pods, 3D torus + optical circuit switches.</li>
</ul>

<p><strong>Split SKUs &amp; GenAI scale-up</strong></p>
<ul>
<li><strong>TPU v5e (2023)</strong> — cost-efficient training/inference at volume.</li>
<li><strong>TPU v5p (2023)</strong> — high-end large-pod training.</li>
<li><strong>Trillium / TPU v6e (2024)</strong> — larger MXUs; Google cites ~4.7× peak compute/chip vs. v5e.</li>
<li><strong>Ironwood / TPU v7 (2025)</strong> — inference-leaning generation with FP8-class paths and very large pods.</li>
</ul>

<p><strong>Related Google silicon</strong></p>
<ul>
<li><strong>Edge TPU</strong> — Coral edge inference ASIC.</li>
<li><strong>Google Tensor (Pixel)</strong> — mobile SoC ML blocks (separate from Cloud TPU).</li>
</ul>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://docs.cloud.google.com/tpu/docs/release-notes">Ironwood (TPU7x) GA</a></strong> — Mar 31, 2026 — TPU7x (Ironwood family) generally available for large-scale training and inference (LLMs, MoEs, diffusion); up to 9,216-chip pods.</li>
<li><strong><a href="https://blog.google/innovation-and-ai/infrastructure-and-cloud/google-cloud/ironwood-google-tpu-things-to-know/">Ironwood for the age of inference</a></strong> — 2025–2026 — 7th-gen TPU purpose-built for high-volume low-latency inference/serving; Google cites large per-chip gains vs. prior gen.</li>
</ul>
<p><a href="https://cloud.google.com/transform/ai-specialized-chips-tpu-history-gen-ai">10 years of TPU</a> · <a href="https://docs.cloud.google.com/tpu/docs/v6e">v6e docs</a> · <a href="https://cloud.google.com/tpu">Cloud TPU</a> · <a href="https://cloud.google.com/edge-tpu/">Edge TPU</a></p>

<a name="Amazon_AWS"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Amazon_AWS.png" height="50" loading="lazy" alt="AWS" /></div>
<div align="center" class="vendor-title"><h3>Amazon AWS — Trainium &amp; Inferentia</h3></div>
<p class="vendor-blurb">AWS builds first-party AI silicon for EC2: Inferentia for inference and Trainium for training, compiled via the Neuron SDK. Inferentia1/2 lowered LLM serving cost on Inf1/Inf2; Trainium1 and Trainium2 (Trn1/Trn2) plus UltraServers with NeuronLink scale-up target foundation-model training and large inference inside AWS regions—often co-designed with partners such as Marvell/Annapurna.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-ec2-trn3-ultraservers/">EC2 Trn3 UltraServers (Trainium3)</a></strong> — Dec 2025 re:Invent — Trainium3 (first 3nm AWS AI chip) UltraServers GA; AWS cites up to ~4.4× compute and ~4× energy efficiency vs. Trn2 UltraServers.</li>
<li><strong><a href="https://press.aboutamazon.com/2025/12/trainium3-ultraservers-now-available-enabling-customers-to-train-and-deploy-ai-models-faster-at-lower-cost">Trainium3 UltraServers details</a></strong> — Up to 144 Trainium3 chips / ~362 FP8 PFLOPs per UltraServer; Anthropic and Bedrock among early Trainium users; Trainium4 on the roadmap.</li>
</ul>

<a name="Microsoft"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Microsoft_logo.png" height="60" loading="lazy" alt="Microsoft" /></div>
<div align="center" class="vendor-title"><h3>Microsoft — Azure Maia</h3></div>
<p class="vendor-blurb">Microsoft entered custom AI silicon with Azure Maia (accelerator) and Cobalt (Arm CPU) to optimize Azure OpenAI / Copilot economics. Maia 100 (5nm, advanced packaging) is co-designed for Azure AI cloud workloads with a PyTorch/ONNX Runtime software path; subsequent Maia generations are expected to deepen rack-level integration with Azure networking and cooling.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://blogs.microsoft.com/blog/2026/01/26/maia-200-the-ai-accelerator-built-for-inference/">Maia 200 inference accelerator</a></strong> — Jan 2026 — TSMC 3nm inference ASIC with 216GB HBM3e; Microsoft cites ~30% better perf/$ vs. prior fleet hardware and FP4/FP8 leadership claims vs. other custom silicon.</li>
<li><strong><a href="https://news.microsoft.com/source/emea/2026/01/microsoft-introduces-maia-200-new-inference-accelerator-enhances-ai-performance-in-azure/">Maia 200 Azure rollout</a></strong> — Deploying in US Central (then US West 3) for Superintelligence / Foundry / Copilot workloads; Maia SDK preview with PyTorch and Triton.</li>
</ul>

<a name="OpenAI"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/OpenAI_logo.png" height="48" loading="lazy" alt="OpenAI" /></div>
<div align="center" class="vendor-title"><h3>OpenAI — custom Intelligence Processors</h3></div>
<p class="vendor-blurb">Long dependent on NVIDIA GPUs (and Azure capacity), OpenAI moved into custom inference silicon to cut serving cost and diversify supply. Jalapeño—co-developed with Broadcom—is the first “Intelligence Processor,” optimized for LLM inference rather than general training, as the opening move in a multi-generation, multi-gigawatt Broadcom collaboration.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://openai.com/index/openai-broadcom-jalapeno-inference-chip/">Jalapeño LLM inference chip</a></strong> — Jun 2026 — first custom inference-optimized ASIC with Broadcom; initial deployments targeted by end of 2026 within a multi-generation platform.</li>
</ul>

<a name="Anthropic"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Anthropic_logo.png" height="48" loading="lazy" alt="Anthropic" /></div>
<div align="center" class="vendor-title"><h3>Anthropic — multi-hardware compute</h3></div>
<p class="vendor-blurb">Anthropic does not tape out a merchant chip brand; it co-designs capacity across AWS Trainium (Project Rainier), Google TPUs (Broadcom-implemented), and NVIDIA GPUs. The strategy is deliberate multi-sourcing for Claude training and serving at gigawatt scale, with long-term TPU commitments expanding through 2027+.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.anthropic.com/news/google-broadcom-partnership-compute">Google &amp; Broadcom compute partnership</a></strong> — Apr 2026 — expanded multi-GW next-gen TPU capacity (filings cite ~3.5 GW) from 2027, on top of prior &gt;1 GW TPU plus Trainium and NVIDIA.</li>
</ul>

<a name="Apple"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Apple_logo.png" height="60" loading="lazy" alt="Apple" /></div>
<div align="center" class="vendor-title"><h3>Apple — Neural Engine &amp; Apple silicon AI</h3></div>
<p class="vendor-blurb">Apple’s on-device AI runs on the Neural Engine and, increasingly, GPU Neural Accelerators inside Apple silicon—not discrete datacenter GPUs. From A11’s first Neural Engine through M1–M4, Apple scaled unified-memory ML performance for privacy-preserving inference; M5 (2025) and M5 Pro/Max (2026) explicitly target Apple Intelligence and local LLM/creative AI workflows.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.apple.com/newsroom/2025/10/apple-unleashes-m5-the-next-big-leap-in-ai-performance-for-apple-silicon/">Apple M5</a></strong> — Oct 2025 — Neural Accelerators in each GPU core and a faster 16-core Neural Engine for on-device Apple Intelligence.</li>
<li><strong><a href="https://www.apple.com/newsroom/2026/03/apple-debuts-m5-pro-and-m5-max-to-supercharge-the-most-demanding-pro-workflows/">M5 Pro and M5 Max</a></strong> — Mar 2026 — Fusion Architecture scales GPU AI compute and unified memory (up to 128GB / ~614GB/s on M5 Max) for local LLM and pro creative AI.</li>
</ul>

<a name="Alibaba"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/alibaba_logo.png" height="60" loading="lazy" alt="Alibaba" /></div>
<div align="center" class="vendor-title"><h3>Alibaba — T-Head PPU</h3></div>
<p class="vendor-blurb">Alibaba’s T-Head unit designs cloud AI accelerators under the Zhenwu / PPU family for Alibaba Cloud and external customers as a domestic GPU-class alternative. After Zhenwu 810E-class SKUs, Zhenwu M890 (2026) raises HBM capacity and chip-to-chip bandwidth for agentic train/infer, paired with Panjiu AL128 servers, ICN Switch networking, and the SAIL software stack.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.alibabacloud.com/blog/alibaba-unveils-new-ai-chip-flagship-model-and-rebuilt-cloud-stack-ai-for-agentic-era_603151">Zhenwu M890 AI chip</a></strong> — May 2026 Cloud Summit — M890 triples prior-gen performance claims with 144GB HBM3 and 800GB/s chip-to-chip bandwidth; FP32→FP4; powers Panjiu AL128 with ICN Switch 1.0.</li>
<li><strong><a href="https://thenextweb.com/news/alibaba-zhenwu-m890-t-head-china-ai-chip-nvidia">T-Head scale shipments</a></strong> — 2026 — T-Head cites 560,000+ Zhenwu AI chips shipped and 400+ external customers; further V900 (2027) / J900 (2028) roadmap messaging.</li>
</ul>

<a name="Baidu"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Baidu_logo.png" height="40" loading="lazy" alt="Baidu" /></div>
<div align="center" class="vendor-title"><h3>Baidu — Kunlunxin</h3></div>
<p class="vendor-blurb">Baidu’s Kunlunxin (昆仑芯) GPUs underpin ERNIE and Baidu Cloud AI services. From earlier Kunlun generations through P800-class training/inference cards, Baidu has iterated a full stack (hardware + software) as a China-domestic alternative for large-model workloads.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.jiemian.com/article/14421027.html">Kunlunxin trains key ERNIE 5.1 version</a></strong> — Baidu Create 2026 — P800 completed large-scale validation with multiple 10k-card clusters since 2025; fully domestic Kunlunxin cluster trained a key ERNIE 5.1 version (97% effective training rate claimed).</li>
<li><strong><a href="https://www.jiemian.com/article/14421027.html">Tianchi 256-card supernode</a></strong> — May 2026 — Tianchi 256-card Kunlunxin supernode lit up, June launch messaging; +25% throughput / +50% inference efficiency claims vs. prior gen, HPN5.0 networking.</li>
</ul>

<a name="Tencent_Cloud"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tencent_Cloud_logo.png" height="30" loading="lazy" alt="Tencent" /></div>
<div align="center" class="vendor-title"><h3>Tencent Cloud — Zixiao / custom AI</h3></div>
<p class="vendor-blurb">Tencent deploys proprietary Zixiao-class and partner AI accelerators across Tencent Cloud for recommendation, multimodal, and LLM train/infer inside its China footprint—part of a broader mix that also includes merchant GPUs where available.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong>Tencent Cloud AI accelerators</strong> — 2025–2026 — proprietary Zixiao-class and partner AI accelerators deployed for recommendation, multimodal, and LLM train/infer inside Tencent Cloud.</li>
</ul>

<a name="Facebook"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/facebook_logo.png" height="50" loading="lazy" alt="Meta" /></div>
<div align="center" class="vendor-title"><h3>Meta — MTIA</h3></div>
<p class="vendor-blurb">Meta’s MTIA (Meta Training and Inference Accelerator) is an in-house family for ranking, recommendation, and increasingly generative workloads at hyperscale. Built with Broadcom as implementation partner, MTIA has moved to a rapid multi-generation chiplet cadence (MTIA 300–500 class messaging) aimed at Meta’s production AI fleet rather than merchant sale.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://techcrunch.com/2026/07/09/metas-new-ai-chips-will-begin-production-in-september/">MTIA Iris production September 2026</a></strong> — Jul 2026 reporting — next-gen MTIA chip (Iris / v3) cleared testing and targets September production with Broadcom design + TSMC 3nm; part of ~6-month cadence through 2027.</li>
<li><strong><a href="https://ai.meta.com/blog/meta-mtia-scale-ai-chips-for-billions/">Four MTIA chips in two years</a></strong> — Multi-generation MTIA roadmap (300–500 class) with modular chiplets; continues alongside AMD Instinct and NVIDIA GPU capacity.</li>
</ul>

<a name="Tesla"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tesla_logo.png" height="60" loading="lazy" alt="Tesla" /></div>
<div align="center" class="vendor-title"><h3>Tesla — HW / AI inference &amp; Dojo</h3></div>
<p class="vendor-blurb">Tesla designs FSD/AI inference SoCs for vehicles (HW3 → HW4/AI4 → AI5) and pursued Dojo training tiles for internal vision-model training. The vertical stack ties cars, Optimus, and data-center inference together; AI5 is the next major SoC step after AI4, with Dojo3 still on the longer training roadmap.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://electrek.co/2026/04/15/tesla-ai5-chip-taped-out-musk-ai6-dojo3/">Tesla AI5 taped out</a></strong> — Apr 2026 — AI5 inference/training SoC taped out; AI6/Dojo3 mentioned as in progress; broad vehicle deployment still gated (reports: mid–late 2027+).</li>
</ul>

<div align="center" class="section-title"><h2><a name="IP_Vendors"></a>III. Traditional IP Vendors</h2></div>
<hr class="section-rule" />
<a name="ARM"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/ARM_logo.png" height="30" loading="lazy" alt="Arm" /></div>
<div align="center" class="vendor-title"><h3>Arm — Ethos NPU IP</h3></div>
<p class="vendor-blurb">Arm licenses Ethos NPU IP alongside Cortex CPUs for edge and IoT SoCs. The Ethos-U micro-NPU line (U55 → U65 → U85) scales MAC arrays and adds transformer operators while keeping the Vela/Ethos toolchain path; larger Ethos-N products address higher-TOPS vision/GenAI in Cortex-A systems.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.arm.com/products/silicon-ip-cpu/ethos/ethos-u85">Ethos-U85 micro-NPU</a></strong> — Third-gen Ethos-U (to ~4 TOPS @ 1 GHz) with native transformer ops for edge/IoT GenAI; Corstone-320 reference and Vela toolchain.</li>
<li><strong><a href="https://www.techinsights.com/blog/dimensity-9500-debuts-arm-c1-cores-and-dual-npu">Arm C1 / SME2 in flagship SoCs</a></strong> — 2025 — Arm Lumex CSS (C1 cores + SME2) ships in MediaTek Dimensity 9500-class SoCs, accelerating on-CPU ML alongside NPUs.</li>
</ul>

<a name="Synopsys"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Synopsys_logo.png" height="40" loading="lazy" alt="Synopsys" /></div>
<div align="center" class="vendor-title"><h3>Synopsys — ARC NPX NPU IP</h3></div>
<p class="vendor-blurb">Synopsys DesignWare ARC NPX provides licensable neural processor IP for SoC integrators across automotive, consumer, and infrastructure. The family emphasizes scalable TOPS, functional-safety options, and toolchain continuity for DNN/transformer graphs.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.synopsys.com/designware-ip/processor-solutions/neural-processing-unit.html">ARC NPX NPU IP</a></strong> — 2025–2026 — DesignWare ARC NPX neural processor IP for automotive/consumer/infrastructure SoCs; multi-TOPS configs and transformer-ready toolchain updates.</li>
</ul>

<a name="Imagination"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Imagination_logo.png" height="60" loading="lazy" alt="Imagination" /></div>
<div align="center" class="vendor-title"><h3>Imagination — NNA IP</h3></div>
<p class="vendor-blurb">Imagination’s PowerVR Neural Network Accelerators (NNA) and GPU+NNA combinations target edge and automotive SoCs. IMG Continuum software maps CNN and transformer-class networks onto the NNA datapaths for licensees.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.imaginationtech.com/products/ai/">Imagination AI / NNA IP</a></strong> — 2025–2026 — PowerVR Neural Network Accelerators and GPU+NNA combinations for edge and automotive SoCs with Continuum software for transformer-class nets.</li>
</ul>

<a name="CEVA"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/CEVA_logo.png" height="40" loading="lazy" alt="CEVA" /></div>
<div align="center" class="vendor-title"><h3>CEVA — NeuPro / edge AI IP</h3></div>
<p class="vendor-blurb">CEVA licenses low-power AI processor IP and DSP/NPU hybrids for real-time embedded, automotive, and IoT inference. NeuPro-class offerings and the CEVA DNN compiler add transformer-capable paths for on-device GenAI and vision.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.ceva-dsp.com/app/deep-learning/">CEVA edge AI / NeuPro IP</a></strong> — 2025–2026 — low-power NeuPro-class AI processor IP and DNN graph compiler for real-time embedded, automotive, and IoT inference including transformers.</li>
</ul>

<a name="Cadence"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cadence_logo.png" height="40" loading="lazy" alt="Cadence" /></div>
<div align="center" class="vendor-title"><h3>Cadence — Tensilica AI IP</h3></div>
<p class="vendor-blurb">Cadence Tensilica offers configurable NPU and AI DSP IP for on-device and automotive SoCs. The NeuroWeave toolchain maps modern DNN and transformer graphs onto Tensilica datapaths used widely in vision, audio, and edge GenAI chips.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.cadence.com/en_US/home/tools/ip/tensilica-ip/tensilica-ai-platform.html">Tensilica AI Platform</a></strong> — 2025–2026 — Tensilica NPU/AI DSP IP with NeuroWeave toolchain updates for modern DNN and transformer workloads in edge/auto SoCs.</li>
</ul>

<a name="VeriSilicon"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/VeriSilicon_logo.png" height="40" loading="lazy" alt="VeriSilicon" /></div>
<div align="center" class="vendor-title"><h3>VeriSilicon — VIP NPU IP</h3></div>
<p class="vendor-blurb">VeriSilicon provides VIP/Acuity NPU IP plus turnkey ASIC design services, especially strong in China edge and vision SoCs. The IP covers CNN through on-device GenAI use cases for consumer, automotive, and IoT customers.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.verisilicon.com/">VIP / NPU IP & design services</a></strong> — 2025–2026 — Acuity/VIP NPU IP plus turnkey ASIC design services widely used in China and global edge SoCs for vision and on-device GenAI.</li>
</ul>

<div align="center" class="section-title"><h2><a name="Startups"></a>IV. Startups</h2></div>
<hr class="section-rule" />
<a name="Cerebras"></a>
<div align="center" class="vendor-logo"><a href="https://www.cerebras.net/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cerebras_logo.png" height="50" loading="lazy" alt="Cerebras" /></a></div>
<div align="center" class="vendor-title"><h3>Cerebras — wafer-scale engine</h3></div>
<p class="vendor-blurb">Cerebras builds wafer-scale AI processors (WSE) that place an enormous on-wafer SRAM/compute fabric into CS systems, avoiding many multi-GPU communication bottlenecks. WSE-1/2 established the approach; WSE-3 (2024, 5nm) powers CS-3 for foundation-model training and high-throughput inference with cloud and on-prem deployments.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.cnbc.com/2026/05/16/cerebras-blockbuster-ipo-boosts-hype-for-spacex-openai-anthropic.html">Cerebras IPO (CBRS)</a></strong> — May 2026 — blockbuster Nasdaq debut after filing; WSE-3 / CS-3 wafer-scale systems power Training and Inference Cloud services.</li>
<li><strong><a href="https://www.cnbc.com/2026/04/17/cerebras-new-ipo-ai-chips.html">OpenAI multi-year capacity deal</a></strong> — 2025–2026 — OpenAI commits to large inference capacity (filings cite 750MW committed, option to 2GW) plus $1B infrastructure loan / warrants.</li>
</ul>

<a name="Graphcore"></a>
<div align="center" class="vendor-logo"><a href="https://www.graphcore.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Graphcore_logo.png" height="70" loading="lazy" alt="Graphcore" /></a></div>
<div align="center" class="vendor-title"><h3>Graphcore — IPU</h3></div>
<p class="vendor-blurb">Graphcore pioneered Intelligence Processing Units (IPU) with fine-grained MIMD parallelism and large on-chip memory (Colossus Mk1/Mk2, Bow). After competing in the pre-LLM and early-LLM era, SoftBank acquired Graphcore (2024) as a wholly owned subsidiary to fund next-generation AI compute while keeping the Graphcore brand.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.cnbc.com/2026/05/12/softbank-graphcore-ai-chip-investment.html">SoftBank $457M funding into Graphcore</a></strong> — May 2026 — SoftBank funnels ~$457M into Graphcore (wholly owned since Jul 2024) to fund next-gen AI silicon and SoftBank AI infra plans.</li>
<li><strong><a href="https://www.jonpeddie.com/news/graphcores-ipu-doing-well-at-softbank/">Izanagi / SoftBank AI stack</a></strong> — 2025–2026 — next-gen accelerator work (Izanagi messaging) pairs Graphcore IPU heritage with SoftBank/Ampere Arm CPU stack for hyperscale deployment targets.</li>
</ul>

<a name="Tenstorrent"></a>
<div align="center" class="vendor-logo"><a href="http://tenstorrent.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tenstorrent_logo.png" height="80" loading="lazy" alt="Tenstorrent" /></a></div>
<div align="center" class="vendor-title"><h3>Tenstorrent — Wormhole / Blackhole</h3></div>
<p class="vendor-blurb">Tenstorrent (Jim Keller–led) builds Tensix-based AI processors as scalable chiplet meshes with an open software stack (TT-Metalium). Wormhole-generation cards are shipping into developer and rack deployments; Blackhole is the next architecture step toward higher-density train/infer systems.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://tenstorrent.com/en/newsroom/tenstorrent-enables-ai-at-scale-with-industry-leading-performance">Galaxy Blackhole general availability</a></strong> — Apr 28, 2026 — 6U air-cooled Galaxy with 32 Blackhole chips shipping (vendor: 23 PFLOPS Block FP8, Ethernet scale-out); from ~$110k per server.</li>
<li><strong><a href="https://tenstorrent.com/en/newsroom/tt-deploy">TT-Deploy production shipping</a></strong> — May 2026 — TT-Deploy: volume shipping, multi-Galaxy superclusters, open TT-Metalium stack, and third-party validated serving benchmarks.</li>
</ul>

<a name="Etched"></a>
<div align="center" class="vendor-logo"><a href="https://www.etched.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Etched_logo.png" height="48" loading="lazy" alt="Etched" /></a></div>
<div align="center" class="vendor-title"><h3>Etched — transformer ASICs</h3></div>
<p class="vendor-blurb">Etched builds ASICs purpose-built for Transformer inference (Sohu) rather than general-purpose GPU programmability—betting that specialization wins tokens/sec and energy efficiency for LLM serving. TSMC-manufactured silicon and “frontier inference cluster” messaging mark a fast rise from 2024 Series A through 2026 scale-up.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://techcrunch.com/2026/06/30/nvidia-competitor-etched-hits-5b-valuation-1b-in-sales-for-ai-chip/">Etched hits $5B valuation</a></strong> — Jun 2026 — ~$800M raised to date (incl. $500M at $5B valuation) and ~$1B in booked system orders for transformer-specialized ASICs.</li>
</ul>

<a name="Groq"></a>
<div align="center" class="vendor-logo"><a href="https://groq.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Groq_logo.png" height="48" loading="lazy" alt="Groq" /></a></div>
<div align="center" class="vendor-title"><h3>Groq — LPU</h3></div>
<p class="vendor-blurb">Groq’s Language Processing Unit (LPU) uses a deterministic, compiler-scheduled architecture for ultra-low-latency LLM token generation. After building a cloud inference service on LPU racks, Groq’s technology was licensed by NVIDIA (late 2025), with key talent joining NVIDIA; GTC 2026 described LPU-class engines inside the Vera Rubin AI factory for efficient decode alongside Rubin GPUs.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Vera-Rubin-Opens-Agentic-AI-Frontier/default.aspx">NVIDIA Vera Rubin includes Groq LPU</a></strong> — Late 2025 NVIDIA licensed Groq LPU tech; GTC 2026 — LPU-class engines integrated into Vera Rubin for low-latency / high-efficiency token generation.</li>
</ul>

<a name="SambaNova"></a>
<div align="center" class="vendor-logo"><a href="https://sambanova.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/SambaNova_logo.png" height="40" loading="lazy" alt="SambaNova" /></a></div>
<div align="center" class="vendor-title"><h3>SambaNova — RDU</h3></div>
<p class="vendor-blurb">SambaNova’s Reconfigurable Dataflow Unit (RDU) maps full model graphs onto a dataflow fabric for enterprise and agentic inference. SN40L established the GenAI-era platform; SN50 (5th gen) scales compute and network bandwidth for large agentic deployments with SambaNova’s full-stack software.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://sambanova.ai/press/sambanova-unveils-fastest-chip-for-agentic-ai-collaborates-with-intel-and-raises-350m">SN50 RDU, Intel collab, $350M+ Series E</a></strong> — Feb 2026 — SN50 targets agentic inference (vendor: ~5× compute / ~4× network vs. SN40L); SoftBank early deploy; H2 2026 shipping; Intel heterogeneous-inference collaboration.</li>
</ul>

<a name="Mythic"></a>
<div align="center" class="vendor-logo"><a href="https://mythic.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Mythic_logo.png" height="20" loading="lazy" alt="Mythic" /></a></div>
<div align="center" class="vendor-title"><h3>Mythic — analog compute-in-memory</h3></div>
<p class="vendor-blurb">Mythic builds Analog Processing Units (APUs) that use flash-based compute-in-memory for energy-efficient inference at the edge and in data centers. After years of analog AI development, 2025–2026 funding and the Videantis acquisition add digital processor IP for a hybrid analog/digital platform aimed at robotics, automotive, and defense.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.businesswire.com/news/home/20251217546249/en/Mythic-to-Challenge-AIs-GPU-Pantheon-with-100x-Energy-Advantage-and-Oversubscribed-%24125M-Raise">$125M Series D</a></strong> — Dec 2025 — oversubscribed DCVC-led round (Honda, Lockheed Martin among strategics) to scale APUs and chiplet next-gen products.</li>
<li><strong><a href="https://mythic.ai/whats-new/mythic-acquires-videantis-one-of-europes-leading-digital-processor-ip-companies-to-build-the-worlds-most-energy-efficient-ai-compute-platform/">Acquires Videantis</a></strong> — May 2026 — Videantis digital processor IP + software joins Mythic analog CIM for a hybrid efficiency-focused platform.</li>
</ul>

<a name="Hailo"></a>
<div align="center" class="vendor-logo"><a href="https://hailo.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Hailo_logo.png" height="60" loading="lazy" alt="Hailo" /></a></div>
<div align="center" class="vendor-title"><h3>Hailo — edge AI accelerators</h3></div>
<p class="vendor-blurb">Hailo designs high-efficiency edge AI accelerators for vision and, with Hailo-10, on-device generative AI. Hailo-8 established the structure-sparsity / efficient-NPU brand in smart cameras and industrial vision; Hailo-10H adds LLM/VLM-class GenAI at low watts with automotive qualification paths.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://hailo.ai/company-overview/newsroom/news/hailo-announces-general-availability-of-hailo-10h-edge-ai-accelerator-with-generative-ai-capabilities/">Hailo-10H GA for edge GenAI</a></strong> — Jul 2025 — second-gen Hailo-10H for on-device LLM/VLM/GenAI (~40 TOPS INT4, ~2.5W typical); AEC-Q100 Grade 2 with 2026 SOP targeting.</li>
</ul>

<a name="Furiosa"></a>
<div align="center" class="vendor-logo"><a href="https://www.furiosa.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Furiosa_logo.png" height="60" loading="lazy" alt="FuriosaAI" /></a></div>
<div align="center" class="vendor-title"><h3>FuriosaAI — RNGD / TCP</h3></div>
<p class="vendor-blurb">Korea-based FuriosaAI builds Tensor Contraction Processor (TCP) accelerators for datacenter inference. After earlier Warboy edge/vision chips, RNGD (TSMC 5nm) targets LLM and agentic serving in air-cooled multi-card servers, with a Broadcom collaboration to scale into multi-die Ethernet/PCIe platforms.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://furiosa.ai/blog/rngd-enters-mass-production-the-high-performance-ai-accelerator-for-any-data-center">RNGD mass production</a></strong> — Jan 2026 — RNGD (~180W PCIe) volume shipment for LLM/agentic inference; NXT RNGD servers pack multiple cards into ~3kW-class air-cooled systems.</li>
<li><strong><a href="https://furiosa.ai/blog/furiosaai-partners-with-broadcom-to-build-next-generation-inference-platform-for-the-agentic-era">Broadcom inference partnership</a></strong> — May 2026 — evolve TCP into a scale-up multi-die inference platform with Broadcom Ethernet/PCIe switching.</li>
</ul>

<a name="Kinara"></a>
<div align="center" class="vendor-logo"><a href="https://www.kinara.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Deepvision_logo.png" height="40" loading="lazy" alt="Kinara" /></a></div>
<div align="center" class="vendor-title"><h3>Kinara (ex–Deep Vision)</h3></div>
<p class="vendor-blurb">Kinara (formerly Deep Vision) builds Ara/Prisma-class edge NPUs for vision and on-device GenAI inference. The company rebranded and scaled edge AI SKUs before NXP announced an acquisition (2025) to fold Kinara into NXP’s industrial and automotive edge AI portfolio.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.nxp.com/company/about-nxp/newsroom/NW-NXP-TO-ACQUIRE-KINARA">NXP to acquire Kinara</a></strong> — Feb 2025 — NXP acquisition of Kinara for edge AI NPUs used in vision and on-device GenAI; expands NXP industrial/automotive AI.</li>
</ul>

<a name="SiMa"></a>
<div align="center" class="vendor-logo"><a href="https://sima.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/SiMa_logo.png" height="40" loading="lazy" alt="SiMa.ai" /></a></div>
<div align="center" class="vendor-title"><h3>SiMa.ai — Modalix MLSoC</h3></div>
<p class="vendor-blurb">SiMa.ai builds MLSoC platforms for edge / Physical AI—robots, industrial, automotive, and vision—combining CPU, ML accelerator, and software (Palette / LLiMa) for CNN through Transformer/LLM workloads at low power. Modalix is the second-generation production platform after the first MLSoC.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://sima.ai/press-release/sima-ai-next-gen-platform-for-physical-ai-in-production/">Modalix platform in production</a></strong> — Aug 2025 — Modalix ships for Physical AI under ~10W with SoM/devkits and LLiMa for on-device LLM deployment.</li>
</ul>

<a name="d-matrix"></a>
<div align="center" class="vendor-logo"><a href="https://www.d-matrix.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/d-matrix_logo.png" height="60" loading="lazy" alt="d-Matrix" /></a></div>
<div align="center" class="vendor-title"><h3>d-Matrix — Corsair</h3></div>
<p class="vendor-blurb">d-Matrix builds digital compute-in-memory accelerators (Corsair) for low-latency, high-efficiency datacenter LLM inference—contrasting analog CIM approaches with a digital datapath while still attacking the memory-wall bottleneck that dominates decode.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.d-matrix.ai/announcements/d-matrix-corsair-ai-inference-platform-enters-full-production-to-meet-customer-demand/">Corsair enters full production</a></strong> — Jun 2026 — Corsair digital in-memory inference platform in volume production (TSMC N6); shipping to priority hyperscalers, neoclouds, and frontier labs.</li>
<li><strong><a href="https://cryptobriefing.com/d-matrix-corsair-challenges-nvidia-ai-inference/">Series C / $2B valuation</a></strong> — Nov 2025 — $275M Series C (incl. Microsoft M12) at ~$2B valuation to scale Corsair rack-scale inference.</li>
</ul>

<a name="Blaize"></a>
<div align="center" class="vendor-logo"><a href="https://www.blaize.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Blaize_logo.png" height="40" loading="lazy" alt="Blaize" /></a></div>
<div align="center" class="vendor-title"><h3>Blaize — Graph Streaming Processor</h3></div>
<p class="vendor-blurb">Blaize’s Graph Streaming Processor (GSP) targets graph-native edge AI for vision and GenAI in industrial and smart-city deployments. After years as a private edge-AI vendor, Blaize listed via SPAC (Nasdaq: BZAI) in 2025 to scale product and go-to-market.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.blaize.com/">Blaize AI edge platforms</a></strong> — 2025 — listed via SPAC; GSP architecture for edge AI vision / GenAI in industrial and smart-city deployments.</li>
</ul>

<a name="SynSense"></a>
<div align="center" class="vendor-logo"><a href="https://www.synsense.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/aiCTX_logo.png" height="40" loading="lazy" alt="SynSense" /></a></div>
<div align="center" class="vendor-title"><h3>SynSense (ex–aiCTX)</h3></div>
<p class="vendor-blurb">SynSense (formerly aiCTX) builds neuromorphic and event-based sensing+compute chips (Speck, Xylo) for ultra-low-power always-on perception. Collaborations such as with iniVation extend event-camera + neuromorphic pipelines for edge AI.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.synsense.ai/">SynSense neuromorphic products</a></strong> — 2025–2026 — Speck/Xylo-class neuromorphic chips and event-based vision+compute offerings (incl. prior iniVation collaboration) for always-on edge sensing.</li>
</ul>

<a name="Sagence"></a>
<div align="center" class="vendor-logo"><a href="https://www.sagence.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AnalogInference_logo.png" height="60" loading="lazy" alt="Sagence AI" /></a></div>
<div align="center" class="vendor-title"><h3>Sagence AI (ex–Analog Inference)</h3></div>
<p class="vendor-blurb">Sagence AI (rebranded from Analog Inference in Nov 2024) develops analog compute-in-memory accelerators aimed at energy-efficient LLM and vision inference for datacenter and edge deployments—part of the broader analog-AI cohort seeking orders-of-magnitude efficiency vs. digital GPUs on inference.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.sagence.ai/">Sagence AI analog CIM</a></strong> — 2025–2026 — continues analog compute-in-memory accelerators (ex–Analog Inference) aimed at energy-efficient datacenter/edge LLM and vision inference.</li>
</ul>

<div align="center" class="section-title"><h2><a name="China_AI_Chips"></a>V. China AI Accelerator Vendors</h2></div>
<hr class="section-rule" />
<p>Domestic training/inference accelerators have become central under export-control and procurement policies. Coverage below highlights widely reported product lines; treat performance claims as vendor-/press-reported unless independently benchmarked.</p>

<a name="HuaweiAscend"></a>
<div align="center" class="vendor-logo"><a href="https://www.huawei.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/HUAWEI_logo.png" height="40" loading="lazy" alt="HUAWEI logo" /></a>
&nbsp;&nbsp;
<a href="https://www.hisilicon.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/HiSilicon_logo.png" height="40" loading="lazy" alt="HiSilicon logo" /></a></div>
<div align="center" class="vendor-title"><h3>Huawei Ascend / HiSilicon</h3></div>
<p class="vendor-blurb">Huawei’s Ascend line (HiSilicon) is China’s most widely deployed domestic training/inference accelerator family. Ascend 910 established the high-end; 910B/910C scaled under export controls into Atlas servers and SuperPoD / CloudMatrix supernodes. Ascend 950-class (950DT training / 950PR inference messaging) and Atlas 950 SuperPoD push UnifiedBus optical scale-up to thousands of NPUs as a single logical node, with Cann/MindSpore as the software stack.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.huawei.com/en/news/2026/3/mwc-superpod-ai">Atlas 950 SuperPoD at MWC 2026</a></strong> — Mar 2026 — global debut of Atlas 950 SuperPoD on UnifiedBus; scales from 64 NPUs/cabinet toward up to 8,192 Ascend 950-class NPUs for large-model train/infer.</li>
<li><strong><a href="https://it-news.uk/posts/huawei-atlas-950-superpod-waic-2026/">Atlas 950 SuperPoD at WAIC 2026</a></strong> — Jul 2026 — first public hardware demonstration planned at WAIC Shanghai; single-cabinet 64-card base with global unified memory addressing for trillion-parameter models.</li>
</ul>

<a name="Cambricon"></a>
<div align="center" class="vendor-logo"><a href="https://www.cambricon.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cambricon_logo.png" height="50" loading="lazy" alt="Cambricon" /></a></div>
<div align="center" class="vendor-title"><h3>Cambricon (寒武纪)</h3></div>
<p class="vendor-blurb">Cambricon is China’s leading pure-play AI-chip vendor, spanning edge IP/SoCs and cloud MLU / Siyuan accelerators. After an early edge-IP era, the company refocused on cloud training/inference cards for Chinese internet and intelligent-computing customers, with aggressive 2026 volume plans.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://en.shuziqushi.com/new343300.html">Siyuan 690 mass production</a></strong> — 2026 — next-gen Siyuan/MLU 690 cloud accelerators in mass production/delivery (reports: dual-die, ~196GB HBM3, &gt;700 TFLOPS FP16-class); Q1 profit surged on domestic cloud demand.</li>
<li><strong><a href="https://www.tomshardware.com/tech-industry/semiconductors/cambricon-targets-500000-ai-chips-in-2026-as-china-accelerates-domestic-hardware-push">500,000 AI chips target for 2026</a></strong> — Aggressive 2026 volume plans for Siyuan 590/690-class accelerators serving Chinese internet/cloud customers as a leading pure-play domestic AI-chip vendor.</li>
</ul>

<a name="Biren"></a>
<div align="center" class="vendor-logo"><a href="https://www.birentech.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Biren_logo.png" height="48" loading="lazy" alt="Biren" /></a></div>
<div align="center" class="vendor-title"><h3>Biren Technology (壁仞)</h3></div>
<p class="vendor-blurb">Biren builds high-performance GPGPU / AI accelerators (BR100 class) positioned as domestic alternatives for training and inference. After years of product development under export-control pressure, Biren listed in Hong Kong in early 2026, raising capital to scale production and software.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.reuters.com/world/asia-pacific/china-ai-chipmaker-biren-surges-82-hong-kong-debut-kicking-off-2026-listings-2026-01-02/">Hong Kong listing debut</a></strong> — Jan 2026 — listed 6082.HK, raising ~HK$5.58B; BR100-class accelerators as high-performance domestic alternatives.</li>
</ul>

<a name="MooreThreads"></a>
<div align="center" class="vendor-logo"><a href="https://www.mthreads.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/MooreThreads_logo.png" height="48" loading="lazy" alt="Moore Threads" /></a></div>
<div align="center" class="vendor-title"><h3>Moore Threads (摩尔线程)</h3></div>
<p class="vendor-blurb">Moore Threads develops full-function GPUs for graphics and AI (MTT S-series) with the MUSA software stack. The company completed a large STAR Market IPO in late 2025 amid China’s domestic GPU push, targeting intelligent-computing centers and PC/GPU markets.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.cnbc.com/2025/12/05/china-nvidia-moore-threads-trading-debut-1-billion-listing-ipo-shanghai-gpu-enflame-biren.html">Shanghai trading debut</a></strong> — Dec 2025 — ~$1.1B STAR Market IPO; MTT S4000/S5000-class AI cards and MUSA stack in the domestic GPU wave.</li>
</ul>

<a name="MetaX"></a>
<div align="center" class="vendor-logo"><a href="https://www.metax-tech.com/en/about/about.html"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/MetaX_logo.png" height="48" loading="lazy" alt="MetaX" /></a></div>
<div align="center" class="vendor-title"><h3>MetaX (沐曦)</h3></div>
<p class="vendor-blurb">MetaX (沐曦) ships C-series GPUs for training and inference with the MXMACA software stack for AI clusters and intelligent-computing centers. After listing on STAR in Dec 2025, the company reported strong revenue growth into 2026 as domestic GPU demand rose.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.caixinglobal.com/2026-03-26/chinese-gpu-maker-metax-doubles-revenue-amid-push-for-domestic-chips-102427800.html">MetaX doubles revenue</a></strong> — C500 mass production; C600 domestic-process follow-on; STAR 688802.SH (listed Dec 2025) with MXMACA for AI clusters.</li>
</ul>

<a name="Hygon"></a>
<div align="center" class="vendor-logo"><a href="https://www.hygon.cn/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Hygon_logo.png" height="48" loading="lazy" alt="Hygon" /></a></div>
<div align="center" class="vendor-title"><h3>Hygon (海光) DCU</h3></div>
<p class="vendor-blurb">Hygon’s Deep Computing Unit (DCU) accelerators are GPGPU-class chips widely used in China for large-model training and inference, paired with the DTK software stack. Hygon also ships x86 CPUs; the DCU line is the AI-relevant product for intelligent-computing centers.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.trendforce.com/news/2026/04/29/news-huawei-ascend-cambricon-and-hygon-completed-day-0-adaptation-to-deepseek-v4/">DeepSeek-V4 Day-0 adaptation</a></strong> — 2025–2026 — DCU + DTK widely used for LLM train/infer; same-day DeepSeek model adaptations reported with Ascend and Cambricon.</li>
</ul>

<a name="Iluvatar"></a>
<div align="center" class="vendor-logo"><a href="https://www.iluvatar.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Iluvatar_logo.png" height="48" loading="lazy" alt="Iluvatar CoreX" /></a></div>
<div align="center" class="vendor-title"><h3>Iluvatar CoreX (天数智芯)</h3></div>
<p class="vendor-blurb">Iluvatar CoreX (天数智芯) designs general-purpose GPUs for AI training and inference (BI-V series) with a multi-generation architecture roadmap. Hong Kong-listed, the company publicly frames Tianshu / Tianxuan / Tianji / Tianquan messaging against NVIDIA Hopper→Blackwell→Rubin class platforms.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.scmp.com/tech/big-tech/article/3341368/iluvatar-corex-targets-nvidias-rubin-gpu-road-map-amid-china-chip-push">Roadmap vs. NVIDIA Rubin</a></strong> — Jan 2026 — multi-generation GPU roadmap; BI-V150-class products already in AI train/infer deployments.</li>
</ul>

<a name="Enflame"></a>
<div align="center" class="vendor-logo"><a href="https://www.enflame-tech.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Enflame_logo.png" height="48" loading="lazy" alt="Enflame" /></a></div>
<div align="center" class="vendor-title"><h3>Enflame (燧原)</h3></div>
<p class="vendor-blurb">Enflame (燧原) builds CloudBlazer / iGCU accelerators for domestic training and inference in intelligent-computing centers. The TopsRider software stack targets LLM workloads alongside hardware refreshes through 2024–2026.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.enflame-tech.com/">CloudBlazer / iGCU accelerators</a></strong> — 2025–2026 — domestic train/infer GPUs deployed in China intelligent-computing centers with TopsRider software updates for LLM workloads.</li>
</ul>

<a name="Horizon"></a>
<div align="center" class="vendor-logo"><a href="https://www.horizon.auto/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Horizon_Robotics_logo.png" height="50" loading="lazy" alt="Horizon Robotics" /></a></div>
<div align="center" class="vendor-title"><h3>Horizon Robotics (地平线)</h3></div>
<p class="vendor-blurb">Horizon Robotics (地平线) is a leading China automotive AI SoC vendor. Journey-series chips (through Journey 6 with BPU Nash) power L2+ assisted driving in many passenger vehicles, with increasing Transformer support for BEV/occupancy and end-to-end driving models.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.horizon.auto/en/solutions/horizon-journey/horizon-journey6">Journey 6 / BPU Nash</a></strong> — 2025–2026 — Journey 6 automotive AI SoCs with BPU Nash and stronger Transformer support widely designed into China passenger vehicles for L2+ ADAS.</li>
</ul>

<a name="BlackSesame"></a>
<div align="center" class="vendor-logo"><a href="https://www.blacksesame.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Blacksesame_logo.png" height="50" loading="lazy" alt="Black Sesame" /></a></div>
<div align="center" class="vendor-title"><h3>Black Sesame Technologies (黑芝麻智能)</h3></div>
<p class="vendor-blurb">Black Sesame Technologies (黑芝麻智能) designs automotive-grade ADAS/AD SoCs (Huashan family). Hong Kong-listed in 2024, the company focuses on safety-certified L2+/L3 platforms; A1000-family chips are reported in mass-production vehicles, with A2000 extending toward higher-performance and cross-domain AI.</p>
<p class="latest-label"><strong>Latest</strong></p>
<ul class="latest-list">
<li><strong><a href="https://www.blacksesame.com/en/huashan-a1000/">Huashan A1000 / A2000 path</a></strong> — 2025–2026 — A1000-family chips reported in mass-production L2+/L3 vehicles; A2000 messaging extends toward higher-performance and cross-domain AI inference.</li>
</ul>


<a name="AIChipCompilers"></a>

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

<a name="AIChipBenchmarks"></a>

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

<a name="Reference"></a>

<div align="center" class="section-title"><h2>Reference</h2></div>

<hr class="section-rule" />

<div class="resource-list">
<p><em>Archive / background reading (not a current vendor list).</em></p>
1. <strong><a href="https://birenresearch.github.io/AIChip_Paper_List/">AI Chip Paper List</a></strong><br>
2. <strong><a href="https://nicsefc.ee.tsinghua.edu.cn/projects/neural-network-accelerator/">Neural Network Accelerator Comparison</a></strong> (Tsinghua)<br>
3. <a href="http://eyeriss.mit.edu/tutorial.html">Tutorial on Hardware Architectures for Deep Neural Networks</a> (MIT Eyeriss)<br>
4. <strong>"What We Talk About When We Talk About AI Chip"</strong> —
   <a href="https://mp.weixin.qq.com/s/SbX5yz5d3GXaLcl15DO6OQ">#1</a> ·
   <a href="https://mp.weixin.qq.com/s/zvgDgKpIMIRLFUEW0fFOeg">#2</a> ·
   <a href="https://mp.weixin.qq.com/s/CKHs5yblcMur4h2BwUBICw">#3</a> ·
   <a href="https://mp.weixin.qq.com/s/hFnHhaWWYTFRUsD3HlMbLw">#4</a><br>
5. <a href="https://khairy2011.medium.com/tpu-vs-gpu-vs-cerebras-vs-graphcore-a-fair-comparison-between-ml-hardware-3f5a19d89e38">TPU vs GPU vs Cerebras vs Graphcore</a> (comparison essay)<br>
6. "White Paper on AI Chip Technologies 2018" —
   <a href="https://cloud.tsinghua.edu.cn/f/9aa0a4f0a5684cc48495/?dl=1">download</a> ·
   <a href="https://drive.google.com/open?id=1ieDm0bpjVWl5MnSESRs92EcmoSzG5vcm">Google Drive</a><br>
</div>

<div align="center">
<a href="http://www.reliablecounter.com" target="_blank"><img src="http://www.reliablecounter.com/count.php?page=https://basicmi.github.io/AI-Chip/&digit=style/plain/3/&reloads=1" alt="laptop" title="laptop" border="0"></a>
</div>

