# Adaptación Dietética de Ingredientes

## 📋 Resumen

Sistema de adaptación granular de ingredientes para cumplir restricciones dietéticas en el ciclo CBR de planificación de menús.

## 🎯 Problema Resuelto

**ANTES:**
- Si un plato tenía 1 ingrediente que violaba una restricción dietética (ej: gluten-free), el plato COMPLETO era rechazado
- Se perdían buenos candidatos por detalles menores
- Baja flexibilidad en la adaptación

**AHORA:**
- El sistema identifica ingredientes específicos que violan restricciones
- Busca sustitutos apropiados solo para esos ingredientes
- Mantiene el resto del plato intacto
- Mayor flexibilidad y aprovechamiento de la base de casos

## 🔧 Implementación

### 1. Estructura de Datos (`ingredients.json`)

Cada ingrediente declara qué restricciones dietéticas **VIOLA**:

```json
{
  "all-purpose flour": {
    "non_compliant_labels": ["wheat-free", "gluten-free"],
    "cultures": ["Universal"]
  },
  "butter": {
    "non_compliant_labels": ["vegan", "dairy-free", "paleo", "fodmap-free"],
    "cultures": ["European", "Universal"]
  }
}
```

### 2. Nuevos Métodos (`ingredient_adapter.py`)

#### `violates_dietary_restriction(ingredient, label) -> bool`
Verifica si un ingrediente viola una restricción dietética.

```python
adapter.violates_dietary_restriction("butter", "vegan")  # True
adapter.violates_dietary_restriction("olive oil", "vegan")  # False
```

#### `get_compliant_ingredients(label) -> Set[str]`
Obtiene todos los ingredientes que cumplen una restricción.

```python
vegan_ingredients = adapter.get_compliant_ingredients("vegan")
# {'olive oil', 'tomato', 'rice', 'sugar', ...}
```

#### `find_dietary_substitution(ingredient, labels) -> IngredientSubstitution`
Busca un sustituto que cumpla TODAS las restricciones.

**Estrategia de búsqueda:**
1. **Mismo grupo + cumple restricciones** (90% confianza)
   - Busca en el grupo del ingrediente original
   - Ej: `all-purpose flour` → `almond flour` (ambos en `flour_group`)
   - Si no hay sustituto en el mismo grupo, **NO SUSTITUYE** (mantiene coherencia gastronómica)

**IMPORTANTE**: El sistema SOLO sustituye ingredientes del mismo grupo para preservar la coherencia del plato. Usar ingredientes de otros grupos (ej: `sugar` para `chicken`) arruinaría el plato.

```python
sub = adapter.find_dietary_substitution("all-purpose flour", ["gluten-free"])
# IngredientSubstitution(
#   original="all-purpose flour",
#   replacement="almond flour",
#   reason="Dietary: violates gluten-free, same group (flour_group)",
#   confidence=0.85
# )
```

### 3. Adaptación de Platos (`adapt.py`)

El método `_adapt_for_diets()` ahora **ADAPTA** en vez de solo validar:

**ANTES:**
```python
if diet not in dish.diets:
    return False  # ❌ Rechazar plato completo
```

**AHORA:**
```python
# Identificar ingredientes que violan la restricción
violating_ingredients = [
    ing for ing in dish.ingredients
    if adapter.violates_dietary_restriction(ing, diet)
]

# Intentar sustituir cada uno
for ing in violating_ingredients:
    sub = adapter.find_dietary_substitution(ing, [diet])
    if sub:
        dish.ingredients[idx] = sub.replacement
        adaptations.append(sub)

# Si se sustituyeron todos, el plato ahora cumple
if all substitutions successful:
    dish.diets.append(diet)
```

## 📊 Ejemplos de Uso

### Ejemplo 1: Gluten-Free

```python
# Input
dish.ingredients = ["chicken", "all-purpose flour", "tomato", "olive oil"]
diet_restriction = "gluten-free"

# Proceso
violating = ["all-purpose flour"]  # Solo 1 ingrediente viola
substitution = find_dietary_substitution("all-purpose flour", ["gluten-free"])
# → almond flour (85% confianza, mismo grupo)

# Output
dish.ingredients = ["chicken", "almond flour", "tomato", "olive oil"]
dish.diets = ["high-fiber", "gluten-free"]  # ✅ Ahora cumple
```

### Ejemplo 2: Vegan + Dairy-Free

```python
# Input
dish.ingredients = ["pasta", "butter", "garlic", "basil"]
diet_restrictions = ["vegan", "dairy-free"]

# Proceso
violating = ["butter"]  # Viola vegan Y dairy-free
substitution = find_dietary_substitution("butter", ["vegan", "dairy-free"])
# → olive oil (90% confianza, mismo grupo - fats_and_oils)

# Output
dish.ingredients = ["pasta", "olive oil", "garlic", "basil"]
dish.diets = ["vegetarian", "vegan", "dairy-free"]
```

### Ejemplo 3: No Adaptable (Sin Sustituto en Grupo)

```python
# Input
dish.ingredients = ["chicken", "rice", "vegetables"]
diet_restrictions = ["vegan"]

# Proceso
violating = ["chicken"]  # Viola vegan
substitution = find_dietary_substitution("chicken", ["vegan"])
# → None (no hay sustituto vegan en meat_and_poultry group)

# Output
# ❌ PLATO NO ADAPTABLE - Se descarta
# Mantener coherencia gastronómica es prioritario
```

