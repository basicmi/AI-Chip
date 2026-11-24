# Persistent Review State & Aging Alerts (PR #98)

The weekly discovery workflow now tracks first-seen and last-seen timestamps
for every extracted Claim ID across runs. Crucially, the persistent backlog
continues to track unhandled Claim IDs even when they are absent from a later
change-only Discovery run, preventing silent loss of unresolved review items. Its persistent state lives in a
**dedicated GitHub Actions cache** at
.cache/ai-chip-review-state.json (separate from the source-discovery cache).
The cache uses unique run-ID keys and a restore prefix. Cache expiration or
eviction resets first-seen history: this is a best-effort operational cache,
not a durable audit database.

## Review age vs publication age

- \`source_age_days\` in the triage output is the age of the original
  publication, not the time a reviewer has waited.
- \`days_since_first_seen\` in review-state output tracks how long an
  extracted Claim ID has been observed in the cached queue.
- Claim IDs may change when extracted wording or metadata changes. Such a
  change begins a new tracking clock; absence from a run does not mark an
  earlier Claim approved.
- Alert levels: within 7 days, 7–13 days, 14–29 days, and 30+ days.
- \`needs_more_evidence\` decisions that have waited 14+ days are flagged
  for follow-up; this is not an automatic escalation of evidence confidence.

## Explicit human decisions

Optional committed \`data/intelligence-review-decisions.json\` is the
human-controlled ledger. Each item explicitly specifies an extracted Claim
ID, reviewer identity, timezone-aware ISO-8601 decision timestamp, decision
and at least 30 characters of reasoning.
Allowed review outcomes are: needs_more_evidence, rejected, and
accepted_for_evidence_attachment.

The ledger is **not** populated from a browser-local draft exported by
the Workbench, since a draft log is not an authenticated review action.
The default ledger is empty, so all Claims stay pending. Acceptance for
evidence attachment is not proof of the Claim or an authorization to bypass
the separate Evidence-to-PR approval manifest and PR review.

Human decisions only apply to Claim IDs in the current claim extraction
report. Old decisions must be reconciled deliberately instead of silently
altering future extracted records.

## Locally run

    python3 scripts/track_intelligence_review_state.py \
      --triage /tmp/ai-chip-intelligence-triage.json \
      --claims /tmp/ai-chip-intelligence-claims.json \
      --state /tmp/ai-chip-review-state.json \
      --ledger data/intelligence-review-decisions.json \
      --output /tmp/ai-chip-intelligence-review-state.json \
      --markdown /tmp/ai-chip-intelligence-review-aging.md

The output summary and JSON artifact are added to the weekly Actions run.
No automatic commits, notifications, external messages or data PRs are
created. All individual Claim statuses remain unverified for factual
content, regardless of the operational review queue state.


## Ledger validation (PR #128)

The repository CI validates the committed decision ledger before merge, not
only when the next weekly discovery happens to consume it. The shared
`scripts/validate_intelligence_review_ledger.py` validator is also used by
`track_intelligence_review_state.py`, so CI and the scheduled pipeline enforce
the same rules.

The validator rejects:
- Unknown schema fields, unsupported versions or malformed decision rows;
- Duplicate, malformed or (when a review-state file is supplied) unknown
  Claim IDs;
- Unsupported outcomes, empty reviewer identities or short review notes;
- Invalid, timezone-naive or future-dated timestamps.

Run the standalone check:

    python3 scripts/validate_intelligence_review_ledger.py \
      --ledger data/intelligence-review-decisions.json

To additionally verify every decision against a persisted Claim-state cache:

    python3 scripts/validate_intelligence_review_ledger.py \
      --ledger data/intelligence-review-decisions.json \
      --review-state /path/to/ai-chip-intelligence-review-state.json

A passing ledger validation checks record structure and workflow consistency;
it does not authenticate the reviewer, inspect the original source or verify
the technical truth of a Claim. Human GitHub review and the separate
Evidence-to-PR approval process remain required.


## Claim-to-Database Conversion Funnel (Phase 2)

The weekly discovery workflow emits a conversion-funnel snapshot from the
persistent review-state observation, the explicit human decision ledger, and
`data/intelligence-database-integration.json`.

The funnel distinguishes:
- Current-run discovered Claims and the persistent backlog;
- Explicit decisions: pending, needs-more-evidence, rejected, and accepted
  for evidence attachment;
- Database-integrated Claims recorded only after a merged pull request is
  explicitly entered in the integration manifest.

An accepted Claim is **not** a database integration. Integration records must
name the Claim, target dataset, merged PR number, full merge commit SHA,
timezone-aware integration timestamp, reviewer, and rationale. The CI
validator rejects records for Claims not explicitly accepted for evidence
attachment. The manifest is human-maintained and is not an authenticated
claim of technical truth.

Run locally:

    python3 scripts/build_intelligence_conversion_funnel.py \
      --review-state /path/to/ai-chip-intelligence-review-state.json \
      --ledger data/intelligence-review-decisions.json \
      --integration-manifest data/intelligence-database-integration.json \
      --output /tmp/ai-chip-conversion-funnel.json \
      --markdown /tmp/ai-chip-conversion-funnel.md

No Claim, evidence graph, company/product record, or benchmark dataset is
automatically changed by this reporting step.


## Human Decision Analytics and Explicit Reason Codes (Phase 2)

The weekly discovery workflow emits `ai-chip-intelligence-decision-analytics.json`
and a Markdown summary. The report joins the persistent Claim aging state,
the human decision ledger, and the explicit reason-code register.

### Decision reason taxonomy

Reason codes live in `data/intelligence-review-reason-codes.json`. Each
record references one Claim that already has a human decision and includes:
primary reason, up to four secondary reasons, reviewer, timestamp, and a
short rationale. The initial registry is empty. Codes are never inferred from
free-text decision notes.

Allowed primary and secondary reason codes:

| Code | Meaning |
|---|---|
| `source_not_supporting_claim` | The cited source does not support the extracted statement |
| `source_unavailable` | The original source cannot currently be inspected |
| `insufficient_technical_detail` | The statement lacks enough technical specificity |
| `missing_configuration_or_version` | Product, model, firmware, or test configuration is unclear |
| `missing_measurement_conditions` | Benchmark or measurement conditions are incomplete |
| `contradictory_evidence` | Available sources conflict |
| `duplicate_or_syndicated` | The item repeats or republishes existing material |
| `out_of_scope` | The item is outside the project's maintained scope |
| `stale_or_superseded` | The information is outdated or superseded |
| `unclear_attribution` | The source, author, product, or result attribution is ambiguous |
| `independent_corroboration_needed` | A separate measurement or corroborating source is still needed |
| `other` | A reason not covered above; explain it in the rationale |

Reason coding is a separate human action. Missing reason codes remain
uncoded; no NLP or heuristic classification fills them in.

### Metrics and interpretation

- **Decision coverage:** ledger decisions divided by the persistent backlog.
- **Reason-code coverage:** decisions with an explicit reason annotation divided
  by all recorded decisions.
- **Outcome distribution:** needs-more-evidence, rejected, and accepted-for-
  evidence-attachment counts.
- **Decision latency:** elapsed time from the Claim's first observation in the
  persisted cache to the decision timestamp. This is not publication-to-review
  time; cache resets can make latency unavailable.
- **Unresolved age buckets:** pending and needs-more-evidence Claims grouped by
  time since first observation, with a 14-day follow-up threshold.
- **Reason distribution:** explicit primary reason codes, optionally grouped
  by decision outcome.

The dashboard accepts up to 52 local analytics snapshots to compare trends.
It does not upload the files. Reviewer identities and reason labels are not
independently authenticated. These metrics do not establish technical truth,
source entailment, or reviewer accuracy.

Run locally:

    python3 scripts/build_intelligence_decision_analytics.py \
      --review-state /path/to/ai-chip-intelligence-review-state.json \
      --ledger data/intelligence-review-decisions.json \
      --reason-codes data/intelligence-review-reason-codes.json \
      --output /tmp/ai-chip-intelligence-decision-analytics.json \
      --markdown /tmp/ai-chip-intelligence-decision-analytics.md
