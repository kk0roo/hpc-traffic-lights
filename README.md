# hpc-traffic-lights

Parallel traffic light optimization using SLURM job arrays on PLGrid HPC infrastructure.

This project was prepared for the **Large Scale Computing** course. The main goal is to use traffic light management as a realistic computational use case for demonstrating HPC concepts such as batch processing, SLURM job arrays, parallel execution, resource usage analysis, and result aggregation.

The project does not aim to build a production-ready smart city traffic control system. Instead, it provides a scalable prototype in which many traffic light configurations are evaluated in parallel on a computing cluster.

---

## Project idea

Large cities contain many intersections, traffic lights, sensors, and vehicles. Optimizing traffic light schedules can be computationally expensive because each candidate configuration has to be evaluated in a traffic simulation.

In this project, each traffic light configuration is treated as an independent experiment. This makes the workload suitable for **embarrassingly parallel execution** using **SLURM array jobs**.

The general workflow is:

```text
generate traffic light configurations
        |
        v
run many independent simulations in parallel
        |
        v
collect simulation metrics
        |
        v
aggregate results
        |
        v
select the best configuration
        |
        v
visualize and analyze the results
```

Each traffic light configuration is evaluated by a **simulation backend**. The
project ships with a simple, fully functional Python simulator and a clean path
to switch to a SUMO backend later (see *Backend architecture* below).

---

## Repository structure

```text
hpc-traffic-lights/
├── README.md
├── requirements.txt
├── .gitignore
├── configs/              # traffic-light configurations (baseline + generated)
├── data/                 # synthetic network & demand (see data/README.md)
├── src/                  # all Python code
│   ├── run_simulation.py     # central entry point (backend-agnostic)
│   ├── generate_*.py         # network / demand / configs generators
│   ├── aggregate_results.py  # combine result CSVs
│   ├── select_best.py        # pick best configuration
│   ├── optimize.py           # local orchestration / quick test
│   ├── validate_outputs.py   # sanity checks
│   ├── simulators/           # backends: base, python_simulator, sumo_simulator
│   └── utils/                # io + metric schema helpers
├── slurm/                # SLURM batch + array + aggregation scripts
├── notebooks/            # analysis notebook (planned; see notebooks/README.md)
├── results/              # simulation outputs (git-ignored)
├── logs/                 # SLURM logs (git-ignored)
├── tests/                # pytest smoke tests
└── dashboard/            # optional Docker / Kubernetes dashboard
```

---

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Every script is run from the **repository root** and works with plain
`python src/<script>.py` (no installation/packaging step required).

---

## How to run (local workflow)

### 1. Generate network and demand

```bash
python src/generate_network.py
python src/generate_demand.py
```

### 2. Generate configurations

```bash
python src/generate_configs.py --n-configs 100 --output-dir configs --seed 123 --traffic-level medium
```

This writes `config_0000.json … config_0099.json`. Generation is deterministic
for a given seed.

### 3. Run a single simulation

```bash
python src/run_simulation.py \
  --backend python \
  --config configs/config_0000.json \
  --output results/result_0000.csv
```

### 4. Run the baseline

```bash
python src/run_simulation.py \
  --backend python \
  --config configs/baseline.json \
  --output results/baseline_metrics.csv \
  --network data/network/simple_grid.json \
  --demand data/demand/demand_medium.json
```

### 5. Aggregate results

```bash
python src/aggregate_results.py --input-dir results --output results/all_results.csv
```

### 6. Select the best configuration

```bash
python src/select_best.py --results results/all_results.csv --output results/best_config.json --metric avg_waiting_time
```

### 7. Validate outputs

```bash
python src/validate_outputs.py --results results/all_results.csv
```

A quick end-to-end check on a laptop (no cluster needed):

```bash
python src/optimize.py --mode local-test --n-configs 5
```

---

## How to run (SLURM / HPC workflow)

> The `--account` / `--partition` values in the SLURM scripts are PLGrid/Ares
> **examples** and almost certainly need to be adjusted for your allocation.

```bash
# 1) baseline (single job)
sbatch slurm/run_baseline.sh

# 2) evaluate many configs in parallel (job array; default 0-99)
sbatch slurm/run_array.sh

# 3) aggregate + select best + validate (run after the array finishes)
sbatch slurm/run_aggregate.sh
```

