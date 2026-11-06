---
layout: default
title: Software Compatibility Explorer
permalink: /compatibility/
description: Search software compatibility and integration evidence across AI accelerator platforms.
---

<section class="page-heading">
  <p class="eyebrow">SOFTWARE × HARDWARE</p>
  <h1>Compatibility Explorer</h1>
  <p>Search documented software integrations across AI accelerator platforms. Inspect version pins, support maturity, limitations and the primary sources behind each record.</p>
  <div class="page-meta">
    <span>Dataset <strong data-database-version>Loading…</strong></span>
    <span>Last reviewed <strong data-last-reviewed>—</strong></span>
    <a href="{{ '/data/compatibility.json' | relative_url }}">Raw JSON ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/schemas/compatibility.schema.json" target="_blank" rel="noopener noreferrer">JSON Schema ↗</a>
  </div>
</section>

<section class="compat-explorer" data-compatibility-explorer data-source="{{ '/data/compatibility.json' | relative_url }}">
  <div class="compat-stat-grid" aria-label="Dataset summary">
    <div class="compat-stat"><span>Accelerator platforms</span><strong data-stat="platforms">—</strong></div>
    <div class="compat-stat"><span>Integration records</span><strong data-stat="integrations">—</strong></div>
    <div class="compat-stat"><span>Documented support paths</span><strong data-stat="documented">—</strong></div>
    <div class="compat-stat"><span>Experimental / review</span><strong data-stat="review">—</strong></div>
  </div>

  <div class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">QUERY THE DATASET</p><h2>Find a software path</h2></div>
      <button type="button" class="text-button" data-filter-reset>Reset filters</button>
    </div>
    <div class="compat-filters">
      <label class="filter-search">Search
        <input type="search" placeholder="Vendor, chip, framework, version…" data-filter-search autocomplete="off">
      </label>
      <label>Accelerator
        <select data-filter-platform><option value="">All platforms</option></select>
      </label>
      <label>Software layer
        <select data-filter-layer><option value="">All layers</option></select>
      </label>
      <label>Support status
        <select data-filter-status><option value="">All statuses</option></select>
      </label>
      <label>Sort by
        <select data-filter-sort><option value="vendor">Vendor</option><option value="project">Project</option></select>
      </label>
    </div>
    <div class="compat-status-legend">
      <span><i class="legend-dot dot-supported"></i> Documented support</span>
      <span><i class="legend-dot dot-experimental"></i> Experimental / in progress</span>
      <span><i class="legend-dot dot-review"></i> Needs review</span>
    </div>
  </div>

  <div class="compat-results-heading">
    <div><p class="eyebrow">MATCHING RECORDS</p><h2><span data-result-count>—</span> integrations</h2></div>
    <p data-results aria-live="polite">Loading compatibility records…</p>
  </div>
  <div class="compat-load-state" data-load-state role="status">Loading compatibility data…</div>
  <div class="compat-card-grid" data-result-cards></div>
  <div class="compat-empty-state" data-empty-state hidden>
    <strong>No matching integrations</strong>
    <p>Try a broader search or reset one or more filters.</p>
  </div>
</section>

<section class="compat-method-note">
  <h2>Platform support vs. product-specific support</h2>
  <p>Some integrations are documented only for a broad hardware platform (for example, an architecture family or vendor backend). These appear as <strong>platform-level</strong> records and must not be read as SKU validation. A record is marked <strong>product-specific</strong> only when its linked upstream or vendor evidence explicitly names the product or generation; that mapping is also linked back to the Product Explorer. Neither level guarantees support for every model, operator, quantization format or serving feature.</p>

  <div><p class="eyebrow">READ THE STATUS CORRECTLY</p><h2>Compatibility is not a binary property.</h2></div>
  <p>A platform being listed does not mean every model, operator, precision or serving feature is supported. Each record is scoped to its documented device family, software layer and version pins. Vendor-reported examples are kept distinct from upstream-supported paths; unresolved version conflicts are marked for review.</p>
</section>

<script src="{{ '/assets/js/compatibility-explorer.js' | relative_url }}" defer></script>
