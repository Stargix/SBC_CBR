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
  const [simulationCount, setSimulationCount] = useState(1)
  const [viewMode, setViewMode] = useState('main') // 'main' or 'statistics'
  const [statistics, setStatistics] = useState(null)
  const [statsLoading, setStatsLoading] = useState(false)

  // Debug: log viewMode changes
  useEffect(() => {
    console.log('[ViewMode Changed]', viewMode)
  }, [viewMode])

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
    setSyntheticResult(null)
    setTrace(null)
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

      // Check if there was an error in the simulation
      if (data.error) {
        throw new Error(data.error + (data.details ? '\n\n' + data.details : ''))
      }

      // El simulador retorna info de la interacción, no un trace completo
      setSyntheticResult(data)

      // Siempre recargar embeddings porque el simulador guarda casos automáticamente
      await fetchEmbeddings()

      // Si estamos viendo estadísticas, recargarlas también
      if (viewMode === 'statistics') {
        const statsResponse = await fetch(`${API_BASE}/statistics`)
        if (statsResponse.ok) {
          const statsData = await statsResponse.json()
          setStatistics(statsData)
        }
      }
    } catch (err) {
      setError(err.message || 'Synthetic error')
      console.error('Synthetic error:', err)
    } finally {
      setSyntheticLoading(false)
    }
  }

  const handleSimulation = async () => {
    setSyntheticLoading(true)
    setError('')
    setSyntheticResult(null)
    setTrace(null)
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

        // Check if there was an error in the simulation
        if (data.error) {
          throw new Error(data.error + (data.details ? '\n\n' + data.details : ''))
        }

        setSyntheticResult(data)

        // Siempre recargar embeddings después de cada simulación
        await fetchEmbeddings()

        // Small delay to ensure UI updates are visible
        await new Promise(r => setTimeout(r, 500))
      }
    } catch (err) {
      setError(err.message || 'Simulation error')
      console.error('Simulation error:', err)
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
      // Mostrar mensaje de éxito o motivo de no retención
      const successMsg = data.retention_message
        ? data.retention_message
        : data.case_retained
          ? 'Feedback guardado y caso añadido a la base'
          : 'Feedback procesado'
      setError(successMsg)
      setTimeout(() => setError(''), 3000)
      await fetchEmbeddings()
      if (viewMode === 'statistics') {
        await fetchStatistics()
      }
    } catch (err) {
      setError(err.message || 'Feedback error')
    } finally {
      setFeedbackLoading(false)
    }
  }

  const fetchStatistics = async (silent = false) => {
    console.log('[fetchStatistics] Called with silent:', silent)
    if (!silent) setStatsLoading(true)
    if (!silent) setError('')
    try {
      console.log('[fetchStatistics] Fetching from:', `${API_BASE}/statistics`)
      const response = await fetch(`${API_BASE}/statistics`)
      console.log('[fetchStatistics] Response status:', response.status)
      if (!response.ok) {
        throw new Error('Failed to load statistics')
      }
      const data = await response.json()
      console.log('[fetchStatistics] Data received:', Object.keys(data))
      setStatistics(data)
      if (!silent) {
        console.log('[fetchStatistics] Setting viewMode to statistics')
        setViewMode('statistics')
      }
    } catch (err) {
      console.error('[fetchStatistics] Error:', err)
      if (!silent) setError(err.message || 'Error loading statistics')
    } finally {
      if (!silent) setStatsLoading(false)
    }
  }

  // Auto-refresco cada 3s mientras se está viendo estadísticas
  useEffect(() => {
    if (viewMode !== 'statistics') {
      return
    }

    // Primera carga inmediata
    const doFetch = async () => {
      try {
        const response = await fetch(`${API_BASE}/statistics`)
        if (response.ok) {
          const data = await response.json()
          setStatistics(data)
        }
      } catch (e) {
        // Ignorar errores en auto-refresh
      }
    }
    doFetch()

    const intervalId = setInterval(doFetch, 3000)

    return () => {
      clearInterval(intervalId)
    }
  }, [viewMode])

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Chef Digital CBR Lab</h1>
          <p>Explore cases, traces, and manifold embeddings from the CBR system.</p>
        </div>
        <div className="header-actions">
          <div className="nav-buttons">
            <a
              href={`${API_BASE}/reports/index.html`}
              target="_blank"
              rel="noopener noreferrer"
              className="nav-button"
            >
              📊 Tests Precomputados
            </a>
            <button
              className={`nav-button ${viewMode === 'statistics' ? 'active' : ''}`}
              onClick={() => {
                console.log('[Button Click] Statistics button clicked')
                fetchStatistics()
              }}
              disabled={statsLoading}
            >
              {statsLoading ? '⏳ Cargando...' : '📈 Estadísticas'}
            </button>
            {viewMode === 'statistics' && (
              <button
                className="nav-button"
                onClick={() => setViewMode('main')}
              >
                ← Volver al Lab
              </button>
            )}
          </div>
          <div className="status">
            <span className="dot" />
            API: {API_BASE}
          </div>
        </div>
      </header>

      {viewMode === 'statistics' ? (
        <div className="statistics-view">
          {console.log('[Render] Statistics view - statsLoading:', statsLoading, 'statistics:', !!statistics)}
          <section className="panel statistics-panel">
            <h2>📊 Evolución del Sistema</h2>

            {statsLoading && !statistics && (
              <div className="loading-message">
                <p>⏳ Cargando estadísticas...</p>
              </div>
            )}

            {statistics && statistics.learning_history && (
              <div className="stats-section">
                <h3>🎯 Historial de Aprendizaje de Pesos</h3>
                <div className="metadata">
                  <span>Total de iteraciones: {statistics.learning_history.metadata.total_iterations}</span>
                  <span>Tasa de aprendizaje: {statistics.learning_history.metadata.learning_rate}</span>
                  <span>Rango de pesos: [{statistics.learning_history.metadata.min_weight}, {statistics.learning_history.metadata.max_weight}]</span>
                </div>

                <div className="weight-evolution">
                  <h4>📈 Evolución de Pesos Principales</h4>
                  <div className="chart-container">
                    <svg viewBox="0 0 800 400" className="line-chart">
                      <defs>
                        <linearGradient id="grid-gradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#0f766e" stopOpacity="0.1" />
                          <stop offset="100%" stopColor="#0f766e" stopOpacity="0" />
                        </linearGradient>
                      </defs>

                      {/* Grid lines */}
                      {[0, 0.1, 0.2, 0.3, 0.4, 0.5].map((val, i) => {
                        const y = 350 - (val * 600);
                        return (
                          <g key={i}>
                            <line x1="50" y1={y} x2="750" y2={y} stroke="#e1dacf" strokeWidth="1" strokeDasharray="4,4" />
                            <text x="30" y={y + 5} fontSize="12" fill="#5b6474">{val.toFixed(1)}</text>
                          </g>
                        );
                      })}

                      {/* Weight lines */}
                      {['event_type', 'price_range', 'cultural', 'dietary', 'style'].map((weightKey, wIdx) => {
                        const colors = ['#0f766e', '#f59e0b', '#ec4899', '#8b5cf6', '#3b82f6'];
                        const color = colors[wIdx];
                        const points = statistics.learning_history.history.map((entry, idx) => {
                          const x = 50 + (idx / Math.max(statistics.learning_history.history.length - 1, 1)) * 700;
                          const y = 350 - (entry.weights[weightKey] * 600);
                          return { x, y, value: entry.weights[weightKey] };
                        });

                        const pathData = points.map((p, i) =>
                          `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
                        ).join(' ');

                        return (
                          <g key={weightKey}>
                            <path d={pathData} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                            {points.map((p, i) => (
                              <circle key={i} cx={p.x} cy={p.y} r="4" fill={color} stroke="white" strokeWidth="2">
                                <title>{weightKey}: {p.value.toFixed(3)}</title>
                              </circle>
                            ))}
                          </g>
                        );
                      })}

                      {/* X-axis labels */}
                      {statistics.learning_history.history.map((entry, idx) => {
                        const x = 50 + (idx / Math.max(statistics.learning_history.history.length - 1, 1)) * 700;
                        return (
                          <text key={idx} x={x} y="380" fontSize="12" fill="#5b6474" textAnchor="middle">
                            {entry.iteration}
                          </text>
                        );
                      })}

                      {/* Axis labels */}
                      <text x="400" y="395" fontSize="14" fill="#0f172a" textAnchor="middle" fontWeight="600">Iteración</text>
                      <text x="15" y="200" fontSize="14" fill="#0f172a" textAnchor="middle" fontWeight="600" transform="rotate(-90, 15, 200)">Peso</text>
                    </svg>

                    <div className="chart-legend">
                      {['event_type', 'price_range', 'cultural', 'dietary', 'style'].map((key, idx) => {
                        const colors = ['#0f766e', '#f59e0b', '#ec4899', '#8b5cf6', '#3b82f6'];
                        const labels = ['Evento', 'Precio', 'Cultural', 'Dieta', 'Estilo'];
                        return (
                          <div key={key} className="legend-item">
                            <span className="legend-dot" style={{ background: colors[idx] }}></span>
                            <span>{labels[idx]}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <h4>⭐ Evolución de Scores de Feedback</h4>
                  <div className="chart-container">
                    <svg viewBox="0 0 800 300" className="bar-chart">
                      {/* Grid lines */}
                      {[0, 1, 2, 3, 4, 5].map((val, i) => {
                        const y = 250 - (val * 40);
                        return (
                          <g key={i}>
                            <line x1="50" y1={y} x2="750" y2={y} stroke="#e1dacf" strokeWidth="1" strokeDasharray="4,4" />
                            <text x="30" y={y + 5} fontSize="12" fill="#5b6474">{val}</text>
                          </g>
                        );
                      })}

                      {/* Bars */}
                      {statistics.learning_history.history.map((entry, idx) => {
                        const barWidth = Math.min(40, 700 / statistics.learning_history.history.length - 10);
                        const x = 50 + (idx / Math.max(statistics.learning_history.history.length, 1)) * 700 + 10;
                        const height = entry.feedback_score * 40;
                        const y = 250 - height;
                        const color = entry.feedback_score >= 4 ? '#16a34a' : entry.feedback_score >= 2.5 ? '#f59e0b' : '#dc2626';

                        return (
                          <g key={idx}>
                            <rect x={x} y={y} width={barWidth} height={height} fill={color} rx="4">
                              <title>Iteración {entry.iteration}: {entry.feedback_score.toFixed(1)}</title>
                            </rect>
                            <text x={x + barWidth / 2} y={y - 5} fontSize="11" fill={color} textAnchor="middle" fontWeight="600">
                              {entry.feedback_score.toFixed(1)}
                            </text>
                            <text x={x + barWidth / 2} y="270" fontSize="11" fill="#5b6474" textAnchor="middle">
                              {entry.iteration}
                            </text>
                          </g>
                        );
                      })}

                      <text x="400" y="290" fontSize="14" fill="#0f172a" textAnchor="middle" fontWeight="600">Iteración</text>
                      <text x="15" y="150" fontSize="14" fill="#0f172a" textAnchor="middle" fontWeight="600" transform="rotate(-90, 15, 150)">Score</text>
                    </svg>
                  </div>

                  {statistics.learning_history.history.length > 0 && (
                    <details className="adjustments-details">
                      <summary>📝 Ver detalles de ajustes por iteración</summary>
                      <div className="adjustments-timeline">
                        {statistics.learning_history.history.slice(1).map((entry, idx) => (
                          <div key={idx} className="adjustment-item">
                            <strong>Iteración {entry.iteration}</strong> (Score: {entry.feedback_score.toFixed(1)})
                            <ul>
                              {entry.adjustments.map((adj, adjIdx) => (
                                <li key={adjIdx}>{adj}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              </div>
            )}

            {statistics && statistics.simulation_learning && (
              <div className="stats-section">
                <h3>🤖 Resultados de Simulación con Aprendizaje</h3>
                <div className="metadata">
                  <span>Iteraciones: {statistics.simulation_learning.metadata.total_iterations}</span>
                  <span>Tasa: {statistics.simulation_learning.metadata.learning_rate}</span>
                </div>

                <div className="weight-chart">
                  <h4>📊 Comparación de Pesos Clave</h4>
                  <div className="chart-container">
                    <svg viewBox="0 0 800 350" className="line-chart">
                      {/* Grid */}
                      {[0, 0.1, 0.2, 0.3, 0.4, 0.5].map((val, i) => {
                        const y = 300 - (val * 500);
                        return (
                          <g key={i}>
                            <line x1="50" y1={y} x2="750" y2={y} stroke="#e1dacf" strokeWidth="1" strokeDasharray="4,4" />
                            <text x="30" y={y + 5} fontSize="12" fill="#5b6474">{val.toFixed(1)}</text>
                          </g>
                        );
                      })}

                      {/* Lines for key weights */}
                      {['event_type', 'price_range', 'cultural', 'dietary'].map((weightKey, wIdx) => {
                        const colors = ['#0f766e', '#f59e0b', '#ec4899', '#8b5cf6'];
                        const color = colors[wIdx];
                        const points = statistics.simulation_learning.history.map((entry, idx) => {
                          const x = 50 + (idx / Math.max(statistics.simulation_learning.history.length - 1, 1)) * 700;
                          const y = 300 - (entry.weights[weightKey] * 500);
                          return { x, y, value: entry.weights[weightKey] };
                        });

                        const pathData = points.map((p, i) =>
                          `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
                        ).join(' ');

                        return (
                          <g key={weightKey}>
                            <path d={pathData} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
                            {points.map((p, i) => (
                              <circle key={i} cx={p.x} cy={p.y} r="3" fill={color}>
                                <title>{weightKey}: {p.value.toFixed(3)}</title>
                              </circle>
                            ))}
                          </g>
                        );
                      })}

                      <text x="400" y="335" fontSize="14" fill="#0f172a" textAnchor="middle" fontWeight="600">Iteración</text>
                      <text x="15" y="175" fontSize="14" fill="#0f172a" textAnchor="middle" fontWeight="600" transform="rotate(-90, 15, 175)">Peso</text>
                    </svg>

                    <div className="chart-legend">
                      {['event_type', 'price_range', 'cultural', 'dietary'].map((key, idx) => {
                        const colors = ['#0f766e', '#f59e0b', '#ec4899', '#8b5cf6'];
                        const labels = ['Evento', 'Precio', 'Cultural', 'Dieta'];
                        return (
                          <div key={key} className="legend-item">
                            <span className="legend-dot" style={{ background: colors[idx] }}></span>
                            <span>{labels[idx]}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {statistics && statistics.simulation_results && (
              <div className="stats-section">
                <h3>📈 Resultados de Simulación General</h3>
                {statistics.simulation_results.summary && (
                  <div className="simulation-summary">
                    <div className="summary-grid">
                      <div className="summary-card">
                        <span className="summary-label">Total de solicitudes</span>
                        <span className="summary-value">{statistics.simulation_results.summary.total_requests}</span>
                      </div>
                      <div className="summary-card">
                        <span className="summary-label">Casos exitosos</span>
                        <span className="summary-value good-score">{statistics.simulation_results.summary.successful_cases}</span>
                      </div>
                      <div className="summary-card">
                        <span className="summary-label">Tasa de éxito</span>
                        <span className="summary-value">{(statistics.simulation_results.summary.success_rate * 100).toFixed(1)}%</span>
                      </div>
                      <div className="summary-card">
                        <span className="summary-label">Score promedio</span>
                        <span className="summary-value">{statistics.simulation_results.summary.average_score?.toFixed(2) || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                )}

                {statistics.simulation_results.iterations && (
                  <details className="simulation-details">
                    <summary>Ver todas las iteraciones ({statistics.simulation_results.iterations.length})</summary>
                    <div className="iterations-list">
                      {statistics.simulation_results.iterations.map((iter, idx) => (
                        <div key={idx} className="iteration-card">
                          <h5>Iteración {iter.iteration}</h5>
                          <p><strong>Evento:</strong> {iter.request?.event_type}</p>
                          <p><strong>Temporada:</strong> {iter.request?.season}</p>
                          <p><strong>Cultura:</strong> {iter.request?.cultural_preference || 'N/A'}</p>
                          {iter.score && <p><strong>Score:</strong> {iter.score.toFixed(2)}</p>}
                          {iter.success !== undefined && (
                            <p className={iter.success ? 'good-score' : 'low-score'}>
                              {iter.success ? '✅ Exitoso' : '❌ Fallido'}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            )}

            {statistics && statistics.current_case_base && !statistics.current_case_base.error && (
              <div className="stats-section">
                <h3>📦 Estado en tiempo real</h3>
                <div className="live-grid">
                  <div className="summary-card">
                    <span className="summary-label">Total casos</span>
                    <span className="summary-value">{statistics.current_case_base.total_cases}</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Embeddings</span>
                    <span className="summary-value">{statistics.current_case_base.embeddings_total}</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Éxito</span>
                    <span className="summary-value">{(statistics.current_case_base.retention_stats?.success_rate * 100 || 0).toFixed(1)}%</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Positivos</span>
                    <span className="summary-value good-score">{statistics.current_case_base.retention_stats?.positive_cases || 0}</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Negativos</span>
                    <span className="summary-value low-score">{statistics.current_case_base.retention_stats?.negative_cases || 0}</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Feedback medio</span>
                    <span className="summary-value">{(statistics.current_case_base.retention_stats?.avg_feedback || 0).toFixed(2)}</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Actualizado</span>
                    <span className="summary-value">{new Date(statistics.current_case_base.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                {statistics.current_case_base.retention_stats?.cases_by_event && (
                  <div className="weight-chart">
                    <h4>Casos por evento</h4>
                    <div className="bar-list">
                      {Object.entries(statistics.current_case_base.retention_stats.cases_by_event).map(([event, value]) => (
                        <div key={event} className="bar-row">
                          <span>{event}</span>
                          <div className="bar-track">
                            <div className="bar-fill" style={{ width: `${Math.min(100, value * 4)}%` }} />
                          </div>
                          <span className="bar-value">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {statistics.current_case_base.current_weights && (
                  <div className="weight-chart">
                    <h4>⚖️ Pesos actuales</h4>
                    <div className="chart-legend">
                      {Object.entries(statistics.current_case_base.current_weights).map(([key, value]) => (
                        <div key={key} className="legend-item">
                          <span className="legend-dot" style={{ background: '#0f766e' }}></span>
                          <span>{key}: {Number(value).toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {statistics && !statistics.learning_history && !statistics.simulation_learning && !statistics.simulation_results && !statistics.current_case_base && (
              <div className="no-data">
                <p>⚠️ No hay datos de estadísticas disponibles.</p>
                <p>Ejecuta algunas simulaciones primero para generar datos.</p>
              </div>
            )}
          </section>
        </div>
      ) : (
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
                <h3>🤖 Usuario Sintético - Resultado</h3>

                {syntheticResult.request && (
                  <div className="synthetic-request">
                    <h4>Solicitud Generada</h4>
                    <div className="request-details">
                      <span><strong>Evento:</strong> {syntheticResult.request.event_type}</span>
                      <span><strong>Temporada:</strong> {syntheticResult.request.season}</span>
                      <span><strong>Invitados:</strong> {syntheticResult.request.num_guests}</span>
                      <span><strong>Presupuesto:</strong> {syntheticResult.request.price_min}-{syntheticResult.request.price_max}€</span>
                      {syntheticResult.request.cultural_preference && (
                        <span><strong>Cultura:</strong> {syntheticResult.request.cultural_preference}</span>
                      )}
                      {syntheticResult.request.preferred_style && (
                        <span><strong>Estilo:</strong> {syntheticResult.request.preferred_style}</span>
                      )}
                      {syntheticResult.request.required_diets?.length > 0 && (
                        <span><strong>Dietas:</strong> {syntheticResult.request.required_diets.join(', ')}</span>
                      )}
                    </div>
                  </div>
                )}

                <div className="llm-evaluation-box">
                  <h4>Evaluación Automática del LLM</h4>
                  <div className="llm-score">
                    Puntuación: <span className={syntheticResult.llm_score >= 4 ? 'good-score' : syntheticResult.llm_score >= 2.5 ? 'medium-score' : 'low-score'}>
                      {syntheticResult.llm_score?.toFixed(1) || 'N/A'}/5.0
                    </span>
                  </div>
                  <div className="llm-evaluation-text">
                    {syntheticResult.llm_evaluation || 'Sin evaluación'}
                  </div>
                </div>

                <details className="synthetic-details">
                  <summary>📋 Ver detalles completos de la interacción</summary>
                  <pre>{JSON.stringify(syntheticResult, null, 2)}</pre>
                </details>

                <p className="info-note">
                  💡 El caso fue automáticamente procesado, evaluado y {syntheticResult.llm_score >= 3.5 ? '✅ guardado en la base de datos' : '❌ no guardado (score < 3.5)'}
                </p>
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
      )}
    </div>
  )
}

export default App
