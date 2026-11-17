# Evidence Review Workbench — reviewer decisions and manifest export (PR #96)

At /evidence-review/, users load local intelligence Claim JSON and optional
Evidence Graph, Triage, Review-State and bounded Claim Review Batch JSON from
the same weekly GitHub Actions artifact. All files are read locally in the
browser; no upload or automatic approval occurs.

## Local review decisions

Select "Review this claim". Record an outcome: needs more evidence, reject,
or accept for evidence attachment review. Enter the real reviewer identity,
review date and at least 30 characters of rationale. Load the current
`data/intelligence-review-decisions.json` from master before exporting; the
workbench validates it and merges new decisions without discarding prior ones.

The exported file uses the exact schema consumed by
`track_intelligence_review_state.py`. It remains a local file until a human
commits the updated ledger to master. The next weekly Discovery run consumes
that committed ledger. Browser refresh clears unexported decisions. No
approval or factual verification is inferred from the extracted source.
Decision dates are exported as timezone-aware ISO-8601 timestamps.

## Human-reviewed Approval Manifest

The existing Python Evidence-to-PR workflow accepts only attaching one new
reviewed source to an unchanged, existing company Claim.

1. Choose an unverified candidate and inspect the full original source.
2. Record "Accept for evidence attachment review" with rationale.
3. Load a recent data/company-profiles.json directly into the browser.
4. Select the exact company and already-existing Claim; the browser computes
   its SHA256 from canonical key-sorted JSON, matching the Python generator.
5. Enter unique approval and evidence IDs, real reviewer, review/check dates,
   source title/publisher/type/independence and meaningful notes.
6. Explicitly confirm personal source and existing-Claim review.
7. Download the Approval Manifest JSON. Its source URL is taken exactly from
   the extracted Claim and cannot be substituted in the browser.
8. Commit the manifest under reviews/approvals/ on master and the matching
   original Claim report under reviews/claims/, then manually dispatch
   propose-reviewed-evidence.yml on master.

The manifest is a reviewer assertion, not a cryptographic approval or
independent verification. The browser does not authenticate reviewer identity,
visit sources on its own, create PRs or alter any company/product/benchmark
registry. The Python data validator and independent exact-patch verifier
remain the acceptance gates, followed by human PR review.

Rejected/needs-more-evidence claims cannot produce an approval manifest.
A company with an existing evidence entry for the selected source URL is
rejected. The Python generator independently checks that and Claim SHA256.

## Browser test

The Playwright smoke test exercises local review selection, decision recording,
blocked export without explicit confirmation, approval JSON export using a
synthetic test-only company Claim, and SHA256 equality with Node crypto.
No synthetic source is represented as real evidence or saved to production.

## Priority triage (PR #97)

Optionally load `ai-chip-intelligence-triage.json` from the same weekly run.
The browser validates the input Claim IDs and unverified status, then orders
all matched Claim cards by the transparent rule-based **review urgency** score.
Scores do not represent truth confidence; exact-text duplicates are still
not independent evidence. The triage file is local-only and never auto-approves
claims or updates the company/product databases. The original Claim and Graph
files remain required/optional exactly as before.


## Persistent review backlog dashboard (PR #99)

Load the optional \`ai-chip-intelligence-review-state.json\` from **the same
workflow run** as the Claim and (optionally) Evidence Graph / Triage files.
The workbench validates the versioned snapshot, current Claim membership,
review-state counts, backlog coverage, age values, and the explicit
\`state_is_approval: false\` boundary.

The dashboard displays:
- A point-in-time backlog count with unresolved 7/14/30+ day distributions;
- First-observed aging and workflow status on current Claim cards;
- Filters for 7+/14+/30+ day review age and operational review status;
- A separate list of previously observed Claim IDs **absent from this week's
  discovery**. These entries have only the retained ID, last known source
  and operational metadata, not their original Claim text. They cannot be
  approved from this view without retrieving the original report.

**A single snapshot is not a historical trend.** The tool does not invent
time-series charts from one observation; accurate week-over-week trends
would require multiple persisted snapshots. Actions cache eviction, metadata
changes or regenerated IDs may reset first-seen time. Source publication age
and first-seen wait age are different quantities.

\`accepted_for_evidence_attachment\` is an operational review decision, not
independent verification of a product claim. No website upload or GitHub
write occurs. The manually gated Evidence-to-PR approval is unchanged.

The browser smoke test uses synthetic Claim/Graph/Triage/Review-State
snapshots, covers old-but-not-observed backlog, aging counters, review-state
and age filters, and rejects a fabricated \`state_is_approval: true\` file.


## Bounded historical Claim review batches (PR #127)

The weekly artifact now includes
`ai-chip-intelligence-claim-review-batch.json`. Load it alongside the Claim
report and the Review-State JSON from the **same run**. The workbench checks
the batch timestamp, selected Claim IDs, unresolved state, source URL,
retained Claim snapshot and blank decision-template rows before merging the
selected Claims into the review cards.

This makes recovered historical Claims reviewable even when they no longer
appear in the current discovery's Claim extraction report. The persistent
backlog panel also displays retained historical statements and source excerpts
when present. The batch remains bounded (default 25); the workbench does not
silently load the entire historical backlog into the card list.

## Exporting the formal human decision ledger (PR #127)

The workbench requires the current master decision ledger before export.
Existing entries are preserved; duplicate Claim IDs are rejected. Every new
decision requires a reviewer identity, a valid non-future review date and at
least 30 characters of rationale. The exported JSON has exactly the
`schema_version` and `decisions` fields, with each decision containing
exactly `claim_id`, `decision`, `reviewer`, `decided_at` and `notes`.

The export is still local. Commit the reviewed file as
`data/intelligence-review-decisions.json`; no browser action writes to GitHub.
The next Discovery run will update operational review states from this ledger.
`accepted_for_evidence_attachment` remains only a request to prepare a
separate, explicitly reviewed Evidence-to-PR manifest. It is not a verified
technical claim or permission to update a formal registry.
