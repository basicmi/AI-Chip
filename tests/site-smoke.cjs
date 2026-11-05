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

  const routes = ["/", "/directory/", "/software-ecosystem/", "/compatibility/", "/workloads/", "/benchmarks/"];
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
      root.dataset.profileMatchedCount === "50";
  }, null, { timeout: 10000 });
  const companyCount = Number(await page.locator("[data-directory-count]").getAttribute("data-count"));
  if (companyCount !== 50) throw new Error("Directory company index count changed unexpectedly: " + companyCount);
  const registrySummary = (await page.locator("[data-directory-review-summary]").textContent()).trim();
  if (!registrySummary.includes("50 profiles") ||
      !registrySummary.includes("126 source links") ||
      !registrySummary.includes("17 audited evidence records") ||
      !registrySummary.includes("70 structured claims") ||
      !registrySummary.includes("42 profiles not yet reviewed")) {
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
  const nvidiaProfile = profileRegistry.companies.find(company => company.id === "nvidia");
  const gb200 = nvidiaProfile.products.find(product => product.id === "gb200-nvl72");
  const gb200Bandwidth = nvidiaProfile.claims.find(claim => claim.id === "gb200-hbm-bandwidth");
  const awsProfile = profileRegistry.companies.find(company => company.id === "amazon-aws");
  const trainium2Dense = awsProfile.claims.find(claim => claim.id === "trainium2-fp8-dense");
  const trainium2Sparse = awsProfile.claims.find(claim => claim.id === "trainium2-fp8-sparse");
  if (profileRegistry.schema_version !== "1.1" || productCount !== 16 ||
      claimCount !== 70 || evidenceCount !== 17 || metricContextCount < 40 ||
      !profileRegistry.comparison_policy.precision_must_match ||
      !profileRegistry.comparison_policy.sparsity_must_match ||
      !profileRegistry.comparison_policy.measurement_scope_must_match ||
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
      !mi355Evidence.includes("1 evidence record") ||
      !mi355Evidence.includes("6 reviewed claims")) {
    throw new Error("AMD MI355X evidence card is inconsistent: " + mi355Evidence);
  }
  await page.locator("[data-directory-search]").fill("");
  await page.locator("[data-directory-evidence-filter]").selectOption("fresh");
  if (await page.locator(".directory-result-title").count() !== 8) {
    throw new Error("Freshness filter should return the eight audited first-wave company profiles");
  }
  await page.locator("[data-directory-search]").fill("FuriosaAI");
  await page.locator("[data-directory-evidence-filter]").selectOption("not_reviewed");
  await page.locator("[data-directory-search]").fill("FuriosaAI");
  const companyMatches = await page.locator(".directory-result-title").allTextContents();
  if (!companyMatches.some(name => name.includes("FuriosaAI"))) {
    throw new Error("Directory search did not find FuriosaAI");
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
  console.log("PASS: six routes, landscape asset, homepage coverage stats, directory search/group/evidence filters, company profile registry, compatibility/workload/benchmark search, theme toggle and mobile navigation.");
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});
