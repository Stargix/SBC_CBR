# Sistema de Aprendizaje Adaptativo Dual

## Descripción

Este documento describe el sistema de **aprendizaje adaptativo dual** implementado en el proyecto CBR de elaboración de menús. El sistema aprende automáticamente a mejorar tanto la recuperación de casos como la adaptación de platos mediante el análisis del feedback del usuario.

## Componentes del Sistema

### 1. Aprendizaje de Pesos de Similitud de Casos

**Clase**: `AdaptiveWeightLearner` (en `develop/core/adaptive_weights.py`)

**Propósito**: Aprende qué dimensiones son más importantes al recuperar casos similares.

**Pesos aprendidos**:
- `event_type`: Importancia del tipo de evento
- `season`: Importancia de la temporada
- `price_range`: Importancia del presupuesto
- `style`: Importancia del estilo culinario
- `cultural`: Importancia de la tradición cultural
- `dietary`: Importancia de las restricciones dietéticas
- `guests`: Importancia del número de comensales
- `wine_preference`: Importancia de las preferencias de vino
- `success_bonus`: Bonus por casos exitosos previos

**Uso**:
```python
from develop.core.adaptive_weights import AdaptiveWeightLearner

# Inicializar learner
learner = AdaptiveWeightLearner(learning_rate=0.05)

# Tras recibir feedback del usuario
learner.update_from_feedback(feedback, request)

# Obtener pesos actualizados para usar en similitud
weights = learner.get_current_weights()

# Guardar historial de aprendizaje
learner.save_learning_history("data/learning_history.json")
```

### 2. Aprendizaje de Pesos de Similitud de Platos

**Clase**: `AdaptiveDishWeightLearner` (en `develop/core/adaptive_weights.py`)

**Propósito**: Aprende qué características son más importantes al buscar platos alternativos durante la adaptación.

**Pesos aprendidos**:
- `category`: Importancia de la categoría del plato (soup, pasta, etc.)
- `price`: Importancia del precio
- `complexity`: Importancia de la complejidad de preparación
- `flavors`: Importancia de los perfiles de sabor
- `styles`: Importancia de los estilos culinarios
- `temperature`: Importancia de la temperatura (hot/cold)
- `diets`: Importancia de las restricciones dietéticas
- `cultural`: Importancia de la adecuación cultural

**Uso**:
```python
from develop.core.adaptive_weights import AdaptiveDishWeightLearner

# Inicializar learner
dish_learner = AdaptiveDishWeightLearner(learning_rate=0.05)

# Tras una adaptación con feedback
dish_learner.update_from_feedback(
    original_dish=dish1,
    replacement_dish=dish2,
    feedback_score=4.5,
    adaptation_reason="dietary"
)

# Obtener pesos actualizados
weights = dish_learner.get_current_weights()

# Usar en calculate_dish_similarity
from develop.core.similarity import calculate_dish_similarity
similarity = calculate_dish_similarity(dish_a, dish_b, weights=weights)
```

### 3. Pesos Configurables en Similitud de Platos

**Clase**: `DishSimilarityWeights` (en `develop/core/similarity.py`)

**Función mejorada**: `calculate_dish_similarity()`

La función ahora acepta un parámetro opcional `weights` que permite usar pesos personalizados:

```python
from develop.core.similarity import calculate_dish_similarity, DishSimilarityWeights

# Con pesos por defecto
similarity = calculate_dish_similarity(dish1, dish2)

# Con pesos personalizados
custom_weights = DishSimilarityWeights(
    category=0.25,  # Más importancia a la categoría
    flavors=0.20,   # Más importancia a los sabores
    # ... otros pesos
)
custom_weights.normalize()
similarity = calculate_dish_similarity(dish1, dish2, weights=custom_weights)

# Con pesos aprendidos
learner = AdaptiveDishWeightLearner()
# ... tras varias iteraciones de aprendizaje
learned_weights = learner.get_current_weights()
similarity = calculate_dish_similarity(dish1, dish2, weights=learned_weights)
```

## Estrategias de Aprendizaje

### Para Similitud de Casos

El sistema ajusta los pesos basándose en la satisfacción del cliente:

**Feedback Bajo (< 3)**:
- Si el precio fue problemático → Aumenta `price_range`
- Si la cultura no se respetó → Aumenta `cultural`
- Si el sabor fue malo → Aumenta `style`
- Si las dietas no se cumplieron → **Aumenta mucho** `dietary` (crítico)

