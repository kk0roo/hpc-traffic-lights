import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import save_json
from utils.network import sumo_tool, parse_tl_junction_ids

DEFAULT_OUTPUT = os.path.join("data", "network", "simple_grid.json")
DEFAULT_SUMO_OUTPUT = os.path.join("data", "network", "grid3x3.net.xml")


def build_network(rows, cols):
    intersections = []
    for r in range(rows):
        for c in range(cols):
            intersections.append(
                {
                    "id": f"I_{r}_{c}",
                    "row": r,
                    "col": c,
                    "incoming_directions": ["N", "S", "E", "W"],
                }
            )
    return {
        "network_id": f"simple_grid_{rows}x{cols}",
        "rows": rows,
        "cols": cols,
        "intersections": intersections,
    }


def build_sumo_network(output_path, grid_size=3, grid_length=200.0):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    cmd = [
        sumo_tool("netgenerate"),
        "--grid",
        f"--grid.number={grid_size}",
        f"--grid.length={grid_length}",
        "--default-junction-type", "traffic_light",
        "--output-file", output_path,
        "--no-warnings",
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise SystemExit(
            "ERROR: netgenerate not found. Install SUMO and set SUMO_HOME or add its bin/ to PATH."
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ERROR: netgenerate failed:\n{exc.stderr.strip()}")

    tl_ids = parse_tl_junction_ids(output_path)
    print(
        f"[generate_network] generated SUMO {grid_size}x{grid_size} grid "
        f"(grid_length={grid_length}m) -> {output_path}"
    )
    print(f"[generate_network] TL junctions ({len(tl_ids)}): {tl_ids}")
    return tl_ids


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a grid network (JSON for Python backend or net.xml for SUMO)."
    )
    parser.add_argument("--rows", type=int, default=3, help="Grid rows (JSON mode).")
    parser.add_argument("--cols", type=int, default=3, help="Grid cols (JSON mode).")
    parser.add_argument(
        "--sumo",
        action="store_true",
        help="Generate a SUMO net.xml using netgenerate instead of a JSON file.",
    )
    parser.add_argument(
        "--grid-size",
        type=int,
        default=3,
        help="Square grid size for SUMO mode (default: 3 -> 3x3 grid).",
    )
    parser.add_argument(
        "--grid-length",
        type=float,
        default=200.0,
        help="Edge length in metres for SUMO mode (default: 200).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: data/network/simple_grid.json or grid3x3.net.xml).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.sumo:
        output = args.output or DEFAULT_SUMO_OUTPUT
        build_sumo_network(output, grid_size=args.grid_size, grid_length=args.grid_length)
    else:
        output = args.output or DEFAULT_OUTPUT
        network = build_network(args.rows, args.cols)
        save_json(network, output)
        print(
            f"[generate_network] wrote {args.rows}x{args.cols} grid "
            f"({len(network['intersections'])} intersections) to {output}"
        )


if __name__ == "__main__":
    main()
