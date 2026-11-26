# Performance review ledger

Use the offline CLI to append a human decision to an existing ledger:

```bash
python3 scripts/append_performance_review_decision.py --ledger data/performance-review-ledger.json --record record.json --plan plan.json --submission submission.json --decision decision.json --output updated-ledger.json
```

The tool rebuilds the review from the exact record, plan and submission. The
decision must contain a unique decision_id, reviewer, timezone-aware reviewed_at,
review_sha256 (computed with digest(build_review(...))), verdict, rationale,
applicability, limitations, supersedes (null for the first decision), checks
and evidence_run_ids. A revision also requires revision_reason.
See the unit test for a synthetic example.

The supported verdicts are supported, refuted, inconclusive and revision_required.
Supported/refuted require an unblocked report, cited valid runs from both
conditions and explicit true attestations for source_verified, baseline_reproduced,
controls_verified, measurement_alignment_verified, mechanism_evidence_reviewed
and run_completeness_reviewed. These are human attestations, not automated
verification. The tool does not infer a verdict from performance improvement.

Each entry binds the exact evidence version and review hash, plus the preceding
entry hash. Supersession applies only to the exact record/plan/submission version;
new evidence requires a separate decision. The chain detects inconsistent edits
but is not a digital signature, trusted timestamp or proof of reviewer identity.
Someone able to rewrite the entire ledger can recompute hashes. Use Git history
and normal PR review for governance. Keep the original inputs and review packets
alongside the ledger for later reproduction. No example decisions are included
in the production ledger. The CLI writes a separate output; a human must review
and commit it. No hardware execution, automatic approval or registry update.
