#!/bin/bash
# Self-contained EA run: all generations inside ONE SLURM job.
# Each generation's configs are evaluated in parallel across the job's CPU cores.
# This avoids fragile afterok dependency chains and stays within submit limits.
#
# Configure via env vars (all optional):
#   N_GEN         number of generations          (default 6)
#   POP_SIZE      population size per generation  (default 50)
#   SEED          master RNG seed                 (default 42)
#   BACKEND       python | sumo                   (default python)
#   NETWORK       SUMO net.xml path               (default data/network/grid3x3.net.xml)
#   CONFIGS_BASE  base dir for gen_* configs      (default configs/ea_run)
#   OUTPUT_BASE   base dir for gen_* results      (default results/ea_run)
#
# Example:
#   CONFIGS_BASE=configs/comparison/ea OUTPUT_BASE=results/comparison/ea \
#     N_GEN=6 POP_SIZE=50 SEED=1042 sbatch slurm/run_ea_single.sh
#
#SBATCH --job-name=ea-single
#SBATCH --account=plglscclass26-cpu
#SBATCH --partition=plgrid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --mem-per-cpu=1G
#SBATCH --time=01:00:00
#SBATCH --output=logs/ea_single_%j.out
#SBATCH --error=logs/ea_single_%j.err

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"

N_GEN=${N_GEN:-6}
POP_SIZE=${POP_SIZE:-50}
SEED=${SEED:-42}
BACKEND=${BACKEND:-python}
NETWORK=${NETWORK:-data/network/grid3x3.net.xml}
CONFIGS_BASE=${CONFIGS_BASE:-configs/ea_run}
OUTPUT_BASE=${OUTPUT_BASE:-results/ea_run}
NPROC=${SLURM_CPUS_PER_TASK:-4}

mkdir -p logs

echo "[ea_single] N_GEN=${N_GEN} POP_SIZE=${POP_SIZE} SEED=${SEED} BACKEND=${BACKEND} NPROC=${NPROC}"
echo "[ea_single] CONFIGS_BASE=${CONFIGS_BASE} OUTPUT_BASE=${OUTPUT_BASE}"

if [[ ! -f "${CONFIGS_BASE}/gen_0/config_0000.json" ]]; then
  echo "[ea_single] generating initial population (gen_0)..."
  python src/generate_configs.py \
    --n-configs "${POP_SIZE}" \
    --output-dir "${CONFIGS_BASE}/gen_0" \
    --seed "${SEED}" \
    --network "${NETWORK}" \
    --traffic-level medium
fi

for GEN in $(seq 0 $((N_GEN - 1))); do
  CDIR="${CONFIGS_BASE}/gen_${GEN}"
  RDIR="${OUTPUT_BASE}/gen_${GEN}"
  mkdir -p "${RDIR}"

  N_CFG=$(ls "${CDIR}"/config_*.json 2>/dev/null | wc -l)
  echo "[ea_single] gen ${GEN}: evaluating ${N_CFG} configs on ${NPROC} cores"

  running=0
  for f in "${CDIR}"/config_*.json; do
    id=$(basename "${f}" .json | sed 's/config_//')
    python src/run_simulation.py \
      --backend "${BACKEND}" \
      --config "${f}" \
      --output "${RDIR}/result_${id}.csv" \
      --network "${NETWORK}" &
    running=$((running + 1))
    if (( running % NPROC == 0 )); then
      wait
    fi
  done
  wait

  python src/aggregate_results.py --input-dir "${RDIR}" --output "${RDIR}/all.csv"

  if [[ "${GEN}" -lt $((N_GEN - 1)) ]]; then
    python src/ea_next_gen.py \
      --generation "${GEN}" \
      --results-dir "${RDIR}" \
      --config-dir "${CDIR}" \
      --output-dir "${CONFIGS_BASE}/gen_$((GEN + 1))" \
      --pop-size "${POP_SIZE}" \
      --seed "${SEED}"
  fi
done

echo "[ea_single] done. Results in ${OUTPUT_BASE}/gen_0 .. gen_$((N_GEN - 1))"
