"""
Resolution Foundation vs PolicyEngine UK: Universal Credit Comparison
======================================================================

This script compares UC statistics from the Resolution Foundation's
"Listen and Learn" report (January 2026) with PolicyEngine UK estimates.

RF Key Statistics (from the report):
- 26% of working-age people live in UC households (8.5 million)
- 54% of children live in UC households (6.5 million)
- £86 billion per year on UC by 2029-30
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
    "projection_date": "April 2026",
    # Additional RF statistics (pages 22, 33, 39-40)
    "avg_monthly_uc_award": 1030,  # £1,030 (page 63)
    "pct_uc_families_with_children": 46.0,  # 46% (page 39)
    "uc_childcare_recipients_thousands": 190,  # 190k families (page 40)
    "avg_monthly_childcare_element": 420,  # £420/month (page 40)
    "metr_above_70_pct": 3.0,  # 3% under UC (Figure 5, page 33)
    "ptr_above_70_pct": 9.0,  # 9% under UC (Figure 5, page 33)
    "advance_takeup_pct": 56.0,  # 56% of new UC recipients (page 22)
    "avg_advance_value": 570,  # £570 average (page 22)
}

print("=" * 70)
print("Resolution Foundation vs PolicyEngine UK: UC Comparison")
print("=" * 70)
print()

# Initialize microsimulation
sim = Microsimulation()

# ============================================================================
# 1. CORE UC STATISTICS - RF vs PE Comparison
# ============================================================================
print("=" * 70)
print("1. CORE UC STATISTICS")
print("=" * 70)

# Calculate PE estimates
benunit_uc = sim.calculate("universal_credit", period=YEAR, map_to="benunit")
person_uc = sim.calculate("universal_credit", period=YEAR, map_to="person")
age = sim.calculate("age", period=YEAR)

person_in_uc = person_uc > 0
is_working_age = (age >= 16) & (age <= 64)
is_child = age < 16

# PE calculations
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

# Print comparison
print()
print(f"{'Metric':<45} {'RF':<20} {'PE':<20} {'Diff':<15}")
print("-" * 100)

# Working-age adults
rf_wa = f"{RF_DATA['working_age_in_uc_millions']}m ({RF_DATA['working_age_in_uc_pct']}%)"
pe_wa = f"{working_age_in_uc/1e6:.1f}m ({pct_working_age_in_uc:.1f}%)"
diff_wa = f"{(working_age_in_uc/1e6 - RF_DATA['working_age_in_uc_millions']):.1f}m"
print(f"{'Working-age adults in UC households':<45} {rf_wa:<20} {pe_wa:<20} {diff_wa:<15}")

# Children
rf_ch = f"{RF_DATA['children_in_uc_millions']}m ({RF_DATA['children_in_uc_pct']}%)"
pe_ch = f"{children_in_uc/1e6:.1f}m ({pct_children_in_uc:.1f}%)"
diff_ch = f"{(children_in_uc/1e6 - RF_DATA['children_in_uc_millions']):.1f}m"
print(f"{'Children in UC households':<45} {rf_ch:<20} {pe_ch:<20} {diff_ch:<15}")

# UC expenditure
rf_exp = f"£{RF_DATA['uc_expenditure_billions']}bn ({RF_DATA['uc_expenditure_year']})"
pe_exp = f"£{total_uc_expenditure/1e9:.1f}bn ({YEAR})"
diff_exp = f"£{(total_uc_expenditure/1e9 - RF_DATA['uc_expenditure_billions']):.1f}bn"
print(f"{'Annual UC expenditure':<45} {rf_exp:<20} {pe_exp:<20} {diff_exp:<15}")

print()
print("PE Additional Stats:")
print(f"  Total working-age population: {total_working_age/1e6:.1f} million")
print(f"  Total children: {total_children/1e6:.1f} million")
print(f"  Benefit units receiving UC: {benunits_receiving_uc/1e6:.2f} million")
print(f"  Average annual UC award: £{avg_uc_award:,.0f}")
print(f"  Average monthly UC award: £{avg_monthly_uc:,.0f}")

# Compare average monthly award with RF
print()
print(f"Average Monthly UC Award Comparison:")
print(f"  RF: £{RF_DATA['avg_monthly_uc_award']:,}")
print(f"  PE: £{avg_monthly_uc:,.0f}")
print(f"  Diff: £{avg_monthly_uc - RF_DATA['avg_monthly_uc_award']:+,.0f}")

# Calculate % of UC families with dependent children
benunit_count_children = sim.calculate("benunit_count_children", period=YEAR, map_to="benunit")
benunit_has_children = benunit_count_children > 0
uc_families_with_children = ((benunit_uc > 0) & benunit_has_children).sum()
pct_uc_with_children = 100 * uc_families_with_children / benunits_receiving_uc

print()
print(f"UC Families with Children:")
print(f"  RF: {RF_DATA['pct_uc_families_with_children']}%")
print(f"  PE: {pct_uc_with_children:.1f}%")
print(f"  Diff: {pct_uc_with_children - RF_DATA['pct_uc_families_with_children']:+.1f}pp")

# ============================================================================
# 2. SELF-EMPLOYMENT & MIF (RF Recommendations #1-4)
# ============================================================================
print()
print("=" * 70)
print("2. SELF-EMPLOYMENT & MIF (RF Recommendations #1-4)")
print("=" * 70)

self_emp_income = sim.calculate("self_employment_income", period=YEAR, map_to="person")
is_self_employed = self_emp_income > 0
in_uc = person_uc > 0

self_emp_uc = is_self_employed & in_uc & is_working_age
total_self_emp = is_self_employed.sum()
total_self_emp_uc = self_emp_uc.sum()

print(f"Self-employed working-age adults: {total_self_emp/1e6:.2f} million")
print(f"Self-employed UC claimants: {total_self_emp_uc/1e6:.2f} million")
print(f"  -> Potentially affected by MIF rules")

# Carers
print()
print("Carers on UC (Recommendation #4):")
try:
    is_carer = sim.calculate("is_carer_for_benefits", period=YEAR)
    carers_on_uc = (is_carer & in_uc).sum()
    print(f"  Carers receiving UC: {carers_on_uc/1e6:.2f} million")
except Exception:
    try:
        carers_allowance = sim.calculate("carers_allowance", period=YEAR, map_to="person")
        carers_on_uc = ((carers_allowance > 0) & in_uc).sum()
        print(f"  Carer's Allowance recipients on UC: {carers_on_uc/1e6:.2f} million")
    except Exception as e:
        carers_on_uc = 0
        print(f"  (Carer status not available: {e})")

# ============================================================================
# 3. BENEFIT CAP (RF Recommendation #8)
# ============================================================================
print()
print("=" * 70)
print("3. BENEFIT CAP (RF Recommendation #8)")
print("=" * 70)

try:
    benefit_cap_reduction = sim.calculate(
        "benefit_cap_reduction", period=YEAR, map_to="benunit"
    )
    capped_households = (benefit_cap_reduction > 0).sum()
    total_cap_reduction = benefit_cap_reduction.sum()
    avg_cap_loss = total_cap_reduction / capped_households if capped_households > 0 else 0

    print(f"Benefit units affected by cap: {capped_households/1e3:.0f} thousand")
    print(f"Total annual reduction from cap: £{total_cap_reduction/1e6:.0f} million")
    print(f"Average annual loss per capped household: £{avg_cap_loss:,.0f}")
    print(f"Average monthly loss: £{avg_cap_loss/12:,.0f}")
    print()
    print(f"RF proposes exempting those meeting work requirements.")
    print(f"Full abolition would restore £{total_cap_reduction/1e6:.0f}m to {capped_households/1e3:.0f}k households.")
except Exception as e:
    capped_households = 0
    total_cap_reduction = 0
    avg_cap_loss = 0
    print(f"Benefit cap data not available: {e}")

# ============================================================================
# 4. UC CHILDCARE (RF Recommendations #9, #11)
# ============================================================================
print()
print("=" * 70)
print("4. UC CHILDCARE (RF Recommendations #9, #11)")
print("=" * 70)

try:
    uc_childcare = sim.calculate("uc_childcare_element", period=YEAR, map_to="benunit")
    childcare_recipients = (uc_childcare > 0).sum()
    total_childcare_spend = uc_childcare.sum()
    avg_childcare = total_childcare_spend / childcare_recipients if childcare_recipients > 0 else 0

    print(f"Benefit units receiving UC childcare: {childcare_recipients/1e3:.0f} thousand")
    print(f"Total UC childcare expenditure: £{total_childcare_spend/1e9:.2f} billion")
    print(f"Average annual childcare element: £{avg_childcare:,.0f}")
    print(f"Average monthly childcare element: £{avg_childcare/12:,.0f}")
except Exception as e:
    childcare_recipients = 0
    total_childcare_spend = 0
    avg_childcare = 0
    print(f"UC childcare data not available: {e}")

# Tax-Free Childcare
print()
print("Tax-Free Childcare (for comparison):")
try:
    tfc = sim.calculate("tax_free_childcare", period=YEAR, map_to="household")
    tfc_recipients = (tfc > 0).sum()
    total_tfc = tfc.sum()
    print(f"  Households receiving TFC: {tfc_recipients/1e3:.0f} thousand")
    print(f"  Total TFC value: £{total_tfc/1e9:.2f} billion")
except Exception as e:
    tfc_recipients = 0
    total_tfc = 0
    print(f"  TFC data not available: {e}")

# ============================================================================
# 4b. MARGINAL TAX RATES (RF Figure 5, page 33)
# ============================================================================
print()
print("=" * 70)
print("4b. MARGINAL EFFECTIVE TAX RATES (RF Figure 5)")
print("=" * 70)

try:
    # Calculate METRs for working-age adults
    metr = sim.calculate("marginal_tax_rate", period=YEAR, map_to="person")
    # Only consider working-age adults with earnings
    employment_income = sim.calculate("employment_income", period=YEAR, map_to="person")
    has_earnings = employment_income > 0
    working_with_earnings = is_working_age & has_earnings

    # METRs above 70%
    metr_above_70 = (metr > 0.70) & working_with_earnings
    pct_metr_above_70 = 100 * metr_above_70.sum() / working_with_earnings.sum()

    print(f"Workers with METR above 70%:")
    print(f"  RF: {RF_DATA['metr_above_70_pct']}%")
    print(f"  PE: {pct_metr_above_70:.1f}%")
    print(f"  Diff: {pct_metr_above_70 - RF_DATA['metr_above_70_pct']:+.1f}pp")
except Exception as e:
    pct_metr_above_70 = None
    print(f"METR data not available: {e}")

# Participation Tax Rates (work incentive for non-workers)
print()
try:
    # PTR measures the effective tax on moving from out-of-work to in-work
    ptr = sim.calculate("participation_tax_rate", period=YEAR, map_to="person")
    # For non-workers who could potentially work
    not_working = (employment_income <= 0) & is_working_age

    # PTRs above 70%
    ptr_above_70 = (ptr > 0.70) & not_working
    total_not_working = not_working.sum()
    pct_ptr_above_70 = 100 * ptr_above_70.sum() / total_not_working if total_not_working > 0 else 0

    print(f"Non-workers with PTR above 70%:")
    print(f"  RF: {RF_DATA['ptr_above_70_pct']}%")
    print(f"  PE: {pct_ptr_above_70:.1f}%")
    print(f"  Diff: {pct_ptr_above_70 - RF_DATA['ptr_above_70_pct']:+.1f}pp")
except Exception as e:
    pct_ptr_above_70 = 0
    print(f"PTR data not available: {e}")

# Set defaults if METR failed
if pct_metr_above_70 is None:
    pct_metr_above_70 = 0

# ============================================================================
# 5. UC ELEMENTS BREAKDOWN
# ============================================================================
print()
print("=" * 70)
print("5. UC ELEMENTS BREAKDOWN")
print("=" * 70)

uc_max = sim.calculate("uc_maximum_amount", period=YEAR, map_to="benunit")
total_uc_max = uc_max.sum()

elements = [
    ("uc_standard_allowance", "Standard Allowance"),
    ("uc_child_element", "Child Element"),
    ("uc_housing_costs_element", "Housing Costs Element"),
    ("uc_childcare_element", "Childcare Element"),
    ("uc_disability_elements", "Disability Elements"),
    ("uc_carer_element", "Carer Element"),
]

print(f"Total UC (net, after taper): £{total_uc_expenditure/1e9:.1f} billion")
print(f"Total UC (gross max): £{total_uc_max/1e9:.1f} billion")
print(f"Taper reduction: £{(total_uc_max - total_uc_expenditure)/1e9:.1f} billion ({100*(total_uc_max - total_uc_expenditure)/total_uc_max:.0f}%)")
print()
print("Breakdown by element:")

element_totals = {}
for var_name, label in elements:
    try:
        element = sim.calculate(var_name, period=YEAR, map_to="benunit")
        element_total = element.sum()
        element_totals[var_name] = element_total
        pct = 100 * element_total / total_uc_max if total_uc_max > 0 else 0
        print(f"  {label}: £{element_total/1e9:.1f}bn ({pct:.1f}% of gross)")
    except Exception:
        element_totals[var_name] = 0
        print(f"  {label}: (not available)")

# ============================================================================
# Generate Markdown Report
# ============================================================================

script_dir = Path(__file__).parent
output_path = script_dir / "rf_pe_uc_comparison_results.md"

markdown_content = f"""# Resolution Foundation vs PolicyEngine UK: UC Comparison

