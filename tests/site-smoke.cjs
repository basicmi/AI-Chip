const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1365, height: 900 } });
  const base = "http://127.0.0.1:4173/AI-Chip";
  const errors = [];

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
  if (!landscapeInfo.src.includes("AI_Chip_Landscape_v0p9.svg") ||
      landscapeInfo.width < 1800 || landscapeInfo.height < 1200) {
    throw new Error("Landscape image did not load the expected high-resolution v0.9 asset: " +
      JSON.stringify(landscapeInfo));
  }

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
  console.log("PASS: six routes, v0.9 landscape asset, dataset loading and count consistency, compatibility search, workload search, theme toggle and mobile navigation.");
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});
