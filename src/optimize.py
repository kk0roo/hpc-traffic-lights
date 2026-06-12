import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_configs import generate_configs
from simulators.python_simulator import PythonSimulator


def run_local_test(n_configs, config_dir, results_dir, seed, traffic_level, network, demand):
    paths = generate_configs(
        n_configs=n_configs,
        output_dir=config_dir,
        seed=seed,
        traffic_level=traffic_level,
        simulation_duration=3600,
    )
    backend = PythonSimulator()
    os.makedirs(results_dir, exist_ok=True)
    for config_id, config_path in enumerate(paths):
        output_path = os.path.join(results_dir, f"result_{config_id:04d}.csv")
        backend.run(
            config_path=config_path,
            output_path=output_path,
            network_path=network,
            demand_path=demand,
        )
        print(f"[optimize] evaluated {config_path} -> {output_path}")
    print(
        f"[optimize] local-test done: {len(paths)} configs evaluated. "
        f"Next: aggregate_results.py then select_best.py."
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Config generation / local test helper.")
    parser.add_argument(
        "--mode",
        choices=["generate", "local-test"],
        default="local-test",
        help="'generate' only writes configs; 'local-test' also evaluates them.",
    )
    parser.add_argument("--n-configs", type=int, default=5, help="Number of configs.")
    parser.add_argument("--config-dir", default="configs", help="Config output dir.")
    parser.add_argument("--results-dir", default="results", help="Results output dir.")
    parser.add_argument("--seed", type=int, default=123, help="Master seed.")
    parser.add_argument(
        "--traffic-level", default="medium", choices=["low", "medium", "high"]
    )
    parser.add_argument("--network", default=None, help="Optional network JSON path.")
    parser.add_argument("--demand", default=None, help="Optional demand JSON path.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.mode == "generate":
        generate_configs(
            n_configs=args.n_configs,
            output_dir=args.config_dir,
            seed=args.seed,
            traffic_level=args.traffic_level,
            simulation_duration=3600,
        )
        print(
            f"[optimize] generated {args.n_configs} configs in '{args.config_dir}'.\n"
            f"[optimize] The real evaluation is done in parallel via SLURM:\n"
            f"           sbatch slurm/run_array.sh"
        )
    else:
        run_local_test(
            n_configs=args.n_configs,
            config_dir=args.config_dir,
            results_dir=args.results_dir,
            seed=args.seed,
            traffic_level=args.traffic_level,
            network=args.network,
            demand=args.demand,
        )


if __name__ == "__main__":
    main()
