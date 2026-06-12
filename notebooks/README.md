# Notebooks

The final analysis notebook is intentionally **left for later work**. This file
describes what that notebook should contain so the analysis stage has a clear
plan.

## Inputs

- `results/baseline_metrics.csv` — metrics for the baseline configuration.
- `results/all_results.csv` — aggregated metrics for all evaluated configs.
- `results/best_config.json` — the selected best configuration.

## Suggested analysis steps

1. **Load data** with pandas (`baseline_metrics.csv`, `all_results.csv`).
2. **Baseline vs best** — compare `avg_waiting_time`, `avg_queue_length`,
   `throughput` between the baseline and the selected best configuration.
3. **Distribution plots** — histogram / boxplot of `avg_waiting_time` across all
   configurations.
4. **Runtime plot** — distribution of `runtime_seconds` per task (workload
   characterization).
5. **CPU-hours estimate** — combine task runtimes (or `sacct` CPUTimeRAW via
   `slurm/cpu_hours.sh`) into a total CPU-hours figure.
6. **Scaling discussion** — how wall-clock time changes with the number of
   parallel array tasks (embarrassingly parallel workload).
7. **Interpretation** — which signal settings tend to reduce waiting time, and
   the limitations of the simplified model.

Save generated figures into `results/plots/`.

> A full, polished notebook is part of the future analysis stage; placeholders
> and this plan are provided on purpose.
