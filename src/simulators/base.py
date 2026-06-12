from typing import Optional


class SimulationBackend:
    name = "base"

    def run(
        self,
        config_path: str,
        output_path: str,
        network_path: Optional[str] = None,
        demand_path: Optional[str] = None,
        fcd_output: Optional[str] = None,
    ) -> None:
        raise NotImplementedError
