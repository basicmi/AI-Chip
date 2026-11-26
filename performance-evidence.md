---
layout: default
title: Performance Evidence Workbench
permalink: /performance-evidence/
description: Inspect linked benchmark records, experiment plans, external runs, review packets and human decisions locally.
---
<link rel="stylesheet" href="{{ '/assets/css/performance-evidence-workbench.css' | relative_url }}">

<section class="page-heading">
  <p class="eyebrow">PERFORMANCE INTELLIGENCE · EVIDENCE LINEAGE</p>
  <h1>Performance Evidence Workbench</h1>
  <p>Inspect one complete performance evidence chain: source benchmark, falsifiable experiment plan, externally supplied run observations, generated review packet and human decision history. All files are read locally in this browser. Nothing is uploaded, executed or automatically approved.</p>
  <div class="page-meta">
    <a href="{{ '/diagnosis/' | relative_url }}">Performance Diagnosis ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/performance-experiment-planner.md" target="_blank" rel="noopener noreferrer">Experiment planner guide ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/performance-evidence-chain.md" target="_blank" rel="noopener noreferrer">Evidence review guide ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/performance-review-ledger.md" target="_blank" rel="noopener noreferrer">Decision ledger guide ↗</a>
  </div>
</section>

<section class="performance-evidence" data-performance-evidence>
  <section class="pe-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">01 / LOAD LOCAL FILES</p><h2>Open one evidence chain</h2></div>
      <button class="pe-reset" type="button" data-pe-reset>Clear files</button>
    </div>
    <p>Choose files belonging to the same experiment. The record, plan, submission and review report are required. Load the current decision ledger to inspect prior human decisions; download its initial empty version from <a href="https://raw.githubusercontent.com/basicmi/AI-Chip/master/data/performance-review-ledger.json" target="_blank" rel="noopener noreferrer">master ↗</a>.</p>
    <div class="pe-files">
      <label>Benchmark record JSON (required)<input type="file" accept=".json,application/json" data-pe-record></label>
      <label>Experiment plan JSON (required)<input type="file" accept=".json,application/json" data-pe-plan></label>
      <label>External run submission JSON (required)<input type="file" accept=".json,application/json" data-pe-submission></label>
      <label>Generated review packet JSON (required)<input type="file" accept=".json,application/json" data-pe-review></label>
      <label>Current human decision ledger JSON (optional)<input type="file" accept=".json,application/json" data-pe-ledger></label>
    </div>
    <p class="pe-status" data-pe-status role="status" aria-live="polite">Choose the evidence files to begin.</p>
  </section>

  <div data-pe-content hidden>
    <section class="pe-stats" aria-label="Evidence chain summary">
      <div><span>Benchmark records</span><strong data-pe-stat="records">—</strong></div>
      <div><span>Planned experiments</span><strong data-pe-stat="experiments">—</strong></div>
      <div><span>Submitted runs</span><strong data-pe-stat="runs">—</strong></div>
      <div><span>Review blockers</span><strong data-pe-stat="blockers">—</strong></div>
    </section>
    <section class="pe-panel">
      <p class="eyebrow">02 / LINEAGE</p><h2>Evidence identity</h2>
      <div data-pe-summary></div>
      <p class="pe-hash-note" data-pe-hash-note></p>
    </section>
    <div class="pe-grid">
      <section class="pe-panel"><p class="eyebrow">03 / EXPERIMENT</p><h2>Hypothesis and protocol</h2><div data-pe-experiment-detail></div></section>
      <section class="pe-panel"><p class="eyebrow">04 / REVIEW GATE</p><h2>Blockers and limitations</h2><ul data-pe-blockers></ul><p>Hypothesis conclusions remain undetermined until a human reviewer evaluates the original sources, physical controls and mechanism-specific measurements.</p></section>
    </div>
    <section class="pe-panel">
      <p class="eyebrow">05 / OBSERVED RESULTS</p><h2>Baseline versus treatment</h2>
      <div class="pe-stats" data-pe-metric-stats></div>
      <p>Relative improvement: <strong data-pe-improvement>—</strong> · Practical threshold: <strong data-pe-threshold>—</strong></p>
      <p class="pe-callout">These are descriptive summaries from submitted runs. They are not statistical significance, proof of causality or independent verification of the source data.</p>
      <div class="pe-table-wrap"><table class="pe-table" data-pe-run-table><thead><tr><th>Run</th><th>Condition</th><th>Status</th><th>Value</th><th>Source</th><th>Reason</th></tr></thead><tbody></tbody></table></div>
    </section>
    <section class="pe-panel">
      <p class="eyebrow">06 / HUMAN DECISIONS</p><h2>Decision history for this exact evidence version</h2>
      <p>Ledger entries are filtered by record, plan, experiment and submission digest. The visible chain links are structurally checked; cryptographic verification remains with the Python ledger validator.</p>
      <p>Ledger entries loaded: <strong data-pe-ledger-count>Not loaded</strong></p>
      <div class="pe-decision-list" data-pe-decision-list></div>
    </section>
  </div>
  <section class="pe-panel">
    <p class="eyebrow">INTERPRETATION BOUNDARIES</p>
    <h2>What this workbench does not claim</h2>
    <ul>
      <li>It does not independently fetch or verify external source URLs.</li>
      <li>It does not cryptographically recompute Python SHA-256 digests in the browser.</li>
      <li>It does not prove that declared controls were physically maintained or that all runs were submitted.</li>
      <li>It does not approve hypotheses, execute hardware experiments or modify the production ledger.</li>
    </ul>
    <p>For authoritative structural, digest and hash-chain validation, use <code>scripts/review_performance_experiment_evidence.py</code> and <code>scripts/append_performance_review_decision.py</code> in a reviewed repository workflow.</p>
  </section>
</section>
<script src="{{ '/assets/js/performance-evidence-workbench.js' | relative_url }}" defer></script>
