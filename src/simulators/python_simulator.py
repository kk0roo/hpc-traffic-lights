"""Simple discrete-time queueing simulator for a single signalised intersection.

This is the default backend. Simple and readable rather
than physically accurate. The goal is to provide a deterministic, CPU-bound
workload whose result depends on the traffic-light configuration, so that
evaluating many configurations in parallel on an HPC cluster is meaningful.

Summary of the model assumptions:
* Time step = 1 second.
* Four incoming directions: N, S, E, W (queues of waiting vehicles).
* The signal cycle has two green phases separated by lost time:
      NS green -> lost (yellow + all-red) -> EW green -> lost -> remainder lost
* NS green serves the N and S queues; EW green serves the E and W queues.
* During lost time (yellow / all-red / leftover) no vehicle is served.
* Arrivals are drawn deterministically from ``random.Random(seed)``.

See ``compute_metrics`` for how the reported metrics are derived.
"""

import csv
import time
from typing import Optional

from utils.io import ensure_dir, load_json
from utils.metrics import RESULT_COLUMNS
from simulators.base import SimulationBackend

# How many vehicles a single approach can discharge per second of green light:
SERVICE_RATE_PER_SECOND = 1

# Expected vehicles per second per direction - used when
# no demand file is supplied - and indexed by traffic level
DEFAULT_ARRIVAL_RATES = {
    "low": {"N": 0.10, "S": 0.10, "E": 0.12, "W": 0.12},
    "medium": {"N": 0.20, "S": 0.20, "E": 0.25, "W": 0.25},
    "high": {"N": 0.40, "S": 0.40, "E": 0.45, "W": 0.45},
}

DIRECTIONS = ["N", "S", "E", "W"]
NS_DIRECTIONS = {"N", "S"}
EW_DIRECTIONS = {"E", "W"}


def _sample_arrivals(rate, rng):
    """Return an integer number of arrivals for a given expected ``rate``.
    This is a simple way to introduce some randomness while ensuring that the
    expected number of arrivals is correct. For example, a rate of 0.3 would
    yield 1 arrival with probability 0.3 and 0 arrivals with probability 0.7.
    """
    base = int(rate)
    frac = rate - base
    if frac > 0 and rng.random() < frac:
        base += 1
    return base


def _served_directions(cycle_pos, green_ns, green_ew, lost_time):
    """Return the set of directions served at a given position in the cycle.
    Returns an empty set during lost time (yellow / all-red / leftover).
    """
    ns_end = green_ns
    ew_start = green_ns + lost_time
    ew_end = ew_start + green_ew
    if cycle_pos < ns_end:
        return NS_DIRECTIONS
    if ew_start <= cycle_pos < ew_end:
        return EW_DIRECTIONS
    return set()


def _resolve_arrival_rates(config, demand):
    """Pick arrival rates from the demand file if present, else from defaults."""
    if demand and "arrival_rates" in demand:
        rates = demand["arrival_rates"]
    else:
        level = config.get("traffic_level", "medium")
        rates = DEFAULT_ARRIVAL_RATES.get(level, DEFAULT_ARRIVAL_RATES["medium"])
    # default 0.0 for a missing one
    return {d: float(rates.get(d, 0.0)) for d in DIRECTIONS}


def simulate(config, demand=None):
    """Run the queueing simulation and return a metrics dictionary.
    ``config`` and ``demand`` are already-parsed dictionaries.
    """
    import random

    cycle_length = int(config["cycle_length"])
    green_ns = int(config["green_ns"])
    green_ew = int(config["green_ew"])
    yellow_time = int(config["yellow_time"])
    all_red_time = int(config["all_red_time"])
    offset = int(config.get("offset", 0))
    duration = int(config["simulation_duration"])
    seed = int(config["seed"])

    lost_time = yellow_time + all_red_time
    rates = _resolve_arrival_rates(config, demand)
    rng = random.Random(seed)

    queues = {d: 0 for d in DIRECTIONS}
    total_arrivals = 0
    total_departures = 0
    total_stops = 0
    waiting_vehicle_seconds = 0
    accumulated_queue_length = 0
    max_queue_length = 0

    for t in range(duration):
        cycle_pos = (t + offset) % cycle_length
        served = _served_directions(cycle_pos, green_ns, green_ew, lost_time)

        for d in DIRECTIONS:
            arrivals = _sample_arrivals(rates[d], rng)
            if arrivals == 0:
                continue
            queue_was_empty = queues[d] == 0
            queues[d] += arrivals
            total_arrivals += arrivals
            # A vehicle "stops" if the light is red for it, or if it joins a
            # queue that already had waiting vehicles. Vehicles arriving on a
            # green, empty approach pass without stopping.
            if d not in served or not queue_was_empty:
                total_stops += arrivals

        for d in served:
            departures = min(queues[d], SERVICE_RATE_PER_SECOND)
            queues[d] -= departures
            total_departures += departures

        qsum = sum(queues.values())
        accumulated_queue_length += qsum
        waiting_vehicle_seconds += qsum
        current_max = max(queues.values())
        if current_max > max_queue_length:
            max_queue_length = current_max

    vehicles_remaining = total_arrivals - total_departures
    avg_waiting_time = waiting_vehicle_seconds / max(total_departures, 1)
    avg_queue_length = accumulated_queue_length / max(duration, 1)
    throughput = total_departures / max(duration, 1)

    return {
        "total_arrivals": total_arrivals,
        "total_departures": total_departures,
        "vehicles_remaining": vehicles_remaining,
        "avg_waiting_time": round(avg_waiting_time, 4),
        "avg_queue_length": round(avg_queue_length, 4),
        "max_queue_length": max_queue_length,
        "total_stops": total_stops,
        "throughput": round(throughput, 4),
    }


def compute_metrics(config, demand, backend_name, runtime_seconds):
    """Assemble the full result row (config echo + simulation metrics)."""
    sim = simulate(config, demand)
    row = {
        "config_id": config.get("config_id", ""),
        "backend": backend_name,
        "traffic_level": config.get("traffic_level", ""),
        "cycle_length": config["cycle_length"],
        "green_ns": config["green_ns"],
        "green_ew": config["green_ew"],
        "yellow_time": config["yellow_time"],
        "all_red_time": config["all_red_time"],
        "offset": config.get("offset", 0),
        "simulation_duration": config["simulation_duration"],
        "seed": config["seed"],
        "runtime_seconds": round(runtime_seconds, 4),
        "status": "ok",
    }
    row.update(sim)
    return row


def write_result_csv(row, output_path):
    """Write a single result ``row`` to ``output_path`` using the shared schema."""
    ensure_dir(output_path)
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerow({col: row.get(col, "") for col in RESULT_COLUMNS})


class PythonSimulator(SimulationBackend):
    """Default simulation backend implemented in pure Python."""

    name = "python"

    def run(
        self,
        config_path: str,
        output_path: str,
        network_path: Optional[str] = None,
        demand_path: Optional[str] = None,
    ) -> None:
        config = load_json(config_path)
        demand = load_json(demand_path) if demand_path else None
        start = time.perf_counter()
        row = compute_metrics(config, demand, self.name, 0.0)
        runtime = time.perf_counter() - start
        row["runtime_seconds"] = round(runtime, 4)
        write_result_csv(row, output_path)
