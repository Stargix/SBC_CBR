import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const EVENT_TYPES = [
  'FAMILIAR',
  'WEDDING',
  'CONGRESS',
  'CORPORATE',
  'CHRISTENING',
  'COMMUNION',
]

const SEASONS = ['SPRING', 'SUMMER', 'AUTUMN', 'WINTER']

const STYLES = ['CLASSIC', 'MODERN', 'FUSION', 'REGIONAL', 'SIBARITA', 'GOURMET', 'SUAVE']

const CULTURES = [
  'AMERICAN',
  'CHINESE',
  'FRENCH',
  'INDIAN',
  'ITALIAN',
  'JAPANESE',
  'KOREAN',
  'LEBANESE',
  'MEXICAN',
  'SPANISH',
  'THAI',
  'VIETNAMESE',
]

const PALETTE = [
  '#0f766e',
  '#1d4ed8',
  '#b91c1c',
  '#ca8a04',
  '#0f172a',
  '#9333ea',
  '#0ea5e9',
  '#4d7c0f',
  '#be185d',
  '#ea580c',
  '#16a34a',
  '#475569',
]

const DEFAULT_FORM = {
  event_type: 'FAMILIAR',
  season: 'SPRING',
  num_guests: 50,
  price_min: 20,
  price_max: 60,
  wants_wine: false,
  required_diets: '',
  restricted_ingredients: '',
  preferred_style: '',
  cultural_preference: '',
}

const parseListField = (value) =>
  value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)

