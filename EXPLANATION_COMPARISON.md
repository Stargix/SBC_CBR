# Ejemplo: Explicación Actual vs Explicación Ideal

## Escenario de Prueba

```python
Request(
    event_type=EventType.WEDDING,
    num_guests=100,
    price_max=60.0,
    season=Season.SUMMER,
    cultural_preference=CulturalTradition.ITALIAN
)
```

---

## 1. EXPLICACIÓN ACTUAL (explanation.py)

```
============================================================
INFORME DE SELECCIÓN DE MENÚS
============================================================

📋 SOLICITUD RECIBIDA
----------------------------------------
Tipo de evento: wedding
Número de comensales: 100
Presupuesto por persona: 60.00€
Temporada: summer

✅ MENÚS PROPUESTOS
----------------------------------------

🍽️ OPCIÓN 1 (Similitud: 83.3%)

Detalles:
  • Similitud con caso exitoso previo: 83.3%
  • Diseñado específicamente para una boda, momento especial que requiere elegancia
  • Adaptado a la temporada de verano, privilegiando platos refrescantes
  • Ajustado al presupuesto de 60.00€ por persona

Composición del menú:
  - Bruschetta (starter)
  - Pasta alla Norma (main_course)
  - Tiramisu (dessert)

Precio total: 58.50€ por persona
```

### Problemas:
- ❌ No dice CÓMO se calculó 83.3%
- ❌ No menciona qué caso base se usó
- ❌ No explica si se adaptó algo
- ❌ No dice por qué 83.3% es bueno o malo
- ❌ No menciona cultura italiana solicitada

---

## 2. EXPLICACIÓN IDEAL (Mejorada)

