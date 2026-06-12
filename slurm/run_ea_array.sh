#!/bin/bash
# EA array job: evaluate one generation of configs in parallel.
# Each array task evaluates exactly ONE configuration → ONE result file.
#
# Required env vars (set by run_ea_pipeline.sh via --export):
#   EA_GENERATION  — integer generation index (0, 1, 2, ...)
#   EA_NETWORK     — path to the pre-generated SUMO net.xml (optional; defaults below)
#
# Adjust --account / --partition for your PLGrid allocation.
#SBATCH --job-name=tl-ea-array
#SBATCH --account=plglscclass26-cpu
#SBATCH --partition=plgrid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=2G
#SBATCH --time=00:20:00
#SBATCH --array=0-49
#SBATCH --output=logs/ea_%A_gen%x_%a.out
#SBATCH --error=logs/ea_%A_gen%x_%a.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:-.}"

mkdir -p logs

EA_GENERATION=${EA_GENERATION:-0}
EA_NETWORK=${EA_NETWORK:-data/network/grid3x3.net.xml}
BACKEND=${BACKEND:-python}
CONFIGS_BASE=${CONFIGS_BASE:-configs}
OUTPUT_BASE=${OUTPUT_BASE:-results}
CONFIG_DIR="${CONFIGS_BASE}/gen_${EA_GENERATION}"
RESULTS_DIR="${OUTPUT_BASE}/gen_${EA_GENERATION}"
mkdir -p "${RESULTS_DIR}"

CONFIG_ID=$(printf "%04d" "${SLURM_ARRAY_TASK_ID}")
CONFIG_PATH="${CONFIG_DIR}/config_${CONFIG_ID}.json"
OUTPUT_PATH="${RESULTS_DIR}/result_${CONFIG_ID}.csv"

echo "Date       : $(date)"
echo "Host       : $(hostname)"
echo "Job ID     : ${SLURM_ARRAY_JOB_ID:-<none>}"
echo "Task ID    : ${SLURM_ARRAY_TASK_ID:-<none>}"
echo "Generation : ${EA_GENERATION}"
echo "Config     : ${CONFIG_PATH}"
echo "Output     : ${OUTPUT_PATH}"
echo "Network    : ${EA_NETWORK}"

# Load Python environment (adjust to your cluster setup)
# module load python/3.11
# module load SUMO/1.19.0
# source .venv/bin/activate

if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "ERROR: config file not found: ${CONFIG_PATH}" >&2
  exit 1
fi

CMD="python src/run_simulation.py \
  --backend ${BACKEND} \
  --config ${CONFIG_PATH} \
  --output ${OUTPUT_PATH} \
  --network ${EA_NETWORK}"

echo "Command : ${CMD}"
eval "${CMD}"

echo "Task ${SLURM_ARRAY_TASK_ID} (gen ${EA_GENERATION}) done."
