"""Plotting utilities for the hybrid rocket project."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_temperature_vs_of(results: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for pressure_bar, group in results.groupby("pressure_bar"):
        ax.plot(
            group["of_ratio"],
            group["temperature_k"],
            marker="o",
            linewidth=1.8,
            markersize=3.2,
            label=f"{pressure_bar:g} bar",
        )
    ax.set_xlabel("Oxidizer-to-fuel ratio, O/F")
    ax.set_ylabel("Adiabatic chamber temperature [K]")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Chamber pressure")
    _save(fig, path)


def plot_performance_vs_of(results: pd.DataFrame, path: Path, pressure_bar: float) -> None:
    subset = results[results["pressure_bar"] == pressure_bar].sort_values("of_ratio")
    fig, ax1 = plt.subplots(figsize=(7.2, 4.8))
    ax1.plot(
        subset["of_ratio"],
        subset["isp_sea_level_s"],
        color="#0a9396",
        marker="o",
        label="sea-level Isp",
    )
    ax1.plot(
        subset["of_ratio"],
        subset["isp_vacuum_s"],
        color="#9b2226",
        marker="^",
        label="vacuum Isp",
    )
    ax1.plot(
        subset["of_ratio"],
        subset["isp_ideal_1atm_s"],
        color="#94d2bd",
        linestyle="--",
        label="ideally expanded to 1 atm",
    )
    ax1.set_xlabel("Oxidizer-to-fuel ratio, O/F")
    ax1.set_ylabel("Ideal specific impulse [s]")
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(
        subset["of_ratio"],
        subset["cstar_m_per_s"],
        color="#005f73",
        marker="s",
        label="c*",
    )
    ax2.set_ylabel("c* [m/s]", color="#005f73")
    ax2.tick_params(axis="y", labelcolor="#005f73")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], loc="best")
    fig.suptitle(f"Ideal nozzle performance at {pressure_bar:g} bar, area ratio 15")
    _save(fig, path)


def plot_gamma_mw_vs_of(results: pd.DataFrame, path: Path, pressure_bar: float) -> None:
    subset = results[results["pressure_bar"] == pressure_bar].sort_values("of_ratio")
    fig, ax1 = plt.subplots(figsize=(7.2, 4.6))
    ax1.plot(subset["of_ratio"], subset["gamma"], color="#005f73", marker="o", label="gamma")
    ax1.set_xlabel("Oxidizer-to-fuel ratio, O/F")
    ax1.set_ylabel("Heat capacity ratio gamma [-]", color="#005f73")
    ax1.tick_params(axis="y", labelcolor="#005f73")
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(
        subset["of_ratio"],
        subset["molecular_weight_kg_per_kmol"],
        color="#9b2226",
        marker="s",
        label="molecular weight",
    )
    ax2.set_ylabel("Mean molecular weight [kg/kmol]", color="#9b2226")
    ax2.tick_params(axis="y", labelcolor="#9b2226")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], loc="best")
    _save(fig, path)


def plot_pressure_sweep(pressure_sweep: pd.DataFrame, path: Path) -> None:
    fig, ax1 = plt.subplots(figsize=(7.2, 4.6))
    ax1.plot(
        pressure_sweep["pressure_bar"],
        pressure_sweep["temperature_k"],
        color="#bb3e03",
        marker="o",
        label="temperature",
    )
    ax1.set_xlabel("Chamber pressure [bar]")
    ax1.set_ylabel("Temperature [K]", color="#bb3e03")
    ax1.tick_params(axis="y", labelcolor="#bb3e03")
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(
        pressure_sweep["pressure_bar"],
        pressure_sweep["isp_sea_level_s"],
        color="#0a9396",
        marker="s",
        label="sea-level Isp",
    )
    ax2.plot(
        pressure_sweep["pressure_bar"],
        pressure_sweep["isp_vacuum_s"],
        color="#005f73",
        marker="^",
        label="vacuum Isp",
    )
    ax2.set_ylabel("Ideal specific impulse [s]", color="#005f73")
    ax2.tick_params(axis="y", labelcolor="#005f73")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], loc="best")
    _save(fig, path)


def plot_transport_vs_of(results: pd.DataFrame, path: Path, pressure_bar: float) -> None:
    subset = results[results["pressure_bar"] == pressure_bar].sort_values("of_ratio")
    fig, ax1 = plt.subplots(figsize=(7.2, 4.6))
    ax1.plot(
        subset["of_ratio"],
        subset["viscosity_pa_s"] * 1e6,
        color="#9b2226",
        marker="o",
        label="dynamic viscosity",
    )
    ax1.set_xlabel("Oxidizer-to-fuel ratio, O/F")
    ax1.set_ylabel("Dynamic viscosity [uPa s]", color="#9b2226")
    ax1.tick_params(axis="y", labelcolor="#9b2226")
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(
        subset["of_ratio"],
        subset["prandtl_number"],
        color="#005f73",
        marker="s",
        label="Prandtl number",
    )
    ax2.set_ylabel("Prandtl number [-]", color="#005f73")
    ax2.tick_params(axis="y", labelcolor="#005f73")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], loc="best")
    _save(fig, path)


def plot_species_vs_of(results: pd.DataFrame, path: Path, pressure_bar: float) -> None:
    subset = results[results["pressure_bar"] == pressure_bar].sort_values("of_ratio")
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for column, label in [
        ("x_CO2", "CO2"),
        ("x_H2O", "H2O"),
        ("x_CO", "CO"),
        ("x_H2", "H2"),
        ("x_O2", "O2"),
        ("x_NO", "NO"),
    ]:
        ax.plot(subset["of_ratio"], subset[column], marker="o", linewidth=1.6, label=label)
    ax.set_xlabel("Oxidizer-to-fuel ratio, O/F")
    ax.set_ylabel("Equilibrium mole fraction")
    ax.set_yscale("log")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(ncol=3)
    _save(fig, path)


def plot_port_history(history: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 7.0), sharex=True)
    axes[0].plot(history["time_s"], history["port_diameter_mm"], color="#005f73")
    axes[0].set_ylabel("Port diameter [mm]")
    axes[0].grid(True, alpha=0.3)
    axes[1].plot(history["time_s"], history["of_ratio"], color="#9b2226")
    axes[1].set_ylabel("O/F [-]")
    axes[1].grid(True, alpha=0.3)
    axes[2].plot(history["time_s"], history["thrust_n"], color="#0a9396")
    axes[2].set_xlabel("Time [s]")
    axes[2].set_ylabel("Ideal thrust [N]")
    axes[2].grid(True, alpha=0.3)
    _save(fig, path)


def plot_report_summary(
    results: pd.DataFrame,
    pressure_sweep: pd.DataFrame,
    history: pd.DataFrame,
    path: Path,
) -> None:
    """Create a compact multi-panel figure for the two-page report."""

    fig, axes = plt.subplots(2, 2, figsize=(8.6, 5.8))
    ax = axes[0, 0]
    for pressure_bar, group in results.groupby("pressure_bar"):
        ax.plot(group["of_ratio"], group["temperature_k"], linewidth=1.4, label=f"{pressure_bar:g} bar")
    ax.set_xlabel("O/F")
    ax.set_ylabel("T [K]")
    ax.set_title("Chamber temperature")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)

    subset = results[results["pressure_bar"] == 20.0].sort_values("of_ratio")
    ax = axes[0, 1]
    ax.plot(subset["of_ratio"], subset["cstar_m_per_s"], color="#005f73", label="c* [m/s]")
    ax.set_xlabel("O/F")
    ax.set_ylabel("c* [m/s]", color="#005f73")
    ax.tick_params(axis="y", labelcolor="#005f73")
    ax.grid(True, alpha=0.3)
    twin = ax.twinx()
    twin.plot(subset["of_ratio"], subset["isp_vacuum_s"], color="#9b2226", label="vacuum Isp [s]")
    twin.set_ylabel("Vacuum Isp [s]", color="#9b2226")
    twin.tick_params(axis="y", labelcolor="#9b2226")
    ax.set_title("Ideal performance, 20 bar")

    ax = axes[1, 0]
    ax.plot(pressure_sweep["pressure_bar"], pressure_sweep["temperature_k"], color="#bb3e03")
    ax.set_xlabel("Pressure [bar]")
    ax.set_ylabel("T [K]", color="#bb3e03")
    ax.tick_params(axis="y", labelcolor="#bb3e03")
    ax.grid(True, alpha=0.3)
    twin = ax.twinx()
    twin.plot(pressure_sweep["pressure_bar"], pressure_sweep["isp_vacuum_s"], color="#005f73")
    twin.set_ylabel("Vacuum Isp [s]", color="#005f73")
    twin.tick_params(axis="y", labelcolor="#005f73")
    ax.set_title("Pressure sweep at best O/F")

    ax = axes[1, 1]
    ax.plot(history["time_s"], history["port_diameter_mm"], color="#005f73", label="Port diameter [mm]")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Diameter [mm]", color="#005f73")
    ax.tick_params(axis="y", labelcolor="#005f73")
    ax.grid(True, alpha=0.3)
    twin = ax.twinx()
    twin.plot(history["time_s"], history["of_ratio"], color="#9b2226", label="O/F")
    twin.set_ylabel("O/F", color="#9b2226")
    twin.tick_params(axis="y", labelcolor="#9b2226")
    ax.set_title("Port regression")

    _save(fig, path)
