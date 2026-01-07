# ANÁLISIS: Por qué con restricciones dietéticas no se recuperan menús

## Resumen Ejecutivo

**PROBLEMA:** Cuando se solicita un menú con restricción vegan (o similar), el sistema NO propone ningún menú válido, todos son rechazados.

**CAUSA RAÍZ:** Incompatibilidad arquitectónica entre RETRIEVE y ADAPT.

---

## Flujo Actual del Sistema

### 1. FASE RETRIEVE
```
Input: Request con required_diets=['vegan']
Acción: Recupera casos por SIMILITUD GENERAL
Output: 8 casos con similitud 62-66%
```

**PROBLEMA:** RETRIEVE NO filtra por dietas compatibles, solo por similitud de:
- Tipo de evento
- Rango de precio
- Temporada
- Estilo culinario

**Resultado:** Recupera menús con:
- Caso 1: honey (miel), eggs, parmesan cheese
- Caso 2: milk, eggs, butter
- Caso 3: chicken breasts, bacon, cheese

### 2. FASE ADAPT
```
Input: Menús NO veganos
Acción: _adapt_for_diets() intenta sustituir ingredientes
Restricción: Solo sustituye dentro del MISMO GRUPO
Output: None (falla la adaptación)
```

**Regla del sistema:**
```python
# ingredient_adapter.py línea 322
# SOLO buscar en el mismo grupo (mantener coherencia gastronómica)
if ingredient in self.ingredient_to_group:
    group_name = self.ingredient_to_group[ingredient]
    group_ingredients = self.groups[group_name]
    
    compliant_matches = [
        ing for ing in group_ingredients
        if ing != ingredient and all(not self.violates_dietary_restriction(ing, label) for label in dietary_labels)
    ]
```

**Ejemplos de sustituciones IMPOSIBLES:**

| Ingrediente | Grupo | Problema |
|-------------|-------|----------|
| honey | liquid_sweetener_group | NO hay miel vegan en el grupo |
| milk | milk_group | Almond milk está, PERO el plato usa milk por sabor específico |
| eggs | (sin grupo definido) | NO tiene grupo → no se puede sustituir |
| chicken breasts | (sin grupo definido) | NO tiene grupo → no se puede sustituir |
| cheese | cheese_group | Hay quesos veganos? NO en el JSON |
| butter | butter_group | Margarine existe pero también non-compliant vegan |

### 3. FASE REVISE
```
Input: (NUNCA LLEGA NADA - ADAPT descartó todo)
Output: 0 menús propuestos, 8 rechazados
```

---

## Análisis Detallado del JSON ingredients.json

### Grupos de ingredientes con sustitutos veganos:

#### ✓ milk_group
```json
{
  "milk_group": [
    "milk",           // ❌ non-compliant: vegan
    "yogurt",         // ❌ non-compliant: vegan
    "sour cream",     // ❌ non-compliant: vegan
    "heavy cream",    // ❌ non-compliant: vegan
    "buttermilk",     // ❌ non-compliant: vegan
    "almond milk",    // ✓ vegan compliant
    "coconut milk",   // ✓ vegan compliant
    "soy milk"        // ✓ vegan compliant
  ]
}
```
**RESULTADO:** **SÍ** hay sustitutos veganos en este grupo ✓

#### ❌ liquid_sweetener_group
```json
{
  "liquid_sweetener_group": [
    "honey",          // ❌ non-compliant: vegan (miel de abejas)
    "maple syrup",    // ❌ non-compliant: vegan
    "molasses",       // ❌ non-compliant: vegan
    "agave",          // ❌ non-compliant: vegan
    "corn syrup"      // ❌ non-compliant: vegan
  ]
}
```
**RESULTADO:** **NO** hay sustitutos veganos en este grupo ✗

#### ❌ butter_group
```json
{
  "butter_group": [
    "butter",         // ❌ non-compliant: vegan
    "margarine",      // ❌ non-compliant: vegan
    "shortening"      // ❌ non-compliant: vegan
  ]
}
```
**RESULTADO:** **NO** hay sustitutos veganos (margarine también está marcada como non-vegan) ✗

#### ❌ Ingredientes SIN GRUPO
- **eggs**: No tiene grupo → imposible sustituir
- **chicken breasts**: No tiene grupo → imposible sustituir
- **bacon**: No tiene grupo → imposible sustituir
- **cheese**: Probablemente en cheese_group, pero sin sustitutos veganos

---

## Soluciones Propuestas

### Solución A: RETRIEVE debe filtrar por dietas (RÁPIDA) ⭐

**Cambio en:** `develop/cycle/retrieve.py`

