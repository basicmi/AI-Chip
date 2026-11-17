# AI Chip — deeper targeted arXiv retrieval experiment

This experiment increases the isolated targeted-query depth from one page to
at most two pages per query group. Each page remains capped at 50 raw arXiv
entries, so the experiment is bounded to at most 100 raw entries per group and
400 across the four configured groups.

The production arXiv source registry is unchanged. The experiment still uses
the same 45-day discovery window, date filtering, Atom parser, retry policy,
known-item seed set, candidate de-duplication and human-review sampling.
Pagination diagnostics record pages fetched, raw entries scanned and whether
the configured page cap was reached.

The purpose is to measure marginal coverage beyond the first 50 results:
- additional unique papers beyond the production baseline;
- additional known-item seed hits;
- overlap across groups and with baseline;
- the share of query groups that still saturate the second-page cap.

A second full page is a signal that the experiment may still be truncated; it
is not proof that more relevant papers exist. Candidate relevance remains
unverified until independent human labels are recorded. The experiment does
not modify production queries or feed its candidates into the production
review queue.

The scheduled Discovery workflow runs weekly, or this experiment can be
rerun by manually dispatching that workflow after the PR is merged.
