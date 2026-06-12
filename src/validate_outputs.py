import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.metrics import RESULT_COLUMNS, NON_NEGATIVE_COLUMNS


def validate(results_path):
    problems = []

    if not os.path.exists(results_path):
        return False, [f"results file not found: {results_path}"]

    df = pd.read_csv(results_path)

    missing = [c for c in RESULT_COLUMNS if c not in df.columns]
    if missing:
        problems.append(f"missing required columns: {missing}")

    if "status" not in df.columns:
        problems.append("missing 'status' column")

    for col in NON_NEGATIVE_COLUMNS:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if (numeric < 0).any():
                problems.append(f"negative values found in '{col}'")

    return len(problems) == 0, problems


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Validate aggregated results CSV.")
    parser.add_argument(
        "--results", default="results/all_results.csv", help="Aggregated results CSV."
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    ok, problems = validate(args.results)

    print(f"[validate_outputs] file: {args.results}")
    if ok:
        df = pd.read_csv(args.results)
        n_ok = int((df["status"] == "ok").sum()) if "status" in df.columns else 0
        print(f"[validate_outputs] rows total      : {len(df)}")
        print(f"[validate_outputs] rows status==ok : {n_ok}")
        print("[validate_outputs] VALIDATION PASSED")
    else:
        print("[validate_outputs] VALIDATION FAILED:")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
