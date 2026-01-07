# Solución Real: Todas las Adaptaciones Respetan Restricciones Críticas

## El Problema Verdadero

No es un problema de **ORDEN**, es un problema de **COORDINACIÓN**.

### Situación Actual (ROTA):

```python
# 1. _adapt_for_diets() adapta ingredientes
menu.starter = "Pan Integral" (honey→agave, ahora es vegan)

# 2. _adapt_for_price() busca alternativas más baratas
alternatives = get_dishes_by_type(STARTER)
cheaper = [d for d in alternatives if d.price < current.price]
# ❌ NO FILTRA POR VEGAN - puede elegir "Pan con Leche" (más barato pero NO vegan)
menu.starter = "Pan con Leche"  # ← SE PERDIÓ LA ADAPTACIÓN DIETÉTICA
```

**Resultado:** El menú final NO cumple las restricciones dietéticas.

---

## La Solución Real

### Principio: **Restricciones Críticas = Filtros Globales**

Las restricciones dietéticas y alergias son **CRÍTICAS** (no negociables).
Por tanto, TODAS las adaptaciones que cambien platos DEBEN respetarlas.

### Arquitectura Correcta:

```python
def _adapt_case(self, case, request, original_similarity):
    # Extraer restricciones críticas
    required_diets = request.required_diets
    restricted_ingredients = request.restricted_ingredients
    
    # 1. Adaptar restricciones dietéticas (ingredientes cuando sea posible)
    diet_ok, diet_adaptations = self._adapt_for_diets(
        adapted_menu, required_diets
    )
    if not diet_ok:
        return None  # Caso no adaptable
    
    # 2. Adaptar precio (RESPETANDO dietas)
    price_adaptations = self._adapt_for_price(
        adapted_menu, 
        request.price_min, 
        request.price_max,
        required_diets=required_diets,  # ← NUEVO
        restricted_ingredients=restricted_ingredients  # ← NUEVO
    )
    
    # 3. Adaptar temporada (RESPETANDO dietas)
    season_adaptations = self._adapt_for_season(
        adapted_menu, 
        request.season,
        required_diets=required_diets,  # ← NUEVO
        restricted_ingredients=restricted_ingredients  # ← NUEVO
    )
    
    # 4. Adaptar cultura (RESPETANDO dietas)
    cultural_adaptations = self._adapt_for_culture(
        adapted_menu,
        case.menu.cultural_theme,
        request.cultural_preference,
        request,  # Ya tiene required_diets dentro
        required_diets=required_diets,  # ← EXPLÍCITO
        restricted_ingredients=restricted_ingredients  # ← EXPLÍCITO
    )
    
    # 5. Adaptar estilo (RESPETANDO dietas)
    style_adaptations = self._adapt_style(
        adapted_menu,
        request,  # Ya tiene required_diets dentro
        required_diets=required_diets,  # ← EXPLÍCITO
        restricted_ingredients=restricted_ingredients  # ← EXPLÍCITO
    )
    
    # ... validación, etc.
```

---

## Cambios Necesarios en Cada Función

### 1. `_adapt_for_diets()` - SIN CAMBIOS en la lógica

Ya hace lo correcto:
- Intenta adaptar ingredientes primero
- Si falla, busca plato alternativo (NUEVO)
- Solo rechaza si nada funciona

### 2. `_adapt_for_price()` - FILTRAR por dietas

**ANTES:**
```python
def _reduce_price(self, menu: Menu, amount: float) -> List[str]:
    alternatives = self.case_base.get_dishes_by_type(dish.dish_type)
    cheaper = [d for d in alternatives if d.price < dish.price]
    # ❌ NO FILTRA POR DIETAS
```

**DESPUÉS:**
```python
def _reduce_price(self, menu: Menu, amount: float, 
                  required_diets: List[str] = None,
                  restricted_ingredients: List[str] = None) -> List[str]:
    
    alternatives = self.case_base.get_dishes_by_type(dish.dish_type)
    
    # FILTRAR por restricciones críticas
    if required_diets:
        alternatives = [d for d in alternatives 
                        if all(diet in d.diets for diet in required_diets)]
    
    if restricted_ingredients:
        alternatives = [d for d in alternatives 
                        if not any(ing in d.ingredients 
                                   for ing in restricted_ingredients)]
    
    cheaper = [d for d in alternatives if d.price < dish.price]
    # ✅ AHORA solo considera platos compatibles con dietas
```

