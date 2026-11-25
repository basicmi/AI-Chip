# InferenceX ISL × OSL interaction matrices

Run from the repository root:

```bash
python3 scripts/analyze_inferencex_isl_osl_interaction.py --output /tmp/inferencex-isl-osl-interaction.json
```

The analyzer groups published InferenceX records by matching model, scenario,
precision, concurrency, hardware identity, system boundary, software metadata,
recipe fingerprint, stable execution configuration and evidence class. It then
varies both input sequence length (ISL) and output sequence length (OSL).

Each metric matrix requires at least two distinct observed ISL values and two
distinct observed OSL values. Only cells present in the source registry are
emitted. The report includes the rectangular grid size, observed cell count and
coverage fraction so sparse evidence is explicit. Each cell retains record IDs,
source URLs, publication dates, observed min/max and median of published values.

The metrics are source-normalized output throughput/GPU, median and P99 TTFT,
median and P99 TPOT, and P99 ITL where available. Different metrics may have
different source records; their cells must not be combined into synthetic runs.

No missing cell is interpolated. Coverage is not statistical confidence.
The matrix visualizes a two-dimensional observed workload surface, not a causal
interaction estimate. Unreported runtime details can still confound comparisons.
No KV-cache estimates, extrapolation, cost estimates, saturation claims or
benchmark execution are performed.
