---
layout: default
title: Product Integration Workbench
permalink: /product-integration/
description: Local-only review of provenance-bound new-product proposals.
---

<section class="page-heading">
  <p class="eyebrow">INTELLIGENCE · PRODUCT IDENTITY · DATABASE GOVERNANCE</p>
  <h1>Product Integration Workbench</h1>
  <p>Review a proposed new product, its initial identity Claim and source Evidence as one atomic change. The workbench checks the original Claim report, human Approval Manifest, exact base registry and three permitted append operations. Files stay in this browser.</p>
  <div class="page-meta">
    <span>Mode <strong>local-only review</strong></span>
    <a href="{{ '/database-integration/' | relative_url }}">Evidence Attachment Workbench ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/product-integration-workbench.md" target="_blank" rel="noopener noreferrer">Methodology ↗</a>
  </div>
</section>

<section class="evidence-workbench" data-product-integration>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">01 / LOAD</p><h2>Open a product proposal package</h2></div>
      <button class="text-button" type="button" data-pi-clear>Clear files</button>
    </div>
    <p>Generate the package with <code>scripts/build_product_creation_proposal.py</code> from the exact registry, original Claim extraction report and a human-reviewed Product Creation Approval Manifest.</p>
    <div class="workload-filters">
      <label>Product proposal JSON
        <input type="file" accept=".json,application/json" data-pi-package>
      </label>
      <label>Original Claim extraction JSON
        <input type="file" accept=".json,application/json" data-pi-claims>
      </label>
      <label>Product Creation Approval Manifest JSON
        <input type="file" accept=".json,application/json" data-pi-approval>
      </label>
      <label>Exact base company-profiles.json
        <input type="file" accept=".json,application/json" data-pi-registry>
      </label>
    </div>
    <p class="compat-load-state" data-pi-status role="status" aria-live="polite">Choose all four files to verify a complete product provenance chain.</p>
  </section>

  <section class="compat-filter-panel" data-pi-results hidden>
    <div class="compat-filter-heading">
      <div><p class="eyebrow">02 / PROVENANCE CHAIN</p><h2>Source → Product → Initial Claim</h2></div>
      <span class="status-pill">Human review required</span>
    </div>
    <div class="di-chain">
      <article><p class="eyebrow">ORIGINAL SOURCE</p><h3 data-pi-source-title>—</h3><p data-pi-source-quote></p><a data-pi-source-link target="_blank" rel="noopener noreferrer">Open source ↗</a><p class="di-meta" data-pi-source-meta></p></article>
      <div class="di-chain-arrow" aria-hidden="true">→</div>
      <article><p class="eyebrow">NEW PRODUCT</p><h3 data-pi-product-name>—</h3><p data-pi-product-meta></p><p class="di-meta" data-pi-company></p></article>
      <div class="di-chain-arrow" aria-hidden="true">→</div>
      <article><p class="eyebrow">INITIAL PRODUCT CLAIM</p><h3 data-pi-claim-id>—</h3><p data-pi-claim-statement></p><span class="status-pill">vendor_reported</span></article>
    </div>
  </section>

  <div class="workload-stat-grid" data-pi-results hidden>
    <div class="compat-stat"><span>Base registry SHA256</span><strong class="di-hash" data-pi-base-hash>—</strong></div>
    <div class="compat-stat"><span>Proposal package SHA256</span><strong class="di-hash" data-pi-package-hash>—</strong></div>
    <div class="compat-stat"><span>Proposed registry SHA256</span><strong class="di-hash" data-pi-proposed-hash>—</strong></div>
    <div class="compat-stat"><span>Permitted record appends</span><strong>3</strong></div>
  </div>

  <section class="compat-filter-panel" data-pi-results hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">03 / FIELD-LEVEL DIFF</p><h2>Exact permitted changes</h2></div></div>
    <div class="ops-table-scroll"><table class="ops-table">
      <thead><tr><th>Database path</th><th>Operation</th><th>Record</th></tr></thead>
      <tbody data-pi-diff></tbody>
    </table></div>
    <details class="di-patch"><summary>Inspect JSON Patch operations</summary><pre data-pi-operations></pre></details>
  </section>

  <section class="compat-filter-panel" data-pi-results hidden>
    <div class="compat-filter-heading"><div><p class="eyebrow">04 / AUDIT</p><h2>Verification and policy gates</h2></div></div>
    <div class="di-checks" data-pi-checks></div>
    <p class="compat-limitations">A passing package proves that the proposed database change is reproducible and constrained to three typed appends. It does not prove the source statement is true, independently validate product specifications, or establish measured performance. The initial Claim remains vendor_reported.</p>
    <div class="di-downloads">
      <button type="button" class="text-button" data-pi-download="patch">Download JSON Patch</button>
      <button type="button" class="text-button" data-pi-download="audit">Download audit JSON</button>
      <button type="button" class="text-button" data-pi-download="database">Download proposed registry JSON</button>
    </div>
  </section>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">05 / GOVERNED INTEGRATION</p><h2>One product. One identity Claim. One reviewed source.</h2></div>
  <ol>
    <li>Review the original source and prepare a Product Creation Approval Manifest.</li>
    <li>Generate the proposal package locally; inspect the Source → Product → Claim chain and exact three-record diff.</li>
    <li>Commit the proposal under <code>reviews/product-proposals/</code>, the Approval Manifest under <code>reviews/approvals/</code>, and the matching Claim report under <code>reviews/claims/</code>.</li>
    <li>Manually dispatch the <a href="https://github.com/basicmi/AI-Chip/actions/workflows/integrate-product-proposal.yml" target="_blank" rel="noopener noreferrer">Integrate reviewed new product proposal workflow</a> on master with all three paths.</li>
    <li>Inspect the generated PR and CI. Merge only after normal human review.</li>
  </ol>
  <p>This first product adapter deliberately excludes numeric performance Claims, compatibility links and benchmark results. It creates only a vendor_reported product-identity Claim; those other record types require separate adapters and evidence rules.</p>
</section>

<link rel="stylesheet" href="{{ '/assets/css/database-integration.css' | relative_url }}">
<script src="{{ '/assets/js/product-integration.js' | relative_url }}" defer></script>
