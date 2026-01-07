# 📺 Demos del Sistema CBR de Chef Digital

Este directorio contiene demostraciones interactivas del sistema de razonamiento basado en casos (CBR) para recomendación de menús personalizados.

## 🚀 Cómo ejecutar las demos

Desde la raíz del proyecto:

```bash
# Ver lista de demos disponibles
python run_demos.py

# Ejecutar una demo específica
python run_demos.py <nombre_demo>
```

## 📋 Demos disponibles

### 1. **simulacion** - Simulación de usuarios sintéticos
Demuestra cómo el sistema aprende de múltiples usuarios con diferentes preferencias.
- Genera usuarios sintéticos con preferencias diversas
- Procesa solicitudes y recopila feedback
- Muestra evolución de la base de conocimiento

**Ejecución:**
```bash
python run_demos.py simulacion
```

### 2. **retain** - Ciclo CBR completo con aprendizaje
Demostración del ciclo RETRIEVE → ADAPT → REVISE → RETAIN.
- Recupera casos similares
- Adapta el menú a la solicitud
- Valida la solución
- Aprende del feedback del usuario

**Ejecución:**
```bash
python run_demos.py retain
```

### 3. **menu_completo** - Adaptación completa de menú
Muestra cómo el sistema adapta menús con restricciones dietéticas.
- Recupera menú de la base de casos
- Adapta ingredientes según restricciones
- Muestra sustituciones realizadas

**Ejecución:**
```bash
python run_demos.py menu_completo
```

### 4. **recalculo_similitud** - Recálculo de similitud
Demuestra cómo la similitud cambia después de adaptaciones.
- Calcula similitud inicial
- Realiza adaptaciones
- Recalcula similitud global

**Ejecución:**
```bash
python run_demos.py recalculo_similitud
```

### 5. **filtrado_critico** - Filtrado de restricciones
Muestra cómo RETRIEVE filtra por dietas y alergias.
- Filtra casos incompatibles ANTES del scoring
- Evita desperdiciar intentos de adaptación
- Mejora eficiencia

**Ejecución:**
```bash
python run_demos.py filtrado_critico
```

### 6. **adaptacion_dietetica** - Adaptación de ingredientes
Demuestra sustitución inteligente de ingredientes.
- Identifica ingredientes problemáticos
- Busca sustituciones compatibles
- Muestra confianza de cada sustitución

**Ejecución:**
```bash
python run_demos.py adaptacion_dietetica
```

### 7. **negative_cases** - Manejo de casos negativos
Muestra cómo el sistema almacena y evita repetir errores.
- Almacena casos de fracaso (negative cases)
- Mantenimiento periódico de la base
- Eliminación inteligente de redundancias

**Ejecución:**
```bash
python run_demos.py negative_cases
```

## 🎯 Estructura de ejecución

Desde fuera de la carpeta `demos`:

```
proyecto/
├── run_demos.py           # Script para ejecutar demos
├── run_chef_cbr.py        # Script para ejecutar el sistema
├── develop/
│   ├── main.py
│   ├── core/
│   ├── cycle/
│   └── ...
├── demos/                 # ← TÚ ESTÁS AQUÍ
│   ├── __init__.py
│   ├── demo_simulacion.py
│   ├── demo_retain.py
│   └── ...
└── ...
```

## 💡 Notas

- Las demos realizan imports relativos desde el paquete `develop`
- Se ejecutan como módulos Python (`python -m demos.demo_XXX`)
- Cada demo genera salida completa y documentada
- Se pueden personalizar parámetros dentro de cada archivo

## 🔗 Ejecución alternativa

Si quieres ejecutar una demo directamente desde VS Code o terminal:

```bash
# Desde la raíz del proyecto
python -m demos.demo_simulacion
python -m demos.demo_retain
python -m demos.demo_menu_completo
```

---

**Autor:** Sistema CBR Chef Digital  
**Actualizado:** 2026-01-03
