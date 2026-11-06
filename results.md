---
layout: default
title: Benchmark Results
permalink: /results/
description: Source-linked public AI accelerator benchmark submissions and inference observations with configuration-aware filters.
---

<section class="page-heading">
  <p class="eyebrow">BENCHMARK INTELLIGENCE</p>
  <h1>Benchmark Results</h1>
  <p>Explore published AI system results with their model, workload, system boundary, software stack and source evidence intact. This is a source-linked result registry, not a universal leaderboard.</p>
  <div class="page-meta">
    <span>Registry <strong data-results-version>Loading…</strong></span>
    <span>Imported <strong data-results-imported>—</strong></span>
    <a href="{{ '/data/benchmark-results.json' | relative_url }}">Raw results ↗</a>
    <a href="{{ '/benchmarks/' | relative_url }}">Benchmark catalogue ↗</a>
  </div>
</section>

<section class="benchmark-results-explorer" data-benchmark-results data-source="{{ '/data/benchmark-results.json' | relative_url }}">
  <div class="benchmark-results-summary">
    <div class="compat-stat"><span>Result records</span><strong data-results-stat="total">—</strong></div>
    <div class="compat-stat"><span>Available</span><strong data-results-stat="available">—</strong></div>
    <div class="compat-stat"><span>Inferred submissions</span><strong data-results-stat="inferred">—</strong></div>
    <div class="compat-stat"><span>Measured power records</span><strong data-results-stat="power">—</strong></div>
    <div class="compat-stat"><span>Submitters</span><strong data-results-stat="submitters">—</strong></div>
  </div>

  <div class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">FILTER THE EVIDENCE</p><h2>Find comparable submissions</h2></div>
      <button class="text-button" type="button" data-results-reset>Reset filters</button>
    </div>
    <div class="benchmark-results-filters">
      <label>Search<input type="search" data-results-search placeholder="Model, system, submitter, framework, notes…" autocomplete="off"></label>
      <label>Source<select data-results-source><option value="">All sources</option></select></label>
      <label>Accelerator vendor<select data-results-vendor><option value="">All vendors</option></select></label>
      <label>Model<select data-results-model><option value="">All models</option></select></label>
      <label>Scenario<select data-results-scenario><option value="">All scenarios</option></select></label>
      <label>Availability<select data-results-availability><option value="">All statuses</option></select></label>
      <label>Submission type<select data-results-inferred><option value="">All submission types</option></select></label>
      <label>Division<select data-results-division><option value="">All divisions</option></select></label>
      <label>System type<select data-results-system><option value="">All system types</option></select></label>
    </div>
  </div>

  <div class="benchmark-results-heading">
    <div><p class="eyebrow">PUBLISHED RECORDS</p><h2><span data-results-count>—</span> results</h2></div>
    <p data-results-summary aria-live="polite">Loading result registry…</p>
  </div>
  <div class="compat-load-state" data-results-load role="status">Loading benchmark results…</div>
  <div class="benchmark-results-table-wrap">
    <table class="benchmark-results-table">
      <thead>
        <tr>
          <th>Submitter</th>
          <th>Accelerator / system</th>
          <th>Model / scenario</th>
          <th>Result</th>
          <th>Status / evidence</th>
        </tr>
      </thead>
      <tbody data-results-rows></tbody>
    </table>
  </div>
  <div class="compat-empty-state" data-results-empty hidden><strong>No matching results</strong><p>Try a broader filter or reset the filters.</p></div>
  <div class="benchmark-results-pagination">
    <button class="text-button" type="button" data-results-prev disabled>← Previous</button>
    <span data-results-page>Page 1</span>
    <button class="text-button" type="button" data-results-next disabled>Next →</button>
  </div>
</section>

<section class="benchmark-source-status" data-results-sources>
  <p class="eyebrow">DATA SOURCES</p>
  <h2>What is in the registry?</h2>
  <div data-results-source-cards></div>
</section>

<section class="compat-method-note benchmark-editorial-note">
  <div><p class="eyebrow">COMPARABILITY POLICY</p><h2>Context before ranking.</h2></div>
  <div>
    <p>Do not compare results across different benchmark suites, models, scenarios, divisions, system types, units or accuracy targets. For MLPerf, preserve the suite version, Closed/Open division, Available/Preview/RDI status, scenario, inference mode, accuracy target and full system boundary. Inferred submissions are marked separately.</p>
    <p>The MLPerf v6.1 summary snapshot contains no measured power records. Design power is not measured power. For InferenceX, TTFT/TPOT and throughput metrics retain the API's units; strict power comparisons require <code>power_valid=1</code> and <code>power_metric_schema_version=2</code>.</p>
    <p>Every row links to its publisher's source record where available. A public submission or observation is attributed to its publisher; it is not automatically an independent replication.</p>
  </div>
</section>

<script src="{{ '/assets/js/benchmark-results.js' | relative_url }}" defer></script>
