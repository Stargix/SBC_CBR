# DOCUMENTACIÓN DETALLADA - CARPETA CONFIG

## RESUMEN EJECUTIVO

La carpeta `config/` contiene todos los archivos JSON que definen el conocimiento del dominio gastronómico del sistema CBR. Estos archivos permiten modificar y ampliar el conocimiento del sistema sin necesidad de cambiar código Python. Son la base de datos declarativa del sistema.

---

## 📁 ESTRUCTURA DE LA CARPETA CONFIG

```
config/
├── __init__.py                  # Módulo Python vacío
├── knowledge_base.json          # Reglas gastronómicas y compatibilidades
├── dishes.json                  # Catálogo de 25 platos disponibles
├── beverages.json               # Catálogo de 17 bebidas disponibles
└── initial_cases.json           # 10 casos iniciales de ejemplo
```

---

## 1. knowledge_base.json

**Propósito**: Define las reglas gastronómicas, compatibilidades y conocimiento experto del dominio culinario.

### 1.1 Estructura del archivo

#### A) flavor_compatibility
Define qué sabores son compatibles entre sí para crear armonía gastronómica.

```json
{
    "flavor_compatibility": {
        "sweet": ["salty", "sour"],
        "salty": ["sweet", "umami", "fatty"],
        "sour": ["fatty", "sweet", "umami"],
        "bitter": ["sweet", "umami", "fatty"],
        "umami": ["sour", "bitter"],
        "fatty": ["sour", "bitter"],
        "spicy": ["sweet", "fatty", "sour"]
    }
}
```

**Uso en el sistema**:
- Durante la fase REVISE, valida que los sabores de diferentes platos sean compatibles
- Evita combinaciones que generen conflictos gustativos
- Ejemplo: Un entrante dulce puede seguirse de un plato salado (compatible), pero no de uno muy amargo

**Sabores definidos**:
- `sweet` (dulce): Compatible con salado y ácido
- `salty` (salado): Compatible con dulce, umami y graso
- `sour` (ácido): Compatible con graso, dulce y umami
- `bitter` (amargo): Compatible con dulce, umami y graso
- `umami`: Compatible con ácido y amargo
- `fatty` (graso): Compatible con ácido y amargo
- `spicy` (picante): Compatible con dulce, graso y ácido

#### B) incompatible_categories
Define categorías de platos que no deben aparecer juntas en el mismo menú.

```json
{
    "incompatible_categories": [
        ["soup", "cream"],
        ["soup", "broth"],
        ["cream", "broth"],
        ["legume", "pasta"],
        ["legume", "rice"],
        ["pasta", "rice"],
        ["meat", "fish"],
        ["meat", "seafood"],
        ["fish", "poultry"]
    ]
}
```

**Razones de incompatibilidad**:
- **Sopas/Cremas/Caldos**: Muy similar en textura y presentación
- **Legumbres/Pasta/Arroz**: Demasiado carbohidrato en un solo menú
- **Carne/Pescado/Pollo**: Proteínas principales que no se mezclan en alta gastronomía

**Uso en el sistema**:
- Validación durante REVISE
- Filtrado durante ADAPT para buscar alternativas
- Ejemplo: Si el entrante es sopa, el plato principal no puede ser una crema

#### C) wine_flavor_compatibility
Define qué tipos de vino maridan bien con qué sabores de platos.

```json
{
    "wine_flavor_compatibility": {
        "dry": ["salty", "sour", "fatty"],
        "fruity": ["sweet", "umami"],
        "full-bodied": ["fatty", "umami", "bitter"],
        "young": ["salty", "sour"],
        "aged": ["fatty", "umami", "bitter"],
        "sweet": ["sweet", "fatty"],
        "sparkling": ["salty", "sweet", "sour"],
        "rose": ["sweet", "sour", "salty"]
    }
}
```

**Reglas de maridaje**:
- **Vinos secos (dry)**: Carnes saladas, pescados ácidos, platos grasos
- **Vinos frutales (fruity)**: Platos dulces o umami
- **Vinos con cuerpo (full-bodied)**: Carnes grasas, sabores intensos
- **Vinos jóvenes (young)**: Platos frescos, salados o ácidos
- **Vinos envejecidos (aged)**: Platos complejos con grasa o umami
- **Vinos dulces (sweet)**: Postres y platos grasos
- **Espumosos (sparkling)**: Versátiles, funcionan con muchos sabores
- **Rosados (rose)**: Equilibrados, versátiles

