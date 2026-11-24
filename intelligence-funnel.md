---
layout: default
title: Evidence-to-Database Funnel
permalink: /intelligence-funnel/
description: Read-only tracking from public discovery through human review to manually receipted registry integrations.
---

<section class="page-heading">
  <p class="eyebrow">INTELLIGENCE · PHASE 2 · KNOWLEDGE CONVERSION</p>
  <h1>Evidence-to-Database Conversion</h1>
  <p>Track how public observations become structured Claim candidates, receive human workflow decisions, and are eventually represented by manually reviewed changes to curated registries.</p>
  <div class="page-meta">
    <span>Input <strong>local Actions JSON files</strong></span>
    <a href="https://github.com/basicmi/AI-Chip/actions/workflows/model-catalog-audit.yml" target="_blank" rel="noopener noreferrer">Weekly discovery artifacts ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/intelligence-conversion-funnel.md">Methodology ↗</a>
  </div>
</section>

<section class="evidence-workbench intelligence-operations" data-conversion-funnel>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">01 / IMPORT</p><h2>Load conversion snapshots</h2></div>
      <button class="text-button" type="button" data-cf-clear>Clear</button>
    </div>
    <p>Select one or more ai-chip-intelligence-conversion-funnel.json files from completed weekly runs. Files are parsed and validated locally; nothing is uploaded.</p>
    <label>Conversion funnel JSON snapshots
      <input type="file" accept=".json,application/json" multiple data-cf-files>
    </label>
    <p class="compat-load-state" role="status" aria-live="polite" data-cf-status>No conversion snapshots loaded.</p>
  </section>

  <div class="workload-stat-grid">
    <div class="compat-stat"><span>Latest discovered candidates</span><strong data-cf-stat="candidates">—</strong></div>
    <div class="compat-stat"><span>Latest extracted Claims</span><strong data-cf-stat="claims">—</strong></div>
    <div class="compat-stat"><span>Human decisions recorded</span><strong data-cf-stat="decisions">—</strong></div>
    <div class="compat-stat"><span>Claims with integration receipts</span><strong data-cf-stat="integrated">—</strong></div>
  </div>

  <section class="compat-filter-panel" data-cf-history-panel hidden>
    <div class="compat-filter-heading">
      <div><p class="eyebrow">02 / HISTORY</p><h2>Conversion trends</h2></div>
      <span class="status-pill">Imported runs only</span>
    </div>
    <p>Rates use explicitly named denominators. A missing denominator is N/A, not zero. Counts from different stages are not assumed to be a monotonic funnel.</p>
    <div class="ops-table-scroll">
      <table class="ops-table">
        <thead><tr><th>Run UTC</th><th>Discovery candidates</th><th>Extracted Claims</th><th>Review backlog</th><th>Human decisions</th><th>Decision coverage</th><th>Eligible for attachment</th><th>Integrated Claims</th><th>Integration coverage</th></tr></thead>
        <tbody data-cf-history></tbody>
      </table>
    </div>
  </section>

  <section class="compat-filter-panel" data-cf-detail-panel hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">03 / CURRENT RUN</p><h2>Stage breakdown and interpretation</h2></div></div>
    <label>Inspect run
      <select data-cf-select></select>
    </label>
    <div data-cf-details class="compat-limitations"></div>
  </section>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">GOVERNANCE BOUNDARIES</p><h2>Conversion is not verification</h2></div>
  <p>accepted_for_evidence_attachment is only permission to prepare a proposed evidence attachment. An integration receipt is counted only when it names an existing allowlisted registry record and a merged AI-Chip pull request. The receipt is an audit trail, not independent authentication of the underlying technical claim. The workflow never writes to production registries.</p>
</section>
<link rel="stylesheet" href="{{ '/assets/css/evidence-review.css' | relative_url }}">
<link rel="stylesheet" href="{{ '/assets/css/intelligence-operations.css' | relative_url }}">
<script src="{{ '/assets/js/intelligence-conversion-funnel.js' | relative_url }}" defer></script>