*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}*
*PolicyEngine UK v{PE_VERSION}*

## Overview

This report compares Universal Credit statistics from the Resolution Foundation's
"Listen and Learn" report (January 2026) with PolicyEngine UK microsimulation estimates.

---

## 1. Core UC Statistics Comparison

| Metric | Resolution Foundation | PolicyEngine UK | Difference |
|--------|----------------------|-----------------|------------|
| Working-age adults in UC | {RF_DATA['working_age_in_uc_millions']}m ({RF_DATA['working_age_in_uc_pct']}%) | {working_age_in_uc/1e6:.1f}m ({pct_working_age_in_uc:.1f}%) | {(working_age_in_uc/1e6 - RF_DATA['working_age_in_uc_millions']):+.1f}m ({pct_working_age_in_uc - RF_DATA['working_age_in_uc_pct']:+.1f}pp) |
| Children in UC households | {RF_DATA['children_in_uc_millions']}m ({RF_DATA['children_in_uc_pct']}%) | {children_in_uc/1e6:.1f}m ({pct_children_in_uc:.1f}%) | {(children_in_uc/1e6 - RF_DATA['children_in_uc_millions']):+.1f}m ({pct_children_in_uc - RF_DATA['children_in_uc_pct']:+.1f}pp) |
| Annual UC expenditure | £{RF_DATA['uc_expenditure_billions']}bn ({RF_DATA['uc_expenditure_year']}) | £{total_uc_expenditure/1e9:.1f}bn ({YEAR}) | £{(total_uc_expenditure/1e9 - RF_DATA['uc_expenditure_billions']):+.1f}bn |

