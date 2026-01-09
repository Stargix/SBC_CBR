# Solución: Evaluación Separada de Dimensiones de Satisfacción

## Problema Identificado

**A. Sobresimplificación del feedback:**
- Todas las dimensiones de satisfacción se derivaban del score único del LLM
- No se podía distinguir qué aspecto específico causó insatisfacción
- El aprendizaje era menos efectivo al no identificar el problema exacto

## Solución Implementada

### 1. Modificación de `FeedbackData` (develop/cycle/retain.py)

Añadidos campos específicos para cada dimensión:

```python
@dataclass
class FeedbackData:
    menu_id: str
    success: bool
    score: float  # Puntuación general (1-5)
    comments: str
    would_recommend: bool
    # 🆕 Dimensiones específicas de satisfacción
    price_satisfaction: Optional[float] = None       # 1-5
    cultural_satisfaction: Optional[float] = None    # 1-5
    flavor_satisfaction: Optional[float] = None      # 1-5
```

### 2. Evaluación LLM con Dimensiones Separadas (simulation/groq_simulator.py)

#### Prompt Actualizado

El LLM ahora evalúa cada dimensión por separado:

```
Evalúa CADA DIMENSIÓN POR SEPARADO (escala 0.0-5.0):

1. PRECIO: ¿Está dentro del presupuesto? ¿Es apropiado para el evento?
2. CULTURA: ¿El menú respeta la tradición cultural solicitada?
3. SABOR: ¿Los sabores y combinaciones son coherentes?
4. DIETAS: ¿Se cumplen las restricciones dietéticas?

Termina con:
PRECIO: X.X
CULTURA: X.X
SABOR: X.X
GENERAL: X.X
```

#### Nuevo Método: `_extract_dimension_scores_from_evaluation()`

Extrae las puntuaciones individuales del response del LLM:

```python
def _extract_dimension_scores_from_evaluation(self, evaluation_text: str) -> Dict[str, float]:
    """
    Extrae las puntuaciones de cada dimensión de la evaluación del LLM.
    
    Returns:
        Dict con: 'price', 'cultural', 'flavor', 'overall'
    """
    # Usa regex para extraer cada dimensión
    patterns = {
        'price': r'(?:PRECIO|PRICE):\s*(\d+\.?\d*)',
        'cultural': r'(?:CULTURA|CULTURAL):\s*(\d+\.?\d*)',
        'flavor': r'(?:SABOR|FLAVOR):\s*(\d+\.?\d*)',
        'overall': r'(?:GENERAL|OVERALL):\s*(\d+\.?\d*)'
    }
    # ...
```

### 3. Aprendizaje con Dimensiones Específicas (develop/main.py)

La función `learn_from_feedback()` ahora usa las dimensiones específicas:

```python
def learn_from_feedback(self, feedback_data: FeedbackData, request: Request):
    # Usar las dimensiones específicas si están disponibles
    price_sat = feedback_data.price_satisfaction if feedback_data.price_satisfaction is not None else feedback_data.score
    cultural_sat = feedback_data.cultural_satisfaction if feedback_data.cultural_satisfaction is not None else feedback_data.score
    flavor_sat = feedback_data.flavor_satisfaction if feedback_data.flavor_satisfaction is not None else feedback_data.score
    
    feedback = Feedback(
        overall_satisfaction=feedback_data.score,
        price_satisfaction=price_sat,        # 🆕 Específico
        cultural_satisfaction=cultural_sat,   # 🆕 Específico
        flavor_satisfaction=flavor_sat,       # 🆕 Específico
        dietary_satisfaction=5.0 if feedback_data.success else 2.0,
        comments=feedback_data.comments
    )
    # ...
```

## Ventajas de la Solución

### ✅ Feedback Más Preciso
- El LLM evalúa cada dimensión independientemente
- Se identifica exactamente qué aspecto falló

### ✅ Aprendizaje Más Efectivo
- El sistema ajusta pesos específicos según dimensión problemática
- Si falla precio → aumenta peso de `price_range`
- Si falla cultura → aumenta peso de `cultural`
- Si falla sabor → ajusta pesos de adaptación de platos

### ✅ Evita Sobresimplificación
- Ya no se usa un solo score para todas las dimensiones
- Cada aspecto tiene su propia evaluación independiente

### ✅ Retrocompatibilidad
- Los campos de dimensión son `Optional[float]`
- Si no se proporcionan, usa el score general como fallback
- El código antiguo sigue funcionando

## Ejemplo de Uso

```python
# Feedback con dimensiones diferenciadas
feedback = FeedbackData(
    menu_id="menu_001",
    success=False,
    score=2.5,  # Score general bajo
    comments="Precio excesivo para el evento",
    would_recommend=False,
    price_satisfaction=1.5,      # ⚠️ Problema identificado
    cultural_satisfaction=4.5,   # ✅ Cultura OK
    flavor_satisfaction=4.0      # ✅ Sabor OK
)

# El sistema aprende que el problema fue el PRECIO
cbr.learn_from_feedback(feedback, request)
# → Incrementa peso de 'price_range' en similitud
# → Futuras búsquedas priorizarán casos con mejor precio
```

## Flujo Completo

```
1. Usuario solicita menú
   ↓
2. CBR propone menú
   ↓
3. LLM evalúa CADA DIMENSIÓN por separado:
   - Precio: 4.5/5 ✅
   - Cultura: 2.0/5 ⚠️
   - Sabor: 4.0/5 ✅
   ↓
4. Se crea FeedbackData con scores separados
   ↓
5. learn_from_feedback() detecta problema CULTURAL
   ↓
6. Ajusta peso de 'cultural' en similitud
   ↓
7. Próximas búsquedas priorizan match cultural
```

## Archivos Modificados

1. **develop/cycle/retain.py**
   - Añadidos campos de dimensión a `FeedbackData`

2. **simulation/groq_simulator.py**
   - Actualizado prompt para evaluar dimensiones separadas
   - Nuevo método `_extract_dimension_scores_from_evaluation()`
   - Actualizado `_apply_learning_from_score()` para usar dimensiones

3. **develop/main.py**
   - Actualizado `learn_from_feedback()` para usar dimensiones específicas

## Testing

Ejecutar el test de demostración:

```bash
python test_separate_dimensions.py
```

Esto demuestra:
- Cómo crear FeedbackData con dimensiones separadas
- Cómo el CBR aprende de cada dimensión
- Diferentes escenarios (problema de precio, cultura, sabor)

## Próximos Pasos Sugeridos

1. **Validación con casos reales**: Probar con simulaciones completas
2. **Análisis de efectividad**: Comparar aprendizaje antes/después
3. **Dashboard de dimensiones**: Visualizar scores por dimensión
4. **Pesos por dimensión**: Considerar pesos adaptativos también para dishes
