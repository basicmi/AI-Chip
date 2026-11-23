# Evidence Quality Dashboard

The `/evidence-quality/` page displays **local-only** evidence-hygiene and
review-workload trends. No API calls, files uploads, user decisions, or
production database changes are made by the page.

## Generation

After each completed weekly Discovery run, the workflow produces:

- `ai-chip-intelligence-evidence-dashboard.json`
- `ai-chip-intelligence-evidence-dashboard.md`

The snapshot combines the same-run evidence-quality audit, persistent review
state, blank human semantic review packet and blank source-lineage review
worksheet.

    python3 scripts/build_intelligence_evidence_quality_snapshot.py \
      --quality ai-chip-intelligence-evidence-quality.json \
      --review-state ai-chip-intelligence-review-state.json \
      --lineage ai-chip-intelligence-source-lineage-review-template.json \
      --semantic ai-chip-intelligence-semantic-review-template.json \
      --output ai-chip-intelligence-evidence-dashboard.json \
      --markdown ai-chip-intelligence-evidence-dashboard.md

Run `/evidence-quality/`, select one or more JSON snapshots and compare
completed runs. The browser validates counts, policy flags, timestamps,
denominators, and duplicate imported timestamps before rendering.

## Metric interpretation

| Metric | What it measures | What it does **not** measure |
|---|---|---|
| Quote traceability | Extracted quotes present in the fetched excerpt | The quote actually entails the Claim |
| Provenance completeness | Filled origin metadata including publication date | The technical assertion is true |
| Source document count | Distinct URLs in extracted Claim reports | Independent replications |
| Review backlog | Persistent Claim work awaiting decisions | Verified technical findings |
| Payload coverage | Historical Claims with retained text | Completeness of original scientific evidence |
| Semantic queued | Blank two-human review slots generated | Completed human support judgments |
| Lineage queued | Cross-document duplicate clusters selected | Confirmed source lineage |

Human reviewer agreement, completed lineage coverage, and independently
verified Claim counts are deliberately **null / N/A** unless a separately
reviewed and authenticated evaluation is integrated in a later stage. A blank
worksheet is not evidence of a completed review. No combined credibility
score is produced.

Older snapshots that were never downloaded, expired artifacts, and failed
weekly runs are absent from trend comparisons. Percentage trends are based on
the mix of extracted Claims in each run, not a fixed cohort.


## Optional reviewer-reported semantic evaluation overlay (PR #133)

The dashboard may optionally load a semantic evaluation JSON produced *after
human review* by `scripts/review_intelligence_semantic_support.py --evaluate`.
The evaluation is not part of the weekly generated evidence snapshot, because
the weekly workflow has no access to completed human judgments.

The JSON must match an imported snapshot's `semantic_batch_id`. The page
checks exact selected-batch counts, reviewer-label totals, agreement
arithmetic, unique Claim IDs, disagreement bookkeeping, and the explicit
zero-auto-verification flag. Invalid or cross-batch files are rejected and
their overlay is cleared.

When a matching evaluation is available, the dashboard displays its raw
reviewer agreement with the number of double-reviewed Claims and outstanding
adjudication cases. The value is prominently labeled
**reviewer-reported / not authenticated**. It is a measure of consistency
within a small priority-selected review batch, not a claim of accuracy,
independent replication, or a representative population statistic.

The local file is never uploaded or committed. In particular, importing
an evaluation does not change the immutable weekly snapshot, the Claim
Decision Ledger, the evidence graph, or any production chip/benchmark data.
A malicious or fabricated file can still imitate a structurally valid
evaluation; the page cannot authenticate reviewer identity.
