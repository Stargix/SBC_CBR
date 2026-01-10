# CBR/develop - Sistema de Catering CBR

Implementación modular del sistema CBR para catering con aprendizaje adaptativo y similitud semántica.

## 📁 Estructura

```
develop/
├── config/                   # Configuración y datos JSON
│   ├── knowledge_base.json   # Reglas de compatibilidad
│   ├── dishes.json           # 25+ platos
│   ├── beverages.json        # 17 bebidas
│   ├── initial_cases.json    # Casos iniciales
│   ├── umap_embeddings.json  # Embeddings UMAP precalculados
│   ├── umap_model.pkl        # Modelo UMAP entrenado
│   └── umap_feature_spec.pkl # Especificación de features
│
├── core/                     # Componentes fundamentales
│   ├── models.py             # Dataclasses y enums (Request, EventType, Season, etc.)
│   ├── knowledge.py          # Base de conocimiento y reglas
│   ├── case_base.py          # Gestión de casos con persistencia
│   ├── similarity.py         # Cálculo de similitudes (semántico + tradicional)
│   └── adaptive_weights.py   # Sistema de aprendizaje adaptativo de pesos
│
├── cycle/                    # Ciclo CBR 4R
│   ├── retrieve.py           # Fase 1: Recuperación de casos similares
│   ├── adapt.py              # Fase 2: Adaptación (precio, cultura, dietas)
│   ├── revise.py             # Fase 3: Revisión y validación
│   ├── retain.py             # Fase 4: Retención y aprendizaje
│   └── explanation.py        # Generación de explicaciones detalladas
│
├── main.py                   # Orquestador principal (ChefDigitalCBR)
├── example.py                # Ejemplo de uso
└── __init__.py               # Exportaciones del módulo
```

## 🚀 Uso

### Desde dentro de develop/

```bash
cd CBR/develop
python example.py
```

### Como módulo Python (desde la raíz)

```python
from develop.main import ChefDigitalCBR, CBRConfig
from develop.core.models import Request, EventType, Season, CulturalTradition

# Configurar sistema
config = CBRConfig(
    verbose=True, 
    max_proposals=3,
    enable_learning=True  # Activar aprendizaje adaptativo
)
cbr = ChefDigitalCBR(config)

# Crear solicitud
request = Request(
    event_type=EventType.WEDDING,
    num_guests=100,
    season=Season.SUMMER,
    price_min=40.0,
    price_max=60.0,
    wants_wine=True,
    cultural_preference=CulturalTradition.ITALIAN,
    required_diets=['vegan', 'gluten-free'],
    restricted_ingredients=['shrimp']
)

# Procesar solicitud
result = cbr.process_request(request)

# Ver resultados
print(f"Propuestas generadas: {len(result.proposed_menus)}")
print(result.explanations)
```

## 🎯 Características Principales

### Similitud Semántica
- Embeddings UMAP para cálculo de distancias culturales
- Sustitucióninteligente de ingredientes por cultura
- Adaptación cross-cultural automática

### Aprendizaje Adaptativo
- Ajuste automático de pesos de similitud según feedback
- Historial de aprendizaje persistente
- Métricas de mejora continua

### Ciclo CBR Completo
1. **RETRIEVE**: Recuperación de casos similares (semántico + tradicional)
2. **ADAPT**: Adaptación de precio, cultura, dietas e ingredientes
3. **REVISE**: Validación exhaustiva (dietas, presupuesto, ingredientes prohibidos)
4. **RETAIN**: Aprendizaje de casos positivos y negativos

### Sistema de Explicaciones
- Justificación detallada de cada decisión
- Trazabilidad completa del razonamiento
- Explicaciones adaptadas al usuario

## 📊 Componentes Clave

### AdaptiveWeightLearner
Sistema de aprendizaje que ajusta pesos de similitud:
- Dimensiones: precio, cultura, dietas, sabor
- Feedback multi-dimensional
- Persistencia de historial

### SemanticSimilarity
Cálculo de similitud cultural:
- UMAP para reducción dimensional
- Distancias euclidianas en espacio embedding
- Fallback a heurísticas si no hay embeddings

### CaseBase
Gestión de casos:
- Persistencia JSON
- Casos positivos y negativos
- Sistema de warnings

## 🔧 Configuración (CBRConfig)

```python
@dataclass
class CBRConfig:
    case_base_path: str = "cases.json"
    max_proposals: int = 3
    diversity_threshold: float = 0.3
    verbose: bool = False
    enable_learning: bool = True
    learning_rate: float = 0.1
```
    num_guests=100,
    price_max=80.0,
    season=Season.SPRING
)

# Procesar
result = cbr.process_request(request)
print(result.explanations)
```

## 📝 Configuración

Todos los datos están en archivos JSON en `config/`:

- **knowledge_base.json**: Compatibilidades, maridajes, estilos
- **dishes.json**: Catálogo de platos con atributos
- **beverages.json**: Catálogo de bebidas
- **initial_cases.json**: Casos de ejemplo

## 🔄 Ciclo CBR

1. **RETRIEVE** (`cycle/retrieve.py`): Busca casos similares
2. **ADAPT** (`cycle/adapt.py`): Adapta el caso al nuevo problema
3. **REVISE** (`cycle/revise.py`): Valida la solución
4. **RETAIN** (`cycle/retain.py`): Aprende de la experiencia

## ✨ Características

- ✅ 10 casos iniciales pre-cargados
- ✅ 25 platos y 17 bebidas
- ✅ 6 tipos de eventos
- ✅ 8 estilos culinarios
- ✅ Sin dependencias externas
