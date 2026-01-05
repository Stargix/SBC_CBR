# Sistema de Explicabilidad - Cómo se Generan las Explicaciones

## 📚 ¿Cómo se Generan las Explicaciones?

Las explicaciones se generan en el módulo **[`develop/cycle/explanation.py`](develop/cycle/explanation.py)**, que contiene la clase `ExplanationGenerator`.

### Flujo de Generación

```
1. Usuario hace solicitud (Request)
       ↓
2. Sistema ejecuta ciclo CBR (RETRIEVE → ADAPT → REVISE)
       ↓
3. ExplanationGenerator recopila datos de cada fase
       ↓
4. Se genera informe completo con:
   - Desglose de similitud (RETRIEVE)
   - Adaptaciones realizadas (ADAPT)
   - Validaciones y warnings (REVISE)
       ↓
5. Explicación textual devuelta al usuario
```

### Componente Responsable

**Archivo:** `develop/cycle/explanation.py` (~609 líneas)

**Clase principal:**
```python
class ExplanationGenerator:
    """
    Generador de explicaciones para el sistema CBR.
    
    Proporciona explicaciones claras y útiles sobre
    las decisiones del sistema.
    """
```

**Método principal:**
```python
def generate_full_report(self, proposed_menus, rejected_cases, request, 
                         retrieval_results=None):
    """
    Genera el informe completo de razonamiento CBR.
    
    ANTES del refactor: ~200 palabras, solo similitud global
    DESPUÉS del refactor: ~1000+ palabras, desglose completo
    """
```

---

## 🎯 ¿Qué Explican?

Las explicaciones cubren **3 fases principales del ciclo CBR**:

### 1. **RETRIEVE - Recuperación de Casos**

**Qué explica:**
- Por qué se seleccionó cada caso base
- Desglose de similitud por **9 criterios**:
  1. Tipo de evento (wedding, corporate, etc.)
  2. Rango de precio
  3. Temporada (spring, summer, autumn, winter)
  4. Estilo culinario (classic, modern, fusion, etc.)
  5. Tradición cultural (italiana, francesa, etc.)
  6. Requisitos dietéticos (vegetarian, vegan, etc.)
  7. Número de comensales
  8. Preferencia de vino
  9. Bonus por éxito previo

**Ejemplo de explicación generada:**
```
🔍 FASE 1: RETRIEVE - Recuperación de casos similares

Caso #1: case-init-7 (Similitud: 83.3%)

Desglose de similitud:
  • Tipo de evento       : 60.0% ████████████
  • Rango de precio      : 100.0% ████████████████████
  • Temporada            : 100.0% ████████████████████
  • Tradición cultural   : 80.0% ████████████████
  • Requisitos dietéticos: 100.0% ████████████████████
```

### 2. **ADAPT - Adaptación de Casos**

**Qué explica:**
- Qué adaptaciones se realizaron
- Por qué se hicieron (cultural, dietética, precio)
- Qué platos se sustituyeron

**Tipos de adaptaciones:**

#### A) Adaptaciones Culturales
```
🔧 ADAPT: Adaptaciones culturales
  • Sustituido Beef Wellington → Risotto ai Funghi (tradición italiana)
  • Cambiado Wine Pairing → Italian Wine Selection
  • Adaptado French Onion Soup → Minestrone (cultura italiana)
```

#### B) Adaptaciones Dietéticas
```
🔧 ADAPT: Adaptaciones dietéticas
  • Sustituido Beef Tenderloin → Grilled Portobello (vegetarian)
  • Eliminado Prosciutto de la ensalada (restricción: vegetarian)
  • Cambiada salsa con mantequilla → salsa vegetal
```

#### C) Adaptaciones de Precio
```
🔧 ADAPT: Ajustes de precio
  • Sustituido Lobster Bisque (€18) → Tomato Soup (€8)
  • Precio original: 95€ → Precio adaptado: 78€
  • Mantenida calidad dentro del presupuesto 40-70€
```

### 3. **REVISE - Validación**

**Qué explica:**
- Estado de validación (válido, con warnings, rechazado)
- Puntuación de validación (0-100%)
- Warnings detectados
- Errores críticos (si los hay)

