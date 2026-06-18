import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import cantera as ct
import pandas as pd

from mkws_hybrid.hybrid_model import simulate_port_regression
from mkws_hybrid.thermochemistry import (
    FUEL,
    MECHANISM,
    OXIDIZER,
    area_mach_relation,
    evaluate_case,
    mixture_moles_for_of,
    stoichiometric_of_ratio,
    supersonic_mach_from_area_ratio,
)


class HybridThermochemistryTest(unittest.TestCase):
    def test_stoichiometric_of_matches_c2h4_n2o_reaction(self):
        gas = ct.Solution(MECHANISM)
        expected = 6.0 * gas.molecular_weights[gas.species_index(OXIDIZER)]
        expected /= gas.molecular_weights[gas.species_index(FUEL)]
        self.assertAlmostEqual(stoichiometric_of_ratio(), expected, places=8)

    def test_of_ratio_conversion_has_correct_mass_ratio(self):
        gas = ct.Solution(MECHANISM)
        composition = mixture_moles_for_of(gas, of_ratio=6.0)
        fuel_mass = composition[FUEL] * gas.molecular_weights[gas.species_index(FUEL)]
        oxidizer_mass = composition[OXIDIZER] * gas.molecular_weights[gas.species_index(OXIDIZER)]
        self.assertAlmostEqual(oxidizer_mass / fuel_mass, 6.0, places=8)

    def test_area_mach_inverse_on_supersonic_branch(self):
        gamma = 1.24
        mach = supersonic_mach_from_area_ratio(15.0, gamma)
        self.assertGreater(mach, 1.0)
        self.assertAlmostEqual(area_mach_relation(mach, gamma), 15.0, places=6)

    def test_equilibrium_case_is_physical(self):
        gas = ct.Solution(MECHANISM)
        case = evaluate_case(gas, of_ratio=6.0, pressure_bar=20.0)
        self.assertGreater(case.temperature_k, 2500.0)
        self.assertTrue(1.0 < case.gamma < 1.4)
        self.assertGreater(case.cstar_m_per_s, 1000.0)
        self.assertGreater(case.isp_vacuum_s, case.isp_sea_level_s)
        self.assertGreater(case.prandtl_number, 0.0)

    def test_port_regression_changes_geometry_and_of_ratio(self):
        rows = []
        gas = ct.Solution(MECHANISM)
        for of_ratio in [5.0, 6.0, 7.0]:
            rows.append(evaluate_case(gas, of_ratio=of_ratio, pressure_bar=20.0).as_row())
        history = simulate_port_regression(pd.DataFrame(rows), burn_time_s=1.0, dt_s=0.2)
        self.assertGreater(history["port_diameter_mm"].iloc[-1], history["port_diameter_mm"].iloc[0])
        self.assertGreater(history["of_ratio"].iloc[-1], history["of_ratio"].iloc[0])


if __name__ == "__main__":
    unittest.main()

