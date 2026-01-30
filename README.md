# Resolution Foundation vs PolicyEngine UK: UC Comparison

Interactive dashboard comparing Universal Credit statistics from the Resolution Foundation's "Listen and Learn" report (January 2026) with PolicyEngine UK microsimulation estimates.

## Live Dashboard

**[View Dashboard](https://pe-rf-compare-uc.vercel.app)**

## Key Comparisons

### Population & Expenditure (2026)
| Metric | RF | PE | Difference |
|--------|-----|-----|------------|
| Working-age adults in UC | 8.5m (26%) | 8.3m (19%) | -0.2m |
| Children in UC households | 6.5m (54%) | 5.3m (42%) | -1.2m |
| Annual UC expenditure (2029) | £86bn | £90.8bn | +£4.8bn |

### Award Amounts & Demographics (2026)
| Metric | RF | PE | Difference |
|--------|-----|-----|------------|
| Avg monthly UC award | £1,030 | £1,082 | +£52 |
| UC families with children | 46% | 49.3% | +3.3pp |
| UC childcare recipients | 190k | 189k | -1k |

## RF Recommendations Assessment

The dashboard also assesses which of RF's 16 policy recommendations can be modelled using PolicyEngine UK:
- **5** can be fully modelled
- **4** can be partially modelled
- **7** cannot be modelled (administrative/operational changes)

## Project Structure

```
pe-rf-compare-uc/
├── dashboard/                    # React dashboard (Vite)
│   ├── public/data/              # CSV data files
│   │   ├── comparison.csv
│   │   ├── policy_impacts.csv
│   │   ├── uc_elements.csv
│   │   └── metadata.csv
│   └── src/
│       ├── App.jsx               # Main dashboard component
│       ├── App.css               # PolicyEngine styling
│       └── index.css             # Design system variables
├── scripts/
│   └── rf_pe_uc_comparison.py    # Python script to generate CSV data
└── README.md
```

## Development

### Generate comparison data
```bash
conda activate python313
python scripts/rf_pe_uc_comparison.py
```

### Run dashboard locally
```bash
cd dashboard
npm install
npm run dev
```

### Deploy to Vercel
```bash
cd dashboard
npm run build
npx vercel --prod
```

## Data Sources

- [Resolution Foundation "Listen and Learn" report (January 2026)](https://www.resolutionfoundation.org/app/uploads/2026/01/Listen-and-learn.pdf)
- [PolicyEngine UK](https://policyengine.org) microsimulation model v2.72.2

## License

MIT
