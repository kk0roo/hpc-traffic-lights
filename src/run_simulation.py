import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import ensure_dir
from simulators.python_simulator import PythonSimulator
from simulators.sumo_simulator import SumoSimulator
from simulators.mc_simulator import MCSimulator

BACKENDS = {
    "python": PythonSimulator,
    "sumo": SumoSimulator,
    "mc": MCSimulator,
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
        "--network", default=None, help="Optional path to a network file (JSON or SUMO net.xml)."
    )
    parser.add_argument(
        "--demand", default=None, help="Optional path to a JSON demand file."
    )
    parser.add_argument(
        "--fcd-output",
        default=None,
        dest="fcd_output",
        help="Optional path to write SUMO FCD XML for traffic animation.",
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
    if args.fcd_output and args.backend != "sumo":
        print("[run_simulation] WARNING: --fcd-output is only used by the sumo backend; ignoring.")

    backend.run(
        config_path=args.config,
        output_path=args.output,
        network_path=args.network,
        demand_path=args.demand,
        fcd_output=args.fcd_output,
    )
    print(f"[run_simulation] done: wrote {args.output}")


if __name__ == "__main__":
    main()
