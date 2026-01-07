# Sistema de Explicabilidad Completa - Chef Digital CBR

## 🎯 Objetivo

Refactorizar el sistema para que `explanation.py` sea el **único módulo responsable de generar explicaciones**, utilizando **datos estructurados** de todas las fases del CBR en lugar de prints incondicionales dispersos por el código.

## 📋 Problemas Identificados

### 1. **Prints Incondicionales**
   - **adapt.py (líneas 921-1031)**: Prints con emojis 🔍📊✅ en `_find_cultural_dish_replacement()`
   - **retain.py (líneas 313, 431, 588-589)**: Prints de mantenimiento de casos
   - Estos prints se ejecutaban **incluso con `verbose=False`**

### 2. **Explicaciones Superficiales**
   - `explanation.py` solo usaba `menu.similarity_score` (un número)
   - **NO** usaba `similarity_details` (desglose por 9 criterios)
   - **NO** mostraba detalles de ADAPT (qué sustituciones se hicieron)
   - **NO** mostraba detalles de REVISE (warnings, validaciones)
   - **NO** explicaba RETAIN (decisiones de retención)

### 3. **Pérdida de Información**
   - `RetrievalResult.similarity_details` existía pero no se usaba
   - `AdaptationResult.adaptations_made` no se mostraba completamente
   - `ValidationResult.issues` se perdían en el informe final

## ✅ Solución Implementada

### 1. **Eliminación de Prints (Data-Driven)**

#### adapt.py
```python
# ANTES: Prints incondicionales
print(f"\n   🔍 BÚSQUEDA DE REEMPLAZO para {original_dish.name}")
print(f"      Cultura objetivo: {target_culture_name}")
print(f"      📊 TOP 5 candidatos:")
print(f"      ✅ SELECCIONADO: {best_dish.name}")

# DESPUÉS: Datos capturados en AdaptationResult
# Toda la información se guarda en adaptations_made[]
# y se procesa en explanation.py para generar explicaciones
```

#### retain.py
```python
# ANTES: Prints con emojis
print(f"🧹 Mantenimiento: {len(to_remove)} casos redundantes eliminados")
print(f"🗑️ Política de olvido: {to_remove_count} casos eliminados")

# DESPUÉS: Datos estructurados en RetainResult
# La información se registra en metadata y se puede consultar
```

### 2. **Explicabilidad Completa en explanation.py**

#### generate_full_report() Mejorado

```python
def generate_full_report(self, proposed_menus, rejected_cases, request, 
                         retrieval_results=None):
    """
    ANTES: ~200 palabras, solo similitud global
    DESPUÉS: ~1000+ palabras, desglose completo de RETRIEVE/ADAPT/REVISE
    """
```

**Estructura del nuevo informe:**

```
================================================================================
INFORME COMPLETO DE RAZONAMIENTO CBR - Chef Digital
================================================================================

📋 SOLICITUD RECIBIDA
- Tipo de evento, comensales, presupuesto, temporada
- Restricciones dietéticas, ingredientes prohibidos
- Preferencias culturales y de estilo

🔍 FASE 1: RETRIEVE - Recuperación de casos similares
  Caso #1: case-init-7 (Similitud: 83.3%)
    Desglose de similitud:
      • Tipo de evento       : 60.0% ████████████
      • Rango de precio      : 100.0% ████████████████████
      • Temporada            : 100.0% ████████████████████
      • Tradición cultural   : 80.0% ████████████████
      • Requisitos dietéticos: 100.0% ████████████████████

✅ FASE 2-3: ADAPT + REVISE - Menús adaptados y validados

🍽️ PROPUESTA #1
================================================================================
📋 COMPOSICIÓN DEL MENÚ:
  Entrante:     Ensalada Caprese
  Plato Fuerte: Risotto ai Funghi
  Postre:       Tiramisu
  💰 Precio total: 58.50€ por persona

🔍 RETRIEVE: Caso base seleccionado
  • Caso origen: case-init-7
  • Similitud inicial: 83.3%
  • Desglose:
    - event_type: 60.0%
    - price_range: 100.0%
    - season: 100.0%

🔧 ADAPT: Adaptaciones aplicadas (3 total)
  1. Ajuste de precio: 62.00€ → 58.50€
  2. Ensalada Caprese: tomate→tomate cherry (temporada)
  3. Añadido maridaje: Vino blanco Frascati

✓ REVISE: Validación del menú
  • Estado: VALID
  • Puntuación de calidad: 92.5%
  • Advertencias (0)
  • Explicaciones de validación:
    → Compatibilidad de categorías: ÓPTIMA
    → Compatibilidad de sabores: EXCELENTE
    → Proporción de precios: EQUILIBRADA

❌ MENÚS DESCARTADOS EN FASE REVISE
  1. case-init-22 (Similitud: 75.2%)
     • Precio excede presupuesto en 12%
     • Combinación de temperaturas no óptima

📊 RESUMEN DEL PROCESO CBR
✓ Casos analizados en RETRIEVE: 3
✓ Menús adaptados en ADAPT: 4
✓ Menús validados en REVISE: 1
✓ Menús rechazados: 3
✓ Propuestas finales presentadas: 1
```

