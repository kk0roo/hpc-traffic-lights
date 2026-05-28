"""Generate a simplified grid network description.

This is a synthetic, abstract network model (not a real road map). It exists so
that the project structure already supports a network input, and so the future
SUMO backend can grow a real ``*.net.xml`` from a richer version of this file.

Example
-------
    python src/generate_network.py
    python src/generate_network.py --rows 4 --cols 4 --output data/network/grid_4x4.json
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import save_json  # noqa: E402

DEFAULT_OUTPUT = os.path.join("data", "network", "simple_grid.json")


def build_network(rows, cols):
    """Build a simple rows x cols grid of intersections."""
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate a synthetic grid network.")
    parser.add_argument("--rows", type=int, default=3, help="Grid rows.")
    parser.add_argument("--cols", type=int, default=3, help="Grid columns.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSON path.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    network = build_network(args.rows, args.cols)
    save_json(network, args.output)
    print(
        f"[generate_network] wrote {args.rows}x{args.cols} grid "
        f"({len(network['intersections'])} intersections) to {args.output}"
    )


if __name__ == "__main__":
    main()
