import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import ensure_dir, save_json

CYCLE_MIN = 40
CYCLE_MAX = 120
GREEN_MIN = 10
DEFAULT_YELLOW = 3
DEFAULT_ALL_RED = 2


def make_config(config_id, rng, traffic_level, simulation_duration, base_seed, n_tl_junctions=0):
    yellow_time = DEFAULT_YELLOW
    all_red_time = DEFAULT_ALL_RED
    lost_total = 2 * yellow_time + 2 * all_red_time

    min_cycle = max(CYCLE_MIN, 2 * GREEN_MIN + lost_total)
    cycle_length = rng.randint(min_cycle, CYCLE_MAX)

    green_budget = cycle_length - lost_total
    green_ns = rng.randint(GREEN_MIN, green_budget - GREEN_MIN)
    green_ew_max = green_budget - green_ns
    green_ew = rng.randint(GREEN_MIN, green_ew_max)

    offset = rng.randint(0, cycle_length - 1)
    seed = base_seed + config_id

    config = {
        "config_id": config_id,
        "cycle_length": cycle_length,
        "green_ns": green_ns,
        "green_ew": green_ew,
        "yellow_time": yellow_time,
        "all_red_time": all_red_time,
        "offset": offset,
        "traffic_level": traffic_level,
        "simulation_duration": simulation_duration,
        "seed": seed,
    }
    if n_tl_junctions > 0:
        config["offsets"] = [rng.randint(0, cycle_length - 1) for _ in range(n_tl_junctions)]
    return config


def generate_configs(n_configs, output_dir, seed, traffic_level, simulation_duration, n_tl_junctions=0):
    ensure_dir(output_dir)
    rng = random.Random(seed)
    paths = []
    for config_id in range(n_configs):
        config = make_config(
            config_id, rng, traffic_level, simulation_duration, seed, n_tl_junctions
        )
        filename = f"config_{config_id:04d}.json"
        path = os.path.join(output_dir, filename)
        save_json(config, path)
        paths.append(path)
    return paths


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate random traffic-light configs.")
    parser.add_argument("--n-configs", type=int, default=100, help="How many configs.")
    parser.add_argument("--output-dir", default="configs", help="Output directory.")
    parser.add_argument("--seed", type=int, default=123, help="Master RNG seed.")
    parser.add_argument(
        "--traffic-level",
        default="medium",
        choices=["low", "medium", "high"],
        help="Traffic level written into every config.",
    )
    parser.add_argument(
        "--simulation-duration",
        type=int,
        default=3600,
        help="Simulated seconds per configuration.",
    )
    parser.add_argument(
        "--network",
        default=None,
        help="Path to a SUMO net.xml; when given, counts TL junctions and adds "
             "an 'offsets' list to every config.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    n_tl_junctions = 0
    if args.network and args.network.endswith(".net.xml"):
        from utils.network import parse_tl_junction_ids
        tl_ids = parse_tl_junction_ids(args.network)
        n_tl_junctions = len(tl_ids)
        print(f"[generate_configs] network has {n_tl_junctions} TL junctions -> adding offsets")

    paths = generate_configs(
        n_configs=args.n_configs,
        output_dir=args.output_dir,
        seed=args.seed,
        traffic_level=args.traffic_level,
        simulation_duration=args.simulation_duration,
        n_tl_junctions=n_tl_junctions,
    )
    print(
        f"[generate_configs] wrote {len(paths)} configs to '{args.output_dir}' "
        f"(seed={args.seed}, traffic_level={args.traffic_level})"
    )


if __name__ == "__main__":
    main()
