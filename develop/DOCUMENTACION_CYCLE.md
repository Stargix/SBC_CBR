# DOCUMENTACIÓN - CARPETA CYCLE

## RESUMEN EJECUTIVO

La carpeta `cycle/` implementa las 4 fases del ciclo CBR (Case-Based Reasoning) más el módulo de explicaciones. Cada archivo es responsable de una fase específica del proceso de razonamiento basado en casos.

---

## 📁 ESTRUCTURA

```
cycle/
├── __init__.py          # Módulo Python vacío
├── retrieve.py          # FASE 1: Recuperación de casos similares
├── adapt.py             # FASE 2: Adaptación de casos al nuevo contexto
├── revise.py            # FASE 3: Validación de soluciones propuestas
├── retain.py            # FASE 4: Aprendizaje y retención de casos
└── explanation.py       # Generación de explicaciones para el usuario
```

---

## 1. retrieve.py (312 líneas)

**Propósito**: Implementa la fase RETRIEVE - recuperar casos similares de la base de conocimiento.

### 1.1 Clases principales

#### RetrievalResult
```python
@dataclass
class RetrievalResult:
    """Resultado de recuperación de un caso"""
    case: Case                           # Caso recuperado
    similarity: float                    # Similitud con la solicitud (0-1)
    similarity_details: Dict[str, float] # Similitud desglosada
    rank: int                            # Posición en ranking (1=mejor)
    
    def get_explanation() -> str:
        # Genera explicación de por qué se recuperó
        # Ejemplo: "Tipo de evento muy similar; Precio dentro del rango"
```

#### CaseRetriever
```python
class CaseRetriever:
    """Recuperador de casos del sistema CBR"""
    
    case_base: CaseBase                  # Base de casos a consultar
    similarity_calc: SimilarityCalculator # Calculadora de similitudes
    min_similarity_threshold: float = 0.3 # Mínima similitud (30%)
    max_candidates: int = 50             # Máximo de candidatos
```

### 1.2 Métodos principales

```python
retrieve(request: Request, k: int = 5) -> List[RetrievalResult]:
    """
    Recupera los k casos más similares
    
    Proceso en 3 fases:
    1. PRE-FILTRADO: Usar índices para candidatos iniciales
       - Por tipo de evento
       - Por rango de precio (±20%)
       - Por temporada
    
    2. CÁLCULO DETALLADO: Similitud completa para cada candidato
       - Usar SimilarityCalculator
       - Filtrar por min_similarity_threshold (30%)
    
    3. RANKING: Ordenar por similitud descendente
       - Seleccionar top-k
       - Asignar ranks (1, 2, 3...)
    
    Returns: Lista ordenada de RetrievalResult
    """

_prefilter_candidates(request: Request) -> List[Case]:
    """
    Optimización para bases grandes
    
    Estrategia:
    1. Casos del mismo evento
    2. Casos en rango de precio (con margen 20%)
    3. Casos de misma temporada
    
    Returns: Candidatos pre-filtrados (sin duplicados)
    """

retrieve_with_explanations(request, k) -> Tuple[List[RetrievalResult], str]:
    """
    Recupera casos + genera explicación textual
    
    Returns: (resultados, explicación legible)
    Ejemplo explicación:
    "Se buscaron casos similares para un evento wedding en temporada summer
     con presupuesto 80-150€. Se encontraron 3 casos relevantes:
     1. Caso 'case-init-1' (similitud: 0.96)
        - Tipo de evento muy similar
        - Precio dentro del rango
        - Temporada coincidente"
    """

retrieve_diverse(request, k, diversity_weight=0.3) -> List[RetrievalResult]:
    """
    Recupera casos DIVERSOS (no solo similares)
    
    Utiliza Maximal Marginal Relevance (MMR):
    - Balance entre similitud y diversidad
    - Útil para ofrecer variedad al usuario
    
    Algoritmo:
    1. Recuperar k*3 candidatos
    2. Seleccionar el más similar
    3. Para resto: maximizar MMR score
       MMR = (1-λ)·similitud - λ·max_sim_con_seleccionados
    4. Repetir hasta tener k casos
    
    diversity_weight: 0=solo similitud, 1=solo diversidad
    """

get_retrieval_statistics(request) -> Dict[str, Any]:
    """
    Estadísticas para diagnóstico
    
    Returns:
    - Total de casos en base
    - Similitud promedio
    - Similitud máxima/mínima
    - Distribución de similitudes
    """
```

### 1.3 Ejemplo de uso

