import csv

from simulators.python_simulator import PythonSimulator, simulate
from utils.io import save_json
from utils.metrics import RESULT_COLUMNS


BASE_CONFIG = {
    "config_id": 0,
    "cycle_length": 60,
    "green_ns": 30,
    "green_ew": 25,
    "yellow_time": 3,
    "all_red_time": 2,
    "offset": 0,
    "traffic_level": "medium",
    "simulation_duration": 600,
    "seed": 123,
}


def test_run_writes_valid_csv(tmp_path):
    config_path = tmp_path / "config.json"
    output_path = tmp_path / "result.csv"
    save_json(BASE_CONFIG, str(config_path))

    PythonSimulator().run(str(config_path), str(output_path))

    assert output_path.exists()
    with open(output_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    row = rows[0]
    for col in RESULT_COLUMNS:
        assert col in row
    assert row["status"] == "ok"
    assert row["backend"] == "python"
    assert int(row["total_arrivals"]) >= int(row["total_departures"])
    assert float(row["avg_waiting_time"]) >= 0


def test_simulate_is_deterministic():
    a = simulate(BASE_CONFIG)
    b = simulate(BASE_CONFIG)
    assert a == b


def test_vehicles_remaining_consistent():
    metrics = simulate(BASE_CONFIG)
    assert (
        metrics["vehicles_remaining"]
        == metrics["total_arrivals"] - metrics["total_departures"]
    )