**Uso en el sistema**:
- Durante ADAPT para seleccionar bebidas apropiadas
- Validación en REVISE del maridaje
- Regla especial: Postres priorizan vinos dulces y espumosos

#### D) event_styles
Define qué estilos culinarios son apropiados para cada tipo de evento, con prioridades.

```json
{
    "event_styles": {
        "wedding": [
            {"style": "gourmet", "priority": 1},
            {"style": "sibarita", "priority": 2},
            {"style": "classic", "priority": 3},
            {"style": "modern", "priority": 4}
        ],
        "communion": [
            {"style": "classic", "priority": 1},
            {"style": "regional", "priority": 2},
            {"style": "modern", "priority": 3}
        ],
        "christening": [
            {"style": "regional", "priority": 1},
            {"style": "classic", "priority": 2},
            {"style": "suave", "priority": 3}
        ],
        "familiar": [
            {"style": "regional", "priority": 1},
            {"style": "classic", "priority": 2},
            {"style": "suave", "priority": 3}
        ],
        "congress": [
            {"style": "modern", "priority": 1},
            {"style": "fusion", "priority": 2},
            {"style": "classic", "priority": 3}
        ],
        "corporate": [
            {"style": "modern", "priority": 1},
            {"style": "classic", "priority": 2},
            {"style": "fusion", "priority": 3}
        ]
    }
}
```

**Lógica de prioridades**:
- `priority: 1` = Estilo más recomendado
- `priority: 2` = Alternativa buena
- `priority: 3-4` = Aceptable pero no ideal

**Interpretación por evento**:
- **Bodas**: Requieren sofisticación (gourmet/sibarita)
- **Comuniones/Bautizos**: Preferencia por lo tradicional y familiar
- **Familiares**: Cocina regional, casera, reconfortante
- **Congresos/Corporativos**: Modernos, ejecutivos, equilibrados

**Uso en el sistema**:
- RETRIEVE: Filtra casos por estilo apropiado
- ADAPT: Sugiere cambios de estilo si no es apropiado
- REVISE: Valida que el estilo sea adecuado

#### E) event_complexity
Define qué niveles de complejidad de elaboración son apropiados por evento.

```json
{
    "event_complexity": {
        "wedding": ["medium", "high"],
        "communion": ["low", "medium"],
        "christening": ["low", "medium"],
        "familiar": ["low", "medium"],
        "congress": ["medium", "high"],
        "corporate": ["medium"]
    }
}
```

**Niveles de complejidad**:
- `low`: Platos sencillos, tradicionales, rápidos
- `medium`: Elaboración estándar de restauración
- `high`: Alta cocina, técnicas avanzadas, presentación elaborada

**Uso en el sistema**:
- Filtrado durante RETRIEVE
- Validación en REVISE
- Regla especial: Bodas con bajo presupuesto (<50€) evitan alta complejidad

---

## 2. dishes.json

**Propósito**: Catálogo completo de los 25 platos disponibles en el sistema.

### 2.1 Estructura de un plato

Cada plato tiene esta estructura JSON:

```json
{
    "id": "identificador-unico",
    "name": "Nombre Completo del Plato",
    "dish_type": "starter|main_course|dessert",
    "price": 21.0,
    "category": "soup|salad|meat|fish|...",
    "styles": ["classic", "modern", "fusion", ...],
    "seasons": ["spring", "summer", "autumn", "winter", "all"],
    "temperature": "hot|warm|cold",
    "complexity": "low|medium|high",
    "calories": 300,
    "max_guests": 400,
    "flavors": ["sweet", "salty", "sour", ...],
    "diets": ["vegetarian", "vegan", "gluten-free", ...],
    "ingredients": ["ingredient1", "ingredient2", ...],
    "compatible_beverages": ["wine-id", "tea-id", ...],
    "cultural_traditions": ["mediterranean", "catalan", ...]
}
```

### 2.2 Campos explicados

