---
layout: default
title: Cross-benchmark Evidence
permalink: /cross-benchmark/
description: Review candidate semantic mappings between normalized metrics from different benchmark suites without comparing unlike scores.
---

<section class="page-heading">
  <p class="eyebrow">PERFORMANCE INTELLIGENCE · CROSS-BENCHMARK EVIDENCE</p>
  <h1>Cross-benchmark Evidence</h1>
  <p>Discover where different benchmark suites publish metrics that may describe related system behavior. This is a metric-definition crosswalk for human review—not a score conversion, benchmark equivalence claim or cross-suite leaderboard.</p>
  <div class="page-meta">
    <a href="{{ '/performance/' | relative_url }}">Performance Workspace ↗</a>
    <a href="{{ '/results/' | relative_url }}">Benchmark Results ↗</a>
    <a href="{{ '/recipe-review/' | relative_url }}">Recipe Evidence Review ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/cross-benchmark-evidence.md">Methodology ↗</a>
  </div>
</section>

<section class="cross-benchmark" data-cross-benchmark data-source="{{ '/data/benchmark-results.json.gz' | relative_url }}">
  <div class="cb-summary">
    <div><span>Benchmark suites</span><strong data-cb-stat="suites">—</strong></div>
    <div><span>Normalized metric definitions</span><strong data-cb-stat="definitions">—</strong></div>
    <div><span>Cross-suite mapping candidates</span><strong data-cb-stat="candidates">—</strong></div>
    <div><span>Source-linked observations</span><strong data-cb-stat="observations">—</strong></div>
  </div>
  <section class="cb-panel">
    <div class="cb-heading"><div><p class="eyebrow">STEP 01 · DISCOVER</p><h2>Metric mapping candidates</h2></div></div>
    <p>Candidate links are derived from the registry's normalized metric metadata. The same unit and family do not prove the same measurement boundary, aggregation window, workload or benchmark intent.</p>
    <div class="cb-filters">
      <label>Relationship<select data-cb-relation><option value="">All candidate relationships</option><option value="same_signature">Same normalized signature</option><option value="same_dimension">Same family, unit and direction</option><option value="unit_review">Same family and direction; unit differs</option></select></label>
      <label>Metric family<select data-cb-family><option value="">All families</option></select></label>
      <label>Search<input type="search" data-cb-search placeholder="Suite, metric key, label, source…"></label>
    </div>
    <p class="cb-status" data-cb-status role="status">Loading benchmark registry…</p>
    <div class="cb-candidates" data-cb-candidates></div>
    <p class="cb-empty" data-cb-empty hidden>No cross-suite metric mapping candidates match these filters.</p>
  </section>
  <section class="cb-panel">
    <div class="cb-heading"><div><p class="eyebrow">STEP 02 · INSPECT DEFINITIONS</p><h2>What the registry actually records</h2></div></div>
    <p>Choose a suite/metric definition to inspect the raw normalized metadata and representative source-linked observations. Raw score values are intentionally omitted from this cross-suite view.</p>
    <div class="cb-inspector" data-cb-inspector><p>Select a candidate above to inspect its definitions.</p></div>
  </section>
  <div class="compat-load-state" data-cb-load role="status">Loading benchmark registry…</div>
  <div class="compat-empty-state" data-cb-error hidden></div>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">INTERPRETATION</p><h2>Related metrics are not interchangeable benchmarks.</h2></div>
  <p>This page links metric definitions for review only. It does not convert units, normalize scores, equate workload protocols, infer accuracy equivalence, compare accelerator performance across suites, or create a combined ranking. Even an exact normalized key/unit/family/direction match is only a candidate: inspect the original metric definition, measurement boundary, statistic (mean/median/percentile), time window, workload, accuracy target and source evidence before deciding whether a mapping is valid. Missing or ambiguous metadata stays unknown.</p>
</section>
<link rel="stylesheet" href="{{ '/assets/css/cross-benchmark.css' | relative_url }}">
<script src="{{ '/assets/js/cross-benchmark.js' | relative_url }}" defer></script>
