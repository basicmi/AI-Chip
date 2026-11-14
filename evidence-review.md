---
layout: default
title: Evidence Review Workbench
permalink: /evidence-review/
description: Local-only review of unverified intelligence claim and evidence graph artifacts.
---

<section class="page-heading">
  <p class="eyebrow">INTELLIGENCE · EVIDENCE · HUMAN REVIEW</p>
  <h1>Evidence Review Workbench</h1>
  <p>Review unverified technical claims, original sources, duplicate wording and reviewer-scoped comparison flags. Files are read locally in your browser; nothing is uploaded or approved.</p>
  <div class="page-meta">
    <span>Data <strong>local GitHub Actions artifacts</strong></span>
    <a href="https://github.com/basicmi/AI-Chip/actions/workflows/model-catalog-audit.yml" target="_blank" rel="noopener noreferrer">Download weekly discovery artifact ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/evidence-review-workbench.md">Review methodology ↗</a>
  </div>
</section>

<section class="evidence-workbench" data-evidence-workbench>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">01 / LOAD</p><h2>Open a review artifact</h2></div>
      <button class="text-button" type="button" data-ew-reset>Clear files</button>
    </div>
    <p>Download the ai-chip-intelligence-discovery artifact. Choose its Claim JSON and optional Evidence Graph JSON from the <strong>same run</strong>. The workbench does not fetch data automatically.</p>
    <div class="workload-filters">
      <label>Claim extraction JSON (required)
        <input type="file" accept=".json,application/json" data-ew-claims>
      </label>
      <label>Evidence graph JSON (optional)
        <input type="file" accept=".json,application/json" data-ew-graph>
      </label>
    </div>
    <p class="compat-load-state" data-ew-status role="status" aria-live="polite">Choose a Claim JSON file to begin.</p>
    <p class="compat-limitations" data-ew-provenance hidden></p>
  </section>
  <div class="workload-stat-grid">
    <div class="compat-stat"><span>Unverified claims</span><strong data-ew-stat="claims">—</strong></div>
    <div class="compat-stat"><span>Source documents</span><strong data-ew-stat="sources">—</strong></div>
    <div class="compat-stat"><span>Exact-text duplicate clusters</span><strong data-ew-stat="duplicates">—</strong></div>
    <div class="compat-stat"><span>Possible specification conflicts</span><strong data-ew-stat="conflicts">—</strong></div>
  </div>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">02 / TRIAGE</p><h2>Filter unverified claims</h2></div>
      <button class="text-button" type="button" data-ew-clear-filters>Reset filters</button>
    </div>
    <div class="workload-filters">
      <label>Search claim or source
        <input type="search" data-ew-search placeholder="GPU, HBM, publisher…" autocomplete="off" disabled>
      </label>
      <label>Topic
        <select data-ew-topic disabled><option value="">All topics</option></select>
      </label>
      <label>Publisher
        <select data-ew-publisher disabled><option value="">All publishers</option></select>
      </label>
      <label>Relationship
        <select data-ew-relationship disabled>
          <option value="">All candidate claims</option>
          <option value="duplicates">Exact-text duplicate</option>
          <option value="conflicts">Possible specification conflict</option>
          <option value="comparisons">Reviewer-scoped comparison</option>
          <option value="standalone">No flagged relationship</option>
        </select>
      </label>
    </div>
  </section>
  <div class="workload-results-heading">
    <div><p class="eyebrow">03 / REVIEW QUEUE</p><h2><span data-ew-result-count>0</span> candidates</h2></div>
    <p data-ew-summary>No review candidates loaded.</p>
  </div>
  <div class="model-support-grid" data-ew-results></div>
  <div class="compat-empty-state" data-ew-empty><strong>No claim candidates loaded</strong><p>Load a Claim JSON artifact to inspect unverified source-backed observations.</p></div>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">EVIDENCE POLICY</p><h2>Duplicates and conflicts are leads, not verification.</h2></div>
  <p>Identical wording may be syndicated from one origin. A numerical disagreement is not a proven contradiction. Only reviewer-scoped groups can flag possible conflicts. This page does not approve claims, change statuses or modify any formal registry.</p>
</section>
<link rel="stylesheet" href="{{ '/assets/css/evidence-review.css' | relative_url }}">
<script src="{{ '/assets/js/evidence-review-workbench.js' | relative_url }}" defer></script>
