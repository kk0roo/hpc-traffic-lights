import argparse
import itertools
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from utils.io import ensure_dir, save_json
from utils.network import parse_tl_junction_ids

YELLOW_TIME = 3
ALL_RED_TIME = 2
GREEN_MIN = 10


def generate_grid_configs(
    output_dir,
    seed=0,
    traffic_level="medium",
    simulation_duration=3600,
    network=None,
    cycle_values=(50, 70, 90),
    green_ns_values=(15, 25, 35, 45),
    green_ew_values=(15, 25, 35),
    n_offset_sets=3,
):
    ensure_dir(output_dir)
    rng = random.Random(seed)

    n_tl = 0
    if network and network.endswith(".net.xml"):
        n_tl = len(parse_tl_junction_ids(network))

    configs = []
    for cycle, gns, gew in itertools.product(cycle_values, green_ns_values, green_ew_values):
        lost = 2 * YELLOW_TIME + 2 * ALL_RED_TIME
        if gns < GREEN_MIN or gew < GREEN_MIN:
            continue
        if gns + gew + lost > cycle:
            continue
        for _ in range(n_offset_sets):
            cfg = {
                "cycle_length": cycle,
                "green_ns": gns,
                "green_ew": gew,
                "yellow_time": YELLOW_TIME,
                "all_red_time": ALL_RED_TIME,
                "offset": rng.randint(0, cycle - 1),
                "traffic_level": traffic_level,
                "simulation_duration": simulation_duration,
                "seed": rng.randint(0, 2**31 - 1),
            }
            if n_tl > 0:
                cfg["offsets"] = [rng.randint(0, cycle - 1) for _ in range(n_tl)]
            configs.append(cfg)

    paths = []
    for i, cfg in enumerate(configs):
        cfg["config_id"] = i
        path = os.path.join(output_dir, f"config_{i:04d}.json")
        save_json(cfg, path)
        paths.append(path)

    print(f"[generate_grid_configs] wrote {len(paths)} configs to '{output_dir}'")
    return paths


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate grid-search traffic-light configs.")
    parser.add_argument("--output-dir", required=True, help="Output directory for configs.")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed.")
    parser.add_argument("--traffic-level", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--simulation-duration", type=int, default=3600)
    parser.add_argument("--network", default=None, help="SUMO net.xml for offset count.")
    parser.add_argument("--n-offset-sets", type=int, default=3,
                        help="Random offset sets per (cycle, green_ns, green_ew) combo.")
    parser.add_argument("--n-per-axis", type=int, default=None,
                        help="Shorthand: use N values per axis (overrides individual settings).")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.n_per_axis is not None:
        n = args.n_per_axis
        cycle_values = [50 + i * (70 // max(n - 1, 1)) for i in range(n)]
        cycle_values = sorted(set(max(30, min(120, c)) for c in cycle_values))
        green_ns_values = [15 + i * (30 // max(n - 1, 1)) for i in range(n)]
        green_ew_values = [15 + i * (20 // max(n - 1, 1)) for i in range(n)]
    else:
        cycle_values = (50, 70, 90)
        green_ns_values = (15, 25, 35, 45)
        green_ew_values = (15, 25, 35)

    generate_grid_configs(
        output_dir=args.output_dir,
        seed=args.seed,
        traffic_level=args.traffic_level,
        simulation_duration=args.simulation_duration,
        network=args.network,
        cycle_values=cycle_values,
        green_ns_values=green_ns_values,
        green_ew_values=green_ew_values,
        n_offset_sets=args.n_offset_sets,
    )


if __name__ == "__main__":
    main()
