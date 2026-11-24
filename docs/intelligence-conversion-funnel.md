# Evidence-to-Database Conversion Funnel

Phase 2 makes the path from public information to curated technical records measurable.
The funnel is generated from one weekly discovery run and imported locally at
`/intelligence-funnel/`.

## Weekly snapshot

The discovery workflow writes:

- `ai-chip-intelligence-conversion-funnel.json`
- `ai-chip-intelligence-conversion-funnel.md`

The snapshot reconciles six inputs: discovery candidates, extracted Claims,
triage output, persistent review-state observations, the committed human
decision ledger, and the manually maintained database-integration receipt
manifest. Cross-stage counts and timestamps are checked before output.

## Metrics and denominators

| Metric | Denominator | Interpretation |
|---|---|---|
| Candidates yielding Claims | Discovered candidates | Extraction coverage, not truth |
| Decision coverage | Persistent review backlog | Claims with an explicit human decision |
| Acceptance rate | Recorded human decisions | Workflow eligibility for evidence attachment |
| Integration coverage | Accepted-for-attachment Claims | Claims with at least one explicit merged integration receipt |

Discovery candidates, extracted Claims and triage groups are different units.
One candidate can yield multiple Claims, and exact-text duplicate Claims can
collapse into one triage group. The page therefore shows stage counts and only
the rates with explicit denominators; it does not invent a single monotonic
conversion percentage.

## Human decisions are not factual verification

The allowed human decision states are:

- `pending`
- `needs_more_evidence`
- `rejected`
- `accepted_for_evidence_attachment`

The last state means only that a Claim is suitable for preparing a proposed
source-linked evidence attachment. It is not a fact check, independent
corroboration, final registry approval or permission for automatic writes.

## Manual integration receipts

`data/intelligence-database-integrations.json` is an
append-only-by-review convention, manually maintained receipt ledger. A receipt
must identify:

- the accepted Claim ID;
- an allowlisted target registry and an existing target record ID;
- the canonical merged AI-Chip pull-request URL and full merge commit SHA;
- integration timestamp, reviewer and a rationale.

The validator checks that the Claim has the accepted-for-attachment decision,
that the target record ID exists in the named registry, and that the receipt
contains a canonical PR reference and commit SHA. The receipt is still a
human-reported audit record; the workflow does not independently authenticate
the PR's merge status or the technical truth of the Claim.

The manifest never triggers a registry mutation. Formal database changes are
made through normal reviewed pull requests, not by the discovery workflow.

## Read-only and privacy boundaries

- The workflow reads curated registries and the receipt manifest; it does not
  write to company profiles, benchmark results, compatibility, model support,
  or workload registries.
- The browser dashboard only reads locally selected JSON files. It does not
  upload files, call APIs or persist imported snapshots.
- No composite credibility score or automatic factual-verification metric is
  produced.
- Missing denominators are N/A, never silently converted to zero.
- Integration coverage counts unique Claim IDs with receipts; multiple target
  records for one Claim do not inflate the unique integrated-Claim count.
