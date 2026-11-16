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

The curated registry version `2026.11.13-2` has 24 active sources:

| Source kind | Count | Collection method |
|---|---:|---|
| GitHub Releases | 15 | Up to 3 pages × 20 releases per repository |
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
