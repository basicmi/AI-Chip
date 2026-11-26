# Performance Experiment Planner

The planner converts one benchmark record and its evidence-constrained diagnosis into a set of falsifiable investigation plans. It does not run benchmarks, change production configurations, rank hypotheses or claim that a candidate is the bottleneck.

## Generate a plan

Start with a single record JSON object from the benchmark registry:

```bash
python3 scripts/build_performance_experiment_plan.py \
  --input /path/to/one-benchmark-record.json \
  --output /tmp/performance-experiment-plan.json \
  --markdown /tmp/performance-experiment-plan.md \
  --repetitions 3
```

The tool calls the existing `diagnose_record()` engine itself, verifies that the diagnosis refers to the same record and that its overall verdict remains `undetermined`, then generates one or more experiment proposals from the returned candidates.

## Plan contents

Each proposal contains:

- A starting observation and evidence status.
- A hypothesis and a falsifiable question.
- A baseline anchored to the selected record's model, workload, hardware, software recipe and configuration.
- A proposed single-factor intervention. The exact parameter and value are deliberately left for an engineer to specify.
- Control conditions and required measurements.
- Results that would support or weaken the hypothesis.
- Interpretation limits and a run/repetition policy.
- An execution state fixed to `performed: false`, `result: not_run`.

Supported investigation families include compute/roofline, memory movement, interconnect, KV-cache capacity/allocator behavior, thermal/power throttling and runtime scheduling/queueing. Missing evidence produces an evidence-acquisition proposal rather than an invented tuning experiment.

## Experimental discipline

1. Reproduce the selected baseline first. If it cannot be reproduced, mark the experiment blocked; do not substitute an unmatched run.
2. Predeclare one primary outcome and practical effect size before running.
3. Change one factor at a time. Record the exact parameter/value and keep all other declared controls fixed.
4. Randomize or interleave baseline/treatment runs where practical; report every valid, failed and invalid run.
5. Report dispersion, offered load and workload identity. A default of three repetitions is a planning aid, not a guarantee of statistical power.
6. Do not infer causality if hardware identity, software recipe, workload, measurement boundary or time alignment changes.
7. Treat the plan as a proposal only. A human engineer must review and execute it in a separate controlled environment.

## Guardrails

- No automatic benchmark execution or hardware control.
- No automatic hypothesis ranking or bottleneck verdict.
- No universal utilization thresholds or ungrounded pass/fail criteria.
- Missing evidence is unknown, not zero.
- A candidate mechanism is not an attributed cause.