**Ejemplo:**
```
🔍 REVISE: Validación

Estado: validated_with_warnings
Puntuación: 85.0%

Advertencias detectadas:
  ⚠ El menú no cumple completamente con la tradición cultural italiana
  ⚠ Algunas calorías por encima del rango ideal
  ⚠ Ingrediente 'parmesan' puede no ser apto para algunos vegetarianos
```

---

## 📊 Tipos de Explicaciones

El sistema genera **7 tipos** de explicaciones:

```python
class ExplanationType(Enum):
    SELECTION = "selection"          # Por qué se seleccionó
    REJECTION = "rejection"          # Por qué se rechazó
    ADAPTATION = "adaptation"        # Qué adaptaciones se hicieron
    SIMILARITY = "similarity"        # Por qué es similar
    STYLE = "style"                  # Influencia del estilo culinario
    PAIRING = "pairing"              # Maridaje de bebidas
    CULTURAL = "cultural"            # Tradición cultural
```

---

## 🔬 Cómo Varían las Explicaciones Según la Solicitud

Las explicaciones son **dinámicas** y varían según:

### 1. **Restricciones Dietéticas**

#### Sin restricciones:
```
Menú usado sin modificaciones o con adaptaciones mínimas
```

#### Con restricciones (vegetarian):
```
🔧 Adaptaciones realizadas:
  • 5 sustituciones para cumplir requisito: vegetarian
  • Eliminados: beef, prosciutto, chicken stock
  • Añadidos: tofu, portobello, vegetable stock
```

#### Con restricciones estrictas (vegan + alergias):
```
🔧 Adaptaciones realizadas:
  • 12 sustituciones para cumplir: vegan, gluten-free
  • Ingredientes prohibidos eliminados: honey, gelatin, wheat
  • Alternativas seleccionadas: agave, agar-agar, rice flour
```

### 2. **Cultura/Tradición**

#### Sin preferencia cultural:
```
Menú multicultural con influencias variadas
```

#### Con cultura italiana:
```
🌍 Tradición Cultural: Italiana

Este menú incorpora elementos de la tradición culinaria italiana,
una de las más ricas del Mediterráneo.

Platos representativos:
  • Minestrone - sopa tradicional italiana
  • Risotto ai Funghi - arroz italiano clásico
  • Tiramisu - postre emblemático
```

### 3. **Presupuesto**

#### Presupuesto alto (120-200€):
```
💎 Categoría: PREMIUM

Platos seleccionados por calidad excepcional:
  • Lobster Bisque (€22)
  • Wagyu Beef Tenderloin (€85)
  • Chocolate Soufflé (€18)
  
Precio total: 145€/persona
```

#### Presupuesto bajo (25-40€):
```
💰 Categoría: ECONÓMICO

Ajustes de precio realizados:
  • Sustituido Lobster → Tomato Soup (ahorro: €14)
  • Sustituido Wagyu → Grilled Chicken (ahorro: €45)
  • Precio final: 38€/persona ✅ Dentro del presupuesto
```

### 4. **Complejidad de Adaptación**

#### Adaptación simple (similitud alta):
```
Similitud inicial: 92.5%
Similitud final: 91.8%

El menú es muy similar al caso base exitoso.
Se realizaron 2 adaptaciones menores para ajustar al presupuesto.
```

#### Adaptación compleja (similitud baja + muchas restricciones):
```
Similitud inicial: 58.3%
Similitud final: 45.7% ⚠️

El menú requirió adaptaciones significativas:
  • 15 sustituciones realizadas
  • Cambios culturales: 5
  • Cambios dietéticos: 8
  • Ajustes de precio: 2

⚠️ Nota: La similitud disminuyó debido a las restricciones estrictas,
pero el menú cumple todos los requisitos.
```

---

## 🧪 Tests para Ver las Explicaciones

Se han creado **2 archivos de prueba**:

### 1. Test Comprehensivo (Interactivo)
**Archivo:** `test_explanation_showcase.py`

