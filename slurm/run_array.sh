#!/bin/bash
# Evaluate many configurations in parallel using a SLURM job array.
# Each array task evaluates exactly ONE configuration -> ONE result file.
#
# NOTE: --account / --partition values are PLGrid/Ares examples and very likely
# need to be adjusted for your allocation.
#
# The array range below is 0-99 to stay safe. To evaluate config_0000..config_0499
# change it to:   #SBATCH --array=0-499%50
# (the %50 limits how many run concurrently).
#SBATCH --job-name=tl-array
#SBATCH --account=plglscclass26-cpu
#SBATCH --partition=plgrid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1G
#SBATCH --time=00:10:00
#SBATCH --array=0-99
#SBATCH --output=logs/traffic_%A_%a.out
#SBATCH --error=logs/traffic_%A_%a.err

set -euo pipefail

# Run from the repository root
cd "$(dirname "$0")/.."

mkdir -p logs results

CONFIG_DIR=${CONFIG_DIR:-configs}
RESULTS_DIR=${RESULTS_DIR:-results}
BACKEND=${BACKEND:-python}

CONFIG_ID=$(printf "%04d" "${SLURM_ARRAY_TASK_ID}")
CONFIG_PATH="${CONFIG_DIR}/config_${CONFIG_ID}.json"
OUTPUT_PATH="${RESULTS_DIR}/result_${CONFIG_ID}.csv"

echo "Date      : $(date)"
echo "Host      : $(hostname)"
echo "Job ID    : ${SLURM_ARRAY_JOB_ID:-<none>}"
echo "Task ID   : ${SLURM_ARRAY_TASK_ID:-<none>}"
echo "Config    : ${CONFIG_PATH}"
echo "Output    : ${OUTPUT_PATH}"

# Python environment if needed
#   module load python/3.11
#   source .venv/bin/activate

if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "ERROR: config file not found: ${CONFIG_PATH}" >&2
  exit 1
fi

CMD="python src/run_simulation.py \
  --backend ${BACKEND} \
  --config ${CONFIG_PATH} \
  --output ${OUTPUT_PATH} \
  --network data/network/simple_grid.json \
  --demand data/demand/demand_medium.json"

echo "Command   : ${CMD}"
eval "${CMD}"

echo "Task ${SLURM_ARRAY_TASK_ID} done."
