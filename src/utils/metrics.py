"""Shared metric schema for simulation result CSV files.

Every simulation backend (Python today, SUMO later) MUST produce a CSV with
exactly these columns, in this order. The aggregation, validation, selection
and analysis steps all rely on this stable schema.
"""

# The canonical, ordered list of output columns.
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

# Columns that must never be negative in a valid result row.
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
    """Return a single scalar score for a result row (lower is better).

    By default the score is the average waiting time, which is the primary
    optimization objective. This helper exists so that future optimizers can
    use a richer objective (e.g. a weighted combination of waiting time and
    queue length) without changing every call site.
    """
    return float(row["avg_waiting_time"])
