# AI Chip Intelligence — end-to-end reliability (PR #100)

## Source health and consistency checks

The weekly discovery workflow now generates:

- ai-chip-intelligence-health.json
- ai-chip-intelligence-health.md

The report includes per-run source availability, error counts, review candidates,
extracted Claim counts, triage coverage, persistent backlog and unresolved
age. It validates identities and counts across Discovery, Claim Extraction,
Evidence Graph, Triage and Review State.

Health is **healthy** when stages agree and sources were observed,
**degraded** for recoverable source outages or incomplete review presentation,
and **failed** for structural inconsistency, accidental verification
assertions, or a total outage of all configured discovery sources.

A degraded run continues to produce review artifacts with explicit warnings;
an all-source outage fails closed rather than advancing checkpoints. A
successful scan with zero recent candidates is not an outage; source
availability is independent of observed item count.

## Cache commit protection

Previously the discovery CLI wrote its change-detection state before the
downstream Claim / Evidence / Triage stages had completed. A failure in one
of those stages could make changes appear unchanged in a later run.

Both existing cache files are now copied to staging paths under RUNNER_TEMP.
All stages use the staged files, and the workflow restores them to their
cache paths *only after* the consistency and health audit returns success.

GitHub Actions cache still uses run-scoped keys and restore prefixes. It
can be evicted or reset and is not a permanent audit ledger. It is also not
transactional across different runs: workflow concurrency is the repository's
existing protection against overlapping scheduled/manual executions.

## Offline integration replay

    python3 -m unittest discover -s tests -p "test_intelligence_reliability.py"

This covers synthetic GitHub release + RSS sources with no external network
calls, the complete Discovery -> Claim -> Evidence Graph -> Triage ->
Persistent Review State -> Audit pipeline, second-week unchanged discoveries
with unresolved backlog retention, partial and complete outages, and
fail-closed tests for state/identity mismatch and status escalation.

### Explicit limitations

This PR does **not** claim to run an authenticated live discovery test
against all 24 remote sources; access and rate limits are external. It
does **not** test a real human-reviewed Evidence-to-PR dispatch (that
requires reviewed input and repository PR permissions).

GitHub Actions' summary and artifacts surface source problems, but this
PR does not send ongoing notifications or create background automations.
No scanned Claim is promoted to independently verified, and no production
registry is modified automatically.
