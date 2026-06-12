#!/bin/bash
# EA step job: aggregate results for generation N and generate configs for N+1.
# Runs after the array job for generation N completes (--dependency=afterok:$JOB_ID).
#
# Required env vars (set via --export):
#   EA_GENERATION  — integer index of the just-completed generation
#   EA_POP_SIZE    — population size for the next generation (default 50)
#   EA_SEED        — master RNG seed (default 42)
#
#SBATCH --job-name=tl-ea-step
#SBATCH --account=plglscclass26-cpu
#SBATCH --partition=plgrid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/ea_step_%j_gen%x.out
#SBATCH --error=logs/ea_step_%j_gen%x.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:-.}"

EA_GENERATION=${EA_GENERATION:-0}
EA_POP_SIZE=${EA_POP_SIZE:-50}
EA_SEED=${EA_SEED:-42}
NEXT_GEN=$((EA_GENERATION + 1))
CONFIGS_BASE=${CONFIGS_BASE:-configs}
OUTPUT_BASE=${OUTPUT_BASE:-results}

RESULTS_DIR="${OUTPUT_BASE}/gen_${EA_GENERATION}"
CONFIG_DIR="${CONFIGS_BASE}/gen_${EA_GENERATION}"
NEXT_CONFIG_DIR="${CONFIGS_BASE}/gen_${NEXT_GEN}"

echo "Date       : $(date)"
echo "Host       : $(hostname)"
echo "Generation : ${EA_GENERATION} → ${NEXT_GEN}"

# Load Python environment (adjust to your cluster setup)
# module load python/3.11
# source .venv/bin/activate

# 1. Aggregate results for completed generation
python src/aggregate_results.py \
  --input-dir "${RESULTS_DIR}" \
  --output "${RESULTS_DIR}/all.csv"

# 2. Generate next generation configs via EA operators
python src/ea_next_gen.py \
  --generation "${EA_GENERATION}" \
  --results-dir "${RESULTS_DIR}" \
  --config-dir "${CONFIG_DIR}" \
  --output-dir "${NEXT_CONFIG_DIR}" \
  --pop-size "${EA_POP_SIZE}" \
  --seed "${EA_SEED}"

echo "EA step for generation ${EA_GENERATION} done. Gen ${NEXT_GEN} configs ready."
