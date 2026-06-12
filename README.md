# hpc-traffic-lights

Parallel traffic light optimization using SLURM job arrays on PLGrid/Ares HPC infrastructure.

Prepared for the **Large Scale Computing** course. The goal is to demonstrate HPC concepts — batch processing, SLURM job arrays, parallel execution, resource analysis — using traffic light optimization as a realistic computational workload. Many independent traffic-light configurations are evaluated in parallel on a computing cluster; this is a textbook embarrassingly-parallel problem.

---

## Repository structure

```text
hpc-traffic-lights/
├── data/network/grid3x3.net.xml   # SUMO network (3×3 grid, generated once)
├── configs/                       # generated traffic-light configs (git-ignored)
├── results/                       # simulation outputs + plots (git-ignored)
├── logs/                          # SLURM logs (git-ignored)
├── src/
│   ├── run_simulation.py          # single entry point for all backends
│   ├── generate_network.py        # build grid3x3.net.xml with netconvert
│   ├── generate_configs.py        # random config generator
│   ├── generate_demand.py         # synthetic demand JSON
│   ├── aggregate_results.py       # merge result_*.csv → all.csv
│   ├── select_best.py             # pick best config by metric
│   ├── validate_outputs.py        # sanity-check result CSVs
│   ├── ea_next_gen.py             # EA: selection + crossover + mutation
│   ├── animate_sumo.py            # render FCD trace → GIF animation
│   ├── plot_ea_progress.py        # EA convergence plots
│   ├── simulators/
│   │   ├── base.py                # SimulationBackend ABC
│   │   ├── python_simulator.py    # pure-Python queueing model (no SUMO needed)
│   │   ├── sumo_simulator.py      # SUMO backend (requires SUMO install)
│   │   └── mc_simulator.py        # Monte Carlo π estimator
│   ├── utils/
│   │   ├── metrics.py             # RESULT_COLUMNS schema + compute_score()
│   │   ├── io.py                  # shared helpers: ensure_dir, save_json, load_json
│   │   └── network.py             # SUMO network XML parsers
│   └── experiments/
│       ├── generate_grid_configs.py   # grid search config generator
│       ├── generate_mc_configs.py     # MC config generator
│       ├── plot_scaling.py            # speedup + efficiency charts
│       ├── plot_comparison.py         # EA vs Random vs Grid
│       ├── plot_sensitivity.py        # pop_size × n_gen sensitivity
│       └── plot_mc_convergence.py     # π convergence + log-log error
├── slurm/
│   ├── run_ea_single.sh           # self-contained EA job (all gens, one SLURM job)
│   ├── run_comparison_pipeline.sh # submit Random + Grid + EA comparison
│   ├── run_sensitivity_sweep.sh   # submit all 7 EA (pop,gen) combinations
│   ├── run_scaling_sweep.sh       # submit scaling experiment for N=1…100
│   ├── run_mc_array.sh            # MC array job (500 tasks)
│   └── run_ea_pipeline.sh         # legacy: chain of array+step jobs (use ea_single instead)
└── tests/                         # pytest smoke tests
```

---

## Prerequisites

