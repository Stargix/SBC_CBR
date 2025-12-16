# 🔄 Ciclo CBR - Explicación Completa

## Resumen del Sistema

El sistema utiliza **Case-Based Reasoning (Razonamiento Basado en Casos)**, que aprende de experiencias pasadas para resolver nuevos problemas.

## Las 4 Fases del Ciclo CBR

```
┌─────────────┐
│  SOLICITUD  │ (Cliente pide menú para boda, 100 personas, 80€, primavera)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. RETRIEVE (Recuperar)                                     │
│    Busca casos similares en la base de conocimiento         │
│    - Pre-filtrado: por evento, precio, temporada            │
│    - Cálculo de similitud: compara atributos                │
│    - Ranking: ordena por similitud                          │
│                                                              │
│    📊 Similitudes calculadas:                               │
│    • Caso #1: 93% similar (boda primavera, mismo estilo)   │
│    • Caso #2: 85% similar (boda otoño, similar precio)     │
│    • Caso #3: 78% similar (boda, diferente temporada)      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. REUSE/ADAPT (Reutilizar/Adaptar)                        │
│    Modifica los casos para que encajen con la solicitud     │
│                                                              │
│    🔧 Adaptaciones realizadas:                              │
│    • Dietas: Si piden vegetariano, cambiar plato de carne  │
│    • Precio: Ajustar platos para cumplir presupuesto       │
│    • Temporada: Cambiar por ingredientes de temporada      │
│    • Ingredientes: Eliminar alérgenos/restricciones        │
│    • Estilo: Ajustar al estilo culinario preferido         │
│                                                              │
│    Ejemplo: Caso original tenía cordero (€35)              │
│            → Cliente pide vegetariano                        │
│            → Se adapta a: Risotto de setas (€28)           │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. REVISE (Revisar/Validar)                                │
│    Valida que el menú adaptado sea correcto                 │
│                                                              │
│    ✅ Validaciones:                                          │
│    • Compatibilidad de sabores                              │
│    • Balance nutricional                                    │
│    • Presupuesto cumplido                                   │
│    • Restricciones dietéticas                               │
│    • Coherencia de estilos                                  │
│    • Maridaje adecuado                                      │
│                                                              │
│    Si pasa: ✅ Menú aceptado → se propone al cliente        │
│    Si falla: ❌ Menú rechazado → se descarta               │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ RESULTADO: 3 Menús Propuestos                               │
│ - Opción 1 (93% similitud): Ceviche + Lubina + Frutas      │
│ - Opción 2 (85% similitud): Ensalada + Tagine + Tiramisú   │
│ - Opción 3 (78% similitud): Salmón + Bacalao + Chocolate   │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. RETAIN (Retener/Aprender) 🧠                             │
│    Después de que el cliente use el menú                    │
│                                                              │
│    Proceso de aprendizaje:                                  │
│    1. Cliente da feedback: ⭐⭐⭐⭐⭐ (4.8/5)                │
│    2. Sistema evalúa si vale la pena guardar:               │
│                                                              │
│       Decision Tree:                                        │
│       ┌─ Score < 3.5? → ❌ DESCARTAR (mala experiencia)    │
│       │                                                      │
│       ├─ ¿Ya existe caso similar (>85%)?                    │
│       │  ├─ Sí → ¿El nuevo es mejor?                        │
│       │  │      ├─ Sí → ✅ ACTUALIZAR caso existente        │
│       │  │      └─ No → ❌ DESCARTAR (ya tenemos mejor)     │
│       │  └─ No → ✅ AÑADIR NUEVO caso                       │
│       │                                                      │
│       └─ ¿Demasiados casos del mismo tipo?                  │
│          └─ Sí → LIMPIEZA: eliminar casos viejos/malos      │
│                                                              │
│    💾 Resultado: Nuevo caso guardado en la base             │
│       → Sistema aprende y mejora para próximas veces        │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Umbrales y Parámetros

### RETRIEVE (retrieve.py)
```python
min_similarity_threshold = 0.3   # Mínimo 30% de similitud
max_candidates = 50              # Máximo 50 casos a evaluar
```

### ADAPT (adapt.py)
```python
# Pesos de similitud:
event_weight = 0.30      # 30% - Tipo de evento
price_weight = 0.25      # 25% - Presupuesto
season_weight = 0.15     # 15% - Temporada
style_weight = 0.15      # 15% - Estilo culinario
dietary_weight = 0.15    # 15% - Restricciones
```

### REVISE (revise.py)
```python
# Validaciones:
- Sabores incompatibles
- Balance calórico (1200-2500 kcal)
- Presupuesto ±10%
- Compatibilidad de estilos
```

### RETAIN (retain.py)
```python
novelty_threshold = 0.85         # Si <85%, es novedoso
quality_threshold = 3.5          # Mínimo 3.5/5 estrellas
max_cases_per_event = 50         # Máximo 50 casos por evento
```

## 🎯 Ejemplo Práctico Completo

```
📝 SOLICITUD
Usuario: "Necesito menú para boda, 100 personas, 80€/persona, primavera"

