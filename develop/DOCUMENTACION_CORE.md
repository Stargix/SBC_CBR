# DOCUMENTACIÓN - CARPETA CORE

## RESUMEN EJECUTIVO

La carpeta `core/` contiene los componentes fundamentales del sistema CBR: modelos de datos, base de conocimiento, gestión de casos y cálculo de similitudes. Es la capa de abstracción que representa el dominio gastronómico.

---

## 📁 ESTRUCTURA

```
core/
├── __init__.py          # Módulo Python vacío
├── models.py            # Clases de datos (Dish, Menu, Case, Request)
├── knowledge.py         # Base de conocimiento gastronómico
├── case_base.py         # Gestión de la base de casos CBR
└── similarity.py        # Cálculo de similitudes entre casos
```

---

## 1. models.py (526 líneas)

**Propósito**: Define todas las estructuras de datos del sistema mediante dataclasses y enums.

### 1.1 Enums principales

```python
# Tipos de eventos
EventType: WEDDING, FAMILIAR, CONGRESS, CORPORATE, CHRISTENING, COMMUNION

# Temporadas
Season: SPRING, SUMMER, AUTUMN, WINTER, ALL

# Tipos de plato
DishType: STARTER, MAIN_COURSE, DESSERT

# Categorías gastronómicas
DishCategory: SOUP, CREAM, BROTH, SALAD, VEGETABLE, LEGUME, PASTA, 
              RICE, MEAT, POULTRY, FISH, SEAFOOD, EGG, TAPAS, 
              SNACK, FRUIT, PASTRY, ICE_CREAM

# Estilos culinarios
CulinaryStyle: CLASSIC, MODERN, FUSION, REGIONAL, SIBARITA, 
               GOURMET, CLASSICAL, SUAVE

# Tradiciones culturales
CulturalTradition: MEDITERRANEAN, CATALAN, BASQUE, GALICIAN, ITALIAN,
                   FRENCH, GREEK, MOROCCAN, TURKISH, LEBANESE, 
                   NORDIC, RUSSIAN, JAPANESE, MEXICAN, SPANISH

# Atributos físicos
Temperature: HOT, WARM, COLD
Complexity: LOW, MEDIUM, HIGH
Flavor: SWEET, SALTY, SOUR, BITTER, UMAMI, FATTY, SPICY
```

### 1.2 Clase Dish

Representa un plato gastronómico con todos sus atributos.

```python
@dataclass
class Dish:
    id: str                              # Identificador único
    name: str                            # Nombre del plato
    dish_type: DishType                  # starter/main_course/dessert
    price: float                         # Precio por persona
    category: DishCategory               # Tipo de plato
    styles: List[CulinaryStyle]          # Estilos asociados
    seasons: List[Season]                # Temporadas disponibles
    temperature: Temperature             # Temperatura de servicio
    complexity: Complexity               # Dificultad de elaboración
    calories: int                        # Calorías aproximadas
    max_guests: int                      # Capacidad máxima
    flavors: List[Flavor]                # Sabores principales
    diets: List[str]                     # Dietas compatibles
    ingredients: List[str]               # Ingredientes principales
    compatible_beverages: List[str]      # IDs de bebidas compatibles
    cultural_traditions: List[CulturalTradition]
    chef_style: Optional[str]            # Estilo de chef inspirador
    presentation_notes: str              # Notas de presentación
```

**Métodos útiles**:
- `is_available_in_season(season)`: Verifica disponibilidad temporal
- `meets_dietary_restrictions(diets)`: Valida restricciones dietéticas
- `has_restricted_ingredient(restricted)`: Detecta ingredientes prohibidos
- `to_dict()`: Serialización a diccionario

### 1.3 Clase Beverage

Representa una bebida o maridaje.

```python
@dataclass
class Beverage:
    id: str                              # Identificador único
    name: str                            # Nombre de la bebida
    alcoholic: bool                      # Contiene alcohol
    price: float                         # Precio por persona
    styles: List[str]                    # Tipos (wine, tea, soft-drink)
    subtype: str                         # Características (dry, fruity, etc.)
    compatible_flavors: List[Flavor]     # Sabores que marida bien
```

