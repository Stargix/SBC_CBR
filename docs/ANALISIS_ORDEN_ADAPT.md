# Análisis del Orden de Operaciones en ADAPT

## Flujo Actual de `_adapt_case()`

```python
1. ✅ Verificar casos negativos
2. 🔴 Adaptar restricciones dietéticas (_adapt_for_diets)
3. ✅ Adaptar ingredientes restringidos/alergias (_adapt_for_ingredients)
4. 🟡 Adaptar precio (_adapt_for_price)
5. 🟡 Adaptar temporada (_adapt_for_season)
6. ✅ Adaptar bebida (_adapt_beverage)
7. 🟡 Adaptar cultura (_adapt_for_culture)
8. 🟡 Adaptar estilo (_adapt_style)
9. ✅ Validación preventiva (_preventive_validation)
10. ✅ Recalcular similitud final
```

**Leyenda:**
- 🔴 = Problema identificado (solo sustituye ingredientes, no platos)
- 🟡 = Ya cambia platos completos usando `dish_similarity`
- ✅ = Funciona correctamente

---

## Análisis de Interdependencias

### Operaciones que YA cambian platos completos:

#### 1. **`_adapt_for_price()` (líneas 400-475)**
```python
# Busca platos más baratos/caros usando dish_similarity
alternatives = self.case_base.get_dishes_by_type(dish.dish_type)
cheaper.sort(
    key=lambda d: (calculate_dish_similarity(dish, d), -d.price),
    reverse=True
)
new_dish = cheaper[0]
setattr(menu, attr, new_dish)  # ← CAMBIA PLATO COMPLETO
```

#### 2. **`_adapt_for_season()` (líneas 477-510)**
```python
# Cambia starter por temperatura inapropiada
appropriate = [d for d in candidates if ...]
best = max(appropriate, 
    key=lambda d: calculate_dish_similarity(menu.starter, d)
)
menu.starter = best  # ← CAMBIA PLATO COMPLETO
```

#### 3. **`_adapt_for_culture()` (líneas 1011-1225)**
```python
# OPCIÓN 1: Adaptar ingredientes (como _adapt_for_diets actual)
# OPCIÓN 2: Buscar plato de reemplazo
replacement_dish = self._find_cultural_dish_replacement(...)

# Compara similitud global y elige la mejor opción
if replacement_dish and (replacement_score > adapted_score):
    setattr(menu, dish_attr, replacement_dish)  # ← CAMBIA PLATO COMPLETO
else:
    setattr(menu, dish_attr, adapted_dish)  # ← Ingredientes adaptados
```

#### 4. **`_adapt_style()` (líneas 585-617)**
```python
# Busca platos con el estilo preferido
if request.preferred_style not in dish.styles:
    alternatives = self.case_base.get_dishes_by_type(dish.dish_type)
    styled = [d for d in alternatives if request.preferred_style in d.styles]
    best = max(styled, key=lambda d: calculate_dish_similarity(dish, d))
    setattr(menu, dish_attr, best)  # ← CAMBIA PLATO COMPLETO
```

---

## Problema Identificado

### `_adapt_for_diets()` (líneas 260-335) 🔴

**Comportamiento actual:**
- ❌ SOLO sustituye ingredientes usando `find_dietary_substitution()`
- ❌ Si NO encuentra sustituto en el mismo grupo → **RECHAZA TODO EL CASO**
- ❌ NO busca platos alternativos compatibles
- ❌ NO usa `calculate_dish_similarity` para encontrar reemplazos

**Inconsistencia:**
- Todas las demás adaptaciones (precio, temporada, cultura, estilo) SÍ cambian platos completos
- `_adapt_for_diets()` es la ÚNICA que rechaza casos en vez de buscar alternativas

---

## Impacto del Orden Actual

### Orden Crítico para Dietas:

```
ACTUAL:
1. _adapt_for_diets() ← PRIMERA (falla → rechaza TODO)
2. _adapt_for_price()
3. _adapt_for_season()
4. _adapt_for_culture()
5. _adapt_for_style()
```