### PolicyEngine Population Estimates

| Metric | Value |
|--------|-------|
| Total working-age population (16-64) | {total_working_age/1e6:.1f} million |
| Total children (under 16) | {total_children/1e6:.1f} million |
| Benefit units receiving UC | {benunits_receiving_uc/1e6:.2f} million |
| Average annual UC award | £{avg_uc_award:,.0f} |
| Average monthly UC award | £{avg_monthly_uc:,.0f} |

### Additional RF Comparisons

| Metric | Resolution Foundation | PolicyEngine UK | Difference |
|--------|----------------------|-----------------|------------|
| Average monthly UC award | £{RF_DATA['avg_monthly_uc_award']:,} | £{avg_monthly_uc:,.0f} | £{avg_monthly_uc - RF_DATA['avg_monthly_uc_award']:+,.0f} |
| UC families with children | {RF_DATA['pct_uc_families_with_children']}% | {pct_uc_with_children:.1f}% | {pct_uc_with_children - RF_DATA['pct_uc_families_with_children']:+.1f}pp |
| UC childcare recipients | {RF_DATA['uc_childcare_recipients_thousands']}k | {childcare_recipients/1e3:.0f}k | {childcare_recipients/1e3 - RF_DATA['uc_childcare_recipients_thousands']:+.0f}k |
| Avg monthly childcare element | £{RF_DATA['avg_monthly_childcare_element']} | £{avg_childcare/12:,.0f} | £{avg_childcare/12 - RF_DATA['avg_monthly_childcare_element']:+,.0f} |

