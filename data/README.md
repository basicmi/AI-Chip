# Software compatibility data

This directory contains the machine-readable compatibility dataset used by the AI Chip landscape.

- `compatibility.json`: current public evidence snapshot.
- `../schemas/compatibility.schema.json`: JSON Schema (Draft 2020-12).
- `../scripts/validate_compatibility.py`: standard-library structural and referential validator.

## Validate

From the repository root:

```bash
python3 scripts/validate_compatibility.py
```

The validator checks JSON parsing, unique IDs, platform references, controlled status / layer / maintainer / evidence vocabularies, ISO dates, and HTTP(S) evidence URLs. It does not prove that an upstream compatibility claim is true; reviewers must inspect the linked primary evidence.

## Contribution rules

1. One record represents one project × platform × integration layer × version scope.
2. Use a specific hardware SKU / generation where public evidence permits.
3. Every integration must contain at least one dated evidence record and a non-empty limitations field.
4. Distinguish upstream support, vendor plugins, vendor frameworks, experimental branches, work in progress, and vendor-reported examples.
5. If public documents disagree, use `needs_review`; preserve the conflict in `limitations`.
6. Never infer support from a product announcement, marketing compatibility logo, or repository name.
7. Do not overwrite historical claims silently: update `last_checked`, replace / append evidence, and describe the change in the PR.
8. Version strings are evidence snapshots, not a promise that arbitrary combinations work.
