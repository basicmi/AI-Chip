<header class="page-header" id="top" align="center">
<h1 class="site-brand">AI Chip (ICs and IPs)</h1>
<div class="hero-art"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AI-chips.png" loading="lazy" alt="AI chips illustration" /></div>
<p class="editor-line">Editor <a href="https://www.linkedin.com/in/shan-tang-27342510/"><strong>S.T.</strong></a> (LinkedIn)</p>
<p class="wechat-line"><strong>WeChat / 微信公众号</strong> · <a href="https://mp.weixin.qq.com/mp/appmsgalbum?action=getalbum&amp;__biz=MzI3MDQ2MjA3OA==&amp;scene=1&amp;album_id=1374108991751782402&amp;count=3#wechat_redirect">StarryHeavensAbove</a> — AI chip articles</p>
<div class="wechat-qr"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/qrcode_for_weichat_258.jpg" height="100" loading="lazy" alt="WeChat QR code" /></div>
<div class="landscape-map"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AI_Chip_Landscape_v0p8.png" loading="lazy" alt="AI Chip Landscape v0.8 (2026)" /></div>
<p class="page-intro">A living directory of AI accelerators (ICs &amp; IPs) — hyperscaler custom silicon, GPU/NPU vendors, IP houses, startups, and China domestic accelerators. Prefer official / primary sources; performance claims are often vendor-reported.</p>
</header>

 
<div align="center" class="section-title"><h2>Latest updates</h2></div>
<p class="refresh-note" align="center"><em>Last refreshed: July 2026 — defunct vendors removed; pre-2024 entries cleared (except NVIDIA/Google lineage); landscape map v0.8.</em></p>
<hr class="section-rule" />

<ul class="updates-list">
<li><strong>Hygiene</strong>: removed shut-down / pivoted AI-chip vendors; cleared pre-2024 news for other orgs.</li>
<li><strong>NVIDIA</strong>: full GPU AI lineage CUDA/Pascal → Volta → Hopper → Blackwell → <a href="#Nvidia">Rubin</a>.</li>
<li><strong>Google</strong>: full <a href="#Google">TPU</a> lineage v1 → Trillium (v6e) → Ironwood (v7).</li>
<li><strong>AMD / Intel</strong>: <a href="#AMD">MI350</a>; <a href="#Habana">Gaudi 3</a>.</li>
<li><strong>Custom silicon</strong>: AWS <a href="#Amazon_AWS">Trainium2</a>, Azure <a href="#Microsoft">Maia</a>, Meta <a href="#Facebook">MTIA</a>, <a href="#OpenAI">Jalapeño</a>, <a href="#Anthropic">Anthropic</a> deals.</li>
<li><strong>Edge</strong>: <a href="#SiMa">SiMa</a>, <a href="#Hailo">Hailo-10H</a>, <a href="#Tesla">Tesla AI5</a>, <a href="#BlackSesame">Black Sesame</a>.</li>
<li><strong>Active startups</strong>: <a href="#Cerebras">Cerebras</a>, <a href="#Furiosa">Furiosa</a>, <a href="#Etched">Etched</a>, <a href="#SambaNova">SambaNova</a>, <a href="#Mythic">Mythic</a>, <a href="#Kinara">Kinara</a>, …</li>
<li><strong>China</strong>: <a href="#China_AI_Chips">Ascend / Cambricon / Biren / MetaX / Hygon / Iluvatar</a> …</li>
<li><strong>Map</strong>: regenerated AI Chip Landscape <strong>v0.8</strong> (2026).</li>
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

<p>Architecture history for AI/HPC (CUDA era → rack-scale platforms). Figures are vendor-reported.</p>

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

<p><strong><a href="https://nvidianews.nvidia.com/news/rubin-platform-ai-supercomputer">NVIDIA Rubin platform announcement</a></strong></p>
<blockquote>
  <p>CES 2026 — Vera Rubin platform for agentic AI and large MoE models; NVIDIA claims large gains in inference token cost and training GPU-efficiency vs. Blackwell.</p>
</blockquote>

<p><strong><a href="https://nvidianews.nvidia.com/news/nvidia-blackwell-platform-arrives-to-power-a-new-era-of-computing">NVIDIA Blackwell platform</a></strong></p>
<blockquote>
  <p>GTC 2024 — B200 Tensor Core GPU and GB200 Grace Blackwell Superchip / NVL72 systems for generative AI training and real-time LLM inference.</p>
</blockquote>

<p><a href="https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth">Hopper architecture in-depth</a> ·
<a href="https://www.nvidia.com/en-us/data-center/technologies/hopper-architecture/">Hopper</a> ·
<a href="https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/">Blackwell</a></p>

