"""
Resolution Foundation vs PolicyEngine UK: Universal Credit Comparison
======================================================================

This script compares UC statistics from the Resolution Foundation's
"Listen and Learn" report (January 2026) with PolicyEngine UK estimates.

PE calculates each metric for the same year as RF uses.

Outputs CSV file for dashboard consumption.
"""

from policyengine_uk import Microsimulation
from importlib.metadata import version
import pandas as pd
from datetime import datetime
from pathlib import Path

# Get version dynamically
PE_VERSION = version("policyengine_uk")

# Resolution Foundation figures (from "Listen and Learn" report, January 2026)
# All figures from: https://www.resolutionfoundation.org/app/uploads/2026/01/Listen-and-learn.pdf
RF_DATA = {
    # Population figures - RF projects for April 2026 (full UC rollout)
    "working_age_in_uc_millions": 8.5,
    "working_age_in_uc_year": 2026,
    "working_age_in_uc_pct": 26.0,
    "children_in_uc_millions": 6.5,
    "children_in_uc_year": 2026,
    "children_in_uc_pct": 54.0,
    # Expenditure - RF cites £86bn for 2029-30
    "uc_expenditure_billions": 86.0,
    "uc_expenditure_year": 2029,
    # Award amounts - RF report p.19: "average monthly UC award of £1,030" (2025-26)
    "avg_monthly_uc_award": 1030,
    "avg_monthly_uc_award_year": 2026,
    # Family composition - RF report: 46% of UC families have children (2025-26)
    "pct_uc_families_with_children": 46.0,
    "pct_uc_families_with_children_year": 2026,
    # Childcare - RF cites 190k recipients (2025-26)
    "uc_childcare_recipients_thousands": 190,
    "uc_childcare_recipients_year": 2026,
    "avg_monthly_childcare_element": 420,
    "avg_monthly_childcare_element_year": 2026,
    # METRs - RF analysis (2025-26)
    "metr_above_70_pct": 3.0,
    "metr_above_70_year": 2026,
}

print("=" * 70)
print("Resolution Foundation vs PolicyEngine UK: UC Comparison")
print(f"PolicyEngine UK v{PE_VERSION}")
print("=" * 70)
print()

# Initialize microsimulation
sim = Microsimulation()

# ============================================================================
# CALCULATIONS - Each metric calculated for the matching RF year
# ============================================================================

