---
layout: default
title: Recipe Evidence Review
permalink: /recipe-review/
description: Inspect source-linked InferenceX parallelism observations whose recipe fingerprints differ or are missing before drawing comparisons.
---

<section class="page-heading">
  <p class="eyebrow">PERFORMANCE INTELLIGENCE · EVIDENCE REVIEW</p>
  <h1>Recipe Evidence Review</h1>
  <p>Inspect parallelism observations that share the recorded context except for one TP/EP axis, but have different or missing recipe fingerprints. This is a review queue—not an equivalence decision or performance ranking.</p>
  <div class="page-meta">
    <a href="{{ '/performance/' | relative_url }}">Performance Workspace ↗</a>
    <a href="{{ '/results/' | relative_url }}">Benchmark Results ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/inferencex-parallelism-sensitivity.md">Analysis methodology ↗</a>
  </div>
</section>

<section class="recipe-review" data-recipe-review data-source="{{ '/data/benchmark-results.json.gz' | relative_url }}">
  <div class="rr-summary">
    <div><span>Candidate groups</span><strong data-rr-stat="groups">—</strong></div>
    <div><span>Source observations</span><strong data-rr-stat="observations">—</strong></div>
    <div><span>Groups with missing fingerprints</span><strong data-rr-stat="missing">—</strong></div>
    <div><span>Groups with differing fingerprints</span><strong data-rr-stat="different">—</strong></div>
  </div>
  <section class="rr-panel">
    <div class="rr-heading"><div><p class="eyebrow">REVIEW QUEUE</p><h2>Find candidate groups</h2></div></div>
    <div class="rr-filters">
      <label>Parallelism axis<select data-rr-axis><option value="">All axes</option><option value="prefill_tp">Prefill TP</option><option value="prefill_ep">Prefill EP</option><option value="decode_tp">Decode TP</option><option value="decode_ep">Decode EP</option></select></label>
      <label>Metric<select data-rr-metric><option value="">All metrics</option></select></label>
      <label>Search<input type="search" data-rr-search placeholder="Model, hardware, fingerprint, record ID…"></label>
    </div>
    <p class="rr-status" data-rr-status role="status" aria-live="polite">Loading registry…</p>
    <div class="rr-groups" data-rr-groups></div>
    <p class="rr-empty" data-rr-empty hidden>No review candidates match these filters. This does not mean all possible configurations are equivalent.</p>
  </section>
  <div class="compat-load-state" data-rr-load role="status">Loading InferenceX registry…</div>
  <div class="compat-empty-state" data-rr-error hidden></div>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">REVIEW PROTOCOL</p><h2>Different fingerprints are evidence, not proof of different recipes.</h2></div>
  <p>Groups are formed only when the recorded benchmark/workload protocol, hardware identity, system boundary, software metadata excluding the fingerprint, and other stable configuration fields match. Exactly one positive integer TP/EP degree varies. Different or missing fingerprints trigger manual review. A matching fingerprint is not proof that the recipe is identical; a different fingerprint is not proof that the recipe is materially different. Review source material and the full recipe before any equivalence policy change. This page does not persist approvals, merge fingerprints, aggregate candidate metrics or change the registry.</p>
</section>
<link rel="stylesheet" href="{{ '/assets/css/recipe-review.css' | relative_url }}">
<script src="{{ '/assets/js/recipe-review.js' | relative_url }}" defer></script>