<a name="Intel"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Intel_logo.png" height="60" loading="lazy" alt="Intel" /></div>
<div align="center" class="vendor-title"><h3>Intel / Habana Gaudi</h3></div>
<a name="Habana"></a>
<p><strong><a href="https://newsroom.intel.com/artificial-intelligence/vision-2024-enterprise-ai-gaudi-3-open-systems-strategy">Intel Unleashes Enterprise AI with Gaudi 3</a></strong></p>
<blockquote>
  <p>Intel Vision 2024 — Gaudi 3 targets generative AI training and inference with Ethernet scale-out. Intel positions Gaudi 3 for enterprise GenAI price/performance vs. GPU alternatives, with OEM availability through Dell, HPE, Lenovo, Supermicro and cloud partners.</p>
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

<a name="Samsung"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Samsung_logo.png" height="35" loading="lazy" alt="Samsung" /></div>
<p><strong><a href="https://semiconductor.samsung.com/processor/mobile-processor/exynos-2500/">Samsung Exynos 2500</a></strong></p>
<blockquote>
  <p>2025 flagship mobile SoC on Samsung 3nm GAA with a substantially upgraded NPU (Samsung cites up to ~59 TOPS and large on-device AI gains vs. Exynos 2400) for generative AI and privacy-preserving on-device inference.</p>
</blockquote>

<a name="MediaTek"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/MediaTek_logo.png" height="40" loading="lazy" alt="MediaTek" /></div>

<p><strong><a href="https://www.mediatek.com/press-room/mediateks-dimensity-9400-flagship-soc-offers-extreme-performance-and-efficiency-for-the-latest-ai-experiences">MediaTek Dimensity 9400 — 8th Gen NPU for agentic AI</a></strong></p>
<blockquote>
  <p>Oct 2024 — Flagship Dimensity 9400 (TSMC 3nm) pairs an all-big-core CPU with MediaTek’s 8th-generation NPU 890. MediaTek highlights on-device LoRA training, high-quality video generation, MoE LLM support, and the Dimensity Agentic AI Engine (DAE), with claimed large gains in LLM prompt / diffusion performance vs. Dimensity 9300.</p>
</blockquote>

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

<a name="Marvell"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Marvell_logo.png" height="60" loading="lazy" alt="Marvell" /></div>
<p><strong><a href="https://www.marvell.com/products/data-processing-units.html">Custom AI ASICs + DPUs</a></strong></p>
<blockquote>
  <p>2024–2026 — Beyond OCTEON / ARMADA DPUs, Marvell is a major custom AI accelerator design partner for hyperscalers (widely reported programs include AWS Trainium/Inferentia-class and Microsoft Maia-class silicon), complementing Broadcom’s XPU franchise.</p>
</blockquote>

<a name="Broadcom"></a>
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

<a name="Google"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Google_logo.png" height="40" loading="lazy" alt="Google" /></div>
<div align="center" class="vendor-title"><h3>Google — TPU lineage</h3></div>

<p>Cloud TPU generation history (Edge TPU / Pixel Tensor noted as related). Specs are Google-reported.</p>

<p><strong>Early generations</strong></p>
<ul>
<li><strong>TPU v1 (2015)</strong> — inference-only systolic MXU (INT8) inside Google production services; public details followed ~2016–2017.</li>
<li><strong>TPU v2 (2017)</strong> — training + inference, bfloat16, HBM, first multi-chip pods.</li>
<li><strong>TPU v3 (2018)</strong> — higher compute, liquid cooling at pod scale.</li>
<li><strong>TPU v4 (2021)</strong> — denser pods, 3D torus + optical circuit switches; backbone for many Google foundation-model trainings.</li>
</ul>

<p><strong>Split SKUs &amp; GenAI scale-up</strong></p>
<ul>
<li><strong>TPU v5e (2023)</strong> — cost-efficient training/inference at volume.</li>
<li><strong>TPU v5p (2023)</strong> — high-end large-pod training performance.</li>
<li><strong>Trillium / TPU v6e (2024)</strong> — larger MXUs; Google cites ~4.7× peak compute/chip vs. v5e, with higher HBM capacity/bandwidth and better energy efficiency.</li>
<li><strong>Ironwood / TPU v7 (2025)</strong> — inference-leaning generation with native low-precision (FP8-class) paths and very large pod configurations.</li>
</ul>

<p><strong>Related Google silicon</strong></p>
<ul>
<li><strong>Edge TPU</strong> — Coral edge inference ASIC.</li>
<li><strong>Google Tensor (Pixel)</strong> — mobile SoC ML blocks (separate from Cloud TPU).</li>
</ul>

<p><strong><a href="https://cloud.google.com/blog/products/compute/introducing-trillium-6th-gen-tpus">Introducing Trillium (TPU v6e)</a></strong></p>
<blockquote>
  <p>Sixth-generation Cloud TPU for foundation-model training and serving; Google cites large per-chip compute and efficiency gains vs. TPU v5e.</p>
