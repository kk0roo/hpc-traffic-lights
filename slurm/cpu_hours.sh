#!/bin/bash
# Estimate total CPU-hours consumed by a (completed) SLURM job or array.
# Usage:
#   ./slurm/cpu_hours.sh <JOB_ID>
#
# It sums CPUTimeRAW (CPU-seconds) across all job steps reported by sacct and
# converts the total to CPU-hours. Run this AFTER the job has finished.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <JOB_ID>" >&2
  exit 1
fi

JOB_ID="$1"

TOTAL_CPU_SECONDS=$(sacct -j "${JOB_ID}" -X --noheader --parsable2 \
  --format=CPUTimeRAW | awk '{ sum += $1 } END { print sum + 0 }')

CPU_HOURS=$(awk -v s="${TOTAL_CPU_SECONDS}" 'BEGIN { printf "%.4f", s / 3600.0 }')

echo "Job ID          : ${JOB_ID}"
echo "Total CPU-seconds: ${TOTAL_CPU_SECONDS}"
echo "Total CPU-hours  : ${CPU_HOURS}"
