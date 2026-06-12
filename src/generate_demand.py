import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import save_json

ARRIVAL_RATES = {
    "low": {"N": 0.10, "S": 0.10, "E": 0.12, "W": 0.12},
    "medium": {"N": 0.20, "S": 0.20, "E": 0.25, "W": 0.25},
    "high": {"N": 0.40, "S": 0.40, "E": 0.45, "W": 0.45},
}

DEFAULT_OUTPUT = os.path.join("data", "demand", "demand_medium.json")


def build_demand(traffic_level):
    rates = ARRIVAL_RATES[traffic_level]
    return {
        "demand_id": traffic_level,
        "traffic_level": traffic_level,
        "arrival_rates": dict(rates),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate synthetic traffic demand.")
    parser.add_argument(
        "--traffic-level",
        default="medium",
        choices=sorted(ARRIVAL_RATES.keys()),
        help="Traffic level to generate.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSON path.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    demand = build_demand(args.traffic_level)
    save_json(demand, args.output)
    print(f"[generate_demand] wrote '{args.traffic_level}' demand to {args.output}")


if __name__ == "__main__":
    main()