#### Identificación
- **id**: Identificador único (kebab-case)
- **name**: Nombre descriptivo del plato
- **dish_type**: Posición en el menú
  - `starter`: Entrante
  - `main_course`: Plato principal
  - `dessert`: Postre

#### Atributos económicos
- **price**: Precio por persona en euros
- **max_guests**: Capacidad máxima de servicio

#### Clasificación gastronómica
- **category**: Tipo de plato
  - Entrantes: `soup`, `cream`, `broth`, `salad`, `tapas`, `snack`
  - Principales: `meat`, `poultry`, `fish`, `seafood`, `pasta`, `rice`, `legume`, `vegetable`, `egg`
  - Postres: `fruit`, `pastry`, `ice_cream`

- **styles**: Estilos culinarios asociados (puede tener varios)
  - `classic`: Cocina clásica tradicional
  - `modern`: Cocina moderna/contemporánea
  - `fusion`: Fusión de tradiciones
  - `regional`: Cocina regional/local
  - `sibarita`: Alta cocina, molecular
  - `gourmet`: Cocina gourmet refinada
  - `classical`: Nouvelle cuisine
  - `suave`: Cocina suave, familiar

- **cultural_traditions**: Influencias culturales
  - `mediterranean`, `catalan`, `basque`, `galician`, `spanish`
  - `italian`, `french`, `greek`, `nordic`
  - `moroccan`, `turkish`, `lebanese`
  - `japanese`, `mexican`, `russian`

#### Atributos temporales y físicos
- **seasons**: Temporadas en que está disponible
  - `spring`, `summer`, `autumn`, `winter`, `all`
  - Basado en disponibilidad de ingredientes de temporada

- **temperature**: Temperatura de servicio
  - `hot`: Caliente (ej: sopas de invierno)
  - `warm`: Templado (ej: platos principales)
  - `cold`: Frío (ej: ensaladas, gazpachos)

- **complexity**: Dificultad de elaboración
  - `low`: Sencillo, rápido
  - `medium`: Elaboración estándar
  - `high`: Alta cocina, técnicas avanzadas

#### Atributos nutricionales y dietéticos
- **calories**: Calorías aproximadas por ración
- **flavors**: Sabores principales (múltiples posibles)
  - `sweet`, `salty`, `sour`, `bitter`, `umami`, `fatty`, `spicy`

- **diets**: Dietas compatibles (filtro crítico)
  - `vegetarian`: Sin carne ni pescado
  - `vegan`: Sin productos animales
  - `pescatarian`: Solo pescado (no carne)
  - `dairy-free`: Sin lácteos
  - `gluten-free`: Sin gluten
  - `wheat-free`: Sin trigo
  - `egg-free`: Sin huevo

- **ingredients**: Lista de ingredientes principales
  - Usado para detectar restricciones (ej: "nuts" para alérgicos)

- **compatible_beverages**: IDs de bebidas que maridan bien

### 2.3 Ejemplos de platos representativos

#### Entrante de lujo
```json
{
    "id": "foie-gras-terrine",
    "name": "Foie Gras Terrine",
    "dish_type": "starter",
    "price": 45.0,
    "category": "snack",
    "styles": ["sibarita", "gourmet"],
    "seasons": ["autumn", "winter"],
    "temperature": "cold",
    "complexity": "high",
    "calories": 462,
    "flavors": ["fatty", "umami"],
    "diets": ["pescatarian"],
    "ingredients": ["foie-gras", "butter", "cognac", "salt", "pepper"]
}
```

#### Plato principal económico
```json
{
    "id": "whole-chicken-cabbage",
    "name": "Whole Chicken in Cabbage",
    "dish_type": "main_course",
    "price": 19.0,
    "category": "poultry",
    "styles": ["regional", "classic"],
    "seasons": ["winter"],
    "temperature": "hot",
    "complexity": "medium",
    "calories": 443,
    "flavors": ["salty", "umami"],
    "diets": ["dairy-free", "gluten-free"]
}
```