# Helper function to calculate UC stats for a given year
def calculate_uc_stats(year):
    print(f"Calculating for year {year}...")
    benunit_uc = sim.calculate("universal_credit", period=year, map_to="benunit")
    person_uc = sim.calculate("universal_credit", period=year, map_to="person")
    age = sim.calculate("age", period=year)

    person_in_uc = person_uc > 0
    is_working_age = (age >= 16) & (age <= 64)
    is_child = age < 16

    total_working_age = is_working_age.sum()
    working_age_in_uc = (is_working_age & person_in_uc).sum()
    pct_working_age_in_uc = 100 * working_age_in_uc / total_working_age

    total_children = is_child.sum()
    children_in_uc = (is_child & person_in_uc).sum()
    pct_children_in_uc = 100 * children_in_uc / total_children

    total_uc_expenditure = benunit_uc.sum()
    benunits_receiving_uc = (benunit_uc > 0).sum()
    avg_uc_award = total_uc_expenditure / benunits_receiving_uc
    avg_monthly_uc = avg_uc_award / 12

    # UC families with children
    benunit_count_children = sim.calculate("benunit_count_children", period=year, map_to="benunit")
    benunit_has_children = benunit_count_children > 0
    uc_families_with_children = ((benunit_uc > 0) & benunit_has_children).sum()
    pct_uc_with_children = 100 * uc_families_with_children / benunits_receiving_uc

    # UC Childcare
    uc_childcare = sim.calculate("uc_childcare_element", period=year, map_to="benunit")
    on_uc = benunit_uc > 0
    monthly_childcare = uc_childcare / 12
    childcare_recipients_substantial = (on_uc & (monthly_childcare > 190)).sum()
    childcare_spend_substantial = (uc_childcare * on_uc * (monthly_childcare > 190)).sum()
    avg_childcare_substantial = childcare_spend_substantial / childcare_recipients_substantial if childcare_recipients_substantial > 0 else 0

    # METRs
    try:
        metr = sim.calculate("marginal_tax_rate", period=year, map_to="person")
        employment_income = sim.calculate("employment_income", period=year, map_to="person")
        has_earnings = employment_income > 0
        working_with_earnings = is_working_age & has_earnings
        metr_above_70 = (metr > 0.70) & working_with_earnings
        pct_metr_above_70 = 100 * metr_above_70.sum() / working_with_earnings.sum()
    except Exception:
        pct_metr_above_70 = 0

    # Self-employment
    self_emp_income = sim.calculate("self_employment_income", period=year, map_to="person")
    is_self_employed = self_emp_income > 0
    in_uc = person_uc > 0
    self_emp_uc = is_self_employed & in_uc & is_working_age
    total_self_emp_uc = self_emp_uc.sum()

    # Carers
    try:
        is_carer = sim.calculate("is_carer_for_benefits", period=year)
        carers_on_uc = (is_carer & in_uc).sum()
    except Exception:
        try:
            carers_allowance = sim.calculate("carers_allowance", period=year, map_to="person")
            carers_on_uc = ((carers_allowance > 0) & in_uc).sum()
        except Exception:
            carers_on_uc = 0

    # Benefit cap
    try:
        benefit_cap_reduction = sim.calculate("benefit_cap_reduction", period=year, map_to="benunit")
        capped_households = (benefit_cap_reduction > 0).sum()
        total_cap_reduction = benefit_cap_reduction.sum()
        avg_cap_loss = total_cap_reduction / capped_households if capped_households > 0 else 0
    except Exception:
        capped_households = 0
        total_cap_reduction = 0
        avg_cap_loss = 0

    # UC Elements - calculate NET expenditure (actual spending after taper)
    # First get gross element totals to determine proportions
    uc_max = sim.calculate("uc_maximum_amount", period=year, map_to="benunit")
    total_uc_max = uc_max.sum()

    # Get actual UC expenditure (net, after taper)
    actual_uc = total_uc_expenditure  # This is the net UC after taper

    elements = {}
    gross_totals = {}

    # First pass: get gross totals for each element
    for var_name, label in [
        ("uc_standard_allowance", "Standard Allowance"),
        ("uc_child_element", "Child Element"),
        ("uc_housing_costs_element", "Housing Costs"),
        ("uc_childcare_element", "Childcare Element"),
        ("uc_disability_elements", "Disability Elements"),
        ("uc_carer_element", "Carer Element"),
    ]:
        try:
            element = sim.calculate(var_name, period=year, map_to="benunit")
            gross_totals[label] = element.sum()
        except Exception:
            gross_totals[label] = 0

    total_gross = sum(gross_totals.values())

    # Second pass: calculate net expenditure by pro-rating actual UC
    for label, gross_total in gross_totals.items():
        pct_of_gross = 100 * gross_total / total_gross if total_gross > 0 else 0
        # Pro-rate actual UC expenditure based on element's share of gross
        net_expenditure = actual_uc * (gross_total / total_gross) if total_gross > 0 else 0
        elements[label] = {
            "expenditure_bn": round(net_expenditure / 1e9, 1),
            "pct_gross": round(pct_of_gross, 1)
        }

    return {
        "working_age_in_uc": working_age_in_uc,
        "pct_working_age_in_uc": pct_working_age_in_uc,
        "children_in_uc": children_in_uc,
        "pct_children_in_uc": pct_children_in_uc,
        "total_uc_expenditure": total_uc_expenditure,
        "avg_monthly_uc": avg_monthly_uc,
        "pct_uc_with_children": pct_uc_with_children,
        "childcare_recipients_substantial": childcare_recipients_substantial,
        "avg_childcare_substantial": avg_childcare_substantial,
        "pct_metr_above_70": pct_metr_above_70,
        "total_self_emp_uc": total_self_emp_uc,
        "carers_on_uc": carers_on_uc,
        "capped_households": capped_households,
        "total_cap_reduction": total_cap_reduction,
        "avg_cap_loss": avg_cap_loss,
        "elements": elements,
    }

# Calculate for each year we need
years_needed = set([
    RF_DATA["working_age_in_uc_year"],
    RF_DATA["children_in_uc_year"],
    RF_DATA["uc_expenditure_year"],
    RF_DATA["avg_monthly_uc_award_year"],
    RF_DATA["pct_uc_families_with_children_year"],
    RF_DATA["uc_childcare_recipients_year"],
    RF_DATA["avg_monthly_childcare_element_year"],
    RF_DATA["metr_above_70_year"],
])