| Tool | Required for |
|------|-------------|
| Python 3.10+ | everything |
| pip packages in `requirements.txt` | everything |
| [SUMO](https://sumo.dlr.de/) ≥ 1.19 | `--backend sumo`, network generation, GIF animation |

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

All scripts are run from the **repository root** with `python src/<script>.py`.

---

## Quick start — full local workflow

Run these commands in order, once, to go from zero to plots on your local machine.

### Step 1 — Generate the SUMO network (one-time)

```bash
python src/generate_network.py --sumo --output data/network/grid3x3.net.xml
```

Creates a 3×3 grid road network used by all SUMO-backed experiments.

### Step 2 — Generate traffic-light configs

```bash
python src/generate_configs.py \
    --n-configs 50 \
    --output-dir configs/gen_0 \
    --seed 42 \
    --network data/network/grid3x3.net.xml \
    --traffic-level medium
```

Writes `configs/gen_0/config_0000.json … config_0049.json`.
Config schema: `config_id, cycle_length, green_ns, green_ew, yellow_time, all_red_time, offset, traffic_level, simulation_duration, seed`.
Constraint `green_ns + green_ew + 2·yellow_time + 2·all_red_time ≤ cycle_length` is always enforced.

### Step 3 — Run a single simulation

```bash
# Python backend (no SUMO needed, fast)
python src/run_simulation.py \
    --backend python \
    --config configs/gen_0/config_0000.json \
    --output results/result_0000.csv

# SUMO backend (realistic, requires SUMO)
python src/run_simulation.py \
    --backend sumo \
    --config configs/gen_0/config_0000.json \
    --network data/network/grid3x3.net.xml \
    --output results/result_0000.csv
```

Both produce one CSV row with the same schema (see *Output schema* below).

### Step 4 — Aggregate results

```bash
python src/aggregate_results.py --input-dir results --output results/all.csv
```

### Step 5 — Select the best config

```bash
python src/select_best.py \
    --results results/all.csv \
    --output results/best_config.json \
    --metric avg_waiting_time
```

### Step 6 — Validate outputs

```bash
python src/validate_outputs.py --results results/all.csv
```

---

## Visualize the simulation (GIF animation)

You can generate an animated GIF of vehicles moving through the grid intersection.
**Requires SUMO** — the simulation must be run with `--fcd-output` to capture per-vehicle traces.

### 1. Run the simulation with trace output

```bash
mkdir -p results/vis
python src/run_simulation.py \
    --backend sumo \
    --config results/best_config.json \
    --network data/network/grid3x3.net.xml \
    --output results/vis/best_result.csv \
    --fcd-output results/vis/trace_best.xml
```

### 2. Generate the GIF

```bash
python src/animate_sumo.py \
    --fcd results/vis/trace_best.xml \
    --network data/network/grid3x3.net.xml \
    --config results/best_config.json \
    --output results/plots/anim_best.gif \
    --title "Best EA configuration"
```

### 3. Side-by-side comparison (best vs. random)

```bash
# First run a random (gen_0) config too
python src/run_simulation.py \
    --backend sumo \
    --config configs/gen_0/config_0000.json \
    --network data/network/grid3x3.net.xml \
    --output results/vis/random_result.csv \
    --fcd-output results/vis/trace_random.xml

# Compare in one GIF
python src/animate_sumo.py \
    --fcd            results/vis/trace_random.xml \
    --config         configs/gen_0/config_0000.json \
    --title          "Random (gen 0)" \
    --compare-fcd    results/vis/trace_best.xml \
    --compare-config results/best_config.json \
    --compare-title  "EA Best" \
    --network        data/network/grid3x3.net.xml \
    --output         results/plots/anim_compare.gif
```

---

## Evolutionary Algorithm (EA) — local run

EA iteratively improves a population of configs using truncation selection, uniform crossover, and Gaussian mutation.

### Run EA locally (all generations in one go)

```bash
# Generate initial population (gen_0)
python src/generate_configs.py \
    --n-configs 50 \
    --output-dir configs/ea/gen_0 \
    --seed 42 \
    --network data/network/grid3x3.net.xml \
    --traffic-level medium

# Evaluate gen_0
mkdir -p results/ea/gen_0
for i in $(seq 0 49); do
    python src/run_simulation.py --backend python \
        --config configs/ea/gen_0/config_$(printf '%04d' $i).json \
        --output results/ea/gen_0/result_$(printf '%04d' $i).csv
done
python src/aggregate_results.py \
    --input-dir results/ea/gen_0 --output results/ea/gen_0/all.csv

# Breed gen_1 from gen_0
python src/ea_next_gen.py \
    --generation 0 \
    --results-dir results/ea/gen_0 \
    --config-dir  configs/ea/gen_0 \
    --output-dir  configs/ea/gen_1 \
    --pop-size 50 --seed 42

# Repeat evaluate → breed for each subsequent generation
```

### Plot EA progress

```bash
python src/plot_ea_progress.py \
    --results-dir results/ea \
    --generations 6 \
    --plot-dir results/plots
```

---

## Experiments

Four experiments are included. All results land in `results/` and plots in `results/plots/`.

---

### Experiment 1 — Scaling analysis

Measures speedup and efficiency as the number of parallel workers increases (strong scaling: fixed 100 configs, vary N workers).

#### On Ares (SLURM)

```bash
# Generate 100 configs once
python src/generate_configs.py --n-configs 100 --output-dir configs/scaling \
    --seed 1 --network data/network/grid3x3.net.xml --traffic-level medium

# Submit all scaling levels (N = 1, 2, 5, 10, 20, 50, 100)
bash slurm/run_scaling_sweep.sh
```

#### Plot (run locally after pulling results)

```bash
python src/experiments/plot_scaling.py \
    --results-dir results/scaling \
    --output-dir  results/plots
# → results/plots/scaling.png
```

---

### Experiment 2 — EA vs Random Search vs Grid Search

Equal budget of 300 simulations per method. Which finds a better traffic-light schedule?

#### On Ares (SLURM)

```bash
# Submits Random (300 tasks) + Grid (~72 tasks) + EA (50 individuals × 6 gen) simultaneously
bash slurm/run_comparison_pipeline.sh
```

#### Plot (run locally after pulling results)

```bash
python src/experiments/plot_comparison.py \
    --random  results/comparison/random/all.csv \
    --grid    results/comparison/grid/all.csv \
    --ea      results/comparison/ea/gen_5/all.csv \
    --ea-dir  results/comparison/ea \
    --output-dir results/plots
# → results/plots/search_comparison.png
```

---

### Experiment 3 — EA sensitivity analysis

Fixed budget of 300 simulations; 7 combinations of `(pop_size, n_gen)`:

| pop_size | n_gen | total sims |
|----------|-------|-----------|
| 300 | 1 | 300 |
| 150 | 2 | 300 |
| 100 | 3 | 300 |
| 60  | 5 | 300 |
| 50  | 6 | 300 |
| 30  | 10 | 300 |
| 15  | 20 | 300 |

#### On Ares (SLURM)

```bash
bash slurm/run_sensitivity_sweep.sh
```

#### Plot (run locally after pulling results)

```bash
python src/experiments/plot_sensitivity.py \
    --results-dir results/sensitivity \
    --output-dir  results/plots
# → results/plots/sensitivity.png
```

---

### Experiment 4 — Monte Carlo π estimation

Pure embarrassingly-parallel baseline (no SUMO needed). Each task estimates π by the hit-or-miss method. Used to compare ideal parallelism (MC) vs. barrier-synchronised parallelism (EA).

#### On Ares (SLURM)

```bash
# Generate 500 MC configs (one-time)
python src/experiments/generate_mc_configs.py \
    --n-configs 500 --n-samples 100000 --output-dir configs/mc

mkdir -p results/mc
sbatch slurm/run_mc_array.sh
```

#### Plot (run locally after pulling results)

```bash
python src/experiments/plot_mc_convergence.py \
    --results-dir results/mc \
    --ea-dir      results/comparison/ea \
    --output-dir  results/plots
# → results/plots/mc_convergence.png
```

---

### Generate all plots at once (after pulling results from Ares)

```bash
python src/experiments/plot_scaling.py \
    --results-dir results/scaling --output-dir results/plots

python src/experiments/plot_comparison.py \
    --random  results/comparison/random/all.csv \
    --grid    results/comparison/grid/all.csv \
    --ea      results/comparison/ea/gen_5/all.csv \
    --ea-dir  results/comparison/ea \
    --output-dir results/plots

python src/experiments/plot_sensitivity.py \
    --results-dir results/sensitivity --output-dir results/plots

python src/experiments/plot_mc_convergence.py \
    --results-dir results/mc \
    --ea-dir      results/comparison/ea \
    --output-dir  results/plots
```

| Plot file | What it shows |
|-----------|---------------|
| `results/plots/scaling.png` | Speedup and efficiency vs. number of workers |
| `results/plots/search_comparison.png` | Bar chart + CDF + learning curve: EA vs Random vs Grid |
| `results/plots/sensitivity.png` | Best fitness vs pop\_size and n\_gen |
| `results/plots/mc_convergence.png` | π convergence, log-log error, MC vs EA speedup |

---

## Full HPC workflow (Ares / PLGrid)

End-to-end from a clean home directory on the cluster.

```bash
# 0. Upload the repo (from your local machine)
#    git push origin final   (then on Ares:)
git clone <repo-url>   # or: git pull origin final
cd hpc-traffic-lights

# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Generate the SUMO network (one-time)
python src/generate_network.py --sumo --output data/network/grid3x3.net.xml

# 3. Run all four experiments (submit SLURM jobs)
bash slurm/run_scaling_sweep.sh        # Experiment 1
bash slurm/run_comparison_pipeline.sh  # Experiment 2
bash slurm/run_sensitivity_sweep.sh    # Experiment 3

python src/experiments/generate_mc_configs.py \
    --n-configs 500 --n-samples 100000 --output-dir configs/mc
mkdir -p results/mc
sbatch slurm/run_mc_array.sh           # Experiment 4

# 4. Monitor jobs
squeue -u $USER

# 5. After all jobs finish — commit results and push
git add results/ configs/
git commit -m "Add experiment results"
git push origin final

# 6. On your local machine — pull and plot
git pull origin final
python src/experiments/plot_scaling.py     --results-dir results/scaling    --output-dir results/plots
python src/experiments/plot_comparison.py  --random results/comparison/random/all.csv --grid results/comparison/grid/all.csv --ea results/comparison/ea/gen_5/all.csv --ea-dir results/comparison/ea --output-dir results/plots
python src/experiments/plot_sensitivity.py --results-dir results/sensitivity --output-dir results/plots
python src/experiments/plot_mc_convergence.py --results-dir results/mc --ea-dir results/comparison/ea --output-dir results/plots
```

---

## Backend architecture

The design rule: **nothing outside `src/simulators/` knows how a simulator works internally.**

Every backend implements the same contract:
- **Input:** one JSON config file (+ optional network path)
- **Output:** one CSV row matching `RESULT_COLUMNS` from `src/utils/metrics.py`

```bash
# Both commands produce identical output format
python src/run_simulation.py --backend python --config configs/gen_0/config_0000.json --output results/r.csv
python src/run_simulation.py --backend sumo   --config configs/gen_0/config_0000.json --output results/r.csv --network data/network/grid3x3.net.xml
python src/run_simulation.py --backend mc     --config configs/mc/config_0000.json    --output results/r.csv
```

| Backend | Description |
|---------|-------------|
| `python` | Discrete-time queueing model. Fast (~0.01 s/sim), no external dependencies. |
| `sumo` | Realistic microscopic traffic simulation via SUMO. ~3 s/sim. Requires SUMO install. |
| `mc` | Monte Carlo π estimator. Used for pure embarrassingly-parallel benchmarking. |

### Adding a new backend

1. Create `src/simulators/my_simulator.py` subclassing `SimulationBackend` from `src/simulators/base.py`
2. Implement `run(config_path, output_path, network_path, demand_path)` — write exactly one CSV row
3. Register it in the `BACKENDS` dict in `src/run_simulation.py`

### Output schema

Every result CSV has these columns:

```
config_id, backend, traffic_level, cycle_length, green_ns, green_ew,
yellow_time, all_red_time, offset, simulation_duration, seed,
total_arrivals, total_departures, vehicles_remaining,
avg_waiting_time, avg_queue_length, max_queue_length,
total_stops, throughput, runtime_seconds, status
```

The objective is to minimise `avg_waiting_time`. The `status` column is `"ok"` on success or `"error"` on failure (SUMO backend never crashes — failures are recorded, not propagated).

---

## Tests

```bash
pytest                                        # all tests
pytest tests/test_python_simulator.py         # single file
```

---

## SLURM scripts reference

| Script | Purpose |
|--------|---------|
| `slurm/run_ea_single.sh` | Self-contained EA: all generations inside one job, parallelism via background `&` + `wait`. Configure via env vars: `N_GEN`, `POP_SIZE`, `SEED`, `BACKEND`, `CONFIGS_BASE`, `OUTPUT_BASE`. |
| `slurm/run_comparison_pipeline.sh` | Submit Random + Grid + EA comparison (equal 300-sim budget each). |
| `slurm/run_sensitivity_sweep.sh` | Submit all 7 `(pop_size, n_gen)` EA variants. |
| `slurm/run_scaling_sweep.sh` | Submit scaling experiment for N = 1, 2, 5, 10, 20, 50, 100 workers. |
| `slurm/run_mc_array.sh` | 500-task MC array job (`--backend mc`). |
| `slurm/run_ea_pipeline.sh` | Legacy chain of `afterok` dependencies (use `run_ea_single.sh` instead). |