### 1.4 Clase Menu

Representa un menú completo (3 platos + bebida).

```python
@dataclass
class Menu:
    id: str                              # Identificador único
    starter: Dish                        # Entrante
    main_course: Dish                    # Plato principal
    dessert: Dish                        # Postre
    beverage: Beverage                   # Bebida/maridaje
    total_price: float                   # Precio total calculado
    total_calories: int                  # Calorías totales
    dominant_style: Optional[CulinaryStyle]  # Estilo dominante
    cultural_theme: Optional[CulturalTradition]  # Tema cultural
    explanation: List[str]               # Explicaciones del menú
    score: float                         # Puntuación de calidad
```

**Métodos importantes**:
- `calculate_totals()`: Calcula precio y calorías automáticamente
- `get_all_ingredients()`: Obtiene todos los ingredientes del menú
- `get_all_diets()`: Dietas que cumple todo el menú (intersección)
- `get_all_flavors()`: Todos los sabores presentes
- `to_dict()`: Serialización completa

### 1.5 Clase Request

Representa la solicitud del cliente.

```python
@dataclass
class Request:
    id: str                              # Identificador único
    event_type: EventType                # Tipo de evento
    num_guests: int                      # Número de comensales
    price_min: float                     # Presupuesto mínimo
    price_max: float                     # Presupuesto máximo
    season: Season                       # Temporada del evento
    
    # Preferencias opcionales
    preferred_style: Optional[CulinaryStyle]
    cultural_preference: Optional[CulturalTradition]
    required_diets: List[str]            # Dietas obligatorias
    restricted_ingredients: List[str]    # Ingredientes prohibidos
    wants_wine: bool                     # Preferencia de vino
    wine_per_dish: bool                  # Maridaje por plato
    
    # Restricciones adicionales
    avoid_categories: List[DishCategory]
    preferred_complexity: Optional[Complexity]
```

### 1.6 Clase Case

Representa un caso CBR (problema + solución + feedback).

```python
@dataclass
class Case:
    id: str                              # Identificador único
    request: Request                     # Problema (contexto)
    menu: Menu                           # Solución (menú propuesto)
    success: bool                        # Si fue exitoso
    feedback_score: float                # Puntuación 1-5
    feedback_comments: str               # Comentarios del cliente
    usage_count: int                     # Veces usado
    last_used: Optional[str]             # Última vez usado (ISO format)
    source: str                          # Origen: "initial" o "learned"
    created_at: str                      # Fecha de creación
    adaptation_notes: List[str]          # Historial de adaptaciones
```

**Métodos**:
- `increment_usage()`: Registra uso del caso
- `to_dict()`: Serialización para persistencia

### 1.7 Clase ProposedMenu

Resultado de la fase de adaptación y validación.

```python
@dataclass
class ProposedMenu:
    menu: Menu                           # Menú propuesto
    source_case: Case                    # Caso del que deriva
    similarity_score: float              # Similitud con la solicitud
    adaptations: List[str]               # Adaptaciones realizadas
    validation_result: ValidationResult  # Resultado de validación
    rank: int                            # Ranking (1=mejor)
```

---

## 2. knowledge.py (561 líneas)

**Propósito**: Carga y expone el conocimiento del dominio gastronómico desde `knowledge_base.json`.

### 2.1 Variables globales cargadas

```python
# Cargado desde knowledge_base.json al importar el módulo
_KB_CONFIG = json.load('config/knowledge_base.json')

# Diccionarios de conocimiento
FLAVOR_COMPATIBILITY: Dict[Flavor, List[Flavor]]
INCOMPATIBLE_CATEGORIES: List[Tuple[DishCategory, DishCategory]]
WINE_FLAVOR_COMPATIBILITY: Dict[str, List[Flavor]]
EVENT_STYLES: Dict[EventType, List[Tuple[CulinaryStyle, int]]]
EVENT_COMPLEXITY: Dict[EventType, List[Complexity]]
CALORIE_RANGES: Dict[Season, Tuple[int, int]]
APPROPRIATE_STARTER_TEMPS: Dict[Season, List[Temperature]]
```