Incluye 6 casos de test:
1. Boda simple sin restricciones
2. Corporativo vegetariano italiano
3. Cumpleaños vegano presupuesto bajo
4. Gala premium (alta categoría)
5. Aniversario con alergias múltiples
6. Comparación de propuestas

**Ejecutar:**
```bash
python test_explanation_showcase.py
```

### 2. Demo Simple (Automática)
**Archivo:** `demo_explicaciones_simple.py`

3 casos progresivos que muestran:
- Caso 1: Explicación básica
- Caso 2: Adaptaciones culturales + dietéticas
- Caso 3: Restricciones complejas + validaciones

**Ejecutar:**
```bash
python demo_explicaciones_simple.py
```

---

## 📈 Diferencia Antes/Después del Refactor

### ANTES (Sistema antiguo)
```
Informe breve (~200 palabras):

"Menú seleccionado para boda:
 - Similitud: 85%
 - Precio: 95€
 - Se realizaron algunas adaptaciones"
```

### DESPUÉS (Sistema actual)
```
Informe completo (~1000+ palabras):

================================================================================
INFORME COMPLETO DE RAZONAMIENTO CBR - Chef Digital
================================================================================

📋 SOLICITUD RECIBIDA
  • Evento: Boda (100 comensales)
  • Presupuesto: 80-150€/persona
  • Temporada: Verano
  • Restricciones: vegetarian
  • Cultura: italiana

🔍 FASE 1: RETRIEVE - Recuperación de casos similares

  Caso #1: case-init-7 (Similitud: 83.3%)
  
  Desglose de similitud por criterio:
    • Tipo de evento       : 60.0% ████████████
    • Rango de precio      : 100.0% ████████████████████
    • Temporada            : 100.0% ████████████████████
    • Tradición cultural   : 80.0% ████████████████
    • Requisitos dietéticos: 100.0% ████████████████████
    
✅ FASE 2-3: ADAPT + REVISE - Menús adaptados y validados

🍽️ PROPUESTA #1
================================================================================
📋 COMPOSICIÓN DEL MENÚ:
  Entrante:     Minestrone
  Plato Fuerte: Eggplant Parmesan
  Postre:       Tiramisu
  💰 Precio total: 58.50€ por persona

🔍 RETRIEVE: Caso base seleccionado
  • Caso origen: case-init-7
  • Similitud inicial: 83.3%
  • Desglose de criterios: [ver arriba]

🔧 ADAPT: Adaptaciones aplicadas (5 total)
  1. Sustituido Beef Tenderloin → Eggplant Parmesan (vegetarian)
  2. Adaptado menú a tradición italiana
  3. Cambiado French Onion Soup → Minestrone (cultura italiana)
  4. Ajustado precio de 95€ → 58€ (dentro presupuesto)
  5. Optimizado para temporada summer

🔍 REVISE: Validación
  • Estado: validated_with_warnings
  • Puntuación: 88.5%
  • Warnings: 2
    ⚠ Calorías ligeramente superiores al rango ideal
    ⚠ Ingrediente 'parmesan' puede requerir alternativa vegana

🌟 EVALUACIÓN FINAL:
  • Cumple requisitos: ✅ Sí
  • Dentro de presupuesto: ✅ Sí (58€ < 150€)
  • Cumple restricciones dietéticas: ✅ Sí (vegetarian)
  • Tradición cultural respetada: ✅ Sí (italiana)
  
...
```

---

## 🎓 Conclusión

**Las explicaciones en el sistema CBR se generan de forma dinámica y personalizada:**

1. **Módulo responsable:** `develop/cycle/explanation.py`
2. **Datos de entrada:** Resultados de RETRIEVE, ADAPT y REVISE
3. **Salida:** Informe textual detallado y comprensible
4. **Variación:** Según restricciones, cultura, presupuesto y complejidad

**Para ver ejemplos prácticos, ejecuta:**
```bash
# Demo rápida (3 casos con pause entre cada uno)
python demo_explicaciones_simple.py

# Test completo (6 casos, selección interactiva)
python test_explanation_showcase.py
```

Cada solicitud diferente activa diferentes partes del generador de explicaciones, mostrando información relevante al contexto específico del usuario.