### 3. `_adapt_for_season()` - FILTRAR por dietas

**ANTES:**
```python
def _adapt_for_season(self, menu: Menu, season: Season) -> List[str]:
    candidates = self.case_base.get_dishes_by_type(DishType.STARTER)
    appropriate = [d for d in candidates if ...]
    # ❌ NO FILTRA POR DIETAS
```

**DESPUÉS:**
```python
def _adapt_for_season(self, menu: Menu, season: Season,
                      required_diets: List[str] = None,
                      restricted_ingredients: List[str] = None) -> List[str]:
    
    candidates = self.case_base.get_dishes_by_type(DishType.STARTER)
    
    # FILTRAR por restricciones críticas PRIMERO
    if required_diets:
        candidates = [d for d in candidates 
                      if all(diet in d.diets for diet in required_diets)]
    
    if restricted_ingredients:
        candidates = [d for d in candidates 
                      if not any(ing in d.ingredients 
                                 for ing in restricted_ingredients)]
    
    appropriate = [d for d in candidates if ...]
    # ✅ AHORA solo considera platos compatibles
```

### 4. `_adapt_for_culture()` - FILTRAR por dietas

**ANTES:**
```python
def _adapt_for_culture(self, menu, original_culture, target_culture, request):
    replacement_dish = self._find_cultural_dish_replacement(
        dish, target_culture, menu, request
    )
    # _find_cultural_dish_replacement NO filtra por dietas
```

**DESPUÉS:**
```python
def _find_cultural_dish_replacement(self, original_dish, target_culture, 
                                    current_menu, request,
                                    required_diets: List[str] = None,
                                    restricted_ingredients: List[str] = None):
    
    candidates = self.case_base.get_dishes_by_type(original_dish.dish_type)
    
    # FILTRAR por restricciones críticas
    if required_diets:
        candidates = [d for d in candidates 
                      if all(diet in d.diets for diet in required_diets)]
    
    if restricted_ingredients:
        candidates = [d for d in candidates 
                      if not any(ing in d.ingredients 
                                 for ing in restricted_ingredients)]
    
    # Filtrar por temporada
    if request.season != Season.ALL:
        candidates = [d for d in candidates 
                      if d.is_available_in_season(request.season)]
    
    # ... resto de la lógica de scoring cultural ...
```

### 5. `_adapt_style()` - FILTRAR por dietas

Similar a los anteriores.

---

## Ventajas de esta Solución

### ✅ 1. Orden No Importa
```
_adapt_for_diets()  → Adapta a vegan
_adapt_for_price()  → Busca más barato PERO solo entre veganos
_adapt_for_season() → Busca temperatura PERO solo entre veganos

Resultado: Menú final ES vegan y cumple todo lo demás
```

### ✅ 2. No Necesita Re-validación
Las restricciones críticas se respetan en CADA paso.
No hay forma de que se "deshagan".

### ✅ 3. Más Menús Recuperados
Antes:
- Caso con pan no-vegano → Rechazado (no se puede adaptar ingredientes)

Después:
- _adapt_for_diets() busca pan vegano alternativo → Éxito
- _adapt_for_price() busca más barato entre veganos → Éxito
- Resultado: 1 menú propuesto ✅

### ✅ 4. Coherencia Total
```
request.required_diets = ['vegan', 'gluten-free']

TODAS las adaptaciones:
- Solo consideran platos vegan + gluten-free
- Nunca rompen estas restricciones
- Menú final GARANTIZADO cumple ambas
```

---

## Implementación Paso a Paso

### Paso 1: Modificar `_adapt_for_diets()` para que cambie platos

Añadir nivel 2 (buscar plato alternativo) cuando ingredientes no funcionan.

### Paso 2: Añadir parámetros a funciones auxiliares

```python
def _reduce_price(self, menu, amount, required_diets=None, restricted_ingredients=None)
def _increase_price(self, menu, amount, required_diets=None, restricted_ingredients=None)
def _adapt_for_season(self, menu, season, required_diets=None, restricted_ingredients=None)
def _find_cultural_dish_replacement(self, ..., required_diets=None, restricted_ingredients=None)
def _adapt_style(self, menu, request, required_diets=None, restricted_ingredients=None)
```