### 2.2 Funciones principales

#### Compatibilidad de sabores
```python
are_flavors_compatible(flavor1, flavor2) -> bool
    # Verifica si dos sabores son compatibles
    # Ejemplo: SWEET + SALTY = True, SWEET + BITTER = False

get_compatible_flavors(flavor) -> List[Flavor]
    # Obtiene lista de sabores compatibles con uno dado
```

#### Categorías de platos
```python
are_categories_compatible(cat1, cat2) -> bool
    # Verifica si dos categorías pueden aparecer juntas
    # Ejemplo: MEAT + FISH = False (no mezclar proteínas)
```

#### Maridaje de vinos
```python
is_wine_compatible_with_flavors(wine_subtype, flavors, is_dessert) -> bool
    # Verifica si un vino marida bien con los sabores
    # Ejemplo: "dry" + [SALTY, FATTY] = True

get_wine_priority(wine_subtype, is_dessert) -> int
    # Prioridad de selección de vino (mayor = mejor)
    # Postres priorizan vinos dulces y espumosos
```

#### Estilos por evento
```python
get_preferred_styles_for_event(event_type) -> List[CulinaryStyle]
    # Estilos recomendados ordenados por preferencia
    # Ejemplo: WEDDING → [GOURMET, SIBARITA, CLASSIC]

is_style_appropriate_for_event(style, event_type) -> bool
    # Valida si un estilo es apropiado
```

#### Complejidad
```python
is_complexity_appropriate(complexity, event_type, budget) -> bool
    # Valida complejidad según evento y presupuesto
    # Regla especial: Bodas baratas evitan alta complejidad
```

#### Calorías y temperatura
```python
get_calorie_range(season) -> Tuple[int, int]
    # Rango apropiado de calorías según temporada
    # Verano: 550-950, Invierno: 850-1450

is_calorie_count_appropriate(calories, season) -> bool
    # Valida si las calorías están en rango

is_starter_temperature_appropriate(temp, season) -> bool
    # Valida temperatura del entrante para la temporada
    # Verano: COLD/WARM, Invierno: HOT
```

#### Postres y balance
```python
is_dessert_appropriate_after_fatty(main_flavors, dessert) -> bool
    # Valida si el postre es apropiado tras plato graso
    # Platos grasos → postres ligeros (frutas, sorbetes)
```

#### Proporciones de precio
```python
validate_price_proportions(starter, main, dessert, beverage) -> Tuple[bool, str]
    # Valida proporciones de precio en el menú
    # Principal debe ser 35-50% del total
    # Entrante y postre similares

classify_price_category(total_price) -> str
    # Clasifica: "economico", "medio", "premium"
```

### 2.3 Constantes adicionales

```python
STYLE_DESCRIPTIONS: Dict[CulinaryStyle, str]
    # Descripciones de cada estilo culinario

EVENT_STYLE_PREFERENCES: Dict[EventType, List[CulinaryStyle]]
    # Matriz de preferencias evento-estilo

CULTURAL_TRADITIONS: Dict[CulturalTradition, Dict]
    # Características de cada tradición cultural

CHEF_SIGNATURES: Dict[str, Dict]
    # Estilos de chefs famosos (Ferran Adrià, Arzak, etc.)
```

---

## 3. case_base.py (342 líneas)

**Propósito**: Gestiona la base de casos CBR - almacenamiento, indexación y persistencia.

### 3.1 Clase CaseBase

```python
class CaseBase:
    """Base de casos del sistema CBR"""
    
    # Datos
    cases: List[Case]                    # Todos los casos
    dishes: Dict[str, Dish]              # Catálogo de platos
    beverages: Dict[str, Beverage]       # Catálogo de bebidas
    
    # Índices para búsqueda eficiente
    index_by_event: Dict[EventType, List[Case]]
    index_by_price_range: Dict[str, List[Case]]  # low/medium/high/premium
    index_by_season: Dict[Season, List[Case]]
    index_by_style: Dict[CulinaryStyle, List[Case]]
```

