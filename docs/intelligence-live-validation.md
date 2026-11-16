# Live Intelligence Source Validation

## Why this run exists

The discovery workflow has three entry points:

- Weekly scheduled run: Monday at 06:15 UTC.
- Manual run: `workflow_dispatch`, with a 45-day default lookback.
- Relevant master-branch changes: a push to `master` that changes the
  discovery workflow, source registry, model catalog, review ledger, claim
  schema, or an intelligence pipeline script.

The push trigger is deliberately path-filtered. Changes to the website,
benchmark results, company/product data or unrelated documentation do not
cause external source polling. The workflow is read-only with respect to
formal registries. It restores and checkpoints only its GitHub Actions cache
state after a successful end-to-end audit, and uploads a 30-day artifact.

## Current source inventory

The curated registry version `2026.11.16-2` has 24 active sources:

| Source kind | Count | Collection method |
|---|---:|---|
| GitHub Releases | 15 | Up to 3 pages × 50 releases per repository |
| RSS / Atom | 8 | One feed document per publisher |
| arXiv API | 1 | Up to 3 pages × 100 entries, with 3-second spacing |

The Hugging Face model-catalog audit is an additional, separate check:
13 curated model repositories plus recent publisher listings for six
organizations. Do not add these checks to the 24-source denominator.

## First-run review checklist

Treat the first real run as a baseline, not a quality ranking.

1. **Availability:** distinguish observed, recovered and unavailable. Read
   failure category, failure tier, consecutive-failure count and retry count.
2. **Freshness:** inspect newest publication age, invalid/missing dates and
   empty-but-successful feeds. Empty does not mean failed or inactive.
3. **Completeness:** flag saturated pagination windows. Three full pages are
   evidence of a possible truncation boundary, not proof of missing items.
4. **Cost and performance:** compare request count, failed attempts, average
   and maximum latency, response bytes and slow-request sources. Counts
   include retries and pagination.
5. **Relevance:** inspect topic-tag distribution and manually sample titles
   and excerpts. Keyword tags are a routing aid, not a semantic relevance
   score.
6. **Deduplication:** review cross-source shared URL groups. The same URL
   observed in two feeds is not independent corroboration.
7. **Claim quality:** sample extracted claims for quote fidelity, atomicity,
   scope (chip/package/board/rack/datacenter), units, lifecycle qualifiers
   and evidence-source independence. The extractor is a deterministic
   heuristic, not a factual verifier.
8. **Model-catalog boundary:** separate repository presence and SHA changes
   from runtime support, hardware compatibility or model quality.

## First live baseline — 2026-11-16

