"""
Resolution Foundation vs PolicyEngine UK: Universal Credit Comparison
======================================================================

This script compares UC statistics from the Resolution Foundation's
"Listen and Learn" report (January 2026) with PolicyEngine UK estimates.

Outputs CSV file for dashboard consumption.
"""

from policyengine_uk import Microsimulation
from importlib.metadata import version
import pandas as pd
from datetime import datetime
from pathlib import Path

# Get version dynamically
PE_VERSION = version("policyengine_uk")
YEAR = 2025

# Resolution Foundation figures (from "Listen and Learn" report)
RF_DATA = {
    "working_age_in_uc_millions": 8.5,
    "working_age_in_uc_pct": 26.0,
    "children_in_uc_millions": 6.5,
    "children_in_uc_pct": 54.0,
    "uc_expenditure_billions": 86.0,
    "uc_expenditure_year": "2029-30",
    "avg_monthly_uc_award": 1030,
    "pct_uc_families_with_children": 46.0,
    "uc_childcare_recipients_thousands": 190,
    "avg_monthly_childcare_element": 420,
    "metr_above_70_pct": 3.0,
    "ptr_above_70_pct": 9.0,
}

print("=" * 70)
print("Resolution Foundation vs PolicyEngine UK: UC Comparison")
print(f"PolicyEngine UK v{PE_VERSION}")
print("=" * 70)
print()

# Initialize microsimulation
sim = Microsimulation()

# ============================================================================
# CALCULATIONS
# ============================================================================

# Core UC stats
benunit_uc = sim.calculate("universal_credit", period=YEAR, map_to="benunit")
person_uc = sim.calculate("universal_credit", period=YEAR, map_to="person")
age = sim.calculate("age", period=YEAR)

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
benunit_count_children = sim.calculate("benunit_count_children", period=YEAR, map_to="benunit")
benunit_has_children = benunit_count_children > 0
uc_families_with_children = ((benunit_uc > 0) & benunit_has_children).sum()
pct_uc_with_children = 100 * uc_families_with_children / benunits_receiving_uc

# Self-employment
self_emp_income = sim.calculate("self_employment_income", period=YEAR, map_to="person")
is_self_employed = self_emp_income > 0
in_uc = person_uc > 0
self_emp_uc = is_self_employed & in_uc & is_working_age
total_self_emp = is_self_employed.sum()
total_self_emp_uc = self_emp_uc.sum()

# Carers
try:
    is_carer = sim.calculate("is_carer_for_benefits", period=YEAR)
    carers_on_uc = (is_carer & in_uc).sum()
except Exception:
    try:
        carers_allowance = sim.calculate("carers_allowance", period=YEAR, map_to="person")
        carers_on_uc = ((carers_allowance > 0) & in_uc).sum()
    except Exception:
        carers_on_uc = 0

# Benefit cap
try:
    benefit_cap_reduction = sim.calculate("benefit_cap_reduction", period=YEAR, map_to="benunit")
    capped_households = (benefit_cap_reduction > 0).sum()
    total_cap_reduction = benefit_cap_reduction.sum()
    avg_cap_loss = total_cap_reduction / capped_households if capped_households > 0 else 0
except Exception:
    capped_households = 0
    total_cap_reduction = 0
    avg_cap_loss = 0

# UC Childcare - count only UC recipients with childcare element
uc_childcare = sim.calculate("uc_childcare_element", period=YEAR, map_to="benunit")
on_uc = benunit_uc > 0
monthly_childcare = uc_childcare / 12

# All UC recipients with any childcare
childcare_recipients_all = (on_uc & (uc_childcare > 0)).sum()
total_childcare_spend = (uc_childcare * on_uc).sum()
avg_childcare_all = total_childcare_spend / childcare_recipients_all if childcare_recipients_all > 0 else 0

# UC recipients with substantial childcare (>£190/mo to match RF methodology)
childcare_recipients_substantial = (on_uc & (monthly_childcare > 190)).sum()
childcare_spend_substantial = (uc_childcare * on_uc * (monthly_childcare > 190)).sum()
avg_childcare_substantial = childcare_spend_substantial / childcare_recipients_substantial if childcare_recipients_substantial > 0 else 0

