# Model Support Explorer v2

Model releases and verified accelerator recipes are separate datasets.

- data/model-catalog.json is the model index. An official model page confirms
  the named checkpoint and curated model metadata, **not** accelerator support.
- data/model-support.json remains the configuration-specific evidence matrix.
  No support path may be added without source evidence for the exact
  accelerator, checkpoint, runtime/precision and configuration.
- The UI exposes two searchable sections with independent counts. Catalog-only
  checkpoints prominently say that no verified hardware path is curated.
- Each catalog record has an independently tracked checked date and source
  status. Older than 90 days is visibly labeled REVIEW OVERDUE. Legacy entries
  are labeled as inherited registry metadata, not newly verified official cards.
- No model catalog entries are benchmark observations.

## Updating the catalog

1. Read the model publisher's official model card, including model repository,
   access requirements, architecture, parameter counts, context and license.
2. Add a record to data/model-catalog.json with a real model page link and
   date you verified it. Use null for unverified optional claims.
3. Do not create a support path until exact accelerator documentation is
   independently available. Running a model card example does not by itself
   establish an accelerator- and runtime-specific support record.
4. Run the catalog and support validators and the browser smoke tests.

    python3 scripts/validate_model_catalog.py
    python3 scripts/validate_model_support.py
    python3 -m unittest discover -s tests -p 'test_model_catalog.py'

## Scheduled read-only discovery

The weekly workflow checks known model repositories and scans recent official
publisher-organization model listings for potential new checkpoints via the
Hugging Face model API and writes a downloadable discovery snapshot as a
GitHub Actions artifact. It does **not** commit changes or auto-approve model
facts/hardware support: human review of model versions, licences and hardware
evidence is necessary. Failures in external discovery do not alter CI or the
published registry.

    python3 scripts/discover_model_catalog.py --output /tmp/model-discovery.json

No API token is required for public model pages. Unreviewed publisher listing entries are explicitly labeled candidates (not
new verified models). Gated/private model pages may
not be available without credentials; that is reported as an error, not as an
absence of the model or an unsupported accelerator.

The six newly curated official model cards for this PR are:
DeepSeek-V3.2, Qwen3-Coder-480B-A35B-Instruct, Kimi-K2-Thinking,
gpt-oss-20b, Llama-4-Maverick-17B-128E-Instruct, and
Mistral-Small-3.2-24B-Instruct-2506.