```
============================================================
INFORME DE SELECCIÓN DE MENÚS - ANÁLISIS DETALLADO
============================================================

📋 SOLICITUD RECIBIDA
----------------------------------------
Tipo de evento: Boda
Comensales: 100
Presupuesto: 60.00€/persona
Temporada: Verano
Preferencia cultural: Italiana

============================================================
🔍 FASE 1: RETRIEVE (Recuperación de Casos Similares)
============================================================

Se analizaron 41 casos en la base de conocimiento.
Se recuperó el caso más similar: #W2024-034

📊 DESGLOSE DE SIMILITUD: 83.3% (ALTA)

Criterio               Score    Peso    Contribución
───────────────────────────────────────────────────
Tipo de evento         95.0%    20%     19.0%
Rango de precio        87.5%    18%     15.8%
Temporada             100.0%    12%     12.0%
Estilo culinario       70.0%    12%      8.4%
Cultural (italiana)    85.0%     8%      6.8%
Restricciones diet.   100.0%    10%     10.0%
Núm. comensales        90.0%     5%      4.5%
Preferencia vino      100.0%     5%      5.0%
Bonus éxito previo     95.0%    10%      9.5%
───────────────────────────────────────────────────
SIMILITUD GLOBAL                       83.3%

✅ Por qué este caso:
  • Evento: Boda en verano 2024 con 120 invitados (similar)
  • Presupuesto: 55-65€ (dentro de rango)
  • Feedback previo: 4.8/5 estrellas (muy exitoso)
  • Cultural: Menú mediterráneo (compatible con italiano)

============================================================
🔧 FASE 2: ADAPT (Adaptaciones Realizadas)
============================================================

El menú original fue adaptado para tu solicitud específica.

Adaptaciones culturales (3):
  1. ✅ Entrante: "Gazpacho" → "Bruschetta"
     Razón: Preferencia italiana (similitud cultural: 85%)
     Confianza: ALTA
  
  2. ✅ Principal: "Paella de Marisco" → "Pasta alla Norma"
     Razón: Tradición italiana + temporada verano
     Confianza: ALTA
  
  3. ✅ Postre: "Crema Catalana" → "Tiramisu"  
     Razón: Icónico de cocina italiana
     Confianza: MUY ALTA

Adaptaciones de precio (1):
  4. 📊 Precio ajustado: 62.50€ → 58.50€
     Razón: Ajuste preventivo para cumplir límite 60€
     Método: Reducción proporcional de todos los platos

Ingredientes adaptados (2):
  5. 🔄 Berenjenas (Pasta): Verificadas temporada verano ✓
  6. 🔄 Tomates (Bruschetta): Ingrediente de temporada óptimo ✓

============================================================
✓ FASE 3: REVISE (Validación)
============================================================

Estado: PASS (Validación exitosa)

Validaciones realizadas:
  ✅ Presupuesto: 58.50€ < 60.00€ (OK)
  ✅ Restricciones dietéticas: Ninguna violación
  ✅ Compatibilidad de sabores: Excelente (Score: 92%)
  ✅ Balance nutricional: Adecuado (1850 kcal)
  ✅ Coherencia cultural: Italiana consistente
  ✅ Maridaje: Vino blanco italiano → Compatible

Advertencias: Ninguna

============================================================
🍽️ MENÚ PROPUESTO (Opción 1)
============================================================

Similitud Global: 83.3%
Confianza: ALTA
Origen: Caso #W2024-034 (adaptado)

Composición:
  Entrante:   Bruschetta con tomate fresco y albahaca    15.00€
  Principal:  Pasta alla Norma (berenjena, ricotta)     28.50€
  Postre:     Tiramisu clásico                          12.00€
  Bebida:     Pinot Grigio DOC Friuli                    3.00€
              ─────────
  TOTAL:                                                58.50€/persona

Características del menú:
  • Cultura: 100% Italiana
  • Temporada: Ingredientes de verano
  • Estilo: Clásico italiano con toque regional
  • Éxito previo: Menú base tuvo 4.8/5 estrellas

============================================================
📈 TRANSPARENCIA DEL SISTEMA
============================================================

Pesos de similitud actuales:
  Los pesos han sido aprendidos de 43 casos previos.
  Último ajuste: Hace 2 días (+3% en precio por feedback)

Caso base #W2024-034:
  • Fecha: Junio 2024
  • Evento: Boda mediterránea, 120 invitados
  • Feedback: "Excelente, todos encantados" (4.8/5)
  • Adaptaciones previas: 2 (precio, bebida)

Razón de recomendación:
  Este menú combina la experiencia exitosa de un caso 
  previo similar (83.3% de coincidencia) con adaptaciones
  precisas para tu preferencia italiana. La alta similitud
  en tipo de evento, temporada y presupuesto garantiza
  un resultado óptimo.
```

---

## Comparación Lado a Lado

| Aspecto | Actual | Ideal |
|---------|--------|-------|
| **Longitud** | ~200 palabras | ~600 palabras |
| **Detalle RETRIEVE** | Solo % global | Desglose completo por criterio |
| **Caso base** | No menciona | ID, fecha, feedback |
| **Adaptaciones** | "Se adaptó" | Lista detallada con razones |
| **Validación** | No menciona | Estado + checks realizados |
| **Trazabilidad** | ❌ Baja | ✅ Alta |
| **Confianza** | ❌ No cuantificada | ✅ Niveles claros |
| **Aprendizaje** | ❌ No visible | ✅ Transparente |
| **Utilidad académica** | ⚠️ Limitada | ✅ Completa |

---

## Conclusión

La explicación **actual es suficiente para un usuario final** que solo quiere saber "qué se recomienda y por qué en términos generales".

La explicación **ideal es necesaria para:**
- ✅ Evaluación académica del CBR
- ✅ Debugging del sistema  
- ✅ Transparencia completa (XAI)
- ✅ Auditoría de decisiones
- ✅ Mejora continua basada en análisis

**Para tu report académico, la explicabilidad actual es INSUFICIENTE si quieres demostrar un CBR transparente y auditable.**
