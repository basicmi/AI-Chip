---
layout: default
title: Evidence Review Workbench
permalink: /evidence-review/
description: Local-only review of unverified intelligence claim and evidence graph artifacts.
---

<section class="page-heading">
  <p class="eyebrow">INTELLIGENCE · EVIDENCE · HUMAN REVIEW</p>
  <h1>Evidence Review Workbench</h1>
  <p>Review unverified technical claims, original sources, duplicate wording and reviewer-scoped comparison flags. Files are read locally in your browser; nothing is uploaded or approved.</p>
  <div class="page-meta">
    <span>Data <strong>local GitHub Actions artifacts</strong></span>
    <a href="https://github.com/basicmi/AI-Chip/actions/workflows/model-catalog-audit.yml" target="_blank" rel="noopener noreferrer">Download weekly discovery artifact ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/evidence-review-workbench.md">Review methodology ↗</a>
  </div>
</section>

<section class="evidence-workbench" data-evidence-workbench>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">01 / LOAD</p><h2>Open a review artifact</h2></div>
      <button class="text-button" type="button" data-ew-reset>Clear files</button>
    </div>
    <p>Download the ai-chip-intelligence-discovery artifact. Choose its Claim JSON and optional Evidence Graph JSON from the <strong>same run</strong>. The workbench does not fetch data automatically.</p>
    <div class="workload-filters">
      <label>Claim extraction JSON (required)
        <input type="file" accept=".json,application/json" data-ew-claims>
      </label>
      <label>Evidence graph JSON (optional)
        <input type="file" accept=".json,application/json" data-ew-graph>
      </label>
      <label>Priority triage JSON (optional, same run)
        <input type="file" accept=".json,application/json" data-ew-triage>
      </label>
    </div>
    <p class="compat-load-state" data-ew-status role="status" aria-live="polite">Choose a Claim JSON file to begin.</p>
    <p class="compat-limitations" data-ew-provenance hidden></p>
  </section>
  <div class="workload-stat-grid">
    <div class="compat-stat"><span>Unverified claims</span><strong data-ew-stat="claims">—</strong></div>
    <div class="compat-stat"><span>Source documents</span><strong data-ew-stat="sources">—</strong></div>
    <div class="compat-stat"><span>Exact-text duplicate clusters</span><strong data-ew-stat="duplicates">—</strong></div>
    <div class="compat-stat"><span>Possible specification conflicts</span><strong data-ew-stat="conflicts">—</strong></div>
  </div>
  <section class="compat-filter-panel">
    <div class="compat-filter-heading">
      <div><p class="eyebrow">02 / TRIAGE</p><h2>Filter unverified claims</h2></div>
      <button class="text-button" type="button" data-ew-clear-filters>Reset filters</button>
    </div>
    <div class="workload-filters">
      <label>Search claim or source
        <input type="search" data-ew-search placeholder="GPU, HBM, publisher…" autocomplete="off" disabled>
      </label>
      <label>Topic
        <select data-ew-topic disabled><option value="">All topics</option></select>
      </label>
      <label>Publisher
        <select data-ew-publisher disabled><option value="">All publishers</option></select>
      </label>
      <label>Relationship
        <select data-ew-relationship disabled>
          <option value="">All candidate claims</option>
          <option value="duplicates">Exact-text duplicate</option>
          <option value="conflicts">Possible specification conflict</option>
          <option value="comparisons">Reviewer-scoped comparison</option>
          <option value="standalone">No flagged relationship</option>
        </select>
      </label>
    </div>
  </section>
  <div class="workload-results-heading">
    <div><p class="eyebrow">03 / REVIEW QUEUE</p><h2><span data-ew-result-count>0</span> candidates</h2></div>
    <p data-ew-summary>No review candidates loaded.</p>
  </div>
  <div class="model-support-grid" data-ew-results></div>
  <div class="compat-empty-state" data-ew-empty><strong>No claim candidates loaded</strong><p>Load a Claim JSON artifact to inspect unverified source-backed observations.</p></div>

  <section class="compat-filter-panel" data-ew-decision-panel>
    <div class="compat-filter-heading">
      <div><p class="eyebrow">04 / HUMAN DECISION</p><h2>Review selected Claim</h2></div>
      <span class="status-pill">Local draft only</span>
    </div>
    <p data-ew-selected>No Claim selected. Use “Review this claim” in a card above.</p>
    <div class="workload-filters">
      <label>Decision (local)
        <select data-ew-decision disabled>
          <option value="">Choose review outcome</option>
          <option value="needs_more_evidence">Needs more evidence</option>
          <option value="rejected">Reject / not suitable</option>
          <option value="accepted_for_evidence_attachment">Accept for evidence attachment review</option>
        </select>
      </label>
      <label>Review note
        <textarea data-ew-decision-note rows="3" placeholder="Explain why and what was checked…" disabled></textarea>
      </label>
    </div>
    <p data-ew-decision-status role="status">No review decision recorded. Decisions remain in this browser session.</p>
    <button class="text-button" type="button" data-ew-export-decisions disabled>Download local decision log</button>
  </section>

  <section class="compat-filter-panel" data-ew-approval-panel>
    <div class="compat-filter-heading">
      <div><p class="eyebrow">05 / EVIDENCE ATTACHMENT</p><h2>Prepare a gated Approval Manifest</h2></div>
      <span class="status-pill">Requires explicit human review</span>
    </div>
    <p>The existing Evidence-to-PR workflow only supports attaching one reviewed source to one <strong>existing</strong> company Claim. Load the current local company profile registry, select the exact target, and verify the source before generating a manifest. No claim value or status is changed.</p>
    <label class="ew-block-label">Company profiles JSON (local, current master)
      <input type="file" data-ew-profiles accept=".json,application/json">
    </label>
    <div class="workload-filters">
      <label>Existing company
        <select data-ew-company disabled><option value="">Select company</option></select>
      </label>
      <label>Existing Claim (same company)
        <select data-ew-existing disabled><option value="">Select existing Claim</option></select>
      </label>
      <label>Approval ID
        <input data-ew-approval-id type="text" placeholder="review-unique-source-2026" autocomplete="off">
      </label>
      <label>New evidence ID
        <input data-ew-evidence-id type="text" placeholder="vendor-product-spec-2026">
      </label>
      <label>Reviewer (real identity)
        <input data-ew-reviewer type="text" placeholder="Maintainer handle">
      </label>
      <label>Review date
        <input data-ew-reviewed type="date">
      </label>
      <label>Evidence title (verified from original page)
        <input data-ew-title type="text" placeholder="Official datasheet / announcement">
      </label>
      <label>Evidence publisher
        <input data-ew-publisher-input type="text" placeholder="Publisher of the primary source">
      </label>
      <label>Source type
        <select data-ew-source-type>
          <option value="vendor_primary">Vendor primary</option>
          <option value="company_primary">Company primary</option>
          <option value="official_project">Official project</option>
          <option value="research_paper">Research paper</option>
          <option value="independent_media">Independent media</option>
          <option value="government_or_regulatory">Government / regulatory</option>
          <option value="repository">Repository</option>
          <option value="other">Other</option>
        </select>
      </label>
      <label>Source independence category (not verification)
        <select data-ew-independence>
          <option value="vendor">Vendor-reported</option>
          <option value="project">Project-reported</option>
          <option value="independent">Independent origin reported</option>
          <option value="official">Official source</option>
        </select>
      </label>
      <label>Publication date (leave blank if unknown)
        <input data-ew-published type="date">
      </label>
      <label>Evidence checked date
        <input data-ew-checked type="date">
      </label>
    </div>
    <label class="ew-block-label">Evidence notes
      <textarea data-ew-evidence-notes rows="3" placeholder="Describe what is explicitly supported, and its limits"></textarea>
    </label>
    <label class="ew-block-label">Review rationale (minimum 30 characters)
      <textarea data-ew-review-notes rows="4" placeholder="Explain source review, target identity, exact technical scope and remaining uncertainty"></textarea>
    </label>
    <label class="ew-confirm"><input type="checkbox" data-ew-confirm> I personally inspected the original source and the selected existing database Claim; this is an evidence attachment, not an independent verification or a change to numeric specifications.</label>
    <p class="compat-load-state" data-ew-approval-status role="status" aria-live="polite">Select a Claim and accept it for evidence attachment review before exporting.</p>
    <button type="button" data-ew-export-manifest disabled>Download human-reviewed Approval Manifest (JSON)</button>
    <p>Next, commit this manifest under <code>reviews/approvals/</code> and its matching original Claim extraction report under <code>reviews/claims/</code>, then manually dispatch the <a href="https://github.com/basicmi/AI-Chip/actions/workflows/propose-reviewed-evidence.yml" target="_blank" rel="noopener noreferrer">gated Evidence-to-PR workflow</a> on master. This page does not submit anything.</p>
  </section>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">EVIDENCE POLICY</p><h2>Duplicates and conflicts are leads, not verification.</h2></div>
  <p>Identical wording may be syndicated from one origin. A numerical disagreement is not a proven contradiction. Only reviewer-scoped groups can flag possible conflicts. Review decisions and export drafts stay local; human approval manifests require explicit confirmation and still go through the separate manual Evidence-to-PR gate. This page never changes official claim statuses or registries.</p>
</section>
<link rel="stylesheet" href="{{ '/assets/css/evidence-review.css' | relative_url }}">
<script src="{{ '/assets/js/evidence-review-workbench.js' | relative_url }}" defer></script>
<script src="{{ '/assets/js/evidence-review-decisions.js' | relative_url }}" defer></script>