</blockquote>

<p><strong><a href="https://docs.cloud.google.com/tpu/docs/release-notes">Ironwood (TPU v7 / TPU7x) availability notes</a></strong></p>
<blockquote>
  <p>Seventh-generation Cloud TPU family for large-scale training and inference (LLMs, MoEs, diffusion).</p>
</blockquote>

<p><a href="https://cloud.google.com/transform/ai-specialized-chips-tpu-history-gen-ai">Google: 10 years of TPU history</a> ·
<a href="https://docs.cloud.google.com/tpu/docs/v6e">TPU v6e architecture docs</a> ·
<a href="https://cloud.google.com/tpu">Cloud TPU</a> ·
<a href="https://cloud.google.com/edge-tpu/">Edge TPU</a></p>

<a name="Amazon_AWS"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Amazon_AWS.png" height="50" loading="lazy" alt="Amazon AWS" /></div>
<p><strong><a href="https://aws.amazon.com/blogs/aws/amazon-ec2-trn2-instances-and-trn2-ultraservers-for-aiml-training-and-inference-is-now-available/">Amazon EC2 Trn2 / Trainium2 UltraServers</a></strong></p>
<blockquote>
  <p>2024–2025 — Trainium2-powered Trn2 instances and UltraServers for generative AI training and inference with NeuronLink scale-up; Inferentia2 (Inf2) continues for cost-efficient LLM serving.</p>
</blockquote>

<a name="Microsoft"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Microsoft_logo.png" height="60" loading="lazy" alt="Microsoft" /></div>
<p><strong><a href="https://azure.microsoft.com/en-us/blog/azure-maia-for-the-era-of-ai-from-silicon-to-software-to-systems/">Azure Maia for the era of AI</a></strong></p>
<blockquote>
  <p>2024 — Microsoft’s first in-house AI accelerator, Azure Maia 100 (5nm, advanced packaging), co-designed for Azure AI / Copilot-class cloud workloads, with a software stack integrating PyTorch and ONNX Runtime.</p>
</blockquote>

<a name="OpenAI"></a>
<div align="center"><h3>OpenAI</h3></div>

<p><strong><a href="https://openai.com/index/openai-broadcom-jalapeno-inference-chip/">OpenAI and Broadcom unveil Jalapeño LLM inference chip</a></strong> · <a href="https://techcrunch.com/2026/06/24/openai-unveils-its-first-custom-chip-built-by-broadcom/">TechCrunch coverage</a></p>
<blockquote>
  <p>Jun 2026 — OpenAI’s first custom “Intelligence Processor,” Jalapeño, is an inference-optimized ASIC co-developed with Broadcom (networking + silicon implementation) for lower-cost, higher-utilization LLM serving. First step in a multi-generation platform with initial deployments targeted by end of 2026.</p>
</blockquote>

<a name="Anthropic"></a>
<div align="center"><h3>Anthropic</h3></div>

<p><strong><a href="https://www.anthropic.com/news/google-broadcom-partnership-compute">Anthropic expands partnership with Google and Broadcom for next-generation compute</a></strong></p>
<blockquote>
  <p>Apr 2026 — Expanded agreement for multiple gigawatts of next-generation Google TPU capacity (Broadcom SEC filings cite ~3.5 GW), expected online from 2027, on top of prior &gt;1 GW TPU commitments. Anthropic emphasizes a multi-hardware strategy: AWS Trainium (incl. Project Rainier), Google TPUs, and NVIDIA GPUs.</p>
</blockquote>

<a name="Apple"></a>

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

<a name="Alibaba"></a>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/alibaba_logo.png" height="60" loading="lazy" alt="Alibaba" /></div>

<p><strong><a href="https://www.eetimes.com/alibaba-unveils-own-ai-chip-mounting-direct-challenge-to-nvidia/">Alibaba Unveils Own AI Chip, Mounting Direct Challenge to Nvidia</a></strong></p>
<blockquote>
  <p>Sep 2025 — Alibaba’s T-Head Parallel Processing Unit (PPU / Zhenwu family) targets cloud AI training and inference as a domestic alternative under export-control constraints. Reports cite ~96GB HBM2e-class memory and high chip-to-chip bandwidth; deployed in large China Unicom / Alibaba Cloud clusters.</p>
</blockquote>

<p>

<a name="Baidu"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Baidu_logo.png" height="40" loading="lazy" alt="Baidu" /></div>
<p><strong><a href="https://www.baidu.com/">Baidu Kunlunxin</a></strong></p>
<blockquote>
  <p>2024–2026 — Kunlunxin P800-class GPUs and follow-ons remain a core China training/inference option in Baidu Cloud / ERNIE deployments, with continued software stack updates for large-model serving.</p>
</blockquote>