#### Postre vegetariano
```json
{
    "id": "crema-catalana",
    "name": "Crema Catalana",
    "dish_type": "dessert",
    "price": 8.0,
    "category": "pastry",
    "styles": ["regional", "classic"],
    "seasons": ["all"],
    "temperature": "cold",
    "complexity": "medium",
    "calories": 320,
    "flavors": ["sweet"],
    "diets": ["vegetarian", "gluten-free"],
    "cultural_traditions": ["catalan"]
}
```

### 2.4 Distribución del catálogo

**Por tipo** (dish_type):
- Entrantes (starter): ~8 platos
- Principales (main_course): ~10 platos  
- Postres (dessert): ~7 platos
- **Total: 25 platos**

**Por rango de precio**:
- Económico (<20€): ~8 platos
- Medio (20-40€): ~12 platos
- Premium (>40€): ~5 platos

**Por temporada**:
- All seasons: ~10 platos (disponibles siempre)
- Primavera/Verano: ~6 platos (frescos, ligeros)
- Otoño/Invierno: ~9 platos (contundentes, calientes)

**Uso en el sistema**:
- Cargado al inicializar `CaseBase`
- Accesible mediante `case_base.dishes[dish_id]`
- Búsqueda por tipo: `case_base.get_dishes_by_type(DishType.STARTER)`
- Durante ADAPT para buscar alternativas compatibles con restricciones

---

## 3. beverages.json

**Propósito**: Catálogo completo de las 17 bebidas disponibles.

### 3.1 Estructura de una bebida

```json
{
    "id": "identificador-unico",
    "name": "Nombre de la Bebida",
    "alcoholic": true|false,
    "price": 4.5,
    "styles": ["white-wine", "red-wine", "herbal-tea", "soft-drink"],
    "subtype": "dry|fruity|young|aged|sparkling|sweet|...",
    "compatible_flavors": ["salty", "sour", "fatty"]
}
```

### 3.2 Campos explicados

#### Identificación y precio
- **id**: Identificador único
- **name**: Nombre comercial o descriptivo
- **price**: Precio por persona en euros
- **alcoholic**: Booleano indicando si contiene alcohol

#### Clasificación
- **styles**: Categoría principal de bebida
  - `white-wine`: Vino blanco
  - `red-wine`: Vino tinto
  - `rose-wine`: Vino rosado
  - `cava`: Cava/espumoso
  - `herbal-tea`: Infusión/té
  - `soft-drink`: Refresco/agua

- **subtype**: Características específicas del vino
  - Blancos: `dry` (seco), `fruity` (afrutado)
  - Tintos: `young` (joven), `aged` (crianza/reserva), `full-bodied` (con cuerpo)
  - Cavas: `brut-nature` (seco), `semi-seco` (medio)
  - Otros: `none` (no aplica)

- **compatible_flavors**: Sabores con los que marida bien
  - Usado para maridaje automático en ADAPT

### 3.3 Catálogo de bebidas

#### Bebidas sin alcohol (6 bebidas)
```json
// Infusiones (precio: 1.8-3.0€)
{"id": "chamomile-infusion", "name": "Chamomile Infusion"}
{"id": "green-tea-mint", "name": "Green Tea with Mint"}
{"id": "ginger-lemon-blend", "name": "Ginger Lemon Blend"}

// Refrescos (precio: 1.5-3.0€)
{"id": "sparkling-water", "name": "Sparkling Water"}
{"id": "still-water", "name": "Still Mineral Water"}
{"id": "lemonade", "name": "Fresh Lemonade"}
```

#### Vinos blancos (4 vinos, precio: 4.0-5.0€)
```json
{"id": "cloudy-bay-sauvignon", "subtype": "dry", "compatible_flavors": ["salty", "sour", "fatty"]}
{"id": "albarino-rias-baixas", "subtype": "fruity", "compatible_flavors": ["sweet", "umami"]}
{"id": "verdejo-rueda", "subtype": "dry"}
{"id": "albariño-martin-codax", "subtype": "fruity"}
```

#### Vinos tintos (4 vinos, precio: 4.5-6.5€)
```json
{"id": "rioja-reserva", "subtype": "aged", "compatible_flavors": ["fatty", "umami", "bitter"]}
{"id": "ribera-duero-crianza", "subtype": "full-bodied"}
{"id": "priorat-garnacha", "subtype": "full-bodied"}
{"id": "somontano-tempranillo", "subtype": "young"}
```

