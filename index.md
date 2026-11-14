---
layout: default
title: AI Chip Landscape
permalink: /
description: An evidence-led map of AI accelerator hardware, software ecosystems, compatibility and benchmarks.
---

<section class="home-hero">
  <div class="home-hero-copy">
    <p class="eyebrow">AI COMPUTING · HARDWARE · SOFTWARE · SYSTEMS</p>
    <h1>Navigate the<br><span>AI accelerator</span> landscape.</h1>
    <p class="home-hero-lede">A curated, evidence-led map of the chips, software stacks and benchmarks shaping modern AI infrastructure — from silicon and IP to kernels, runtimes and serving systems.</p>
    <div class="home-actions">
      <a class="button button-primary" href="{{ '/products/' | relative_url }}">Compare products <span aria-hidden="true">↗</span></a>
      <a class="button button-secondary" href="{{ '/directory/' | relative_url }}">Explore hardware</a>
      <a class="button button-secondary" href="{{ '/compatibility/' | relative_url }}">Open compatibility explorer</a>
    </div>
    <div class="home-metrics" aria-label="Current database coverage" data-home-stats data-compat-source="{{ '/data/compatibility.json' | relative_url }}" data-workload-source="{{ '/data/workloads.json' | relative_url }}" data-benchmark-source="{{ '/data/benchmark-projects.json' | relative_url }}">
      <div><strong data-home-stat="platforms">11</strong><span>accelerator platforms</span></div>
      <div><strong data-home-stat="integrations">18</strong><span>software integrations</span></div>
      <div><strong data-home-stat="workloads">10</strong><span>workload definitions</span></div>
      <div><strong data-home-stat="benchmarks">26</strong><span>public benchmark resources</span></div>
    </div>
  </div>
  <div class="home-hero-visual">
    <div class="hero-visual-frame">
      <a class="landscape-full-link" href="{{ '/resource/AI_Chip_Landscape_v0p9p1.svg' | relative_url }}" target="_blank" rel="noopener noreferrer" aria-label="Open the full-size AI Chip Landscape">
        <img src="{{ '/resource/AI_Chip_Landscape_v0p9p1.svg' | relative_url }}" alt="AI Chip Landscape, version 0.9.1. A map of global AI accelerator companies, software ecosystems and benchmarks." loading="lazy">
      </a>
    </div>
    <p class="visual-caption"><span class="status-dot"></span> Landscape snapshot · November 2026 · 48 company logos · Open full-size ↗</p>
  </div>
</section>

<section class="home-section">
  <div class="section-heading">
    <div>
      <p class="eyebrow">EXPLORE THE ECOSYSTEM</p>
      <h2>Five views. One connected landscape.</h2>
    </div>
    <p>Move from a vendor or chip to its software support, then compare the benchmarks that matter.</p>
  </div>
  <div class="feature-grid">
    <a class="feature-card" href="{{ '/directory/' | relative_url }}">
      <span class="feature-number">01 / HARDWARE</span>
      <span class="feature-icon" aria-hidden="true">◈</span>
      <h3>Chip &amp; IP directory</h3>
      <p>Explore GPUs, NPUs, custom AI silicon, edge accelerators and semiconductor IP vendors.</p>
      <span class="feature-link">Browse the directory <span aria-hidden="true">→</span></span>
    </a>
    <a class="feature-card" href="{{ '/software-ecosystem/' | relative_url }}">
      <span class="feature-number">02 / SOFTWARE</span>
      <span class="feature-icon" aria-hidden="true">⌘</span>
      <h3>Software ecosystem</h3>
      <p>Map compilers, IRs, kernel DSLs, operator libraries, runtimes, communication and serving engines.</p>
      <span class="feature-link">Explore software layers <span aria-hidden="true">→</span></span>
    </a>
    <a class="feature-card feature-card-highlight" href="{{ '/compatibility/' | relative_url }}">
      <span class="feature-number">03 / COMPATIBILITY</span>
      <span class="feature-icon" aria-hidden="true">⌗</span>
      <h3>Compatibility explorer</h3>
      <p>Search hardware-to-software integration records, version pins, support status and primary evidence.</p>
      <span class="feature-link">Query compatibility <span aria-hidden="true">→</span></span>
    </a>
    <a class="feature-card feature-card-highlight" href="{{ '/workloads/' | relative_url }}">
      <span class="feature-number">04 / WORKLOADS</span>
      <span class="feature-icon" aria-hidden="true">⌁</span>
      <h3>Workload explorer</h3>
      <p>Connect model families and workload phases to candidate hardware/software paths, with evidence maturity made explicit.</p>
      <span class="feature-link">Explore execution paths <span aria-hidden="true">→</span></span>
    </a>
    <a class="feature-card feature-card-highlight" href="{{ '/model-support/' | relative_url }}">
      <span class="feature-number">05 / MODEL SUPPORT</span>
      <span class="feature-icon" aria-hidden="true">◈</span>
      <h3>Model support explorer</h3>
      <p>Trace exact model checkpoints to accelerator products, serving stacks, precision modes and source-backed deployment recipes.</p>
      <span class="feature-link">Explore model support <span aria-hidden="true">→</span></span>
    </a>
    <a class="feature-card" href="{{ '/benchmarks/' | relative_url }}">
      <span class="feature-number">06 / BENCHMARKS</span>
      <span class="feature-icon" aria-hidden="true">▥</span>
      <h3>Benchmark landscape</h3>
      <p>Understand model, serving, kernel, memory, interconnect, power and cost benchmarks.</p>
      <span class="feature-link">Explore benchmarks <span aria-hidden="true">→</span></span>
    </a>
    <a class="feature-card" href="{{ '/evidence-review/' | relative_url }}">
      <span class="feature-number">07 / INTELLIGENCE</span>
      <span class="feature-icon" aria-hidden="true">◇</span>
      <h3>Evidence Review Workbench</h3>
      <p>Explore unverified intelligence claim candidates, source provenance, duplicates and reviewer-scoped conflicts from local Actions artifacts.</p>
      <span class="feature-link">Open review workbench <span aria-hidden="true">→</span></span>
    </a>
    <a class="feature-card" href="{{ '/intelligence-operations/' | relative_url }}">
      <span class="feature-number">08 / OPERATIONS</span>
      <span class="feature-icon" aria-hidden="true">▤</span>
      <h3>Intelligence Operations</h3>
      <p>Compare actual weekly source health, unresolved review backlog and cache recovery from local operational snapshots.</p>
      <span class="feature-link">Open operations dashboard <span aria-hidden="true">→</span></span>
    </a>
  </div>
</section>

<section class="home-bottom-grid"
  <div class="home-note-card">
    <p class="eyebrow">EDITORIAL PRINCIPLES</p>
    <h2>Evidence before rankings.</h2>
    <p>Compatibility and performance are workload-, device- and version-specific. We distinguish upstream support, vendor plugins, experimental branches and vendor-reported results rather than collapsing them into a single score.</p>
    <a href="{{ '/compatibility/' | relative_url }}">See how support is classified <span aria-hidden="true">→</span></a>
  </div>
  <div class="home-note-card home-note-card-muted">
    <p class="eyebrow">PROJECT &amp; CONTRIBUTIONS</p>
    <h2>A living technical reference.</h2>
    <p>Primary sources are preferred. Version snapshots are dated, compatibility claims carry evidence links, and unresolved documentation conflicts remain visible for review.</p>
    <a href="https://github.com/basicmi/AI-Chip" target="_blank" rel="noopener noreferrer">View the project on GitHub <span aria-hidden="true">↗</span></a>
  </div>
</section>