<a name="Tencent_Cloud"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tencent_Cloud_logo.png" height="30" loading="lazy" alt="Tencent Cloud" /></div>
<p><strong>Tencent Cloud AI accelerators (Zixiao / custom)</strong></p>
<blockquote>
  <p>2024–2026 — Tencent continues deploying proprietary and partner AI accelerators across Tencent Cloud for recommendation, multimodal, and LLM inference/training inside its China cloud footprint.</p>
</blockquote>

<a name="Facebook"></a>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/facebook_logo.png" height="50" loading="lazy" alt="Meta" /></div>

<p><strong><a href="https://ai.meta.com/blog/meta-mtia-scale-ai-chips-for-billions/">Four MTIA Chips in Two Years: Scaling AI Experiences for Billions</a></strong></p>
<blockquote>
  <p>Meta describes a multi-generation MTIA roadmap (including MTIA 300–500 class chips) with modular chiplet designs and accelerating deployment cadence through 2026–2027.</p>
</blockquote>

<a name="Tesla"></a>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tesla_logo.png" height="60" loading="lazy" alt="Tesla" /></div>

<p><strong><a href="https://electrek.co/2026/04/15/tesla-ai5-chip-taped-out-musk-ai6-dojo3/">Tesla AI5 chip taped out</a></strong></p>
<blockquote>
  <p>Apr 2026 — Elon Musk announced Tesla’s next-generation AI5 inference/training SoC has taped out, with AI6 / Dojo3 also mentioned as in progress. Volume production and broad vehicle deployment remain gated (reports point to mid–late 2027+); near-term vehicles continue on AI4 / interim upgrades, while AI5 is also positioned for Optimus and internal clusters.</p>
</blockquote>

<div align="center" class="section-title"><h2><a name="IP_Vendors"></a>III. Traditional IP Vendors</h2></div>

<hr class="section-rule" />

<a name="ARM"></a>

<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/ARM_logo.png" height="30" loading="lazy" alt="Arm" /></div>

<p><strong><a href="https://www.arm.com/products/silicon-ip-cpu/ethos/ethos-u85">Arm Ethos-U85</a></strong> — third-generation Ethos-U micro-NPU</p>
<blockquote>
  <p>Scales from 128–2048 MACs (up to ~4 TOPS @ 1 GHz) with native transformer operator support for edge / IoT generative and vision models; ~20% more energy efficient than Ethos-U65 and pairs with Cortex-M or Cortex-A hosts (Corstone-320 reference). Same Ethos toolchain / Vela compiler path as prior U-series.</p>
</blockquote>

<p><a href="https://newsroom.arm.com/news/iot-reference-design-platform-2024">Arm newsroom: Ethos-U85 + Corstone-320 IoT reference platform</a></p>

<p>

<a name="Synopsys"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Synopsys_logo.png" height="40" loading="lazy" alt="Synopsys" /></div>
<p><strong><a href="https://www.synopsys.com/designware-ip/processor-solutions/neural-processing-unit.html">Synopsys ARC NPX NPU IP</a></strong></p>
<blockquote>
  <p>2024–2026 — DesignWare ARC NPX neural processor IP family for automotive / consumer / datacenter SoCs, with multi-TOPS scalable configurations and ongoing toolchain updates.</p>
</blockquote>

<a name="Imagination"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Imagination_logo.png" height="60" loading="lazy" alt="Imagination" /></div>
<p><strong><a href="https://www.imaginationtech.com/products/ai/">Imagination AI / NNA IP</a></strong></p>
<blockquote>
  <p>2024–2026 — PowerVR Neural Network Accelerators (NNA) and GPU+NNA combinations for edge and automotive SoCs, with IMG Continuum software for transformer-class networks.</p>
</blockquote>

<a name="CEVA"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/CEVA_logo.png" height="40" loading="lazy" alt="CEVA" /></div>
<p><strong><a href="https://www.ceva-dsp.com/app/deep-learning/">CEVA edge AI / NPU IP</a></strong></p>
<blockquote>
  <p>2024–2026 — Low-power AI processor IP and DNN graph compiler for real-time embedded / automotive / IoT inference, including transformer-capable NeuPro-class offerings.</p>
</blockquote>

<a name="Cadence"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cadence_logo.png" height="40" loading="lazy" alt="Cadence" /></div>
<p><strong><a href="https://www.cadence.com/en_US/home/tools/ip/tensilica-ip/tensilica-ai-platform.html">Cadence Tensilica AI Platform</a></strong></p>
<blockquote>
  <p>2024–2026 — Tensilica NPU / AI DSP IP for on-device and automotive SoCs, with NeuroWeave toolchain updates for modern DNN / transformer workloads.</p>
</blockquote>

