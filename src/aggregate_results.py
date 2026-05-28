"""Aggregate many per-configuration result CSVs into a single table.

Reads every ``result_*.csv`` in the input directory, concatenates them, sorts
by ``config_id`` when possible, and writes one combined CSV.

Example
-------
    python src/aggregate_results.py --input-dir results --output results/all_results.csv
"""

import argparse
import glob
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import ensure_dir
EXCLUDED_BASENAMES = {"all_results.csv", "baseline_metrics.csv"}


def find_result_files(input_dir):
    """Return sorted result_*.csv paths, excluding aggregate/baseline files."""
    pattern = os.path.join(input_dir, "result_*.csv")
    files = sorted(glob.glob(pattern))
    return [f for f in files if os.path.basename(f) not in EXCLUDED_BASENAMES]


def aggregate(input_dir, output_path):
    """Aggregate result files and write the combined CSV. Returns the DataFrame."""
    files = find_result_files(input_dir)
    frames = []
    skipped = 0
    for path in files:
        try:
            df = pd.read_csv(path)
            if df.empty:
                raise ValueError("empty file")
            frames.append(df)
        except Exception as exc:
            skipped += 1
            print(f"[aggregate_results] WARNING: skipping '{path}': {exc}")

    if not frames:
        raise SystemExit(
            f"ERROR: no valid result files found in '{input_dir}' "
            f"(matched {len(files)} files, all unreadable/empty)."
        )

    combined = pd.concat(frames, ignore_index=True)
    if "config_id" in combined.columns:
        sort_key = pd.to_numeric(combined["config_id"], errors="coerce")
        combined = combined.assign(_sort=sort_key).sort_values(
            by=["_sort", "config_id"], kind="stable"
        ).drop(columns="_sort").reset_index(drop=True)

    ensure_dir(output_path)
    combined.to_csv(output_path, index=False)

    print(f"[aggregate_results] result files found : {len(files)}")
    print(f"[aggregate_results] files skipped      : {skipped}")
    print(f"[aggregate_results] rows aggregated    : {len(combined)}")
    print(f"[aggregate_results] output written to  : {output_path}")
    return combined


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Aggregate result CSVs into one file.")
    parser.add_argument("--input-dir", default="results", help="Directory with results.")
    parser.add_argument(
        "--output", default="results/all_results.csv", help="Combined CSV output path."
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    aggregate(args.input_dir, args.output)


if __name__ == "__main__":
    main()