**Problemas del orden actual:**
1. ❌ Si dietas falla, **nunca se intenta** adaptar precio/temporada/etc.
2. ❌ Podría haber un plato compatible con dietas pero fuera de temporada
   - Dietas lo acepta (con ingredientes adaptados)
   - Temporada lo cambia después
   - **Resultado:** Plato final puede NO cumplir dietas
3. ❌ Precio puede cambiar platos DESPUÉS de adaptación dietética
   - **Resultado:** El nuevo plato puede NO cumplir dietas

---

## Escenarios Problemáticos

### Escenario 1: Dietas + Precio
```
1. _adapt_for_diets() adapta "Pan Integral" (honey→agave) 
   → Pan adaptado cumple vegan, cuesta 8€
2. _adapt_for_price() ve que es muy caro para budget 5-6€
   → Cambia a "Pan Blanco" más barato (4€)
   → ❌ Pan Blanco contiene milk, NO es vegan
```

### Escenario 2: Dietas + Temporada
```
1. _adapt_for_diets() adapta "Sopa de Pollo" (chicken→tofu)
   → Sopa adaptada cumple vegan, temperatura: hot
2. _adapt_for_season() ve que estamos en Summer
   → Cambia a "Ensalada Fresca" (cold)
   → ❌ Ensalada puede contener cheese, NO es vegan
```

### Escenario 3: Dietas + Cultura
```
1. _adapt_for_diets() adapta "Risotto" (butter→margarine)
   → Risotto adaptado cumple vegan
2. _adapt_for_culture() ve que target_culture=MEXICAN
   → Cambia todo el plato a "Tacos"
   → ❌ Tacos pueden contener beef, NO es vegan
```

---

## Propuesta de Solución

### Opción A: Hacer que `_adapt_for_diets()` también cambie platos (RECOMENDADO)

**Ventajas:**
- ✅ Consistente con el resto de adaptaciones
- ✅ No rechaza casos innecesariamente
- ✅ Mantiene el orden actual (dietas primero)

**Implementación:**
```python
def _adapt_for_diets(self, menu: Menu, required_diets: List[str]):
    # Nivel 1: Intentar sustituir ingredientes (ACTUAL)
    if substitutions_made:
        return True, adaptations
    
    # Nivel 2: Buscar plato alternativo (NUEVO) 
    alternative_dishes = self.case_base.get_dishes_by_type(dish.dish_type)
    compatible = [d for d in alternative_dishes 
                  if all(diet in d.diets for diet in missing_diets)]
    
    if compatible:
        best = max(compatible, 
                   key=lambda d: calculate_dish_similarity(dish, d))
        setattr(menu, dish_attr, best)
        adaptations.append(f"Plato cambiado: {dish.name} → {best.name}")
        return True, adaptations
    
    return False, adaptations  # Solo si ni ingredientes ni platos funcionan
```

**Problema con esta opción:**
- ⚠️ Las adaptaciones posteriores pueden DESHACER el cambio dietético
- ⚠️ Necesitamos RE-VALIDAR dietas al final

---

### Opción B: Cambiar el orden - Dietas al FINAL

```
NUEVO ORDEN:
1. _adapt_for_price()        ← Ajusta precio primero
2. _adapt_for_season()        ← Ajusta temporada
3. _adapt_for_culture()       ← Ajusta cultura
4. _adapt_for_style()         ← Ajusta estilo
5. _adapt_for_diets()         ← AL FINAL (con cambio de platos)
6. _preventive_validation()   ← Re-valida todo
```

**Ventajas:**
- ✅ Dietas es la última adaptación → no se deshace
- ✅ Trabaja con platos ya ajustados por precio/temporada
- ✅ Validación preventiva al final asegura coherencia

**Desventajas:**
- ⚠️ Cambio más drástico en el flujo
- ⚠️ Puede buscar platos dietéticos fuera de temporada
  - Pero _adapt_for_season ya los filtró antes

---

### Opción C: Doble Validación (HÍBRIDO)