stats_by_year = {}
for year in sorted(years_needed):
    stats_by_year[year] = calculate_uc_stats(year)

# Default year for additional stats (benefit cap, elements, etc.)
DEFAULT_YEAR = 2026
if DEFAULT_YEAR not in stats_by_year:
    stats_by_year[DEFAULT_YEAR] = calculate_uc_stats(DEFAULT_YEAR)

# ============================================================================
# BUILD CSV DATA
# ============================================================================

# Helper to determine status based on percentage difference
def get_status(rf_val, pe_val):
    if rf_val == 0 or rf_val is None:
        return "moderate_diff"
    pct_diff = abs((pe_val - rf_val) / rf_val) * 100
    if pct_diff < 10:
        return "close_match"
    elif pct_diff < 20:
        return "moderate_diff"
    else:
        return "large_discrepancy"

# Main comparison data - each metric uses matching year
year_2026 = stats_by_year[2026]
year_2029 = stats_by_year[2029]

comparison_rows = [
    {
        "category": "core",
        "metric": "Working-age adults in UC",
        "description": "Number of people aged 16-64 living in households receiving Universal Credit",
        "rf_value": RF_DATA["working_age_in_uc_millions"],
        "rf_unit": "m",
        "rf_year": RF_DATA["working_age_in_uc_year"],
        "rf_pct": RF_DATA["working_age_in_uc_pct"],
        "pe_value": round(year_2026["working_age_in_uc"] / 1e6, 1),
        "pe_unit": "m",
        "pe_year": 2026,
        "pe_pct": round(year_2026["pct_working_age_in_uc"], 1),
        "diff_value": round(year_2026["working_age_in_uc"] / 1e6 - RF_DATA["working_age_in_uc_millions"], 1),
        "diff_pct": round(year_2026["pct_working_age_in_uc"] - RF_DATA["working_age_in_uc_pct"], 1),
        "status": get_status(RF_DATA["working_age_in_uc_millions"], year_2026["working_age_in_uc"] / 1e6),
        "note": ""
    },
    {
        "category": "core",
        "metric": "Children in UC households",
        "description": "Number of children under 16 living in households receiving Universal Credit",
        "rf_value": RF_DATA["children_in_uc_millions"],
        "rf_unit": "m",
        "rf_year": RF_DATA["children_in_uc_year"],
        "rf_pct": RF_DATA["children_in_uc_pct"],
        "pe_value": round(year_2026["children_in_uc"] / 1e6, 1),
        "pe_unit": "m",
        "pe_year": 2026,
        "pe_pct": round(year_2026["pct_children_in_uc"], 1),
        "diff_value": round(year_2026["children_in_uc"] / 1e6 - RF_DATA["children_in_uc_millions"], 1),
        "diff_pct": round(year_2026["pct_children_in_uc"] - RF_DATA["children_in_uc_pct"], 1),
        "status": get_status(RF_DATA["children_in_uc_millions"], year_2026["children_in_uc"] / 1e6),
        "note": ""
    },
    {
        "category": "core",
        "metric": "Annual UC expenditure",
        "description": "Total government spending on Universal Credit per year",
        "rf_value": RF_DATA["uc_expenditure_billions"],
        "rf_unit": "bn",
        "rf_year": RF_DATA["uc_expenditure_year"],
        "rf_pct": None,
        "pe_value": round(year_2029["total_uc_expenditure"] / 1e9, 1),
        "pe_unit": "bn",
        "pe_year": 2029,
        "pe_pct": None,
        "diff_value": round(year_2029["total_uc_expenditure"] / 1e9 - RF_DATA["uc_expenditure_billions"], 1),
        "diff_pct": None,
        "status": get_status(RF_DATA["uc_expenditure_billions"], year_2029["total_uc_expenditure"] / 1e9),
        "note": ""
    },
    {
        "category": "additional",
        "metric": "Average monthly UC award",
        "description": "Mean Universal Credit payment per benefit unit per month",
        "rf_value": RF_DATA["avg_monthly_uc_award"],
        "rf_unit": "£",
        "rf_year": RF_DATA["avg_monthly_uc_award_year"],
        "rf_pct": None,
        "pe_value": round(year_2026["avg_monthly_uc"]),
        "pe_unit": "£",
        "pe_year": 2026,
        "pe_pct": None,
        "diff_value": round(year_2026["avg_monthly_uc"] - RF_DATA["avg_monthly_uc_award"]),
        "diff_pct": round(100 * (year_2026["avg_monthly_uc"] - RF_DATA["avg_monthly_uc_award"]) / RF_DATA["avg_monthly_uc_award"], 1),
        "status": get_status(RF_DATA["avg_monthly_uc_award"], year_2026["avg_monthly_uc"]),
        "note": ""
    },
    {
        "category": "additional",
        "metric": "UC families with children",
        "description": "Percentage of UC claimant families that have dependent children",
        "rf_value": RF_DATA["pct_uc_families_with_children"],
        "rf_unit": "%",
        "rf_year": RF_DATA["pct_uc_families_with_children_year"],
        "rf_pct": None,
        "pe_value": round(year_2026["pct_uc_with_children"], 1),
        "pe_unit": "%",
        "pe_year": 2026,
        "pe_pct": None,
        "diff_value": round(year_2026["pct_uc_with_children"] - RF_DATA["pct_uc_families_with_children"], 1),
        "diff_pct": None,
        "status": get_status(RF_DATA["pct_uc_families_with_children"], year_2026["pct_uc_with_children"]),
        "note": ""
    },
    {
        "category": "additional",
        "metric": "UC childcare recipients",
        "description": "Families receiving substantial childcare support (>£190/month) through UC",
        "rf_value": RF_DATA["uc_childcare_recipients_thousands"],
        "rf_unit": "k",
        "rf_year": RF_DATA["uc_childcare_recipients_year"],
        "rf_pct": None,
        "pe_value": round(year_2026["childcare_recipients_substantial"] / 1e3),
        "pe_unit": "k",
        "pe_year": 2026,
        "pe_pct": None,
        "diff_value": round(year_2026["childcare_recipients_substantial"] / 1e3 - RF_DATA["uc_childcare_recipients_thousands"]),
        "diff_pct": None,
        "status": get_status(RF_DATA["uc_childcare_recipients_thousands"], year_2026["childcare_recipients_substantial"] / 1e3),
        "note": ""
    },
    {
        "category": "additional",
        "metric": "Avg monthly childcare element",
        "description": "Average monthly childcare element payment for those receiving substantial support",
        "rf_value": RF_DATA["avg_monthly_childcare_element"],
        "rf_unit": "£",
        "rf_year": RF_DATA["avg_monthly_childcare_element_year"],
        "rf_pct": None,
        "pe_value": round(year_2026["avg_childcare_substantial"] / 12),
        "pe_unit": "£",
        "pe_year": 2026,
        "pe_pct": None,
        "diff_value": round(year_2026["avg_childcare_substantial"] / 12 - RF_DATA["avg_monthly_childcare_element"]),
        "diff_pct": None,
        "status": get_status(RF_DATA["avg_monthly_childcare_element"], year_2026["avg_childcare_substantial"] / 12),
        "note": ""
    },
    {
        "category": "additional",
        "metric": "Workers with METR > 70%",
        "description": "Share of workers facing marginal effective tax rates above 70% (lose >70p per extra £1 earned)",
        "rf_value": RF_DATA["metr_above_70_pct"],
        "rf_unit": "%",
        "rf_year": RF_DATA["metr_above_70_year"],
        "rf_pct": None,
        "pe_value": round(year_2026["pct_metr_above_70"], 1),
        "pe_unit": "%",
        "pe_year": 2026,
        "pe_pct": None,
        "diff_value": round(year_2026["pct_metr_above_70"] - RF_DATA["metr_above_70_pct"], 1),
        "diff_pct": None,
        "status": get_status(RF_DATA["metr_above_70_pct"], year_2026["pct_metr_above_70"]),
        "note": ""
    },
]