```python
retriever = CaseRetriever(case_base)

request = Request(
    event_type=EventType.WEDDING,
    season=Season.SUMMER,
    price_max=100.0
)

# Recuperar top-3 casos más similares
results = retriever.retrieve(request, k=3)

for result in results:
    print(f"Caso {result.case.id}: {result.similarity:.1%}")
    print(f"  {result.get_explanation()}")
```

**Salida típica**:
```
Caso case-init-1: 96%
  Tipo de evento muy similar; Precio dentro del rango; Temporada coincidente
Caso case-init-7: 85%
  Tipo de evento muy similar; Precio cercano al rango
Caso case-init-3: 78%
  Tipo de evento muy similar
```

---

## 2. adapt.py (781 líneas)

**Propósito**: Implementa la fase REUSE/ADAPT - adaptar casos recuperados al nuevo contexto.

### 2.1 Clases principales

#### AdaptationResult
```python
@dataclass
class AdaptationResult:
    """Resultado de adaptación de un caso"""
    original_case: Case                  # Caso original
    adapted_menu: Menu                   # Menú adaptado
    adaptations_made: List[str]          # Descripción de cambios
    adaptation_score: float              # Qué tan bien se adaptó (0-1)
    price_category: str                  # "economico", "medio", "premium"
    
    def get_adaptation_explanation() -> str:
        # "Adaptaciones: Sustituido cordero por risotto (vegetariano)"
```

#### CaseAdapter
```python
class CaseAdapter:
    """Adaptador de casos del sistema CBR"""
    
    case_base: CaseBase                  # Para buscar alternativas
```

### 2.2 Método principal

```python
adapt(retrieval_results: List[RetrievalResult], 
      request: Request,
      num_proposals: int = 3) -> List[AdaptationResult]:
    """
    Adapta casos recuperados al contexto actual
    
    Proceso:
    1. Para cada caso recuperado:
       - Intentar adaptar al nuevo contexto
       - Si tiene éxito, añadir a propuestas
    
    2. Si no hay suficientes propuestas:
       - Generar menús nuevos desde cero
    
    3. Clasificar por categoría de precio
    
    4. Ordenar por adaptation_score
    
    Returns: Top-N propuestas adaptadas
    """
```

### 2.3 Proceso de adaptación

```python
_adapt_case(case: Case, request: Request) -> Optional[AdaptationResult]:
    """
    Adapta un caso específico
    
    PASO 1: Restricciones dietéticas
    - Verificar cada plato cumple dietas requeridas
    - Si no cumple: buscar alternativa con _find_diet_alternative()
    - Si no hay alternativa: FALLO (return None)
    
    PASO 2: Ingredientes restringidos
    - Verificar si hay ingredientes prohibidos
    - Buscar alternativas sin esos ingredientes
    - Si no hay: FALLO
    
    PASO 3: Ajuste de precio
    - Si fuera del rango: buscar alternativas más caras/baratas
    - Mantener balance (principal > entrante/postre)
    
    PASO 4: Adaptación temporal
    - Verificar temperatura del entrante para la temporada
    - Verano: priorizar entrantes fríos
    - Invierno: priorizar entrantes calientes
    
    PASO 5: Adaptación de bebida
    - Si wants_wine=False y caso tiene vino: cambiar a refresco
    - Verificar maridaje con nuevos platos (si hubo cambios)
    
    PASO 6: Adaptación de estilo
    - Si preferred_style diferente: intentar ajustar platos
    - Mantener coherencia del menú
    
    Returns: AdaptationResult o None si no es posible adaptar
    """
```

### 2.4 Funciones auxiliares de búsqueda

```python
_find_diet_alternative(original: Dish, missing_diets, all_required) -> Optional[Dish]:
    """
    Busca plato alternativo que cumpla dietas
    
    Proceso:
    1. Obtener todos los platos del mismo tipo (starter/main/dessert)
    2. Filtrar por dietas requeridas
    3. Calcular similitud con original
    4. Retornar el más similar
    
    Ejemplo:
    Original: Beef Wellington (carne)
    Requerido: vegetariano
    → Busca en main_course vegetarianos
    → Encuentra: Risotto Funghi (más similar por sabores umami)
    """

_find_ingredient_alternative(original: Dish, restricted) -> Optional[Dish]:
    """Similar pero filtrando ingredientes prohibidos"""

_find_price_alternative(original: Dish, target_price, tolerance) -> Optional[Dish]:
    """Busca alternativa en rango de precio específico"""

_find_season_alternative(original: Dish, season) -> Optional[Dish]:
    """Busca alternativa disponible en temporada"""

_find_style_alternative(original: Dish, style) -> Optional[Dish]:
    """Busca alternativa del estilo culinario deseado"""
```

