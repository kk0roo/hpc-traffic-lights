import csv

import pandas as pd

from aggregate_results import aggregate, find_result_files
from utils.metrics import RESULT_COLUMNS


def _write_fake_result(path, config_id):
    row = {col: 0 for col in RESULT_COLUMNS}
    row["config_id"] = config_id
    row["backend"] = "python"
    row["traffic_level"] = "medium"
    row["status"] = "ok"
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerow(row)


def test_aggregate_collects_all_rows(tmp_path):
    for cid in range(5):
        _write_fake_result(tmp_path / f"result_{cid:04d}.csv", cid)
    _write_fake_result(tmp_path / "baseline_metrics.csv", 999)

    output = tmp_path / "all_results.csv"
    df = aggregate(str(tmp_path), str(output))

    assert output.exists()
    assert len(df) == 5
    assert sorted(df["config_id"].tolist()) == [0, 1, 2, 3, 4]


def test_find_result_files_excludes_aggregates(tmp_path):
    _write_fake_result(tmp_path / "result_0000.csv", 0)
    _write_fake_result(tmp_path / "baseline_metrics.csv", 1)
    _write_fake_result(tmp_path / "all_results.csv", 2)

    found = [f.split("/")[-1].split("\\")[-1] for f in find_result_files(str(tmp_path))]
    assert "result_0000.csv" in found
    assert "baseline_metrics.csv" not in found
    assert "all_results.csv" not in found


def test_aggregate_skips_corrupted_file(tmp_path):
    _write_fake_result(tmp_path / "result_0000.csv", 0)
    (tmp_path / "result_0001.csv").write_text("", encoding="utf-8")

    output = tmp_path / "all_results.csv"
    df = aggregate(str(tmp_path), str(output))
    assert len(df) == 1