---

## 2. Self-Employment & MIF (Recommendations #1-4)

The Minimum Income Floor (MIF) assumes self-employed UC claimants earn at least
minimum wage × 35 hours/week.

| Metric | PolicyEngine UK |
|--------|-----------------|
| Self-employed working-age adults | {total_self_emp/1e6:.2f} million |
| Self-employed UC claimants | {total_self_emp_uc/1e6:.2f} million |
| Carers on UC | {carers_on_uc/1e6:.2f} million |

**RF Recommendations:**
- #1: Extend MIF startup period from 12 to 24 months
- #2: Apply MIF after 3-month rolling average
- #3: Align MIF expected hours with individual work commitments
- #4: Review MIF exemption for carers

---

## 3. Benefit Cap (Recommendation #8)

The benefit cap limits total household benefits to £22,020/year (£25,323 in London).

| Metric | PolicyEngine UK |
|--------|-----------------|
| Benefit units affected by cap | {capped_households/1e3:.0f} thousand |
| Total annual reduction from cap | £{total_cap_reduction/1e6:.0f} million |
| Average annual loss | £{avg_cap_loss:,.0f} |
| Average monthly loss | £{avg_cap_loss/12:,.0f} |

**RF Recommendation #8:** Abolish benefit cap for those meeting work requirements.

**Impact of full abolition:** £{total_cap_reduction/1e6:.0f}m restored to {capped_households/1e3:.0f}k households.

---