### 2.5 Adaptación de bebidas

```python
_adapt_beverage(menu: Menu, wants_wine: bool, wine_per_dish: bool) -> List[str]:
    """
    Adapta la bebida del menú
    
    Si wants_wine == False:
    - Cambiar a agua, refresco o infusión
    - Precio similar
    
    Si wants_wine == True:
    - Verificar maridaje con platos
    - Priorizar vinos según:
      * Sabores del plato principal
      * Postre → vinos dulces o espumosos
      * Main → vinos con cuerpo o secos
    
    Si wine_per_dish == True:
    - Seleccionar múltiples vinos (uno por plato)
    - Calcular precio total
    """
```

### 2.6 Cálculo de adaptation_score

```python
_calculate_adaptation_score(original_menu, adapted_menu, request) -> float:
    """
    Evalúa qué tan bien se adaptó el menú (0-1)
    
    Factores:
    - Número de cambios (menos cambios = mejor)
    - Diferencia de precio con el original
    - Cumplimiento de restricciones
    - Mantenimiento de estilo
    - Balance del menú
    
    Score alto: Pocos cambios necesarios
    Score bajo: Muchas modificaciones
    """
```

### 2.7 Generación de menús nuevos

```python
_generate_new_menu(request: Request) -> Optional[AdaptationResult]:
    """
    Genera menú completamente nuevo (sin caso base)
    
    Usado cuando:
    - No hay suficientes casos adaptables
    - Solicitud muy específica sin casos similares
    
    Proceso:
    1. Seleccionar estilo apropiado para el evento
    2. Filtrar platos por:
       - Temporada disponible
       - Restricciones dietéticas
       - Ingredientes prohibidos
       - Presupuesto
    3. Buscar combinación válida:
       - Compatibilidad de sabores
       - Categorías no incompatibles
       - Balance de precios
       - Calorías apropiadas
    4. Seleccionar bebida compatible
    5. Crear menú completo
    
    Nota: Es más arriesgado que adaptar un caso exitoso
    """
```

---

## 3. revise.py (629 líneas)

**Propósito**: Implementa la fase REVISE - validar y revisar soluciones propuestas.

### 3.1 Clases y enums

```python
class ValidationStatus(Enum):
    VALID = "valid"                      # Menú válido
    VALID_WITH_WARNINGS = "valid_with_warnings"  # Válido con advertencias
    INVALID = "invalid"                  # Menú rechazado

@dataclass
class ValidationIssue:
    """Problema encontrado en validación"""
    severity: str                        # "error", "warning", "info"
    category: str                        # "price", "flavors", "diet", etc.
    message: str                         # Descripción del problema
    suggestion: Optional[str]            # Sugerencia de solución

@dataclass
class ValidationResult:
    """Resultado de validación de un menú"""
    menu: Menu
    status: ValidationStatus
    issues: List[ValidationIssue]
    score: float                         # Puntuación 0-100
    explanations: List[str]
    
    def is_valid() -> bool:
        # True si VALID o VALID_WITH_WARNINGS
    
    def get_rejection_reason() -> str:
        # Primera razón de error
```

### 3.2 Clase MenuReviser

```python
class MenuReviser:
    """Revisor de menús del sistema CBR"""
    
    strict_mode: bool = False            # Si True, warnings también invalidan
    max_warnings: int = 3                # Máximo de warnings antes de invalidar
```

### 3.3 Método principal

```python
revise(adaptation_results: List[AdaptationResult],
       request: Request) -> List[ValidationResult]:
    """
    Revisa y valida propuestas de adaptación
    
    Proceso:
    1. Para cada propuesta adaptada:
       - Validar menú completo
       - Agregar información de adaptaciones
    
    2. Ordenar por puntuación
    
    3. Filtrar solo válidos
    
    Returns: Lista de menús válidos ordenados por calidad
    """
```

### 3.4 Validaciones realizadas

