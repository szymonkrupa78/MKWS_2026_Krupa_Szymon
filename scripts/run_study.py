#!/usr/bin/env python3
"""Generate data tables and figures for the MKWS hybrid rocket project."""

from __future__ import annotations

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:
    raise SystemExit("Install numpy and pandas first: pip install -r requirements.txt") from exc

try:
    import cantera as ct
except ImportError as exc:
    raise SystemExit("Install Cantera first: pip install -r requirements.txt") from exc

from mkws_hybrid.hybrid_model import simulate_port_regression
from mkws_hybrid.plotting import (
    plot_gamma_mw_vs_of,
    plot_performance_vs_of,
    plot_port_history,
    plot_pressure_sweep,
    plot_report_summary,
    plot_species_vs_of,
    plot_temperature_vs_of,
    plot_transport_vs_of,
)
from mkws_hybrid.thermochemistry import (
    MECHANISM,
    run_equilibrium_sweep,
    run_pressure_sweep,
    stoichiometric_of_ratio,
)


def main() -> None:
    data_dir = ROOT / "data" / "processed"
    figure_dir = ROOT / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    of_values = np.linspace(3.0, 12.0, 37)
    pressure_values_bar = [10.0, 20.0, 30.0, 40.0]

    rows = run_equilibrium_sweep(of_values, pressure_values_bar, mechanism=MECHANISM)
    results = pd.DataFrame(rows)
    results_path = data_dir / "equilibrium_sweep.csv"
    results.to_csv(results_path, index=False)

    reference_pressure = 20.0
    reference = results[results["pressure_bar"] == reference_pressure].copy()
    best_cstar = reference.loc[reference["cstar_m_per_s"].idxmax()]
    best_vacuum_isp = reference.loc[reference["isp_vacuum_s"].idxmax()]
    best_sea_level_isp = reference.loc[reference["isp_sea_level_s"].idxmax()]

    pressure_sweep_values = [10.0, 20.0, 30.0, 40.0, 60.0, 80.0]
    pressure_sweep = pd.DataFrame(
        run_pressure_sweep(
            pressure_sweep_values,
            of_ratio=float(best_vacuum_isp["of_ratio"]),
            mechanism=MECHANISM,
        )
    )
    pressure_sweep_path = data_dir / "pressure_sweep.csv"
    pressure_sweep.to_csv(pressure_sweep_path, index=False)

    summary = pd.DataFrame(
        [
            {
                "metric": "stoichiometric_of_ratio",
                "of_ratio": stoichiometric_of_ratio(),
                "pressure_bar": np.nan,
                "value": stoichiometric_of_ratio(),
                "unit": "-",
            },
            {
                "metric": "maximum_cstar_at_20_bar",
                "of_ratio": best_cstar["of_ratio"],
                "pressure_bar": reference_pressure,
                "value": best_cstar["cstar_m_per_s"],
                "unit": "m/s",
            },
            {
                "metric": "maximum_vacuum_isp_at_20_bar",
                "of_ratio": best_vacuum_isp["of_ratio"],
                "pressure_bar": reference_pressure,
                "value": best_vacuum_isp["isp_vacuum_s"],
                "unit": "s",
            },
            {
                "metric": "maximum_sea_level_isp_at_20_bar",
                "of_ratio": best_sea_level_isp["of_ratio"],
                "pressure_bar": reference_pressure,
                "value": best_sea_level_isp["isp_sea_level_s"],
                "unit": "s",
            },
        ]
    )
    summary_path = data_dir / "summary_metrics.csv"
    summary.to_csv(summary_path, index=False)

    history = simulate_port_regression(reference)
    history_path = data_dir / "port_regression_history.csv"
    history.to_csv(history_path, index=False)

    plot_temperature_vs_of(results, figure_dir / "adiabatic_temperature_vs_of.png")
    plot_performance_vs_of(
        results,
        figure_dir / "performance_vs_of_20bar.png",
        pressure_bar=reference_pressure,
    )
    plot_species_vs_of(
        results,
        figure_dir / "species_vs_of_20bar.png",
        pressure_bar=reference_pressure,
    )
    plot_gamma_mw_vs_of(
        results,
        figure_dir / "gamma_molecular_weight_vs_of_20bar.png",
        pressure_bar=reference_pressure,
    )
    plot_transport_vs_of(
        results,
        figure_dir / "transport_vs_of_20bar.png",
        pressure_bar=reference_pressure,
    )
    plot_pressure_sweep(pressure_sweep, figure_dir / "pressure_sweep.png")
    plot_port_history(history, figure_dir / "port_regression_history.png")
    plot_report_summary(results, pressure_sweep, history, figure_dir / "report_summary.png")

    print(f"Cantera version: {ct.__version__}")
    print(f"Equilibrium sweep: {results_path}")
    print(f"Pressure sweep: {pressure_sweep_path}")
    print(f"Summary metrics: {summary_path}")
    print(f"Port history: {history_path}")
    print(f"Figures: {figure_dir}")


if __name__ == "__main__":
    main()
