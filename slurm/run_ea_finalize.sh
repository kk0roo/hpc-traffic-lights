#!/bin/bash
# EA finalize job: aggregate the last generation, generate all plots and animations.
# Runs after the last array job completes.
#
# Env vars (set via --export):
#   EA_GENERATIONS — total number of generations
#   EA_NETWORK     — path to the SUMO net.xml
#   EA_SEED        — master RNG seed
#
#SBATCH --job-name=tl-ea-finalize
#SBATCH --account=plglscclass26-cpu
#SBATCH --partition=plgrid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=2G
#SBATCH --time=00:30:00
#SBATCH --output=logs/ea_finalize_%j.out
#SBATCH --error=logs/ea_finalize_%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:-.}"

EA_GENERATIONS=${EA_GENERATIONS:-6}
EA_NETWORK=${EA_NETWORK:-data/network/grid3x3.net.xml}
EA_SEED=${EA_SEED:-42}
CONFIGS_BASE=${CONFIGS_BASE:-configs}
OUTPUT_BASE=${OUTPUT_BASE:-results}
LAST_GEN=$((EA_GENERATIONS - 1))

echo "Date        : $(date)"
echo "Host        : $(hostname)"
echo "Generations : ${EA_GENERATIONS} (last = ${LAST_GEN})"

# Load Python environment (adjust to your cluster setup)
# module load python/3.11
# module load SUMO/1.19.0
# source .venv/bin/activate

mkdir -p results/plots

# 1. Aggregate the last generation's results
python src/aggregate_results.py \
  --input-dir "${OUTPUT_BASE}/gen_${LAST_GEN}" \
  --output "${OUTPUT_BASE}/gen_${LAST_GEN}/all.csv"

# 2. Generate EA progress plots
python src/plot_ea_progress.py \
  --results-dir results \
  --generations "${EA_GENERATIONS}" \
  --baseline results/baseline_metrics.csv \
  --plot-dir results/plots

# 3. Find the best config from the last generation
BEST_CONFIG=$(python - <<'PYEOF'
import sys, os, pandas as pd
sys.path.insert(0, 'src')
last_gen = int(os.environ['EA_GENERATIONS']) - 1
df = pd.read_csv(f'results/gen_{last_gen}/all.csv')
ok = df[df['status']=='ok'] if 'status' in df.columns else df
best_id = int(ok.loc[ok['avg_waiting_time'].idxmin(), 'config_id'])
print(f'configs/gen_{last_gen}/config_{best_id:04d}.json')
PYEOF
)
echo "Best config : ${BEST_CONFIG}"

# 4. Run the best config with FCD output for animation
if [[ -f "${BEST_CONFIG}" && -f "${EA_NETWORK}" ]]; then
  python src/run_simulation.py \
    --backend sumo \
    --config "${BEST_CONFIG}" \
    --network "${EA_NETWORK}" \
    --output results/ea_best_result.csv \
    --fcd-output results/trace_ea_best.xml

  # 5. Run a random (gen_0) config with FCD for comparison
  python src/run_simulation.py \
    --backend sumo \
    --config configs/gen_0/config_0000.json \
    --network "${EA_NETWORK}" \
    --output results/random_ref_result.csv \
    --fcd-output results/trace_random.xml

  # 6. Generate animations
  python src/animate_sumo.py \
    --fcd results/trace_ea_best.xml \
    --network "${EA_NETWORK}" \
    --config "${BEST_CONFIG}" \
    --output results/plots/anim_ea_best.gif \
    --title "EA Best Configuration"

  python src/animate_sumo.py \
    --fcd results/trace_random.xml \
    --network "${EA_NETWORK}" \
    --config configs/gen_0/config_0000.json \
    --output results/plots/anim_random.gif \
    --title "Random Configuration (Gen 0)"

  python src/animate_sumo.py \
    --fcd results/trace_random.xml \
    --network "${EA_NETWORK}" \
    --config configs/gen_0/config_0000.json \
    --title "Random (Gen 0)" \
    --compare-fcd results/trace_ea_best.xml \
    --compare-config "${BEST_CONFIG}" \
    --compare-title "EA Best (Gen ${LAST_GEN})" \
    --output results/plots/anim_compare.gif
else
  echo "WARNING: skipping animation (SUMO network or best config not found)."
fi

echo "=== EA Pipeline complete. Results in results/plots/ ==="
