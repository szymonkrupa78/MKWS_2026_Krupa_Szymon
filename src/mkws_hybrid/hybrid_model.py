"""Simple port regression model for a paraffin hybrid rocket grain."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mkws_hybrid.thermochemistry import G0


def simulate_port_regression(
    performance_at_pressure: pd.DataFrame,
    burn_time_s: float = 8.0,
    dt_s: float = 0.05,
    grain_length_m: float = 0.20,
    initial_port_radius_m: float = 0.015,
    oxidizer_mass_flow_kg_s: float = 0.25,
    fuel_density_kg_m3: float = 900.0,
    regression_a: float = 7.0e-5,
    regression_n: float = 0.62,
) -> pd.DataFrame:
    """Simulate a single cylindrical port with a power-law regression rate.

    The regression correlation is illustrative and is used only to connect the
    thermochemical O/F sweep to a hybrid-motor-like time history:

        r_dot = a * G_ox ** n

    where G_ox is the oxidizer mass flux through the port.
    """

    perf = performance_at_pressure.sort_values("of_ratio")
    of_grid = perf["of_ratio"].to_numpy()
    isp_grid = perf["isp_ideal_1atm_s"].to_numpy()
    cstar_grid = perf["cstar_m_per_s"].to_numpy()
    temp_grid = perf["temperature_k"].to_numpy()

    times = np.arange(0.0, burn_time_s + dt_s, dt_s)
    radius = initial_port_radius_m
    rows = []

    for time_s in times:
        port_area_m2 = np.pi * radius**2
        burning_area_m2 = 2.0 * np.pi * radius * grain_length_m
        oxidizer_flux_kg_m2_s = oxidizer_mass_flow_kg_s / port_area_m2
        regression_rate_m_s = regression_a * oxidizer_flux_kg_m2_s**regression_n
        fuel_mass_flow_kg_s = fuel_density_kg_m3 * burning_area_m2 * regression_rate_m_s
        total_mass_flow_kg_s = oxidizer_mass_flow_kg_s + fuel_mass_flow_kg_s
        of_ratio = oxidizer_mass_flow_kg_s / fuel_mass_flow_kg_s
        isp_s = float(np.interp(of_ratio, of_grid, isp_grid))
        cstar_m_s = float(np.interp(of_ratio, of_grid, cstar_grid))
        chamber_temperature_k = float(np.interp(of_ratio, of_grid, temp_grid))
        thrust_n = total_mass_flow_kg_s * isp_s * G0

        rows.append(
            {
                "time_s": time_s,
                "port_radius_m": radius,
                "port_diameter_mm": 2.0 * radius * 1000.0,
                "oxidizer_flux_kg_m2_s": oxidizer_flux_kg_m2_s,
                "regression_rate_mm_s": regression_rate_m_s * 1000.0,
                "fuel_mass_flow_kg_s": fuel_mass_flow_kg_s,
                "oxidizer_mass_flow_kg_s": oxidizer_mass_flow_kg_s,
                "total_mass_flow_kg_s": total_mass_flow_kg_s,
                "of_ratio": of_ratio,
                "temperature_k": chamber_temperature_k,
                "cstar_m_per_s": cstar_m_s,
                "isp_ideal_1atm_s": isp_s,
                "thrust_n": thrust_n,
            }
        )

        radius += regression_rate_m_s * dt_s

    return pd.DataFrame(rows)
