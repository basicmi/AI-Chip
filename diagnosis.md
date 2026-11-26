---
layout: default
title: Performance Diagnosis Workbench
permalink: /diagnosis/
description: Inspect benchmark runtime signals, profiler evidence and missing measurements without automatic bottleneck attribution.
---

<section class="page-heading">
  <p class="eyebrow">PERFORMANCE INTELLIGENCE · EVIDENCE DIAGNOSIS</p>
  <h1>Performance Diagnosis Workbench</h1>
  <p>Move from observed serving behavior to the evidence needed to investigate compute, memory, communication, KV cache, throttling and runtime scheduling. The workbench distinguishes recorded signals from hypotheses and does not automatically declare a bottleneck.</p>
  <div class="page-meta">
    <a href="{{ '/performance/' | relative_url }}">Performance Workspace ↗</a>
    <a href="{{ '/results/' | relative_url }}">Benchmark Results ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/scripts/diagnose_hardware_performance.py">Diagnosis engine ↗</a>
    <a href="https://github.com/basicmi/AI-Chip/blob/master/docs/hardware-performance-diagnosis.md">Evidence contract ↗</a>
  </div>
</section>

<section class="diagnosis-workbench" data-diagnosis-workbench data-source="{{ '/data/benchmark-results.json.gz' | relative_url }}">
  <section class="dw-overview">
    <div><span>Published records</span><strong data-dw-stat="records">—</strong></div>
    <div><span>Records with profiler evidence</span><strong data-dw-stat="hardware">—</strong></div>
    <div><span>Records with runtime traces</span><strong data-dw-stat="traces">—</strong></div>
    <div><span>Records with serving metrics</span><strong data-dw-stat="serving">—</strong></div>
  </section>
  <section class="dw-panel">
    <p class="eyebrow">STEP 01 · SELECT AN OBSERVATION</p>
    <h2>Choose a published benchmark record</h2>
    <div class="dw-selectors">
      <label>Search model, hardware or record ID<input type="search" data-dw-search placeholder="e.g. H200, DeepSeek, record ID"></label>
      <label>Record<select data-dw-record><option value="">Select a record…</option></select></label>
    </div>
    <p class="dw-status" data-dw-status role="status">Loading benchmark registry…</p>
    <div class="dw-record" data-dw-record-summary></div>
  </section>
  <section class="dw-panel">
    <p class="eyebrow">STEP 02 · OBSERVED SERVING BEHAVIOR</p>
    <h2>Runtime signals</h2>
    <p>These are publisher-normalized benchmark metrics. They describe observed behavior but do not isolate the underlying cause.</p>
    <div class="dw-runtime" data-dw-runtime><p>Select a record to inspect its serving metrics.</p></div>
  </section>
  <section class="dw-panel">
    <p class="eyebrow">STEP 03 · HARDWARE AND TRACE EVIDENCE</p>
    <h2>Profiler evidence coverage</h2>
    <p>Evidence is grouped by the measurements needed to test a mechanism. Availability alone does not prove matching scope, precision, directionality, time window or critical-path relevance; the diagnosis engine validates those constraints before calculating derived quantities.</p>
    <div class="dw-evidence-grid" data-dw-evidence></div>
    <div class="dw-provenance" data-dw-provenance></div>
  </section>
  <section class="dw-panel">
    <p class="eyebrow">STEP 04 · INVESTIGATION PLAN</p>
    <h2>Candidate mechanisms and next measurements</h2>
    <p>Candidate mechanisms are not diagnoses. Missing evidence remains unknown, not zero. A performance symptom must not be assigned to a mechanism without the corresponding counter or trace.</p>
    <div class="dw-mechanisms" data-dw-mechanisms><p>Select a record to build its evidence checklist.</p></div>
  </section>
  <div class="compat-load-state" data-dw-load role="status">Loading published benchmark registry…</div>
  <div class="compat-empty-state" data-dw-error hidden></div>
</section>

<section class="compat-method-note">
  <div><p class="eyebrow">INTERPRETATION BOUNDARY</p><h2>Observation is not attribution.</h2></div>
  <p>High GPU utilization is not proof of compute saturation; DRAM activity is not proof of bandwidth saturation; link traffic is not proof of communication being on the critical path; KV-cache occupancy is not proof of eviction or preemption; TTFT/TPOT and throughput do not isolate queueing or scheduler delay. Profiler and serving records may come from different captures. Temporal alignment must be demonstrated, not assumed. This page is a review interface over published registry evidence and does not execute benchmarks or collect new telemetry.</p>
</section>
<link rel="stylesheet" href="{{ '/assets/css/performance-diagnosis.css' | relative_url }}">
<script src="{{ '/assets/js/performance-diagnosis.js' | relative_url }}" defer></script>
