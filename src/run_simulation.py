"""Central entry point: evaluate ONE traffic-light configuration.

This is the single command the SLURM array workflow calls. It is backend
agnostic -- switching ``--backend python`` to ``--backend sumo`` (once SUMO is
implemented) requires no change to the surrounding workflow.

Examples
    python src/run_simulation.py \
        --backend python \
        --config configs/config_0000.json \
        --output results/result_0000.csv

    python src/run_simulation.py \
        --backend python \
        --config configs/baseline.json \
        --output results/baseline_metrics.csv \
        --network data/network/simple_grid.json \
        --demand data/demand/demand_medium.json
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import ensure_dir  # noqa: E402
from simulators.python_simulator import PythonSimulator  # noqa: E402
from simulators.sumo_simulator import SumoSimulator  # noqa: E402

BACKENDS = {
    "python": PythonSimulator,
    "sumo": SumoSimulator,
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Evaluate one traffic-light configuration with a chosen backend."
    )
    parser.add_argument(
        "--backend",
        choices=sorted(BACKENDS.keys()),
        default="python",
        help="Simulation backend to use (default: python).",
    )
    parser.add_argument(
        "--config", required=True, help="Path to the JSON configuration file."
    )
    parser.add_argument(
        "--output", required=True, help="Path of the CSV result file to write."
    )
    parser.add_argument(
        "--network", default=None, help="Optional path to a JSON network file."
    )
    parser.add_argument(
        "--demand", default=None, help="Optional path to a JSON demand file."
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if not os.path.exists(args.config):
        raise SystemExit(f"ERROR: config file not found: {args.config}")

    backend_cls = BACKENDS.get(args.backend)
    if backend_cls is None:
        raise SystemExit(
            f"ERROR: unsupported backend '{args.backend}'. "
            f"Available: {', '.join(sorted(BACKENDS))}."
        )

    ensure_dir(args.output)
    backend = backend_cls()

    print(
        f"[run_simulation] backend={args.backend} config={args.config} "
        f"-> output={args.output}"
    )
    backend.run(
        config_path=args.config,
        output_path=args.output,
        network_path=args.network,
        demand_path=args.demand,
    )
    print(f"[run_simulation] done: wrote {args.output}")


if __name__ == "__main__":
    main()
