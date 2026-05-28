"""SUMO simulation backend -- TO DO.

When implemented, :meth:`SumoSimulator.run` should:

1. Read the SAME JSON configuration file as Python backend.
2. Translate that configuration into SUMO XML input files.
3. Create an isolated per-run working directory, so that parallel SLURM array tasks never clash on shared files.
4. Run SUMO as a subprocess.
5. Parse SUMO output (e.g. ``tripinfo.xml`` / summary output) and map SUMO's
   metrics onto THIS project's stable schema (see ``utils.metrics``)
6. Write exactly one CSV row using the same ``RESULT_COLUMNS`` order, with
   ``backend = "sumo"`` and ``status = "ok"`` (or ``"error"`` on failure).

Until then, calling this backend raises a clear NotImplementedError.
"""

from typing import Optional

from simulators.base import SimulationBackend


class SumoSimulator(SimulationBackend):
    """Future SUMO backend. Currently a non-functional scaffold."""

    name = "sumo"

    def run(
        self,
        config_path: str,
        output_path: str,
        network_path: Optional[str] = None,
        demand_path: Optional[str] = None,
    ) -> None:
        raise NotImplementedError(
            "SUMO backend is not implemented yet. Use --backend python."
        )
