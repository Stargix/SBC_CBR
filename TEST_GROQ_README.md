# Test de Dimensiones Separadas con Groq

Este test verifica que el sistema evalúa correctamente precio, cultura y sabor por separado usando Groq LLM.

## 📋 Requisitos

### 1. Instalar paquetes Python

```bash
pip install groq python-dotenv
```

### 2. Obtener API Key de Groq (GRATIS)

1. Ve a https://console.groq.com/
2. Crea una cuenta (es gratuita)
3. Ve a "API Keys" en el menú
4. Click en "Create API Key"
5. Copia la API key generada

### 3. Crear archivo `.env`

Crea un archivo llamado `.env` en la raíz del proyecto (`SBC_CBR/`) con:

```env
GROQ_API_KEY=tu_api_key_aqui
```

**Ejemplo:**
```env
GROQ_API_KEY=gsk_abc123xyz456...
```

## 🚀 Ejecutar el Test

```bash
python test_groq_separate_dimensions.py
```

## 🧪 Qué verifica el test

1. **Test Unitario - Extracción de dimensiones:**
   - Verifica que `_extract_dimension_scores_from_evaluation()` funciona
   - Prueba con respuesta simulada del LLM
   - NO requiere llamada a la API

2. **Test de Integración - Evaluación con Groq:**
   - Hace UNA llamada real a Groq API
   - Genera una solicitud de menú
   - El LLM evalúa precio, cultura y sabor por separado
   - Verifica que el aprendizaje funciona con dimensiones específicas

## ✅ Resultado Esperado

```
================================================================================
RESUMEN DE TODOS LOS TESTS
================================================================================
Test unitario (extracción):     ✅ PASADO
Test integración (Groq):        ✅ PASADO
================================================================================

🎉 ¡TODOS LOS TESTS PASARON!

✅ La implementación de dimensiones separadas funciona correctamente:
   - El LLM evalúa precio, cultura y sabor por separado
   - Los scores se extraen correctamente
   - El weight learner aprende de dimensiones específicas
```

## 🔍 Qué hace cada componente

### groq_simulator.py

- **`_evaluate_single_request()`**: Pide al LLM evaluar cada dimensión
- **`_extract_dimension_scores_from_evaluation()`**: Extrae los scores del texto
- **`_apply_learning_from_score()`**: Crea FeedbackData con dimensiones separadas

### main.py

- **`learn_from_feedback()`**: Usa las dimensiones específicas de FeedbackData
- Convierte a objeto `Feedback` con scores separados
- Llama a `AdaptiveWeightLearner.update_from_feedback()`

### adaptive_weights.py

- **`update_from_feedback()`**: Ajusta pesos según dimensión problemática
- Si `price_satisfaction < 3` → aumenta peso de `price_range`
- Si `cultural_satisfaction < 3` → aumenta peso de `cultural`
- Si `flavor_satisfaction < 3` → nota para adaptación de platos

## 💡 Notas

- El test hace **UNA sola llamada** a Groq API (es barato/gratis)
- La API de Groq tiene un tier gratuito generoso
- Si falla, verifica que el `.env` está en la raíz del proyecto
- El test pausará antes de llamar a la API (puedes cancelar con Ctrl+C)

## 🐛 Troubleshooting

**Error: "GROQ_API_KEY no encontrada"**
- Verifica que el archivo `.env` existe en `SBC_CBR/.env`
- Verifica que el formato es: `GROQ_API_KEY=tu_key` (sin espacios extras)

**Error: "ModuleNotFoundError: No module named 'groq'"**
```bash
pip install groq python-dotenv
```

**Error de API: "Invalid API key"**
- Regenera la API key en https://console.groq.com/
- Asegúrate de copiar la key completa

## 📊 Comparación: Antes vs Después

### ANTES (Sobresimplificado)
```python
# Un solo score para todo
score = 2.5

feedback = FeedbackData(
    score=2.5,
    price_satisfaction=2.5,     # ← Igual
    cultural_satisfaction=2.5,  # ← Igual
    flavor_satisfaction=2.5     # ← Igual
)
# No se sabe qué falló específicamente
```

### DESPUÉS (Dimensiones Separadas)
```python
# LLM evalúa cada dimensión
PRECIO: 1.5      # ⚠️ Problema identificado
CULTURA: 4.5     # ✅ OK
SABOR: 4.0       # ✅ OK
GENERAL: 2.5

feedback = FeedbackData(
    score=2.5,
    price_satisfaction=1.5,     # ← Específico
    cultural_satisfaction=4.5,  # ← Específico
    flavor_satisfaction=4.0     # ← Específico
)
# El sistema sabe que el problema fue el PRECIO
# → Aumenta peso de 'price_range' en similitud
```

## 🎯 Beneficios

- ✅ Feedback más preciso y detallado
- ✅ Aprendizaje más efectivo
- ✅ El sistema identifica exactamente qué falló
- ✅ Ajusta pesos específicos, no todos por igual