#### Vinos rosados (1 vino, precio: 4.0€)
```json
{"id": "provence-rose", "subtype": "rose", "compatible_flavors": ["sweet", "sour", "salty"]}
```

#### Cavas (2 cavas, precio: 5.0-6.0€)
```json
{"id": "cava-brut-nature", "subtype": "sparkling"}
{"id": "cava-semi-seco", "subtype": "sparkling"}
```

### 3.4 Uso en el sistema

**Carga inicial**:
```python
case_base = CaseBase()
# Automáticamente carga beverages.json
beverage = case_base.beverages["rioja-reserva"]
```

**Durante ADAPT**:
- Filtrado por preferencia de alcohol: `case_base.get_compatible_beverages(wants_wine=True)`
- Maridaje automático basado en `compatible_flavors` y sabores del menú
- Priorización de vinos según contexto (postres → dulces/espumosos)

**Durante REVISE**:
- Validación de maridaje correcto
- Verificación de coherencia de precio con el menú

**Reglas especiales**:
- Postres priorizan vinos dulces o espumosos
- Eventos familiares pueden no tener alcohol
- Bodas y eventos corporativos suelen incluir vino

---

## 4. initial_cases.json

**Propósito**: 10 casos iniciales pre-definidos para poblar la base de conocimiento al inicio.

### 4.1 Estructura de un caso inicial

```json
{
    "event": "wedding|communion|christening|familiar|congress|corporate",
    "season": "spring|summer|autumn|winter|all",
    "price_min": 80,
    "price_max": 150,
    "starter": "dish-id",
    "main": "dish-id",
    "dessert": "dish-id",
    "beverage": "beverage-id",
    "style": "gourmet|sibarita|classic|modern|regional|fusion|classical|suave",
    "culture": "mediterranean|catalan|italian|...",
    "success": true,
    "feedback": 4.8
}
```

### 4.2 Campos explicados

#### Contexto del caso
- **event**: Tipo de evento para el que fue usado
- **season**: Temporada en que se celebró
- **price_min/price_max**: Rango de presupuesto del cliente (€/persona)

#### Solución (Menú)
- **starter**: ID del plato entrante
- **main**: ID del plato principal
- **dessert**: ID del postre
- **beverage**: ID de la bebida/maridaje

#### Atributos del menú
- **style**: Estilo culinario dominante del menú
- **culture**: Tradición cultural (opcional)

#### Feedback histórico
- **success**: Si el caso fue exitoso (booleano)
- **feedback**: Puntuación del cliente (escala 1-5)

### 4.3 Los 10 casos iniciales

#### Caso 1: Boda Gourmet Verano
```json
{
    "event": "wedding",
    "season": "summer",
    "price_min": 80, "price_max": 150,
    "starter": "ceviche-peruano",
    "main": "grilled-sea-bass",
    "dessert": "fresh-fruit-platter",
    "beverage": "cava-brut-nature",
    "style": "gourmet",
    "success": true,
    "feedback": 4.8
}
```
**Características**: Menú fresco, marinero, alta calidad. Ideal para bodas sofisticadas en verano.

#### Caso 2: Boda Sibarita Otoño
```json
{
    "event": "wedding",
    "season": "autumn",
    "price_min": 100, "price_max": 180,
    "starter": "foie-gras-terrine",
    "main": "beef-wellington",
    "dessert": "chocolate-fondant",
    "beverage": "rioja-reserva",
    "style": "sibarita",
    "success": true,
    "feedback": 4.9
}
```
**Características**: Alta cocina, ingredientes premium, presentación elaborada. El caso más lujoso.

#### Caso 3: Comunión Clásica Primavera
```json
{
    "event": "communion",
    "season": "spring",
    "price_min": 40, "price_max": 70,
    "starter": "mediterranean-bruschetta",
    "main": "moroccan-chicken-tagine",
    "dessert": "tiramisu-classic",
    "beverage": "lemonade",
    "style": "classic",
    "success": true,
    "feedback": 4.5
}
```
**Características**: Familiar, sin alcohol, sabores reconocibles, precio medio.