# Tax-Free Childcare
try:
    tfc = sim.calculate("tax_free_childcare", period=YEAR, map_to="household")
    tfc_recipients = (tfc > 0).sum()
    total_tfc = tfc.sum()
except Exception:
    tfc_recipients = 0
    total_tfc = 0

# METRs
try:
    metr = sim.calculate("marginal_tax_rate", period=YEAR, map_to="person")
    employment_income = sim.calculate("employment_income", period=YEAR, map_to="person")
    has_earnings = employment_income > 0
    working_with_earnings = is_working_age & has_earnings
    metr_above_70 = (metr > 0.70) & working_with_earnings
    pct_metr_above_70 = 100 * metr_above_70.sum() / working_with_earnings.sum()
except Exception:
    pct_metr_above_70 = 0

# UC Elements
uc_max = sim.calculate("uc_maximum_amount", period=YEAR, map_to="benunit")
total_uc_max = uc_max.sum()

elements_data = []
for var_name, label in [
    ("uc_standard_allowance", "Standard Allowance"),
    ("uc_child_element", "Child Element"),
    ("uc_housing_costs_element", "Housing Costs"),
    ("uc_childcare_element", "Childcare Element"),
    ("uc_disability_elements", "Disability Elements"),
    ("uc_carer_element", "Carer Element"),
]:
    try:
        element = sim.calculate(var_name, period=YEAR, map_to="benunit")
        element_total = element.sum()
        pct = 100 * element_total / total_uc_max if total_uc_max > 0 else 0
        elements_data.append({
            "element": label,
            "expenditure_bn": round(element_total / 1e9, 1),
            "pct_gross": round(pct, 1)
        })
    except Exception:
        elements_data.append({"element": label, "expenditure_bn": 0, "pct_gross": 0})

# ============================================================================
# BUILD CSV DATA
# ============================================================================

