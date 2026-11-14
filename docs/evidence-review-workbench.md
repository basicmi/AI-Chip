# Evidence Review Workbench — reviewer decisions and manifest export (PR #96)

At /evidence-review/, users load local intelligence Claim JSON and optional
Evidence Graph JSON from a weekly GitHub Actions artifact.

## Local review decisions

Select "Review this claim". Record a local outcome: needs more evidence,
reject, or accept for evidence attachment review. At least 30 characters of
review notes are required. Export a local decision log if useful.

The log remains a session-local draft, never an authoritative status change.
Browser refresh clears it. No approval is inferred from the extracted source.

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
