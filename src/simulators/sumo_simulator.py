import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from typing import Optional

from utils.io import load_json, ensure_dir
from utils.network import sumo_tool as _sumo_tool
from simulators.base import SimulationBackend

from simulators.python_simulator import (
    _resolve_arrival_rates,
    _sample_arrivals,
    write_result_csv,
)

DIRECTIONS = ["N", "S", "E", "W"]
NS_DIRECTIONS = {"N", "S"}
EW_DIRECTIONS = {"E", "W"}

_ARM_LENGTH = 200.0
_NODE_COORDS = {
    "N": (0.0, _ARM_LENGTH),
    "S": (0.0, -_ARM_LENGTH),
    "E": (_ARM_LENGTH, 0.0),
    "W": (-_ARM_LENGTH, 0.0),
}
_OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}

_GRID_PERIOD = {"low": 4.0, "medium": 2.5, "high": 2.0}

_TIME_TO_TELEPORT = 300


def _run_tool(args):
    try:
        proc = subprocess.run(args, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"SUMO tool not found: {args[0]!r}. Install SUMO and set SUMO_HOME "
            f"or put its bin/ on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"{os.path.basename(args[0])} failed (exit {exc.returncode}):\n"
            f"{exc.stderr.strip()}"
        ) from exc
    return proc


def _write_network(tmpdir):
    nodes_path = os.path.join(tmpdir, "nodes.nod.xml")
    edges_path = os.path.join(tmpdir, "edges.edg.xml")
    net_path = os.path.join(tmpdir, "net.net.xml")

    nodes = ['<nodes>', '  <node id="C" x="0.0" y="0.0" type="traffic_light"/>']
    for d in DIRECTIONS:
        x, y = _NODE_COORDS[d]
        nodes.append(f'  <node id="{d}" x="{x}" y="{y}" type="priority"/>')
    nodes.append('</nodes>\n')

    edges = ['<edges>']
    for d in DIRECTIONS:
        edges.append(f'  <edge id="{d}2C" from="{d}" to="C" numLanes="1"/>')
        edges.append(f'  <edge id="C2{d}" from="C" to="{d}" numLanes="1"/>')
    edges.append('</edges>\n')

    with open(nodes_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(nodes))
    with open(edges_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(edges))

    _run_tool([
        _sumo_tool("netconvert"),
        "--node-files", nodes_path,
        "--edge-files", edges_path,
        "--output-file", net_path,
        "--no-warnings",
    ])
    return net_path


def _build_phases(config, controlled):
    n_links = (max(controlled) + 1) if controlled else 0

    def state(green_dirs, yellow_dirs=frozenset()):
        chars = []
        for i in range(n_links):
            d = controlled.get(i)
            if d in green_dirs:
                chars.append("G")
            elif d in yellow_dirs:
                chars.append("y")
            else:
                chars.append("r")
        return "".join(chars)

    green_ns = int(config["green_ns"])
    green_ew = int(config["green_ew"])
    yellow = int(config["yellow_time"])
    all_red = int(config["all_red_time"])
    cycle_length = int(config["cycle_length"])
    all_red_state = state(frozenset())

    phases = [(green_ns, state(NS_DIRECTIONS))]
    if yellow > 0:
        phases.append((yellow, state(frozenset(), NS_DIRECTIONS)))
    if all_red > 0:
        phases.append((all_red, all_red_state))
    phases.append((green_ew, state(EW_DIRECTIONS)))

    used = sum(d for d, _ in phases)
    remainder = cycle_length - used
    if remainder > 0:
        phases.append((remainder, all_red_state))
    return phases


def _apply_signal_plan(net_path, config):
    tree = ET.parse(net_path)
    root = tree.getroot()

    controlled = {}
    for conn in root.iter("connection"):
        if conn.get("tl") != "C":
            continue
        idx = conn.get("linkIndex")
        src = conn.get("from", "")
        if idx is None or "2" not in src:
            continue
        controlled[int(idx)] = src.split("2")[0]

    tl = root.find("tlLogic[@id='C']")
    if tl is None or not controlled:
        raise RuntimeError(
            "netconvert did not produce a traffic-light program for node 'C'."
        )

    for phase in list(tl.findall("phase")):
        tl.remove(phase)
    tl.set("offset", str(int(config.get("offset", 0))))
    for duration, st in _build_phases(config, controlled):
        ET.SubElement(tl, "phase", {"duration": str(duration), "state": st})

    tree.write(net_path, encoding="UTF-8", xml_declaration=True)


