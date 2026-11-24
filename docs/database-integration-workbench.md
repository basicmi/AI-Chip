# Database Integration Workbench (Phase 2)

The Database Integration Workbench adds a reproducible proposal boundary
between human Claim review and the published company-profile registry.

## Scope of the first integration adapter

Version 1 supports exactly one operation class:

**Attach one human-reviewed Evidence object to one existing company-profile
Claim, and append that Evidence ID to the Claim's `evidence_ids`.**

It does not create new company/product/Claim records, edit numeric values,
change claim status, change scope or metric context, alter product identity,
or modify model support, compatibility, workload or benchmark registries.
Those require separate typed adapters and validators.

## Inputs and provenance

The proposal generator consumes:

1. The exact current `data/company-profiles.json` registry (schema 1.3).
2. The original Claim extraction report from one discovery run (schema 1.0).
3. A human-reviewed Approval Manifest exported by the Evidence Review Workbench.

The Approval Manifest must identify an existing company and Claim, contain the
Claim's canonical SHA256, reference the exact extracted Claim ID, and use the
same original HTTPS source URL. The Evidence object must have a reviewed
status and complete source metadata. The generator reuses the existing
`propose_evidence_update.py` and `verify_evidence_patch.py` safety gates.

## Generate a proposal locally

From the repository root:

    python3 scripts/build_database_integration_proposal.py build \
      --company-profiles data/company-profiles.json \
      --claim-report /path/to/ai-chip-intelligence-claims.json \
      --approval /path/to/reviewed-approval.json \
      --proposal-output /tmp/integration-proposal.json \
      --patch-output /tmp/integration-patch.json \
      --audit-output /tmp/integration-audit.json \
      --diff-output /tmp/integration.diff \
      --database-output /tmp/company-profiles-proposed.json

The generator does not edit the checkout. It writes:
- **Proposal package:** source Claim snapshot, approval, target registry and
  Claim fingerprints, two JSON Patch operations, audit assertions and hashes.
- **JSON Patch:** the exact two append operations and the base registry hash.
- **Audit JSON:** independent exact-change verification and provenance metadata.
- **Unified diff:** a human-readable before/after view of the complete registry.
- **Proposed registry:** a separate candidate file for inspection.

The package is content-addressed with a SHA256 over its canonical JSON body.
It also binds to the SHA256 of the exact raw base registry file. A proposal
cannot be replayed against a different registry revision.

## Local review

Open `/database-integration/` on the site, then load all three files:
- the proposal package;
- the original Claim extraction report from the same discovery run;
- the exact `company-profiles.json` revision used to build the package.

The page verifies the package hash, source Claim equality, registry hash,
target company/Claim, exact allowed patch paths, Evidence URL and quote
checksum, proposed-registry hash and audit guardrails. It displays the
Source → Extracted Claim → Existing Database Claim chain and a field-level
diff. Files are read locally and are not uploaded.

The browser review is a convenience layer. The Python verifier in CI is the
authoritative acceptance gate. During workflow replay, the original Claim
report and Approval Manifest are separate required inputs; the package alone
is not treated as its own source of provenance.

## Commit and create a review-only PR

After inspecting the proposal, commit all three provenance inputs:

    reviews/integration-proposals/<proposal-id>.json
    reviews/approvals/<approval-id>.json
    reviews/claims/<discovery-run-claims>.json

Then manually dispatch
`.github/workflows/integrate-database-proposal.yml` on `master`, supplying
the three committed paths. The workflow checks that the embedded source Claim
and Approval Manifest exactly match those separate committed originals. It:

1. Rejects paths outside the designated directory, uncommitted files,
   symlinks and path traversal.
2. Rebuilds the exact proposal against the current master registry.
3. Rejects package tampering, stale registry hashes, changed target Claims,
   mismatched source Claims or any operation other than the two appends.
4. Runs the full company-profile validator.
5. Confirms that the only changed path is
   `data/company-profiles.json`.
6. Uploads the patch, audit and diff, then opens a pull request for human review.

No auto-merge or scheduled write is enabled. The proposal package remains
committed as the provenance record. The generated PR contains only the
company-profile registry change.

## Audit semantics and limitations

The chain records:
- extracted Claim ID, statement and original evidence quote;
- exact source URL and source metadata;
- reviewer, decision date and review rationale;
- target company and existing Claim;
- source quote, target Claim and base registry fingerprints;
- the exact two JSON Patch paths;
- proposed registry hash and independent patch-verification result.

A passing package means the proposal is reproducible and the database change
is exactly within the permitted write set. It does **not** mean the source
statement is true, the source is independent, the benchmark was reproduced,
or the Claim deserves a higher verification status. Reviewer identity is not
cryptographically authenticated. Human review of the resulting PR remains
mandatory.

## Tests

Run:

    python3 -m unittest discover -s tests -p "test_database_integration_proposal.py"

CI runs this suite as part of the repository's required validation workflow.