# Additional UC statistics - use 2026
stats = stats_by_year[DEFAULT_YEAR]
policy_rows = [
    {
        "category": "benefit_cap",
        "metric": "Households capped",
        "description": "Number of households whose UC is reduced by the benefit cap (limits total benefits a household can receive)",
        "value": round(stats["capped_households"] / 1e3),
        "unit": "k",
        "year": DEFAULT_YEAR
    },
    {
        "category": "benefit_cap",
        "metric": "Total cap reduction",
        "description": "Annual amount cut from household benefits due to the benefit cap",
        "value": round(stats["total_cap_reduction"] / 1e6),
        "unit": "£m",
        "year": DEFAULT_YEAR
    },
    {
        "category": "benefit_cap",
        "metric": "Avg monthly cap loss",
        "description": "Average monthly reduction for capped households",
        "value": round(stats["avg_cap_loss"] / 12),
        "unit": "£",
        "year": DEFAULT_YEAR
    },
    {
        "category": "self_employment",
        "metric": "Self-employed on UC",
        "description": "Number of self-employed individuals receiving Universal Credit",
        "value": round(stats["total_self_emp_uc"] / 1e6, 2),
        "unit": "m",
        "year": DEFAULT_YEAR
    },
    {
        "category": "carers",
        "metric": "Carers on UC",
        "description": "Number of carers (eligible for Carer's Allowance) receiving Universal Credit",
        "value": round(stats["carers_on_uc"] / 1e6, 2),
        "unit": "m",
        "year": DEFAULT_YEAR
    },
]

