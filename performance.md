---
layout: default
title: Performance Intelligence Workspace
permalink: /performance/
description: A unified evidence-first workspace for filtering published InferenceX observations and launching configuration-aware AI system performance analysis.
---

<section class="page-heading">
  <p class="eyebrow">PERFORMANCE INTELLIGENCE · WORKSPACE</p>
  <h1>Performance Intelligence Workspace</h1>
  <p>Start with a published model and system configuration, inspect the evidence available in the registry, then open the appropriate analysis. This workspace does not run benchmarks or rank unlike systems.</p>
  <div class="page-meta">
    <span>Registry <strong data-pw-version>Loading…</strong></span>
    <span>Imported <strong data-pw-imported>—</strong></span>
    <a href="{{ '/results/' | relative_url }}">Full benchmark registry ↗</a>
    <a href="{{ '/coverage/' | relative_url }}">Evidence coverage ↗</a>
  </div>
</section>

<section class="performance-workspace" data-performance-workspace data-source="{{ '/data/benchmark-results.json.gz' | relative_url }}">
  <section class="pw-overview">
    <div class="pw-stat"><span>Published InferenceX records</span><strong data-pw-stat="records">—</strong></div>
    <div class="pw-stat"><span>Models represented</span><strong data-pw-stat="models">—</strong></div>
    <div class="pw-stat"><span>Hardware labels</span><strong data-pw-stat="hardware">—</strong></div>
    <div class="pw-stat"><span>Records with normalized metrics</span><strong data-pw-stat="metrics">—</strong></div>
  </section>

  <section class="pw-panel" aria-labelledby="pw-filter-title">
    <div class="pw-panel-heading">
      <div><p class="eyebrow">STEP 01 · DEFINE THE OBSERVED CONTEXT</p><h2 id="pw-filter-title">Choose a workload and system</h2></div>
      <button type="button" class="text-button" data-pw-reset>Reset filters</button>
    </div>
    <p>Filters narrow published records only. Empty or unknown fields remain unknown; the workspace never fills them with assumed defaults.</p>
    <div class="pw-filters">
      <label>Model<select data-pw-filter="model"><option value="">All models</option></select></label>
      <label>Accelerator / hardware<select data-pw-filter="hardware"><option value="">All hardware</option></select></label>
      <label>Framework<select data-pw-filter="framework"><option value="">All frameworks</option></select></label>
      <label>Workload type<select data-pw-filter="benchmark_type"><option value="">All workload types</option></select></label>
      <label>Precision<select data-pw-filter="precision"><option value="">All precisions</option></select></label>
      <label>Serving mode<select data-pw-filter="serving"><option value="">Aggregated / disaggregated</option></select></label>
    </div>
    <div class="pw-filter-status" data-pw-filter-status role="status" aria-live="polite">Loading registry…</div>
  </section>

  <section class="pw-panel" aria-labelledby="pw-evidence-title">
    <div class="pw-panel-heading"><div><p class="eyebrow">STEP 02 · CHECK THE EVIDENCE</p><h2 id="pw-evidence-title">What can this selection tell us?</h2></div></div>
    <div class="pw-evidence-grid" data-pw-evidence></div>
    <p class="pw-caveat">These are coverage counts inside the current filter, not proof that records form a strict comparison cohort. For strict cohort membership, inspect the comparability rules and the source/configuration details on the Results page.</p>
  </section>

  <section class="pw-panel" aria-labelledby="pw-metric-title">
    <div class="pw-panel-heading">
      <div><p class="eyebrow">STEP 03 · INSPECT REPORTED METRICS</p><h2 id="pw-metric-title">Published metric observations</h2></div>
      <label class="pw-metric-select">Metric<select data-pw-metric></select></label>
    </div>
    <p class="pw-caveat">Values are shown as publisher observations, not as a cross-system leaderboard. Different records may have different run contexts, measurement boundaries and repetitions.</p>
    <div class="pw-metric-summary" data-pw-metric-summary></div>
    <div class="pw-observations-wrap">
      <table class="pw-observations">
        <thead><tr><th>Record</th><th>Model</th><th>Hardware</th><th>Workload</th><th>Value</th><th>Source</th></tr></thead>
        <tbody data-pw-observations></tbody>
      </table>
    </div>
    <p class="pw-empty" data-pw-empty hidden>No records report this metric within the selected filters.</p>
  </section>

  <section class="pw-panel" aria-labelledby="pw-analysis-title">
    <div class="pw-panel-heading"><div><p class="eyebrow">STEP 04 · OPEN A DEEPER ANALYSIS</p><h2 id="pw-analysis-title">Analysis tools</h2></div></div>
    <div class="pw-tools">
      <a class="pw-tool" href="{{ '/results/' | relative_url }}#benchmark-scaling-title"><span class="pw-tool-kicker">SCALING</span><strong>Observed throughput scaling</strong><span>GPU-count scaling within an active strict workload cohort.</span><b>Open Results ↗</b></a>
      <a class="pw-tool" href="{{ '/results/' | relative_url }}#benchmark-frontier-title"><span class="pw-tool-kicker">TRADE-OFFS</span><strong>Latency–throughput Pareto frontier</strong><span>Inspect the observed TTFT, TPOT and throughput frontier.</span><b>Open Results ↗</b></a>
      <a class="pw-tool" href="{{ '/concurrency/' | relative_url }}"><span class="pw-tool-kicker">SERVING</span><strong>Concurrency response</strong><span>Inspect matching-context concurrency observations.</span><b>Open explorer ↗</b></a>
      <a class="pw-tool" href="{{ '/performance-evidence/' | relative_url }}"><span class="pw-tool-kicker">EVIDENCE CHAIN</span><strong>Performance Evidence Workbench</strong><span>Inspect benchmark lineage, external runs, review packets and human decision history.</span><b>Open workbench ↗</b></a>
      <a class="pw-tool" href="{{ '/diagnosis/' | relative_url }}"><span class="pw-tool-kicker">DIAGNOSIS</span><strong>Evidence-based performance diagnosis</strong><span>Inspect serving signals, profiler counters, runtime traces and missing measurements.</span><b>Open workbench ↗</b></a>
      <a class="pw-tool" href="{{ '/coverage/' | relative_url }}"><span class="pw-tool-kicker">DATA QUALITY</span><strong>Coverage & missing evidence</strong><span>Find which fields and metrics are actually present.</span><b>Open explorer ↗</b></a>
      <a class="pw-tool" href="{{ '/results/' | relative_url }}#benchmark-energy-title"><span class="pw-tool-kicker">ENERGY</span><strong>GPU energy efficiency</strong><span>Inspect publisher-validated GPU power and energy records.</span><b>Open Results ↗</b></a>
      <a class="pw-tool" href="{{ '/results/' | relative_url }}#benchmark-runtime-alignment-title"><span class="pw-tool-kicker">RUNTIME × HARDWARE</span><strong>Runtime phase alignment</strong><span>Review timestamp and trace evidence readiness.</span><b>Open Results ↗</b></a>
    </div>
  </section>

  <div class="compat-load-state" data-pw-load role="status">Loading published benchmark registry…</div>
  <div class="compat-empty-state" data-pw-error hidden></div>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">METHOD</p><h2>Evidence first, interpretation second.</h2></div>
  <p>The workspace filters records from the local published registry. It does not execute experiments, infer missing configuration, estimate unreported metrics or establish causality. A matching model and workload label alone are insufficient for comparison. Check the source, benchmark version, workload shape, hardware/system boundary, software recipe, stable configuration, evidence class and metric definition before interpreting differences.</p>
</section>
<link rel="stylesheet" href="{{ '/assets/css/performance-workspace.css' | relative_url }}">
<script src="{{ '/assets/js/performance-workspace.js' | relative_url }}" defer></script>
