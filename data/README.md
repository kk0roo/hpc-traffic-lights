# Data

This project currently uses **synthetic data only** — no external datasets are
required to run the Python backend.

## Files

- `network/simple_grid.json`
  A simplified, abstract grid network (intersections on a `rows x cols` grid).
  It is **not** a real road map. Generate / regenerate it with:

  ```bash
  python src/generate_network.py
  ```

- `demand/demand_medium.json`
  Synthetic traffic demand: expected vehicle arrivals per second per direction
  (N, S, E, W). Generate / regenerate it with:

  ```bash
  python src/generate_demand.py                       # medium (default)
  python src/generate_demand.py --traffic-level high  # other levels
  ```

## Interpretation

The Python simulator treats `arrival_rates` as the expected number of vehicle
arrivals per second per direction. The single-intersection model does not yet
use the full network topology — the network file is provided so the structure is
ready for richer models.

## Future work - TO DO

- Import a real road network from **OpenStreetMap** (start with a small campus
  or district, not a whole city).
- Convert these JSON files into **SUMO** inputs (`*.net.xml`, `*.rou.xml`).
- Calibrate demand against **real traffic counts** / city open data.