```python
_validate_menu(menu: Menu, request: Request) -> ValidationResult:
    """
    Valida un menú completo (10 validaciones)
    
    1. PRECIO EN RANGO
       - Dentro del rango: ✓
       - Por debajo: Warning (no aprovecha presupuesto)
       - Por encima: ERROR (excede presupuesto)
    
    2. TEMPERATURA DEL ENTRANTE
       - Verano: Cold/Warm apropiado
       - Invierno: Hot apropiado
       - Mal: Warning
    
    3. COMPATIBILIDAD DE SABORES
       - Verificar starter-main, main-dessert
       - Usar FLAVOR_COMPATIBILITY
       - Incompatible: Warning/Error
    
    4. CATEGORÍAS INCOMPATIBLES
       - Meat + Fish: ERROR
       - Soup + Cream: ERROR
       - Legume + Pasta: ERROR
    
    5. CALORÍAS SEGÚN TEMPORADA
       - Verano: 550-950 kcal
       - Invierno: 850-1450 kcal
       - Fuera de rango: Warning
    
    6. POSTRE TRAS PLATO GRASO
       - Si main muy graso → postre ligero (frutas)
       - Si main muy graso + postre graso: Warning
    
    7. COMPLEJIDAD PARA EVENTO
       - Boda: Medium/High OK
       - Familiar: Low/Medium OK
       - Corporate: Medium OK
       - Inadecuado: Warning
    
    8. PROPORCIONES DE PRECIO
       - Main: 35-50% del total
       - Starter ≈ Dessert
       - Beverage: <30%
       - Desequilibrado: Warning
    
    9. RESTRICCIONES DIETÉTICAS (CRÍTICO)
       - Debe cumplir TODAS las dietas requeridas
       - No cumple: ERROR (eliminatorio)
    
    10. INGREDIENTES RESTRINGIDOS (CRÍTICO)
        - No debe tener ingredientes prohibidos
        - Contiene: ERROR (eliminatorio)
    
    Determina status según errores y warnings:
    - 0 errores, 0 warnings: VALID
    - 0 errores, 1-3 warnings: VALID_WITH_WARNINGS
    - 0 errores, >3 warnings: INVALID (si strict_mode)
    - ≥1 error: INVALID
    """
```

### 3.5 Cálculo de puntuación

```python
_calculate_score(menu: Menu, request: Request, issues: List[ValidationIssue]) -> float:
    """
    Calcula puntuación 0-100 del menú
    
    Base: 100 puntos
    
    Penalizaciones:
    - Cada ERROR: -30 puntos
    - Cada WARNING: -10 puntos
    - Cada INFO: -2 puntos
    
    Bonificaciones:
    - Precio en rango óptimo: +5
    - Sabores muy compatibles: +5
    - Estilo perfecto para evento: +5
    - Balance de calorías perfecto: +5
    
    Score final: max(0, min(100, score))
    """
```

### 3.6 Funciones de validación específicas

```python
_validate_price(menu, request) -> Tuple[List[ValidationIssue], List[str]]
_validate_temperature(menu, request) -> Tuple[List[ValidationIssue], List[str]]
_validate_flavors(menu) -> Tuple[List[ValidationIssue], List[str]]
_validate_categories(menu) -> Tuple[List[ValidationIssue], List[str]]
_validate_calories(menu, request) -> Tuple[List[ValidationIssue], List[str]]
_validate_dessert_after_fatty(menu) -> Tuple[List[ValidationIssue], List[str]]
_validate_complexity(menu, request) -> Tuple[List[ValidationIssue], List[str]]
_validate_proportions(menu, request) -> Tuple[List[ValidationIssue], List[str]]
_validate_diets(menu, request) -> Tuple[List[ValidationIssue], List[str]]
_validate_ingredients(menu, request) -> Tuple[List[ValidationIssue], List[str]]

# Todas retornan: (lista de issues, lista de explicaciones positivas)
```

### 3.7 Ejemplo de uso

```python
reviser = MenuReviser(strict_mode=False)

adaptation_results = [...]  # De la fase ADAPT

valid_results = reviser.revise(adaptation_results, request)

for result in valid_results:
    print(f"Menú: {result.menu.id}")
    print(f"Status: {result.status.value}")
    print(f"Score: {result.score}/100")
    
    if result.issues:
        print("Issues:")
        for issue in result.issues:
            print(f"  [{issue.severity}] {issue.message}")
```

---

## 4. retain.py (400 líneas)

**Propósito**: Implementa la fase RETAIN - aprendizaje y retención de nuevos casos.

### 4.1 Clases principales

```python
@dataclass
class RetentionDecision:
    """Decisión sobre si retener un caso"""
    should_retain: bool                  # Si se debe guardar
    reason: str                          # Razón de la decisión
    similarity_to_existing: float        # Similitud con casos existentes
    most_similar_case: Optional[Case]    # Caso más parecido
    action: str                          # "add_new", "update_existing", "discard"

@dataclass
class FeedbackData:
    """Datos de feedback del cliente"""
    menu_id: str
    success: bool                        # Si el evento fue exitoso
    score: float                         # Puntuación 1-5
    comments: str                        # Comentarios del cliente
    would_recommend: bool                # Si lo recomendaría
```

