"""Cantera-based equilibrium calculations for a N2O/paraffin hybrid motor.

The fuel is represented by ethylene (C2H4). This is a practical gas-phase
surrogate for paraffin pyrolysis products and is supported by GRI-Mech 3.0.
The model is intended for preliminary thermochemical trends, not for detailed
CFD or surface chemistry.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import cantera as ct

BAR_TO_PA = 100_000.0
G0 = 9.80665
FUEL = "C2H4"
OXIDIZER = "N2O"
MECHANISM = "gri30.yaml"
TRACKED_SPECIES = ("N2", "CO2", "H2O", "CO", "H2", "O2", "NO", "OH")


@dataclass(frozen=True)
class EquilibriumCase:
    """One equilibrium chamber state for a selected O/F and pressure."""

    of_ratio: float
    pressure_bar: float
    temperature_k: float
    gamma: float
    molecular_weight_kg_per_kmol: float
    gas_constant_j_kg_k: float
    density_kg_m3: float
    cp_mass_j_kg_k: float
    cv_mass_j_kg_k: float
    sound_speed_m_per_s: float
    viscosity_pa_s: float
    thermal_conductivity_w_m_k: float
    prandtl_number: float
    cstar_m_per_s: float
    nozzle_area_ratio: float
    exit_mach: float
    exit_pressure_bar: float
    exit_temperature_k: float
    exit_velocity_m_per_s: float
    cf_sea_level: float
    cf_vacuum: float
    isp_sea_level_s: float
    isp_vacuum_s: float
    cf_ideal_1atm: float
    isp_ideal_1atm_s: float
    mole_fractions: dict[str, float]

    def as_row(self) -> dict[str, float]:
        row = {
            "of_ratio": self.of_ratio,
            "pressure_bar": self.pressure_bar,
            "temperature_k": self.temperature_k,
            "gamma": self.gamma,
            "molecular_weight_kg_per_kmol": self.molecular_weight_kg_per_kmol,
            "gas_constant_j_kg_k": self.gas_constant_j_kg_k,
            "density_kg_m3": self.density_kg_m3,
            "cp_mass_j_kg_k": self.cp_mass_j_kg_k,
            "cv_mass_j_kg_k": self.cv_mass_j_kg_k,
            "sound_speed_m_per_s": self.sound_speed_m_per_s,
            "viscosity_pa_s": self.viscosity_pa_s,
            "thermal_conductivity_w_m_k": self.thermal_conductivity_w_m_k,
            "prandtl_number": self.prandtl_number,
            "cstar_m_per_s": self.cstar_m_per_s,
            "nozzle_area_ratio": self.nozzle_area_ratio,
            "exit_mach": self.exit_mach,
            "exit_pressure_bar": self.exit_pressure_bar,
            "exit_temperature_k": self.exit_temperature_k,
            "exit_velocity_m_per_s": self.exit_velocity_m_per_s,
            "cf_sea_level": self.cf_sea_level,
            "cf_vacuum": self.cf_vacuum,
            "isp_sea_level_s": self.isp_sea_level_s,
            "isp_vacuum_s": self.isp_vacuum_s,
            "cf_ideal_1atm": self.cf_ideal_1atm,
            "isp_ideal_1atm_s": self.isp_ideal_1atm_s,
        }
        for species, value in self.mole_fractions.items():
            row[f"x_{species}"] = value
        return row


def stoichiometric_of_ratio(mechanism: str = MECHANISM) -> float:
    """Return stoichiometric O/F for C2H4 + 6 N2O -> products."""

    gas = ct.Solution(mechanism)
    fuel_mw = gas.molecular_weights[gas.species_index(FUEL)]
    oxidizer_mw = gas.molecular_weights[gas.species_index(OXIDIZER)]
    return 6.0 * oxidizer_mw / fuel_mw


def mixture_moles_for_of(gas: ct.Solution, of_ratio: float) -> dict[str, float]:
    """Build a reactant composition from a mass O/F ratio.

    The basis is 1 kg of fuel and ``of_ratio`` kg of oxidizer. Cantera accepts
    any proportional mole amounts, so no normalization is needed here.
    """

    if of_ratio <= 0:
        raise ValueError("O/F ratio must be positive.")
    fuel_mw = gas.molecular_weights[gas.species_index(FUEL)]
    oxidizer_mw = gas.molecular_weights[gas.species_index(OXIDIZER)]
    return {FUEL: 1.0 / fuel_mw, OXIDIZER: of_ratio / oxidizer_mw}


def ideal_cstar(temperature_k: float, gamma: float, molecular_weight: float) -> float:
    """Calculate ideal characteristic velocity from chamber gas properties."""

    r_specific = ct.gas_constant / molecular_weight
    pressure_factor = ((gamma + 1.0) / 2.0) ** (
        (gamma + 1.0) / (2.0 * (gamma - 1.0))
    )
    return math.sqrt(r_specific * temperature_k / gamma) * pressure_factor


def ideal_thrust_coefficient(gamma: float, pressure_ratio: float) -> float:
    """Ideal thrust coefficient for expansion to the ambient pressure.

    ``pressure_ratio`` is p_exit / p_chamber. The pressure thrust term is zero
    because the nozzle is assumed to be ideally expanded to 1 atm.
    """

    if not 0.0 < pressure_ratio < 1.0:
        return 0.0
    expansion_term = 1.0 - pressure_ratio ** ((gamma - 1.0) / gamma)
    coefficient = (
        2.0
        * gamma**2
        / (gamma - 1.0)
        * (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (gamma - 1.0))
        * expansion_term
    )
    return math.sqrt(max(coefficient, 0.0))


def area_mach_relation(mach: float, gamma: float) -> float:
    """Return isentropic area ratio A/A* for a calorically perfect gas."""

    if mach <= 0.0:
        raise ValueError("Mach number must be positive.")
    exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0))
    bracket = (2.0 / (gamma + 1.0)) * (1.0 + 0.5 * (gamma - 1.0) * mach**2)
    return (1.0 / mach) * bracket**exponent


def supersonic_mach_from_area_ratio(area_ratio: float, gamma: float) -> float:
    """Find the supersonic Mach number for a specified nozzle area ratio."""

    if area_ratio < 1.0:
        raise ValueError("Area ratio must be greater than or equal to one.")

    low = 1.0 + 1e-9
    high = 2.0
    while area_mach_relation(high, gamma) < area_ratio:
        high *= 1.5
        if high > 100.0:
            raise RuntimeError("Could not bracket supersonic Mach number.")

    for _ in range(100):
        mid = 0.5 * (low + high)
        if area_mach_relation(mid, gamma) < area_ratio:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def fixed_area_nozzle_performance(
    chamber_pressure_pa: float,
    chamber_temperature_k: float,
    gamma: float,
    gas_constant_j_kg_k: float,
    cstar_m_per_s: float,
    area_ratio: float = 15.0,
    ambient_pressure_pa: float = ct.one_atm,
) -> dict[str, float]:
    """Compute frozen-gamma nozzle performance for a fixed area ratio."""

    exit_mach = supersonic_mach_from_area_ratio(area_ratio, gamma)
    pressure_ratio = (
        1.0 + 0.5 * (gamma - 1.0) * exit_mach**2
    ) ** (-gamma / (gamma - 1.0))
    temperature_ratio = (1.0 + 0.5 * (gamma - 1.0) * exit_mach**2) ** -1.0

    exit_pressure_pa = chamber_pressure_pa * pressure_ratio
    exit_temperature_k = chamber_temperature_k * temperature_ratio
    momentum_cf = math.sqrt(
        (2.0 * gamma**2 / (gamma - 1.0))
        * (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (gamma - 1.0))
        * (1.0 - pressure_ratio ** ((gamma - 1.0) / gamma))
    )
    cf_sea_level = momentum_cf + (
        (exit_pressure_pa - ambient_pressure_pa) * area_ratio / chamber_pressure_pa
    )
    cf_vacuum = momentum_cf + (exit_pressure_pa * area_ratio / chamber_pressure_pa)
    exit_velocity = exit_mach * math.sqrt(
        gamma * gas_constant_j_kg_k * exit_temperature_k
    )

    return {
        "nozzle_area_ratio": area_ratio,
        "exit_mach": exit_mach,
        "exit_pressure_bar": exit_pressure_pa / BAR_TO_PA,
        "exit_temperature_k": exit_temperature_k,
        "exit_velocity_m_per_s": exit_velocity,
        "cf_sea_level": cf_sea_level,
        "cf_vacuum": cf_vacuum,
        "isp_sea_level_s": cstar_m_per_s * cf_sea_level / G0,
        "isp_vacuum_s": cstar_m_per_s * cf_vacuum / G0,
    }


def evaluate_case(
    gas: ct.Solution,
    of_ratio: float,
    pressure_bar: float,
    inlet_temperature_k: float = 298.15,
    ambient_pressure_pa: float = ct.one_atm,
    nozzle_area_ratio: float = 15.0,
) -> EquilibriumCase:
    """Run one HP equilibrium calculation and return rocket performance data."""

    pressure_pa = pressure_bar * BAR_TO_PA
    gas.TPX = inlet_temperature_k, pressure_pa, mixture_moles_for_of(gas, of_ratio)
    gas.equilibrate("HP")

    gamma = gas.cp_mass / gas.cv_mass
    gas_constant = ct.gas_constant / gas.mean_molecular_weight
    cstar = ideal_cstar(gas.T, gamma, gas.mean_molecular_weight)
    cf = ideal_thrust_coefficient(gamma, ambient_pressure_pa / pressure_pa)
    nozzle = fixed_area_nozzle_performance(
        pressure_pa,
        gas.T,
        gamma,
        gas_constant,
        cstar,
        area_ratio=nozzle_area_ratio,
        ambient_pressure_pa=ambient_pressure_pa,
    )
    thermal_conductivity = float(gas.thermal_conductivity)
    viscosity = float(gas.viscosity)
    mole_fractions = {
        species: float(gas.X[gas.species_index(species)])
        for species in TRACKED_SPECIES
        if species in gas.species_names
    }

    return EquilibriumCase(
        of_ratio=float(of_ratio),
        pressure_bar=float(pressure_bar),
        temperature_k=float(gas.T),
        gamma=float(gamma),
        molecular_weight_kg_per_kmol=float(gas.mean_molecular_weight),
        gas_constant_j_kg_k=float(gas_constant),
        density_kg_m3=float(gas.density),
        cp_mass_j_kg_k=float(gas.cp_mass),
        cv_mass_j_kg_k=float(gas.cv_mass),
        sound_speed_m_per_s=float(math.sqrt(gamma * gas_constant * gas.T)),
        viscosity_pa_s=viscosity,
        thermal_conductivity_w_m_k=thermal_conductivity,
        prandtl_number=float(gas.cp_mass * viscosity / thermal_conductivity),
        cstar_m_per_s=float(cstar),
        nozzle_area_ratio=float(nozzle["nozzle_area_ratio"]),
        exit_mach=float(nozzle["exit_mach"]),
        exit_pressure_bar=float(nozzle["exit_pressure_bar"]),
        exit_temperature_k=float(nozzle["exit_temperature_k"]),
        exit_velocity_m_per_s=float(nozzle["exit_velocity_m_per_s"]),
        cf_sea_level=float(nozzle["cf_sea_level"]),
        cf_vacuum=float(nozzle["cf_vacuum"]),
        isp_sea_level_s=float(nozzle["isp_sea_level_s"]),
        isp_vacuum_s=float(nozzle["isp_vacuum_s"]),
        cf_ideal_1atm=float(cf),
        isp_ideal_1atm_s=float(cstar * cf / G0),
        mole_fractions=mole_fractions,
    )


def run_equilibrium_sweep(
    of_values: Iterable[float],
    pressure_values_bar: Iterable[float],
    mechanism: str = MECHANISM,
) -> list[dict[str, float]]:
    """Evaluate a grid of O/F ratios and chamber pressures."""

    gas = ct.Solution(mechanism)
    rows: list[dict[str, float]] = []
    for pressure_bar in pressure_values_bar:
        for of_ratio in of_values:
            rows.append(evaluate_case(gas, of_ratio, pressure_bar).as_row())
    return rows


def run_pressure_sweep(
    pressure_values_bar: Iterable[float],
    of_ratio: float,
    mechanism: str = MECHANISM,
) -> list[dict[str, float]]:
    """Evaluate pressure effects at a selected O/F ratio."""

    gas = ct.Solution(mechanism)
    return [
        evaluate_case(gas, of_ratio=of_ratio, pressure_bar=pressure_bar).as_row()
        for pressure_bar in pressure_values_bar
    ]