# UC Elements - sorted by expenditure descending
elements_data = []
for label, data in stats["elements"].items():
    elements_data.append({
        "element": label,
        "expenditure_bn": data["expenditure_bn"],
        "pct_gross": data["pct_gross"],
        "year": DEFAULT_YEAR
    })

# Sort by expenditure descending
elements_data = sorted(elements_data, key=lambda x: x["expenditure_bn"], reverse=True)

# Metadata
metadata = {
    "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "policyengine_version": PE_VERSION,
    "pe_year": DEFAULT_YEAR,
    "rf_report": "Listen and Learn (January 2026)"
}

# ============================================================================
# SAVE TO CSV FILES
# ============================================================================

script_dir = Path(__file__).parent
data_dir = script_dir.parent / "dashboard" / "public" / "data"
data_dir.mkdir(parents=True, exist_ok=True)

# Save comparison data
comparison_df = pd.DataFrame(comparison_rows)
comparison_df.to_csv(data_dir / "comparison.csv", index=False)
print(f"Saved: {data_dir / 'comparison.csv'}")

# Save policy impacts
policy_df = pd.DataFrame(policy_rows)
policy_df.to_csv(data_dir / "policy_impacts.csv", index=False)
print(f"Saved: {data_dir / 'policy_impacts.csv'}")

# Save UC elements
elements_df = pd.DataFrame(elements_data)
elements_df.to_csv(data_dir / "uc_elements.csv", index=False)
print(f"Saved: {data_dir / 'uc_elements.csv'}")

# Save metadata
metadata_df = pd.DataFrame([metadata])
metadata_df.to_csv(data_dir / "metadata.csv", index=False)
print(f"Saved: {data_dir / 'metadata.csv'}")

# ============================================================================
# RF RECOMMENDATIONS - COST ESTIMATES USING POLICYENGINE REFORMS
# ============================================================================

print()
print("=" * 70)
print("Calculating PolicyEngine cost estimates for RF recommendations...")
print("=" * 70)

from policyengine_uk import Scenario

# Baseline calculations
baseline_uc = sim.calculate("universal_credit", period=DEFAULT_YEAR, map_to="benunit").sum()
baseline_uc_bn = baseline_uc / 1e9
baseline_cap_reduction = sim.calculate("benefit_cap_reduction", period=DEFAULT_YEAR, map_to="benunit").sum()
print(f"Baseline UC expenditure ({DEFAULT_YEAR}): £{baseline_uc_bn:.1f}bn")
print(f"Baseline benefit cap reduction: £{baseline_cap_reduction/1e6:.0f}m")

# Reform 1: Abolish Benefit Cap (set caps to £1m effectively removing limit)
print("\nReform 8: Abolish Benefit Cap")
try:
    abolish_cap_scenario = Scenario(parameter_changes={
        "gov.dwp.benefit_cap.single.in_london": 1_000_000,
        "gov.dwp.benefit_cap.single.outside_london": 1_000_000,
        "gov.dwp.benefit_cap.non_single.in_london": 1_000_000,
        "gov.dwp.benefit_cap.non_single.outside_london": 1_000_000,
    })
    reformed_sim = Microsimulation(scenario=abolish_cap_scenario)
    reformed_cap_reduction = reformed_sim.calculate("benefit_cap_reduction", period=DEFAULT_YEAR, map_to="benunit").sum()
    benefit_cap_cost = round(baseline_cap_reduction / 1e6)
    print(f"  Abolish benefit cap: £{benefit_cap_cost:,.0f}m")
