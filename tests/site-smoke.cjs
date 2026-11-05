const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1365, height: 900 } });
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  const base = "http://127.0.0.1:4173/AI-Chip";
  const routes = ["/", "/directory/", "/software-ecosystem/", "/compatibility/", "/workloads/", "/benchmarks/"];
  for (const route of routes) {
    const response = await page.goto(base + route, { waitUntil: "networkidle" });
    if (!response || !response.ok()) throw new Error("Route failed: " + route);
    await page.locator("header.site-header").waitFor();
    await page.locator("main#main-content").waitFor();
  }
  await page.goto(base + "/compatibility/", { waitUntil: "networkidle" });
  await page.locator("[data-result-count]").waitFor();
  if (await page.locator("[data-result-count]").textContent() !== "18") throw new Error("Expected 18 compatibility records");
  await page.locator("[data-filter-search]").fill("vLLM");
  if (Number(await page.locator("[data-result-count]").textContent()) < 1) throw new Error("Search did not return vLLM records");
  await page.locator("[data-filter-reset]").click();
  await page.locator("[data-theme-toggle]").click();
  if (await page.locator("html").getAttribute("data-theme") !== "dark") throw new Error("Dark theme toggle failed");
  await page.locator("[data-theme-toggle]").click();
  await page.goto(base + "/workloads/", { waitUntil: "networkidle" });
  await page.locator("[data-workload-result-count]").waitFor();
  if (await page.locator("[data-workload-result-count]").textContent() !== "17") throw new Error("Expected 17 workload paths");
  await page.locator("[data-workload-search]").fill("Biren");
  if (await page.locator("[data-workload-result-count]").textContent() !== "1") throw new Error("Workload search did not isolate Biren path");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("[data-nav-toggle]").click();
  if (await page.locator("[data-nav-toggle]").getAttribute("aria-expanded") !== "true") throw new Error("Mobile nav did not open");
  await page.locator("[data-site-nav] a[href*='workloads']").click();
  if (await page.locator("[data-nav-toggle]").getAttribute("aria-expanded") !== "false") throw new Error("Mobile nav did not close after navigation");
  if (errors.length) throw new Error("Browser errors: " + errors.join(" | "));
  console.log("PASS: six routes, compatibility search, workload search, theme toggle and mobile navigation.");
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