### 4.2 Clase CaseRetainer

```python
class CaseRetainer:
    """Gestor de retención de casos"""
    
    case_base: CaseBase
    similarity_calc: SimilarityCalculator
    
    # Umbrales de retención
    novelty_threshold: float = 0.85      # Si similitud <85%, es novedoso
    quality_threshold: float = 3.5       # Mínimo score 3.5/5
    max_cases_per_event: int = 50        # Límite por tipo de evento
```

### 4.3 Proceso de evaluación

```python
evaluate_retention(request, menu, feedback) -> RetentionDecision:
    """
    Evalúa si un nuevo caso debe ser retenido
    
    ÁRBOL DE DECISIÓN:
    
    1. ¿Score < 3.5?
       → SÍ: DESCARTAR (mala experiencia)
       → NO: Continuar
    
    2. ¿Existen casos en la base?
       → NO: AÑADIR NUEVO (primer caso)
       → SÍ: Continuar
    
    3. Calcular similitud con casos existentes
       similitud = 0.6·sim_request + 0.4·sim_menu
    
    4. ¿Similitud >= 85%? (muy similar a uno existente)
       → SÍ:
          4a. ¿Score nuevo > Score existente?
              → SÍ: ACTUALIZAR EXISTENTE
              → NO: DESCARTAR (ya hay uno igual o mejor)
       → NO: AÑADIR NUEVO (es novedoso)
    
    Returns: RetentionDecision con acción recomendada
    """
```

### 4.4 Métodos principales

```python
retain(request: Request, menu: Menu, feedback: FeedbackData) -> Tuple[bool, str]:
    """
    Retiene un nuevo caso si es apropiado
    
    Proceso:
    1. Evaluar si debe retener (evaluate_retention)
    
    2. Según acción:
       
       ADD_NEW:
       - Crear nuevo Case
       - Añadir a case_base
       - Verificar si necesita mantenimiento
       - Returns: (True, "Nuevo caso añadido: case-20260101-...")
       
       UPDATE_EXISTING:
       - Actualizar menu del caso existente
       - Actualizar feedback_score
       - Incrementar usage_count
       - Añadir nota de adaptación
       - Returns: (True, "Caso actualizado: case-init-3")
       
       DISCARD:
       - No hacer nada
       - Returns: (False, "Score insuficiente" / "Ya existe mejor")
    
    3. Si se añadió/actualizó:
       - Ejecutar mantenimiento si se excede límite
    """

update_case_feedback(case_id: str, feedback: FeedbackData) -> Tuple[bool, str]:
    """
    Actualiza feedback de un caso existente
    
    Usado cuando:
    - Un caso se usa múltiples veces
    - Se recibe nuevo feedback del mismo menú
    
    Proceso:
    - Calcular promedio ponderado de scores
      nuevo_score = (score_old * usage_count + score_new) / (usage_count + 1)
    - Actualizar success (AND lógico)
    - Incrementar usage_count
    - Actualizar comentarios si hay nuevos
    """
```

### 4.5 Mantenimiento de la base

```python
_maintenance_if_needed(event_type: EventType):
    """
    Limpia la base cuando se excede el límite
    
    Proceso:
    1. Contar casos del tipo de evento
    
    2. ¿Excede max_cases_per_event (50)?
       → NO: No hacer nada
       → SÍ: Continuar
    
    3. Calcular utilidad de cada caso
       utility = _calculate_case_utility(case)
    
    4. Ordenar por utilidad (descendente)
    
    5. Mantener solo los mejores 50
    
    6. Eliminar los demás
    
    7. Reconstruir índices
    """

_calculate_case_utility(case: Case) -> float:
    """
    Calcula utilidad de un caso (para decidir si mantener)
    
    Factores:
    
    1. FEEDBACK (50 puntos máximo)
       - Score 5.0 → 50 puntos
       - Score 2.5 → 25 puntos
       - Fórmula: score * 10
    
    2. USO (20 puntos máximo)
       - Cada uso añade 2 puntos
       - Máximo 20 (10 usos)
       - Rendimientos decrecientes
    
    3. ÉXITO (10 puntos)
       - success=True → +10 puntos
       - success=False → 0 puntos
    
    4. RECENCIA (20 puntos máximo)
       - Casos recientes valen más
       - <30 días: 20 puntos
       - 30-90 días: 15 puntos
       - 90-180 días: 10 puntos
       - >180 días: 5 puntos
    
    5. FUENTE (bonus)
       - source="initial": +5 (proteger casos base)
       - source="learned": 0
    
    Total máximo: 105 puntos
    
    Ejemplos:
    - Caso excelente usado frecuentemente: ~95 puntos
    - Caso bueno pero viejo y poco usado: ~40 puntos
    - Caso malo: ~15 puntos → se elimina en limpieza
    """
```