#### Caso 4: Bautizo Regional Primavera
```json
{
    "event": "christening",
    "season": "spring",
    "price_min": 35, "price_max": 60,
    "starter": "gazpacho-andaluz",
    "main": "cordero-asado",
    "dessert": "tarta-santiago",
    "beverage": "verdejo-rueda",
    "style": "regional",
    "success": true,
    "feedback": 4.6
}
```
**Características**: Cocina española tradicional, familiar, reconfortante.

#### Caso 5: Familiar Regional Invierno
```json
{
    "event": "familiar",
    "season": "winter",
    "price_min": 25, "price_max": 45,
    "starter": "carrot-ginger-soup",
    "main": "whole-chicken-cabbage",
    "dessert": "crema-catalana",
    "beverage": "still-water",
    "style": "regional",
    "success": true,
    "feedback": 4.3
}
```
**Características**: Económico, contundente, sin alcohol, perfecto para familia.

#### Caso 6: Congreso Moderno Todo Año
```json
{
    "event": "congress",
    "season": "all",
    "price_min": 50, "price_max": 80,
    "starter": "skinny-tangy-smoked-salmon-salad",
    "main": "risotto-funghi",
    "dessert": "tiramisu-classic",
    "beverage": "albarino-rias-baixas",
    "style": "modern",
    "success": true,
    "feedback": 4.4
}
```
**Características**: Ejecutivo, equilibrado, sabores internacionales.

#### Caso 7: Corporativo Clásico Todo Año
```json
{
    "event": "corporate",
    "season": "all",
    "price_min": 45, "price_max": 75,
    "starter": "mediterranean-bruschetta",
    "main": "grilled-sea-bass",
    "dessert": "cheesecake-ice-cream",
    "beverage": "cloudy-bay-sauvignon",
    "style": "classic",
    "success": true,
    "feedback": 4.5
}
```
**Características**: Profesional, seguro, sabores universales.

#### Caso 8-10: (Casos adicionales siguiendo patrones similares)

### 4.4 Distribución estratégica

**Por tipo de evento**:
- Weddings: 3 casos (diferentes estilos y temporadas)
- Communion: 1 caso
- Christening: 1 caso  
- Familiar: 1 caso
- Congress: 1 caso
- Corporate: 1 caso
- **Otros eventos**: 2 casos adicionales

**Por rango de precio**:
- Económico (<40€): 2 casos
- Medio (40-80€): 5 casos
- Premium (>80€): 3 casos

**Por temporada**:
- Todo el año: 3 casos
- Primavera: 2 casos
- Verano: 1 caso
- Otoño: 2 casos
- Invierno: 2 casos

**Por estilo**:
- Classic: 2 casos
- Regional: 2 casos
- Gourmet: 1 caso
- Sibarita: 1 caso
- Modern: 2 casos
- Otros: 2 casos

### 4.5 Proceso de carga en el sistema

```python
# En CaseBase.__init__()
def _generate_initial_cases(self):
    menu_templates = self._load_initial_cases_from_json()
    
    for i, template in enumerate(menu_templates):
        # Crear objetos Dish, Beverage
        starter = self.dishes.get(template["starter"])
        main = self.dishes.get(template["main"])
        dessert = self.dishes.get(template["dessert"])
        beverage = self.beverages.get(template["beverage"])
        
        # Crear Menu
        menu = Menu(
            id=f"menu-init-{i+1}",
            starter=starter,
            main_course=main,
            dessert=dessert,
            beverage=beverage,
            dominant_style=CulinaryStyle(template["style"])
        )
        
        # Crear Request
        request = Request(
            event_type=EventType(template["event"]),
            season=Season(template["season"]),
            price_min=template["price_min"],
            price_max=template["price_max"]
        )
        
        # Crear Case
        case = Case(
            id=f"case-init-{i+1}",
            request=request,
            menu=menu,
            success=template["success"],
            feedback_score=template["feedback"],
            source="initial"
        )
        
        self.add_case(case)
```

### 4.6 Propósito de los casos iniciales

