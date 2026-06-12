import argparse
import os
import random
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import load_json, save_json, ensure_dir
from utils.metrics import compute_score

CYCLE_MIN = 40
CYCLE_MAX = 120
GREEN_MIN = 10


def _clamp_config(config):
    yellow = int(config["yellow_time"])
    all_red = int(config["all_red_time"])
    lost = 2 * yellow + 2 * all_red

    cycle = int(round(config["cycle_length"]))
    cycle = max(CYCLE_MIN, min(CYCLE_MAX, cycle))
    config["cycle_length"] = cycle

    green_budget = cycle - lost
    green_ns = int(round(config["green_ns"]))
    green_ns = max(GREEN_MIN, min(green_ns, green_budget - GREEN_MIN))
    config["green_ns"] = green_ns

    green_ew = int(round(config["green_ew"]))
    green_ew = max(GREEN_MIN, min(green_ew, green_budget - green_ns))
    config["green_ew"] = green_ew

    config["offset"] = int(round(config.get("offset", 0))) % cycle

    if "offsets" in config:
        config["offsets"] = [int(round(o)) % cycle for o in config["offsets"]]

    return config


def crossover(cfg_a, cfg_b, rng):
    child = {k: v for k, v in cfg_a.items()}

    for key in ("cycle_length", "green_ns", "green_ew", "offset"):
        if key in cfg_a and key in cfg_b:
            child[key] = cfg_a[key] if rng.random() < 0.5 else cfg_b[key]

    if "offsets" in cfg_a and "offsets" in cfg_b:
        child["offsets"] = [
            a if rng.random() < 0.5 else b
            for a, b in zip(cfg_a["offsets"], cfg_b["offsets"])
        ]

    return _clamp_config(child)


def mutate(config, rng, rate=0.2, strength=0.2):
    cfg = {k: v for k, v in config.items()}
    cycle = int(cfg["cycle_length"])

    def perturb_int(val, lo, hi):
        delta = int(round(val * strength * rng.uniform(-1, 1)))
        return max(lo, min(hi, val + delta))

    if rng.random() < rate:
        cfg["cycle_length"] = perturb_int(cycle, CYCLE_MIN, CYCLE_MAX)

    lost = 2 * int(cfg["yellow_time"]) + 2 * int(cfg["all_red_time"])
    green_budget = cfg["cycle_length"] - lost

    if rng.random() < rate:
        cfg["green_ns"] = perturb_int(int(cfg["green_ns"]), GREEN_MIN, green_budget - GREEN_MIN)
    if rng.random() < rate:
        cfg["green_ew"] = perturb_int(int(cfg["green_ew"]), GREEN_MIN, green_budget - int(cfg["green_ns"]))

    if rng.random() < rate and "offset" in cfg:
        delta = int(round(cfg["cycle_length"] * strength * rng.uniform(-1, 1)))
        cfg["offset"] = (int(cfg["offset"]) + delta) % cfg["cycle_length"]

    if "offsets" in cfg:
        cfg["offsets"] = [
            ((int(o) + int(round(cfg["cycle_length"] * strength * rng.uniform(-1, 1)))) % cfg["cycle_length"])
            if rng.random() < rate else int(o)
            for o in cfg["offsets"]
        ]

    return _clamp_config(cfg)


def load_population(results_dir, config_dir):
    agg_path = os.path.join(results_dir, "all.csv")
    if not os.path.exists(agg_path):
        import glob
        files = sorted(glob.glob(os.path.join(results_dir, "result_*.csv")))
        if not files:
            raise SystemExit(f"ERROR: no results found in '{results_dir}'. Run aggregate first.")
        df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    else:
        df = pd.read_csv(agg_path)

    if "status" in df.columns:
        df = df[df["status"] == "ok"].copy()
    if df.empty:
        raise SystemExit(f"ERROR: no successful results in '{results_dir}'.")

    population = []
    for _, row in df.iterrows():
        config_id = row.get("config_id", "")
        try:
            cfg_filename = f"config_{int(config_id):04d}.json"
        except (ValueError, TypeError):
            cfg_filename = f"config_{config_id}.json"
        cfg_path = os.path.join(config_dir, cfg_filename)
        if not os.path.exists(cfg_path):
            continue
        config = load_json(cfg_path)
        fitness = float(row.get("avg_waiting_time", float("inf")))
        population.append((fitness, config))

    if not population:
        raise SystemExit(f"ERROR: could not load any config JSONs from '{config_dir}'.")

    return population


def select_parents(population, top_fraction=0.5):
    sorted_pop = sorted(population, key=lambda x: x[0])
    n_keep = max(2, int(len(sorted_pop) * top_fraction))
    return [cfg for _, cfg in sorted_pop[:n_keep]]


def generate_next_generation(results_dir, config_dir, output_dir, generation, pop_size, seed):
    ensure_dir(output_dir)
    rng = random.Random(seed + generation)

    print(f"[ea_next_gen] loading generation {generation} from '{results_dir}'...")
    population = load_population(results_dir, config_dir)
    print(f"[ea_next_gen] loaded {len(population)} individuals")

    parents = select_parents(population)
    print(f"[ea_next_gen] selected {len(parents)} parents (top {100*len(parents)//len(population)}%)")

    paths = []
    for new_id in range(pop_size):
        pa = parents[rng.randint(0, len(parents) - 1)]
        pb = parents[rng.randint(0, len(parents) - 1)]
        if len(parents) > 1:
            while pb is pa:
                pb = parents[rng.randint(0, len(parents) - 1)]

        child = crossover(pa, pb, rng)
        child = mutate(child, rng)
        child["config_id"] = new_id
        child["seed"] = seed + (generation + 1) * 1000 + new_id

        cfg_path = os.path.join(output_dir, f"config_{new_id:04d}.json")
        save_json(child, cfg_path)
        paths.append(cfg_path)

    print(f"[ea_next_gen] wrote {len(paths)} configs to '{output_dir}' (gen {generation + 1})")
    return paths


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="EA: generate next-generation configs from results.")
    parser.add_argument("--generation", type=int, required=True, help="Current generation index.")
    parser.add_argument("--results-dir", required=True, help="Directory with gen_N results.")
    parser.add_argument("--config-dir", required=True, help="Directory with gen_N config JSONs.")
    parser.add_argument("--output-dir", required=True, help="Output directory for gen_N+1 configs.")
    parser.add_argument("--pop-size", type=int, default=50, help="Population size for next gen.")
    parser.add_argument("--seed", type=int, default=42, help="Master RNG seed.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    generate_next_generation(
        results_dir=args.results_dir,
        config_dir=args.config_dir,
        output_dir=args.output_dir,
        generation=args.generation,
        pop_size=args.pop_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
