#!/bin/bash
# Submits strong-scaling jobs for N = 1, 2, 5, 10, 20, 50, 100 workers.
# Usage: bash slurm/run_scaling_sweep.sh

set -e

WORKERS=(1 2 5 10 20 50 100)

echo "[run_scaling_sweep] Generating 100 configs for scaling experiment..."
python src/generate_configs.py \
    --n-configs 100 \
    --output-dir configs/scaling \
    --seed 1 \
    --network data/network/grid3x3.net.xml \
    --traffic-level medium

for N in "${WORKERS[@]}"; do
    mkdir -p "results/scaling/strong_n${N}"
    echo "[run_scaling_sweep] Submitting N=${N} workers..."
    sbatch --export=ALL,N_WORKERS=${N} slurm/run_scaling_strong.sh
done

echo "[run_scaling_sweep] All jobs submitted. Monitor with: squeue -u \$USER"
echo "[run_scaling_sweep] After completion, plot with:"
echo "  python src/experiments/plot_scaling.py --results-dir results/scaling --output-dir results/plots"
