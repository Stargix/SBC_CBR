# Análisis: Puntuación de Calidad en REVISE

## 🔍 El Problema Actual

La puntuación de calidad **siempre está cerca de 80** porque:

### 1. **Cálculo Simplista**

```python
def _calculate_score(self, menu: Menu, request: Request,
                     issues: List[ValidationIssue]) -> float:
    """
    Calcula una puntuación de calidad para el menú.
    
    Returns:
        Puntuación entre 0 y 100
    """
    score = 100.0  # ⚠️ EMPIEZA SIEMPRE EN 100
    
    # Penalizar por issues
    for issue in issues:
        if issue.severity == "error":
            score -= 25      # Error: -25 puntos
        elif issue.severity == "warning":
            score -= 10      # Warning: -10 puntos
        elif issue.severity == "info":
            score -= 2       # Info: -2 puntos
    
    # Bonus por estar en centro del rango de precio
    if request.price_max > request.price_min:
        center = (request.price_min + request.price_max) / 2
        deviation = abs(menu.total_price - center) / (request.price_max - request.price_min)
        # Bonus si está cerca del centro
        if deviation < 0.2:
            score += 5       # +5 puntos máximo
    
    # Bonus por feedback alto si viene de un caso
    if hasattr(menu, 'source_case_feedback'):
        score += menu.source_case_feedback * 2  # +0 a +10 puntos
    
    return max(0, min(100, score))
```

### 2. **Por Qué Siempre es ~80**

**Escenario típico:**
- Empieza en: **100 puntos**
- Menú tiene 2 warnings típicos: **-20 puntos**
- Total: **80 puntos** ✅

**Los warnings comunes son:**
1. "Temperatura del entrante no ideal para la temporada" (-10)
2. "Adaptación cultural limitada" (-10)
3. "Calorías ligeramente fuera de rango" (-2)

**Resultado:** `100 - 10 - 10 = 80` 🎯

### 3. **Problemas del Sistema Actual**

❌ **No discrimina bien:**
- Un menú perfecto: 100 puntos
- Un menú con 2 warnings: 80 puntos
- Un menú con 4 warnings: 60 puntos
- **Solo 40 puntos de rango útil (60-100)**

❌ **Penalizaciones arbitrarias:**
- ¿Por qué -10 por warning y no -5 o -15?
- ¿Por qué -25 por error y no -20 o -30?
- **No hay justificación teórica**

❌ **Bonus insignificantes:**
- +5 puntos por precio centrado
- +10 puntos máximo por feedback
- **Apenas afectan la puntuación final**

❌ **No considera aspectos positivos:**
- Armonía de sabores ✓
- Compatibilidad de categorías ✓
- Temperatura apropiada ✓
- Calorías balanceadas ✓
- **Solo resta, no suma**

---

## ✅ Solución Propuesta

### Sistema de Puntuación Mejorado

```python
def _calculate_score(self, menu: Menu, request: Request,
                     issues: List[ValidationIssue]) -> float:
    """
    Calcula puntuación basada en múltiples factores ponderados.
    
    Componentes (0-100):
    - Cumplimiento de restricciones (30%)
    - Calidad gastronómica (25%)
    - Adaptación cultural (20%)
    - Adecuación al evento (15%)
    - Relación calidad-precio (10%)
    
    Returns:
        Puntuación entre 0 y 100
    """
    
    # 1. CUMPLIMIENTO DE RESTRICCIONES (0-30 puntos)
    compliance_score = 30.0
    for issue in issues:
        if issue.category in ["ingredients", "diets"]:
            if issue.severity == "error":
                compliance_score = 0  # Fallo crítico
                break
            elif issue.severity == "warning":
                compliance_score -= 10
    
    # 2. CALIDAD GASTRONÓMICA (0-25 puntos)
    gastro_score = 25.0
    
    # Penalizar incompatibilidades
    for issue in issues:
        if issue.category in ["categories", "flavors"]:
            if issue.severity == "error":
                gastro_score -= 15
            elif issue.severity == "warning":
                gastro_score -= 5
    
    # Bonus por armonías detectadas
    harmony_count = sum(1 for exp in explanations 
                       if "armonía" in exp.lower() or "complementa" in exp.lower())
    gastro_score += min(5, harmony_count * 2)
    
    # 3. ADAPTACIÓN CULTURAL (0-20 puntos)
    cultural_score = 20.0
    
    if request.cultural_preference:
        for issue in issues:
            if issue.category == "culture":
                if issue.severity == "warning":
                    cultural_score -= 10
                elif issue.severity == "info":
                    cultural_score -= 5
    else:
        cultural_score = 20.0  # No aplica, puntaje completo
    
    # 4. ADECUACIÓN AL EVENTO (0-15 puntos)
    event_score = 15.0
    
    for issue in issues:
        if issue.category in ["temperature", "calories", "complexity"]:
            if issue.severity == "warning":
                event_score -= 5
            elif issue.severity == "info":
                event_score -= 2
    
    # 5. RELACIÓN CALIDAD-PRECIO (0-10 puntos)
    price_score = 10.0
    
    # Penalizar si está fuera de rango
    for issue in issues:
        if issue.category == "price":
            if issue.severity == "error":
                price_score = 0
            elif issue.severity == "warning":
                price_score -= 5
    
    # Bonus por estar centrado
    if request.price_max > request.price_min:
        center = (request.price_min + request.price_max) / 2
        deviation = abs(menu.total_price - center) / (request.price_max - request.price_min)
        if deviation < 0.1:  # Muy centrado
            price_score += 3
        elif deviation < 0.2:  # Centrado
            price_score += 2
    
    # Bonus por feedback histórico
    feedback_bonus = 0
    if hasattr(menu, 'source_case_feedback') and menu.source_case_feedback:
        # Feedback 5 estrellas = +5 puntos extra
        feedback_bonus = (menu.source_case_feedback - 3) * 2.5
        feedback_bonus = max(0, min(5, feedback_bonus))
    
    # TOTAL
    total = (compliance_score + gastro_score + cultural_score + 
             event_score + price_score + feedback_bonus)
    
    return max(0, min(100, total))
```