def _write_routes(tmpdir, config, demand, duration):
    rou_path = os.path.join(tmpdir, "routes.rou.xml")
    rates = _resolve_arrival_rates(config, demand)
    rng = random.Random(int(config["seed"]))

    lines = ['<routes>', '  <vType id="car" length="5.0" maxSpeed="13.9"/>']
    for d in DIRECTIONS:
        lines.append(f'  <route id="r_{d}" edges="{d}2C C2{_OPPOSITE[d]}"/>')

    veh_id = 0
    for t in range(duration):
        for d in DIRECTIONS:
            for _ in range(_sample_arrivals(rates[d], rng)):
                lines.append(
                    f'  <vehicle id="{veh_id}" type="car" route="r_{d}" '
                    f'depart="{t}"/>'
                )
                veh_id += 1
    lines.append('</routes>\n')

    with open(rou_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return rou_path, veh_id


def _classify_connections_by_coords(root, junction_id):
    junc = root.find(f'.//junction[@id="{junction_id}"]')
    if junc is None:
        return {}
    jx, jy = float(junc.get("x", 0)), float(junc.get("y", 0))

    node_pos = {}
    for j in root.iter("junction"):
        jid = j.get("id")
        if jid:
            try:
                node_pos[jid] = (float(j.get("x", 0)), float(j.get("y", 0)))
            except (TypeError, ValueError):
                pass

    edge_from_pos = {}
    for edge in root.iter("edge"):
        eid = edge.get("id")
        from_id = edge.get("from")
        if eid and from_id and from_id in node_pos:
            edge_from_pos[eid] = node_pos[from_id]

    controlled = {}
    for conn in root.iter("connection"):
        if conn.get("tl") != junction_id:
            continue
        idx = conn.get("linkIndex")
        edge_id = conn.get("from", "")
        if idx is None or edge_id not in edge_from_pos:
            continue
        fx, fy = edge_from_pos[edge_id]
        dx, dy = fx - jx, fy - jy
        if abs(dx) < 0.5 and abs(dy) < 0.5:
            continue
        if abs(dy) >= abs(dx):
            direction = "N" if dy > 0 else "S"
        else:
            direction = "E" if dx > 0 else "W"
        controlled[int(idx)] = direction

    return controlled


def _apply_signal_plan_grid(net_path, config):
    tree = ET.parse(net_path)
    root = tree.getroot()

    tl_elements = root.findall("tlLogic")
    offsets_list = config.get("offsets", None)

    for i, tl in enumerate(tl_elements):
        tl_id = tl.get("id")
        controlled = _classify_connections_by_coords(root, tl_id)
        if not controlled:
            continue

        for phase in list(tl.findall("phase")):
            tl.remove(phase)

        if offsets_list and i < len(offsets_list):
            off = int(offsets_list[i]) % int(config.get("cycle_length", 60))
        else:
            off = int(config.get("offset", 0))
        tl.set("offset", str(off))

        for duration, st in _build_phases(config, controlled):
            ET.SubElement(tl, "phase", {"duration": str(duration), "state": st})

    tree.write(net_path, encoding="UTF-8", xml_declaration=True)


def _write_routes_random_trips(tmpdir, net_path, config, duration):
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        raise RuntimeError(
            "SUMO_HOME is not set. Cannot run randomTrips.py for grid demand generation."
        )
    random_trips_script = os.path.join(sumo_home, "tools", "randomTrips.py")
    if not os.path.exists(random_trips_script):
        raise RuntimeError(f"randomTrips.py not found at {random_trips_script}")

    trips_path = os.path.join(tmpdir, "trips.trips.xml")
    routes_path = os.path.join(tmpdir, "routes.rou.xml")

    traffic_level = config.get("traffic_level", "medium")
    period = _GRID_PERIOD.get(traffic_level, 1.0)

    _run_tool([
        sys.executable, random_trips_script,
        "-n", net_path,
        "-e", str(duration),
        "-p", str(period),
        "--seed", str(int(config["seed"])),
        "-o", trips_path,
        "--fringe-factor", "5",
        "--trip-attributes", 'departLane="best" departSpeed="max"',
    ])

    _run_tool([
        _sumo_tool("duarouter"),
        "-n", net_path,
        "--route-files", trips_path,
        "-o", routes_path,
        "--ignore-errors",
        "--no-warnings",
    ])

    total = sum(1 for _ in ET.parse(routes_path).getroot().iter("vehicle"))
    return routes_path, total


def _parse_outputs(tripinfo_path, summary_path, total_arrivals, duration):
    waiting_times = []
    total_stops = 0
    total_departures = 0
    if os.path.exists(tripinfo_path):
        for trip in ET.parse(tripinfo_path).getroot().iter("tripinfo"):
            total_departures += 1
            waiting_times.append(float(trip.get("waitingTime", 0.0)))
            total_stops += int(float(trip.get("waitingCount", 0)))

    halting = []
    if os.path.exists(summary_path):
        for step in ET.parse(summary_path).getroot().iter("step"):
            halting.append(int(float(step.get("halting", 0))))

    avg_waiting = sum(waiting_times) / max(total_departures, 1)
    avg_queue = (sum(halting) / len(halting)) if halting else 0.0
    return {
        "total_arrivals": total_arrivals,
        "total_departures": total_departures,
        "vehicles_remaining": total_arrivals - total_departures,
        "avg_waiting_time": round(avg_waiting, 4),
        "avg_queue_length": round(avg_queue, 4),
        "max_queue_length": max(halting) if halting else 0,
        "total_stops": total_stops,
        "throughput": round(total_departures / max(duration, 1), 4),
    }


def _base_row(config, backend_name, runtime_seconds, status):
    offsets = config.get("offsets")
    offset_val = offsets[0] if offsets else config.get("offset", 0)
    return {
        "config_id": config.get("config_id", ""),
        "backend": backend_name,
        "traffic_level": config.get("traffic_level", ""),
        "cycle_length": config.get("cycle_length", ""),
        "green_ns": config.get("green_ns", ""),
        "green_ew": config.get("green_ew", ""),
        "yellow_time": config.get("yellow_time", ""),
        "all_red_time": config.get("all_red_time", ""),
        "offset": offset_val,
        "simulation_duration": config.get("simulation_duration", ""),
        "seed": config.get("seed", ""),
        "total_arrivals": 0,
        "total_departures": 0,
        "vehicles_remaining": 0,
        "avg_waiting_time": 0.0,
        "avg_queue_length": 0.0,
        "max_queue_length": 0,
        "total_stops": 0,
        "throughput": 0.0,
        "runtime_seconds": round(runtime_seconds, 4),
        "status": status,
    }


class SumoSimulator(SimulationBackend):
    name = "sumo"

    def run(
        self,
        config_path: str,
        output_path: str,
        network_path: Optional[str] = None,
        demand_path: Optional[str] = None,
        fcd_output: Optional[str] = None,
    ) -> None:
        config = load_json(config_path)
        demand = load_json(demand_path) if demand_path and demand_path.endswith(".json") else None
        duration = int(config["simulation_duration"])
        grid_mode = network_path is not None and network_path.endswith(".net.xml")

        start = time.perf_counter()
        try:
            with tempfile.TemporaryDirectory(prefix="sumo_run_") as tmpdir:
                if grid_mode:
                    net_path = os.path.join(tmpdir, "net.net.xml")
                    shutil.copy2(network_path, net_path)
                    _apply_signal_plan_grid(net_path, config)
                    rou_path, total_arrivals = _write_routes_random_trips(
                        tmpdir, net_path, config, duration
                    )
                else:
                    net_path = _write_network(tmpdir)
                    _apply_signal_plan(net_path, config)
                    rou_path, total_arrivals = _write_routes(tmpdir, config, demand, duration)

                tripinfo_path = os.path.join(tmpdir, "tripinfo.xml")
                summary_path = os.path.join(tmpdir, "summary.xml")

                sumo_cmd = [
                    _sumo_tool("sumo"),
                    "--net-file", net_path,
                    "--route-files", rou_path,
                    "--tripinfo-output", tripinfo_path,
                    "--summary-output", summary_path,
                    "--end", str(duration),
                    "--seed", str(int(config["seed"])),
                    "--time-to-teleport", str(_TIME_TO_TELEPORT),
                    "--no-step-log",
                    "--no-warnings",
                ]
                if fcd_output:
                    fcd_abs = os.path.abspath(fcd_output)
                    ensure_dir(fcd_abs)
                    sumo_cmd += ["--fcd-output", fcd_abs, "--device.fcd.period", "10"]

                _run_tool(sumo_cmd)
                metrics = _parse_outputs(tripinfo_path, summary_path, total_arrivals, duration)

            runtime = time.perf_counter() - start
            row = _base_row(config, self.name, runtime, "ok")
            row.update(metrics)
        except Exception as exc:
            runtime = time.perf_counter() - start
            row = _base_row(config, self.name, runtime, "error")
            print(f"[sumo] simulation failed: {exc}", file=sys.stderr)

        write_result_csv(row, output_path)
