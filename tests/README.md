# Formal Testing Suite

Suite de tests formales para el sistema CBR Chef Digital.

## Estructura

```
tests/
├── runner.py          # Script unificado: ejecuta tests + genera reportes
├── cases/             # Directorio con los 8 tests formales
│   ├── test_complete_cbr_cycle.py
│   ├── test_user_simulation.py
│   ├── test_adaptive_weights.py
│   ├── test_adaptive_learning.py
│   ├── test_semantic_cultural_adaptation.py
│   ├── test_semantic_retrieve.py
│   ├── test_semantic_retain.py
│   └── test_negative_cases.py
└── README.md          # Este archivo
```

## Uso

### Ejecutar toda la suite de tests + generar reportes

```bash
python tests/runner.py
```

Esto ejecutará:
1. **Todos los tests** en `tests/cases/`
2. **Generará reportes**:
   - `data/results/master_test_report.json` - reporte maestro JSON
   - `data/reports/FORMAL_REPORT.md` - reporte académico en markdown
   - `data/reports/test_summary.csv` - resumen CSV para análisis

### Solo ejecutar tests (sin generar reportes)

```bash
python tests/runner.py --no-report
```

## Tests Incluidos

## Tests Incluidos

### 1. Complete CBR Cycle (`test_complete_cbr_cycle.py`)
- **Objetivo**: Validar el ciclo completo RETRIEVE → ADAPT → REVISE → RETAIN
- **Métricas**: similarity, retention_rate, cases_learned

### 2. Multi-User Simulation (`test_user_simulation.py`)
- **Objetivo**: Simular múltiples usuarios con diferentes preferencias
- **Métricas**: feedback evolution, learning improvement
- **Plot**: `data/plots/feedback_evolution.png`

### 3. Adaptive Weight Learning (`test_adaptive_weights.py`)
- **Objetivo**: Comparar sistema estático vs adaptativo
- **Métricas**: similarity improvement, weight convergence
- **Plot**: `data/plots/weight_evolution.png`

### 4. Adaptive Learning Evaluation (`test_adaptive_learning.py`)
- **Objetivo**: Evaluación completa del aprendizaje adaptativo
- **Métricas**: static vs adaptive comparison
- **Plots**: generados por cbr.plot_learning_evolution()

### 5. Semantic Cultural Adaptation (`test_semantic_cultural_adaptation.py`)
- **Objetivo**: Validar adaptaciones culturales semánticas
- **Métricas**: cultural_match_rate, adaptation_accuracy

### 6. Semantic RETRIEVE (`test_semantic_retrieve.py`)
- **Objetivo**: Validar retrieval semántico por cultura
- **Métricas**: exact_match_rate, top_result_match_rate

### 7. Semantic RETAIN (`test_semantic_retain.py`)
- **Objetivo**: Validar almacenamiento de nuevos casos
- **Métricas**: retention_rate, cases_stored

### 8. Negative Cases Learning (`test_negative_cases.py`)
- **Objetivo**: Validar aprendizaje de casos negativos
- **Métricas**: negative_cases_stored, avoidance_rate

## Outputs

Todos los tests generan outputs en `data/`:

- **`data/results/`**: JSONs con resultados de cada test
- **`data/plots/`**: Gráficos de visualización (matplotlib)
- **`data/reports/`**: Reportes formateados (MD, CSV)

## Requisitos

- Python 3.10+
- Dependencias: ver `requirements.txt` en el directorio raíz
- matplotlib (para generación de plots)

## Notas

- Cada test puede ejecutarse individualmente: `python tests/cases/test_*.py`
- Los tests usan el sistema CBR real (no mocks)
- Tiempo de ejecución total: ~2-5 minutos
- `FORMAL_REPORT.md` - Formatted report for presentation
- `test_summary.csv` - Metrics summary (spreadsheet compatible)
- Text explanations and documentation

### Visualizations (`data/plots/`)
- Generated charts and plots (PNG format)

### Interactive (`data/htmls/`)
- HTML visualizations and reports

## Test Characteristics

- **Formal output**: No emojis, minimal console output
- **Structured results**: JSON format with clear metrics
- **Reproducible**: Deterministic where possible
- **Quantitative**: Focus on measurable metrics
- **Academic**: Suitable for research reports and presentations
