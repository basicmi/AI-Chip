---
layout: default
title: Evidence Quality Dashboard
permalink: /evidence-quality/
description: Local-only trends for source provenance, quote traceability, and human-review workload.
---

<section class="page-heading">
  <p class="eyebrow">INTELLIGENCE · EVIDENCE QUALITY · REVIEW COVERAGE</p>
  <h1>Evidence Quality Dashboard</h1>
  <p>Compare completed discovery reports for quote traceability, provenance coverage and review backlog. Source completeness is not factual accuracy; queued human reviews are not completed judgments.</p>
  <div class="page-meta">
    <span>Input <strong>local Actions JSON files</strong></span>
    <a href="https://github.com/basicmi/AI-Chip/actions/workflows/model-catalog-audit.yml" target="_blank" rel="noopener noreferrer">Weekly discovery artifacts ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/intelligence-evidence-dashboard.md">Methodology ↗</a>
  </div>
</section>
<section class="evidence-workbench intelligence-operations" data-quality-dashboard>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">01 / IMPORT</p><h2>Load evidence-quality snapshots</h2></div>
      <button class="text-button" type="button" data-eq-clear>Clear</button>
    </div>
    <p>Select one or more <code>ai-chip-intelligence-evidence-dashboard.json</code> files from completed weekly runs. All validation and rendering happens locally.</p>
    <label>Evidence quality JSON snapshots
      <input type="file" accept=".json,application/json" multiple data-eq-files>
    </label>
    <p class="compat-load-state" role="status" aria-live="polite" data-eq-status>No snapshots loaded.</p>
    <label>Optional human semantic-review evaluation JSON (generated after two reviewers complete the same batch)
      <input type="file" accept=".json,application/json" data-eq-semantic-eval>
    </label>
    <p class="compat-load-state" role="status" aria-live="polite" data-eq-eval-status>No human evaluation loaded. Results are supplied locally and are not independently authenticated.</p>
    <label>Optional human source-lineage evaluation JSON (annotated source origins, same run)
      <input type="file" accept=".json,application/json" data-eq-lineage-eval>
    </label>
    <p class="compat-load-state" role="status" aria-live="polite" data-eq-lineage-status>No source-lineage evaluation loaded. Reviewer statements are not independently authenticated.</p>
  </section>
  <div class="workload-stat-grid">
    <div class="compat-stat"><span>Latest quote traceability</span><strong data-eq-stat="quotes">—</strong></div>
    <div class="compat-stat"><span>Latest provenance completeness</span><strong data-eq-stat="provenance">—</strong></div>
    <div class="compat-stat"><span>Latest unresolved Claims</span><strong data-eq-stat="unresolved">—</strong></div>
    <div class="compat-stat"><span>Runs imported</span><strong data-eq-stat="runs">—</strong></div>
  </div>
  <section class="compat-filter-panel" data-eq-history-panel hidden>
    <div class="compat-filter-heading">
      <div><p class="eyebrow">02 / HISTORY</p><h2>Evidence hygiene and review queue trends</h2></div>
      <span class="status-pill">Imported runs only</span>
    </div>
    <p>Missing human evaluations are displayed as N/A, never 0% or 100%. Percentages use the current run's Claim count as denominator. Backlog is persistent across runs.</p>
    <div class="ops-table-scroll">
      <table class="ops-table">
        <thead><tr><th>Run UTC</th><th>Claims</th><th>Quote traceability</th><th>Provenance</th><th>Metadata mismatches</th><th>Source documents</th><th>Backlog</th><th>Unresolved</th><th>Payload coverage</th><th>Lineage queued</th><th>Semantic queued</th><th>Human reported agreement</th><th>Lineage clusters reviewed</th></tr></thead>
        <tbody data-eq-history></tbody>
      </table>
    </div>
  </section>
  <section class="compat-filter-panel" data-eq-detail-panel hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">03 / CURRENT RUN</p><h2>Source evidence vs human judgments</h2></div></div>
    <label>Inspect run
      <select data-eq-select></select>
    </label>
    <div data-eq-details class="compat-limitations"></div>
  </section>