**Feedback Alto (≥ 4)**:
- Refuerza los criterios que funcionaron bien
- Pequeños aumentos en dimensiones exitosas

**Feedback Medio (3)**:
- Ajustes finos y menores

### Para Similitud de Platos

El sistema ajusta los pesos basándose en el éxito de las adaptaciones:

**Adaptación Exitosa (score ≥ 4)**:
- Si mantuvieron la misma categoría → Refuerza `category`
- Si los estilos fueron similares → Refuerza `styles`
- Si los sabores coincidieron → Refuerza `flavors`
- Si fue adaptación cultural exitosa → Refuerza `cultural`
- Si fue adaptación dietética exitosa → Refuerza `diets`

**Adaptación Problemática (score < 3)**:
- Si cambiaron la categoría → **Aumenta mucho** `category`
- Si cambiaron el estilo → Aumenta `styles`
- Si el precio difirió mucho → Aumenta `price`
- Si los sabores fueron muy diferentes → Aumenta `flavors`

## Integración en el Ciclo CBR

```
┌─────────────────────────────────────────────────────────────┐
│                    CICLO CBR COMPLETO                        │
└─────────────────────────────────────────────────────────────┘

1️⃣ RETRIEVE (Recuperación)
   ├─ Usa: case_learner.get_current_weights()
   ├─ Calcula similitud entre Request y Cases
   └─ Retorna los K casos más similares

2️⃣ REUSE (Reutilización)
   └─ Usa el caso más similar como base

3️⃣ REVISE/ADAPT (Adaptación)
   ├─ Si necesita reemplazar platos:
   │  ├─ Usa: dish_learner.get_current_weights()
   │  ├─ Busca platos similares con calculate_dish_similarity()
   │  └─ Selecciona el mejor reemplazo
   └─ Aplica adaptaciones culturales, dietéticas, etc.

4️⃣ RETAIN (Retención y Aprendizaje)
   ├─ Recibe feedback del usuario
   ├─ Actualiza: case_learner.update_from_feedback(feedback, request)
   ├─ Por cada adaptación de plato:
   │  └─ Actualiza: dish_learner.update_from_feedback(...)
   ├─ Guarda historiales de aprendizaje
   └─ Los nuevos pesos se usan en la próxima iteración
```

## Ejemplo Completo

```python
from develop.core.adaptive_weights import AdaptiveWeightLearner, AdaptiveDishWeightLearner
from develop.core.similarity import SimilarityCalculator, calculate_dish_similarity

# === INICIALIZACIÓN ===
case_learner = AdaptiveWeightLearner(learning_rate=0.05)
dish_learner = AdaptiveDishWeightLearner(learning_rate=0.05)

# === RETRIEVE (usando pesos aprendidos de casos) ===
case_weights = case_learner.get_current_weights()
similarity_calc = SimilarityCalculator(weights=case_weights)
best_cases = retrieve_similar_cases(request, cases, similarity_calc)

# === ADAPT (usando pesos aprendidos de platos) ===
dish_weights = dish_learner.get_current_weights()
if need_replacement:
    candidates = get_candidate_dishes(...)
    best_replacement = None
    best_similarity = 0
    
    for candidate in candidates:
        sim = calculate_dish_similarity(
            original_dish, 
            candidate, 
            weights=dish_weights
        )
        if sim > best_similarity:
            best_similarity = sim
            best_replacement = candidate
    
    # Reemplazar plato
    adapted_menu = replace_dish(menu, best_replacement)

# === RETAIN (actualizar ambos learners) ===
# Recibir feedback del usuario
feedback = get_user_feedback(adapted_menu)

# Actualizar pesos de casos
case_learner.update_from_feedback(feedback, request)

# Actualizar pesos de platos (por cada adaptación realizada)
if dish_was_replaced:
    dish_learner.update_from_feedback(
        original_dish=original_dish,
        replacement_dish=best_replacement,
        feedback_score=feedback.overall_satisfaction,
        adaptation_reason="dietary"  # o "cultural", "general", etc.
    )

# Guardar historiales
case_learner.save_learning_history("data/case_learning.json")
dish_learner.save_learning_history("data/dish_learning.json")
```

## Demostración

Ejecuta el script de demostración para ver el sistema en acción:

```bash
python develop/demo_dual_weight_learning.py
```

