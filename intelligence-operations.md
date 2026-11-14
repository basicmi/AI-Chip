---
layout: default
title: Intelligence Operations Dashboard
permalink: /intelligence-operations/
description: Local-only multi-run observability of AI Chip Intelligence source health, review backlog and cache recovery.
---

<section class="page-heading">
  <p class="eyebrow">INTELLIGENCE · OPERATIONAL HEALTH · HISTORY</p>
  <h1>Intelligence Operations</h1>
  <p>Compare actual weekly discovery snapshots: source availability, generated review leads, unverified claims and unresolved backlog. This is an operational view, not evidence verification or a live status monitor.</p>
  <div class="page-meta">
    <span>Input <strong>local Actions JSON snapshots</strong></span>
    <a href="https://github.com/basicmi/AI-Chip/actions/workflows/model-catalog-audit.yml" target="_blank" rel="noopener noreferrer">Browse weekly runs ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/intelligence-operations.md">Methodology ↗</a>
  </div>
</section>

<section class="evidence-workbench intelligence-operations" data-ops-dashboard>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">01 / LOCAL SNAPSHOTS</p><h2>Load one or more completed runs</h2></div>
      <button class="text-button" type="button" data-ops-clear>Clear</button>
    </div>
    <p>Download the <code>ai-chip-intelligence-discovery</code> artifact from each weekly run and select its <code>ai-chip-intelligence-operations.json</code>. Choose multiple files to compare distinct run timestamps. Files never leave your browser.</p>
    <label>Operational JSON snapshots
      <input type="file" accept=".json,application/json" multiple data-ops-files>
    </label>
    <p class="compat-load-state" data-ops-status role="status" aria-live="polite">No snapshots loaded.</p>
  </section>

  <div class="workload-stat-grid" aria-label="Most recent imported operational snapshot">
    <div class="compat-stat"><span>Latest source availability</span><strong data-ops-stat="availability">—</strong></div>
    <div class="compat-stat"><span>Latest review leads</span><strong data-ops-stat="leads">—</strong></div>
    <div class="compat-stat"><span>Unresolved backlog</span><strong data-ops-stat="backlog">—</strong></div>
    <div class="compat-stat"><span>Runs compared</span><strong data-ops-stat="runs">—</strong></div>
  </div>

  <section class="compat-filter-panel" data-ops-history-panel hidden>
    <div class="compat-filter-heading">
      <div><p class="eyebrow">02 / RUN HISTORY</p><h2>Observed run-to-run changes</h2></div>
      <span class="status-pill">Not a live feed</span>
    </div>
    <p>One point per imported run. Counts are operational outputs from completed workflows; a single snapshot is not a trend.</p>
    <div class="ops-table-scroll">
      <table class="ops-table">
        <thead><tr><th>Run timestamp (UTC)</th><th>Health</th><th>Sources</th><th>Leads</th><th>Claims</th><th>Backlog</th><th>Oldest unresolved</th></tr></thead>
        <tbody data-ops-history></tbody>
      </table>
    </div>
  </section>

  <section class="compat-filter-panel" data-ops-sources-panel hidden>
    <div class="compat-filter-heading">
      <div><p class="eyebrow">03 / SOURCE DIAGNOSTICS</p><h2>Source availability by run</h2></div>
      <span class="status-pill">Observed ≠ verified</span>
    </div>
    <label>Inspect snapshot
      <select data-ops-select></select>
    </label>
    <p data-ops-cache></p>
    <div data-ops-warnings class="compat-limitations"></div>
    <div class="ops-table-scroll">
      <table class="ops-table">
        <thead><tr><th>Source</th><th>Type</th><th>Run status</th><th>Recent items</th></tr></thead>
        <tbody data-ops-sources></tbody>
      </table>
    </div>
  </section>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">DATA BOUNDARIES</p><h2>Operational success is not factual verification.</h2></div>
  <p>Source availability means a feed was reached and parsed during a scan—not that its hardware or software claims are true. Cache presence is an observation, not a guarantee of preserved history. Missing failed runs, expired Actions artifacts, or manually omitted snapshots make trends incomplete. No production registry or review status is changed here.</p>
</section>

<link rel="stylesheet" href="{{ '/assets/css/evidence-review.css' | relative_url }}">
<link rel="stylesheet" href="{{ '/assets/css/intelligence-operations.css' | relative_url }}">
<script src="{{ '/assets/js/intelligence-operations.js' | relative_url }}" defer></script>
