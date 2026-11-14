# Evidence-to-PR — end-to-end rehearsal and independent patch verification (PR #94)

PR #93 established a human-approved, manual workflow for attaching one new
evidence record to one pre-existing company Claim. PR #94 adds a complete
CI rehearsal against the **real company-profiles.json registry** and an
independent exact-change verifier before the write-capable workflow creates
a PR.

## What the CI rehearsal does

tests/test_evidence_to_pr_rehearsal.py uses the actual existing NVIDIA
B200 memory-capacity Claim and the current repository data model. It creates
an explicitly synthetic claim extraction and test-only approval in memory,
then executes the same proposal CLI and independent verifier used by the
manual GitHub workflow.

It verifies:
- the original database remains untouched;
- exactly one new evidence object was appended to the intended company;
- exactly one existing Claim gained exactly one evidence ID;
- no claims, numeric values, units, scopes, statuses, product identities or
  unrelated database fields changed;
- stale claim approvals and duplicated existing real source URLs are rejected;
- arbitrary claim-status escalation and extra evidence records are rejected;
- the resulting diff, audit and independent verification are generated.

The fixture URL (example.org) and CI reviewer identity are intentionally
fake. They are **not real evidence or actual human approvals** and must
never be committed under reviews/approvals/ or used to invoke the live
PR-writing workflow. This is an end-to-end local/CI rehearsal of the logic,
**not** a successful real-world GitHub workflow_dispatch or data PR.

    python3 -m unittest discover -s tests -p "test_evidence_to_pr_rehearsal.py"

## Independent patch gate

    python3 scripts/verify_evidence_patch.py \
      --original data/company-profiles.json \
      --updated /tmp/company-profiles-proposal.json \
      --approval /path/to/reviewed-approval.json \
      --audit /tmp/evidence-approval-audit.json \
      --output /tmp/verification.json

The verifier reconstructs the original data from the proposal by reversing
**only** the approved appended evidence and Claim evidence-ID. If any other
object differs, it fails closed. It is deliberately separate from the
patch-generation function.

## Manual write workflow safeguards

.github/workflows/propose-reviewed-evidence.yml:

- Runs only when dispatched against the master branch.
- Accepts only committed JSON inputs under reviews/approvals/ and
  reviews/claims/; checks confinement to repository and git tracking.
- Checks reviewer manifest, source URL equality and exact existing Claim
  SHA256; then performs the independent verifier BEFORE touching the
  checked-out database.
- Executes the full company-profile data validator and enforces the single
  modified path data/company-profiles.json.
- Uploads an audit report, diff and patch verification as Actions artifacts.
- Uses a unique branch per approval ID, preventing an unrelated approval
  from overwriting the proposal in an existing PR.
- Still requires human inspection and merge; it never auto-merges.

**GitHub setup remains required**: Actions must be allowed to create PRs,
and the repository's branch protection/review rules should be configured.
The manifest's reviewer string is an operator assertion, not a cryptographic
identity signature; GitHub actor, commit provenance and branch protection
provide the surrounding governance. The CI rehearsal cannot establish
that these repository settings or a real manual dispatch work end-to-end.

## Next safe live test

A maintainer can choose a genuinely new primary source that is not already
in the company's evidence list; manually inspect the original page; review
the precise existing Claim, scope and value; commit a real approval manifest
and matching extracted source report; and dispatch on master.

Inspect the resulting proposal PR before merge. If no genuinely new
appropriate source is available, **do not manufacture a reviewed evidence
record just to test the workflow**.
