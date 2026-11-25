---
layout: default
title: InferenceX Concurrency Explorer
permalink: /concurrency/
description: Explore published matching-context concurrency observations.
---
<section class="page-heading">
  <p class="eyebrow">BENCHMARK INTELLIGENCE · SERVING</p>
  <h1>InferenceX Concurrency Explorer</h1>
  <p>Inspect published throughput and latency observations as concurrency changes. Each series holds recorded hardware, workload, software recipe and execution configuration fixed. Unreported variables may still differ.</p>
  <div class="page-meta"><a href="{{ '/results/' | relative_url }}">Benchmark Results ↗</a><a href="https://github.com/basicmi/AI-Chip/blob/master/docs/inferencex-concurrency-sweeps.md">Methodology ↗</a></div>
</section>
<section data-sweep-explorer data-source="{{ '/data/benchmark-results.json.gz' | relative_url }}">
  <div class="compat-filter-panel">
    <h2>Choose an observed series</h2>
    <p>Load the public registry and reconstruct the matching-context series locally. No benchmarks are executed.</p>
    <button class="text-button" type="button" data-sweep-load>Load published observations</button>
    <p data-sweep-status role="status" aria-live="polite">Registry not loaded.</p>
    <div class="benchmark-results-filters">
      <label>Metric<select data-sweep-metric disabled></select></label>
      <label>Hardware<select data-sweep-hardware disabled></select></label>
      <label>Model<select data-sweep-model disabled></select></label>
      <label>Matching context<select data-sweep-context disabled></select></label>
    </div>
  </div>
  <section class="compat-filter-panel">
    <h2>Observed concurrency response</h2>
    <p data-sweep-description>Choose a series to inspect individual observations and repeated-value ranges.</p>
    <div data-sweep-chart style="overflow-x:auto"></div>
    <p>Dots: published values. Vertical bars: observed min–max, not confidence intervals. Diamonds: median of published values, not pooled request percentiles. No interpolated points or saturation claims.</p>
    <details><summary>Exact recorded context</summary><pre data-sweep-details style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></details>
    <div style="overflow-x:auto"><table><thead><tr><th>Concurrency</th><th>Count</th><th>Min</th><th>Median</th><th>Max</th></tr></thead><tbody data-sweep-table></tbody></table></div>
    <details><summary>Individual source records</summary><div data-sweep-records></div></details>
  </section>
</section>
<script src="{{ '/assets/js/concurrency-explorer.js' | relative_url }}" defer></script>