<a name="VeriSilicon"></a>
<div align="center" class="vendor-logo"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/VeriSilicon_logo.png" height="40" loading="lazy" alt="VeriSilicon" /></div>
<p><strong><a href="https://www.verisilicon.com/">VeriSilicon VIP / NPU IP &amp; design services</a></strong></p>
<blockquote>
  <p>2024–2026 — Acuity / VIP NPU IP and turnkey design services widely used in China and global edge SoCs for vision and on-device GenAI.</p>
</blockquote>

<div align="center" class="section-title"><h2><a name="Startups"></a>IV. Startups</h2></div>

<hr class="section-rule" />

<a name="Cerebras"></a>

<div align="center" class="vendor-logo"><a href="https://www.cerebras.net/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cerebras_logo.png" height="50" loading="lazy" alt="Cerebras" /></a></div>

<p><strong><a href="https://www.cerebras.net/press-release/cerebras-announces-third-generation-wafer-scale-engine">Cerebras Systems Unveils World’s Fastest AI Chip with 4 Trillion Transistors (WSE-3)</a></strong></p>
<blockquote>
  <p>March 2024 — WSE-3 (5nm) powers the CS-3 system with ~900,000 AI-optimized cores and 125 petaflops peak AI performance, doubling WSE-2 performance at the same power/price point for large-model training and high-throughput inference.</p>
</blockquote>

<a name="Graphcore"></a>

<div align="center" class="vendor-logo"><a href="https://www.graphcore.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Graphcore_logo.png" height="70" loading="lazy" alt="Graphcore" /></a></div>

<p><strong><a href="https://www.graphcore.ai/posts/graphcore-joins-softbank-group-to-build-next-generation-of-ai-compute">Graphcore joins SoftBank Group to build next generation of AI compute</a></strong></p>
<blockquote>
  <p>Jul 2024 — SoftBank acquired Graphcore as a wholly owned subsidiary (terms undisclosed; press estimates ~$500M). Graphcore continues under its own brand, with SoftBank backing next-generation IPU / AI compute development (including SoftBank-ecosystem follow-on investment reporting into 2026).</p>
</blockquote>

<p>

<p>

<a name="Tenstorrent"></a>
<div align="center" class="vendor-logo"><a href="http://tenstorrent.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Tenstorrent_logo.png" height="80" loading="lazy" alt="Tenstorrent" /></a></div>
<p><strong><a href="https://tenstorrent.com/">Tenstorrent Wormhole / Blackhole</a></strong></p>
<blockquote>
  <p>2024–2026 — Tensix-based AI processors (Wormhole shipping; Blackhole next) with open software (TT-Metalium) and growing rack-scale deployments; Jim Keller–led roadmap emphasizes scalable chiplet meshes.</p>
</blockquote>

<a name="Blaize"></a>
<div align="center" class="vendor-logo"><a href="https://www.blaize.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Blaize_logo.png" height="40" loading="lazy" alt="Blaize" /></a></div>
<p><strong><a href="https://www.blaize.com/">Blaize AI edge platforms (Nasdaq: BZAI)</a></strong></p>
<blockquote>
  <p>2025 — Listed via SPAC; Graph Streaming Processor (GSP) architecture for edge AI vision / GenAI inference in industrial and smart-city deployments.</p>
</blockquote>

<a name="Mythic"></a>

<div align="center" class="vendor-logo"><a href="https://mythic.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Mythic_logo.png" height="20" loading="lazy" alt="Mythic" /></a></div>

<p><strong><a href="https://www.businesswire.com/news/home/20251217546249/en/Mythic-to-Challenge-AIs-GPU-Pantheon-with-100x-Energy-Advantage-and-Oversubscribed-%24125M-Raise">Mythic raises $125M Series D for analog AI compute</a></strong></p>
<blockquote>
  <p>Dec 2025 — Oversubscribed round led by DCVC (strategic participation including Honda and Lockheed Martin) to scale Mythic’s Analog Processing Units (APUs) — flash-based compute-in-memory for energy-efficient inference at the edge and in data centers. Roadmap emphasizes chiplet-based next-gen APUs for robotics, automotive, and defense.</p>
</blockquote>
<p><strong><a href="https://mythic.ai/whats-new/mythic-acquires-videantis-one-of-europes-leading-digital-processor-ip-companies-to-build-the-worlds-most-energy-efficient-ai-compute-platform/">Mythic acquires Videantis for hybrid analog/digital AI platform</a></strong></p>
<blockquote>
  <p>May 2026 — Acquisition of Videantis GmbH adds a production digital processor IP + software stack alongside Mythic’s analog in-memory compute, targeting a hybrid platform with large claimed efficiency gains vs. conventional GPU inference.</p>
</blockquote>

<p>