function App() {
  const [embeddings, setEmbeddings] = useState([])
  const [selectedCase, setSelectedCase] = useState(null)
  const [colorMode, setColorMode] = useState('culture')
  const [trace, setTrace] = useState(null)
  const [syntheticResult, setSyntheticResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [syntheticLoading, setSyntheticLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState(DEFAULT_FORM)

  const fetchEmbeddings = async () => {
    try {
      const response = await fetch(`${API_BASE}/cases`)
      if (!response.ok) {
        throw new Error('Failed to load embeddings')
      }
      const data = await response.json()
      setEmbeddings(data.embeddings || [])
    } catch (err) {
      setError(err.message || 'Error loading embeddings')
    }
  }

  useEffect(() => {
    fetchEmbeddings()
  }, [])

  const cultureColors = useMemo(() => {
    const map = {}
    const cultures = [...new Set(embeddings.map((item) => item.culture).filter(Boolean))]
    cultures.forEach((culture, index) => {
      map[culture] = PALETTE[index % PALETTE.length]
    })
    return map
  }, [embeddings])

  const extents = useMemo(() => {
    if (!embeddings.length) {
      return { xMin: 0, xMax: 1, yMin: 0, yMax: 1 }
    }
    const xs = embeddings.map((d) => d.umap_1)
    const ys = embeddings.map((d) => d.umap_2)
    return {
      xMin: Math.min(...xs),
      xMax: Math.max(...xs),
      yMin: Math.min(...ys),
      yMax: Math.max(...ys),
    }
  }, [embeddings])

  const points = useMemo(() => {
    const width = 640
    const height = 480
    const pad = 24
    const xRange = extents.xMax - extents.xMin || 1
    const yRange = extents.yMax - extents.yMin || 1

    const scaleX = (value) => pad + ((value - extents.xMin) / xRange) * (width - pad * 2)
    const scaleY = (value) => height - pad - ((value - extents.yMin) / yRange) * (height - pad * 2)

    return embeddings.map((item, idx) => {
      const fill =
        colorMode === 'success'
          ? item.success
            ? '#16a34a'
            : '#dc2626'
          : cultureColors[item.culture] || '#64748b'
      return {
        id: item.case_id || `case-${idx}`,
        x: scaleX(item.umap_1),
        y: scaleY(item.umap_2),
        fill,
        data: item,
      }
    })
  }, [embeddings, extents, colorMode, cultureColors])

  const handleChange = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setSyntheticResult(null)
    try {
      const payload = {
        event_type: form.event_type,
        season: form.season,
        num_guests: Number(form.num_guests),
        price_min: Number(form.price_min),
        price_max: Number(form.price_max),
        wants_wine: form.wants_wine,
        required_diets: parseListField(form.required_diets),
        restricted_ingredients: parseListField(form.restricted_ingredients),
        preferred_style: form.preferred_style || null,
        cultural_preference: form.cultural_preference || null,
      }

      const response = await fetch(`${API_BASE}/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error('Request failed')
      }

      const data = await response.json()
      setTrace(data)
      if (data.retention?.success) {
        await fetchEmbeddings()
      }
    } catch (err) {
      setError(err.message || 'Request error')
    } finally {
      setLoading(false)
    }
  }

  const handleSynthetic = async () => {
    setSyntheticLoading(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE}/synthetic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ use_llm: true }),
      })

      if (!response.ok) {
        const detail = await response.json()
        throw new Error(detail?.detail?.error || 'Synthetic run failed')
      }

      const data = await response.json()
      if (data.trace) {
        setTrace(data.trace)
        setSyntheticResult(null)
      } else {
        setTrace(null)
        setSyntheticResult(data)
      }
    } catch (err) {
      setError(err.message || 'Synthetic error')
    } finally {
      setSyntheticLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Chef Digital CBR Lab</h1>
          <p>Explore cases, traces, and manifold embeddings from the CBR system.</p>
        </div>
        <div className="status">
          <span className="dot" />
          API: {API_BASE}
        </div>
      </header>

      <div className="grid">
        <section className="panel form-panel">
          <h2>Request Builder</h2>
          <form onSubmit={handleSubmit} className="form-grid">
            <label>
              Event
              <select value={form.event_type} onChange={handleChange('event_type')}>
                {EVENT_TYPES.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Season
              <select value={form.season} onChange={handleChange('season')}>
                {SEASONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Guests
              <input type="number" value={form.num_guests} onChange={handleChange('num_guests')} />
            </label>
            <label>
              Price min
              <input type="number" value={form.price_min} onChange={handleChange('price_min')} />
            </label>
            <label>
              Price max
              <input type="number" value={form.price_max} onChange={handleChange('price_max')} />
            </label>
            <label className="checkbox">
              <input type="checkbox" checked={form.wants_wine} onChange={handleChange('wants_wine')} />
              Wants wine
            </label>
            <label>
              Preferred style
              <select value={form.preferred_style} onChange={handleChange('preferred_style')}>
                <option value="">None</option>
                {STYLES.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Cultural preference
              <select value={form.cultural_preference} onChange={handleChange('cultural_preference')}>
                <option value="">None</option>
                {CULTURES.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label className="full">
              Required diets (comma separated)
              <input
                type="text"
                value={form.required_diets}
                onChange={handleChange('required_diets')}
                placeholder="vegan, gluten-free"
              />
            </label>
            <label className="full">
              Restricted ingredients (comma separated)
              <input
                type="text"
                value={form.restricted_ingredients}
                onChange={handleChange('restricted_ingredients')}
                placeholder="nuts, shellfish"
              />
            </label>
            <div className="actions">
              <button type="submit" className="primary" disabled={loading}>
                {loading ? 'Running...' : 'Run request'}
              </button>
              <button type="button" className="secondary" onClick={handleSynthetic} disabled={syntheticLoading}>
                {syntheticLoading ? 'Simulating...' : 'Usuario sintetico'}
              </button>
            </div>
          </form>
          {error && <p className="error">{error}</p>}
          {trace && (
            <div className="trace">
              <h3>Trace summary</h3>
              <div className="stats">
                <div>Retrieved: {trace.stats.cases_retrieved}</div>
                <div>Adapted: {trace.stats.cases_adapted}</div>
                <div>Validated: {trace.stats.cases_validated}</div>
                <div>Rejected: {trace.stats.cases_rejected}</div>
              </div>
              {trace.retention && (
                <p className={`retention-note ${trace.retention.success ? 'success' : ''}`}>
                  Auto-retain: {trace.retention.message}
                </p>
              )}
              <div className="menus">
                {trace.proposed_menus.map((menu) => (
                  <div key={menu.rank} className="menu-card">
                    <h4>Proposal #{menu.rank}</h4>
                    <p>Starter: {menu.menu.starter.name}</p>
                    <p>Main: {menu.menu.main_course.name}</p>
                    <p>Dessert: {menu.menu.dessert.name}</p>
                    <p>Beverage: {menu.menu.beverage.name}</p>
                    <p>Similarity: {(menu.similarity * 100).toFixed(1)}%</p>
                    <p>Status: {menu.validation?.status}</p>
                  </div>
                ))}
              </div>
              <details>
                <summary>Full report</summary>
                <pre>{trace.explanations}</pre>
              </details>
            </div>
          )}
          {syntheticResult && (
            <div className="trace">
              <h3>Synthetic result</h3>
              <p>LLM score: {syntheticResult.llm_score?.toFixed(2) || 'n/a'}</p>
              <details>
                <summary>LLM evaluation</summary>
                <p className="score-hint">Scores (0-5)</p>
                <pre>
                  {syntheticResult.llm_evaluation || 'Sin evaluación disponible.'}
                </pre>
              </details>
            </div>
          )}
        </section>

        <section className="panel manifold-panel">
          <div className="panel-header">
            <h2>Case manifold</h2>
            <div className="controls">
              <label>
                Color
                <select value={colorMode} onChange={(event) => setColorMode(event.target.value)}>
                  <option value="culture">Culture</option>
                  <option value="success">Success</option>
                </select>
              </label>
            </div>
          </div>
          <div className="manifold">
            <svg viewBox="0 0 640 480" role="img" aria-label="UMAP manifold">
              {points.map((point) => (
                <circle
                  key={point.id}
                  cx={point.x}
                  cy={point.y}
                  r={6}
                  fill={point.fill}
                  stroke="#0f172a"
                  strokeWidth={point.data.case_id === selectedCase?.case_id ? 2.5 : 1}
                  onClick={() => setSelectedCase(point.data)}
                />
              ))}
            </svg>
          </div>
          <div className="legend">
            {colorMode === 'culture'
              ? Object.entries(cultureColors).map(([culture, color]) => (
                  <div key={culture} className="legend-item">
                    <span className="swatch" style={{ background: color }} />
                    {culture}
                  </div>
                ))
              : [
                  <div key="success" className="legend-item">
                    <span className="swatch" style={{ background: '#16a34a' }} />Success
                  </div>,
                  <div key="fail" className="legend-item">
                    <span className="swatch" style={{ background: '#dc2626' }} />Failure
                  </div>,
                ]}
          </div>
          {selectedCase && (
            <div className="case-detail">
              <h3>Case detail</h3>
              <p>Event: {selectedCase.event}</p>
              <p>Culture: {selectedCase.culture}</p>
              <p>Success: {selectedCase.success ? 'yes' : 'no'}</p>
              <p>Feedback: {selectedCase.feedback}</p>
              <p>Starter: {selectedCase.starter}</p>
              <p>Main: {selectedCase.main}</p>
              <p>Dessert: {selectedCase.dessert}</p>
              <p>Beverage: {selectedCase.beverage}</p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default App
