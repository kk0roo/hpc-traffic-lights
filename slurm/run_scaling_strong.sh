#!/bin/bash
#SBATCH --job-name=scaling_strong
#SBATCH --partition=plgrid
#SBATCH --account=plglscclass26-cpu
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --array=0-99%${N_WORKERS:-1}
#SBATCH --output=results/scaling/strong_n${N_WORKERS:-1}/slurm_%a.log
#SBATCH --error=results/scaling/strong_n${N_WORKERS:-1}/slurm_%a.err

set -e

N=${N_WORKERS:-1}
TASK_ID=$SLURM_ARRAY_TASK_ID
CONFIG=$(printf "configs/scaling/config_%04d.json" $TASK_ID)
OUTPUT=$(printf "results/scaling/strong_n${N}/result_%04d.csv" $TASK_ID)

mkdir -p "results/scaling/strong_n${N}"

module load SUMO 2>/dev/null || true

python src/run_simulation.py \
    --backend sumo \
    --network data/network/grid3x3.net.xml \
    --config "$CONFIG" \
    --output "$OUTPUT"