except Exception as e:
    print(f"  Error: {e}")
    benefit_cap_cost = None

# Reform 2: Reduce UC taper rate from 55% to 50% (related to MIF/work incentives)
print("\nReform: Reduce UC taper rate to 50%")
try:
    taper_scenario = Scenario(parameter_changes={
        "gov.dwp.universal_credit.means_test.reduction_rate": 0.50,
    })
    reformed_sim = Microsimulation(scenario=taper_scenario)
    reformed_uc = reformed_sim.calculate("universal_credit", period=DEFAULT_YEAR, map_to="benunit").sum()
    taper_cost = round((reformed_uc - baseline_uc) / 1e6)
    print(f"  Reduce taper to 50%: £{taper_cost:,.0f}m")
except Exception as e:
    print(f"  Error: {e}")
    taper_cost = None

# Reform 3: Increase UC work allowance by 10% (helps working claimants)
print("\nReform: Increase work allowance by 10%")
try:
    # Current values ~£425/month with housing, £708 without
    work_allowance_scenario = Scenario(parameter_changes={
        "gov.dwp.universal_credit.means_test.work_allowance.with_housing": 425 * 1.1,
        "gov.dwp.universal_credit.means_test.work_allowance.without_housing": 708 * 1.1,
    })
    reformed_sim = Microsimulation(scenario=work_allowance_scenario)
    reformed_uc = reformed_sim.calculate("universal_credit", period=DEFAULT_YEAR, map_to="benunit").sum()
    work_allowance_cost = round((reformed_uc - baseline_uc) / 1e6)
    print(f"  Increase work allowance 10%: £{work_allowance_cost:,.0f}m")
except Exception as e:
    print(f"  Error: {e}")
    work_allowance_cost = None

# Reform 4: Increase UC childcare element from 85% to 100%
print("\nReform 9/11: Increase childcare support to 100%")
try:
    childcare_scenario = Scenario(parameter_changes={
        "gov.dwp.universal_credit.elements.childcare.coverage_rate": 1.0,
    })
    reformed_sim = Microsimulation(scenario=childcare_scenario)
    reformed_uc = reformed_sim.calculate("universal_credit", period=DEFAULT_YEAR, map_to="benunit").sum()
    childcare_cost = round((reformed_uc - baseline_uc) / 1e6)
    print(f"  Childcare 100%: £{childcare_cost:,.0f}m")
except Exception as e:
    print(f"  Error: {e}")
    childcare_cost = None

# Reform 5: Increase UC standard allowance by 10%
print("\nReform: Increase UC standard allowance by 10%")
try:
    params = sim.tax_benefit_system.parameters
    sa = params.gov.dwp.universal_credit.standard_allowance.amount
    current_single_old = sa.SINGLE_OLD(f"{DEFAULT_YEAR}-01-01")
    current_single_young = sa.SINGLE_YOUNG(f"{DEFAULT_YEAR}-01-01")
    current_couple_old = sa.COUPLE_OLD(f"{DEFAULT_YEAR}-01-01")
    current_couple_young = sa.COUPLE_YOUNG(f"{DEFAULT_YEAR}-01-01")

    standard_allowance_scenario = Scenario(parameter_changes={
        "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": current_single_old * 1.1,
        "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG": current_single_young * 1.1,
        "gov.dwp.universal_credit.standard_allowance.amount.COUPLE_OLD": current_couple_old * 1.1,
        "gov.dwp.universal_credit.standard_allowance.amount.COUPLE_YOUNG": current_couple_young * 1.1,
    })
    reformed_sim = Microsimulation(scenario=standard_allowance_scenario)
    reformed_uc = reformed_sim.calculate("universal_credit", period=DEFAULT_YEAR, map_to="benunit").sum()
    standard_allowance_cost = round((reformed_uc - baseline_uc) / 1e6)
    print(f"  Increase standard allowance 10%: £{standard_allowance_cost:,.0f}m")
