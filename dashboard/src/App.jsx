import { useState, useEffect } from 'react'
import './App.css'

// CSV parser helper
function parseCSV(text) {
  const lines = text.trim().split('\n')
  const headers = lines[0].split(',')
  return lines.slice(1).map(line => {
    const values = line.split(',')
    const obj = {}
    headers.forEach((header, i) => {
      let val = values[i]
      // Handle quoted values
      if (val && val.startsWith('"') && val.endsWith('"')) {
        val = val.slice(1, -1)
      }
      // Parse numbers
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

function StatusBadge({ status }) {
  const colors = {
    close_match: { bg: '#dcfce7', text: '#166534', label: '✓' },
    moderate_diff: { bg: '#fef3c7', text: '#92400e', label: '~' },
    large_discrepancy: { bg: '#fee2e2', text: '#991b1b', label: '!' }
  }
  const { bg, text, label } = colors[status] || colors.moderate_diff
  return (
    <span style={{ backgroundColor: bg, color: text, padding: '2px 8px', borderRadius: '8px', fontSize: '14px', fontWeight: 600 }}>
      {label}
    </span>
  )
}

function formatValue(val, unit, pct) {
  let str = ''
  if (unit === '£') str = `£${val.toLocaleString()}`
  else if (unit === 'bn') str = `£${val}bn`
  else if (unit === '%') str = `${val}%`
  else if (unit === 'k') str = `${val.toLocaleString()}k`
  else if (unit === 'm') str = `${val}m`
  else str = `${val}${unit}`

  if (pct !== null && pct !== undefined) {
    str += ` (${pct}%)`
  }
  return str
}

function formatDiff(val, unit) {
  const sign = val >= 0 ? '+' : ''
  if (unit === '£') return `${sign}£${val}`
  if (unit === 'bn') return `${sign}£${val}bn`
  if (unit === '%') return `${sign}${val}pp`
  if (unit === 'k') return `${sign}${val}k`
  if (unit === 'm') return `${sign}${val}m`
  return `${sign}${val}${unit}`
}

function ComparisonTable({ data, title }) {
  return (
    <div className="comparison-table-container">
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Resolution Foundation</th>
            <th>PolicyEngine</th>
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
                {row.diff_pct !== null && row.diff_pct !== undefined && ` (${row.diff_pct >= 0 ? '+' : ''}${row.diff_pct}pp)`}
              </td>
              <td className="status-cell"><StatusBadge status={row.status} /></td>
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
    <div className="elements-chart">
      {elements.map((el, i) => (
        <div key={i} className="element-row">
          <span className="element-label">{el.element}</span>
          <div className="bar-container">
            <div
              className="bar"
              style={{ width: `${(el.expenditure_bn / maxVal) * 100}%` }}
            />
            <span className="bar-value">£{el.expenditure_bn}bn ({el.pct_gross}%)</span>
          </div>
        </div>
      ))}
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
          metaRes.text(),
          compRes.text(),
          elemRes.text(),
          policyRes.text()
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
  if (error) return <div className="error">Error loading data: {error}</div>

  const benefitCap = policyImpacts.filter(p => p.category === 'benefit_cap')
  const selfEmp = policyImpacts.find(p => p.category === 'self_employment')
  const carers = policyImpacts.find(p => p.category === 'carers')

  return (
    <div className="dashboard">
      <header>
        <div className="header-content">
          <h1>RF vs PolicyEngine UK</h1>
          <p className="subtitle">Universal Credit Comparison Dashboard</p>
          <div className="meta-info">
            <span>📄 {metadata?.rf_report}</span>
            <span>🔧 PolicyEngine v{metadata?.policyengine_version}</span>
            <span>📅 Generated {metadata?.generated}</span>
          </div>
        </div>
      </header>

      <main>
        <section className="section">
          <h2>RF vs PolicyEngine Comparison</h2>
          <ComparisonTable data={comparison} />
          <div className="table-legend">
            <span><StatusBadge status="close_match" /> Close match</span>
            <span><StatusBadge status="moderate_diff" /> Moderate difference</span>
            <span><StatusBadge status="large_discrepancy" /> Large gap</span>
          </div>
        </section>

        <section className="section">
          <h2>UC Elements Breakdown (PolicyEngine)</h2>
          <ElementsChart elements={elements} />
        </section>

        <section className="section">
          <h2>Policy Reform Impacts</h2>
          <div className="impacts-grid">
            <div className="impact-card">
              <h3>Benefit Cap</h3>
              <div className="impact-stats">
                {benefitCap.map((item, i) => (
                  <div key={i}><strong>{item.value}{item.unit}</strong> {item.metric.toLowerCase()}</div>
                ))}
              </div>
              <p className="impact-note">RF Recommendation #8: Abolish cap for those meeting work requirements</p>
            </div>
            <div className="impact-card">
              <h3>Self-Employment & MIF</h3>
              <div className="impact-stats">
                {selfEmp && <div><strong>{selfEmp.value}{selfEmp.unit}</strong> {selfEmp.metric.toLowerCase()}</div>}
                {carers && <div><strong>{carers.value}{carers.unit}</strong> {carers.metric.toLowerCase()}</div>}
              </div>
              <p className="impact-note">RF Recommendations #1-4: Reform Minimum Income Floor rules</p>
            </div>
          </div>
        </section>

        <section className="section explainer">
          <h2>Why Do Estimates Differ?</h2>
          <div className="explainer-grid">
            <div className="explainer-card">
              <h4>📊 Entitlement vs Receipt</h4>
              <p>PolicyEngine calculates who is <strong>entitled</strong> to UC. RF reports who <strong>actually claims</strong>. Take-up is ~80-85% overall.</p>
            </div>
            <div className="explainer-card">
              <h4>📅 Different Time Periods</h4>
              <p>RF projections are for April 2026 (post-migration) and 2029-30 (expenditure). PE shows {metadata?.pe_year} under current rules.</p>
            </div>
            <div className="explainer-card">
              <h4>📁 Data Sources</h4>
              <p>RF uses DWP administrative data (StatXplore). PE uses Family Resources Survey microsimulation.</p>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <p>Data sources: Resolution Foundation "Listen and Learn" (Jan 2026) | PolicyEngine UK microsimulation</p>
        <p><a href="https://policyengine.org" target="_blank" rel="noopener">PolicyEngine</a> | <a href="https://github.com/PolicyEngine/pe-rf-compare-uc" target="_blank" rel="noopener">GitHub</a></p>
      </footer>
    </div>
  )
}

export default App
