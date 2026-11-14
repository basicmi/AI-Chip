# Evidence-to-PR — reviewed evidence attachment (PR #93)

The first write-capable stage of AI Chip Intelligence deliberately supports
only a narrow operation: **attach one reviewed source to one existing,
unchanged company-profile claim**. This reduces risk of fabricated hardware
specifications or unreviewed model support.

The approval artifact is a versioned JSON manifest prepared and authorized
by a human reviewer after reading the full original source. It contains:
- reviewer, review date and rationale;
- an existing company ID and claim ID;
- exact SHA256 of the current claim object (computed from canonical sorted JSON);
- a PR #90 unverified extracted claim ID;
- a new evidence record that uses the *same* original source URL.

The generator verifies all IDs, evidence fields, dates, review decision,
source URL, exact target claim fingerprint and duplicates. It does not fetch
the source, judge factual truth, or assert independent verification.

Example steps for a human reviewer:

    python3 - <<'PY'
    import hashlib, json
    db = json.load(open("data/company-profiles.json"))
    target = next(c for c in db["companies"] if c["id"] == "nvidia")
    claim = next(c for c in target["claims"] if c["id"] == "b200-memory-capacity")
    raw = json.dumps(claim, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    print(hashlib.sha256(raw.encode("utf-8")).hexdigest())
    PY

Write an approval JSON conforming to the format in
tests/test_evidence_update_proposal.py, after verifying the exact source and
target claim. The original claim candidate JSON must be supplied.

    python3 scripts/propose_evidence_update.py \
      --company-profiles data/company-profiles.json \
      --claim-report /path/to/ai-chip-intelligence-claims.json \
      --approval /path/to/reviewed-approval.json \
      --output /tmp/company-profiles-proposal.json \
      --audit-output /tmp/evidence-approval-audit.json \
      --diff-output /tmp/evidence-update.diff

The proposal file and diff are for review; nothing is modified in the checkout.

## Creating a PR from an approved manifest

A manual workflow_dispatch job accepts paths to a **committed** reviewed
approval manifest and matching extracted-claim report. It validates the proposed
database, then creates a PR modifying only data/company-profiles.json.
Permissions are scoped to contents:write and pull-requests:write for this
manually invoked workflow. Approval files must be under reviews/approvals/
and reports under reviews/claims/; path traversal and symlinks are rejected.

No scheduled job, auto-merging or automatic approval is included. GitHub branch
protection and human code review are required before any data update enters master.

## Boundaries

This initial phase does not create new claims, modify numeric values, change
claim statuses or alter model support, compatibility, benchmark, product
identity, hardware scope or lifecycle state. These require separate governed
workflows with stronger claim-level evidence checks.