Este demo muestra:
1. **Demo 1**: Aprendizaje de pesos de casos con 3 escenarios (insatisfacción con precio, cultura, y éxito total)
2. **Demo 2**: Aprendizaje de pesos de platos con 3 escenarios (adaptación exitosa, cambio problemático de categoría, adaptación dietética)
3. **Demo 3**: Integración de ambos learners en el ciclo CBR

## Análisis del Historial

Los archivos JSON generados contienen:

```json
{
  "metadata": {
    "learner_type": "dish_similarity",
    "total_iterations": 15,
    "learning_rate": 0.05,
    "min_weight": 0.02,
    "max_weight": 0.50
  },
  "history": [
    {
      "timestamp": "2026-01-07T10:30:00",
      "iteration": 1,
      "weights": {
        "category": 0.155,
        "price": 0.149,
        ...
      },
      "feedback_score": 4.5,
      "adjustments": ["Reforzar importancia de categoría"]
    }
  ],
  "summary": {
    "total_iterations": 15,
    "most_changed": [
      {"weight": "category", "change": 0.025, "change_pct": "+16.7%"},
      {"weight": "diets", "change": 0.018, "change_pct": "+18.0%"}
    ]
  }
}
```

## Parámetros de Configuración

### Learning Rate (Tasa de Aprendizaje)

Controla qué tan rápido se adaptan los pesos:

- **0.01-0.03**: Aprendizaje lento y conservador
- **0.05-0.08**: Balance entre estabilidad y adaptación (recomendado)
- **0.10-0.15**: Aprendizaje rápido pero más volátil

```python
# Aprendizaje conservador
learner = AdaptiveWeightLearner(learning_rate=0.03)

# Aprendizaje equilibrado (recomendado)
learner = AdaptiveWeightLearner(learning_rate=0.05)

# Aprendizaje agresivo
learner = AdaptiveWeightLearner(learning_rate=0.12)
```

### Límites de Pesos

Evitan que un peso domine completamente:

- **min_weight**: Peso mínimo permitido (default: 0.02)
- **max_weight**: Peso máximo permitido (default: 0.50)

```python
learner = AdaptiveWeightLearner(
    learning_rate=0.05,
    min_weight=0.01,  # Permitir pesos muy pequeños
    max_weight=0.40   # Limitar dominación
)
```

## Ventajas del Sistema Dual

1. **Especialización**: Cada learner se enfoca en su dominio específico
2. **Precisión**: Mejora tanto la recuperación de casos como la adaptación de platos
3. **Independencia**: Los learners no interfieren entre sí
4. **Complementariedad**: Trabajan juntos para mejorar el sistema completo
5. **Trazabilidad**: Historiales separados para análisis detallado

## Visualización (Opcional)

Si tienes matplotlib instalado, puedes generar gráficas de evolución:

```python
# Instalar matplotlib
# pip install matplotlib

# Generar gráfica de evolución de pesos
case_learner.plot_evolution("docs/case_weights_evolution.png")
dish_learner.plot_evolution("docs/dish_weights_evolution.png")

# Generar gráfica de correlación con feedback
case_learner.plot_feedback_correlation("docs/feedback_correlation.png")
```

## Próximos Pasos

Para integrar completamente el sistema en tu aplicación:

1. **En `retrieve.py`**: Usar `case_learner.get_current_weights()` al calcular similitud
2. **En `adapt.py`**: Usar `dish_learner.get_current_weights()` al buscar platos de reemplazo
3. **En `retain.py`**: Actualizar ambos learners con el feedback
4. **Persistencia**: Guardar y cargar pesos aprendidos entre sesiones
5. **UI**: Mostrar al usuario cómo está aprendiendo el sistema

## Preguntas Frecuentes

**P: ¿Los pesos se reinician cada vez?**
R: No, puedes guardar el historial con `save_learning_history()` y cargar pesos previos al inicializar.

**P: ¿Qué pasa si el feedback es inconsistente?**
R: El learning rate controla esto. Con tasas bajas (0.03-0.05), el sistema es robusto ante feedback errático.

**P: ¿Puedo tener múltiples perfiles de aprendizaje?**
R: Sí, puedes crear instancias separadas para diferentes tipos de eventos o clientes.

**P: ¿Cómo reseteo el aprendizaje?**
R: Usa `learner.reset_to_defaults()` para volver a pesos iniciales.

## Referencias

- Wettschereck & Aha (1995): "Weighting Features"
- Stahl & Gabel (2003): "Using Evolution Programs to Learn Local Similarity Measures"
- Aamodt & Plaza (1994): "Case-Based Reasoning: Foundational Issues"