### 4.6 Estadísticas

```python
get_retention_statistics() -> Dict[str, Any]:
    """
    Estadísticas de la base de casos
    
    Returns:
    - total_cases: Total de casos
    - successful_cases: Casos con success=True
    - success_rate: Porcentaje de éxito
    - avg_feedback: Feedback promedio
    - cases_by_event: Distribución por evento
    - cases_by_source: inicial vs aprendidos
    - avg_usage: Uso promedio de casos
    - recent_additions: Casos añadidos recientemente
    """
```

### 4.7 Ejemplo completo

```python
retainer = CaseRetainer(case_base)

# Cliente usó un menú y da feedback
feedback = FeedbackData(
    menu_id="menu-123",
    success=True,
    score=4.8,
    comments="Excelente, a todos les encantó",
    would_recommend=True
)

# Evaluar si retener
decision = retainer.evaluate_retention(request, menu, feedback)

print(f"Decisión: {decision.action}")
print(f"Razón: {decision.reason}")
print(f"¿Retener?: {decision.should_retain}")

# Ejecutar retención
if decision.should_retain:
    success, message = retainer.retain(request, menu, feedback)
    print(message)
```

**Salida típica**:
```
Decisión: add_new
Razón: Caso novedoso para la base de conocimiento
¿Retener?: True
Nuevo caso añadido: case-20260101-143022-456
```

---

## 5. explanation.py (456 líneas)

**Propósito**: Genera explicaciones comprensibles para el usuario sobre las decisiones del sistema.

### 5.1 Enum y clase

```python
class ExplanationType(Enum):
    SELECTION = "selection"              # Por qué se seleccionó
    REJECTION = "rejection"              # Por qué se rechazó
    ADAPTATION = "adaptation"            # Qué se adaptó
    SIMILARITY = "similarity"            # Por qué es similar
    STYLE = "style"                      # Influencia del estilo
    PAIRING = "pairing"                  # Maridaje de bebidas
    CULTURAL = "cultural"                # Tradición cultural

@dataclass
class Explanation:
    """Una explicación generada"""
    type: ExplanationType
    title: str                           # Título de la sección
    content: str                         # Texto principal
    details: List[str]                   # Detalles en lista
    confidence: float = 1.0              # Confianza (0-1)
```

### 5.2 Clase ExplanationGenerator

```python
class ExplanationGenerator:
    """Generador de explicaciones del sistema CBR"""
```

### 5.3 Tipos de explicaciones

#### Explicación de selección
```python
generate_selection_explanation(menu: ProposedMenu, request: Request) -> Explanation:
    """
    Por qué se seleccionó un menú
    
    Incluye:
    - Similitud con caso exitoso previo (96%)
    - Diseñado para el tipo de evento específico
    - Adaptado a la temporada
    - Ajustado al presupuesto
    - Respeta restricciones dietéticas
    
    Ejemplo:
    "Por qué se seleccionó este menú:
     - Similitud con caso exitoso previo: 96%
     - Diseñado específicamente para bodas
     - Adaptado a la temporada de verano
     - Ajustado al presupuesto de 100€ por persona
     - Respeta restricciones: vegetariano"
    """
```

#### Explicación de rechazo
```python
generate_rejection_explanation(case: Case, request: Request, reasons: List[str]) -> Explanation:
    """
    Por qué se descartó un menú
    
    Traduce razones técnicas a lenguaje natural:
    - "budget" → "El precio excede el presupuesto"
    - "diet" → "Contiene ingredientes no compatibles con las dietas"
    - "season" → "Los ingredientes no son óptimos para la temporada"
    - "event" → "El estilo no es adecuado para el evento"
    
    Ejemplo:
    "Por qué se descartó este menú:
     - El precio del menú excede el presupuesto establecido
     - Los ingredientes no son óptimos para la temporada actual
     - Otro menú se ajusta mejor a los requisitos"
    """
```