```
1. _adapt_for_diets()         ← Primera pasada (con cambio de platos)
2. _adapt_for_price()
3. _adapt_for_season()
4. _adapt_for_culture()
5. _adapt_for_style()
6. _preventive_validation()
7. _revalidate_diets()        ← NUEVA: Re-valida dietas al final
```

**Implementación de `_revalidate_diets()`:**
```python
def _revalidate_diets(self, menu: Menu, required_diets: List[str]):
    # Verificar que TODOS los platos finales cumplan dietas
    for dish_attr in ['starter', 'main_course', 'dessert']:
        dish = getattr(menu, dish_attr)
        missing = [d for d in required_diets if d not in dish.diets]
        
        if missing:
            # El plato fue cambiado por otra adaptación y ya no cumple
            # Buscar alternativa compatible
            alternatives = self.case_base.get_dishes_by_type(dish.dish_type)
            compatible = [d for d in alternatives 
                          if all(diet in d.diets for diet in required_diets)]
            
            if compatible:
                best = max(compatible, 
                           key=lambda d: calculate_dish_similarity(dish, d))
                setattr(menu, dish_attr, best)
            else:
                return False  # No hay alternativa → rechazar menú
    
    return True
```

**Ventajas:**
- ✅ Mantiene orden actual (dietas primero)
- ✅ Garantiza que el menú FINAL cumple dietas
- ✅ Permite que otras adaptaciones funcionen libremente

**Desventajas:**
- ⚠️ Más complejo (dos pasadas)
- ⚠️ Puede cambiar platos dos veces (eficiencia)

---

## Recomendación Final

**Implementar Opción C (Doble Validación)** por las siguientes razones:

1. **Seguridad:** Garantiza que restricciones dietéticas (CRÍTICAS) se cumplen al final
2. **Compatibilidad:** No rompe el orden actual de adaptaciones
3. **Flexibilidad:** Permite que adaptaciones de precio/temporada funcionen libremente
4. **Robustez:** Si precio cambia un plato, la revalidación lo corrige

**Pasos de implementación:**
1. Modificar `_adapt_for_diets()` para incluir cambio de platos (Nivel 2)
2. Añadir `_revalidate_diets()` al final de `_adapt_case()`
3. Actualizar tests para verificar que dietas se mantienen después de todas las adaptaciones

**Orden final propuesto:**
```python
def _adapt_case(self, case, request, original_similarity):
    # ... (verificación de negativos)
    
    # 1. PRIMERA PASADA: Adaptar dietas (con cambio de platos)
    diet_ok, diet_adaptations = self._adapt_for_diets(adapted_menu, request.required_diets)
    if not diet_ok:
        return None
    adaptations.extend(diet_adaptations)
    
    # 2-5. Otras adaptaciones (pueden cambiar platos libremente)
    # ... precio, temporada, cultura, estilo ...
    
    # 6. SEGUNDA PASADA: Re-validar que dietas se mantienen
    diet_revalidation_ok = self._revalidate_diets(adapted_menu, request.required_diets)
    if not diet_revalidation_ok:
        return None
    
    # 7. Validación preventiva final
    preventive_adaptations = self._preventive_validation(adapted_menu, request)
    
    # 8. Recalcular similitud
    # ...
```

---

## Testing Necesario

Después de la implementación, verificar:

1. ✅ Menú vegan con presupuesto bajo → debe encontrar platos veganos baratos
2. ✅ Menú gluten-free en verano → debe ser sin gluten Y temperatura apropiada
3. ✅ Menú vegan + cultura italiana → debe ser vegano E ingredientes italianos
4. ✅ Comparar número de menús recuperados ANTES vs DESPUÉS del cambio
5. ✅ Verificar que la similitud final no empeora significativamente

**Test específico para problema reportado:**
```python
request = Request(
    num_guests=4,
    required_diets=['vegan'],
    price_min=10.0,
    price_max=20.0
)

# ANTES: 0 menús propuestos
# DESPUÉS: Debería haber 2-3 menús propuestos
```