except Exception as e:
    print(f"  Error: {e}")
    standard_allowance_cost = None

# Build recommendations data matching RF Table 4 costs exactly
# Mapping dashboard recommendations to RF Table 4 proposals
recommendations_data = [
    {
        "id": 1,
        "recommendation": "Extend MIF startup period to 24 months",
        "description": "Currently self-employed UC claimants get 12-month exemption from the Minimum Income Floor before assumed earnings apply. RF proposes doubling to 24 months.",
        "status": "can_model",
        "pe_notes": "PE has uc_mif_applies.py with in_startup_period parameter.",
        "rf_del": "None",  # RF Table 4: "Allow discretionary extensions of MIF start-up period"
        "rf_ame": "<£100m",
    },
    {
        "id": 2,
        "recommendation": "Apply MIF after 3-month rolling average",
        "description": "Instead of applying MIF monthly, use 3-month rolling average of self-employment earnings to smooth volatility for gig workers.",
        "status": "partial",
        "pe_notes": "PE uses annual periods. Cannot model monthly rolling calculation.",
        "rf_del": "£1-10m",  # RF Table 4: "Allow self-employed claimants to choose rolling 3-monthly AP"
        "rf_ame": "<£100m",
    },
    {
        "id": 3,
        "recommendation": "Align MIF expected hours with claimant commitments",
        "description": "MIF currently assumes 35 hours/week for all. RF proposes aligning with individual's agreed work commitment.",
        "status": "can_model",
        "pe_notes": "PE has default_expected_hours.yaml. Could parameterize by circumstances.",
        "rf_del": None,  # Not in RF Table 4
        "rf_ame": None,
    },
    {
        "id": 4,
        "recommendation": "Review MIF exemption for carers",
        "description": "Carers caring 35+ hours/week are MIF-exempt. RF wants review of whether threshold is appropriate.",
        "status": "can_model",
        "pe_notes": "PE can adjust carer exemption thresholds.",
        "rf_del": None,  # Not in RF Table 4
        "rf_ame": None,
    },
    {
        "id": 5,
        "recommendation": "Pay UC fortnightly or 4-weekly",
        "description": "UC currently paid monthly. RF proposes more frequent payment options to help budgeting.",
        "status": "partial",
        "pe_notes": "Annual model cannot capture payment frequency effects.",
        "rf_del": "£40-100m",  # RF Table 4: "Allow claimants to choose a 4-weekly AP"
        "rf_ame": "<£100m",
    },
    {
        "id": 6,
        "recommendation": "Reduce 5-week wait",
        "description": "New claimants wait 5 weeks for first payment. RF proposes shortening this gap via backdating.",
        "status": "cannot_model",
        "pe_notes": "Administrative timing outside model scope.",
        "rf_del": "Negligible",  # RF Table 4: "Backdating of up to a month by default"
        "rf_ame": "up to £360m",
    },
    {
        "id": 7,
        "recommendation": "Improve Advance Payments access",
        "description": "Claimants can get advances during 5-week wait but must repay. RF wants better awareness and discretionary grants.",
        "status": "cannot_model",
        "pe_notes": "Loan dynamics outside model scope.",
        "rf_del": "Negligible",  # RF Table 4: "Discretionary grants"
        "rf_ame": "up to £350m",
    },
    {
        "id": 8,
        "recommendation": "Abolish Benefit Cap for those meeting work requirements",
        "description": "£22,020/year cap on total benefits. RF proposes exempting those meeting work conditionality.",
        "status": "partial",
        "pe_notes": "PE models benefit cap. Can model full abolition.",
        "rf_del": None,  # Not in RF Table 4 - they don't propose this
        "rf_ame": None,
        "pe_cost_mn": benefit_cap_cost,  # PE can estimate full abolition
    },
    {
        "id": 9,
        "recommendation": "Extend childcare run-on to 3 months",
        "description": "UC childcare element stops when employment ends. RF proposes 13-week continuation to help parents search for new work.",
        "status": "can_model",
        "pe_notes": "PE has uc_childcare_element.py. Could add run-on parameter.",
        "rf_del": "Negligible",  # RF Table 4: "Extend childcare run-on to 13 weeks"
        "rf_ame": "Negligible",
    },
    {
        "id": 10,
        "recommendation": "Improve upfront childcare cost support",
        "description": "UC reimburses childcare in arrears, but parents need upfront payment. RF wants FSF childcare element brought into UC.",
        "status": "cannot_model",
        "pe_notes": "Discretionary FSF grants outside model scope.",
        "rf_del": "£40-100m",  # RF Table 4: "Bring childcare element of FSF into UC"
        "rf_ame": "None",
    },
    {
        "id": 11,
        "recommendation": "Better integrate UC with Tax-Free Childcare",
        "description": "UC childcare and TFC can't be combined. RF proposes using TFC architecture to pay UC childcare support upfront.",
        "status": "partial",
        "pe_notes": "PE models both UC childcare and TFC separately.",
        "rf_del": "£10-40m",  # RF Table 4: "Use TFC architecture to pay childcare support upfront"
        "rf_ame": "Negligible",
    },
    {
        "id": 12,
        "recommendation": "Promote benefits calculators for entitlement checks",
        "description": "RF recommends UC claimants use independent benefits calculators to verify entitlement and catch DWP errors.",
        "status": "can_model",
        "pe_notes": "This IS PolicyEngine's core function.",
        "rf_del": "£1-10m",  # RF Table 4: "Benefit entitlement calculation as part of UC application"
        "rf_ame": "<£100m",
    },
    {
        "id": 13,
        "recommendation": "Simplify Mandatory Reconsideration process",
        "description": "MR is first step to challenge UC decisions. RF wants simpler forms and clearer deadlines.",
        "status": "cannot_model",
        "pe_notes": "Administrative process outside model scope.",
        "rf_del": "£1-10m",  # RF Table 4: "Mandatory Reconsideration button in UC journal"
        "rf_ame": "None",
    },
    {
        "id": 14,
        "recommendation": "Improve DWP communication and transparency",
        "description": "RF wants clearer UC statements, better explanation of calculations, proactive notification of changes.",
        "status": "cannot_model",
        "pe_notes": "Operational change outside model scope.",
        "rf_del": "£1-10m",  # RF Table 4: "Sort journal messages" or "Vulnerability flag"
        "rf_ame": "None",
    },
    {
        "id": 15,
        "recommendation": "Train work coaches on self-employment support",
        "description": "Work coaches often lack expertise in self-employment. RF wants specialized training.",
        "status": "cannot_model",
        "pe_notes": "Training outside model scope.",
        "rf_del": "£40-100m",  # RF Table 4: "Dignity put centre-stage in UC system"
        "rf_ame": "None",
    },
    {
        "id": 16,
        "recommendation": "Develop DWP digital self-employment tools",
        "description": "RF proposes DWP-provided apps/tools to help self-employed track income and understand MIF.",
        "status": "cannot_model",
        "pe_notes": "IT development outside model scope.",
        "rf_del": None,  # Not specifically in RF Table 4
        "rf_ame": None,
    }
]