#### Explicación de adaptaciones
```python
generate_adaptation_explanation(original: Menu, adapted: Menu, adaptations: List[str]) -> Explanation:
    """
    Qué adaptaciones se realizaron
    
    Ejemplo:
    "Adaptaciones realizadas:
     - Sustituido Beef Wellington por Risotto Funghi (vegetariano)
     - Cambiado Rioja Reserva por Lemonade (sin alcohol)
     - Ajustado precio al presupuesto (95€ → 78€)"
    """
```

#### Explicación de estilo
```python
generate_style_explanation(menu: Menu, style: CulinaryStyle) -> Explanation:
    """
    Influencia del estilo culinario
    
    Usa STYLE_DESCRIPTIONS y CHEF_SIGNATURES:
    
    Ejemplo para GOURMET:
    "Estilo Gourmet:
     - Inspirado en chefs como Ferran Adrià y Juan Mari Arzak
     - Énfasis en creatividad y presentación
     - Ingredientes de alta calidad
     - Técnicas modernas de cocina"
    """
```

#### Explicación de maridaje
```python
generate_pairing_explanation(menu: Menu) -> Explanation:
    """
    Por qué se eligió la bebida
    
    Ejemplo:
    "Maridaje Seleccionado - Albariño Rías Baixas:
     - Marida perfectamente con los sabores salados del entrante
     - Complementa el pescado del plato principal
     - Vino blanco afrutado ideal para mariscos
     - Temperatura fresca apropiada para verano"
    """
```

#### Explicación cultural
```python
generate_cultural_explanation(menu: Menu, tradition: CulturalTradition) -> Explanation:
    """
    Tradición cultural del menú
    
    Ejemplo para CATALAN:
    "Tradición Gastronómica Catalana:
     - Cocina mediterránea de raíces profundas
     - Uso de productos locales y de temporada
     - Salsas como sofrito y picada
     - Combinación mar y montaña
     - Platos representativos: este menú"
    """
```

### 5.4 Generación de reporte completo

```python
generate_full_report(proposed_menus: List[ProposedMenu],
                     rejected_cases: List[Dict],
                     request: Request) -> str:
    """
    Genera reporte completo del proceso CBR
    
    Estructura:
    
    === RESUMEN DE LA SOLICITUD ===
    - Tipo de evento
    - Número de comensales
    - Presupuesto
    - Temporada
    - Preferencias
    
    === MENÚS PROPUESTOS ===
    Para cada menú:
    
    OPCIÓN 1 (Similitud: 96%)
    --------------------------
    Entrante: Ceviche Peruano (21€)
    Principal: Lubina a la Parrilla (32€)
    Postre: Frutas Frescas (12€)
    Bebida: Cava Brut Nature (6€)
    TOTAL: 71€/persona
    
    ✓ Por qué se seleccionó:
      - Similitud con caso exitoso previo: 96%
      - Diseñado para bodas
      - Temporada de verano perfecta
      - Precio dentro del rango
    
    ℹ Adaptaciones realizadas:
      - Ninguna (menú usado tal cual)
    
    🍷 Maridaje:
      - Cava espumoso ideal para la celebración
      - Marida con todos los platos
    
    === MENÚS DESCARTADOS ===
    - Caso 'case-init-2' rechazado: Precio excede presupuesto
    - Caso 'case-init-5' rechazado: Temporada no apropiada
    
    === ESTADÍSTICAS DEL PROCESO ===
    - Casos recuperados: 5
    - Casos adaptados: 3
    - Casos validados: 3
    - Casos rechazados: 2
    - Tiempo de procesamiento: 0.35s
    """
```

### 5.5 Helpers

```python
_get_event_description(event_type) -> str:
    # WEDDING → "una boda elegante"
    # FAMILIAR → "una comida familiar"

_get_season_description(season) -> str:
    # SUMMER → "verano, con ingredientes frescos y ligeros"

_format_menu_section(menu, section_name) -> str:
    # Formatea una sección del menú con estilo

_get_diet_friendly_label(diets) -> str:
    # ["vegetarian", "gluten-free"] → "Vegetariano y Sin Gluten"
```

---

## 6. __init__.py

Archivo vacío que convierte `cycle/` en módulo Python.

---

## FLUJO COMPLETO DEL CICLO CBR