### 3.2 Métodos de inicialización

```python
__init__(data_path: Optional[str] = None):
    # 1. Inicializa estructuras vacías
    # 2. Carga dishes.json
    # 3. Carga beverages.json
    # 4. Genera 10 casos iniciales desde initial_cases.json
    # 5. Indexa todos los casos
    # 6. Carga casos persistidos si existen

_load_dishes_from_json():
    # Lee config/dishes.json
    # Crea objetos Dish
    # Almacena en self.dishes[id]

_load_beverages_from_json():
    # Lee config/beverages.json
    # Crea objetos Beverage
    # Almacena en self.beverages[id]

_generate_initial_cases():
    # Lee config/initial_cases.json
    # Crea 10 objetos Case completos
    # Los añade a la base con add_case()
```

### 3.3 Métodos de gestión de casos

```python
add_case(case: Case):
    # Añade caso a la base
    # Actualiza todos los índices

_index_case(case: Case):
    # Indexa un caso en:
    # - Por evento
    # - Por rango de precio (low/medium/high/premium)
    # - Por temporada
    # - Por estilo culinario
```

### 3.4 Métodos de consulta

```python
get_cases_by_event(event_type) -> List[Case]:
    # Casos de un tipo de evento específico

get_cases_by_price_range(min_price, max_price) -> List[Case]:
    # Casos dentro de un rango de precios

get_cases_by_season(season) -> List[Case]:
    # Casos de una temporada (incluye ALL)

get_all_cases() -> List[Case]:
    # Todos los casos de la base

get_dish_by_id(dish_id) -> Optional[Dish]:
    # Busca un plato por ID

get_beverage_by_id(bev_id) -> Optional[Beverage]:
    # Busca una bebida por ID

get_dishes_by_type(dish_type) -> List[Dish]:
    # Todos los platos de un tipo (starter/main/dessert)

get_compatible_beverages(wants_wine: bool) -> List[Beverage]:
    # Bebidas según preferencia de alcohol
```

### 3.5 Persistencia

```python
save_to_file(filepath: str):
    # Guarda la base completa en JSON
    # Solo guarda casos (no platos/bebidas)

load_from_file(filepath: str):
    # Carga casos desde JSON
    # Reconstruye índices

get_statistics() -> Dict:
    # Estadísticas de la base:
    # - Total de casos
    # - Casos por evento
    # - Casos exitosos
    # - Tasa de éxito
    # - Feedback promedio
```

### 3.6 Estructura de índices

Los índices permiten búsqueda O(1) en lugar de O(n):

```python
# Ejemplo de índices poblados
index_by_event = {
    EventType.WEDDING: [case1, case2, case8],
    EventType.FAMILIAR: [case5],
    EventType.CONGRESS: [case6],
    # ...
}

index_by_price_range = {
    "low": [case5],              # <30€
    "medium": [case3, case4],    # 30-60€
    "high": [case6, case7],      # 60-100€
    "premium": [case1, case2]    # >100€
}
```

---

## 4. similarity.py (616 líneas)

**Propósito**: Calcula similitudes entre casos para la fase RETRIEVE del CBR.

### 4.1 Clase SimilarityWeights

Define pesos para cada dimensión de similitud.

```python
@dataclass
class SimilarityWeights:
    event_type: float = 0.20      # 20% - Tipo de evento
    season: float = 0.12          # 12% - Temporada
    price_range: float = 0.18     # 18% - Presupuesto
    style: float = 0.12           # 12% - Estilo culinario
    cultural: float = 0.08        # 8% - Tradición cultural
    dietary: float = 0.15         # 15% - Restricciones dietéticas
    guests: float = 0.05          # 5% - Número de comensales
    wine_preference: float = 0.05 # 5% - Preferencia de vino
    success_bonus: float = 0.05   # 5% - Bonus por éxito
    
    def normalize():
        # Normaliza para que sumen 1.0
```