1️⃣ RETRIEVE
   → Busca en 10 casos iniciales
   → Encuentra caso #1: boda primavera gourmet (93% similar)
   → Encuentra caso #2: boda otoño sibarita (85% similar)

2️⃣ ADAPT
   → Caso #1: Ya es perfecto, solo ajusta cantidad (100 personas)
   → Caso #2: Cambia plato otoño → plato primavera
             Foie-gras (otoño) → Ceviche (primavera)

3️⃣ REVISE
   → Caso #1: ✅ Válido (sabores OK, precio 73€ ✓)
   → Caso #2: ✅ Válido (sabores OK, precio 78€ ✓)

✅ PROPUESTAS ENVIADAS AL CLIENTE

... Cliente elige Caso #1 ...
... Evento ocurre ...
... Cliente da feedback: 4.8/5 ⭐⭐⭐⭐⭐ ...

4️⃣ RETAIN
   → Score 4.8 > 3.5 ✅ (bueno)
   → Compara con caso original #1
   → Similitud 95% (muy similar)
   → ¿Mejor que original? 4.8 vs 4.8 (igual)
   → ❌ DECISIÓN: No guardar (ya existe uno igual de bueno)
```

## 🧠 Aprendizaje Continuo

El sistema mejora con el tiempo:

1. **Inicio**: 10 casos base (cargados desde JSON)
2. **Después de 50 eventos**: ~15 casos (nuevos aprendidos)
3. **Después de 100 eventos**: ~25 casos (experiencia acumulada)
4. **Limpieza automática**: Elimina casos malos (score <3.0)

### Estrategias de Retención

```python
# AÑADIR NUEVO - Cuando:
- Score ≥ 3.5
- Similitud con existentes < 85% (es novedoso)
- No excede límite de casos por evento

# ACTUALIZAR EXISTENTE - Cuando:
- Score ≥ 3.5
- Similitud con existentes ≥ 85% (casi idéntico)
- Nuevo score > score existente (es mejor)

# DESCARTAR - Cuando:
- Score < 3.5 (mala experiencia)
- Ya existe uno similar con igual o mejor score
- Base de casos llena y este no es mejor que los peores
```

## 🔍 Cálculo de Similitud (Detalle)

```python
def calculate_similarity(request_new, case_existing):
    # 1. Similitud de evento (exacta o compatible)
    event_sim = 1.0 if same else 0.5 if compatible else 0.0
    
    # 2. Similitud de precio (distancia normalizada)
    price_sim = 1.0 - |price_new - price_old| / max_price
    
    # 3. Similitud de temporada
    season_sim = 1.0 if same else 0.7 if compatible else 0.3
    
    # 4. Similitud de estilo
    style_sim = 1.0 if same else 0.5 if related else 0.0
    
    # 5. Restricciones dietéticas (todas deben cumplirse)
    diet_sim = 1.0 if all_satisfied else 0.0
    
    # TOTAL PONDERADO
    total = (event_sim * 0.30 +
             price_sim * 0.25 +
             season_sim * 0.15 +
             style_sim * 0.15 +
             diet_sim * 0.15)
    
    return total  # 0.0 a 1.0
```

## 📊 Mantenimiento de la Base de Casos

```python
# Limpieza automática cuando:
if casos_por_evento > max_cases_per_event:
    # Ordenar por utilidad
    casos_ordenados = sort_by_utility(casos)
    
    # Utility = (score * 0.4) + 
    #           (frecuencia_uso * 0.3) + 
    #           (novedad * 0.3)
    
    # Eliminar los peores
    eliminar(casos_ordenados[-10:])
```

---

**Resumen**: El sistema **aprende de la experiencia**, guardando solo casos útiles y mejorando continuamente sus recomendaciones. Cada evento exitoso puede convertirse en conocimiento para futuros menús.
