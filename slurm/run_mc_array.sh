#!/bin/bash
#SBATCH --job-name=mc_pi
#SBATCH --partition=plgrid
#SBATCH --account=plglscclass26-cpu
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --array=0-499
#SBATCH --output=results/mc/slurm_%a.log
#SBATCH --error=results/mc/slurm_%a.err

set -e

TASK_ID=$SLURM_ARRAY_TASK_ID
N_CONFIGS=${N_CONFIGS:-500}
N_SAMPLES=${N_SAMPLES:-100000}
CONFIG_DIR=${CONFIG_DIR:-configs/mc}
RESULTS_DIR=${RESULTS_DIR:-results/mc}

CONFIG=$(printf "${CONFIG_DIR}/config_%04d.json" $TASK_ID)
OUTPUT=$(printf "${RESULTS_DIR}/result_%04d.csv" $TASK_ID)

mkdir -p "$RESULTS_DIR"

python src/run_simulation.py \
    --backend mc \
    --config "$CONFIG" \
    --output "$OUTPUT"
