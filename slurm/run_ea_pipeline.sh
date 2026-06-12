#!/bin/bash
# Submit the full EA pipeline as a chain of SLURM jobs with --dependency=afterok.
#
# Usage:
#   bash slurm/run_ea_pipeline.sh [N_GENERATIONS] [POP_SIZE] [SEED]
#
# Defaults:
#   N_GENERATIONS = 6
#   POP_SIZE      = 50
#   SEED          = 42
#
# Prerequisites (run once before this script):
#   python src/generate_network.py --sumo --output data/network/grid3x3.net.xml
#   python src/generate_configs.py --n-configs 50 --output-dir configs/gen_0 \
#       --network data/network/grid3x3.net.xml --seed 42 --traffic-level medium
#
# The script prints all submitted job IDs so you can monitor them with:
#   squeue -u $USER

set -euo pipefail

N_GENERATIONS=${1:-6}
POP_SIZE=${2:-50}
SEED=${3:-42}
NETWORK=${EA_NETWORK:-data/network/grid3x3.net.xml}
CONFIGS_BASE=${CONFIGS_BASE:-configs}
OUTPUT_BASE=${OUTPUT_BASE:-results}
BACKEND=${BACKEND:-python}

echo "=== EA Pipeline ==="
echo "Generations : ${N_GENERATIONS}"
echo "Pop size    : ${POP_SIZE}"
echo "Seed        : ${SEED}"
echo "Network     : ${NETWORK}"
echo ""

LAST_STEP_JID=""

for GEN in $(seq 0 $((N_GENERATIONS - 1))); do
  # Array job: evaluate all configs for generation GEN
  ARRAY_EXPORT="EA_GENERATION=${GEN},EA_NETWORK=${NETWORK},EA_POP_SIZE=${POP_SIZE},EA_SEED=${SEED},CONFIGS_BASE=${CONFIGS_BASE},OUTPUT_BASE=${OUTPUT_BASE},BACKEND=${BACKEND}"
  ARRAY_RANGE="0-$((POP_SIZE - 1))"
  if [[ -z "${LAST_STEP_JID}" ]]; then
    ARRAY_JID=$(sbatch --parsable \
      --array="${ARRAY_RANGE}" \
      --export="${ARRAY_EXPORT}" \
      slurm/run_ea_array.sh)
  else
    ARRAY_JID=$(sbatch --parsable \
      --array="${ARRAY_RANGE}" \
      --dependency="afterok:${LAST_STEP_JID}" \
      --export="${ARRAY_EXPORT}" \
      slurm/run_ea_array.sh)
  fi
  echo "Gen ${GEN}: array job  → ${ARRAY_JID}"

  # Skip the step job after the last generation (no next gen needed)
  if [[ "${GEN}" -lt $((N_GENERATIONS - 1)) ]]; then
    STEP_EXPORT="EA_GENERATION=${GEN},EA_POP_SIZE=${POP_SIZE},EA_SEED=${SEED},CONFIGS_BASE=${CONFIGS_BASE},OUTPUT_BASE=${OUTPUT_BASE}"
    STEP_JID=$(sbatch --parsable \
      --dependency="afterok:${ARRAY_JID}" \
      --export="${STEP_EXPORT}" \
      slurm/run_ea_step.sh)
    echo "Gen ${GEN}: step job   → ${STEP_JID}"
    LAST_STEP_JID="${STEP_JID}"
  else
    LAST_STEP_JID="${ARRAY_JID}"
  fi
done

# Finalize: plots + animations
FIN_EXPORT="EA_GENERATIONS=${N_GENERATIONS},EA_NETWORK=${NETWORK},EA_SEED=${SEED},CONFIGS_BASE=${CONFIGS_BASE},OUTPUT_BASE=${OUTPUT_BASE}"
FIN_JID=$(sbatch --parsable \
  --dependency="afterok:${LAST_STEP_JID}" \
  --export="${FIN_EXPORT}" \
  slurm/run_ea_finalize.sh)
echo "Finalize job → ${FIN_JID}"
echo ""
echo "All jobs submitted. Monitor with: squeue -u \$USER"
echo "View logs in: logs/"