```python
def retrieve(self, request: Request, k: int = 10) -> List[RetrievalResult]:
    # ANTES DE calcular similitud, filtrar casos incompatibles
    
    if request.required_diets:
        compatible_cases = []
        for case in self.case_base.cases:
            # Verificar que TODOS los platos del menú cumplan las dietas
            menu = case.menu
            if self._menu_satisfies_diets(menu, request.required_diets):
                compatible_cases.append(case)
        
        # Trabajar solo con casos compatibles
        cases_to_rank = compatible_cases
    else:
        cases_to_rank = self.case_base.cases
    
    # Calcular similitud solo sobre casos compatibles
    ...
```

**Ventajas:**
- Solución simple y rápida
- Garantiza que ADAPT recibe menús ya compatibles
- No requiere cambios en ADAPT

**Desventajas:**
- Si NO hay casos veganos en la base, retornará 0 resultados
- Reduce la reutilización de conocimiento previo

---

### Solución B: ADAPT debe sustituir PLATOS completos (COMPLETA)

**Cambio en:** `develop/cycle/adapt.py`

```python
def _adapt_for_diets(self, menu: Menu, required_diets: List[str]):
    # Si un plato no puede adaptarse por ingredientes...
    if not substitutions_made:
        # BUSCAR PLATO ALTERNATIVO del mismo tipo que cumpla dietas
        alternative_dish = self._find_diet_compatible_dish(
            dish_type=dish.dish_type,
            required_diets=required_diets,
            current_dish_similarity=dish  # Para mantener similitud
        )
        
        if alternative_dish:
            setattr(menu, dish_attr, alternative_dish)
            adaptations.append(f"Sustituido PLATO {dish.name} → {alternative_dish.name} (cumple {diets})")
        else:
            return False  # No se puede adaptar ni ingredientes ni plato
```

**Ventajas:**
- Mayor reutilización del conocimiento
- Puede adaptar casos NO veganos a veganos
- Más flexible y potente

**Desventajas:**
- Más complejo de implementar
- Puede reducir mucho la similitud del menú adaptado
- Requiere calcular dish_similarity para encontrar el mejor reemplazo

---

### Solución C: HÍBRIDA (ÓPTIMA) ⭐⭐⭐

**Combinar ambas:**

1. **RETRIEVE:** Priorizar casos con platos compatibles (peso alto en similitud)
2. **ADAPT:** 
   - Intentar sustitución de ingredientes primero (mantiene plato)
   - Si falla, intentar sustitución de plato completo (mantiene tipo)
   - Si falla, descartar caso

```python
# retrieve.py
def _calculate_similarity(case, request):
    # ...código actual...
    
    # BONUS si cumple dietas (priorizar casos compatibles)
    if request.required_diets:
        menu = case.menu
        if self._menu_satisfies_diets(menu, request.required_diets):
            similarity += 0.15  # Bonus 15% por cumplir dietas
    
    return similarity

# adapt.py
def _adapt_for_diets(self, menu, required_diets):
    # 1. Intentar sustituir ingredientes (ACTUAL)
    if substitutions_made:
        return True, adaptations
    
    # 2. Intentar sustituir plato completo (NUEVO)
    alternative = self._find_compatible_dish(dish, required_diets)
    if alternative:
        setattr(menu, dish_attr, alternative)
        return True, [f"Sustituido plato {dish.name} → {alternative.name}"]
    
    # 3. No se puede adaptar
    return False, adaptations
```

**Ventajas:**
- Lo mejor de ambos mundos
- RETRIEVE encuentra casos más adecuados
- ADAPT puede trabajar con casos menos adecuados
- Balance entre similitud y adaptabilidad

---

## Recomendación Final

**IMPLEMENTAR SOLUCIÓN C (HÍBRIDA)**

**Razón:** El CBR se trata de **REUTILIZAR conocimiento previo**. Si solo filtramos en RETRIEVE (Solución A), perdemos casos valiosos. Si solo mejoramos ADAPT (Solución B), seguimos desperdiciando tiempo adaptando casos malos.

**La combinación:**
1. RETRIEVE prioriza casos ya compatibles (+15% bonus)
2. ADAPT puede adaptar casos menos compatibles si es necesario
3. Balance óptimo entre eficiencia y reutilización

---

## Impacto Estimado

### Situación Actual:
- Request vegan → 0 menús propuestos
- Request gluten-free → probablemente 0 menús
- Request vegetarian → puede que 1-2 menús

### Con Solución C:
- Request vegan → 3-5 menús propuestos
- Request gluten-free → 3-5 menús propuestos
- Request vegetarian → 3-5 menús propuestos

**Mejora estimada:** De 0% éxito a 80-100% éxito en requests con dietas