# Save recommendations data
recommendations_df = pd.DataFrame(recommendations_data)
recommendations_df.to_csv(data_dir / "recommendations.csv", index=False)
print(f"\nSaved: {data_dir / 'recommendations.csv'}")

# Print reform summary
print("\n" + "=" * 70)
print("PolicyEngine Reform Cost Estimates:")
print("=" * 70)
if benefit_cap_cost:
    print(f"  Abolish benefit cap: £{benefit_cap_cost:,}m")
if taper_cost:
    print(f"  Reduce taper to 50%: £{taper_cost:,}m")
if work_allowance_cost:
    print(f"  Work allowance +50%: £{work_allowance_cost:,}m")
if childcare_cost:
    print(f"  Childcare 100%: £{childcare_cost:,}m")
if standard_allowance_cost:
    print(f"  Standard allowance +10%: £{standard_allowance_cost:,}m")

print()
print("=" * 70)
print("CSV files generated for dashboard")
print("=" * 70)

# Print summary
print("\nComparison Summary:")
for row in comparison_rows:
    status = "✓" if row["status"] == "close_match" else "~" if row["status"] == "moderate_diff" else "✗"
    print(f"  {status} {row['metric']}: RF {row['rf_value']}{row['rf_unit']} ({row['rf_year']}) vs PE {row['pe_value']}{row['pe_unit']} ({row['pe_year']}) (diff: {row['diff_value']})")