<a name="Kinara"></a>
<div align="center" class="vendor-logo"><a href="https://www.kinara.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Deepvision_logo.png" height="40" loading="lazy" alt="Kinara" /></a></div>
<div align="center" class="vendor-title"><h3>Kinara (ex–Deep Vision)</h3></div>
<p><strong><a href="https://www.nxp.com/company/about-nxp/newsroom/NW-NXP-TO-ACQUIRE-KINARA">NXP to acquire Kinara (2025)</a></strong></p>
<blockquote>
  <p>Feb 2025 — NXP announced acquisition of Kinara (rebranded from Deep Vision) for edge AI / Ara / Prisma-class NPUs used in vision and on-device GenAI inference; expands NXP’s industrial and automotive edge AI portfolio.</p>
</blockquote>

<a name="Groq"></a>

<div align="center" class="vendor-title"><h3><a href="https://groq.com/">Groq</a></h3></div>

<p><strong><a href="https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Vera-Rubin-Opens-Agentic-AI-Frontier/default.aspx">NVIDIA Vera Rubin Opens Agentic AI Frontier (includes Groq LPU)</a></strong></p>
<blockquote>
  <p>In late 2025 NVIDIA licensed Groq’s LPU technology and brought on key engineering talent. At GTC 2026, NVIDIA described integrating Groq-class LPU engines into the Vera Rubin AI factory stack for low-latency / high-efficiency token generation alongside Rubin GPUs.</p>
</blockquote>

<a name="SambaNova"></a>

<div align="center" class="vendor-logo"><a href="https://sambanova.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/SambaNova_logo.png" height="40" loading="lazy" alt="SambaNova" /></a></div>

<p><strong><a href="https://sambanova.ai/press/sambanova-unveils-fastest-chip-for-agentic-ai-collaborates-with-intel-and-raises-350m">SambaNova unveils SN50 RDU for agentic AI, Intel collaboration, $350M+ Series E</a></strong></p>
<blockquote>
  <p>Feb 2026 — Fifth-generation Reconfigurable Dataflow Unit (SN50) targets large-scale agentic inference (vendor claims up to ~5× compute and ~4× network bandwidth vs. SN40L; scales toward 256 accelerators). SoftBank named as an early deploy partner; shipping targeted for H2 2026. Planned multi-year collaboration with Intel for heterogeneous inference stacks; oversubscribed Series E led with Vista / Cambium participation including Intel Capital.</p>
</blockquote>

<p>

<a name="SynSense"></a>
<div align="center" class="vendor-logo"><a href="https://www.synsense.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/aiCTX_logo.png" height="40" loading="lazy" alt="SynSense" /></a></div>
<div align="center" class="vendor-title"><h3>SynSense (ex–aiCTX)</h3></div>
<p><strong><a href="https://www.synsense.ai/">SynSense neuromorphic / event-based sensing+compute</a></strong></p>
<blockquote>
  <p>2024–2026 — Continues Speck / Xylo-class neuromorphic chips; 2024 iniVation collaboration and subsequent funding extend event-based vision + edge AI offerings.</p>
</blockquote>

<a name="Hailo"></a>

<div align="center" class="vendor-logo"><a href="https://hailo.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Hailo_logo.png" height="60" loading="lazy" alt="Hailo" /></a></div>

<p><strong><a href="https://hailo.ai/company-overview/newsroom/news/hailo-announces-general-availability-of-hailo-10h-edge-ai-accelerator-with-generative-ai-capabilities/">Hailo-10H generally available for edge generative AI</a></strong></p>
<blockquote>
  <p>Jul 2025 — Second-generation Hailo-10H brings on-device LLM / VLM / GenAI capabilities to the edge (~40 TOPS INT4 class, ~2.5W typical), while retaining vision workloads from the Hailo-8 generation. Automotive-qualified (AEC-Q100 Grade 2) with 2026 SOP targeting for some designs.</p>
</blockquote>

<p>

<p>

<p>

<p>

<p>

<p>

<p>

<p>

<a name="SiMa"></a>

<div align="center" class="vendor-logo"><a href="https://sima.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/SiMa_logo.png" height="40" loading="lazy" alt="SiMa.ai" /></a></div>

<p><strong><a href="https://sima.ai/press-release/sima-ai-next-gen-platform-for-physical-ai-in-production/">SiMa.ai Modalix platform for Physical AI in production</a></strong></p>
<blockquote>
  <p>Aug 2025 — Second-generation MLSoC Modalix ships for edge / Physical AI (robots, industrial, automotive, vision), targeting CNNs + Transformers/LLMs/GenAI under ~10W, with SoM/devkits and the LLiMa framework for on-device LLM deployment.</p>
</blockquote>

<p>

<a name="Furiosa"></a>

<div align="center" class="vendor-logo"><a href="https://www.furiosa.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Furiosa_logo.png" height="60" loading="lazy" alt="FuriosaAI" /></a></div>