## 4. UC Childcare (Recommendations #9, #11)

UC covers 85% of childcare costs up to £1,014/month (1 child) or £1,739/month (2+ children).

| Metric | PolicyEngine UK |
|--------|-----------------|
| Benefit units receiving UC childcare | {childcare_recipients/1e3:.0f} thousand |
| Total UC childcare expenditure | £{total_childcare_spend/1e9:.2f} billion |
| Average annual childcare element | £{avg_childcare:,.0f} |
| Tax-Free Childcare households | {tfc_recipients/1e3:.0f} thousand |
| Total TFC value | £{total_tfc/1e9:.2f} billion |

**RF Recommendations:**
- #9: Extend childcare run-on to 3 months after employment ends
- #11: Better integrate UC childcare with Tax-Free Childcare

---

## 4b. Marginal Tax Rates (RF Figure 5)

High marginal rates (above 70%) reduce work incentives. RF Figure 5 shows the
share of workers facing very high METRs/PTRs under UC.

| Metric | Resolution Foundation | PolicyEngine UK | Difference |
|--------|----------------------|-----------------|------------|
| Workers with METR > 70% | {RF_DATA['metr_above_70_pct']}% | {pct_metr_above_70:.1f}% | {pct_metr_above_70 - RF_DATA['metr_above_70_pct']:+.1f}pp |
| Non-workers with PTR > 70% | {RF_DATA['ptr_above_70_pct']}% | {pct_ptr_above_70:.1f}% | {pct_ptr_above_70 - RF_DATA['ptr_above_70_pct']:+.1f}pp |

**Note:** METRs measure the effective tax on an extra £1 of earnings for current workers.
PTRs measure the effective tax on moving from out-of-work to in-work. Both are affected
by the UC 55% taper rate plus income tax and National Insurance.

---

## 5. UC Elements Breakdown

| Element | Annual Expenditure | % of Gross Max |
|---------|-------------------|----------------|
| **Total UC (net)** | **£{total_uc_expenditure/1e9:.1f}bn** | - |
| **Total UC (gross max)** | **£{total_uc_max/1e9:.1f}bn** | **100%** |
| **Taper reduction** | **£{(total_uc_max - total_uc_expenditure)/1e9:.1f}bn** | **{100*(total_uc_max - total_uc_expenditure)/total_uc_max:.0f}%** |
"""

for var_name, label in elements:
    pct = 100 * element_totals[var_name] / total_uc_max if total_uc_max > 0 else 0
    markdown_content += f"| {label} | £{element_totals[var_name]/1e9:.1f}bn | {pct:.1f}% |\n"

markdown_content += f"""
---

## 6. Explaining the Differences

### Why PE estimates differ from RF:

1. **Entitlement vs Receipt:** PolicyEngine calculates UC **entitlement**, not actual
   claims. Take-up is ~80-85%, so PE overestimates claimant numbers but shows full
   potential reach of UC.

2. **Timing:** RF figures are projections for April 2026 (end of managed migration).
   PE shows {YEAR} entitlement under current rules.

3. **Data Sources:**
   - RF uses DWP StatXplore administrative data
   - PE uses Family Resources Survey (FRS) microsimulation

4. **Expenditure Year:** RF's £86bn is for 2029-30; PE's £{total_uc_expenditure/1e9:.1f}bn is for {YEAR}.

5. **Working Age Definition:** PE uses 16-64; RF may use a different definition
   (e.g., up to State Pension age of 66).

---

## 7. What PolicyEngine Can Model

| RF Recommendation | Modelable? | PE Estimate |
|-------------------|------------|-------------|
| #1-3 MIF reforms | ✅ Yes | {total_self_emp_uc/1e6:.2f}m self-employed UC claimants |
| #4 Carer MIF exemption | ✅ Yes | {carers_on_uc/1e6:.2f}m carers on UC |
| #8 Benefit cap abolition | ✅ Yes | £{total_cap_reduction/1e6:.0f}m to {capped_households/1e3:.0f}k households |
| #9 Childcare run-on | ✅ Yes | {childcare_recipients/1e3:.0f}k receive UC childcare |
| #11 UC/TFC integration | ⚠️ Partial | Policy effects modelable |
| #12 Benefits calculators | ✅ PE does this | PolicyEngine IS this solution |

---

## Sources

- Resolution Foundation "Listen and Learn" report (January 2026)
- PolicyEngine UK microsimulation model v{PE_VERSION}
"""

with open(output_path, "w") as f:
    f.write(markdown_content)

print()
print("=" * 70)
print(f"Report saved to: {output_path}")
print("=" * 70)
