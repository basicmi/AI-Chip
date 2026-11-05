---
layout: default
title: AI Accelerator Product Explorer
permalink: /products/
description: Explore and compare AI accelerator products using source-linked specifications and explicit measurement context.
---

<section class="page-heading">
  <p class="eyebrow">PRODUCTS × ARCHITECTURE × EVIDENCE</p>
  <h1>AI Accelerator Product Explorer</h1>
  <p>Search product generations and compare their published specifications. Every metric retains its precision, dense/sparse mode, measurement scope and source; this is a technical comparison workspace, not a performance ranking.</p>
  <div class="page-meta">
    <span>Registry <strong data-product-version>Loading…</strong></span>
    <span>Last reviewed <strong data-product-reviewed>—</strong></span>
    <a href="{{ '/data/company-profiles.json' | relative_url }}">Raw product registry ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/schemas/company-profiles.schema.json" target="_blank" rel="noopener noreferrer">Schema v1.1 ↗</a>
  </div>
</section>

<section class="product-explorer" data-product-explorer data-source="{{ '/data/company-profiles.json' | relative_url }}">
  <div class="product-stat-grid" aria-label="Product registry summary">
    <div class="product-stat"><span>Companies in directory</span><strong data-product-stat="companies">—</strong></div>
    <div class="product-stat"><span>Structured products</span><strong data-product-stat="products">—</strong></div>
    <div class="product-stat"><span>Structured claims</span><strong data-product-stat="claims">—</strong></div>
    <div class="product-stat"><span>Reviewed source records</span><strong data-product-stat="evidence">—</strong></div>
  </div>

  <section class="product-filter-panel">
    <div class="product-filter-heading">
      <div><p class="eyebrow">QUERY THE CATALOGUE</p><h2>Find an accelerator</h2></div>
      <button type="button" class="text-button" data-product-reset>Reset filters</button>
    </div>
    <div class="product-filters">
      <label class="product-search">Search
        <input type="search" placeholder="Product, vendor, architecture, specification…" data-product-search autocomplete="off">
      </label>
      <label>Company
        <select data-product-company><option value="">All companies</option></select>
      </label>
      <label>Product type
        <select data-product-type><option value="">All types</option></select>
      </label>
      <label>Availability
        <select data-product-availability><option value="">All statuses</option></select>
      </label>
      <label>Precision
        <select data-product-precision><option value="">All precisions</option></select>
      </label>
    </div>
  </section>

  <div class="product-results-heading">
    <p data-product-count aria-live="polite">Loading product records…</p>
    <span>Source-linked · No composite ranking</span>
  </div>
  <div class="product-results-grid" data-product-results></div>
  <div class="product-empty-state" data-product-empty hidden>
    <strong>No matching products</strong>
    <p>Try a broader search or reset one or more filters.</p>
  </div>

  <section class="product-compare-panel" aria-labelledby="product-compare-title">
    <div class="product-compare-heading">
      <div><p class="eyebrow">SIDE-BY-SIDE ANALYSIS</p><h2 id="product-compare-title">Comparison workspace</h2></div>
      <div class="product-compare-actions">
        <span data-product-compare-count>0 / 4 selected</span>
        <button type="button" class="text-button" data-product-compare-clear>Clear selection</button>
      </div>
    </div>
    <p class="product-compare-note" data-product-compare-note>Select two to four products from the catalogue. Metrics are aligned only when their topic, precision, sparsity, scope, measurement type and unit match; unmatched values remain separate.</p>
    <div class="product-compare-empty" data-product-compare-empty>
      Choose products above to build a comparison. System-level aggregates and per-chip specifications are intentionally kept in separate rows.
    </div>
    <div class="product-compare-table-wrap" data-product-compare-table hidden></div>
  </section>
</section>

<section class="product-method-note">
  <div><p class="eyebrow">HOW TO READ THE DATA</p><h2>Comparable means same measurement context.</h2></div>
  <p>Peak compute is separated by precision and dense/sparse mode. Memory and interconnect figures retain their original units and hardware boundary. A rack-level aggregate is not a per-chip specification; a vendor peak is not an application benchmark. Follow each claim to its source before drawing conclusions.</p>
</section>

<script src="{{ '/assets/js/product-explorer.js' | relative_url }}" defer></script>