## 🎯 Ventajas del Sistema

### 1. Adaptación Granular
- **Antes**: Rechaza plato completo si 1 ingrediente viola restricción
- **Ahora**: Sustituye solo el ingrediente problemático

### 2. Mayor Aprovechamiento de Casos
- **Antes**: Base de casos limitada (solo platos 100% compatibles)
- **Ahora**: Platos "casi compatibles" se pueden adaptar

### 3. Alta Confianza en Sustituciones
- Prioriza ingredientes del mismo grupo (mejor sabor/textura)
- Ej: harina → harina, aceite → aceite, no mezcla tipos

### 4. Mantiene Esencia del Plato
- Cambios mínimos necesarios
- Estructura y concepto del plato preservados

### 5. Múltiples Restricciones Simultáneas
- Soporta combinar varias restricciones
- Garantiza que el sustituto cumple TODAS

## 📈 Impacto en el Ciclo CBR

### RETRIEVE
- **Cambio**: Filtrado híbrido (críticas vs flexibles)
- **Antes**: Filtraba TODO en RETRIEVE
- **Ahora**: Solo filtra restricciones críticas (alergias), dietas flexibles

### ADAPT
- **Cambio**: Adaptación activa de ingredientes
- **Antes**: Solo validaba si cumple
- **Ahora**: Intenta adaptar ingredientes violadores

### REVISE
- **Cambio**: Recalculo de similitud post-adaptación
- **Antes**: Similitud solo de RETRIEVE
- **Ahora**: `original_similarity` + `final_similarity` (recalculada)

## 🧪 Demostración

### Demo 1: Sustitución de Ingredientes
```bash
python develop/demo_sustitucion_ingredientes.py
```

**Muestra:**
- Verificación de violaciones dietéticas
- Búsqueda de sustituciones
- Validación que sustituto cumple restricciones
- Múltiples restricciones simultáneas

### Demo 2: Menú Completo
```bash
python develop/demo_menu_completo.py
```

**Muestra:**
- Flujo completo RETRIEVE → ADAPT
- Análisis de ingredientes con gluten
- Adaptación granular del menú
- Estadísticas de mejora (0/3 → 1/3 platos GF)

### Demo 3: Adaptación Dietética (Integración)
```bash
python develop/demo_adaptacion_dietetica.py
```

**Muestra:**
- Integración con sistema CBR completo
- Request con restricción gluten-free
- Candidatos recuperados y análisis
- (Nota: puede fallar por similarities a failures previos)

## 🔍 Casos de Uso

### ✅ Funciona Bien
- **Gluten-free**: `all-purpose flour` → `almond flour` / `rice flour`
- **Vegan**: `butter` → `olive oil`, `chicken` → `tofu`
- **Dairy-free**: `milk` → `almond milk`, `cheese` → `nutritional yeast`
- **Combinaciones**: vegan + gluten-free, paleo + dairy-free

### ⚠️  Limitaciones
- **SOLO sustituye ingredientes del mismo grupo** (mantiene coherencia gastronómica)
- Si NO hay sustituto en el mismo grupo, el plato **NO se puede adaptar**
- Algunos ingredientes no tienen buenos sustitutos en su grupo (ej: huevo en repostería)
- Platos con ingredientes esenciales no adaptables serán descartados

## 📝 Archivos Modificados

### `cycle/ingredient_adapter.py`
- Añadido: `ingredient_non_compliant` (dict de ingrediente → restricciones violadas)
- Añadido: `violates_dietary_restriction()`
- Añadido: `get_compliant_ingredients()`
- Añadido: `find_dietary_substitution()`
- Modificado: `_build_culture_to_ingredients()` para cargar `non_compliant_labels`

### `cycle/adapt.py`
- Modificado: `_adapt_for_diets()` para adaptar ingredientes vs solo validar
- Añadido: Recalculo de similitud post-adaptación
- Modificado: `AdaptationResult` con `original_similarity` + `final_similarity`

### `config/ingredients.json`
- Añadido campo `non_compliant_labels` a TODOS los ingredientes
- Estructura: `{"ingredient": {"non_compliant_labels": [...], "cultures": [...]}}`

## 🚀 Próximos Pasos

### Mejoras Pendientes
1. **Scoring cultural con dietas**: `_find_cultural_dish_replacement()` considere `non_compliant_labels`
2. **Testing exhaustivo**: Crear tests unitarios para todos los casos
3. **Mejores sustitutos**: Ampliar grupos de ingredientes para mejor matching
4. **Confianza dinámica**: Ajustar confianza según contexto del plato

### Validaciones Pendientes
- Verificar que TODOS los ingredientes en `ingredients.json` tienen `non_compliant_labels`
- Validar sustituciones en casos reales con feedback de clientes
- Comparar resultados vs sistema anterior (métricas de éxito)

## 📚 Referencias

- [CICLO_CBR.md](CICLO_CBR.md) - Arquitectura del sistema CBR
- [MEJORAS_RETAIN.md](MEJORAS_RETAIN.md) - Mejoras en fase RETAIN
- `demo_recalculo_similitud.py` - Demo de similitud pre/post adaptación