```
┌─────────────────────────────────────────────────────────────┐
│ 1. RETRIEVE (retrieve.py)                                    │
│                                                              │
│ Input: Request del cliente                                   │
│                                                              │
│ Proceso:                                                     │
│ ├── Pre-filtrado por índices                                │
│ ├── Cálculo de similitud detallado                          │
│ └── Ranking de casos                                        │
│                                                              │
│ Output: List[RetrievalResult]                               │
│         - Top-K casos más similares (k=3-5)                 │
│         - Con score de similitud                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ADAPT (adapt.py)                                          │
│                                                              │
│ Input: RetrievalResult + Request                            │
│                                                              │
│ Proceso:                                                     │
│ ├── Adaptar restricciones dietéticas                        │
│ ├── Eliminar ingredientes prohibidos                        │
│ ├── Ajustar a presupuesto                                   │
│ ├── Adaptar a temporada                                     │
│ ├── Ajustar bebida                                          │
│ └── Adaptar estilo                                          │
│                                                              │
│ Output: List[AdaptationResult]                              │
│         - 3 menús adaptados                                 │
│         - Con lista de cambios realizados                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. REVISE (revise.py)                                        │
│                                                              │
│ Input: AdaptationResult + Request                           │
│                                                              │
│ Proceso: 10 validaciones                                    │
│ ├── ✓ Precio en rango                                       │
│ ├── ✓ Temperatura apropiada                                 │
│ ├── ✓ Sabores compatibles                                   │
│ ├── ✓ Categorías compatibles                                │
│ ├── ✓ Calorías apropiadas                                   │
│ ├── ✓ Postre tras plato graso                               │
│ ├── ✓ Complejidad apropiada                                 │
│ ├── ✓ Proporciones de precio                                │
│ ├── ✓ Restricciones dietéticas (CRÍTICO)                    │
│ └── ✓ Ingredientes prohibidos (CRÍTICO)                     │
│                                                              │
│ Output: List[ValidationResult]                              │
│         - Solo menús VÁLIDOS                                │
│         - Con score 0-100                                   │
│         - Con lista de issues                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PRESENTACIÓN AL USUARIO                                      │
│                                                              │
│ - 3 opciones de menú válidas                                │
│ - Ordenadas por calidad                                     │
│ - Con explicaciones (explanation.py)                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ CLIENTE ELIGE Y USA EL MENÚ                                  │
│ (evento real ocurre)                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ CLIENTE DA FEEDBACK                                          │
│ - Score: 1-5 estrellas                                       │
│ - Comentarios                                                │
│ - Success: true/false                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. RETAIN (retain.py)                                        │
│                                                              │
│ Input: Request + Menu + FeedbackData                        │
│                                                              │
│ Decisión:                                                    │
│ ├── Score < 3.5? → DESCARTAR                                │
│ ├── Similitud >= 85%?                                       │
│ │   ├── Nuevo mejor? → ACTUALIZAR EXISTENTE                 │
│ │   └── Existente mejor? → DESCARTAR                        │
│ └── Similitud < 85% → AÑADIR NUEVO                          │
│                                                              │
│ Mantenimiento:                                               │
│ └── Si >50 casos del evento → Eliminar los peores          │
│                                                              │
│ Output: Base de casos actualizada                           │
│         - Sistema ha aprendido                              │
└─────────────────────────────────────────────────────────────┘
```

---

## RESUMEN POR ARCHIVO

| Archivo | Líneas | Fase CBR | Propósito Principal |
|---------|--------|----------|---------------------|
| **retrieve.py** | 312 | 1-RETRIEVE | Encuentra casos similares en la base |
| **adapt.py** | 781 | 2-REUSE/ADAPT | Modifica casos para ajustarlos al contexto |
| **revise.py** | 629 | 3-REVISE | Valida que las soluciones sean correctas |
| **retain.py** | 400 | 4-RETAIN | Aprende de nuevas experiencias |
| **explanation.py** | 456 | Auxiliar | Genera explicaciones para el usuario |

**Total: ~2578 líneas de código**

---

## CONCLUSIÓN

La carpeta `cycle/` implementa el **corazón inteligente del sistema CBR**:

✅ **retrieve.py**: Encuentra experiencias relevantes (búsqueda inteligente)  
✅ **adapt.py**: Personaliza soluciones (adaptación creativa)  
✅ **revise.py**: Asegura calidad (validación rigurosa)  
✅ **retain.py**: Aprende continuamente (mejora con el tiempo)  
✅ **explanation.py**: Comunica decisiones (transparencia total)  

Este ciclo permite que el sistema **razone como un chef experto**: busca en su experiencia, adapta recetas al contexto, valida la propuesta, y aprende de cada nuevo evento para mejorar en el futuro.
