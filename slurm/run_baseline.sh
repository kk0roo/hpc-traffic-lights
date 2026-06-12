#!/bin/bash
# Run the single baseline configuration on the cluster.
#
# NOTE: --account / --partition values are PLGrid/Ares examples and very likely
# need to be adjusted for your allocation.
#SBATCH --job-name=tl-baseline
#SBATCH --account=plglscclass26-cpu
#SBATCH --partition=plgrid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1G
#SBATCH --time=00:10:00
#SBATCH --output=logs/baseline_%j.out
#SBATCH --error=logs/baseline_%j.err

set -euo pipefail

# Run from the repository root
cd "$(dirname "$0")/.."

mkdir -p logs results

echo "Date      : $(date)"
echo "Host      : $(hostname)"
echo "Job ID    : ${SLURM_JOB_ID:-<none>}"

# Python environment if needed
#   module load python/3.11
#   source .venv/bin/activate

CMD="python src/run_simulation.py \
  --backend python \
  --config configs/baseline.json \
  --output results/baseline_metrics.csv \
  --network data/network/simple_grid.json \
  --demand data/demand/demand_medium.json"

echo "Command   : ${CMD}"
eval "${CMD}"

echo "Baseline done."