Or submit the whole dependent pipeline at once:

```bash
bash slurm/run_pipeline.sh
```

The array size defaults to `0-99` for safety. To evaluate `config_0000..0499`,
edit `#SBATCH --array=0-99` to `#SBATCH --array=0-499%50` in
`slurm/run_array.sh` (the `%50` caps concurrency).

### Estimate CPU-hours

After a job (or array) completes:

```bash
./slurm/cpu_hours.sh <JOB_ID>
```

This sums `CPUTimeRAW` from `sacct` and prints total CPU-hours.

---

## Backend architecture

The key design rule: **nothing outside `src/simulators/` depends on how a
simulator works internally.** A backend obeys one contract:

- **Input:** one JSON config (+ optional JSON network and demand files).
- **Output:** one CSV file with exactly one row using a stable metric schema
  (see `src/utils/metrics.py`).

This is why the same command works for both backends:

```bash
python src/run_simulation.py --backend python --config configs/config_0042.json --output results/result_0042.csv
python src/run_simulation.py --backend sumo   --config configs/config_0042.json --output results/result_0042.csv
```

- ✅ **`python` backend** (`src/simulators/python_simulator.py`) — implemented
  and fully functional. A simple discrete-time queueing model of one
  intersection (NS / EW green phases, lost time for yellow + all-red).
- 🚧 **`sumo` backend** (`src/simulators/sumo_simulator.py`) — **scaffolded
  only**. The class and method signatures exist and document the planned steps
  (generate SUMO XML, run `sumo -c simulation.sumocfg`, parse output into the
  same CSV schema). It currently raises a clear `NotImplementedError`.

Because both backends share the exact same input/output contract, switching to
SUMO later will **not** require changing the SLURM array workflow, the
aggregation/selection scripts, or the analysis notebook.

### Output schema

Every result CSV has exactly these columns:

```text
config_id, backend, traffic_level, cycle_length, green_ns, green_ew,
yellow_time, all_red_time, offset, simulation_duration, seed,
total_arrivals, total_departures, vehicles_remaining, avg_waiting_time,
avg_queue_length, max_queue_length, total_stops, throughput,
runtime_seconds, status
```

---

## Tests

```bash
pytest
```

The tests cover configuration constraints + determinism, the Python simulator
output schema, and result aggregation (including skipping corrupted files).

---

## Analysis stage (left for later)
See `notebooks/README.md` for the planned steps: baseline-vs-best comparison,
waiting-time distributions, runtime plots, CPU-hours estimation, and a scaling
discussion. Figures should be saved into `results/plots/`.

---

## Future development

Things that can be done in the future:

**Plug in a real traffic simulator (SUMO).** Swap our rough Python model for
SUMO using the placeholder backend we already left — turn each JSON config into
SUMO's XML, run `sumo -c simulation.sumocfg`, and read the output back into the
same CSV. Done right, nothing else in the pipeline changes.

**Use a real map instead of a toy grid.** Pull an actual road layout from
OpenStreetMap instead of the synthetic grid — starting with one neighbourhood or
the campus before attempting a whole city.

**Try smarter optimization than random search.** Replace blind random search with
an evolutionary algorithm that mutates and combines good configurations, maybe
even an island model passing solutions between nodes via MPI.

**Write the analysis notebook properly.** Compare baseline vs optimized, plot the
waiting-time distribution and per-task runtimes, total up the CPU-hours, and
comment on how the workload scales with more cores.

**Make runs reproducible with containers.** Wrap the environment in Docker for
easy local reproduction, plus an Apptainer/Singularity image for the cluster,
where Docker usually isn't allowed.

**Build out the little dashboard.** Grow the `dashboard/` placeholder into a page
that actually shows the final plots and the winning configuration, deployed on a
local Minikube.

**Add some visualization of the traffic itself.** Actually *see* the best
configuration running — a simple Matplotlib + ffmpeg animation, or rendering
frames as a Blender job array if we're feeling ambitious.

**Feed it real demand data.** Replace the made-up arrival rates with real traffic
counts or a city's open-data portal, even if we only match rough daily patterns
at first.
