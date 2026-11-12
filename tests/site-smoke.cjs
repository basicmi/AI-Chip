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
    summary: { total_records: 4, by_availability: { published: 4 }, inferred_records: 0, power_records: 0, submitters: 1 },
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
        p99_ttft: { value: [1.2, 0.8, 1.0, 1.5][index], unit: "s", label: "P99 TTFT", direction: "lower", family: "latency" },
        p99_tpot: { value: [0.15, 0.16, 0.12, 0.2][index], unit: "s", label: "P99 TPOT", direction: "lower", family: "latency" },
        ...(index === 2 ? {} : {
          p99_itl: { value: 0.18 + index * 0.01, unit: "s", label: "P99 inter-token latency", direction: "lower", family: "latency" }
        })
      },
      metrics: { output_tput_per_gpu: value },
      workload: { precision: "FP8", benchmark_type: "single_turn", isl: index === 3 ? 2048 : 1024, osl: 1024, concurrency: 32, speculative_method: "none", disaggregated: false },
      software: {
        framework: "vLLM 0.11",
        image: "ghcr.io/vllm-project/vllm-openai:v0.11.0",
        recipe_fingerprint: "vllm-0.11-fp8"
      }, configuration: {}, weight_data_types: "FP8"
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
  await page.locator("[data-results-cohort-clear]").click();
  if (!(await page.locator("[data-results-scaling]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide scaling analysis");
  }
  if (!(await page.locator("[data-results-frontier]").isHidden())) {
    throw new Error("Clearing the strict cohort did not hide the Pareto frontier");
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
  await page.locator("[data-comparison-clear]").click();  await page.unroute("**/data/benchmark-results.json.gz");

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
