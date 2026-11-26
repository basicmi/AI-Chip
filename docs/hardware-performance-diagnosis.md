# Hardware and Serving Performance Diagnosis

## Existing engine

`scripts/diagnose_hardware_performance.py` is the repository's evidence-constrained diagnosis engine. It validates attached hardware evidence and reports:

- Roofline inputs and per-boundary arithmetic-intensity/ceiling calculations.
- Per-link communication observations and matching bandwidth evidence.
- Serving runtime metrics, KV-cache occupancy and thermal/throttle observations.
- GPU execution-efficiency evidence.
- Missing inputs and next measurements.
- Explicit attribution candidates with an overall verdict fixed to `undetermined`.

It does not automatically classify a bottleneck, use uncalibrated utilization thresholds, or infer missing measurements. `scripts/correlate_cross_layer_performance.py` reuses diagnosis output in strict-workload comparisons.

Run the engine against one benchmark record JSON object:

```bash
python3 scripts/diagnose_hardware_performance.py \
  --input /path/to/one-benchmark-record.json \
  --output /tmp/performance-diagnosis.json
```

## Browser workbench

The `/diagnosis/` page reads the published benchmark registry and makes evidence visible:

1. Select a published record and inspect its workload/system identity and source.
2. Inspect normalized serving metrics such as TTFT, TPOT and output throughput.
3. Inspect attached hardware profiler metric IDs, sampling scope/window and provenance.
4. Inspect runtime trace categories, clock domain and trace provenance.
5. Review mechanism-specific required/missing measurement checklists and next measurements.

The browser view is an evidence-coverage and investigation interface. It does not reimplement the Python validation/calculation engine and does not claim that the presence of a metric ID satisfies same-scope/entity, precision, directionality or temporal-alignment constraints. Those checks remain the responsibility of the diagnosis engine.

## Interpretation policy

- **Observed signal**: a value or trace event explicitly attached to the selected record.
- **Evidence input available**: a required metric ID or trace category appears in the record. This is not proof that all compatibility constraints pass.
- **Missing input**: required evidence was not supplied; it is unknown, not zero.
- **Candidate mechanism**: a path worth investigating, not an attributed bottleneck.
- **Bottleneck verdict**: remains undetermined unless a separate, validated analysis supports a causal claim.

Do not infer:
- Compute saturation from high GPU utilization.
- Memory-bandwidth saturation from DRAM activity alone.
- Critical-path communication contention from link traffic alone.
- KV-cache eviction/preemption from occupancy alone.
- Queueing, scheduler delay, CPU overhead or kernel launch gaps from TTFT/TPOT and throughput alone.

Profiler and serving metrics from different captures are not assumed to be temporally aligned.

## Validation

Browser smoke tests use deterministic fixtures to verify serving-metric rendering, profiler/trace coverage, missing-input visibility and the no-automatic-verdict guardrail. Fixture values are not production benchmark evidence.
