#!/bin/bash
# EA sensitivity analysis: vary (pop_size, n_gen) at a fixed budget of ~300 simulations.
# Each combination is ONE self-contained EA job (no fragile dependency chains).
# Usage: bash slurm/run_sensitivity_sweep.sh [SEED]

set -e

SEED=${1:-42}
BACKEND=${BACKEND:-python}
NETWORK="data/network/grid3x3.net.xml"

mkdir -p logs

declare -A COMBOS
COMBOS[300]=1
COMBOS[150]=2
COMBOS[100]=3
COMBOS[60]=5
COMBOS[50]=6
COMBOS[30]=10
COMBOS[15]=20

for POP in 300 150 100 60 50 30 15; do
    N_GEN=${COMBOS[$POP]}
    LABEL="pop${POP}_gen${N_GEN}"
    echo "[sensitivity_sweep] Submitting ${LABEL} -> results/sensitivity/${LABEL}/"

    JID=$(sbatch --parsable \
        --job-name=sens_${LABEL} \
        --export=ALL,CONFIGS_BASE=configs/sensitivity/${LABEL},OUTPUT_BASE=results/sensitivity/${LABEL},N_GEN=${N_GEN},POP_SIZE=${POP},SEED=${SEED},BACKEND=${BACKEND} \
        slurm/run_ea_single.sh)

    echo "[sensitivity_sweep]   ${LABEL} -> job ${JID}"
done

echo "[sensitivity_sweep] All jobs submitted. Monitor with: squeue -u \$USER"
echo "[sensitivity_sweep] After completion, plot locally:"
echo "  python src/experiments/plot_sensitivity.py --results-dir results/sensitivity --output-dir results/plots"