### 4.2 Clase SimilarityCalculator

```python
class SimilarityCalculator:
    """Calculadora de similitud entre casos"""
    
    weights: SimilarityWeights
    
    def calculate_similarity(request: Request, case: Case) -> float:
        """
        Calcula similitud total entre 0 y 1
        
        Proceso:
        1. Calcula similitud parcial en cada dimensión
        2. Pondera según weights
        3. Suma total
        
        Retorna: float entre 0.0 (muy diferente) y 1.0 (idéntico)
        """
```

### 4.3 Funciones de similitud por dimensión

#### Evento
```python
_event_similarity(req_event, case_event) -> float:
    # Exacto: 1.0
    # Similar (Wedding-Communion): 0.6
    # Compatible (Congress-Corporate): 0.9
    # Diferente: 0.3
```

#### Temporada
```python
_season_similarity(req_season, case_season) -> float:
    # Exacta: 1.0
    # ALL: 0.9 (muy flexible)
    # Adyacente (Spring-Summer): 0.7
    # Opuesta (Summer-Winter): 0.3
```

#### Precio
```python
_price_similarity(req_min, req_max, case_price) -> float:
    # Dentro del rango: 1.0
    # Cerca del rango (±20%): 0.8-0.9
    # Fuera del rango: decrece con distancia
    # Muy lejos: 0.0
```

#### Estilo culinario
```python
_style_similarity(req_style, req_event, case_style) -> float:
    # Coincidencia exacta: 1.0
    # Sin preferencia: 0.8 (flexible)
    # Ambos apropiados para evento: 0.7
    # No apropiado: 0.3-0.5
```

#### Cultura
```python
_cultural_similarity(req_culture, case_culture) -> float:
    # Coincidencia exacta: 1.0
    # Sin preferencia: 0.8 (flexible)
    # Culturas relacionadas: 0.8
    # Diferentes: 0.4-0.6
```

#### Restricciones dietéticas
```python
_dietary_similarity(required_diets, case_menu) -> float:
    # Cumple todas: 1.0
    # Cumple algunas: proporcional
    # No cumple ninguna: 0.0 (eliminatorio)
```

#### Comensales
```python
_guests_similarity(req_guests, case_guests, menu) -> float:
    # Dentro de capacidad: 1.0
    # Diferencia pequeña: 0.8-0.9
    # Excede capacidad: penalización
```

#### Preferencia de vino
```python
_wine_similarity(req_wants_wine, case_wants_wine) -> float:
    # Coincide: 1.0
    # Diferente: 0.7 (no crítico)
```

#### Bonus por éxito
```python
success_bonus = case.feedback_score / 5.0
    # Score 5.0 → bonus 1.0
    # Score 2.5 → bonus 0.5
    # Score 0.0 → bonus 0.0
```

### 4.4 Funciones auxiliares

```python
calculate_menu_similarity(menu1: Menu, menu2: Menu) -> float:
    # Similitud entre dos menús
    # Compara platos y estilos

calculate_dish_similarity(dish1: Dish, dish2: Dish) -> float:
    # Similitud entre dos platos
    # Compara categoría, sabores, precio, estilo

calculate_detailed_similarity(request, case) -> Dict[str, float]:
    # Retorna similitud desglosada por dimensión
    # Útil para explicaciones
```

### 4.5 Ejemplo de cálculo

```python
request = Request(
    event_type=EventType.WEDDING,
    season=Season.SUMMER,
    price_max=100.0,
    preferred_style=CulinaryStyle.GOURMET
)

case = Case(...)  # Boda verano gourmet, precio 95€

similarities = {
    'event': 1.0,      # Exacto
    'season': 1.0,     # Exacto
    'price': 0.95,     # Dentro del rango
    'style': 1.0,      # Coincide
    'cultural': 0.8,   # Sin preferencia
    'dietary': 1.0,    # Sin restricciones
    'guests': 0.9,     # Similar capacidad
    'wine': 1.0,       # Coincide
    'success': 0.96    # Score 4.8/5
}

total = (0.20*1.0 + 0.12*1.0 + 0.18*0.95 + 0.12*1.0 + 
         0.08*0.8 + 0.15*1.0 + 0.05*0.9 + 0.05*1.0 + 0.05*0.96)
      = 0.96  # 96% de similitud
```