<p><strong><a href="https://furiosa.ai/blog/rngd-enters-mass-production-the-high-performance-ai-accelerator-for-any-data-center">RNGD enters mass production for data-center AI inference</a></strong></p>
<blockquote>
  <p>Jan 2026 — FuriosaAI’s RNGD (Tensor Contraction Processor, TSMC 5nm, ~180W PCIe) entered volume shipment for LLM / agentic inference; NXT RNGD servers pack multiple cards into air-cooled, ~3kW-class systems.</p>
</blockquote>
<p><strong><a href="https://furiosa.ai/blog/furiosaai-partners-with-broadcom-to-build-next-generation-inference-platform-for-the-agentic-era">FuriosaAI partners with Broadcom on next-generation inference platform</a></strong></p>
<blockquote>
  <p>May 2026 — Strategic collaboration to evolve TCP into a scale-up multi-die inference platform with Broadcom Ethernet/PCIe switching for hyperscale agentic workloads.</p>
</blockquote>

<a name="Sagence"></a>
<div align="center" class="vendor-logo"><a href="https://www.sagence.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/AnalogInference_logo.png" height="60" loading="lazy" alt="Sagence AI" /></a></div>
<div align="center" class="vendor-title"><h3>Sagence AI (ex–Analog Inference)</h3></div>
<p><strong>Analog in-memory compute for datacenter inference (2024–2026)</strong></p>
<blockquote>
  <p>Rebranded from Analog Inference (Nov 2024). Continues analog compute-in-memory accelerators aimed at energy-efficient LLM / vision inference; active on the 2025–2026 AI infra circuit.</p>
</blockquote>

<p>

<p>

<p>

<a name="d-matrix"></a>
<div align="center" class="vendor-logo"><a href="https://www.d-matrix.ai/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/d-matrix_logo.png" height="60" loading="lazy" alt="d-Matrix" /></a></div>
<p><strong><a href="https://www.d-matrix.ai/">d-Matrix Corsair — digital in-memory compute for inference</a></strong></p>
<blockquote>
  <p>2024–2026 — Corsair accelerators target low-latency / high-efficiency datacenter LLM inference with digital compute-in-memory; expanding software and cloud partner footprint.</p>
</blockquote>

<a name="Etched"></a>
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

<a name="HuaweiAscend"></a>
<div align="center" class="vendor-logo"><a href="https://www.huawei.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/HUAWEI_logo.png" height="40" loading="lazy" alt="HUAWEI logo" /></a>
&nbsp;&nbsp;
<a href="https://www.hisilicon.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/HiSilicon_logo.png" height="40" loading="lazy" alt="HiSilicon logo" /></a></div>
<div align="center"><h3>Huawei Ascend / HiSilicon</h3></div>

<p><strong><a href="https://www.huawei.com/en/news/2025/9/hc-xu-keynote-speech">Huawei Atlas 900 A3 SuperPoD / Ascend 910C</a></strong></p>
<blockquote>
  <p>2025 — Huawei scaled Ascend 910B/910C deployments and launched Atlas 900 A3 SuperPoD (up to 384× Ascend 910C), also referred to in cloud form as CloudMatrix384-class supernodes, for large-model training and serving. Ascend 950-class follow-ons are on Huawei’s roadmap.</p>
</blockquote>

<a name="Cambricon"></a>
<div align="center" class="vendor-logo"><a href="https://www.cambricon.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Cambricon_logo.png" height="50" loading="lazy" alt="Cambricon" /></a></div>
<div align="center"><h3>Cambricon (寒武纪)</h3></div>

<p><strong><a href="https://www.tomshardware.com/tech-industry/semiconductors/cambricon-targets-500000-ai-chips-in-2026-as-china-accelerates-domestic-hardware-push">Cambricon targets 500,000 AI chips in 2026</a></strong></p>
<blockquote>
  <p>Reports describe aggressive 2026 volume plans for Siyuan / MLU-class accelerators (including Siyuan 590 and next-gen 690 messaging), serving Chinese internet/cloud customers as a leading pure-play domestic AI-chip vendor.</p>
</blockquote>

<a name="Biren"></a>
<div align="center"><h3><a href="https://www.birentech.com/">Biren Technology (壁仞)</a></h3></div>

<p><strong><a href="https://www.reuters.com/world/asia-pacific/china-ai-chipmaker-biren-surges-82-hong-kong-debut-kicking-off-2026-listings-2026-01-02/">China AI chipmaker Biren soars in Hong Kong debut</a></strong></p>
<blockquote>
  <p>Jan 2026 — Shanghai Biren Technology listed in Hong Kong (6082.HK), raising ~HK$5.58B. Best known for BR100-class GPGPU / AI accelerators positioned as high-performance domestic alternatives.</p>
</blockquote>

<a name="MooreThreads"></a>
<div align="center"><h3><a href="https://www.mthreads.com/">Moore Threads (摩尔线程)</a></h3></div>

