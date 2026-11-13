---
layout: default
title: Model Support Explorer
permalink: /model-support/
description: Evidence-backed model support paths across AI accelerator products, software stacks, precision modes and deployment configurations.
---

<section class="page-heading">
  <p class="eyebrow">MODEL × ACCELERATOR × SOFTWARE</p>
  <h1>Model Support Explorer</h1>
  <p>Browse current model releases independently of verified accelerator deployment paths. A model card confirms the checkpoint exists; only the hardware matrix below carries configuration-specific support evidence.</p>
  <div class="page-meta">
    <span>Registry <strong data-model-support-version>Loading…</strong></span>
    <span>Last reviewed <strong data-model-support-reviewed>—</strong></span>
    <a href="{{ '/data/model-catalog.json' | relative_url }}">Model catalog JSON ↗</a>
    <a href="{{ '/data/model-support.json' | relative_url }}">Hardware support JSON ↗</a>
    <a href="{{ '/schemas/model-support.schema.json' | relative_url }}">JSON Schema ↗</a>
  </div>
</section>

<section class="model-support-explorer" data-model-support-explorer
  data-source="{{ '/data/model-support.json' | relative_url }}"
  data-catalog-source="{{ '/data/model-catalog.json' | relative_url }}"
  data-product-source="{{ '/data/company-profiles.json' | relative_url }}"
  data-compat-source="{{ '/data/compatibility.json' | relative_url }}">
  <div class="workload-stat-grid">
    <div class="compat-stat"><span>Catalog checkpoints</span><strong data-model-stat="models">—</strong></div>
    <div class="compat-stat"><span>Documented model paths</span><strong data-model-stat="paths">—</strong></div>
    <div class="compat-stat"><span>Official recipes</span><strong data-model-stat="recipes">—</strong></div>
    <div class="compat-stat"><span>Upstream verified</span><strong data-model-stat="upstream">—</strong></div>
  </div>
  <section class="compat-filter-panel" aria-labelledby="model-catalog-heading">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">MODEL CATALOG</p><h2 id="model-catalog-heading">Explore model checkpoints</h2></div>
      <button class="text-button" type="button" data-catalog-reset>Reset filters</button>
    </div>
    <p>Models are included based on checkpoint metadata, not hardware support. An empty support path count means no accelerator deployment evidence has been curated yet—not that the model is incompatible.</p>
    <div class="workload-filters">
      <label>Search checkpoints
        <input type="search" data-catalog-search placeholder="Model, publisher, architecture, capability…" autocomplete="off">
      </label>
      <label>Publisher
        <select data-catalog-publisher><option value="">All publishers</option></select>
      </label>
      <label>Hardware evidence
        <select data-catalog-coverage>
          <option value="">All catalog checkpoints</option>
          <option value="evidence">With evidence-backed support paths</option>
          <option value="catalog_only">Catalog only (support not yet verified)</option>
        </select>
      </label>
    </div>
  </section>
  <div class="workload-results-heading">
    <div><p class="eyebrow">CHECKPOINTS</p><h2><span data-catalog-result-count>—</span> models</h2></div>
    <p data-catalog-result-summary aria-live="polite">Loading catalog…</p>
  </div>
  <div class="model-support-grid" data-catalog-cards></div>
  <div class="compat-empty-state" data-catalog-empty hidden><strong>No matching models</strong><p>Try a broader query.</p></div>
  <div class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">HARDWARE SUPPORT MATRIX</p><h2>Find an evidence-backed execution path</h2></div>
      <button class="text-button" type="button" data-model-reset>Reset filters</button>
    </div>
    <div class="workload-filters">
      <label>Search
        <input type="search" data-model-search placeholder="Model, product, vendor, framework…" autocomplete="off">
      </label>
      <label>Accelerator platform
        <select data-model-platform><option value="">All platforms</option></select>
      </label>
      <label>Publisher
        <select data-model-publisher><option value="">All publishers</option></select>
      </label>
      <label>Evidence level
        <select data-model-level><option value="">All evidence levels</option></select>
      </label>
    </div>
  </div>
  <div class="workload-results-heading">
    <div><p class="eyebrow">DOCUMENTED PATHS</p><h2><span data-model-result-count>—</span> paths</h2></div>
    <p data-model-result-summary aria-live="polite">Loading model support data…</p>
  </div>
  <div class="compat-load-state" data-model-load role="status">Loading model support data…</div>
  <div class="model-support-grid" data-model-cards></div>
  <div class="compat-empty-state" data-model-empty hidden><strong>No matching model paths</strong><p>Try a broader query or reset the filters.</p></div>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">EVIDENCE POLICY</p><h2>Model support is configuration-specific.</h2></div>
  <p><strong>Documented recipe</strong> means a vendor or upstream project publishes a deployment procedure. <strong>Upstream verified</strong> means the upstream project explicitly lists a model/hardware combination. Neither is an independent reproduction by AI-Chip. A complete support claim must eventually pin the exact model checkpoint, accelerator SKU or system, software release, precision/quantization, parallelism and serving features. Performance measurements are maintained separately in Benchmark Results.</p>
</section>

<script src="{{ '/assets/js/model-support-explorer.js' | relative_url }}" defer></script>
