# Simulador CBR con Groq LLM

Sistema de simulación para el CBR de Chef Digital usando Groq Cloud **solo para evaluar** menús con aprendizaje adaptativo.

## 🚀 Instalación

```bash
pip install groq python-dotenv
```

Configura tu API key en `simulation/.env`:
```bash
GROQ_API_KEY=tu_api_key_aqui
```

## 📊 Uso Básico

```bash
# Simulación con adaptive weights (recomendado)
python simulation/run_groq_simulation.py -n 10 --adaptive

# Simulación sin adaptive weights
python simulation/run_groq_simulation.py -n 10 --static

# Personalizar temperatura y salida
python simulation/run_groq_simulation.py -n 5 -t 0.9 -o data/mi_sim.json
```

## 🎯 Características

- ✅ **Solicitudes aleatorias** generadas programáticamente (sin LLM)
- ✅ **Evaluación individual** de cada menú propuesto por LLM (0-5)
- ✅ **Aprendizaje adaptativo** de pesos de similitud basado en feedback
- ✅ **Evolución del sistema** a través de las interacciones
- ✅ Guardado de historial de aprendizaje

## ⚡ Uso eficiente de Groq API

El LLM **solo se usa para evaluar** el menú final, no para generar solicitudes:
- ❌ **NO se usa LLM para:** Generar requests aleatorios
- ✅ **SÍ se usa LLM para:** Evaluar calidad del menú propuesto (0-5 score)

Esto reduce llamadas API innecesarias y costos.

## 📁 Resultados

Los archivos generados:
- `data/groq_simulation_results.json` - Resultados de la simulación
- `data/groq_simulation_results_learning.json` - Evolución de pesos (si adaptive está activo)

## 🔧 Opciones

| Opción | Descripción | Default |
|--------|-------------|---------|
| `-n` | Número de interacciones | 5 |
| `-t` | Temperatura LLM (0.0-2.0) | 0.9 |
| `--adaptive` | Habilitar adaptive weights | True |
| `--static` | Deshabilitar adaptive weights | False |
| `-o` | Archivo de salida | data/groq_simulation_results.json |
| `-q` | Modo silencioso | False |

## 📈 Evolución del Aprendizaje

Con `--adaptive`, el sistema:
1. **Genera solicitud aleatoria** (programáticamente)
2. Propone menús via CBR
3. **LLM evalúa** el menú final (0-5)
4. **Sistema aprende** y ajusta pesos de similitud
5. Siguiente solicitud usa pesos mejorados

Los pesos evolucionan según el feedback real del LLM, mejorando las propuestas futuras.
