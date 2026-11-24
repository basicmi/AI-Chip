---
layout: default
title: Database Integration Workbench
permalink: /database-integration/
description: Local-only review of provenance-bound database integration proposals.
---

<section class="page-heading">
  <p class="eyebrow">INTELLIGENCE · PROVENANCE · DATABASE GOVERNANCE</p>
  <h1>Database Integration Workbench</h1>
  <p>Inspect a generated integration package before it is committed or submitted for a pull request. The workbench verifies the package checksum, exact base registry, target Claim and the two permitted append-only changes. All files stay in this browser.</p>
  <div class="page-meta">
    <span>Mode <strong>local-only review</strong></span>
    <a href="{{ '/evidence-review/' | relative_url }}">Evidence Review Workbench ↗</a>
    <a href="{{ '/product-integration/' | relative_url }}">New Product Integration Workbench ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/database-integration-workbench.md" target="_blank" rel="noopener noreferrer">Methodology ↗</a>
  </div>
</section>

<section class="evidence-workbench" data-database-integration>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">01 / LOAD</p><h2>Open a proposal package</h2></div>
      <button class="text-button" type="button" data-di-clear>Clear files</button>
    </div>
    <p>Generate the package with <code>scripts/build_database_integration_proposal.py</code> using a reviewed Approval Manifest, its matching Claim extraction report, and the current <code>data/company-profiles.json</code>. The package is a proposal, not a database update.</p>
    <div class="workload-filters">
      <label>Integration proposal JSON
        <input type="file" accept=".json,application/json" data-di-package>
      </label>
      <label>Original Claim extraction JSON (same discovery run)
        <input type="file" accept=".json,application/json" data-di-claims>
      </label>
      <label>Exact base company-profiles.json (same revision)
        <input type="file" accept=".json,application/json" data-di-registry>
      </label>
    </div>
    <p class="compat-load-state" data-di-status role="status" aria-live="polite">Choose a proposal package, its original Claim report and exact base registry.</p>
  </section>

  <section class="compat-filter-panel" data-di-results hidden>
    <div class="compat-filter-heading">
      <div><p class="eyebrow">02 / PROVENANCE CHAIN</p><h2>Source → Claim → Database</h2></div>
      <span class="status-pill">Human review required</span>
    </div>
    <div class="di-chain">
      <article><p class="eyebrow">SOURCE OBSERVATION</p><h3 data-di-source-title>—</h3><p data-di-source-quote></p><a data-di-source-link target="_blank" rel="noopener noreferrer">Open source ↗</a><p class="di-meta" data-di-source-meta></p></article>
      <div class="di-chain-arrow" aria-hidden="true">→</div>
      <article><p class="eyebrow">EXTRACTED CLAIM</p><h3 data-di-extracted-id>—</h3><p data-di-extracted-statement></p><span class="status-pill">Unverified candidate</span></article>
      <div class="di-chain-arrow" aria-hidden="true">→</div>
      <article><p class="eyebrow">EXISTING DATABASE CLAIM</p><h3 data-di-target-name>—</h3><p data-di-target-claim></p><p class="di-meta" data-di-target-meta></p></article>
    </div>
  </section>

  <div class="workload-stat-grid" data-di-results hidden>
    <div class="compat-stat"><span>Base registry SHA256</span><strong class="di-hash" data-di-base-hash>—</strong></div>
    <div class="compat-stat"><span>Proposal package SHA256</span><strong class="di-hash" data-di-package-hash>—</strong></div>
    <div class="compat-stat"><span>Proposed registry SHA256</span><strong class="di-hash" data-di-proposed-hash>—</strong></div>
    <div class="compat-stat"><span>Permitted field changes</span><strong data-di-change-count>—</strong></div>
  </div>

  <section class="compat-filter-panel" data-di-results hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">03 / FIELD-LEVEL DIFF</p><h2>Exact permitted changes</h2></div></div>
    <div class="ops-table-scroll"><table class="ops-table">
      <thead><tr><th>Database path</th><th>Before</th><th>After</th></tr></thead>
      <tbody data-di-diff></tbody>
    </table></div>
    <details class="di-patch"><summary>Inspect JSON Patch operations</summary><pre data-di-operations></pre></details>
  </section>

  <section class="compat-filter-panel" data-di-results hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">04 / AUDIT</p><h2>Verification and policy gates</h2></div></div>
    <div class="di-checks" data-di-checks></div>
    <p class="compat-limitations">This validates provenance linkage and the allowed shape of the proposed change. It does not prove the source statement is true, independently verify a benchmark, or upgrade the formal Claim status.</p>
    <div class="di-downloads">
      <button type="button" class="text-button" data-di-download="patch">Download JSON Patch</button>
      <button type="button" class="text-button" data-di-download="audit">Download audit JSON</button>
      <button type="button" class="text-button" data-di-download="database">Download proposed registry JSON</button>
    </div>
  </section>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">05 / GOVERNED INTEGRATION</p><h2>Proposal first. Pull request second. Merge only after human review.</h2></div>
  <ol>
    <li>Generate a package locally from the current registry, the exact Claim report and the human-reviewed Approval Manifest.</li>
    <li>Review the provenance chain, field-level diff, base hash and audit gates above.</li>
    <li>Commit the package under <code>reviews/integration-proposals/</code>, the original Approval Manifest under <code>reviews/approvals/</code>, and the matching Claim report under <code>reviews/claims/</code>.</li>
    <li>Manually dispatch the <a href="https://github.com/basicmi/AI-Chip/actions/workflows/integrate-database-proposal.yml" target="_blank" rel="noopener noreferrer">Integrate reviewed database proposal workflow</a> on master with all three committed paths.</li>
    <li>Inspect the generated PR and CI. Merge only after normal human review.</li>
  </ol>
  <p>The workflow replays the package against the current master registry. Any stale base, changed Claim, altered operation or unapproved field change fails closed.</p>
</section>

<link rel="stylesheet" href="{{ '/assets/css/database-integration.css' | relative_url }}">
<script src="{{ '/assets/js/database-integration.js' | relative_url }}" defer></script>