### Distribución de Puntos

| Componente | Peso | Rango |
|------------|------|-------|
| **Cumplimiento restricciones** | 30% | 0-30 |
| **Calidad gastronómica** | 25% | 0-25 |
| **Adaptación cultural** | 20% | 0-20 |
| **Adecuación al evento** | 15% | 0-15 |
| **Relación calidad-precio** | 10% | 0-10 |
| **Bonus feedback histórico** | - | 0-5 |
| **TOTAL** | **100%** | **0-105** |

---

## 📊 Ejemplos de Puntuación Nueva

### Escenario 1: Menú Perfecto
```
Cumplimiento: 30 (sin issues)
Gastronómica: 25 (armonías detectadas)
Cultural: 20 (bien adaptado)
Evento: 15 (temperatura y calorías ideales)
Precio: 10 (centrado en rango)
Feedback: +5 (caso exitoso previo)
--------------------------------------------
TOTAL: 105 → normalizado a 100
```

### Escenario 2: Menú Bueno con Warnings Menores
```
Cumplimiento: 30 (sin restricciones violadas)
Gastronómica: 20 (1 warning de sabores)
Cultural: 15 (adaptación moderada)
Evento: 10 (temperatura no ideal)
Precio: 10 (dentro de rango)
Feedback: +2 (feedback medio)
--------------------------------------------
TOTAL: 87
```

### Escenario 3: Menú Mediocre
```
Cumplimiento: 20 (2 warnings dietéticos)
Gastronómica: 10 (incompatibilidad de sabores)
Cultural: 5 (adaptación limitada)
Evento: 5 (varios issues)
Precio: 5 (lejos del centro)
Feedback: 0 (sin historial)
--------------------------------------------
TOTAL: 45
```

### Escenario 4: Menú Rechazado
```
Cumplimiento: 0 (ERROR: ingrediente prohibido)
Gastronómica: 5
Cultural: 5
Evento: 5
Precio: 0 (ERROR: fuera de presupuesto)
Feedback: 0
--------------------------------------------
TOTAL: 15 → RECHAZADO
```

---

## 🎯 Ventajas del Nuevo Sistema

### 1. **Mayor Rango de Discriminación**
- Antes: 60-100 (40 puntos útiles)
- Ahora: 15-100 (85 puntos útiles)
- **Mayor capacidad para ordenar menús**

### 2. **Ponderación Justificada**
- Cumplimiento (30%): **Lo más importante**
- Calidad (25%): **Experiencia gastronómica**
- Cultura (20%): **Personalización**
- Evento (15%): **Contexto**
- Precio (10%): **Valor**

### 3. **Considera Aspectos Positivos**
- Armonías de sabores: +puntos
- Feedback histórico: +puntos
- Precio centrado: +puntos
- **No solo penaliza, también premia**

### 4. **Transparencia**
- Cada componente es trazable
- Se puede explicar por qué un menú tiene X puntuación
- Fácil de ajustar pesos según prioridades

---

## 🔧 Implementación

El nuevo cálculo se implementa en:
- **Archivo:** `develop/cycle/revise.py`
- **Método:** `_calculate_score()`
- **Líneas:** ~601-640

También se necesita pasar `explanations` al método para detectar armonías:
```python
score = self._calculate_score(menu, request, issues, explanations)
```

---

## 📌 Conclusión

**El problema:** Puntuación simplista (100 - penalizaciones) resulta en valores acotados (~80).

**La solución:** Sistema ponderado por componentes con rango amplio y bonificaciones.

**Resultado:** Mejor discriminación, puntuaciones más significativas, y explicabilidad mejorada.
