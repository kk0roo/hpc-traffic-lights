import csv
import os
import shutil

import pytest

from simulators.sumo_simulator import (
    SumoSimulator,
    _build_phases,
    _sumo_tool,
)
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
    "simulation_duration": 200,
    "seed": 123,
}


def _sumo_available():
    return shutil.which(_sumo_tool("sumo")) is not None or bool(
        os.environ.get("SUMO_HOME")
    )


def test_build_phases_durations_and_state_width():
    controlled = {0: "N", 1: "S", 2: "E", 3: "W"}
    phases = _build_phases(BASE_CONFIG, controlled)

    durations = [d for d, _ in phases]
    assert durations[0] == 30
    assert durations[3] == 25
    assert all(len(state) == 4 for _, state in phases)
    assert sum(durations) == BASE_CONFIG["cycle_length"]
    assert phases[0][1] == "GGrr"


def test_run_writes_error_row_when_sumo_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "simulators.sumo_simulator._sumo_tool",
        lambda name: "definitely-not-a-real-sumo-binary",
    )
    config_path = tmp_path / "config.json"
    output_path = tmp_path / "result.csv"
    save_json(BASE_CONFIG, str(config_path))

    SumoSimulator().run(str(config_path), str(output_path))

    with open(output_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["status"] == "error"
    assert rows[0]["backend"] == "sumo"
    for col in RESULT_COLUMNS:
        assert col in rows[0]


@pytest.mark.skipif(not _sumo_available(), reason="SUMO not installed")
def test_run_end_to_end_writes_ok_row(tmp_path):
    config_path = tmp_path / "config.json"
    output_path = tmp_path / "result.csv"
    save_json(BASE_CONFIG, str(config_path))

    SumoSimulator().run(str(config_path), str(output_path))

    with open(output_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "ok"
    assert row["backend"] == "sumo"
    assert int(row["total_arrivals"]) >= int(row["total_departures"])
    assert float(row["avg_waiting_time"]) >= 0
