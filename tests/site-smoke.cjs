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
      !homeStatValues.every(value => /^\\d+$/.test(value))) {
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
    return count && count.dataset.ready === "true";
  }, null, { timeout: 10000 });
  const companyCount = Number(await page.locator("[data-directory-count]").getAttribute("data-count"));
  if (companyCount < 40) throw new Error("Directory company index is unexpectedly incomplete: " + companyCount);
  await page.locator("[data-directory-search]").fill("FuriosaAI");
  const companyMatches = await page.locator(".directory-result-title").allTextContents();
  if (!companyMatches.some(name => name.includes("FuriosaAI"))) {
    throw new Error("Directory search did not find FuriosaAI");
  }
  await page.locator("[data-directory-search]").fill("");
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
  console.log("PASS: six routes, landscape asset, homepage coverage stats, directory search and group filter, compatibility/workload/benchmark search, theme toggle and mobile navigation.");
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});