</section>
<section class="evidence-workbench intelligence-operations" data-decision-analytics>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">04 / DECISION ANALYTICS</p><h2>Human review outcomes and reasons</h2></div>
      <button class="text-button" type="button" data-da-clear>Clear</button>
    </div>
    <p>Import <code>ai-chip-intelligence-decision-analytics.json</code> from completed weekly runs. Review reasons are counted only when explicitly coded by a human; free-text notes are never classified automatically.</p>
    <label>Decision analytics JSON snapshots
      <input type="file" accept=".json,application/json" multiple data-da-files>
    </label>
    <p class="compat-load-state" role="status" aria-live="polite" data-da-status>No decision analytics loaded.</p>
  </section>
  <div class="workload-stat-grid" data-da-results hidden>
    <div class="compat-stat"><span>Decision coverage</span><strong data-da-stat="decision-coverage">—</strong></div>
    <div class="compat-stat"><span>Explicit reason-code coverage</span><strong data-da-stat="reason-coverage">—</strong></div>
    <div class="compat-stat"><span>Median decision latency</span><strong data-da-stat="median-latency">—</strong></div>
    <div class="compat-stat"><span>Unresolved Claims 14+ days</span><strong data-da-stat="overdue">—</strong></div>
  </div>
  <section class="compat-filter-panel" data-da-results hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">HISTORY</p><h2>Decision process over time</h2></div></div>
    <div class="ops-table-scroll"><table class="ops-table">
      <thead><tr><th>Run UTC</th><th>Decisions</th><th>Decision coverage</th><th>Reason-coded</th><th>Reason coverage</th><th>Median latency</th><th>Overdue 14+ days</th></tr></thead>
      <tbody data-da-history></tbody>
    </table></div>
  </section>
  <div class="workload-stat-grid" data-da-results hidden>
    <section class="compat-filter-panel">
      <p class="eyebrow">LATEST RUN</p><h2>Decision outcomes</h2>
      <div class="ops-table-scroll"><table class="ops-table">
        <thead><tr><th>Outcome</th><th>Claims</th></tr></thead><tbody data-da-outcomes></tbody>
      </table></div>
    </section>
    <section class="compat-filter-panel">
      <p class="eyebrow">LATEST RUN</p><h2>Explicit primary reasons</h2>
      <div class="ops-table-scroll"><table class="ops-table">
        <thead><tr><th>Reason code</th><th>Claims</th></tr></thead><tbody data-da-reasons></tbody>
      </table></div>
    </section>
  </div>
  <p class="compat-limitations">Decision latency starts at first observation in the persistent cache, not publication. Reason codes are reviewer assertions, not independently authenticated labels. These metrics describe workflow operations, not technical truth or reviewer accuracy.</p>
</section>
<section class="compat-method-note">
  <div><p class="eyebrow">INTERPRETATION BOUNDARIES</p><h2>No composite trust score</h2></div>
  <p>A quote found in an excerpt does not imply semantic entailment. Different source URLs, publishers or reviewer-assigned origin keys do not establish experimental independence. Blank human templates do not count as completed reviews; human agreement is unavailable until actual reviewed evaluations are supplied. Accepted-for-evidence-attachment is a workflow state, not factual verification. No database changes result from this dashboard.</p>
</section>
<link rel="stylesheet" href="{{ '/assets/css/evidence-review.css' | relative_url }}">
<link rel="stylesheet" href="{{ '/assets/css/intelligence-operations.css' | relative_url }}">
<script src="{{ '/assets/js/intelligence-evidence-quality.js' | relative_url }}" defer></script>
<script src="{{ '/assets/js/intelligence-decision-analytics.js' | relative_url }}" defer></script>
