---
layout: default
title: Workload Explorer
permalink: /workloads/
description: Explore AI workloads and evidence-scoped hardware/software execution paths.
---

<section class="page-heading">
  <p class="eyebrow">MODEL × WORKLOAD × SYSTEM</p>
  <h1>Workload Explorer</h1>
  <p>Start with the workload, not the chip. Explore candidate execution paths and see exactly what the available evidence establishes — and what remains unverified.</p>
  <div class="page-meta">
    <span>Dataset <strong data-workload-version>Loading…</strong></span>
    <span>Last reviewed <strong data-workload-reviewed>—</strong></span>
    <a href="{{ '/data/workloads.json' | relative_url }}">Raw workload data ↗</a>
    <a href="{{ '/schemas/workloads.schema.json' | relative_url }}">JSON Schema ↗</a>
  </div>
</section>

<section class="workload-explorer" data-workload-explorer data-source="{{ '/data/workloads.json' | relative_url }}" data-compat-source="{{ '/data/compatibility.json' | relative_url }}">
  <div class="workload-stat-grid">
    <div class="compat-stat"><span>Workload definitions</span><strong data-workload-stat="workloads">—</strong></div>
    <div class="compat-stat"><span>Candidate execution paths</span><strong data-workload-stat="paths">—</strong></div>
    <div class="compat-stat"><span>Integration documented only</span><strong data-workload-stat="integration">—</strong></div>
    <div class="compat-stat"><span>Vendor-reported</span><strong data-workload-stat="vendor">—</strong></div>
  </div>

  <div class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">DEFINE YOUR WORKLOAD</p><h2>Find candidate execution paths</h2></div>
      <button class="text-button" type="button" data-workload-reset>Reset filters</button>
    </div>
    <div class="workload-filters">
      <label>Search
        <input type="search" data-workload-search placeholder="Model, task, accelerator, software…" autocomplete="off">
      </label>
      <label>Workload
        <select data-workload-kind><option value="">All workloads</option></select>
      </label>
      <label>Accelerator
        <select data-workload-platform><option value="">All platforms</option></select>
      </label>
      <label>Evidence status
        <select data-workload-status><option value="">All statuses</option></select>
      </label>
    </div>
  </div>

  <div class="workload-results-heading">
    <div><p class="eyebrow">CANDIDATE PATHS</p><h2><span data-workload-result-count>—</span> paths</h2></div>
    <p data-workload-result-summary aria-live="polite">Loading workload data…</p>
  </div>
  <div class="compat-load-state" data-workload-load role="status">Loading workload data…</div>
  <div class="workload-path-grid" data-workload-cards></div>
  <div class="compat-empty-state" data-workload-empty hidden><strong>No matching paths</strong><p>Try a broader query or reset the filters.</p></div>
</section>

<section class="workload-catalog-section">
  <div class="section-heading">
    <div><p class="eyebrow">WORKLOAD TAXONOMY</p><h2>What should be measured?</h2></div>
    <p>Each definition identifies the workload dimensions that must be pinned before results can be compared.</p>
  </div>
  <div class="workload-catalog" data-workload-catalog></div>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">EVIDENCE POLICY</p><h2>Integration is not validation.</h2></div>
  <p><strong>Integration only</strong> means the software-to-platform path is documented. <strong>Vendor reported</strong> means a vendor has described an adaptation. Neither establishes a reproducible workload test. Higher maturity requires an explicit model, device configuration, software versions, correctness criteria and, for benchmark claims, a measurement methodology and raw result evidence. Empty metric arrays are intentional — no performance numbers are fabricated.</p>
</section>

<script src="{{ '/assets/js/workload-explorer.js' | relative_url }}" defer></script>
