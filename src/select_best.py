"""Select the best traffic-light configuration from aggregated results.

"Best" means the row with the minimum value of the chosen metric (lower is
better for waiting time, queue length, etc.) among rows whose status is "ok".

Example
-------
    python src/select_best.py \
        --results results/all_results.csv \
        --output results/best_config.json \
        --metric avg_waiting_time
"""

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import ensure_dir, save_json


def select_best(results_path, metric):
    """Return (best_row_dict, n_candidates) for the given metric."""
    if not os.path.exists(results_path):
        raise SystemExit(f"ERROR: results file not found: {results_path}")

    df = pd.read_csv(results_path)
    if metric not in df.columns:
        raise SystemExit(
            f"ERROR: metric '{metric}' not in results columns: {list(df.columns)}"
        )

    if "status" in df.columns:
        df = df[df["status"] == "ok"]
    if df.empty:
        raise SystemExit("ERROR: no rows with status == 'ok' to select from.")

    best_idx = df[metric].astype(float).idxmin()
    best_row = df.loc[best_idx].to_dict()
    return best_row, len(df)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Select the best configuration.")
    parser.add_argument(
        "--results", default="results/all_results.csv", help="Aggregated results CSV."
    )
    parser.add_argument(
        "--output", default="results/best_config.json", help="Output JSON path."
    )
    parser.add_argument(
        "--metric",
        default="avg_waiting_time",
        help="Metric to minimize (default: avg_waiting_time).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    best_row, n_candidates = select_best(args.results, args.metric)

    ensure_dir(args.output)
    save_json(best_row, args.output)

    print(f"[select_best] candidates (status ok) : {n_candidates}")
    print(f"[select_best] metric minimized       : {args.metric}")
    print(f"[select_best] best config_id         : {best_row.get('config_id')}")
    print(f"[select_best] best {args.metric:<18}: {best_row.get(args.metric)}")
    print(f"[select_best] saved best config to   : {args.output}")


if __name__ == "__main__":
    main()