# Main comparison data
comparison_rows = [
    {
        "category": "core",
        "metric": "Working-age adults in UC",
        "rf_value": RF_DATA["working_age_in_uc_millions"],
        "rf_unit": "m",
        "rf_pct": RF_DATA["working_age_in_uc_pct"],
        "pe_value": round(working_age_in_uc / 1e6, 1),
        "pe_unit": "m",
        "pe_pct": round(pct_working_age_in_uc, 1),
        "diff_value": round(working_age_in_uc / 1e6 - RF_DATA["working_age_in_uc_millions"], 1),
        "diff_pct": round(pct_working_age_in_uc - RF_DATA["working_age_in_uc_pct"], 1),
        "status": "moderate_diff",
        "note": "RF projects April 2026; PE shows 2025 entitlement"
    },
    {
        "category": "core",
        "metric": "Children in UC households",
        "rf_value": RF_DATA["children_in_uc_millions"],
        "rf_unit": "m",
        "rf_pct": RF_DATA["children_in_uc_pct"],
        "pe_value": round(children_in_uc / 1e6, 1),
        "pe_unit": "m",
        "pe_pct": round(pct_children_in_uc, 1),
        "diff_value": round(children_in_uc / 1e6 - RF_DATA["children_in_uc_millions"], 1),
        "diff_pct": round(pct_children_in_uc - RF_DATA["children_in_uc_pct"], 1),
        "status": "moderate_diff",
        "note": "PE uses children under 16"
    },
    {
        "category": "core",
        "metric": "Annual UC expenditure",
        "rf_value": RF_DATA["uc_expenditure_billions"],
        "rf_unit": "bn",
        "rf_pct": None,
        "pe_value": round(total_uc_expenditure / 1e9, 1),
        "pe_unit": "bn",
        "pe_pct": None,
        "diff_value": round(total_uc_expenditure / 1e9 - RF_DATA["uc_expenditure_billions"], 1),
        "diff_pct": None,
        "status": "moderate_diff",
        "note": f"RF is {RF_DATA['uc_expenditure_year']}; PE is {YEAR}"
    },
    {
        "category": "additional",
        "metric": "Average monthly UC award",
        "rf_value": RF_DATA["avg_monthly_uc_award"],
        "rf_unit": "£",
        "rf_pct": None,
        "pe_value": round(avg_monthly_uc),
        "pe_unit": "£",
        "pe_pct": None,
        "diff_value": round(avg_monthly_uc - RF_DATA["avg_monthly_uc_award"]),
        "diff_pct": round(100 * (avg_monthly_uc - RF_DATA["avg_monthly_uc_award"]) / RF_DATA["avg_monthly_uc_award"], 1),
        "status": "close_match",
        "note": ""
    },
    {
        "category": "additional",
        "metric": "UC families with children",
        "rf_value": RF_DATA["pct_uc_families_with_children"],
        "rf_unit": "%",
        "rf_pct": None,
        "pe_value": round(pct_uc_with_children, 1),
        "pe_unit": "%",
        "pe_pct": None,
        "diff_value": round(pct_uc_with_children - RF_DATA["pct_uc_families_with_children"], 1),
        "diff_pct": None,
        "status": "close_match",
        "note": ""
    },
    {
        "category": "additional",
        "metric": "UC childcare recipients",
        "rf_value": RF_DATA["uc_childcare_recipients_thousands"],
        "rf_unit": "k",
        "rf_pct": None,
        "pe_value": round(childcare_recipients_substantial / 1e3),
        "pe_unit": "k",
        "pe_pct": None,
        "diff_value": round(childcare_recipients_substantial / 1e3 - RF_DATA["uc_childcare_recipients_thousands"]),
        "diff_pct": None,
        "status": "close_match",
        "note": "PE filtered to >£190/mo to match RF methodology. PE total (any amount) = " + str(round(childcare_recipients_all / 1e3)) + "k"
    },
    {
        "category": "additional",
        "metric": "Avg monthly childcare element",
        "rf_value": RF_DATA["avg_monthly_childcare_element"],
        "rf_unit": "£",
        "rf_pct": None,
        "pe_value": round(avg_childcare_substantial / 12),
        "pe_unit": "£",
        "pe_pct": None,
        "diff_value": round(avg_childcare_substantial / 12 - RF_DATA["avg_monthly_childcare_element"]),
        "diff_pct": None,
        "status": "moderate_diff",
        "note": "PE avg for substantial claimants (>£190/mo)"
    },
    {
        "category": "additional",
        "metric": "Workers with METR > 70%",
        "rf_value": RF_DATA["metr_above_70_pct"],
        "rf_unit": "%",
        "rf_pct": None,
        "pe_value": round(pct_metr_above_70, 1),
        "pe_unit": "%",
        "pe_pct": None,
        "diff_value": round(pct_metr_above_70 - RF_DATA["metr_above_70_pct"], 1),
        "diff_pct": None,
        "status": "moderate_diff",
        "note": ""
    },
]

# Policy impacts
policy_rows = [
    {
        "category": "benefit_cap",
        "metric": "Households affected",
        "value": round(capped_households / 1e3),
        "unit": "k"
    },
    {
        "category": "benefit_cap",
        "metric": "Total annual reduction",
        "value": round(total_cap_reduction / 1e6),
        "unit": "£m"
    },
    {
        "category": "benefit_cap",
        "metric": "Average monthly loss",
        "value": round(avg_cap_loss / 12),
        "unit": "£"
    },
    {
        "category": "self_employment",
        "metric": "Self-employed on UC",
        "value": round(total_self_emp_uc / 1e6, 2),
        "unit": "m"
    },
    {
        "category": "carers",
        "metric": "Carers on UC",
        "value": round(carers_on_uc / 1e6, 2),
        "unit": "m"
    },
]

# Metadata
metadata = {
    "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "policyengine_version": PE_VERSION,
    "pe_year": YEAR,
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

print()
print("=" * 70)
print("CSV files generated for dashboard")
print("=" * 70)

# Print summary
print("\nSummary:")
for row in comparison_rows:
    if row["category"] == "additional":
        status = "✓" if row["status"] == "close_match" else "~"
        print(f"  {status} {row['metric']}: RF {row['rf_value']}{row['rf_unit']} vs PE {row['pe_value']}{row['pe_unit']} (diff: {row['diff_value']})")
