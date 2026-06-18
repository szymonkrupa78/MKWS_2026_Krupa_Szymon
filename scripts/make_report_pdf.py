#!/usr/bin/env python3
"""Build the nine-page technical report from generated project results."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    import pandas as pd
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError as exc:
    raise SystemExit("Install report dependencies first: pip install -r requirements.txt") from exc


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("\n", " "), style)


def data_table(
    rows: list[list[object]],
    widths: list[float] | None = None,
    font_size: float = 8.2,
) -> Table:
    item = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    item.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9ecef")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#a7b0b8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("LEADING", (0, 0), (-1, -1), font_size + 1.6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return item


def report_image(path: Path, width_cm: float) -> Image:
    item = Image(str(path))
    aspect = item.imageHeight / item.imageWidth
    item.drawWidth = width_cm * cm
    item.drawHeight = item.drawWidth * aspect
    return item


def bullet(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(f"&bull;&nbsp; {text}", style)


def page_decor(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#c7cdd2"))
        canvas.line(1.7 * cm, 1.15 * cm, A4[0] - 1.7 * cm, 1.15 * cm)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(1.7 * cm, 0.72 * cm, "MKWS 2026 - Szymon Krupa")
        canvas.drawRightString(A4[0] - 1.7 * cm, 0.72 * cm, str(doc.page - 1))
    canvas.restoreState()


def main() -> None:
    data_dir = ROOT / "data" / "processed"
    figure_dir = ROOT / "figures"
    report_dir = ROOT / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    results = pd.read_csv(data_dir / "equilibrium_sweep.csv")
    pressure = pd.read_csv(data_dir / "pressure_sweep.csv")
    summary = pd.read_csv(data_dir / "summary_metrics.csv")
    history = pd.read_csv(data_dir / "port_regression_history.csv")

    ref = results[results["pressure_bar"] == 20.0].copy()
    selected = ref[ref["of_ratio"].isin([4.0, 5.5, 6.0, 8.0, 10.0])]
    best_cstar = summary[summary["metric"] == "maximum_cstar_at_20_bar"].iloc[0]
    best_vac = summary[summary["metric"] == "maximum_vacuum_isp_at_20_bar"].iloc[0]
    best_sl = summary[summary["metric"] == "maximum_sea_level_isp_at_20_bar"].iloc[0]
    stoich = float(summary[summary["metric"] == "stoichiometric_of_ratio"].iloc[0]["value"])
    best_temp = ref.loc[ref["temperature_k"].idxmax()]
    h0 = history.iloc[0]
    h1 = history.iloc[-1]
    p0 = pressure.iloc[0]
    p1 = pressure.iloc[-1]

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyReport", parent=styles["BodyText"], fontSize=9.3, leading=12.2, spaceAfter=6))
    styles.add(ParagraphStyle(name="SmallReport", parent=styles["BodyText"], fontSize=8.2, leading=10.2, spaceAfter=4))
    styles.add(ParagraphStyle(name="CaptionReport", parent=styles["BodyText"], fontSize=7.7, leading=9.2, alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceAfter=6))
    styles.add(ParagraphStyle(name="SectionReport", parent=styles["Heading1"], fontSize=14.2, leading=16.5, spaceBefore=2, spaceAfter=7))
    styles.add(ParagraphStyle(name="SubsectionReport", parent=styles["Heading2"], fontSize=11.2, leading=13.0, spaceBefore=5, spaceAfter=4))
    styles.add(ParagraphStyle(name="EquationReport", parent=styles["BodyText"], fontName="Courier", fontSize=8.8, leading=11.0, leftIndent=1.0 * cm, spaceBefore=3, spaceAfter=6))
    styles.add(ParagraphStyle(name="TitleReport", parent=styles["Title"], fontSize=22, leading=26, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="SubtitleReport", parent=styles["Normal"], fontSize=12, leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#333333")))

    body = styles["BodyReport"]
    small = styles["SmallReport"]
    caption = styles["CaptionReport"]
    section = styles["SectionReport"]
    subsection = styles["SubsectionReport"]
    equation = styles["EquationReport"]

    doc = SimpleDocTemplate(
        str(report_dir / "report.pdf"),
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.55 * cm,
        bottomMargin=1.55 * cm,
        title="Thermochemical Performance Study of a N2O/Paraffin Hybrid Rocket Motor",
        author="Szymon Krupa",
    )

    story: list = []

    # Page 1: title page
    story.append(Spacer(1, 2.3 * cm))
    story.append(Paragraph("Thermochemical Performance Study of a N2O/Paraffin Hybrid Rocket Motor Using Cantera", styles["TitleReport"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Computer Methods in Combustion", styles["SubtitleReport"]))
    story.append(Paragraph("Metody komputerowe w spalaniu", styles["SubtitleReport"]))
    story.append(Spacer(1, 1.6 * cm))
    title_rows = [
        ["Author", "Szymon Krupa"],
        ["Coordinator", "dr inz. Mateusz Zbikowski"],
        ["Project type", "Python / Cantera thermochemical analysis"],
        ["Propellant pair", "N2O / paraffin fuel surrogate (C2H4)"],
        ["Number of pages", "9"],
        ["Date", "June 2026"],
    ]
    story.append(data_table(title_rows, [5.0 * cm, 10.8 * cm], font_size=9.2))
    story.append(Spacer(1, 2.0 * cm))
    story.append(Paragraph("Repository", subsection))
    story.append(para("https://github.com/szymonkrupa78/MKWS_2026_Krupa_Szymon", body))
    story.append(PageBreak())

    # Page 2: abstract and contents
    story.append(Paragraph("Abstract", section))
    story.append(para(
        "This project presents a reproducible Python/Cantera study of an idealized nitrous oxide/paraffin hybrid rocket motor. The solid paraffin grain is represented by ethylene (C2H4), a gas-phase surrogate for hydrocarbon pyrolysis products available in GRI-Mech 3.0. The model combines constant-pressure adiabatic equilibrium calculations with ideal frozen-gamma nozzle relations and an illustrative single-port fuel-regression model.",
        body,
    ))
    story.append(para(
        "The analysis evaluates oxidizer-to-fuel mass ratios from 3.0 to 12.0 and chamber pressures from 10 to 80 bar. The main outputs are equilibrium chamber temperature, product composition, heat-capacity ratio, mean molecular weight, transport properties, characteristic velocity, sea-level and vacuum specific impulse, and a time history of the fuel port. The highest characteristic velocity at 20 bar is obtained at O/F = 5.25, while the maximum ideal vacuum specific impulse occurs at O/F = 5.50. Both values are strongly fuel-rich compared with the stoichiometric O/F of 9.41.",
        body,
    ))
    story.append(Paragraph("Project Deliverables", subsection))
    for text_value in [
        "Reusable Cantera thermochemistry and nozzle functions in src/mkws_hybrid.",
        "Generated CSV data for O/F, pressure, and port-regression sweeps.",
        "Eight plots describing chemistry, gas properties, performance, and internal ballistics.",
        "Five unit tests for the most important numerical helpers and physical ranges.",
        "A LaTeX source and this generated technical report.",
    ]:
        story.append(bullet(text_value, small))
    story.append(Paragraph("Contents", subsection))
    contents_rows = [
        ["1", "Introduction and State of the Art", "2"],
        ["2", "Model Description", "3"],
        ["3", "Program Description and Verification", "4"],
        ["4", "O/F Sweep Results", "5"],
        ["5", "Rocket Performance Results", "6"],
        ["6", "Pressure and Transport Results", "7"],
        ["7", "Hybrid Port Regression, Limitations, Conclusions", "8"],
    ]
    story.append(data_table([["Section", "Title", "Page"]] + contents_rows, [1.5 * cm, 12.5 * cm, 1.5 * cm], font_size=8.2))
    story.append(PageBreak())

    # Page 3: introduction and state of the art
    story.append(Paragraph("1 Introduction", section))
    story.append(para(
        "A hybrid rocket motor stores the fuel and oxidizer in different physical phases. In the configuration considered here, the fuel is a solid hydrocarbon grain with a cylindrical port, while nitrous oxide is delivered through the port as the oxidizer. The separated propellants provide operational advantages: the motor can be shut down by stopping oxidizer flow, the solid fuel is comparatively simple to store, and the architecture uses fewer fluid systems than a bipropellant liquid engine.",
        body,
    ))
    story.append(para(
        "Hybrid combustion is nevertheless coupled to internal ballistics. The oxidizer mass flux controls the regression rate of the fuel surface. As the port grows, oxidizer flux, fuel mass flow, mixture ratio, chamber conditions, and thrust can all change. This means that thermochemistry and grain geometry cannot be selected independently.",
        body,
    ))
    story.append(Paragraph("1.1 Objective", subsection))
    story.append(para(
        "The objective is to create a transparent computational tool for preliminary reasoning about a N2O/paraffin motor. The project is intended to answer three questions: which O/F range gives the best ideal thermochemical performance, how chamber pressure changes the predicted state and nozzle performance, and how an illustrative port-regression law moves the motor through the O/F map during an eight-second burn.",
        body,
    ))
    story.append(Paragraph("1.2 State of the Art", subsection))
    story.append(para(
        "Chemical equilibrium is a standard first step in rocket analysis. NASA CEA and similar tools minimize thermodynamic potentials subject to elemental conservation to estimate product composition and theoretical performance. Cantera solves the same class of equilibrium problem and also exposes thermodynamic and transport properties through a Python API. It is therefore well suited to a reproducible coursework project in which every assumption and formula remains visible in source code.",
        body,
    ))
    story.append(para(
        "For hybrid motors, detailed prediction would require multiphase flow, heat transfer into the grain, melting and entrainment of paraffin, surface pyrolysis, finite-rate mixing, injector behavior, and a validated regression correlation. The present work deliberately remains at the preliminary level: it uses gas-phase equilibrium for the chamber, frozen-gamma nozzle equations, and a power-law regression model. These assumptions make trends easy to interpret but prevent the model from serving as final hardware design evidence.",
        body,
    ))
    story.append(PageBreak())

    # Page 4: model description
    story.append(Paragraph("2 Model Description", section))
    story.append(Paragraph("2.1 Reactant Composition", subsection))
    story.append(para(
        "The oxidizer is N2O and the fuel vapor is represented by C2H4. Ethylene is not a complete physical model of paraffin; it is a gas-phase surrogate with an approximate CH2 elemental ratio and is available together with N2O chemistry in gri30.yaml. For a one-kilogram fuel basis, the requested mass O/F determines reactant mole amounts:",
        body,
    ))
    story.append(para("n_f = 1 / M_f,    n_ox = (O/F) / M_ox", equation))
    story.append(para(
        f"The global stoichiometric relation C2H4 + 6 N2O gives a stoichiometric mass ratio O/F = {stoich:.2f}. The sweep from 3.0 to 12.0 therefore includes strongly fuel-rich, near-stoichiometric, and oxidizer-rich cases.",
        body,
    ))
    story.append(Paragraph("2.2 Equilibrium Chamber State", subsection))
    story.append(para(
        "Reactants enter at 298.15 K. Cantera solves an adiabatic constant-pressure equilibrium problem for each O/F and pressure combination. Enthalpy, pressure, and elemental composition are conserved while temperature and species fractions are adjusted to equilibrium:",
        body,
    ))
    story.append(para("h(T, p, Y) = h_initial,    p = p_chamber", equation))
    story.append(para(
        "After equilibrium, the code records temperature, density, cp, cv, heat-capacity ratio gamma, mean molecular weight, specific gas constant, sound speed, viscosity, thermal conductivity, Prandtl number, and selected product mole fractions. The warning generated above 3000 K is retained and reported as a limitation because part of the polynomial thermodynamic database is being extrapolated.",
        body,
    ))
    story.append(Paragraph("2.3 Ideal Nozzle Model", subsection))
    story.append(para(
        "The nozzle uses a fixed expansion area ratio Ae/At = 15. The chamber gamma and gas constant are frozen during expansion. The supersonic exit Mach number is found by numerically inverting the isentropic area-Mach relation. Characteristic velocity is calculated from the equilibrium chamber state:",
        body,
    ))
    story.append(para("c* = sqrt(R T_c / gamma) [(gamma + 1) / 2]^[(gamma + 1)/(2(gamma - 1))]", equation))
    story.append(para(
        "Momentum and pressure-thrust terms produce sea-level and vacuum thrust coefficients. Specific impulse follows from Isp = c* Cf / g0. These values are ideal upper-bound trends and exclude combustion efficiency, divergence, boundary-layer, and two-phase losses.",
        body,
    ))
    story.append(PageBreak())

    # Page 5: program description and verification
    story.append(Paragraph("3 Program Description and Verification", section))
    story.append(para(
        "The repository is organized so that physical calculations, plotting, orchestration, tests, data, and the report are separated. Running one analysis script reproduces the CSV tables and figures; a second script rebuilds the PDF from those outputs.",
        body,
    ))
    structure_rows = [
        ["Path", "Responsibility"],
        ["src/mkws_hybrid/thermochemistry.py", "Equilibrium, gas properties, area-Mach inversion, nozzle performance"],
        ["src/mkws_hybrid/hybrid_model.py", "Single cylindrical port and regression-rate time history"],
        ["src/mkws_hybrid/plotting.py", "Publication-ready plots and report summary panel"],
        ["scripts/run_study.py", "O/F sweep, pressure sweep, CSV export, figure generation"],
        ["scripts/make_report_pdf.py", "Builds this report from generated data"],
        ["tests/test_thermochemistry.py", "Unit and physical-consistency tests"],
    ]
    story.append(data_table(structure_rows, [6.3 * cm, 9.5 * cm], font_size=7.8))
    story.append(Paragraph("3.1 Reproduction", subsection))
    story.append(para("python -m venv .venv", equation))
    story.append(para("source .venv/bin/activate", equation))
    story.append(para("pip install -r requirements.txt", equation))
    story.append(para("python scripts/run_study.py", equation))
    story.append(para("python -m unittest discover -s tests", equation))
    story.append(para("python scripts/make_report_pdf.py", equation))
    story.append(Paragraph("3.2 Tests", subsection))
    test_rows = [
        ["Test", "Purpose", "Result"],
        ["Stoichiometric O/F", "Checks molecular-weight-based N2O/C2H4 ratio", "PASS"],
        ["Mass O/F conversion", "Reconstructs the requested oxidizer/fuel mass ratio", "PASS"],
        ["Area-Mach inverse", "Recovers Ae/At = 15 on the supersonic branch", "PASS"],
        ["Physical chamber case", "Checks T, gamma, c*, Isp, and Prandtl ranges", "PASS"],
        ["Port regression", "Checks increasing port diameter and O/F drift", "PASS"],
    ]
    story.append(data_table(test_rows, [4.0 * cm, 9.8 * cm, 2.0 * cm], font_size=7.6))
    story.append(PageBreak())

    # Page 6: O/F temperature and species
    story.append(Paragraph("4 O/F Sweep Results", section))
    story.append(para(
        f"The adiabatic temperature increases rapidly from fuel-rich conditions and reaches {best_temp.temperature_k:.0f} K near O/F = {best_temp.of_ratio:.2f} at 20 bar. Increasing chamber pressure raises equilibrium temperature because dissociation is suppressed. The temperature maximum remains below the simple stoichiometric O/F = {stoich:.2f}, showing that detailed dissociation and thermodynamic effects shift the optimum.",
        body,
    ))
    story.append(report_image(figure_dir / "adiabatic_temperature_vs_of.png", 13.9))
    story.append(para("Figure 1. Adiabatic equilibrium chamber temperature versus O/F for four chamber pressures.", caption))
    story.append(para(
        "The product plot explains the fuel-rich region. Low O/F gives high CO and H2 fractions. Moving toward stoichiometric conditions increases H2O and CO2, while NO becomes more important at high temperature. The logarithmic scale keeps both major and minor products visible.",
        small,
    ))
    story.append(report_image(figure_dir / "species_vs_of_20bar.png", 13.9))
    story.append(para("Figure 2. Selected equilibrium product mole fractions at 20 bar.", caption))
    story.append(PageBreak())

    # Page 7: performance and gas properties
    story.append(Paragraph("5 Rocket Performance Results", section))
    story.append(para(
        f"Maximum c* at 20 bar is {best_cstar['value']:.0f} m/s at O/F = {best_cstar['of_ratio']:.2f}. Maximum vacuum Isp is {best_vac['value']:.1f} s at O/F = {best_vac['of_ratio']:.2f}; the corresponding sea-level optimum is {best_sl['value']:.1f} s. These optima are much richer than the temperature maximum because the H2/CO-rich products have lower molecular weight.",
        body,
    ))
    story.append(report_image(figure_dir / "performance_vs_of_20bar.png", 13.9))
    story.append(para("Figure 3. Fixed-area-ratio ideal nozzle performance and characteristic velocity at 20 bar.", caption))
    selected_rows = [["O/F", "T [K]", "gamma", "M [kg/kmol]", "c* [m/s]", "Isp,vac [s]"]]
    for _, row in selected.iterrows():
        selected_rows.append([
            f"{row.of_ratio:.2f}",
            f"{row.temperature_k:.0f}",
            f"{row.gamma:.3f}",
            f"{row.molecular_weight_kg_per_kmol:.2f}",
            f"{row.cstar_m_per_s:.0f}",
            f"{row.isp_vacuum_s:.1f}",
        ])
    story.append(data_table(selected_rows, [1.5 * cm, 2.2 * cm, 2.0 * cm, 3.1 * cm, 2.6 * cm, 3.0 * cm], font_size=7.8))
    story.append(Spacer(1, 0.15 * cm))
    story.append(report_image(figure_dir / "gamma_molecular_weight_vs_of_20bar.png", 12.8))
    story.append(para("Figure 4. Heat-capacity ratio and mean molecular weight at 20 bar.", caption))
    story.append(PageBreak())

    # Page 8: pressure and transport
    story.append(Paragraph("6 Pressure and Transport Results", section))
    story.append(para(
        f"The pressure sweep is performed at O/F = {best_vac.of_ratio:.2f}. Raising pressure from {p0.pressure_bar:.0f} to {p1.pressure_bar:.0f} bar increases chamber temperature from {p0.temperature_k:.0f} to {p1.temperature_k:.0f} K and vacuum Isp from {p0.isp_vacuum_s:.1f} to {p1.isp_vacuum_s:.1f} s. Sea-level Isp changes much more strongly because a fixed area-ratio nozzle is severely overexpanded at low chamber pressure.",
        body,
    ))
    story.append(report_image(figure_dir / "pressure_sweep.png", 13.9))
    story.append(para("Figure 5. Chamber temperature and ideal specific impulse versus pressure at the best vacuum-Isp O/F.", caption))
    story.append(para(
        "Dynamic viscosity generally follows the temperature trend. The Prandtl number changes more weakly and reflects both temperature and composition. These transport quantities are not used by the present zero-dimensional performance model, but they are recorded for future wall heat-transfer or cooling studies.",
        small,
    ))
    story.append(report_image(figure_dir / "transport_vs_of_20bar.png", 13.9))
    story.append(para("Figure 6. Dynamic viscosity and Prandtl number of equilibrium products at 20 bar.", caption))
    story.append(PageBreak())

    # Page 9: internal ballistics, limitations, conclusions, references
    story.append(Paragraph("7 Hybrid Port Regression", section))
    story.append(para(
        "The illustrative internal-ballistics model uses one cylindrical port, a 0.20 m grain, a fuel density of 900 kg/m3, and a constant oxidizer mass flow of 0.25 kg/s. Fuel regression follows r_dot = a G_ox^n with a = 7.0e-5 and n = 0.62. During the assumed eight-second burn, port diameter increases from 30.0 to 56.9 mm, oxidizer flux falls, and O/F increases from 5.54 to 6.45. The interpolated ideal thrust decreases from approximately 669 to 650 N.",
        small,
    ))
    story.append(report_image(figure_dir / "port_regression_history.png", 10.5))
    story.append(para("Figure 7. Port diameter, O/F ratio, and interpolated ideal thrust during the assumed burn.", caption))
    story.append(Paragraph("7.1 Limitations", subsection))
    story.append(para(
        "The main limitations are the ethylene fuel surrogate, gas-phase equilibrium, ideal reactant states, frozen-gamma nozzle expansion, fixed area ratio, no injector or chamber pressure-loss model, no wall heat transfer, no condensed carbon, and an illustrative rather than experimentally fitted regression coefficient. Some equilibrium temperatures exceed the nominal 3000 K range of part of the mechanism data. Results should therefore be interpreted as ideal trends, not certified motor predictions.",
        small,
    ))
    story.append(Paragraph("7.2 Conclusions", subsection))
    story.append(para(
        f"The study demonstrates that maximum flame temperature is not the same as maximum rocket performance. At 20 bar, best c* and vacuum Isp occur around O/F = {best_cstar.of_ratio:.2f}-{best_vac.of_ratio:.2f}, far below stoichiometry. Pressure moderately improves vacuum performance but strongly changes sea-level expansion matching. The port model also shows that O/F moves during a burn, so thermochemistry, oxidizer flow, and grain geometry must be designed together.",
        small,
    ))
    story.append(Paragraph("References", subsection))
    references = [
        "[1] Cantera Developers, Cantera: chemical kinetics, thermodynamics, and transport processes, https://cantera.org/.",
        "[2] GRI-Mech 3.0 chemical kinetic mechanism, https://combustion.berkeley.edu/gri-mech/.",
        "[3] G. P. Sutton and O. Biblarz, Rocket Propulsion Elements, Wiley.",
        "[4] M. J. Chiaverini and K. K. Kuo, Fundamentals of Hybrid Rocket Combustion and Propulsion, AIAA.",
        "[5] S. Gordon and B. J. McBride, NASA RP-1311: Chemical Equilibrium Compositions and Applications, 1994.",
    ]
    for reference in references:
        story.append(para(reference, styles["SmallReport"]))

    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    print(report_dir / "report.pdf")


if __name__ == "__main__":
    main()

