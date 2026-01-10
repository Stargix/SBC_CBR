# Chef Digital CBR System

Sistema de Razonamiento Basado en Casos (CBR) para planificación de menús con aprendizaje adaptativo.

## Estructura del Proyecto

```
CBR/
├── run_tests.py              # Script principal: ejecuta tests + genera reportes
├── run_chef_cbr.py           # Interfaz de línea de comandos del sistema
│
├── develop/                  # Código fuente del sistema CBR
│   ├── main.py              # Punto de entrada principal
│   ├── core/                # Núcleo del sistema (case base, similarity, etc.)
│   ├── cycle/               # Fases del ciclo CBR (retrieve, adapt, revise, retain)
│   └── config/              # Configuraciones y casos iniciales
│
├── tests/                    # Suite de tests formales
│   ├── test_executor.py     # Ejecutor de tests
│   ├── report_generator.py  # Generador de reportes MD/CSV
│   ├── html_generator.py    # Generador de HTML interactivo
│   └── cases/               # 8 tests formales
│
├── data/                     # Outputs de tests y reportes
│   ├── results/             # JSONs con resultados de tests
│   ├── reports/             # Reportes formales (MD, CSV)
│   ├── plots/               # Gráficos de visualización
│   └── htmls/               # Reportes HTML interactivos
│
├── demos/                    # Demostraciones del sistema
├── simulation/               # Simulación con Groq LLM (opcional)
├── web_api/                  # API REST (backend)
└── web/                      # Interfaz web (frontend)
```

## Uso Rápido

### 1. Ejecutar Tests Formales

```bash
python run_tests.py
```

Esto ejecuta los 8 tests formales, genera reportes en MD/CSV y un HTML interactivo.

**Opciones:**
- `--no-report`: Solo ejecutar tests (sin reportes)
- `--no-html`: Tests + reportes (sin HTML)
- `--quiet`: Modo silencioso

### 2. Usar el Sistema CBR

```bash
python run_chef_cbr.py
```

Interfaz interactiva de línea de comandos para:
- Planificar menús personalizados
- Adaptar recetas a restricciones dietéticas
- Aprender de feedback del usuario

### 3. Web Interface

**Backend:**
```bash
cd web_api
python server.py
```

**Frontend:**
```bash
cd web
python -m http.server 8080
```

Acceder a `http://localhost:8080`

## Tests Incluidos

1. **Complete CBR Cycle**: Validación del ciclo completo RETRIEVE→ADAPT→REVISE→RETAIN
2. **Multi-User Simulation**: Simulación de múltiples usuarios con aprendizaje
3. **Adaptive Weight Learning**: Comparación estático vs adaptativo
4. **Adaptive Learning Evaluation**: Evaluación completa del aprendizaje
5. **Semantic Cultural Adaptation**: Adaptaciones culturales semánticas
6. **Semantic RETRIEVE**: Retrieval semántico por cultura
7. **Semantic RETAIN**: Almacenamiento de nuevos casos
8. **Negative Cases Learning**: Aprendizaje de casos negativos

## Outputs

Todos los tests generan:
- **`data/results/`**: JSONs con resultados detallados
- **`data/plots/`**: Gráficos matplotlib (weight evolution, feedback trends)
- **`data/reports/`**: 
  - `FORMAL_REPORT.md` - Reporte académico
  - `test_summary.csv` - Resumen CSV
- **`data/htmls/`**: 
  - `test_results.html` - Dashboard consolidado
  - `report_test_*.html` - Reporte individual por cada test (7 HTMLs)

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
