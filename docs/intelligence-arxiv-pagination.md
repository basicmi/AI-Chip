# arXiv bounded pagination and query-coverage diagnostics (PR #105)

## Problem

The curated arXiv source previously fetched only \`start=0\` with
\`max_results=100\`, and applied the 45-day lookback *after* fetching.
A broad query may return more than 100 recent submissions, losing relevant
papers outside the first page without a reliable indication.

## Changes

- Fetch at most **3 pages** using the existing per-page \`max_results\`
  (currently 100), up to 300 raw records. Stop at the first short page.
- Use deterministic \`start=0,100,200\` offsets and a 3-second inter-page
  delay to respect arXiv API courtesy limits. Existing timeout, response-size
  protections, and transient transport retry rules remain active.
- Deduplicate overlapping arXiv IDs across pages; preserve original
  preprint/non-peer-reviewed evidence labels.
- Do not assume arXiv's submission sort order implies every paper's
  publication/update date is monotonic.
- Fail the entire source if any later page is invalid/unavailable rather than
  publish partially collected results as a healthy scan.
- Add \`pagination\` metadata to arXiv source results, matching GitHub
  Releases' bounded pagination model. The Source Coverage Audit now uses
  **raw page saturation**, not the post-filtered number of recent papers,
  to flag a potentially truncated window.
- Test short-page termination, cross-page duplicates, bounded cap, source
  failure mid-pagination, oversized response, invalid page sizes and source
  coverage audit consistency with synthetic Atom documents.

## Important limitations

This is **not exhaustive search**. A wide query can exceed 300 entries, and
changing results while paging may shift offsets. Hitting the cap is a warning,
not proof of a missing relevant paper. Narrower topic queries and incremental
time-window partitions could further reduce omissions in a later iteration.

As of the repository check on 2026-11-14 there were no completed Weekly AI
Chip Intelligence Discovery runs in the latest 100 Actions entries. This
PR's CI uses offline synthetic Atom responses. It does not certify the
current reachability or completeness of arXiv, RSS feeds, or GitHub Releases.

After merge, manually dispatch the Weekly AI Chip intelligence discovery
workflow on master. Inspect
\`ai-chip-intelligence-source-coverage.json\` and the corresponding arXiv
\`pagination\` diagnostics, alongside source failure classification.

All extracted claims remain unverified, and the existing human Evidence-to-PR
gate remains unchanged.