1. **Bootstrap del sistema**: Sin casos iniciales, el sistema no tendría experiencia previa
2. **Cobertura diversa**: Cubren diferentes eventos, presupuestos y estilos
3. **Calidad garantizada**: Todos tienen feedback positivo (>4.0)
4. **Base para RETRIEVE**: Puntos de partida para encontrar casos similares
5. **Ejemplos de excelencia**: Representan menús exitosos validados

---

## 5. __init__.py

**Propósito**: Archivo vacío que convierte `config/` en un módulo Python.

**Contenido**: Vacío (0 bytes)

**Función**: Permite hacer imports como:
```python
from develop.config import knowledge_base
```

Aunque en la práctica, los archivos JSON se cargan directamente desde los módulos `core/`.

---

## RESUMEN DE INTERCONEXIONES

### Flujo de datos en el sistema

```
┌─────────────────────────────────────────────────────────────┐
│ INICIALIZACIÓN DEL SISTEMA                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────┐
    │ CaseBase.__init__()                           │
    │                                               │
    │ 1. Cargar dishes.json → self.dishes          │
    │ 2. Cargar beverages.json → self.beverages    │
    │ 3. Cargar initial_cases.json                 │
    │    → Crear 10 objetos Case                   │
    │ 4. Indexar casos por evento/precio/estilo    │
    └───────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────┐
    │ knowledge.py carga knowledge_base.json        │
    │                                               │
    │ - FLAVOR_COMPATIBILITY                        │
    │ - INCOMPATIBLE_CATEGORIES                     │
    │ - WINE_FLAVOR_COMPATIBILITY                   │
    │ - EVENT_STYLES                                │
    │ - EVENT_COMPLEXITY                            │
    └───────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────┐
            │ SISTEMA LISTO PARA USAR  │
            └───────────────────────────┘
```

### Uso durante el ciclo CBR

```
RETRIEVE (Recuperación)
├── Usa: initial_cases.json (casos base)
├── Usa: knowledge_base.json (event_styles)
└── Compara con: dishes.json atributos

ADAPT (Adaptación)
├── Usa: dishes.json (buscar alternativas)
├── Usa: beverages.json (maridaje)
├── Usa: knowledge_base.json (compatibilidades)
└── Filtra por: diets, ingredients, price

REVISE (Validación)
├── Usa: knowledge_base.json (todas las reglas)
│   ├── flavor_compatibility
│   ├── incompatible_categories
│   ├── wine_flavor_compatibility
│   ├── event_complexity
│   └── temperature_by_season
└── Valida: restricciones, presupuesto, balance

RETAIN (Aprendizaje)
├── Guarda: nuevos casos en memoria
├── Persiste: en archivo JSON (opcional)
└── Mantiene: límite de casos por evento
```

---

## CONSIDERACIONES TÉCNICAS

### Formato JSON
- Todos los archivos usan UTF-8 encoding
- Indentación de 2 o 4 espacios
- Sin comentarios (JSON puro)

### Validación
- Los IDs deben ser únicos dentro de cada archivo
- Las referencias (ej: compatible_beverages) deben existir
- Los valores enum deben coincidir con las clases Python

### Extensibilidad
Para añadir contenido:

1. **Nuevo plato**: Añadir objeto a `dishes.json`
2. **Nueva bebida**: Añadir objeto a `beverages.json`
3. **Nuevo caso inicial**: Añadir objeto a `initial_cases.json`
4. **Nueva regla**: Añadir a `knowledge_base.json`

No requiere cambios en código Python, solo reiniciar el sistema.

### Mantenimiento
- Los archivos se pueden editar manualmente
- Se recomienda validar el JSON después de cambios
- Hacer backup antes de modificaciones importantes

---

## CONCLUSIÓN

Los archivos de configuración en `config/` son el **corazón declarativo** del sistema CBR. Permiten:

✅ **Separación clara**: Conocimiento separado de lógica  
✅ **Fácil mantenimiento**: Modificar sin tocar código  
✅ **Escalabilidad**: Añadir platos/bebidas/casos fácilmente  
✅ **Transparencia**: Reglas explícitas y auditables  
✅ **Flexibilidad**: Adaptar a diferentes contextos gastronómicos  

Esta arquitectura sigue el principio de **"datos sobre código"**, facilitando la evolución del sistema sin requerir conocimientos de programación para ajustes básicos.

