# Resolution Foundation vs PolicyEngine UK: UC Comparison

Interactive dashboard comparing Universal Credit statistics from the Resolution Foundation's "Listen and Learn" report (January 2026) with PolicyEngine UK microsimulation estimates.

## Live Dashboard

**[View Dashboard](https://pe-rf-compare-uc.vercel.app)** (once deployed)

## Key Findings

### Close Matches
| Metric | RF | PE | Difference |
|--------|-----|-----|------------|
| Avg monthly UC award | £1,030 | £1,047 | +1.7% |
| UC families with children | 46% | 49.2% | +3.2pp |
| Working-age in UC | 8.5m | 8.2m | -0.3m |

### Notable Discrepancy: UC Childcare Recipients
- **Resolution Foundation:** 190k families
- **PolicyEngine:** 1,825k families (entitled)
- **Explanation:** PE calculates *entitlement* while RF reports *actual claims*. The ~10% take-up rate for UC childcare suggests significant barriers to claiming (complexity, awareness, integration with other support).

## Why Estimates Differ

1. **Entitlement vs Receipt:** PolicyEngine calculates who is entitled to UC. RF reports who actually claims. Take-up is ~80-85% overall.

2. **Different Time Periods:** RF projections are for April 2026 (post-migration) and 2029-30 (expenditure). PE shows 2025 entitlement.

3. **Data Sources:** RF uses DWP administrative data (StatXplore). PE uses Family Resources Survey (FRS) microsimulation.

## Project Structure

```
pe-rf-compare-uc/
├── dashboard/          # React dashboard (Vite)
│   ├── src/
│   │   ├── App.jsx     # Main dashboard component
│   │   ├── App.css     # Styling
│   │   └── data/
│   │       └── comparison.json  # Comparison data
│   └── package.json
├── scripts/
│   └── rf_pe_uc_comparison.py  # Python script to generate comparison data
└── rf_pe_uc_comparison_results.md  # Markdown report
```

## Development

```bash
# Install dependencies
cd dashboard
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Data Sources

- [Resolution Foundation "Listen and Learn"](https://www.resolutionfoundation.org) (January 2026)
- [PolicyEngine UK](https://policyengine.org) microsimulation model v2.45.4

## License

MIT
