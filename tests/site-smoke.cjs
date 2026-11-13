const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1365, height: 900 } });
  const base = "http://127.0.0.1:4173/AI-Chip";
  const errors = [];
  const homeDataRequests = [];

  page.on("request", request => {
    if (request.url().includes("/AI-Chip/data/")) homeDataRequests.push(request.url());
  });
  page.on("pageerror", error => errors.push("Page error: " + error.message));
  page.on("response", response => {
    if (response.url().startsWith(base + "/") && response.status() >= 400) {
      errors.push("HTTP " + response.status() + " " + response.url());
    }
  });

  const waitForDataset = async ({ name, loadSelector, statSelector, countSelector }) => {
    await page.waitForFunction((selector) => {
      const state = document.querySelector(selector);
      return state && (state.hidden || state.classList.contains("is-error"));
    }, loadSelector, { timeout: 15000 });

    const state = await page.locator(loadSelector).evaluate(node => ({
      hidden: node.hidden,
      message: node.textContent.trim()
    }));
    if (!state.hidden) {
      throw new Error(name + " dataset failed to load: " + state.message);
    }

    const total = (await page.locator(statSelector).textContent()).trim();
    const visible = (await page.locator(countSelector).textContent()).trim();
    if (!/^\d+$/.test(total) || visible !== total) {
      throw new Error(name + " count mismatch: visible=" + visible + ", dataset total=" + total);
    }
  };

  const routes = ["/", "/directory/", "/products/", "/software-ecosystem/", "/compatibility/", "/workloads/", "/model-support/", "/benchmarks/", "/results/"];
  for (const route of routes) {
    const response = await page.goto(base + route, { waitUntil: "networkidle" });
    if (!response || !response.ok()) throw new Error("Route failed: " + route);
    await page.locator("header.site-header").waitFor();
    await page.locator("main#main-content").waitFor();
  }

  homeDataRequests.length = 0;
  await page.goto(base + "/", { waitUntil: "networkidle" });
  const landscape = page.locator(".hero-visual-frame img");
  await landscape.waitFor();
  await page.waitForFunction(() => {
    const image = document.querySelector(".hero-visual-frame img");
    return image && image.complete && image.naturalWidth > 0 && image.naturalHeight > 0;
  }, { timeout: 10000 });
  const landscapeInfo = await landscape.evaluate(image => ({
    src: image.currentSrc,
    width: image.naturalWidth,
    height: image.naturalHeight
  }));
  if (!landscapeInfo.src.includes("AI_Chip_Landscape_v0p9p1.svg") ||
      landscapeInfo.width < 1800 || landscapeInfo.height < 1200) {
    throw new Error("Landscape image did not load the expected high-resolution v0.9.1 asset: " +
      JSON.stringify(landscapeInfo));
  }

  await page.waitForFunction(() => {
    const stats = document.querySelector("[data-home-stats]");
    return stats && stats.dataset.statsLoaded === "true";
  }, null, { timeout: 15000 });
  const initialHomeDataRequests = homeDataRequests.length;
  const homeStatValues = await page.locator("[data-home-stat]").evaluateAll(nodes =>
    nodes.map(node => node.textContent.trim())
  );
  if (initialHomeDataRequests !== 3 || homeStatValues.length !== 4 ||
      !homeStatValues.every(value => /^\d+$/.test(value))) {
    throw new Error("Homepage coverage metrics did not load all four datasets: " +
      JSON.stringify({ initialHomeDataRequests, homeStatValues }));
  }
  await page.locator("[data-theme-toggle]").click();
  await page.locator("[data-theme-toggle]").click();
  await page.waitForLoadState("networkidle");
  if (homeDataRequests.length !== initialHomeDataRequests) {
    throw new Error("Theme changes unexpectedly reloaded homepage coverage datasets");
  }

  await page.goto(base + "/directory/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => {
    const count = document.querySelector("[data-directory-count]");
    const root = document.querySelector("[data-directory-explorer]");
    return count && count.dataset.ready === "true" &&
      root && root.dataset.profileRegistryLoaded === "true" &&
      root.dataset.profileMatchedCount === "53";
  }, null, { timeout: 10000 });
  const companyCount = Number(await page.locator("[data-directory-count]").getAttribute("data-count"));
  if (companyCount !== 53) throw new Error("Directory company index count changed unexpectedly: " + companyCount);
  const registrySummary = (await page.locator("[data-directory-review-summary]").textContent()).trim();
  if (!registrySummary.includes("53 profiles") ||
      !registrySummary.includes("159 source links") ||
      !registrySummary.includes("58 audited evidence records") ||
      !registrySummary.includes("165 structured claims") ||
      !registrySummary.includes("30 profiles not yet reviewed")) {
    throw new Error("Company profile registry summary is inconsistent: " + registrySummary);
  }
  const profileRegistry = await page.evaluate(async () => {
    const root = document.querySelector("[data-directory-explorer]");
    const response = await fetch(root.dataset.profileSource);
    if (!response.ok) throw new Error("Company profile registry request failed");
    return response.json();
  });
  const productCount = profileRegistry.companies.reduce((sum, company) => sum + company.products.length, 0);
  const claimCount = profileRegistry.companies.reduce((sum, company) => sum + company.claims.length, 0);
  const evidenceCount = profileRegistry.companies.reduce((sum, company) => sum + company.evidence.length, 0);
  const metricContextCount = profileRegistry.companies.reduce((sum, company) =>
    sum + company.claims.filter(claim => claim.metric_context).length, 0);
  const lifecycleProducts = profileRegistry.companies.flatMap(company =>
    company.products.map(product => ({ company, product }))).filter(item =>
      Array.isArray(item.product.availability_history) && item.product.availability_history.length);
  const invalidLifecycleEvents = lifecycleProducts.flatMap(({ company, product }) =>
    product.availability_history.filter((event, index, events) =>
      !company.evidence.some(record => record.id === event.evidence_id) ||
      (index === events.length - 1 && event.status !== product.availability)));
  const tenstorrentProfile = profileRegistry.companies.find(company => company.id === "tenstorrent");
  const corporateProfiles = Object.fromEntries(profileRegistry.companies.filter(company => company.corporate_status).map(company => [company.id, company.corporate_status]));
  const rebellionsProfile = profileRegistry.companies.find(company => company.id === "rebellions");
  const nvidiaProfile = profileRegistry.companies.find(company => company.id === "nvidia");
  const gb200 = nvidiaProfile.products.find(product => product.id === "gb200-nvl72");
  const gb200Bandwidth = nvidiaProfile.claims.find(claim => claim.id === "gb200-hbm-bandwidth");
  const awsProfile = profileRegistry.companies.find(company => company.id === "amazon-aws");
  const trainium2Dense = awsProfile.claims.find(claim => claim.id === "trainium2-fp8-dense");
  const trainium2Sparse = awsProfile.claims.find(claim => claim.id === "trainium2-fp8-sparse");
  if (profileRegistry.schema_version !== "1.3" || profileRegistry.companies.length !== 53 || productCount !== 40 ||
      claimCount !== 165 || evidenceCount !== 58 || metricContextCount < 40 ||
      !profileRegistry.comparison_policy.precision_must_match ||
      !profileRegistry.comparison_policy.sparsity_must_match ||
      !profileRegistry.comparison_policy.measurement_scope_must_match ||
      lifecycleProducts.length < 10 || invalidLifecycleEvents.length ||
      !tenstorrentProfile.products.some(product => product.id === "tenstorrent-blackhole-p150b") ||
      !rebellionsProfile.products.some(product => product.id === "rebellions-rebel-quad") ||
      !profileRegistry.companies.find(company => company.id === "cambricon").products.some(product => product.id === "mlu370-s4-s8") ||
      corporateProfiles.graphcore?.ownership_status !== "wholly_owned_subsidiary" ||
      corporateProfiles.kinara?.parent_company !== "NXP Semiconductors" ||
      corporateProfiles.ampere?.parent_company !== "SoftBank Group" ||
      corporateProfiles["untether-ai"]?.operating_status !== "ceased" ||
      corporateProfiles.groq?.ownership_status !== "independent" ||
      gb200.product_type !== "system" ||
      gb200Bandwidth.metric_context.measurement_scope !== "rack" ||
      trainium2Dense.metric_context.sparsity !== "dense" ||
      trainium2Sparse.metric_context.sparsity !== "structured_sparse") {
    throw new Error("Product registry v1.1 comparison metadata is inconsistent");
  }
  await page.locator("[data-directory-search]").fill("MI355X");
  const mi355Matches = await page.locator(".directory-result-title").allTextContents();
  if (mi355Matches.length !== 1 || !mi355Matches[0].includes("AMD")) {
    throw new Error("Structured company search did not locate AMD MI355X");
  }
  const mi355Product = (await page.locator(".directory-result-products").first().textContent()).trim();
  if (!mi355Product.includes("AMD Instinct MI355X")) {
    throw new Error("Directory result did not display the structured MI355X product: " + mi355Product);
  }
  const mi355Evidence = (await page.locator(".directory-result-evidence").first().textContent()).trim();
  if (!mi355Evidence.includes("Fresh evidence") ||
      !mi355Evidence.includes("4 evidence records") ||
      !mi355Evidence.includes("17 reviewed claims")) {
    throw new Error("AMD MI355X evidence card is inconsistent: " + mi355Evidence);
  }
  await page.locator("[data-directory-search]").fill("Graphcore");
  const graphcoreCard = page.locator(".directory-result-card").first();
  if (!(await graphcoreCard.textContent()).includes("Wholly owned subsidiary") ||
      !(await graphcoreCard.textContent()).includes("SoftBank Group")) {
    throw new Error("Graphcore ownership status missing from directory search");
  }
  await page.locator("[data-directory-search]").fill("Groq");
  const groqCard = page.locator(".directory-result-card").filter({ hasText: "Groq — LPU" });
  if (await groqCard.count() !== 1 || !(await groqCard.textContent()).includes("Independent")) {
    throw new Error("Groq must remain classified as independent after its NVIDIA licensing agreement");
  }
  await page.locator("[data-directory-search]").fill("");
  await page.locator("[data-directory-evidence-filter]").selectOption("fresh");
  if (await page.locator(".directory-result-title").count() !== 23) {
    throw new Error("Freshness filter should return all 23 recently reviewed company profiles");
  }
  await page.locator("[data-directory-search]").fill("Qualcomm");
  await page.locator("[data-directory-evidence-filter]").selectOption("not_reviewed");
  await page.locator("[data-directory-search]").fill("Qualcomm");
  const companyMatches = await page.locator(".directory-result-title").allTextContents();
  if (!companyMatches.some(name => name.includes("Qualcomm"))) {
    throw new Error("Directory search did not find Qualcomm");
  }
  const profileEvidence = (await page.locator(".directory-result-evidence").first().textContent()).trim();
  if (!profileEvidence.includes("Not reviewed") ||
      !profileEvidence.includes("2 source links") ||
      !profileEvidence.includes("0 evidence records") ||
      !profileEvidence.includes("0 reviewed claims")) {
    throw new Error("Company card did not show profile evidence state: " + profileEvidence);
  }
  await page.locator("[data-directory-evidence-filter]").selectOption("not_reviewed");
  if (await page.locator(".directory-result-title").count() !== 1) {
    throw new Error("Not-reviewed evidence filter did not retain the FuriosaAI profile");
  }
  await page.locator("[data-directory-evidence-filter]").selectOption("stale");
  if (!(await page.locator("[data-directory-empty]").isVisible())) {
    throw new Error("Stale evidence filter should not match unreviewed profiles");
  }
  await page.locator("[data-directory-reset]").click();
  await page.locator("[data-directory-group]").selectOption({ label: "China AI Accelerator Vendors" });
  const chinaMatches = await page.locator(".directory-result-title").allTextContents();
  if (!chinaMatches.some(name => name.includes("Huawei Ascend"))) {
    throw new Error("Directory group filter did not include Huawei Ascend");
  }
  await page.locator("[data-directory-reset]").click();

  await page.goto(base + "/products/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => {
    const root = document.querySelector("[data-product-explorer]");
    const products = document.querySelector('[data-product-stat="products"]');
    return root && root.dataset.loaded === "true" && products && products.textContent.trim() === "40";
  }, null, { timeout: 15000 });
  const productStats = await page.locator(".product-stat strong").allTextContents();
  if (productStats.join(",") !== "53,40,165,58,29,28") {
    throw new Error("Product Explorer coverage stats are inconsistent: " + productStats.join(","));
  }
  await page.locator("[data-product-search]").fill("RNGD");
  const rngdCard = page.locator(".product-card").filter({ hasText: "FuriosaAI RNGD Tensor Contraction Processor" }).first();
  if (!(await rngdCard.locator(".product-lifecycle-note").textContent()).includes("2026-01")) {
    throw new Error("Product Explorer did not show source-precision lifecycle status on the RNGD card");
  }
  await rngdCard.locator("details.product-details summary").click();
  const rngdLifecycle = rngdCard.locator(".product-lifecycle-item");
  if (await rngdLifecycle.count() !== 1 ||
      !(await rngdLifecycle.first().textContent()).includes("production") ||
      !(await rngdLifecycle.first().locator("a").getAttribute("href")).includes("furiosa.ai")) {
    throw new Error("Product Explorer did not render the dated, source-linked RNGD lifecycle history");
  }
  await page.locator("[data-product-search]").fill("");
  await page.locator("[data-product-search]").fill("MI355X");
  const mi355Card = page.locator(".product-card").filter({ hasText: "AMD Instinct MI355X" }).first();
  await mi355Card.locator("details.product-details summary").click();
  if (!(await mi355Card.locator(".product-system-details").filter({ hasText: "Product-specific software integrations" }).textContent()).includes("SGLang")) {
    throw new Error("Product Explorer did not link SGLang's exact MI355X support to the product record");
  }
  if ((await mi355Card.locator(".product-system-details").filter({ hasText: "Platform-level software integrations" }).textContent()).includes("SGLang")) {
    throw new Error("Product Explorer incorrectly duplicated an exact product integration as platform-level support");
  }
  await page.locator("[data-product-search]").fill("");
  await page.locator("[data-product-search]").fill("Trainium2");
  if (await page.locator(".product-card-title").count() !== 1 ||
      !(await page.locator(".product-card-title").first().textContent()).includes("Trainium2")) {
    throw new Error("Product Explorer search did not isolate Trainium2");
  }
  const trainiumCardText = (await page.locator(".product-card").first().textContent()).toLowerCase();
  if (!trainiumCardText.includes("torchneuron") ||
      !trainiumCardText.includes("vllm neuron") ||
      !trainiumCardText.includes("llm serving") ||
      !trainiumCardText.includes("llm pretraining") ||
      !trainiumCardText.includes("integration only") ||
      !trainiumCardText.includes("no product-specific benchmark result")) {
    throw new Error("Product Explorer did not show platform software, workload and benchmark evidence boundaries");
  }
  await page.locator('[data-compare-product="trainium2"]').click();
  await page.locator("[data-product-search]").fill("Trainium3");
  if (await page.locator(".product-card-title").count() !== 1) {
    throw new Error("Product Explorer search did not isolate Trainium3");
  }
  await page.locator('[data-compare-product="trainium3"]').click();
  const compareTable = page.locator("[data-product-compare-table]");
  await compareTable.waitFor({ state: "visible" });
  if (await compareTable.locator("thead th").count() !== 3) {
    throw new Error("Product comparison should show a metric column and two selected products");
  }
  const comparisonText = (await compareTable.textContent()).toLowerCase();
  if (!comparisonText.includes("fp8") || !comparisonText.includes("dense") ||
      !comparisonText.includes("structured sparse") ||
      !comparisonText.includes("96 gib hbm") || !comparisonText.includes("144 gib hbm3e")) {
    throw new Error("Product comparison did not preserve dense/sparse precision and memory context");
  }

  await page.locator("[data-product-compare-clear]").click();
  if (await page.locator("[data-product-compare-table]").isVisible()) {
    throw new Error("Product comparison did not clear selected products");
  }
  await page.locator("[data-product-search]").fill("");
  const sixProductIds = ["rubin-gpu", "mi455x", "tpu7x-ironwood", "trainium3", "maia300", "mtia300"];
  for (const id of sixProductIds) {
    await page.locator('[data-compare-product="' + id + '"]').click();
  }
  if ((await page.locator("[data-product-compare-count]").textContent()).trim() !== "6 / 6 selected" ||
      await page.locator("[data-product-compare-table] thead th").count() !== 7) {
    throw new Error("Product comparison should support six products plus the metric column");
  }
  const seventhCompareButton = page.locator('[data-compare-product="intel-gpu-d270"]');
  if (!(await seventhCompareButton.isDisabled())) {
    throw new Error("Product comparison should disable unselected products after six selections");
  }
  if ((await page.locator("[data-product-compare-count]").textContent()).trim() !== "6 / 6 selected") {
    throw new Error("Product comparison should enforce a maximum of six selected products");
  }
  await page.locator("[data-product-compare-clear]").click();

  await page.goto(base + "/compatibility/", { waitUntil: "networkidle" });
  await waitForDataset({
    name: "Compatibility",
    loadSelector: "[data-load-state]",
    statSelector: '[data-stat="integrations"]',
    countSelector: "[data-result-count]"
  });
  const databaseVersion = (await page.locator("[data-database-version]").textContent()).trim();
  const lastReviewed = (await page.locator("[data-last-reviewed]").textContent()).trim();
  if (!databaseVersion || databaseVersion === "Loading…" || !lastReviewed || lastReviewed === "—") {
    throw new Error("Compatibility page metadata did not render");
  }
  await page.locator("[data-filter-search]").fill("vLLM");
  if (Number(await page.locator("[data-result-count]").textContent()) < 1) {
    throw new Error("Compatibility search did not return vLLM records");
  }
  await page.locator("[data-filter-reset]").click();
  await page.locator("[data-filter-search]").fill("SGLang AWS Trainium");
  if (Number(await page.locator("[data-result-count]").textContent()) !== 1 ||
      !(await page.locator("[data-result-cards]").textContent()).toLowerCase().includes("in progress")) {
    throw new Error("Compatibility Explorer did not distinguish SGLang Trainium as an in-progress integration");
  }
  await page.locator("[data-filter-reset]").click();

  await page.locator("[data-theme-toggle]").click();
  if (await page.locator("html").getAttribute("data-theme") !== "dark") {
    throw new Error("Dark theme toggle failed");
  }
  await page.locator("[data-theme-toggle]").click();

  await page.goto(base + "/benchmarks/", { waitUntil: "networkidle" });
  await waitForDataset({
    name: "Benchmark",
    loadSelector: "[data-benchmark-load]",
    statSelector: '[data-benchmark-stat="projects"]',
    countSelector: "[data-benchmark-count]"
  });
  const benchmarkVersion = (await page.locator("[data-benchmark-version]").textContent()).trim();
  const benchmarkReviewed = (await page.locator("[data-benchmark-reviewed]").textContent()).trim();
  if (!benchmarkVersion || benchmarkVersion === "Loading…" ||
      !benchmarkReviewed || benchmarkReviewed === "—") {
    throw new Error("Benchmark page metadata did not render");
  }
  await page.locator("[data-benchmark-search]").fill("InferenceX");
  if (Number(await page.locator("[data-benchmark-count]").textContent()) < 1) {
    throw new Error("Benchmark search did not return InferenceX");
  }
  await page.locator("[data-benchmark-reset]").click();

  await page.goto(base + "/results/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => {
    const root = document.querySelector("[data-benchmark-results]");
    const load = document.querySelector("[data-results-load]");
    return (root && root.dataset.loaded === "true") || (load && load.classList.contains("is-error"));
  }, null, { timeout: 15000 });
  const resultsLoadError = await page.locator("[data-results-load]").textContent();
  if (await page.locator("[data-results-load]").isVisible()) {
    throw new Error("Benchmark Results Explorer failed to initialize: " + resultsLoadError);
  }
  const qualityPanel = page.locator("[data-results-quality]");
  const qualityText = await qualityPanel.locator("[data-results-quality-content]").textContent();
  if (!qualityText.includes("Source attribution") || !qualityText.includes("Hardware identity") ||
      !qualityText.includes("Software stack") || !qualityText.includes("Measurement validation")) {
    throw new Error("Benchmark quality dashboard is missing evidence coverage dimensions or measurement validation");
  }
  if (!(/^\d+%/.test((await qualityPanel.locator(".benchmark-quality-score strong").textContent()).trim()))) {
    throw new Error("Benchmark quality dashboard did not calculate a core provenance coverage percentage");
  }
  const resultTotal = (await page.locator('[data-results-stat="total"]').textContent()).trim();
  const registryTotal = await page.evaluate(async () => {
    const root = document.querySelector("[data-benchmark-results]");
    const response = await fetch(root.dataset.source);
    if (!response.ok) throw new Error("Benchmark registry request failed");
    const bytes = await response.arrayBuffer();
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    const data = await new Response(stream).json();
    return data.records.length;
  });
  if (resultTotal !== String(registryTotal)) {
    throw new Error("Benchmark Results Explorer summary does not match registry length");
  }
  if (Number(await page.locator("[data-results-count]").textContent()) !== registryTotal) {
    throw new Error("Benchmark Results Explorer should initially show all registry rows");
  }
  await page.locator("[data-results-sort]").selectOption("model");
  const sortedModels = await page.locator("[data-results-rows] .benchmark-model").allTextContents();
  const expectedModels = [...sortedModels].sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" })
  );
  if (JSON.stringify(sortedModels) !== JSON.stringify(expectedModels)) {
    throw new Error("Benchmark Results Explorer model sorting is not alphabetical");
  }
  await page.locator("[data-results-sort]").selectOption("vendor");
  const sortedVendors = await page.locator("[data-results-rows] .benchmark-vendor-tag").allTextContents();
  const expectedVendors = [...sortedVendors].sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" })
  );
  if (JSON.stringify(sortedVendors) !== JSON.stringify(expectedVendors)) {
    throw new Error("Benchmark Results Explorer vendor sorting is not alphabetical");
  }
  await page.locator("[data-results-reset]").click();
  if (await page.locator("[data-results-sort]").inputValue() !== "") {
    throw new Error("Benchmark Results Explorer reset did not restore source order");
  }
  if ((await page.locator("[data-results-source-cards]").textContent()).indexOf("InferenceX") < 0) {
    throw new Error("Benchmark Results Explorer did not show the InferenceX source status");
  }
  await page.locator("[data-results-search]").fill("MI355X");
  if (Number(await page.locator("[data-results-count]").textContent()) < 1) {
    throw new Error("Benchmark result search did not locate MI355X submissions");
  }
  await page.locator("[data-results-reset]").click();
  await page.locator("[data-results-vendor]").selectOption("AMD");
  await page.locator("[data-results-model]").selectOption("deepseek-r1");
  await page.locator("[data-results-scenario]").selectOption("Server");
  await page.locator("[data-results-availability]").selectOption("available");
  await page.locator("[data-results-division]").selectOption("closed");
  await page.locator("[data-results-system]").selectOption("datacenter");
  if (Number(await page.locator("[data-results-count]").textContent()) < 1) {
    throw new Error("Like-for-like MLPerf filters did not return AMD DeepSeek R1 Server results");
  }
  await page.locator("[data-results-reset]").click();
  await page.locator("[data-results-inferred]").selectOption("true");
  if (Number(await page.locator("[data-results-count]").textContent()) !== 125) {
    throw new Error("Inferred-submission filter should isolate the 125 source-marked inferred rows");
  }
  await page.locator("[data-results-reset]").click();
  const resultDetails = page.locator("[data-results-rows] .benchmark-result-details").first();
  await resultDetails.locator("summary").click();
  if (!(await resultDetails.locator(".benchmark-result-detail-links a").count())) {
    throw new Error("Benchmark result details did not retain the publisher source link");
  }

  const metricFixture = {
    database_version: "fixture",
    last_imported_at: "2026-11-10",
    summary: { total_records: 4, by_availability: { published: 4 }, inferred_records: 0, power_records: 3, submitters: 1 },
    sources: [{ id: "inferencex", name: "SemiAnalysis InferenceX", version: "Public API v1", publisher: "SemiAnalysis", source_class: "third_party_public_benchmark", record_count: 4, results_url: "https://inferencex.semianalysis.com/" }],
    records: [100, 250, 150, 400].map((value, index) => ({
      id: "fixture-" + index, source_id: "inferencex", source_class: "third_party_public_benchmark",
      submitter: "SemiAnalysis", accelerator_vendor: index === 1 ? "AMD" : "NVIDIA", system_name: index === 1 ? "MI300X" : "H200 SXM",
      system: {
        hardware: index === 1 ? "MI300X" : "H200 SXM",
        is_multinode: false,
        physical_prefill_gpus: index === 2 ? null : 0,
        physical_decode_gpus: index === 2 ? null : (index === 0 ? 8 : index === 1 ? 8 : 16),
        workers: [{ role: "decode", worker_idx: 0, num_gpus: index === 0 ? 8 : index === 1 ? 8 : index === 2 ? 4 : 16 }]
      }, model: "dsr1",
      model_display_name: "DeepSeek-R1-0528", scenario: "single_turn", availability: "published",
      division: "third_party", system_type: "datacenter", benchmark_suite: "SemiAnalysis InferenceX",
      benchmark_version: null, publication_date: "2026-11-10", inferred: false,
      result_value: null, result_unit: "", accuracy_text: "", source_url: "https://inferencex.semianalysis.com/",
      normalized_metrics: {
        output_throughput_per_gpu: { value, unit: "tok/s/GPU", label: "Output throughput", direction: "higher", family: "throughput" },
        median_ttft: { value: 0.8 + index * 0.1, unit: "s", label: "Median TTFT", direction: "lower", family: "latency" },
        ...(index === 1 ? {} : {
          median_tpot: { value: 0.08 + index * 0.01, unit: "s", label: "Median TPOT", direction: "lower", family: "latency" }
        }),
        mean_gpu_utilization: { value: [76, 65, 80, 91][index], unit: "%", label: "Mean GPU utilization", direction: "context", family: "telemetry" },
        ...(index === 2 ? {} : {
          mean_gpu_memory_used: { value: 19000 + index * 3000, unit: "MB", label: "Mean GPU memory used", direction: "context", family: "telemetry" }
        }),
        p99_ttft: { value: [1.2, 0.8, 1.0, 1.5][index], unit: "s", label: "P99 TTFT", direction: "lower", family: "latency" },
        p99_tpot: { value: [0.15, 0.16, 0.12, 0.2][index], unit: "s", label: "P99 TPOT", direction: "lower", family: "latency" },
        ...(index === 2 ? {} : {
          p99_itl: { value: 0.18 + index * 0.01, unit: "s", label: "P99 inter-token latency", direction: "lower", family: "latency" }
        }),
        energy_per_output_token: { value: [0.30, 0.45, 0.18, 0.22][index], unit: "J/output token", label: "Energy per output token", direction: "lower", family: "energy" },
        ...(index === 1 ? {} : {
          energy_per_total_token: { value: [0.12, 0, 0.08, 0.09][index], unit: "J/total token", label: "Energy per total token", direction: "lower", family: "energy" }
        }),
        ...(index === 0 ? {
          energy_per_successful_query: { value: 8.4, unit: "J/query", label: "Energy per successful query", direction: "lower", family: "energy" },
          prefill_energy_per_input_token: { value: 0.04, unit: "J/input token", label: "Prefill energy per input token", direction: "lower", family: "energy" },
          decode_energy_per_output_token: { value: 0.28, unit: "J/output token", label: "Decode energy per output token", direction: "lower", family: "energy" },
          prefill_gpu_power_per_gpu: { value: 280, unit: "W/GPU", label: "Prefill GPU power", direction: "context", family: "power" },
          decode_gpu_power_per_gpu: { value: 245, unit: "W/GPU", label: "Decode GPU power", direction: "context", family: "power" },
          mean_total_cpu_power: { value: 75, unit: "W", label: "Mean total CPU power", direction: "context", family: "cpu_power" }
        } : {}),
        mean_gpu_power_per_gpu: { value: [260, 280, 180, 240][index], unit: "W/GPU", label: "Mean GPU power", direction: "context", family: "power" },
        mean_total_gpu_power: { value: [2080, 2240, 720, 3840][index], unit: "W", label: "Mean total GPU power", direction: "context", family: "power" },
        ...(index === 2 ? {
          prefill_gpu_power_per_gpu: { value: 999, unit: "W/GPU", label: "Prefill GPU power", direction: "context", family: "power" },
          decode_gpu_power_per_gpu: { value: 999, unit: "W/GPU", label: "Decode GPU power", direction: "context", family: "power" }
        } : {})
      },
      power_measurement_valid: index !== 2,
      power_measurement_status: index === 2 ? "failed" : "valid",
      gpu_power_metrics_available: index !== 2,
      cpu_power_measurement_valid: index === 0,
      cpu_power_measurement_status: index === 0 ? "valid" : "not_present",
      cpu_power_metrics_available: index === 0,
      metrics: { output_tput_per_gpu: value },
      workload: { precision: "FP8", benchmark_type: "single_turn", isl: index === 3 ? 2048 : 1024, osl: 1024, concurrency: 32, speculative_method: "none", disaggregated: false },
      software: {
        framework: "vLLM 0.11",
        image: "ghcr.io/vllm-project/vllm-openai:v0.11.0",
        recipe_fingerprint: "vllm-0.11-fp8"
      }, configuration: {},
      ...(index === 0 ? {
        hardware_evidence: {
          schema_version: "1.0",
          collector: { name: "Nsight Compute", version: "2026.3", type: "profiler" },
          system_scope: { scope_type: "per_gpu", device_count: 8, device_model: "H200 SXM", topology: "8-GPU NVLink node" },
          sampling: { started_at: "2026-11-12T10:00:00Z", ended_at: "2026-11-12T10:01:00Z", sample_interval_ms: 1000, sample_count: 60 },
          provenance: { source_type: "profiler_export", source_url: "https://example.com/hardware-evidence/fixture-0", collected_at: "2026-11-12T10:02:00Z" },
          metrics: [
            { metric_id: "sm_throughput_pct", value: 72, unit: "%", measurement_kind: "telemetry", aggregation: "mean", scope: "per_kernel", source_name: "sm__throughput.avg.pct_of_peak_sustained_elapsed", mapping_quality: "direct", mapping_note: "Profiler throughput relative to peak sustained rate over elapsed cycles.", entity_id: "gpu0", sampling_window: { started_at: "2026-11-12T10:00:02Z", ended_at: "2026-11-12T10:00:02.500Z" } },
            { metric_id: "sm_active_pct", value: 72, unit: "%", measurement_kind: "telemetry", aggregation: "mean", scope: "per_gpu", source_name: "DCGM_FI_PROF_SM_UTIL_RATIO", mapping_quality: "direct", mapping_note: "Ratio of cycles with at least one warp assigned to an SM." },
            { metric_id: "theoretical_peak_flops", value: 1.9e15, unit: "FLOP/s", measurement_kind: "telemetry", aggregation: "max", scope: "per_gpu", source_name: "device_fp8_peak_flops", precision: "FP8", sparsity: "dense" },
            { metric_id: "compute_flop_count", value: 7.2e16, unit: "FLOP", measurement_kind: "hardware_counter", aggregation: "sum", scope: "per_gpu", source_name: "flop_count_sp", precision: "FP8", sparsity: "dense" },
            { metric_id: "achieved_flops", value: 1.2e15, unit: "FLOP/s", measurement_kind: "derived", aggregation: "mean", scope: "per_gpu", source_name: "derived_achieved_flops", formula: "compute_flop_count / measured_window_seconds", input_metric_ids: ["compute_flop_count"], precision: "FP8", sparsity: "dense" },
            { metric_id: "dram_read_bytes", value: 2e12, unit: "byte", measurement_kind: "hardware_counter", aggregation: "sum", scope: "per_gpu", source_name: "dram__bytes_read.sum" },
            { metric_id: "nvlink_tx_bytes", value: 8e12, unit: "byte", measurement_kind: "hardware_counter", aggregation: "sum", scope: "per_link", source_name: "nvlink_tx_bytes", link_type: "nvlink" },
            { metric_id: "gpu_power_w", value: 650, unit: "W", measurement_kind: "telemetry", aggregation: "mean", scope: "per_gpu", source_name: "gpu_power_w" }
          ]
        }
      } : {}),
      ...(index === 0 ? {
        runtime_trace: {
          schema_version: "1.0",
          collector: { name: "Serving Runtime Trace", version: "1.0", type: "runtime_trace" },
          clock_domain: "utc_wall_clock",
          sampling: { started_at: "2026-11-12T10:00:00Z", ended_at: "2026-11-12T10:01:00Z" },
          provenance: { source_type: "runtime_trace_export", source_url: "https://example.com/runtime-trace/fixture-0", collected_at: "2026-11-12T10:02:01Z" },
          events: [
            { event_id: "request-root-17", name: "request 17", category: "request", started_at: "2026-11-12T10:00:00Z", ended_at: "2026-11-12T10:00:20Z", correlation_id: "request-17", dependency_graph_complete: true },
            { event_id: "queue-17", name: "queue wait", category: "queue_wait", started_at: "2026-11-12T10:00:00Z", ended_at: "2026-11-12T10:00:01Z", parent_event_id: "request-root-17", depends_on_event_ids: ["request-root-17"] },
            { event_id: "prefill-1", name: "prefill batch 1", category: "prefill", started_at: "2026-11-12T10:00:01Z", ended_at: "2026-11-12T10:00:08Z", entity_id: "gpu0", parent_event_id: "request-root-17", depends_on_event_ids: ["queue-17"] },
            { event_id: "kernel-1", name: "attention kernel", category: "kernel", started_at: "2026-11-12T10:00:02Z", ended_at: "2026-11-12T10:00:04Z", entity_id: "gpu0", parent_event_id: "prefill-1", stream_id: "stream-0" },
            { event_id: "communication-17", name: "collective communication", category: "communication", started_at: "2026-11-12T10:00:03Z", ended_at: "2026-11-12T10:00:05Z", entity_id: "gpu0", parent_event_id: "request-root-17" },
            { event_id: "decode-17", name: "decode phase", category: "decode", started_at: "2026-11-12T10:00:08Z", ended_at: "2026-11-12T10:00:12Z", parent_event_id: "request-root-17" },
            { event_id: "communication-wait-17", name: "communication wait", category: "communication_wait", started_at: "2026-11-12T10:00:10Z", ended_at: "2026-11-12T10:00:11Z", parent_event_id: "decode-17" },
            { event_id: "token-17-1", name: "first token", category: "token_emit", started_at: "2026-11-12T10:00:08Z", ended_at: "2026-11-12T10:00:08Z", token_index: 1, parent_event_id: "request-root-17", depends_on_event_ids: ["prefill-1"] },
            { event_id: "token-17-2", name: "second token", category: "token_emit", started_at: "2026-11-12T10:00:12Z", ended_at: "2026-11-12T10:00:12Z", token_index: 2, parent_event_id: "request-root-17" }
          ]
        }
      } : {}),
      weight_data_types: "FP8"
    }))
  };
  await page.route("**/data/benchmark-results.json.gz", route => route.fulfill({
    status: 200, contentType: "application/json", body: JSON.stringify(metricFixture)
  }));
  await page.goto(base + "/results/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("[data-benchmark-results]")?.dataset.loaded === "true");
  await page.locator(".benchmark-results-advanced summary").click();
  const metricSelect = page.locator("[data-results-metric]");
  if (await metricSelect.locator("option").count() < 3) {
    throw new Error("Metric selector did not load normalized metric definitions");
  }
  const unselectedCohortAction = page.locator('[data-results-rows] tr[data-result-id="fixture-0"] .benchmark-result-details summary');
  await unselectedCohortAction.click();
  if (!(await page.locator('[data-results-rows] tr[data-result-id="fixture-0"] .benchmark-cohort-action').isDisabled())) {
    throw new Error("InferenceX strict cohort action must require an explicit normalized metric");
  }
  await metricSelect.selectOption("output_throughput_per_gpu");
  if (Number(await page.locator("[data-results-count]").textContent()) !== 4) {
    throw new Error("Metric filter should retain all four rows reporting the selected metric");
  }
  await page.locator("[data-results-sort]").selectOption("metric-best");
  const bestFirst = await page.locator("[data-results-rows] .benchmark-result-value").allTextContents();
  if (!bestFirst[0].includes("400") || !bestFirst[1].includes("250") ||
      !bestFirst[2].includes("150") || !bestFirst[3].includes("100")) {
    throw new Error("Higher-is-better metric sorting did not rank the largest throughput first: " + bestFirst.join(", "));
  }
  await page.locator("[data-results-sort]").selectOption("metric-worst");
  const worstFirst = await page.locator("[data-results-rows] .benchmark-result-value").allTextContents();
  if (!worstFirst[0].includes("100") || !worstFirst[3].includes("400")) {
    throw new Error("Metric worst-first sorting did not reverse the throughput order");
  }
  await metricSelect.selectOption("median_ttft");
  await page.locator("[data-results-sort]").selectOption("metric-best");
  const latencyBest = await page.locator("[data-results-rows] .benchmark-result-value").allTextContents();
  if (!latencyBest[0].includes("0.8")) {
    throw new Error("Lower-is-better latency sorting did not put the smallest TTFT first");
  }
  const cohortRow = page.locator('[data-results-rows] tr[data-result-id="fixture-0"]');
  await cohortRow.locator(".benchmark-result-details summary").click();
  await cohortRow.locator(".benchmark-cohort-action").click();
  if (Number(await page.locator("[data-results-count]").textContent()) !== 3) {
    throw new Error("Strict InferenceX cohort should exclude the row with a different ISL");
  }
  const cohortIds = await page.locator("[data-results-rows] tr").evaluateAll(rows => rows.map(row => row.dataset.resultId));
  if (!cohortIds.includes("fixture-1") || !cohortIds.includes("fixture-2") || cohortIds.includes("fixture-3")) {
    throw new Error("Strict InferenceX cohort should retain hardware/software variants but exclude workload mismatches: " + cohortIds.join(", "));
  }
  const cohortText = await page.locator("[data-results-cohort-summary]").textContent();
  if (!cohortText.includes("3 records") || !cohortText.includes("software stack")) {
    throw new Error("Strict InferenceX cohort explanation did not render its count and variable dimensions");
  }
  await page.locator("[data-results-cohort-clear]").click();
  if (Number(await page.locator("[data-results-count]").textContent()) !== 4) {
    throw new Error("Clearing the strict cohort did not restore all four InferenceX records");
  }

  // Build the cohort from a metric published by only two records. The frontier
  // must still consider fixture-2 because it reports the three frontier metrics.
  await metricSelect.selectOption("p99_itl");
  const partialMetricRow = page.locator('[data-results-rows] tr[data-result-id="fixture-0"]');
  await partialMetricRow.locator(".benchmark-result-details summary").click();
  await partialMetricRow.locator(".benchmark-cohort-action").click();
  const partialMetricFrontierIds = await page.locator("[data-results-frontier-content] tbody tr")
    .evaluateAll(rows => rows.map(row => row.dataset.recordId));
  if (!partialMetricFrontierIds.includes("fixture-2")) {
    throw new Error("Pareto frontier incorrectly required the selected display metric on every cohort record");
  }
  await page.locator("[data-results-cohort-clear]").click();

  await metricSelect.selectOption("output_throughput_per_gpu");
  if (!(await page.locator("[data-results-scaling]").isHidden())) {
    throw new Error("Scaling analysis must remain hidden until a strict workload cohort is selected");
  }
  if (!(await page.locator("[data-results-energy]").isHidden())) {
    throw new Error("Energy analysis must remain hidden until a strict workload cohort is selected");
  }
  if (!(await page.locator("[data-results-decomposition]").isHidden())) {
    throw new Error("Performance decomposition must remain hidden before a strict workload cohort");
  }
  if (!(await page.locator("[data-results-hardware-evidence]").isHidden())) {
    throw new Error("Hardware evidence coverage must remain hidden before a strict workload cohort");
  }
  const scalingRow = page.locator('[data-results-rows] tr[data-result-id="fixture-0"]');
  await scalingRow.locator(".benchmark-result-details summary").click();
  await scalingRow.locator(".benchmark-cohort-action").click();
  if (await page.locator("[data-results-scaling]").isHidden()) {
    throw new Error("Selecting an InferenceX output-throughput cohort did not reveal scaling analysis");
  }
  const scalingText = await page.locator("[data-results-scaling-content]").textContent();
  if (!scalingText.includes("H200 SXM") || !scalingText.includes("66.7%") ||
      !scalingText.includes("4 GPUs") || !scalingText.includes("8 GPUs") ||
      !scalingText.includes("worker-pool counts") || !scalingText.includes("derived estimates")) {
    throw new Error("Scaling analysis did not derive a provenance-aware 4-to-8 GPU efficiency curve: " + scalingText);
  }
  if (await page.locator("[data-results-frontier]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal the latency-throughput frontier");
  }
  if (await page.locator("[data-results-energy]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal GPU energy analysis");
  }
  if (await page.locator("[data-results-decomposition]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal performance decomposition");
  }
  if (await page.locator("[data-results-hardware-evidence]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal hardware evidence coverage");
  }
  const hardwareEvidenceText = await page.locator("[data-results-hardware-evidence-content]").textContent();
  if (!hardwareEvidenceText.includes("1/3 records include a provenance-backed hardware evidence bundle") ||
      !hardwareEvidenceText.includes("Compute") || !hardwareEvidenceText.includes("HBM bandwidth") ||
      !hardwareEvidenceText.includes("KV cache") || !hardwareEvidenceText.includes("Communication") ||
      !hardwareEvidenceText.includes("Power / thermal") || !hardwareEvidenceText.includes("not a bottleneck verdict")) {
    throw new Error("Hardware evidence coverage did not report the five evidence domains and limitations: " + hardwareEvidenceText);
  }
  const evidenceDomains = page.locator("[data-hardware-evidence-domain]");
  if (await evidenceDomains.count() !== 5) {
    throw new Error("Hardware evidence coverage should expose exactly five domains");
  }
  const computeEvidence = await page.locator('[data-hardware-evidence-domain="compute"]').textContent();
  const hbmEvidence = await page.locator('[data-hardware-evidence-domain="hbm"]').textContent();
  const communicationEvidence = await page.locator('[data-hardware-evidence-domain="communication"]').textContent();
  if (!computeEvidence.includes("1 core · 0 partial · 2 missing") ||
      !hbmEvidence.includes("0 core · 1 partial · 2 missing") ||
      !communicationEvidence.includes("0 core · 1 partial · 2 missing")) {
    throw new Error("Hardware evidence readiness incorrectly classified complete/partial/missing signals: " +
      JSON.stringify({computeEvidence, hbmEvidence, communicationEvidence}));
  }
  const evidenceRows = page.locator("[data-hardware-evidence-record-id]");
  if (await evidenceRows.count() !== 3) {
    throw new Error("Hardware evidence table did not retain the selected strict cohort");
  }
  if (await page.locator("[data-results-gpu-execution]").isHidden()) {
    throw new Error("Selecting a strict workload cohort did not reveal GPU execution efficiency analysis");
  }
  const gpuExecutionText = await page.locator("[data-results-gpu-execution-content]").textContent();
  if (!gpuExecutionText.includes("scope/entity/window-matched hardware activity groups") ||
      !gpuExecutionText.includes("SM inactive-cycle complement") ||
      !gpuExecutionText.includes("SM throughput") ||
      !gpuExecutionText.includes("50% (n=1)") ||
      !gpuExecutionText.includes("25% (n=1)")) {
    throw new Error("GPU execution analysis did not preserve counter semantics and request-level compute/communication overlap: " + gpuExecutionText);
  }
  if (await page.locator("[data-gpu-execution-activity] tbody tr").count() !== 2 ||
      await page.locator("[data-gpu-execution-overlap] tbody tr").count() !== 1) {
    throw new Error("GPU activity and request-overlap tables did not render the expected fixture rows");
  }
  const crossLayerText = await page.locator("[data-results-cross-layer-content]").textContent();
  if (!crossLayerText.includes("3 strict-cohort records") ||
      !crossLayerText.includes("3 execution identities") ||
      !crossLayerText.includes("3 descriptive contrasts") ||
      !crossLayerText.includes("P99 TTFT") ||
      !crossLayerText.includes("Not established")) {
    throw new Error("Cross-layer matrix did not compare the strict cohort with runtime and evidence limits: " + crossLayerText);
  }
  if (await page.locator("[data-cross-layer-comparison]").count() !== 3) {
    throw new Error("Cross-layer matrix should render the three unique execution contrasts");
  }
  const runtimeAlignmentText = await page.locator("[data-results-runtime-alignment-content]").textContent();
  if (!runtimeAlignmentText.includes("3 strict-cohort records") ||
      !runtimeAlignmentText.includes("1 runtime traces") ||
      !runtimeAlignmentText.includes("1 hardware/trace pairs") ||
      !runtimeAlignmentText.includes("1 metric-specific windows") ||
      !runtimeAlignmentText.includes("1 eligible phase joins")) {
    throw new Error("Runtime trace alignment panel did not report exact evidence coverage: " + runtimeAlignmentText);
  }
  if (await page.locator("[data-runtime-trace-record-id]").count() !== 1 ||
      await page.locator("[data-runtime-phase-join]").count() !== 1 ||
      !(await page.locator("[data-runtime-phase-join]").textContent()).includes("kernel")) {
    throw new Error("Runtime phase alignment did not join the metric window to the exact nested kernel event");
  }
  const phaseDecompositionText = await page.locator("[data-results-phase-decomposition-content]").textContent();
  if (!phaseDecompositionText.includes("1 request roots") ||
      !phaseDecompositionText.includes("1 trace-derived TTFT samples") ||
      !phaseDecompositionText.includes("1 trace-derived TPOT samples")) {
    throw new Error("Request-level TTFT/TPOT decomposition did not report the explicit token-marker sample");
  }
  const phaseRow = page.locator("[data-runtime-phase-decomposition] tbody tr");
  if (await phaseRow.count() !== 1 ||
      !(await phaseRow.textContent()).includes("8,000 / 8,000 ms") ||
      !(await phaseRow.textContent()).includes("4,000 / 4,000 ms")) {
    throw new Error("Trace-derived TTFT/TPOT values do not match the request and token marker timestamps: " + await phaseRow.textContent());
  }
  const criticalPathRow = page.locator("[data-runtime-critical-path] tbody tr").first();
  if (await page.locator("[data-runtime-critical-path] tbody tr").count() !== 1 ||
      !(await criticalPathRow.textContent()).includes("queue wait") ||
      !(await criticalPathRow.textContent()).includes("prefill batch 1") ||
      !(await criticalPathRow.textContent()).includes("8,000 ms") ||
      !(await criticalPathRow.textContent()).includes("0 ms") ||
      !(await criticalPathRow.textContent()).includes("Available")) {
    throw new Error("Explicit TTFT dependency path did not reconcile event time and unclassified gaps: " +
      await criticalPathRow.textContent());
  }
  const evidenceRecord = page.locator('[data-hardware-evidence-record-id="fixture-0"]');
  await page.locator(".benchmark-hardware-evidence-details summary").click();
  const evidenceDetails = await page.locator(".benchmark-hardware-evidence-details").textContent();
  if (!evidenceDetails.includes("sm_throughput_pct") ||
      !evidenceDetails.includes("dram_read_bytes") ||
      !evidenceDetails.includes("sm__throughput.avg.pct_of_peak_sustained_elapsed") ||
      !evidenceDetails.includes("mapping: direct")) {
    throw new Error("Hardware evidence details did not preserve canonical and raw counter names: " + evidenceDetails);
  }
  if (!evidenceDetails.includes("Roofline: insufficient evidence") ||
      !evidenceDetails.includes("Communication: no comparable per-link utilization") ||
      !evidenceDetails.includes("P99 TTFT") ||
      !evidenceDetails.includes("no automatic bottleneck verdict") ||
      !evidenceDetails.includes("kernel-gap traces")) {
    throw new Error("Hardware diagnostics inferred a bottleneck or omitted runtime/evidence limitations: " + evidenceDetails);
  }
  const noEvidenceRecord = await page.locator('[data-hardware-evidence-record-id="fixture-1"]').textContent();
  if (!noEvidenceRecord.includes("Not reported")) {
    throw new Error("Aggregate GPU metrics were incorrectly promoted to low-level hardware evidence");
  }
  const frontierText = await page.locator("[data-results-frontier-content]").textContent();
  if (!frontierText.includes("3 report all three required metrics") ||
      !frontierText.includes("2 Pareto-optimal configurations") ||
      !frontierText.includes("P99 TTFT") || !frontierText.includes("P99 TPOT")) {
    throw new Error("Pareto frontier did not summarize the three-metric cohort correctly: " + frontierText);
  }
  const frontierIds = await page.locator("[data-results-frontier-content] tbody tr")
    .evaluateAll(rows => rows.map(row => row.dataset.recordId));
  if (frontierIds.length !== 2 || !frontierIds.includes("fixture-1") ||
      !frontierIds.includes("fixture-2") || frontierIds.includes("fixture-0")) {
    throw new Error("Pareto frontier should retain the two non-dominated configurations and exclude fixture-0: " + frontierIds.join(", "));
  }
  const paretoPlot = page.locator("[data-pareto-plot]");
  if (await paretoPlot.locator(".benchmark-frontier-point").count() !== 3 ||
      await paretoPlot.locator(".benchmark-frontier-point.is-pareto").count() !== 2) {
    throw new Error("Pareto scatter plot did not distinguish all candidates from non-dominated points");
  }
  const energyText = await page.locator("[data-results-energy-content]").textContent();
  if (!energyText.includes("3 records in the selected strict workload cohort") ||
      !energyText.includes("2 have validated GPU energy per output token") ||
      !energyText.includes("2 Pareto-optimal energy/throughput configurations") ||
      !energyText.includes("75 W") || !energyText.includes("0.04 J/input token") ||
      !energyText.includes("0.28 J/output token") || !energyText.includes("CPU/socket/module telemetry")) {
    throw new Error("Energy analysis did not summarize validated GPU energy and separate CPU telemetry: " + energyText);
  }
  const energyIds = await page.locator("[data-results-energy-content] tbody tr")
    .evaluateAll(rows => rows.map(row => row.dataset.recordId));
  if (energyIds.length !== 2 || !energyIds.includes("fixture-0") ||
      !energyIds.includes("fixture-1") || energyIds.includes("fixture-2")) {
    throw new Error("Energy analysis included an unvalidated power record or omitted a valid record: " + energyIds.join(", "));
  }
  const energyPlot = page.locator("[data-energy-plot]");
  if (await energyPlot.locator(".benchmark-energy-point").count() !== 2 ||
      await energyPlot.locator(".benchmark-energy-point.is-pareto").count() !== 2) {
    throw new Error("Energy Pareto plot did not distinguish the two non-dominated energy/throughput configurations");
  }
  const decompositionText = await page.locator("[data-results-decomposition-content]").textContent();
  if (!decompositionText.includes("3 records in selected strict workload cohort") ||
      !decompositionText.includes("Median TTFT") ||
      !decompositionText.includes("Median TPOT") ||
      !decompositionText.includes("P99 ITL") ||
      !decompositionText.includes("Prefill GPU energy") ||
      !decompositionText.includes("not a measured decode-kernel breakdown") ||
      !decompositionText.includes("classifications remain undetermined")) {
    throw new Error("Performance decomposition did not explain phase signals and diagnostic boundaries: " + decompositionText);
  }
  const decompositionRows = page.locator("[data-results-decomposition-content] [data-decomposition-record-id]");
  if (await decompositionRows.count() !== 3) {
    throw new Error("Performance decomposition did not respect the strict workload cohort");
  }
  const validPhase = await page.locator('[data-decomposition-record-id="fixture-0"]').textContent();
  const invalidPhase = await page.locator('[data-decomposition-record-id="fixture-2"]').textContent();
  if (!validPhase.includes("280 W/GPU") || !validPhase.includes("245 W/GPU") ||
      !validPhase.includes("0.04 J/input token") || !validPhase.includes("19,000 MB") ||
      !invalidPhase.includes("Validated phase-energy telemetry unavailable") ||
      invalidPhase.includes("999 W/GPU")) {
    throw new Error("Performance decomposition failed to gate phase power and preserve publisher telemetry: " +
      JSON.stringify({validPhase, invalidPhase}));
  }
  const decompositionCoverage = await page.locator("[data-decomposition-signal]").count();
  if (decompositionCoverage !== 12) {
    throw new Error("Performance decomposition must report all twelve signal coverage dimensions");
  }
  await page.locator("[data-results-cohort-clear]").click();
  if (!(await page.locator("[data-results-scaling]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide scaling analysis");
  }
  if (!(await page.locator("[data-results-frontier]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide the Pareto frontier");
  }
  if (!(await page.locator("[data-results-energy]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide energy analysis");
  }
  if (!(await page.locator("[data-results-decomposition]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide performance decomposition");
  }
  if (!(await page.locator("[data-results-hardware-evidence]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide hardware evidence coverage");
  }

  const compareRow = id => page.locator('[data-results-rows] tr[data-result-id="' + id + '"]');
  await metricSelect.selectOption("output_throughput_per_gpu");
  await compareRow("fixture-0").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-0").locator(".benchmark-compare-action").click();
  if (!(await page.locator("[data-comparison-count]").textContent()).includes("1 / 4") ||
      !(await page.locator("[data-comparison-content]").textContent()).includes("Add one more record")) {
    throw new Error("Comparison workspace did not retain the first selected InferenceX record");
  }
  await compareRow("fixture-1").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-1").locator(".benchmark-compare-action").click();
  let comparisonWorkspaceText = await page.locator("[data-comparison-content]").textContent();
  if (!comparisonWorkspaceText.includes("Like-for-like cohort") || !comparisonWorkspaceText.includes("+150.0%") ||
      !comparisonWorkspaceText.includes("better (higher is better)")) {
    throw new Error("Higher-is-better InferenceX comparison did not calculate the source-directed delta: " + comparisonWorkspaceText);
  }
  await compareRow("fixture-3").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-3").locator(".benchmark-compare-action").click();
  comparisonWorkspaceText = await page.locator("[data-comparison-content]").textContent();
  if (!comparisonWorkspaceText.includes("Not directly comparable") ||
      await page.locator(".benchmark-comparison-table").count() !== 0) {
    throw new Error("Comparison workspace must block metric comparison across different workload shapes");
  }
  await page.locator('.benchmark-comparison-remove[data-record-id="fixture-3"]').click();
  if (!(await page.locator("[data-comparison-content]").textContent()).includes("Like-for-like cohort")) {
    throw new Error("Removing a mismatched workload did not restore the valid comparison");
  }
  await page.locator("[data-comparison-clear]").click();
  if (!(await page.locator("[data-comparison-count]").textContent()).includes("0 / 4") ||
      await page.locator(".benchmark-comparison-table").count() !== 0) {
    throw new Error("Clear comparison did not reset the workspace");
  }

  await metricSelect.selectOption("median_ttft");
  await compareRow("fixture-0").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-0").locator(".benchmark-compare-action").click();
  await compareRow("fixture-1").locator(".benchmark-result-details summary").click();
  await compareRow("fixture-1").locator(".benchmark-compare-action").click();
  const latencyComparisonText = await page.locator("[data-comparison-content]").textContent();
  if (!latencyComparisonText.includes("+12.5%") ||
      !latencyComparisonText.includes("worse (lower is better)")) {
    throw new Error("Lower-is-better latency comparison incorrectly interpreted a positive delta: " + latencyComparisonText);
  }
  await page.locator("[data-comparison-clear]").click();
  await page.unroute("**/data/benchmark-results.json.gz");

  const attributionRows = [
    { id: "attr-base-a", hardware: "H200 SXM", gpuCount: 8, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 1, value: 100 },
    { id: "attr-base-b", hardware: "H200 SXM", gpuCount: 8, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 1, value: 102 },
    { id: "attr-software", hardware: "H200 SXM", gpuCount: 8, framework: "SGLang 0.5", image: "lmsysorg/sglang:v0.5.0", recipe: "sglang-0.5-fp8", prefillTp: 1, value: 120 },
    { id: "attr-parallelism", hardware: "H200 SXM", gpuCount: 8, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 2, value: 90 },
    { id: "attr-gpu-count", hardware: "H200 SXM", gpuCount: 4, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 1, value: 130 },
    { id: "attr-hardware", hardware: "MI300X", gpuCount: 8, framework: "vLLM 0.11", image: "ghcr.io/vllm-project/vllm-openai:v0.11.0", recipe: "vllm-0.11-fp8", prefillTp: 1, value: 110 }
  ];
  const attributionFixture = {
    database_version: "attribution-fixture",
    last_imported_at: "2026-11-12",
    summary: { total_records: attributionRows.length, by_availability: { published: attributionRows.length }, inferred_records: 0, power_records: 0, submitters: 1 },
    sources: [{ id: "inferencex", name: "SemiAnalysis InferenceX", version: "Public API v1", publisher: "SemiAnalysis", source_class: "third_party_public_benchmark", record_count: attributionRows.length, results_url: "https://inferencex.semianalysis.com/" }],
    records: attributionRows.map(row => ({
      id: row.id, source_id: "inferencex", source_class: "third_party_public_benchmark",
      submitter: "SemiAnalysis", accelerator_vendor: row.hardware === "MI300X" ? "AMD" : "NVIDIA",
      system_name: row.gpuCount + "x" + row.hardware,
      system: {
        hardware: row.hardware, accelerator_model: row.hardware,
        total_accelerators: row.gpuCount, physical_prefill_gpus: 0,
        physical_decode_gpus: row.gpuCount, is_multinode: false,
        workers: [{ role: "decode", worker_idx: 0, num_gpus: row.gpuCount }]
      },
      model: "dsr1", model_display_name: "DeepSeek-R1-0528",
      scenario: "single_turn", availability: "published", division: "third_party",
      system_type: "datacenter", benchmark_suite: "SemiAnalysis InferenceX",
      benchmark_version: null, publication_date: "2026-11-12", inferred: false,
      result_value: null, result_unit: "", accuracy_text: "",
      source_url: "https://inferencex.semianalysis.com/",
      detail_url: "https://inferencex.semianalysis.com/",
      normalized_metrics: {
        output_throughput_per_gpu: {
          value: row.value, unit: "tok/s/GPU", label: "Output throughput",
          direction: "higher", family: "throughput"
        }
      },
      workload: {
        precision: "FP8", benchmark_type: "single_turn", isl: 1024, osl: 1024,
        concurrency: 32, speculative_method: "none", disaggregated: false
      },
      software: { framework: row.framework, image: row.image, recipe_fingerprint: row.recipe },
      configuration: {
        prefill_tp: row.prefillTp, prefill_ep: 1, prefill_dp_attention: 1,
        prefill_num_workers: 1, decode_tp: 1, decode_ep: 1,
        decode_dp_attention: 1, decode_num_workers: 1, offload_mode: "none"
      },
      weight_data_types: "FP8"
    }))
  };
  await page.route("**/data/benchmark-results.json.gz", route => route.fulfill({
    status: 200, contentType: "application/json", body: JSON.stringify(attributionFixture)
  }));
  await page.goto(base + "/results/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("[data-benchmark-results]")?.dataset.loaded === "true");
  if (!(await page.locator("[data-results-attribution]").isHidden())) {
    throw new Error("Configuration attribution must remain hidden until a strict InferenceX cohort is selected");
  }
  await page.locator(".benchmark-results-advanced summary").click();
  await page.locator("[data-results-metric]").selectOption("output_throughput_per_gpu");
  const attributionBaseRow = page.locator('[data-results-rows] tr[data-result-id="attr-base-a"]');
  await attributionBaseRow.locator(".benchmark-result-details summary").click();
  await attributionBaseRow.locator(".benchmark-cohort-action").click();
  if (await page.locator("[data-results-attribution]").isHidden()) {
    throw new Error("Selecting a strict InferenceX cohort did not reveal configuration attribution");
  }
  const attributionSummary = await page.locator("[data-results-attribution-content]").textContent();
  if (!attributionSummary.includes("6 records in the selected strict workload cohort") ||
      !attributionSummary.includes("6 report the selected metric") ||
      !attributionSummary.includes("5 distinct reported configuration signatures") ||
      !attributionSummary.includes("4 matched one-dimension contrast groups")) {
    throw new Error("Configuration attribution did not summarize the strict cohort and matched contrasts: " + attributionSummary);
  }
  const attributionContrasts = page.locator("[data-results-attribution-content] [data-attribution-contrast]");
  if (await attributionContrasts.count() !== 4) {
    throw new Error("Configuration attribution should produce exactly four isolated hardware/software/parallelism/GPU-count contrasts");
  }
  const contrastDimensions = await attributionContrasts.evaluateAll(rows => rows.map(row => row.dataset.attributionContrast).sort());
  if (JSON.stringify(contrastDimensions) !== JSON.stringify(["gpuCount", "hardware", "parallelism", "software"])) {
    throw new Error("Configuration attribution did not isolate the four expected dimensions: " + contrastDimensions.join(", "));
  }
  const contrastRows = await attributionContrasts.evaluateAll(rows =>
    rows.map(row => ({ dimension: row.dataset.attributionContrast, text: row.textContent, ids: row.dataset.attributionRecords }))
  );
  const hardwareContrast = contrastRows.find(row => row.dimension === "hardware");
  const gpuContrast = contrastRows.find(row => row.dimension === "gpuCount");
  const softwareContrast = contrastRows.find(row => row.dimension === "software");
  const parallelismContrast = contrastRows.find(row => row.dimension === "parallelism");
  if (!hardwareContrast.text.includes("H200 SXM → MI300X") ||
      !hardwareContrast.ids.includes("attr-hardware") ||
      !hardwareContrast.text.includes("+9 tok/s/GPU")) {
    throw new Error("Hardware contrast failed to aggregate duplicate baseline runs or calculate the median delta: " + JSON.stringify(hardwareContrast));
  }
  if (!gpuContrast.text.includes("4 GPUs → 8 GPUs") ||
      !gpuContrast.ids.includes("attr-gpu-count") ||
      !gpuContrast.text.includes("-29 tok/s/GPU")) {
    throw new Error("GPU-count contrast did not hold hardware/software/parallelism constant: " + JSON.stringify(gpuContrast));
  }
  if (!softwareContrast.text.includes("SGLang 0.5") ||
      !softwareContrast.text.includes("vLLM 0.11") ||
      !softwareContrast.ids.includes("attr-software")) {
    throw new Error("Software-stack contrast did not isolate the framework/image/recipe change: " + JSON.stringify(softwareContrast));
  }
  if (!parallelismContrast.text.includes("prefill_tp=1") ||
      !parallelismContrast.text.includes("prefill_tp=2") ||
      !parallelismContrast.ids.includes("attr-parallelism")) {
    throw new Error("Parallelism contrast did not isolate the prefill TP change: " + JSON.stringify(parallelismContrast));
  }
  const attributionCoverage = await page.locator("[data-attribution-coverage-dimension]")
    .evaluateAll(rows => rows.map(row => row.dataset.attributionCoverageDimension));
  if (attributionCoverage.length !== 5) {
    throw new Error("Configuration attribution coverage table is missing one or more dimensions");
  }
  await page.locator("[data-results-cohort-clear]").click();
  if (!(await page.locator("[data-results-attribution]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide configuration attribution");
  }
  await page.unroute("**/data/benchmark-results.json.gz");

  const mlperfFixture = {
    database_version: "fixture",
    last_imported_at: "2026-11-10",
    summary: { total_records: 3, by_availability: { available: 3 }, inferred_records: 0, power_records: 0, submitters: 3 },
    sources: [{ id: "mlperf-inference-v6.1", name: "MLPerf Inference v6.1", version: "v6.1", publisher: "MLCommons", source_class: "standardized_public_submission", record_count: 3, results_url: "https://mlcommons.org/benchmarks/inference-datacenter/" }],
    records: [
      { id: "mlperf-0", source_id: "mlperf-inference-v6.1", source_class: "standardized_public_submission", submitter: "Vendor A", accelerator_vendor: "NVIDIA", system_name: "8xH100", system: { accelerator_model: "H100", total_accelerators: 8 }, software: { framework: "TensorRT" }, model: "deepseek-r1", scenario: "Server", availability: "available", division: "closed", system_type: "datacenter", benchmark_suite: "MLPerf Inference", benchmark_version: "v6.1", accuracy_text: "99% of reference", weight_data_types: "FP8", inferred: false, result_value: 1000, result_unit: "tokens/s", power_metrics_available: false },
      { id: "mlperf-1", source_id: "mlperf-inference-v6.1", source_class: "standardized_public_submission", submitter: "Vendor B", accelerator_vendor: "AMD", system_name: "8xMI355X", system: { accelerator_model: "MI355X", total_accelerators: 8 }, software: { framework: "ROCm" }, model: "deepseek-r1", scenario: "Server", availability: "available", division: "closed", system_type: "datacenter", benchmark_suite: "MLPerf Inference", benchmark_version: "v6.1", accuracy_text: "99% of reference", weight_data_types: "FP8", inferred: false, result_value: 1500, result_unit: "tokens/s", power_metrics_available: false },
      { id: "mlperf-2", source_id: "mlperf-inference-v6.1", source_class: "standardized_public_submission", submitter: "Vendor C", accelerator_vendor: "NVIDIA", system_name: "8xB200", system: { accelerator_model: "B200", total_accelerators: 8 }, software: { framework: "TensorRT" }, model: "deepseek-r1", scenario: "Server", availability: "available", division: "closed", system_type: "datacenter", benchmark_suite: "MLPerf Inference", benchmark_version: "v6.1", accuracy_text: "99.9% of reference", weight_data_types: "FP8", inferred: false, result_value: 1700, result_unit: "tokens/s", power_metrics_available: false }
    ]
  };
  await page.route("**/data/benchmark-results.json.gz", route => route.fulfill({
    status: 200, contentType: "application/json", body: JSON.stringify(mlperfFixture)
  }));
  await page.goto(base + "/results/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("[data-benchmark-results]")?.dataset.loaded === "true");
  const mlperfRow = page.locator('[data-results-rows] tr[data-result-id="mlperf-0"]');
  await mlperfRow.locator(".benchmark-result-details summary").click();
  await mlperfRow.locator(".benchmark-cohort-action").click();
  if (Number(await page.locator("[data-results-count]").textContent()) !== 2) {
    throw new Error("Strict MLPerf cohort should match accuracy target and exclude a different accuracy row");
  }
  const mlperfCohortIds = await page.locator("[data-results-rows] tr").evaluateAll(rows => rows.map(row => row.dataset.resultId));
  if (!mlperfCohortIds.includes("mlperf-1") || mlperfCohortIds.includes("mlperf-2")) {
    throw new Error("Strict MLPerf cohort should retain other systems with the same benchmark conditions");
  }
  await page.locator("[data-results-cohort-clear]").click();
  if (Number(await page.locator("[data-results-count]").textContent()) !== 3) {
    throw new Error("Clearing the strict MLPerf cohort did not restore all fixture rows");
  }
  await page.locator('[data-results-rows] tr[data-result-id="mlperf-0"] .benchmark-result-details summary').click();
  await page.locator('[data-results-rows] tr[data-result-id="mlperf-0"] .benchmark-compare-action').click();
  await page.locator('[data-results-rows] tr[data-result-id="mlperf-1"] .benchmark-result-details summary').click();
  await page.locator('[data-results-rows] tr[data-result-id="mlperf-1"] .benchmark-compare-action').click();
  const mlperfComparison = await page.locator("[data-comparison-content]").textContent();
  if (!mlperfComparison.includes("Like-for-like cohort") ||
      !mlperfComparison.includes("direction not ranked") ||
      !mlperfComparison.includes("no winner is declared")) {
    throw new Error("MLPerf comparison must show deltas without inventing an optimization direction");
  }
  await page.locator("[data-comparison-clear]").click();
  await page.unroute("**/data/benchmark-results.json.gz");

  await page.goto(base + "/workloads/", { waitUntil: "networkidle" });
  await waitForDataset({
    name: "Workload",
    loadSelector: "[data-workload-load]",
    statSelector: '[data-workload-stat="paths"]',
    countSelector: "[data-workload-result-count]"
  });
  await page.locator("[data-workload-search]").fill("Biren");
  if (Number(await page.locator("[data-workload-result-count]").textContent()) !== 1) {
    throw new Error("Workload search did not isolate the Biren path");
  }

  await page.goto(base + "/model-support/", { waitUntil: "networkidle" });
  await waitForDataset({
    name: "Model support",
    loadSelector: "[data-model-load]",
    statSelector: '[data-model-stat="paths"]',
    countSelector: "[data-model-result-count]"
  });
  if (await page.locator("[data-model-support-version]").textContent() === "Loading…" ||
      !(await page.locator("[data-model-support-reviewed]").textContent()).trim()) {
    throw new Error("Model Support page-level registry metadata did not initialize");
  }
  await page.locator("[data-model-search]").fill("Llama 3.3 70B");
  if (Number(await page.locator("[data-model-result-count]").textContent()) !== 1) {
    throw new Error("Model support search did not isolate Llama 3.3 70B");
  }
  const llamaPath = await page.locator(".model-support-card").first().textContent();
  if (!llamaPath.includes("Trainium2") || !llamaPath.includes("Trainium3") ||
      !llamaPath.includes("BF16") || !llamaPath.includes("FP8 static")) {
    throw new Error("Llama 3.3 70B model support path is missing hardware or precision details");
  }
  await page.locator("[data-model-reset]").click();
  await page.locator("[data-model-platform]").selectOption("aws-trainium");
  if (Number(await page.locator("[data-model-result-count]").textContent()) !== 2) {
    throw new Error("Model support platform filter did not return both AWS Trainium paths");
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("[data-nav-toggle]").click();
  if (await page.locator("[data-nav-toggle]").getAttribute("aria-expanded") !== "true") {
    throw new Error("Mobile nav did not open");
  }
  await page.locator("[data-site-nav] a[href*='workloads']").click();
  if (await page.locator("[data-nav-toggle]").getAttribute("aria-expanded") !== "false") {
    throw new Error("Mobile nav did not close after navigation");
  }

  if (errors.length) throw new Error("Browser errors:\n" + errors.join("\n"));
  console.log("PASS: nine routes, Model Support Explorer, Benchmark Results Explorer, Product Explorer, landscape asset, homepage coverage stats, directory search/group/evidence filters, company profile registry, compatibility/workload/benchmark search, theme toggle and mobile navigation.");
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});
