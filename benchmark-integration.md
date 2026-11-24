---
layout: default
title: Benchmark Integration Workbench
permalink: /benchmark-integration/
description: Local-only review of provenance-bound benchmark result proposals.
---

<section class="page-heading">
  <p class="eyebrow">BENCHMARK INTELLIGENCE · PROVENANCE · DATABASE GOVERNANCE</p>
  <h1>Benchmark Integration Workbench</h1>
  <p>Review one proposed benchmark result against its original human Approval Manifest and exact base registry. The workbench reconstructs the append-only change, checks source identity and hashes, and displays the system/workload context before a proposal is submitted. Files stay in this browser.</p>
  <div class="page-meta">
    <span>Mode <strong>local-only review</strong></span>
    <a href="{{ '/results/' | relative_url }}">Benchmark Results ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/benchmark-result-creation-adapter.md" target="_blank" rel="noopener noreferrer">Methodology ↗</a>
  </div>
</section>

<section class="evidence-workbench" data-benchmark-integration>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">01 / LOAD</p><h2>Open a benchmark result proposal</h2></div>
      <button class="text-button" type="button" data-bi-clear>Clear files</button>
    </div>
    <p>Generate the package with <code>scripts/build_benchmark_result_proposal.py</code>. Select the generated proposal, the separate Approval Manifest, and the exact <code>data/benchmark-results.json</code> revision used to build it.</p>
    <div class="workload-filters">
      <label>Benchmark proposal JSON
        <input type="file" accept=".json,application/json" data-bi-package>
      </label>
      <label>Original Benchmark Result Approval Manifest JSON
        <input type="file" accept=".json,application/json" data-bi-approval>
      </label>
      <label>Exact base benchmark-results.json
        <input type="file" accept=".json,application/json" data-bi-registry>
      </label>
    </div>
    <p class="compat-load-state" data-bi-status role="status" aria-live="polite">Choose all three files to verify the benchmark result provenance chain.</p>
  </section>

  <section class="compat-filter-panel" data-bi-results hidden>
    <div class="compat-filter-heading">
      <div><p class="eyebrow">02 / PROVENANCE CHAIN</p><h2>Registered Source → New Result</h2></div>
      <span class="status-pill">Human review required</span>
    </div>
    <div class="di-chain di-chain-two">
      <article>
        <p class="eyebrow">EXISTING SOURCE</p>
        <h3 data-bi-source-name>—</h3>
        <p data-bi-source-publisher></p>
        <a data-bi-source-link target="_blank" rel="noopener noreferrer">Open registered source ↗</a>
        <p class="di-meta" data-bi-source-meta></p>
      </article>
      <div class="di-chain-arrow" aria-hidden="true">→</div>
      <article>
        <p class="eyebrow">PROPOSED RESULT</p>
        <h3 data-bi-record-name>—</h3>
        <p data-bi-record-summary></p>
        <span class="status-pill" data-bi-evidence-level>—</span>
        <p class="di-meta" data-bi-record-meta></p>
      </article>
    </div>
  </section>

  <div class="workload-stat-grid" data-bi-results hidden>
    <div class="compat-stat"><span>Base registry SHA256</span><strong class="di-hash" data-bi-base-hash>—</strong></div>
    <div class="compat-stat"><span>Proposal package SHA256</span><strong class="di-hash" data-bi-package-hash>—</strong></div>
    <div class="compat-stat"><span>Proposed registry SHA256</span><strong class="di-hash" data-bi-proposed-hash>—</strong></div>
    <div class="compat-stat"><span>Permitted operations</span><strong>5</strong></div>
  </div>

  <section class="compat-filter-panel" data-bi-results hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">03 / SYSTEM & WORKLOAD</p><h2>Comparison context</h2></div></div>
    <div class="benchmark-results-summary">
      <div class="compat-stat"><span>Benchmark / version</span><strong data-bi-suite>—</strong></div>
      <div class="compat-stat"><span>Model / scenario</span><strong data-bi-model>—</strong></div>
      <div class="compat-stat"><span>System boundary</span><strong data-bi-system>—</strong></div>
      <div class="compat-stat"><span>Result</span><strong data-bi-value>—</strong></div>
    </div>
    <div class="ops-table-scroll"><table class="ops-table">
      <thead><tr><th>Context field</th><th>Reviewed value</th></tr></thead>
      <tbody data-bi-context></tbody>
    </table></div>
    <p class="compat-limitations">A result is not directly comparable merely because its metric name matches another row. Inspect benchmark version, model/checkpoint, scenario, precision, workload shape, system boundary, software stack, division and availability. Missing context stays missing; no cross-suite score is inferred.</p>
  </section>

  <section class="compat-filter-panel" data-bi-results hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">04 / FIELD-LEVEL DIFF</p><h2>Exact permitted changes</h2></div></div>
    <div class="ops-table-scroll"><table class="ops-table">
      <thead><tr><th>Database path</th><th>Operation</th><th>Value</th></tr></thead>
      <tbody data-bi-diff></tbody>
    </table></div>
    <details class="di-patch"><summary>Inspect JSON Patch operations</summary><pre data-bi-operations></pre></details>
  </section>

  <section class="compat-filter-panel" data-bi-results hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">05 / AUDIT</p><h2>Verification and policy gates</h2></div></div>
    <div class="di-checks" data-bi-checks></div>
    <p class="compat-limitations">A passing browser review establishes package integrity and the shape of the proposed change, not source truth or measurement validity. The authoritative gate is the Python adapter plus the full benchmark registry validator in CI. Human approval is not independent verification. No automatic merge is permitted.</p>
    <div class="di-downloads">
      <button type="button" class="text-button" data-bi-download="patch">Download JSON Patch</button>
      <button type="button" class="text-button" data-bi-download="audit">Download audit JSON</button>
      <button type="button" class="text-button" data-bi-download="database">Download proposed registry JSON</button>
    </div>
  </section>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">06 / GOVERNED INTEGRATION</p><h2>One source. One reviewed result. One auditable append.</h2></div>
  <ol>
    <li>Confirm that the benchmark source is already registered and inspect the original result publication.</li>
    <li>Prepare a separate Approval Manifest with the complete system, workload, software, precision, result and source-record context.</li>
    <li>Build the proposal locally and inspect the provenance chain, context fields, hashes and exact five-operation patch above.</li>
    <li>Commit the proposal under <code>reviews/benchmark-proposals/</code> and its Approval Manifest under <code>reviews/approvals/</code>.</li>
    <li>Manually dispatch the integration workflow after it is available; inspect the generated PR and CI. Merge only after normal human review.</li>
  </ol>
  <p>This adapter v1 only adds one result for an existing source. It does not create source definitions, change existing records, infer missing data, upgrade evidence class, or accept power/hardware-counter/runtime-trace claims.</p>
</section>

<link rel="stylesheet" href="{{ '/assets/css/database-integration.css' | relative_url }}">
<script src="{{ '/assets/js/benchmark-integration.js' | relative_url }}" defer></script>
