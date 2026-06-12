#!/bin/bash
# EA vs Random vs Grid Search comparison with equal budget (~300 simulations each).
# Random + Grid run as single (throttled) array jobs; EA runs as ONE self-contained job.
# Usage: bash slurm/run_comparison_pipeline.sh [SEED]

set -e

SEED=${1:-42}
BUDGET=300
POP_SIZE=50
N_GEN=6
BACKEND=${BACKEND:-python}
NETWORK="data/network/grid3x3.net.xml"
ACCOUNT="plglscclass26-cpu"
PARTITION="plgrid"

echo "[comparison] Seed=${SEED}, budget=${BUDGET} sims each, backend=${BACKEND}."

echo "[comparison] Generating Random Search configs (n=${BUDGET})..."
python src/generate_configs.py \
    --n-configs $BUDGET \
    --output-dir configs/comparison/random \
    --seed $SEED \
    --network $NETWORK \
    --traffic-level medium

echo "[comparison] Generating Grid Search configs..."
python src/experiments/generate_grid_configs.py \
    --output-dir configs/comparison/grid \
    --seed $SEED \
    --network $NETWORK \
    --traffic-level medium \
    --n-offset-sets 3

mkdir -p results/comparison/random results/comparison/grid logs

echo "[comparison] Submitting Random Search array job..."
JOB_RANDOM=$(sbatch \
    --parsable \
    --job-name=cmp_random \
    --partition=$PARTITION \
    --account=$ACCOUNT \
    --time=01:00:00 \
    --mem-per-cpu=1G \
    --array=0-$((BUDGET - 1))%50 \
    --output=logs/cmp_random_%a.log \
    --wrap="python src/run_simulation.py \
        --backend $BACKEND \
        --network $NETWORK \
        --config configs/comparison/random/config_\$(printf '%04d' \$SLURM_ARRAY_TASK_ID).json \
        --output results/comparison/random/result_\$(printf '%04d' \$SLURM_ARRAY_TASK_ID).csv")

GRID_N=$(ls configs/comparison/grid/config_*.json 2>/dev/null | wc -l || echo 0)
echo "[comparison] Submitting Grid Search array job (${GRID_N} configs)..."
JOB_GRID=$(sbatch \
    --parsable \
    --job-name=cmp_grid \
    --partition=$PARTITION \
    --account=$ACCOUNT \
    --time=01:00:00 \
    --mem-per-cpu=1G \
    --array=0-$((GRID_N - 1))%50 \
    --output=logs/cmp_grid_%a.log \
    --wrap="python src/run_simulation.py \
        --backend $BACKEND \
        --network $NETWORK \
        --config configs/comparison/grid/config_\$(printf '%04d' \$SLURM_ARRAY_TASK_ID).json \
        --output results/comparison/grid/result_\$(printf '%04d' \$SLURM_ARRAY_TASK_ID).csv")

echo "[comparison] Submitting EA single job (${N_GEN} generations, pop=${POP_SIZE})..."
JOB_EA=$(CONFIGS_BASE=configs/comparison/ea OUTPUT_BASE=results/comparison/ea \
    N_GEN=$N_GEN POP_SIZE=$POP_SIZE SEED=$((SEED + 1000)) BACKEND=$BACKEND \
    sbatch --parsable \
        --export=ALL,CONFIGS_BASE=configs/comparison/ea,OUTPUT_BASE=results/comparison/ea,N_GEN=$N_GEN,POP_SIZE=$POP_SIZE,SEED=$((SEED + 1000)),BACKEND=$BACKEND \
        slurm/run_ea_single.sh)

echo "[comparison] Jobs submitted: random=${JOB_RANDOM} grid=${JOB_GRID} ea=${JOB_EA}"
echo "[comparison] Monitor with: squeue -u \$USER"
echo "[comparison] After all complete, aggregate + plot locally:"
echo "  python src/aggregate_results.py --input-dir results/comparison/random --output results/comparison/random/all.csv"
echo "  python src/aggregate_results.py --input-dir results/comparison/grid --output results/comparison/grid/all.csv"
echo "  python src/experiments/plot_comparison.py \\"
echo "    --random results/comparison/random/all.csv \\"
echo "    --grid results/comparison/grid/all.csv \\"
echo "    --ea results/comparison/ea/gen_$((N_GEN - 1))/all.csv \\"
echo "    --ea-dir results/comparison/ea \\"
echo "    --output-dir results/plots"
