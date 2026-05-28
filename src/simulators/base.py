"""Backend contract shared by every simulator.

The rest of the project (SLURM scripts, aggregation, analysis) depends ONLY on
this contract, never on the internal details of a specific simulator.
"""

from typing import Optional


class SimulationBackend:
    """Abstract base class for a traffic simulation backend.
    A backend takes a single traffic-light configuration and produces a single
    CSV row of metrics. Concrete subclasses must implement :meth:`run`.
    """
    name = "base"

    def run(
        self,
        config_path: str,
        output_path: str,
        network_path: Optional[str] = None,
        demand_path: Optional[str] = None,
    ) -> None:
        """Evaluate one configuration and write one CSV row to ``output_path``.

        Parameters:
        config_path: path to a JSON traffic-light configuration file
        output_path: path of the CSV file to write (exactly one data row + header)
        network_path: optional path to a JSON network description
        demand_path: optional path to a JSON demand description
        """
        raise NotImplementedError
