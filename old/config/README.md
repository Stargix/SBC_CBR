# Configuración del Sistema CBR

Este directorio contiene archivos de configuración para externalizar el conocimiento del dominio gastronómico.

## Archivos

### `knowledge_base.json`

Contiene todo el conocimiento culinario utilizado por el sistema CBR:

- **flavor_compatibility**: Qué sabores combinan bien entre sí
- **incompatible_categories**: Categorías de platos que no deben aparecer juntas
- **wine_flavor_compatibility**: Qué tipo de vino combina con qué sabores
- **event_styles**: Estilos culinarios recomendados por tipo de evento
- **event_complexity**: Complejidad apropiada según el evento
- **calorie_ranges**: Rangos de calorías recomendados por temporada
- **style_descriptions**: Descripciones de cada estilo culinario

### `dishes.json`

Base de datos completa de 25 platos disponibles con todos sus atributos:
- Información básica (id, nombre, tipo, precio)
- Categoría gastronómica y estilos culinarios
- Temporadas, temperatura, complejidad
- Calorías, capacidad máxima de comensales
- Sabores, dietas compatibles, ingredientes
- Bebidas compatibles, tradiciones culturales

### `beverages.json`

Base de datos completa de 17 bebidas disponibles:
- Información básica (id, nombre, precio)
- Tipo (alcohólica/no alcohólica)
- Estilos y subtipos
- Sabores compatibles (para vinos)

## Estado de la migración

✅ **Completado:**
- Conocimiento del dominio (compatibilidades, reglas, estilos) → `knowledge_base.json`
- Platos (25 items) → `dishes.json`
- Bebidas (17 items) → `beverages.json`

⏳ **Pendiente:**
- Modificar `case_base.py` para cargar platos/bebidas desde JSON en lugar de código
- Casos iniciales (10 menús predefinidos) - opcional

**Archivos generados:**
- `dishes.json`: 1016 líneas, 20KB
- `beverages.json`: 221 líneas, 4.2KB  
- `knowledge_base.json`: 313 líneas, 6.5KB

**Total**: ~1550 líneas de configuración externalizadas

## Cómo modificar

### Agregar una nueva compatibilidad de sabores

```json
"flavor_compatibility": {
  "sweet": ["salty", "sour", "nuevo_sabor"]
}
```

### Agregar un nuevo estilo para eventos

```json
"event_styles": {
  "wedding": [
    {"style": "sibarita", "priority": 1},
    {"style": "nuevo_estilo", "priority": 1}
  ]
}
```

**Nota**: Los valores priority más bajos tienen mayor prioridad (1 es máxima prioridad).

### Modificar incompatibilidades de categorías

```json
"incompatible_categories": [
  ["meat", "fish"],
  ["nueva_categoria", "otra_categoria"]
]
```

## Valores válidos

### Sabores (flavors)
- sweet, salty, sour, bitter, umami, fatty, spicy

### Categorías de platos
- soup, cream, broth, salad, vegetable, legume, pasta, rice
- meat, poultry, fish, seafood, egg
- tapas, snack, fruit, pastry, ice_cream

### Estilos culinarios
- classic, modern, fusion, regional, sibarita, gourmet, classical, suave

### Tipos de evento
- wedding, christening, communion, familiar, congress, corporate

### Complejidad
- low, medium, high

### Temporadas
- spring, summer, autumn, winter, all

## Restaurar valores por defecto

Si cometes un error, puedes restaurar los valores originales usando git:

```bash
git checkout config/knowledge_base.json
```
