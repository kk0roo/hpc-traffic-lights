"""Tests for configuration generation: constraints and determinism."""

from generate_configs import (
    generate_configs,
    make_config,
    CYCLE_MIN,
    CYCLE_MAX,
    GREEN_MIN,
)
from utils.io import load_json

import random


def _assert_valid(config):
    assert CYCLE_MIN <= config["cycle_length"] <= CYCLE_MAX
    assert config["green_ns"] >= GREEN_MIN
    assert config["green_ew"] >= GREEN_MIN
    assert 0 <= config["offset"] <= config["cycle_length"] - 1
    lost = 2 * config["yellow_time"] + 2 * config["all_red_time"]
    assert config["green_ns"] + config["green_ew"] + lost <= config["cycle_length"]


def test_make_config_satisfies_constraints():
    rng = random.Random(42)
    for config_id in range(200):
        config = make_config(config_id, rng, "medium", 3600, base_seed=42)
        _assert_valid(config)


def test_generated_files_satisfy_constraints(tmp_path):
    paths = generate_configs(
        n_configs=20,
        output_dir=str(tmp_path),
        seed=123,
        traffic_level="medium",
        simulation_duration=3600,
    )
    assert len(paths) == 20
    for path in paths:
        _assert_valid(load_json(path))


def test_generation_is_deterministic(tmp_path):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    generate_configs(10, str(dir_a), seed=7, traffic_level="medium", simulation_duration=3600)
    generate_configs(10, str(dir_b), seed=7, traffic_level="medium", simulation_duration=3600)
    for i in range(10):
        name = f"config_{i:04d}.json"
        assert load_json(dir_a / name) == load_json(dir_b / name)
