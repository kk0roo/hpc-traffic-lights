#!/bin/bash
# Submitter script (NOT an sbatch job itself).
# Submits the array job and an aggregation job that runs only after the array
# completes successfully, using SLURM job dependencies.
#
# Usage:
#   bash slurm/run_pipeline.sh
#
# Optionally submit the baseline first; it is independent of the array.

set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p logs results

echo "Submitting baseline job..."
JID_BASE=$(sbatch --parsable slurm/run_baseline.sh)
echo "  baseline job id : ${JID_BASE}"

echo "Submitting array job..."
JID_ARRAY=$(sbatch --parsable slurm/run_array.sh)
echo "  array job id    : ${JID_ARRAY}"

echo "Submitting aggregation job (after array completes OK)..."
JID_AGG=$(sbatch --parsable --dependency=afterok:"${JID_ARRAY}" slurm/run_aggregate.sh)
echo "  aggregate job id: ${JID_AGG}"

echo
echo "Submitted jobs:"
echo "  baseline  : ${JID_BASE}"
echo "  array     : ${JID_ARRAY}"
echo "  aggregate : ${JID_AGG} (depends on ${JID_ARRAY})"
echo
echo "Estimate CPU-hours afterwards with:  ./slurm/cpu_hours.sh ${JID_ARRAY}"
