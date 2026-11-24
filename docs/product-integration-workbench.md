# Product Integration Workbench (Typed Adapter 1)

## Scope

This adapter adds exactly one new product to one existing company profile,
together with:
- one initial product-identity Claim;
- one reviewed Evidence record;
- one product availability-history event linked to that Evidence.

It does not create companies, add performance or benchmark values, change
existing Claims, add compatibility-platform references, add related-product
links, or modify workload, model-support, compatibility or benchmark registries.

The initial Claim is fixed to:
- `subject_type: product`;
- `topic: product_identity`;
- `claim_status: vendor_reported`;
- `evidence_ids: [the new Evidence ID]`.

The Claim statement must exactly match the reviewed extracted source Claim.
A product's initial availability is linked to the same reviewed Evidence.
No measured performance, throughput, FLOPS, bandwidth or power Claim is
created by this adapter.

## Approval Manifest

The Product Creation Approval Manifest has schema version 1.0 and contains:
- reviewer, review date, approval ID and explicit decision
  `approved_new_product_with_identity_claim`;
- an existing company ID;
- the extracted Claim ID;
- a new Product object using the company-profile product schema;
- one initial product-identity Claim;
- one reviewed Evidence record;
- review notes of at least 30 characters.

The Evidence URL must exactly match the source URL in the original Claim
extraction report. The source Claim must be an `unverified_candidate`.
Only company primary, vendor primary or official project sources are accepted
for this first product-creation adapter.

The product's `claim_ids` must contain exactly the new Claim ID. The Claim's
subject must point back to the new product. The Claim's `evidence_ids` and
the single initial `availability_history` event must both point to the new
Evidence ID. These links are checked in both the builder and the full
company-profile validator.

## Build a proposal locally

From the repository root:

    python3 scripts/build_product_creation_proposal.py build \
      --company-profiles data/company-profiles.json \
      --claim-report /path/to/ai-chip-intelligence-claims.json \
      --approval /path/to/product-creation-approval.json \
      --proposal-output /tmp/product-proposal.json \
      --database-output /tmp/company-profiles-proposed.json \
      --patch-output /tmp/product-patch.json \
      --audit-output /tmp/product-audit.json \
      --diff-output /tmp/product.diff

The builder never edits the repository checkout. It produces a content-addressed
proposal, a three-operation JSON Patch, audit metadata, a unified diff and a
separate proposed registry. The package binds to the SHA256 of the exact raw
base registry file.

## Local review

Open `/product-integration/` and load all four inputs:
1. product proposal package;
2. original Claim extraction report;
3. separate Product Creation Approval Manifest;
4. exact base `data/company-profiles.json`.

The browser verifies package integrity, the original Claim and approval
matches, base registry hash, typed object relationships, the exact three
append paths and the proposed registry hash. It displays Source → Product →
Initial Claim and allows local downloads. Files are not uploaded.

The browser is a convenience review surface. The Python verifier and full
company-profile validator in CI are authoritative.

## Commit and create a review-only PR

Commit the three provenance inputs:

    reviews/product-proposals/<proposal-id>.json
    reviews/approvals/<approval-id>.json
    reviews/claims/<discovery-run-claims>.json

Then manually dispatch
`.github/workflows/integrate-product-proposal.yml` on `master` with all
three paths. The workflow:
1. rejects paths outside their designated directories, uncommitted inputs,
   symlinks and path traversal;
2. independently rebuilds the package against the current master registry;
3. verifies the separate Approval Manifest and original Claim report;
4. applies only the three append operations to a temporary checkout;
5. runs the complete company-profile validator;
6. confirms that only `data/company-profiles.json` changed;
7. uploads patch, audit and diff, then creates a human-review PR.

There is no automatic merge or scheduled write. A stale base registry or any
change to the source, approval, typed objects or operation set fails closed.

## Tests

    python3 -m unittest discover -s tests -p "test_product_creation_proposal.py"

The tests cover the exact three-record append, deterministic replay, typed
relationships, duplicate IDs/URLs, source/approval mismatches, stale base
registry, tampered operations, HTTPS requirements, availability history and
CLI round-trip behavior.
