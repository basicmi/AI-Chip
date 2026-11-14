# GitHub Releases Bounded Pagination & Coverage Integrity (PR #104)

## Background
A registry of 24 curated Intelligence sources is available, but as checked
on 2026-11-14 there was **no actual Weekly AI Chip intelligence discovery
run in the most recent 100 GitHub Actions records**. No claim is made that
all configured feeds are healthy. PR #103 added the metadata audit that
must run after an actual network-backed discovery.

A concrete coverage defect existed: each GitHub Releases source requested
only \`per_page=20\` and filtered by publication date **after** fetching
that first page. For busy projects this may miss releases still inside
the 45-day lookback window.

## Fix

- Scan at most **3 pages × 20 GitHub Releases** per repository, stopping on
  a short page. Each page remains subject to the existing request timeout,
  response-size bound and source-level retry policy.
- Do **not** assume the API's list order is monotonic in \`published_at\`.
  An older publication timestamp is not a safe pagination stopping rule.
- Deduplicate releases by tag so overlapping pages do not generate duplicate
  candidate IDs.
- If a later page fails, mark that source unavailable and do not stage a
  partially collected source as successfully observed.
- Record \`pagination.pages_fetched\`, \`raw_items_scanned\`,
  \`paging_cap_reached\`, \`max_pages\` and \`per_page\` on the successful
  source-result metadata. This distinction matters because only a handful
  of recent releases might survive publication-date filtering after all 60
  raw results were fetched.
- Update Source Coverage Audit to flag \`possible_window_truncation\` based
  on the **raw page boundary**, not just the number of filtered results.
  Older reports without this metadata keep their conservative fallback.

This reduces exposure to the first-page blind spot but **does not prove**
exhaustiveness: more than 60 GitHub releases in the lookback window, a
changing feed during pagination, missing publication metadata, or publication
ordering anomalies can still cause misses. Saturating the third page triggers
a manual review flag; it is not proof that further items exist.

The arXiv search remains limited to its current configured first response.
The new coverage report continues flagging its cap. RSS publishers may
truncate feeds server-side, which cannot be detected from returned item
counts alone.

## Validation

- New \`tests/test_intelligence_pagination.py\` covers multi-page paging,
  short-page stops, overlapping pages, old/new mixed publication dates,
  hitting the bounded limit, invalid oversized pages and partial failure.
- Standard CI runs the new tests plus the existing Discovery, Triage,
  Reliability, Source Coverage and browser smoke suites.
- No live all-source scan has been certified by this PR. The next
  operational step is to manually run the weekly Intelligence Discovery
  workflow on master and inspect \`ai-chip-intelligence-source-coverage.md\`.
- No product, model or benchmark facts are auto-verified or written.
