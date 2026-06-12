import csv
import math
import random
import time
from typing import Optional

from simulators.base import SimulationBackend
from utils.io import ensure_dir, load_json
from utils.metrics import RESULT_COLUMNS


class MCSimulator(SimulationBackend):
    name = "mc"

    def run(
        self,
        config_path: str,
        output_path: str,
        network_path: Optional[str] = None,
        demand_path: Optional[str] = None,
        fcd_output: Optional[str] = None,
    ) -> None:
        config = load_json(config_path)
        n_samples = int(config.get("n_samples", config.get("simulation_duration", 100000)))
        seed = int(config.get("seed", 0))

        start = time.perf_counter()
        rng = random.Random(seed)
        hits = sum(1 for _ in range(n_samples) if rng.random() ** 2 + rng.random() ** 2 < 1.0)
        runtime = time.perf_counter() - start

        pi_estimate = 4.0 * hits / n_samples
        pi_error = abs(pi_estimate - math.pi)

        row = {
            "config_id": config.get("config_id", ""),
            "backend": self.name,
            "traffic_level": config.get("traffic_level", ""),
            "cycle_length": config.get("cycle_length", n_samples),
            "green_ns": config.get("green_ns", 0),
            "green_ew": config.get("green_ew", 0),
            "yellow_time": config.get("yellow_time", 0),
            "all_red_time": config.get("all_red_time", 0),
            "offset": config.get("offset", 0),
            "simulation_duration": n_samples,
            "seed": seed,
            "total_arrivals": n_samples,
            "total_departures": hits,
            "vehicles_remaining": n_samples - hits,
            "avg_waiting_time": round(pi_error, 6),
            "avg_queue_length": round(pi_estimate, 6),
            "max_queue_length": 0,
            "total_stops": 0,
            "throughput": round(hits / n_samples, 6),
            "runtime_seconds": round(runtime, 4),
            "status": "ok",
        }

        ensure_dir(output_path)
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=RESULT_COLUMNS)
            writer.writeheader()
            writer.writerow({col: row.get(col, "") for col in RESULT_COLUMNS})
