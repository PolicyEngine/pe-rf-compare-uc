import { useState, useEffect } from 'react'
import './App.css'

function parseCSV(text) {
  const lines = text.trim().split('\n')
  const headers = lines[0].split(',')
  return lines.slice(1).map(line => {
    const values = line.split(',')
    const obj = {}
    headers.forEach((header, i) => {
      let val = values[i]
      if (val && val.startsWith('"') && val.endsWith('"')) {
        val = val.slice(1, -1)
      }
      if (val && !isNaN(val) && val !== '') {
        obj[header] = parseFloat(val)
      } else if (val === '' || val === 'None') {
        obj[header] = null
      } else {
        obj[header] = val
      }
    })
    return obj
  })
}

function formatValue(val, unit, pct) {
  if (val === null || val === undefined) return '—'
  let str = ''
  if (unit === '£') str = `£${val.toLocaleString()}`
  else if (unit === 'bn') str = `£${val}bn`
  else if (unit === '%') str = `${val}%`
  else if (unit === 'k') str = `${val.toLocaleString()}k`
  else if (unit === 'm') str = `${val}m`
  else str = `${val}${unit}`
  if (pct !== null && pct !== undefined) str += ` (${pct}%)`
  return str
}

function formatDiff(val, unit) {
  if (val === null || val === undefined) return '—'
  const sign = val >= 0 ? '+' : ''
  if (unit === '£') return `${sign}£${val}`
  if (unit === 'bn') return `${sign}£${val}bn`
  if (unit === '%') return `${sign}${val}pp`
  if (unit === 'k') return `${sign}${val}k`
  if (unit === 'm') return `${sign}${val}m`
  return `${sign}${val}${unit}`
}

function StatusDot({ status }) {
  return <span className={`status-dot ${status}`}></span>
}

