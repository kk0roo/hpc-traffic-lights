import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from utils.io import ensure_dir, save_json


def generate_mc_configs(output_dir, n_configs, n_samples=100000, seed=0):
    ensure_dir(output_dir)
    paths = []
    for i in range(n_configs):
        cfg = {
            "config_id": i,
            "cycle_length": n_samples,
            "green_ns": 0,
            "green_ew": 0,
            "yellow_time": 0,
            "all_red_time": 0,
            "offset": 0,
            "traffic_level": "medium",
            "simulation_duration": n_samples,
            "seed": seed + i,
            "n_samples": n_samples,
        }
        path = os.path.join(output_dir, f"config_{i:04d}.json")
        save_json(cfg, path)
        paths.append(path)
    print(f"[generate_mc_configs] wrote {len(paths)} configs (n_samples={n_samples}) to '{output_dir}'")
    return paths


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate Monte Carlo configs for pi estimation.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--n-configs", type=int, default=100, help="Number of MC tasks.")
    parser.add_argument("--n-samples", type=int, default=100000, help="Random samples per task.")
    parser.add_argument("--seed", type=int, default=0, help="Base RNG seed.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    generate_mc_configs(args.output_dir, args.n_configs, args.n_samples, args.seed)


if __name__ == "__main__":
    main()
