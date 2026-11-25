---
layout: default
title: InferenceX Data Coverage
permalink: /coverage/
description: Explore completeness, missing metadata and metric coverage in the published InferenceX benchmark registry.
---

<section class="page-heading">
  <p class="eyebrow">PERFORMANCE INTELLIGENCE · EVIDENCE COVERAGE</p>
  <h1>InferenceX Data Coverage Explorer</h1>
  <p>See which workload, hardware, software and metric fields are actually present in the published registry. Coverage describes the records we have—not the completeness of every result published by the benchmark provider.</p>
  <div class="page-meta">
    <span>Registry <strong data-coverage-version>Loading…</strong></span>
    <span>Imported <strong data-coverage-imported>—</strong></span>
    <a href="{{ '/results/' | relative_url }}">Explore published results ↗</a>
    <a href="{{ '/data/benchmark-results.json' | relative_url }}">Raw registry ↗</a>
  </div>
</section>

<section class="coverage-explorer" data-coverage-explorer data-source="{{ '/data/benchmark-results.json.gz' | relative_url }}">
  <div class="coverage-summary">
    <div class="compat-stat"><span>InferenceX records</span><strong data-coverage-stat="records">—</strong></div>
    <div class="compat-stat"><span>Complete comparability fields</span><strong data-coverage-stat="comparable">—</strong></div>
    <div class="compat-stat"><span>Hardware + recipe fingerprint</span><strong data-coverage-stat="hardware-recipe">—</strong></div>
    <div class="compat-stat"><span>Records with a valid normalized metric</span><strong data-coverage-stat="metrics">—</strong></div>
  </div>

  <section class="coverage-panel">
    <div class="coverage-panel-heading">
      <div><p class="eyebrow">FIELD COMPLETENESS</p><h2>Where is metadata missing?</h2></div>
      <label>Dimension
        <select data-coverage-dimension>
          <option value="model">Model</option>
          <option value="hardware">Hardware</option>
          <option value="framework">Framework</option>
          <option value="recipe">Recipe fingerprint</option>
          <option value="benchmark-version">Benchmark version</option>
          <option value="isl">Input length · ISL</option>
          <option value="osl">Output length · OSL</option>
          <option value="concurrency">Concurrency</option>
          <option value="precision">Precision</option>
          <option value="serving-mode">Serving mode</option>
          <option value="prefill-gpus">Prefill GPUs</option>
          <option value="decode-gpus">Decode GPUs</option>
          <option value="topology">Topology</option>
          <option value="configuration">Stable configuration</option>
        </select>
      </label>
    </div>
    <div class="coverage-dimension-summary" data-coverage-dimension-summary aria-live="polite">Loading coverage…</div>
    <div class="coverage-bars" data-coverage-bars></div>
    <div class="coverage-value-list" data-coverage-values></div>
  </section>

  <section class="coverage-panel">
    <div class="coverage-panel-heading">
      <div><p class="eyebrow">METRIC AVAILABILITY</p><h2>Which performance metrics are usable?</h2></div>
      <p>Values count only when numeric, finite and consistent with the expected unit, metric family and optimization direction.</p>
    </div>
    <div class="coverage-metric-list" data-coverage-metrics></div>
  </section>

  <section class="coverage-panel">
    <div class="coverage-panel-heading">
      <div><p class="eyebrow">MISSING EVIDENCE</p><h2>Inspect records with gaps</h2></div>
      <p>Filter the registry to records missing the selected dimension. Source links are retained so gaps can be checked against the publisher.</p>
    </div>
    <div class="coverage-gap-controls">
      <label>Show records missing
        <select data-coverage-gap-field>
          <option value="hardware">Hardware</option>
          <option value="recipe">Recipe fingerprint</option>
          <option value="isl">ISL</option>
          <option value="osl">OSL</option>
          <option value="concurrency">Concurrency</option>
          <option value="precision">Precision</option>
          <option value="framework">Framework</option>
          <option value="configuration">Stable configuration</option>
        </select>
      </label>
      <label>Search records<input type="search" data-coverage-search placeholder="Model, hardware, submitter or record ID…"></label>
    </div>
    <p class="coverage-gap-count" data-coverage-gap-count aria-live="polite">Loading…</p>
    <div class="coverage-gap-table-wrap">
      <table class="coverage-gap-table">
        <thead><tr><th>Record</th><th>Model</th><th>Hardware</th><th>Missing field</th><th>Source</th></tr></thead>
        <tbody data-coverage-gap-rows></tbody>
      </table>
    </div>
    <div class="coverage-gap-pagination">
      <button class="text-button" type="button" data-coverage-prev disabled>← Previous</button>
      <span data-coverage-page>Page 1</span>
      <button class="text-button" type="button" data-coverage-next disabled>Next →</button>
    </div>
  </section>

  <div class="compat-load-state" data-coverage-load role="status">Loading InferenceX registry…</div>
  <div class="compat-empty-state" data-coverage-error hidden></div>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">INTERPRETATION</p><h2>Coverage is not comparability.</h2></div>
  <p>A field being populated does not prove that it is accurate, normalized consistently or sufficiently specific. Distinct-value counts do not imply balanced samples. Missing-field counts can overlap because one record may have several gaps. Strict analysis still requires exact workload and execution-context matching; this page does not certify candidate comparisons or infer missing metadata. The denominator is the InferenceX subset currently stored in this registry, not all results published by InferenceX.</p>
</section>

<link rel="stylesheet" href="{{ '/assets/css/inferencex-coverage.css' | relative_url }}">
<script src="{{ '/assets/js/inferencex-coverage.js' | relative_url }}" defer></script>
