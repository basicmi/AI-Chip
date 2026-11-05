---
layout: default
title: AI Accelerator Benchmarks
permalink: /benchmarks/
description: A curated directory of public AI accelerator benchmarks, result portals and measurement tools.
---

<section class="page-heading">
  <p class="eyebrow">PUBLIC BENCHMARK LANDSCAPE</p>
  <h1>AI Accelerator Benchmarks</h1>
  <p>A curated directory of benchmark suites, published result portals and measurement tools across AI training, inference, kernels, memory, interconnect, edge and power efficiency.</p>
  <div class="page-meta">
    <span>Catalogue <strong data-benchmark-version>Loading…</strong></span>
    <span>Last reviewed <strong data-benchmark-reviewed>—</strong></span>
    <a href="{{ '/data/benchmark-projects.json' | relative_url }}">Raw catalogue ↗</a>
  </div>
</section>

<section class="benchmark-explorer" data-benchmark-explorer data-source="{{ '/data/benchmark-projects.json' | relative_url }}">
  <div class="benchmark-summary">
    <div class="compat-stat"><span>Public resources</span><strong data-benchmark-stat="projects">—</strong></div>
    <div class="compat-stat"><span>Categories</span><strong data-benchmark-stat="categories">—</strong></div>
    <div class="compat-stat"><span>Result portals</span><strong data-benchmark-stat="portals">—</strong></div>
    <div class="compat-stat"><span>Tools & suites</span><strong data-benchmark-stat="tools">—</strong></div>
  </div>
  <div class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">EXPLORE THE LANDSCAPE</p><h2>Find benchmark resources</h2></div>
      <button class="text-button" type="button" data-benchmark-reset>Reset filters</button>
    </div>
    <div class="benchmark-filters">
      <label>Search<input type="search" data-benchmark-search placeholder="Project, maintainer, metric, keyword…" autocomplete="off"></label>
      <label>Category<select data-benchmark-category><option value="">All categories</option></select></label>
      <label>Resource type<select data-benchmark-kind><option value="">All resource types</option></select></label>
    </div>
  </div>
  <div class="benchmark-results-heading">
    <div><p class="eyebrow">DIRECTORY</p><h2><span data-benchmark-count>—</span> resources</h2></div>
    <p data-benchmark-summary aria-live="polite">Loading catalogue…</p>
  </div>
  <div class="compat-load-state" data-benchmark-load role="status">Loading benchmark catalogue…</div>
  <div class="benchmark-card-grid" data-benchmark-cards></div>
  <div class="compat-empty-state" data-benchmark-empty hidden><strong>No matching resources</strong><p>Try another search term or reset the filters.</p></div>
</section>

<section class="compat-method-note benchmark-editorial-note">
  <div><p class="eyebrow">EDITORIAL POLICY</p><h2>Directory, not leaderboard.</h2></div>
  <p>This site collects and explains publicly available benchmark information. It does not run benchmark experiments or certify hardware support. A benchmark suite, a measurement tool and a published result are different things. Vendor-reported, standardized-submission, upstream and independent results must be attributed to their original sources. Comparisons should preserve workload, model, software stack, hardware configuration, metric definitions and measurement boundaries; heterogeneous results should not be forced into one ranking.</p>
</section>

<script src="{{ '/assets/js/benchmark-explorer.js' | relative_url }}" defer></script>
