# InferenceX decode GPU scaling efficiency

Run from the repository root:

```bash
python3 scripts/analyze_inferencex_gpu_scaling.py --output /tmp/inferencex-gpu-scaling.json
```

This first version deliberately analyzes only decode-only systems where
`physical_prefill_gpus = 0` and `physical_decode_gpus > 0`. That makes the
published `output_throughput_per_gpu` denominator unambiguous. Prefill/decode
disaggregated or mixed systems are excluded rather than silently normalizing
against an uncertain GPU population.

A series requires at least two distinct decode GPU counts and exact matching
model/workload, hardware identity, system type, single-vs-multinode flag, worker
roles, software metadata, recipe fingerprint, stable execution configuration
and evidence class. TP/EP and other stable configuration fields remain fixed.

For each observed GPU count, the report retains every source observation and
summarizes published per-GPU throughput. It also computes an **estimated**
aggregate throughput:

`estimated aggregate tok/s = median published tok/s/GPU × decode GPU count`

Relative scaling efficiency is:

`100 × estimated aggregate throughput(N) / (baseline aggregate throughput × N / baseline N)`

The baseline is the smallest observed GPU count in that exact series. 100% means
the per-GPU throughput stayed equal to baseline (linear aggregate scaling);
below 100% means per-GPU throughput declined relative to baseline. Values above
100% are possible and indicate better-than-baseline per-GPU throughput in the
observed points, not a universal hardware property.

Important limits:
- Aggregate throughput is estimated, not a directly published system total.
- Relative scaling efficiency is not SM utilization, power efficiency, or a
  causal estimate of interconnect overhead.
- This version does not analyze TP/EP changes as scaling strategies; those
  configurations are held fixed to isolate GPU-count variation.
- Single-node and multinode records are not mixed, but exact node count/topology
  may remain unavailable.
- No interpolation, extrapolation, benchmark execution, cost or power analysis.
