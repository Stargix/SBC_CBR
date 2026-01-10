# Chef Digital CBR System

Sistema de Razonamiento Basado en Casos (CBR) para planificación de menús con aprendizaje adaptativo y similitud semántica.

## Instalación

```bash
# Clonar repositorio
git clone <repository-url>
cd CBR

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Estructura del Proyecto

```
CBR/
├── run_tests.py              # Script principal: ejecuta tests + genera reportes + HTMLs
├── run_chef_cbr.py           # Interfaz interactiva CLI del sistema
├── run_simulation.py         # Simulación CBR con LLM
├── run_interface.py          # Inicia API + Frontend en paralelo
├── requirements.txt          # Dependencias del proyecto
│
├── develop/                  # Código fuente del sistema CBR
│   ├── main.py              # Punto de entrada principal
│   ├── core/                # Núcleo del sistema (case base, similarity, adaptive weights)
│   ├── cycle/               # Fases del ciclo CBR (retrieve, adapt, revise, retain)
│   └── config/              # Configuraciones y casos iniciales (dishes, beverages, knowledge)
│
├── tests/                    # Suite de tests formales
│   ├── test_executor.py     # Ejecutor de tests
│   ├── report_generator.py  # Generador de reportes MD/CSV
│   ├── html_generator.py    # Generador de HTMLs interactivos con plots Plotly
│   ├── generate_plots.py    # Generador de gráficos PNG adicionales
│   └── cases/               # 8 tests formales del sistema
│
├── data/                     # Outputs de tests y reportes
│   ├── results/             # JSONs con resultados detallados de tests
│   ├── reports/             # Reportes formales (FORMAL_REPORT.md, test_summary.csv)
│   ├── plots/               # 8 gráficos PNG (matplotlib) de visualización
│   └── htmls/               # 9 reportes HTML interactivos (8 tests + index)
│
├── demos/                    # Demostraciones del sistema (12 demos)
├── simulation/               # Simulación multi-usuario con LLM (opcional)
├── interface/                # Sistema web (backend + frontend)
│   ├── api/                 # API REST FastAPI (backend)
│   └── web/                 # Interfaz web React (frontend)
└── develop/                  # Módulo CBR principal (core del sistema)
```

```bash
python run_tests.py
```

Esto ejecuta los 8 tests formales, genera reportes en MD/CSV, 9 HTMLs interactivos y 5 gráficos PNG adicionales.

**Opciones:**
- `--no-report`: Solo ejecutar tests (sin reportes MD/CSV/plots)
- `--no-html`: Tests + reportes (sin HTMLs ni plots PNG)
- `--quiet`: Modo silencioso

**Outputs generados:**
- `data/results/*.json` - Resultados detallados por test
- `data/reports/FORMAL_REPORT.md` - Reporte académico completo
- `data/reports/test_summary.csv` - Resumen en CSV
- `data/htmls/index.html` - Índice de navegación
- `data/htmls/report_*.html` - 8 reportes HTML interactivos con plots Plotly
- `data/plots/*.png` - 5 gráficos PNG adicionales (matplotlib)

### 2. Usar el Sistema CBR (Interfaz Interactiva)

```bash
python run_chef_cbr.py
```

Interfaz interactiva de línea de comandos para planificar menús personalizados:

**Campos de la solicitud:**
- Tipo de evento (boda, congreso, familiar, etc.)
- Número de invitados
- Presupuesto (mín/máx por persona)
- Estación del año
- Preferencia de vino
- **Estilo culinario** (clásico, moderno, fusión, regional, sibarita, gourmet)
- **Preferencia cultural** (italiana, española, francesa, japonesa, mexicana, etc.)
- **Restricciones dietéticas** (vegan, gluten-free, keto, pescatarian, etc.)
- **Ingredientes a evitar** (mariscos, frutos secos, etc.)

### 3. Ejecutar Simulación con LLM

```bash
python run_simulation.py
```

Ejecuta simulaciones CBR con generación automática de solicitudes vía Groq LLM.

**Configuración rápida** (editar variables en el script):
```python
NUM_ITERACIONES = 10           # Número de solicitudes a simular
APRENDIZAJE_ACTIVO = True      # ¿Activar aprendizaje adaptativo?
VERBOSE = True                 # ¿Mostrar detalles durante ejecución?
```

**Requisitos:**
- API key de Groq: `export GROQ_API_KEY='tu_api_key'`
- O crear archivo `simulation/.env` con `GROQ_API_KEY=tu_api_key`

**Output:**
- `data/llm_simulation_results.json` - Resultados detallados de la simulación

### 4. Generar Plots Adicionales (Opcional)

```bash
python tests/generate_plots.py
```

Genera 5 gráficos PNG adicionales en `data/plots/`:
- `cultural_retrieval_quality.png` - Calidad de recuperación por cultura
- `cbr_cycle_performance.png` - Rendimiento del ciclo 4R
- `adaptation_intensity.png` - Intensidad de adaptaciones culturales
- `negative_learning.png` - Aprendizaje de casos negativos
- `retention_strategies.png` - Estrategias de retención

**Nota:** Los plots se generan automáticamente cuando ejecutas `python run_tests.py`

### 5. Web Interface (API + Frontend Juntos)

**Opción rápida (inicia ambos servicios en paralelo):**
```bash
python run_interface.py
```

Inicia automáticamente:
- 🔌 Backend FastAPI en `http://localhost:8000`
- 🌐 Frontend Vite en `http://localhost:5173`

**O iniciar por separado:**

Backend:
```bash
cd interface/api
source ../../.venv/bin/activate
python server.py
```

Frontend:
```bash
cd interface/web
npm install
npm run dev
```

## Tests Incluidos

1. **Adaptive Weights**: Comparación estático vs adaptativo con evolución de pesos
2. **Adaptive Learning**: Evaluación completa del aprendizaje (precisión, satisfacción, tiempo)
3. **User Simulation**: Simulación multi-usuario con feedback y retención
4. **Complete CBR Cycle**: Validación del ciclo completo 4R (RETRIEVE→ADAPT→REVISE→RETAIN)
5. **Semantic Retrieve**: Recuperación semántica con preferencias culturales
6. **Semantic Retain**: Estrategias de almacenamiento de casos
7. **Semantic Cultural Adaptation**: Adaptaciones cross-culturales
8. **Negative Cases**: Aprendizaje de casos negativos y sistema de warnings

## Outputs del Sistema

### JSONs de Resultados (`data/results/`)
- `test_adaptive_weights.json` - Datos de evolución de pesos
- `test_adaptive_learning.json` - Métricas de aprendizaje
- `test_user_simulation.json` - Datos de simulación multi-usuario
- `test_complete_cbr_cycle.json` - Resultados del ciclo completo
- `test_semantic_retrieve.json` - Datos de recuperación cultural
- `test_semantic_retain.json` - Estrategias de retención
- `test_semantic_cultural_adaptation.json` - Adaptaciones culturales
- `test_negative_cases.json` - Aprendizaje de negativos

### Plots PNG (`data/plots/` - 8 gráficos)
- `feedback_evolution.png` - Evolución temporal del feedback
- `feedback_correlation.png` - Correlación entre métricas
- `weight_evolution.png` - Evolución de pesos adaptativos
- `cultural_retrieval_quality.png` - Calidad por cultura
- `cbr_cycle_performance.png` - Rendimiento 4R
- `adaptation_intensity.png` - Intensidad de adaptaciones
- `negative_learning.png` - Evolución de casos negativos
- `retention_strategies.png` - Distribución de estrategias

### Reportes HTML (`data/htmls/` - 9 archivos)
- `index.html` - Índice de navegación categorizado
- `report_adaptive_weights.html` - Plots interactivos Plotly (similarity comparison, improvements)
- `report_adaptive_learning.html` - KPIs y gráficos embebidos base64
- `report_user_simulation.html` - 3 plots Plotly (feedback evolution, case growth, retention)
- `report_complete_cbr_cycle.html` - 2 plots Plotly (cycle performance, quality metrics)
- `report_semantic_retrieve.html` - 2 plots Plotly (similarity by culture, cultural matches)
- `report_semantic_retain.html` - 2 plots Plotly (action distribution, case growth)
- `report_semantic_cultural_adaptation.html` - 2 plots Plotly (retrieval quality, adaptation intensity)
- `report_negative_cases.html` - 2 plots Plotly (case evolution, feedback distribution)

Todos los HTMLs usan:
- **Plotly.js** para plots interactivos
- **Base64 images** para gráficos embebidos (auto-contenidos)
- **Diseño responsivo** con la estética de la web
- **Colores consistentes**: #0f766e (teal), #e07a5f (coral), #059669 (green), etc.

## Demostraciones

El directorio `demos/` contiene 12 demostraciones del sistema:
- Adaptación cultural
- Filtrado crítico de dietas
- Sustitución de ingredientes
- Ciclo CBR completo
- Simulación de usuarios
- Y más...

Ejecutar:
```bash
python demos/demo_<nombre>.py
```

## Simulación con LLM (Opcional)

Si tienes una API key de Groq:

```bash
# Configurar API key
export GROQ_API_KEY="tu_api_key"

# Ejecutar simulación
cd simulation
python groq_simulator.py
```

## Características Principales

✅ **Similitud Semántica**: Embeddings + UMAP para cálculo de similitud cultural  
✅ **Aprendizaje Adaptativo**: Ajuste automático de pesos según feedback  
✅ **Adaptación Cultural**: Sustitución inteligente de ingredientes por cultura  
✅ **Casos Negativos**: Sistema de warnings para evitar repetir errores  
✅ **Explicaciones Detalladas**: Justificación de cada decisión del sistema  
✅ **Reportes Visuales**: HTMLs interactivos con Plotly.js  
✅ **Tests Formales**: 8 tests exhaustivos con métricas cuantitativas  

## Licencia

MIT License

## Requisitos

- Python 3.10+
- Ver `requirements.txt` para dependencias
- Groq API key (opcional, solo para simulación LLM)

## Documentación

- **`tests/README.md`**: Detalle de cada test formal
- **`data/README.md`**: Estructura de datos generados
- **`develop/README.md`**: Arquitectura del sistema CBR
- **`docs/`**: Documentación técnica completa

## Licencia

Proyecto académico - Universidad SBC
