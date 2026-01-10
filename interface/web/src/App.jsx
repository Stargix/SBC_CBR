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
  '#0f766e', // Teal (original)
  '#f59e0b', // Amber
  '#ec4899', // Pink
  '#8b5cf6', // Purple
  '#3b82f6', // Blue
  '#10b981', // Emerald
  '#f97316', // Orange
  '#06b6d4', // Cyan
  '#a855f7', // Violet
  '#14b8a6', // Teal bright
  '#ef4444', // Red
  '#22c55e', // Green
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
  const [feedbackMode, setFeedbackMode] = useState(null)
  const [feedbackScores, setFeedbackScores] = useState({ price: 3, cultural: 3, flavor: 3, overall: 3 })
  const [feedbackLoading, setFeedbackLoading] = useState(false)
  const [simulationCount, setSimulationCount] = useState(1) // Added simulation count state

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

  const handleSimulation = async () => {
    setSyntheticLoading(true)
    setError('')
    try {
      for (let i = 0; i < simulationCount; i++) {
        const response = await fetch(`${API_BASE}/synthetic`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ use_llm: true }),
        })

        if (!response.ok) {
          const detail = await response.json()
          throw new Error(detail?.detail?.error || 'Simulation failed')
        }

        const data = await response.json()
        if (data.trace) {
          setTrace(data.trace)
          setSyntheticResult(null)
          await fetchEmbeddings()
        } else {
          setTrace(null)
          setSyntheticResult(data)
        }

        // Small delay to ensure UI updates are visible
        await new Promise(r => setTimeout(r, 500))
      }
    } catch (err) {
      setError(err.message || 'Simulation error')
    } finally {
      setSyntheticLoading(false)
    }
  }

  const handleFeedback = async (menuIndex) => {
    if (!trace) return
    setFeedbackLoading(true)
    setError('')
    try {
      const menu = trace.proposed_menus[menuIndex]
      const payload = {
        request: trace.request,
        menu_id: menu.menu.id,
        price_satisfaction: feedbackScores.price,
        cultural_satisfaction: feedbackScores.cultural,
        flavor_satisfaction: feedbackScores.flavor,
        overall_satisfaction: feedbackScores.overall,
      }

      const response = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Feedback submission failed')
      }

      const data = await response.json()
      setFeedbackMode(null)
      setFeedbackScores({ price: 3, cultural: 3, flavor: 3, overall: 3 })
      setError('')
      // Mostrar mensaje de éxito brevemente
      const successMsg = data.case_retained ? 'Feedback guardado y caso añadido a la base' : 'Feedback procesado'
      setError(successMsg)
      setTimeout(() => setError(''), 3000)
      await fetchEmbeddings()
    } catch (err) {
      setError(err.message || 'Feedback error')
    } finally {
      setFeedbackLoading(false)
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
              Price min
              <input type="number" value={form.price_min} onChange={handleChange('price_min')} />
            </label>
            <label>
              Price max
              <input type="number" value={form.price_max} onChange={handleChange('price_max')} />
            </label>
            <label>
              Guests
              <input type="number" value={form.num_guests} onChange={handleChange('num_guests')} />
            </label>
            <label>
              Wine pairing
              <select value={form.wants_wine ? 'yes' : 'no'} onChange={(e) => setForm({ ...form, wants_wine: e.target.value === 'yes' })}>
                <option value="yes">Yes, include wine</option>
                <option value="no">No wine</option>
              </select>
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
              <input
                type="number"
                min="1"
                max="15"
                value={simulationCount}
                onChange={(e) => setSimulationCount(Math.min(15, Math.max(1, parseInt(e.target.value) || 1)))}
                className="simulation-input"
              />
              <button type="button" className="secondary" onClick={handleSimulation} disabled={syntheticLoading}>
                Simulación
              </button>
            </div>
          </form>
          {error && <p className={error.startsWith('✅') ? 'success-message' : 'error'}>{error}</p>}
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

              {feedbackMode === 0 ? (
                <div className="feedback-form">
                  <h5>Evaluar menú</h5>

                  <label>
                    Precio <span className="score-display">{feedbackScores.price.toFixed(1)}</span>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.5"
                      value={feedbackScores.price}
                      onChange={(e) => setFeedbackScores({ ...feedbackScores, price: parseFloat(e.target.value) })}
                    />
                  </label>

                  <label>
                    Cultura <span className="score-display">{feedbackScores.cultural.toFixed(1)}</span>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.5"
                      value={feedbackScores.cultural}
                      onChange={(e) => setFeedbackScores({ ...feedbackScores, cultural: parseFloat(e.target.value) })}
                    />
                  </label>

                  <label>
                    Sabor <span className="score-display">{feedbackScores.flavor.toFixed(1)}</span>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.5"
                      value={feedbackScores.flavor}
                      onChange={(e) => setFeedbackScores({ ...feedbackScores, flavor: parseFloat(e.target.value) })}
                    />
                  </label>

                  <label>
                    General <span className="score-display">{feedbackScores.overall.toFixed(1)}</span>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.5"
                      value={feedbackScores.overall}
                      onChange={(e) => setFeedbackScores({ ...feedbackScores, overall: parseFloat(e.target.value) })}
                    />
                  </label>

                  <div className="feedback-actions">
                    <button
                      className="primary"
                      onClick={() => handleFeedback(0)}
                      disabled={feedbackLoading}
                    >
                      {feedbackLoading ? 'Enviando...' : 'Enviar'}
                    </button>
                    <button
                      className="secondary"
                      onClick={() => setFeedbackMode(null)}
                      disabled={feedbackLoading}
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  className="evaluate-btn"
                  onClick={() => {
                    setFeedbackMode(0)
                    setFeedbackScores({ price: 3, cultural: 3, flavor: 3, overall: 3 })
                  }}
                >
                  Evaluar
                </button>
              )}

              <div className="menus">
                {trace.proposed_menus.slice(0, 1).map((menu, idx) => (
                  <div key={menu.rank} className="menu-card">
                    <div className="menu-header">
                      <h4>Menú Propuesto</h4>
                      <span className="price-badge">{menu.menu.total_price?.toFixed(2) || '—'}€</span>
                    </div>

                    <div className="course">
                      <strong>Entrante:</strong> {menu.menu.starter.name}
                      <span className="ingredients">{menu.menu.starter.ingredients?.join(', ') || ''}</span>
                    </div>

                    <div className="course">
                      <strong>Principal:</strong> {menu.menu.main_course.name}
                      <span className="ingredients">{menu.menu.main_course.ingredients?.join(', ') || ''}</span>
                    </div>

                    <div className="course">
                      <strong>Postre:</strong> {menu.menu.dessert.name}
                      <span className="ingredients">{menu.menu.dessert.ingredients?.join(', ') || ''}</span>
                    </div>

                    <div className="course">
                      <strong>Bebida:</strong> {menu.menu.beverage.name}
                    </div>

                    {menu.validation?.explanations && menu.validation.explanations.length > 0 && (
                      <div className="validation-note">
                        {menu.validation.explanations.map((exp, i) => (
                          <div key={i}>• {exp}</div>
                        ))}
                      </div>
                    )}

                    <div className="menu-meta">
                      <span>Similitud: {(menu.similarity * 100).toFixed(1)}%</span>
                      <span>Calidad: {menu.validation?.score ? `${menu.validation.score.toFixed(1)}/100` : '—'}</span>
                    </div>
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
                  {syntheticResult.llm_evaluation || syntheticResult.llm_summary || 'Evaluación en proceso. Verifica la consola del backend o ejecuta más solicitudes.'}
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