---

## 5. __init__.py

**Propósito**: Define exportaciones del módulo `core`.

```python
from .models import (
    Dish, Beverage, Menu, Case, Request, ProposedMenu,
    EventType, Season, CulinaryStyle, DishType, ...
)

from .knowledge import (
    FLAVOR_COMPATIBILITY, INCOMPATIBLE_CATEGORIES,
    are_flavors_compatible, get_preferred_styles_for_event, ...
)

from .case_base import CaseBase

from .similarity import (
    SimilarityCalculator, SimilarityWeights,
    calculate_menu_similarity, calculate_dish_similarity
)

__all__ = [...]  # Lista completa de exportaciones
```

Permite hacer:
```python
from develop.core import Dish, CaseBase, SimilarityCalculator
```

---

## FLUJO DE DATOS ENTRE MÓDULOS CORE

```
┌─────────────────────────────────────────────────────────────┐
│ INICIALIZACIÓN                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────┐
    │ knowledge.py se carga al importar              │
    │ - Lee knowledge_base.json                     │
    │ - Crea diccionarios globales                  │
    └───────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────┐
    │ CaseBase.__init__()                           │
    │ - Crea objetos Dish desde dishes.json        │
    │ - Crea objetos Beverage desde beverages.json │
    │ - Genera 10 Cases desde initial_cases.json   │
    │ - Indexa todo                                 │
    └───────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────┐
    │ SimilarityCalculator inicializado             │
    │ - Con pesos por defecto                       │
    └───────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ USO DURANTE EL CICLO CBR                                     │
└─────────────────────────────────────────────────────────────┘

RETRIEVE usa:
├── CaseBase.get_cases_by_event()
├── CaseBase.get_cases_by_price_range()
├── SimilarityCalculator.calculate_similarity()
└── knowledge.get_preferred_styles_for_event()

ADAPT usa:
├── CaseBase.get_dishes_by_type()
├── CaseBase.get_compatible_beverages()
├── similarity.calculate_dish_similarity()
├── knowledge.are_flavors_compatible()
└── knowledge.is_wine_compatible_with_flavors()

REVISE usa:
├── knowledge.are_flavors_compatible()
├── knowledge.are_categories_compatible()
├── knowledge.is_starter_temperature_appropriate()
├── knowledge.is_calorie_count_appropriate()
├── knowledge.validate_price_proportions()
└── knowledge.is_dessert_appropriate_after_fatty()

RETAIN usa:
├── CaseBase.add_case()
├── CaseBase.save_to_file()
├── SimilarityCalculator.calculate_similarity()
└── similarity.calculate_menu_similarity()
```

---

## RESUMEN POR ARCHIVO

| Archivo | Líneas | Propósito | Componentes clave |
|---------|--------|-----------|-------------------|
| **models.py** | 526 | Definir estructuras de datos | 8 enums, 7 dataclasses |
| **knowledge.py** | 561 | Base de conocimiento gastronómico | 15+ funciones de validación |
| **case_base.py** | 342 | Gestión de base de casos | Indexación, persistencia, estadísticas |
| **similarity.py** | 616 | Cálculo de similitudes | 9 dimensiones de similitud |
| **__init__.py** | ~50 | Exportaciones del módulo | Imports y __all__ |

**Total: ~2095 líneas de código**

---

## CONCLUSIÓN

La carpeta `core/` es la **fundación del sistema CBR**:

✅ **models.py**: Lenguaje común del dominio  
✅ **knowledge.py**: Reglas de negocio gastronómicas  
✅ **case_base.py**: Motor de almacenamiento y recuperación  
✅ **similarity.py**: Inteligencia para encontrar casos relevantes  

Estos módulos son **agnósticos al ciclo CBR** - pueden usarse independientemente para consultas, validaciones o análisis del dominio gastronómico.
