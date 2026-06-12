"""Simulation backends.

Each backend implements the same contract (see ``base.SimulationBackend``):

    input : one JSON config (+ optional network/demand JSON)
    output: one CSV file with exactly one row using the shared metric schema

This lets the SLURM workflow, aggregation and analysis stay identical when
switching ``--backend python`` to ``--backend sumo`` in the future.
"""
