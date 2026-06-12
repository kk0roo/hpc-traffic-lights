RESULT_COLUMNS = [
    "config_id",
    "backend",
    "traffic_level",
    "cycle_length",
    "green_ns",
    "green_ew",
    "yellow_time",
    "all_red_time",
    "offset",
    "simulation_duration",
    "seed",
    "total_arrivals",
    "total_departures",
    "vehicles_remaining",
    "avg_waiting_time",
    "avg_queue_length",
    "max_queue_length",
    "total_stops",
    "throughput",
    "runtime_seconds",
    "status",
]

NON_NEGATIVE_COLUMNS = [
    "total_arrivals",
    "total_departures",
    "vehicles_remaining",
    "avg_waiting_time",
    "avg_queue_length",
    "max_queue_length",
    "total_stops",
    "throughput",
    "runtime_seconds",
]


def compute_score(row):
    return float(row["avg_waiting_time"])