### Paso 3: Añadir filtros en cada función

Antes de seleccionar platos alternativos:
```python
if required_diets:
    candidates = [d for d in candidates 
                  if all(diet in d.diets for diet in required_diets)]

if restricted_ingredients:
    candidates = [d for d in candidates 
                  if not any(ing in d.ingredients 
                             for ing in restricted_ingredients)]
```

### Paso 4: Actualizar `_adapt_case()` para pasar parámetros

Pasar `required_diets` y `restricted_ingredients` a TODAS las funciones.

### Paso 5: Testing

```python
# Test 1: Vegan + bajo presupuesto
request = Request(required_diets=['vegan'], price_min=10, price_max=15)
# Debe encontrar platos veganos baratos

# Test 2: Gluten-free + verano
request = Request(required_diets=['gluten-free'], season=Season.SUMMER)
# Starter debe ser: sin gluten + temperatura fría

# Test 3: Vegan + cultura italiana
request = Request(required_diets=['vegan'], cultural_preference=CulturalTradition.ITALIAN)
# Platos deben ser: veganos + ingredientes italianos
```

---

## Comparación con Otras Opciones

| Enfoque | Orden Importa | Re-validación | Garantía | Complejidad |
|---------|---------------|---------------|----------|-------------|
| **Opción A** (dietas cambia platos) | ✅ Sí, al final | ❌ No | ❌ Baja | Baja |
| **Opción B** (dietas al final) | ✅ Sí, crítico | ❌ No | ⚠️ Media | Media |
| **Opción C** (doble validación) | ⚠️ Algo | ✅ Sí | ✅ Alta | Alta |
| **SOLUCIÓN REAL** (filtros globales) | ❌ No | ❌ No | ✅ Total | Media |

**SOLUCIÓN REAL es superior porque:**
- ❌ Orden NO importa (más robusto)
- ❌ No necesita re-validación (más eficiente)
- ✅ Garantía total (más seguro)
- ⚠️ Complejidad media (aceptable)

---

## Diagrama de Flujo

```
┌─────────────────────────────────────────────────────┐
│ request.required_diets = ['vegan']                  │
│ request.restricted_ingredients = ['peanuts']        │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ _adapt_for_diets()        │
        │ • Adapta ingredientes     │
        │ • O busca plato vegan     │
        └───────────┬───────────────┘
                    │ Menu con platos veganos
                    ▼
        ┌───────────────────────────┐
        │ _adapt_for_price()        │
        │ FILTRO: solo veganos      │◄── required_diets
        │ FILTRO: sin peanuts       │◄── restricted_ingredients
        └───────────┬───────────────┘
                    │ Menu vegano + precio OK
                    ▼
        ┌───────────────────────────┐
        │ _adapt_for_season()       │
        │ FILTRO: solo veganos      │◄── required_diets
        │ FILTRO: sin peanuts       │◄── restricted_ingredients
        └───────────┬───────────────┘
                    │ Menu vegano + temporada OK
                    ▼
        ┌───────────────────────────┐
        │ _adapt_for_culture()      │
        │ FILTRO: solo veganos      │◄── required_diets
        │ FILTRO: sin peanuts       │◄── restricted_ingredients
        └───────────┬───────────────┘
                    │ Menu vegano + cultura OK
                    ▼
        ┌───────────────────────────┐
        │ _adapt_style()            │
        │ FILTRO: solo veganos      │◄── required_diets
        │ FILTRO: sin peanuts       │◄── restricted_ingredients
        └───────────┬───────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ RESULTADO FINAL:          │
        │ ✅ Vegano                 │
        │ ✅ Sin peanuts            │
        │ ✅ Precio correcto        │
        │ ✅ Temporada apropiada    │
        │ ✅ Cultura apropiada      │
        │ ✅ Estilo apropiado       │
        └───────────────────────────┘
```

**CLAVE:** Las restricciones críticas se aplican como **filtros transversales** en TODAS las adaptaciones.
No importa el orden - siempre se respetan.