function ComparisonTable({ data }) {
  return (
    <div className="comparison-table-wrapper">
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th className="rf-col">RF</th>
            <th className="pe-col">PE</th>
            <th>Difference</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} className={row.status}>
              <td className="metric-name">{row.metric}</td>
              <td className="rf-value">{formatValue(row.rf_value, row.rf_unit, row.rf_pct)}</td>
              <td className="pe-value">{formatValue(row.pe_value, row.pe_unit, row.pe_pct)}</td>
              <td className={`diff-value ${row.diff_value >= 0 ? 'positive' : 'negative'}`}>
                {formatDiff(row.diff_value, row.rf_unit)}
              </td>
              <td className="status-cell"><StatusDot status={row.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ElementsChart({ elements }) {
  const maxVal = Math.max(...elements.map(e => e.expenditure_bn))
  return (
    <div className="elements-section">
      <div className="elements-chart">
        {elements.map((el, i) => (
          <div key={i} className="element-row">
            <span className="element-label">{el.element}</span>
            <div className="bar-container">
              <div className="bar" style={{ width: `${(el.expenditure_bn / maxVal) * 100}%` }} />
              <span className="bar-value">£{el.expenditure_bn}bn ({el.pct_gross}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function App() {
  const [metadata, setMetadata] = useState(null)
  const [comparison, setComparison] = useState([])
  const [elements, setElements] = useState([])
  const [policyImpacts, setPolicyImpacts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadData() {
      try {
        const [metaRes, compRes, elemRes, policyRes] = await Promise.all([
          fetch('/data/metadata.csv'),
          fetch('/data/comparison.csv'),
          fetch('/data/uc_elements.csv'),
          fetch('/data/policy_impacts.csv')
        ])
        const [metaText, compText, elemText, policyText] = await Promise.all([
          metaRes.text(), compRes.text(), elemRes.text(), policyRes.text()
        ])
        setMetadata(parseCSV(metaText)[0])
        setComparison(parseCSV(compText))
        setElements(parseCSV(elemText))
        setPolicyImpacts(parseCSV(policyText))
        setLoading(false)
      } catch (err) {
        setError(err.message)
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) return <div className="loading">Loading data...</div>
  if (error) return <div className="error">Error: {error}</div>

  const benefitCap = policyImpacts.filter(p => p.category === 'benefit_cap')
  const selfEmp = policyImpacts.find(p => p.category === 'self_employment')
  const carers = policyImpacts.find(p => p.category === 'carers')

  return (
    <div className="app">
      <header className="title-row">
        <div className="title-row-inner">
          <h1>Resolution Foundation vs PolicyEngine UK</h1>
          <div className="meta-info">
            <span>📄 {metadata?.rf_report}</span>
            <span>🔧 PolicyEngine v{metadata?.policyengine_version}</span>
            <span>📅 {metadata?.generated}</span>
          </div>
        </div>
      </header>

      <main className="main-content">
        <p className="dashboard-intro">
          This dashboard compares Universal Credit statistics from the Resolution Foundation's
          "Listen and Learn" report with PolicyEngine UK microsimulation estimates. Values show
          budgetary impacts and population counts for {metadata?.pe_year}.
        </p>

        <section className="section">
          <h2>PolicyEngine vs RF comparison</h2>
          <p className="section-description">
            Comparing key UC statistics. Green dots indicate close matches; yellow indicates
            moderate differences; red indicates large gaps requiring investigation.
          </p>
          <ComparisonTable data={comparison} />
          <div className="table-legend">
            <span className="legend-item"><StatusDot status="close_match" /> Close match</span>
            <span className="legend-item"><StatusDot status="moderate_diff" /> Moderate difference</span>
            <span className="legend-item"><StatusDot status="large_discrepancy" /> Large gap</span>
          </div>
        </section>

        <section className="section">
          <h2>Policy reform impacts</h2>
          <div className="key-metrics-row">
            <div className="key-metric highlighted">
              <div className="metric-label">Benefit cap reduction</div>
              <div className="metric-number">
                £{benefitCap.find(p => p.metric === 'Total annual reduction')?.value}m
              </div>
            </div>
            <div className="key-metric">
              <div className="metric-label">Households capped</div>
              <div className="metric-number">
                {benefitCap.find(p => p.metric === 'Households affected')?.value}k
              </div>
            </div>
            <div className="key-metric">
              <div className="metric-label">Self-employed on UC</div>
              <div className="metric-number">{selfEmp?.value}m</div>
            </div>
            <div className="key-metric">
              <div className="metric-label">Carers on UC</div>
              <div className="metric-number">{carers?.value}m</div>
            </div>
          </div>
        </section>

        <section className="section">
          <h2>UC elements breakdown</h2>
          <p className="section-description">
            Annual expenditure by UC element (gross, before taper).
          </p>
          <ElementsChart elements={elements} />
        </section>

        <section className="section">
          <h2>Why estimates differ</h2>
          <div className="explainer-grid">
            <div className="explainer-card">
              <h4>Entitlement vs receipt</h4>
              <p>PolicyEngine calculates who is <strong>entitled</strong> to UC. RF reports
              who <strong>actually claims</strong>. Take-up is ~80-85% overall.</p>
            </div>
            <div className="explainer-card">
              <h4>Different time periods</h4>
              <p>RF projections are for April 2026 (post-migration) and 2029-30 (expenditure).
              PE shows {metadata?.pe_year} under current rules.</p>
            </div>
            <div className="explainer-card">
              <h4>Data sources</h4>
              <p>RF uses DWP administrative data (StatXplore). PE uses Family Resources
              Survey microsimulation.</p>
            </div>
          </div>
        </section>

        <footer className="footer">
          <p>Data: Resolution Foundation "Listen and Learn" (Jan 2026) | PolicyEngine UK v{metadata?.policyengine_version}</p>
          <p>
            <a href="https://policyengine.org" target="_blank" rel="noopener">PolicyEngine</a>
            {' · '}
            <a href="https://github.com/PolicyEngine/pe-rf-compare-uc" target="_blank" rel="noopener">GitHub</a>
          </p>
        </footer>
      </main>
    </div>
  )
}

export default App