### 3. **Flujo de Información**

```
REQUEST
   ↓
RETRIEVE
   ├→ RetrievalResult.similarity_details (9 criterios)
   ├→ RetrievalResult.similarity (global)
   └→ RetrievalResult.case
       ↓
ADAPT
   ├→ AdaptationResult.adaptations_made[] (lista detallada)
   ├→ AdaptationResult.original_similarity
   └→ AdaptationResult.final_similarity
       ↓
REVISE
   ├→ ValidationResult.status
   ├→ ValidationResult.score
   ├→ ValidationResult.issues[] (warnings/errors)
   └→ ValidationResult.explanations[]
       ↓
EXPLANATION.PY
   └→ generate_full_report(
         proposed_menus,
         rejected_cases,
         request,
         retrieval_results  ← ¡AHORA SE PASA!
      )
```

### 4. **Cambios en main.py**

```python
# ANTES: Solo pasaba tuplas (case, similarity)
retrieved_cases = self._retrieve_phase(request)

# DESPUÉS: Pasa objetos RetrievalResult completos
retrieval_results = self._retrieve_phase_detailed(request)

# ANTES: No pasaba retrieval_results
explanations = self.explainer.generate_full_report(
    proposed_menus, rejected_cases, request
)

# DESPUÉS: Pasa retrieval_results para explicabilidad
explanations = self.explainer.generate_full_report(
    proposed_menus, rejected_cases, request,
    retrieval_results=retrieval_results  # ← Información completa
)
```

## 📊 Resultados

### Antes vs Después

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| **Prints incondicionales** | 19 prints | 0 prints |
| **Longitud explicación** | ~200 palabras | ~1000+ palabras |
| **Desglose RETRIEVE** | ❌ No | ✅ Sí (9 criterios) |
| **Detalles ADAPT** | ❌ Solo count | ✅ Lista completa |
| **Validación REVISE** | ❌ Solo status | ✅ Score + warnings |
| **Casos rechazados** | ❌ Razón genérica | ✅ Razones específicas |
| **Barras de progreso** | ❌ No | ✅ Sí (visual) |

### Tests Formales

```bash
$ python run_tests_silent.py

Total: 7
Successful: 7
Failed: 0

✅ Sin emojis inesperados
✅ Sin prints incondicionales
✅ Explicaciones completas generadas
```

## 🎓 Explicabilidad para Informe Académico

El sistema ahora proporciona **transparencia completa** del razonamiento CBR:

1. **RETRIEVE Transparency**
   - Desglose de similitud por 9 criterios (event, price, season, style, cultural, dietary, guests, wine, success_bonus)
   - Visualización con barras de progreso
   - Top 5 casos considerados

2. **ADAPT Transparency**
   - Lista completa de adaptaciones realizadas
   - Cambios de precio, ingredientes, temperatura, estilo
   - Justificación de cada adaptación

3. **REVISE Transparency**
   - Estado de validación (VALID/VALID_WITH_WARNINGS/INVALID)
   - Puntuación de calidad (0-100%)
   - Warnings específicos con sugerencias
   - Explicaciones de validación detalladas

4. **RETAIN Transparency** (futuro)
   - Decisión de retención (sí/no)
   - Razones de retención/descarte
   - Mantenimiento de la base de casos

## 📚 Uso

```python
from develop import ChefDigitalCBR, CBRConfig, Request, EventType, Season

config = CBRConfig(verbose=False, max_proposals=3)
cbr = ChefDigitalCBR(config)

request = Request(
    event_type=EventType.WEDDING,
    num_guests=100,
    price_max=60.0,
    season=Season.SUMMER
)

result = cbr.process_request(request)

# Explicación completa con desglose de RETRIEVE/ADAPT/REVISE
print(result.explanations)
```

## ✨ Beneficios

1. **Académicamente Riguroso**: Explicabilidad completa para XAI (Explainable AI)
2. **Mantenible**: Explicaciones centralizadas en un solo módulo
3. **Debuggable**: Sin prints dispersos, toda la información estructurada
4. **Profesional**: Output limpio y formateado
5. **Transparente**: Usuario/investigador puede ver TODO el razonamiento CBR

---

**Autor**: Sistema CBR Chef Digital  
**Fecha**: 2026-01-05  
**Versión**: 2.0 - Explicabilidad Completa
