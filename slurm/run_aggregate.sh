#!/bin/bash
# Aggregate results, select the best configuration, and validate outputs.
# Typically submitted with a dependency on the array job (see run_pipeline.sh).
#
# NOTE: --account / --partition values are PLGrid/Ares examples and very likely
# need to be adjusted for your allocation.
#SBATCH --job-name=tl-aggregate
#SBATCH --account=plglscclass26-cpu
#SBATCH --partition=plgrid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1G
#SBATCH --time=00:10:00
#SBATCH --output=logs/aggregate_%j.out
#SBATCH --error=logs/aggregate_%j.err

set -euo pipefail

# Run from the repository root
cd "$(dirname "$0")/.."

mkdir -p logs results

echo "Date      : $(date)"
echo "Host      : $(hostname)"
echo "Job ID    : ${SLURM_JOB_ID:-<none>}"

# if needed
#   module load python/3.11
#   source .venv/bin/activate

python src/aggregate_results.py --input-dir results --output results/all_results.csv
python src/select_best.py --results results/all_results.csv --output results/best_config.json
python src/validate_outputs.py --results results/all_results.csv

echo "Aggregation done."