<p><strong><a href="https://www.cnbc.com/2025/12/05/china-nvidia-moore-threads-trading-debut-1-billion-listing-ipo-shanghai-gpu-enflame-biren.html">Moore Threads surges over 400% on Shanghai trading debut</a></strong></p>
<blockquote>
  <p>Dec 2025 — Full-function GPU vendor (MTT S4000 / S5000 class AI cards, MUSA software stack) completed a ~$1.1B STAR Market IPO amid China’s domestic GPU push.</p>
</blockquote>

<p>

<a name="Enflame"></a>
<div align="center" class="vendor-title"><h3><a href="https://www.enflame-tech.com/">Enflame (燧原)</a></h3></div>
<p><strong>Enflame CloudBlazer / iGCU accelerators</strong></p>
<blockquote>
  <p>2024–2026 — Domestic training/inference GPUs (CloudBlazer series) deployed in China intelligent-computing centers with TopsRider software stack updates for LLM workloads.</p>
</blockquote>

<a name="Horizon"></a>
<div align="center" class="vendor-logo"><a href="https://www.horizon.auto/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Horizon_Robotics_logo.png" height="50" loading="lazy" alt="Horizon Robotics" /></a></div>
<div align="center" class="vendor-title"><h3>Horizon Robotics (地平线)</h3></div>
<p><strong><a href="https://www.horizon.auto/en/solutions/horizon-journey/horizon-journey6">Horizon Journey 6 / BPU Nash</a></strong></p>
<blockquote>
  <p>2024–2026 — Journey-series automotive AI SoCs (Journey 6 with BPU Nash / stronger Transformer support) widely designed into China passenger vehicles for L2+ assisted driving.</p>
</blockquote>

<a name="BlackSesame"></a>
<div align="center" class="vendor-logo"><a href="https://www.blacksesame.com/"><img src="https://github.com/basicmi/AI-Chip/raw/master/resource/Blacksesame_logo.png" height="50" loading="lazy" alt="Black Sesame" /></a></div>
<div align="center"><h3>Black Sesame Technologies (黑芝麻智能)</h3></div>

<p><strong><a href="https://www.blacksesame.com/en/huashan-a1000/">Huashan A1000 automotive-grade ADAS / AD SoCs</a></strong></p>
<blockquote>
  <p>Hong Kong-listed (02533.HK, Aug 2024) automotive AI SoC vendor. Huashan A1000-family chips target L2+/L3 assisted driving with automotive-grade safety certifications and are reported in mass-production vehicle models; Huashan A2000 messaging extends toward higher-performance / cross-domain AI inference.</p>
</blockquote>

<a name="MetaX"></a>
<div align="center" class="vendor-title"><h3><a href="https://www.metax-tech.com/en/about/about.html">MetaX (沐曦)</a></h3></div>

<p><strong><a href="https://www.caixinglobal.com/2026-03-26/chinese-gpu-maker-metax-doubles-revenue-amid-push-for-domestic-chips-102427800.html">Chinese GPU Maker MetaX Doubles Revenue Amid Push for Domestic Chips</a></strong></p>
<blockquote>
  <p>Shanghai MetaX (STAR: 688802.SH, listed Dec 2025) ships C-series training/inference GPUs (C500 mass production; C600 domestic-process follow-on) with the MXMACA software stack for AI clusters and intelligent-computing centers.</p>
</blockquote>

<a name="Hygon"></a>
<div align="center" class="vendor-title"><h3><a href="https://www.hygon.cn/">Hygon (海光) DCU</a></h3></div>

<p><strong><a href="https://www.trendforce.com/news/2026/04/29/news-huawei-ascend-cambricon-and-hygon-completed-day-0-adaptation-to-deepseek-v4/">Hygon DCU completes Day-0 adaptation for DeepSeek-V4</a></strong></p>
<blockquote>
  <p>Hygon’s Deep Computing Unit (DCU) GPGPU-class accelerators and DTK software stack are widely used in China for large-model training/inference; 2025–2026 coverage highlights same-day DeepSeek model adaptations alongside Ascend and Cambricon.</p>
</blockquote>

<a name="Iluvatar"></a>
<div align="center" class="vendor-title"><h3><a href="https://www.iluvatar.com/">Iluvatar CoreX (天数智芯)</a></h3></div>

<p><strong><a href="https://www.scmp.com/tech/big-tech/article/3341368/iluvatar-corex-targets-nvidias-rubin-gpu-road-map-amid-china-chip-push">Iluvatar CoreX targets Nvidia’s Rubin with GPU road map</a></strong></p>
<blockquote>
  <p>Jan 2026 — Hong Kong-listed Iluvatar CoreX outlined a multi-generation GPU architecture roadmap (Tianshu / Tianxuan / Tianji / Tianquan messaging) aiming to close the gap with Nvidia Hopper→Blackwell→Rubin class platforms, with BI-V150-class products already in AI training/inference deployments.</p>
</blockquote>

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