Run: [GitHub Actions #43787532670](https://github.com/basicmi/AI-Chip/actions/runs/43787532670)

- Discovery completed successfully; end-to-end audit allowed the cache
  checkpoint. Both cache files were absent at run start, so this is the
  first-seen baseline, not a continuity measurement.
- 23/24 sources were observed (95.8%); 1 source, `arxiv-ai-systems`,
  timed out on all 3 attempts. It accounted for 3 failed requests.
- 47 HTTP requests were made in total, 3 failed; successful response payloads
  totalled 19,304,125 bytes. One source had an individual request over 5 s.
- Four sources were empty but reachable: `deepseek-deepep`,
  `mlcommons-inference`, `nvidia-newsroom-ai-platforms` and
  `rocm-composable-kernel`. These are not outages.
- Seven GitHub release sources reached the 3-page / 60-item cap:
  `aws-neuron-sdk`, `flashinfer`, `nvidia-cutlass`,
  `nvidia-tensorrt-llm`, `pytorch`, `sglang` and `vllm`.
  This is a possible completeness warning, not proof of missing releases.
- Discovery produced 393 observations: 47 project releases, 34 technical
  articles, 136 vendor announcements and 176 model-repository records.
  The 176 model records included 13 curated repositories and 163 unreviewed
  publisher-listing candidates. The first scan did not request expanded
  Hugging Face fields, so most listing candidates lacked creation date, SHA
  and task metadata; PR #109 corrects this and applies the 45-day lookback.
- Claim extraction emitted 421 candidates. All had low extraction confidence;
  199 were classified as `other`. Five exact-text duplicate clusters
  collapsed six claims; no claim was independently verified. This is a
  clear signal-quality limitation and is the next separate improvement area.

This single scan is an operational baseline only. It is not a source-quality
ranking or factual validation of any product, model, benchmark or capability.


## Second live run after PR #109 — 2026-11-16

Run: [GitHub Actions #43789263891](https://github.com/basicmi/AI-Chip/actions/runs/43789263891)

- 24/24 configured sources were observed; 36 HTTP requests completed with
  zero failed requests. The arXiv source recovered and returned 300 recent
  preprint records across three pages.
- Discovery produced 539 observations and 323 review leads: 300 new arXiv
  preprints and 23 Hugging Face publisher-listing updates/candidates.
- The previous Claim Extractor reached its 1,000-Claim hard cap. All 1,000
  Claims came from arXiv; 458 (45.8%) were tagged `other`, and 893 (89.3%)
  were typed as the generic `research_finding`. This exposed both broad
  research-feed noise and first-source truncation bias.
- Triage produced 870 groups from those 1,000 Claims; the displayed queue
  remained limited to 100 groups while persistent review state tracked 1,421
  backlog Claims.
- These counts are an operational and extraction baseline, not evidence that
  all 300 papers are relevant or that any extracted statement is true.
  PR #110 introduces a relevance gate, richer routing labels and fair
  source/candidate caps; compare the next run against this baseline.


## First post-PR-110 live run — 2026-11-16

Run: [GitHub Actions #43795362021](https://github.com/basicmi/AI-Chip/actions/runs/43795362021)

- All 24/24 configured sources were observed; 36 requests completed with
  zero failures and 23,391,069 response bytes.
- Persistent change detection found 47 new review leads out of 539 cumulative
  observations. All 47 were arXiv preprints; this was a delta run, not a
  reprocessing of all historical observations.
- Version 2 extracted 92 Claim candidates and the triage stage produced 84
  groups (8 duplicate Claims collapsed). All 92 remained unverified research
  preprint candidates.
- Manual sampling found remaining false positives from broad compiler/kernel
  terms, incidental GPU mentions in application papers, and sentences that
  inherited candidate relevance without carrying their own technical signal.
  PR #111 tightens the arXiv query and sentence-level gate; it adds regression
  cases drawn from these observed examples.
- The 1,513-item persistent review backlog includes 1,421 Claims from earlier
  runs not observed in this delta. It is not a count of newly extracted Claims.

This run was operationally healthy, but the source-query and relevance
precision still need improvement. Do not treat 92/47 as a precision score.

## First live run after PR #112 — 2026-11-16

Run: [GitHub Actions #43798131776](https://github.com/basicmi/AI-Chip/actions/runs/43798131776)

- Discovery observed 23/24 configured sources (95.8%). The unavailable source
  was `google-deepmind-blog`, which returned a ParseError. The overall run
  completed its audit and checkpoint, but the operational health was marked
  degraded.
- 36 HTTP requests completed with zero failed requests; successful response
  payloads totalled 23,377,007 bytes. One source had a request slower than 5 s;
  four sources were empty but reachable.
- Change detection reported 521 cumulative observations: 300 arXiv preprints
  and 219 new review leads, with 302 unchanged observations. This is a delta
  run, not a fresh 521-item discovery.
- Claim extraction emitted 422 unverified candidates from 152 of the 219
  new leads. The other 67 candidates yielded no Claims: 56 were classified
  out of scope and 11 had no excerpt sentence passing the sentence gate.
  Relevance labels were 108 direct AI-compute and 55 adjacent AI-system
  candidates. All 422 Claims were arXiv preprints; none were independently
  verified.
- Triage grouped the 422 Claims into 385 groups, with 22 exact-text duplicate
  groups collapsing 37 rows. The persistent review backlog was 1,935 Claims,
  all pending; 1,513 were not observed in this delta run.
- Manual sampling still found generic GPU/HPC false positives (for example,
  multi-GPU tridiagonal CUDA linear algebra, GPU nonlinear-program solving,
  and generic GPU numerical-bug research), plus relevant MoE serving and
  on-device RL runtime papers that the sentence gate did not fully capture.
  PR #113 introduces the v4 contextual anchors and a human-curated evaluation
  set to make these misses and false positives measurable.

The run was operationally healthy enough to checkpoint state, but source
coverage was degraded by one parser error. The 422 Claim count is not a
precision score and is not evidence that all 219 new leads are relevant.

## When to score source quality

Do not assign a composite score from one scan. Keep the following dimensions
separate until there are at least eight weekly observations:

- **Reliability:** successful scheduled observations / expected observations,
  with manual reruns distinguished from scheduled runs.
- **Freshness:** publication-age distribution, not just the newest item.
- **Relevance:** a human-reviewed sample of useful items / sampled items.
- **Incremental value:** new or meaningfully updated items, not raw feed volume.
- **Evidence utility:** proportion of sampled candidates that yield a
  well-scoped, source-faithful claim or useful independent corroboration.

An empty source can be healthy; a high-volume source can be noisy; a vendor
announcement and an independent paper are different evidence classes. Avoid
a single ranking until these dimensions have enough observations and a
documented weighting policy.

## Artifacts

Each successful run uploads `ai-chip-intelligence-discovery`, including:

- `ai-chip-intelligence-discovery.json`
- `ai-chip-intelligence-source-coverage.json/.md`
- `ai-chip-intelligence-claims.json/.md`
- `ai-chip-intelligence-evidence-graph.json`
- `ai-chip-intelligence-triage.json/.md`
- `ai-chip-intelligence-review-state.json`
- `ai-chip-intelligence-health.json/.md`
- `ai-chip-intelligence-operations.json`

The Operations Dashboard can compare explicitly selected
`ai-chip-intelligence-operations.json` files. It does not fetch live
Actions data and cannot infer missing runs.

## Safety boundary

All outputs are investigation leads. A successful HTTP response, a release
tag, a model repository, or a high topic match does not establish a product
announcement, production availability, benchmark result, accelerator
compatibility or technical claim. Formal registries remain unchanged until
a human verifies original sources and approves a narrowly scoped data PR.

## First live run after PR #114 — 2026-11-16

Run: [GitHub Actions #43815816745](https://github.com/basicmi/AI-Chip/actions/runs/43815816745)

- 23/24 configured sources were observed (95.8%). All 15/15 GitHub Release
  sources were reachable after authenticated API discovery was enabled.
- Google DeepMind's official RSS feed recovered and yielded 18 recent items.
  This confirms the earlier parser failure was transient; the configured
  endpoint and existing RSS/Atom parser worked on this run.
- The single unavailable source was the broad arXiv query. All three attempts
  timed out at approximately 20 seconds each. The source made zero successful
  requests and was unavailable after 60.2 seconds of request time.
- Discovery recorded 239 observations, all unchanged; there were zero new or
  updated candidates and therefore zero new Claim Candidates. This is a
  delta-run result, not evidence that the sources contain no new publications.
- The run made 36 requests, 3 failed, and received 22,647,817 bytes. Four
  sources were reachable but empty. The overall pipeline completed its audit
  and checkpoint, with operational health marked degraded due to arXiv.

PR #115 splits the arXiv search into four independently monitored, bounded
queries. The next scheduled run should be used to assess whether this reduces
timeouts without creating unacceptable pagination truncation or relevance
noise.

## First live run after PR #115 — 2026-11-16

Run: [GitHub Actions #43819178894](https://github.com/basicmi/AI-Chip/actions/runs/43819178894)

- Discovery itself completed and recorded 621 observations, including 212
  new or updated review leads.
- All four arXiv shards returned their full two-page allowance: 100 raw
  records per shard, 400 raw arXiv records in total. Each shard correctly
  set `paging_cap_reached=true`; these are explicit possible-truncation
  signals, not evidence of exhaustive coverage.
- 26/27 sources were observed. The Google DeepMind RSS source returned a
  parse error on this run; its 33,960-byte response was received successfully
  over HTTP, so this is a parser/payload issue rather than a transport failure.
  The run does not retain the raw response, so the exact malformed XML
  construct is not established.
- The Source Coverage Audit rejected the four arXiv records because it still
  hard-coded a three-page maximum after PR #115 changed the configured shard
  bound to two. Claim extraction and downstream stages were skipped, and the
  transactional cache checkpoint did not run.
- PR #116 updates the audit to validate the actual registry page bound and
  adds regression tests for both matching and mismatched two-page metadata.

The 212 new/updated count is a Discovery delta result. It must not be read as
212 independently verified claims or as a relevance/recall score.

## First successful full run after PR #116 — 2026-11-16

Run: [GitHub Actions #43820741766](https://github.com/basicmi/AI-Chip/actions/runs/43820741766).

- 27/27 sources observed; zero failed HTTP requests across 41 requests.
  Previously broken Source Coverage Audit passed, and the entire pipeline
  through Claim extraction, triage, review-state and health audit completed.
- The four arXiv shards each returned 100 raw records (two 50-record pages).
  All four hit their page caps; this flags possible retrieval truncation.
  There were 381 distinct arXiv paper IDs in those 400 source observations.
- 639 total observations, including 212 new/updated review leads, produced
  581 **unverified** Claim candidates. The persistent review backlog reached
  2,516; none of these figures establishes factual verification.
- A comparison with the 16 manually labelled relevant papers used for PR #117
  found 8/16 present by per-shard depth 25, 9/16 by depth 50 and 9/16
  by depth 100. Seven known relevant papers were not observed in the capped
  four-shard result. This is a biased known-item calibration, not a production
  estimate of corpus recall.

PR #117 makes this calculation reproducible and adds it to the weekly
artifacts. Missing papers should be reviewed to determine whether query
taxonomy, arXiv categories or the page cap is responsible, rather than
immediately broadening all OR terms.

## First automated miss diagnosis after PR #117 — 2026-11-16

Run: [GitHub Actions #43837297395](https://github.com/basicmi/AI-Chip/actions/runs/43837297395)

- 27/27 sources observed; all four arXiv shards returned 100 raw records and
  reached their two-page caps.
- The 16-paper known-item seed scored 8/16 at per-shard depth 25 and 9/16 at
  depth 50 and 100. Seven papers remained absent.
- PR #118 adds a category-aware lexical diagnostic over those seven misses.
  It preserves explicit uncertainty where category metadata is not captured
  or comes from a secondary index, and distinguishes a configured phrase
  visible in the abstract from a phrase gap.
- Candidate query terms are evidence-grounded suggestions, not automatic
  query edits. The next stage will trial a small, isolated query expansion
  and compare incremental recall, source volume, page-cap behavior and
  relevance precision before adopting it.
