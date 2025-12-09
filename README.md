# Sistema CBR - Chef Digital

## Descripción

Sistema de **Razonamiento Basado en Casos (CBR)** para la propuesta de menús de catering personalizados. Este sistema implementa el paradigma CBR completo (Retrieve-Reuse-Revise-Retain) para generar hasta 3 propuestas de menú adaptadas a las necesidades específicas de cada evento.

## Inspiración Culinaria

El sistema se inspira en grandes figuras de la gastronomía:

- **Ferran Adrià** (elBulli) - Creatividad molecular y texturas innovadoras
- **Juan Mari Arzak** (Arzak) - Cocina vasca de vanguardia
- **Paul Bocuse** - Nouvelle cuisine y tradición francesa
- **René Redzepi** (Noma) - Localismo y productos de temporada

## Tradiciones Culturales Soportadas

### Mediterráneas
- Griega
- Italiana
- Catalana
- Vasca
- Gallega

### Medio Oriente
- Marroquí
- Turca
- Libanesa

### África
- Somalí
- Etíope

### Este de Europa
- Rusa

## Arquitectura del Sistema

```
CBR/
├── __init__.py          # Punto de entrada del paquete
├── models.py            # Modelos de datos (Dish, Menu, Case, Request)
├── knowledge.py         # Conocimiento del dominio gastronómico
├── case_base.py         # Gestión de la base de casos
├── similarity.py        # Funciones de similitud
├── retrieve.py          # Fase RETRIEVE del ciclo CBR
├── adapt.py             # Fase REUSE/ADAPT del ciclo CBR
├── revise.py            # Fase REVISE del ciclo CBR
├── retain.py            # Fase RETAIN del ciclo CBR
├── explanation.py       # Generación de explicaciones
├── case_library.py      # Biblioteca de casos iniciales
├── main.py              # Orquestador principal
└── example_usage.py     # Ejemplos de uso
```

## Ciclo CBR

### 1. RETRIEVE (Recuperar)
Recupera casos similares de la base de conocimiento basándose en:
- Tipo de evento (boda, corporativo, bautizo, etc.)
- Temporada
- Presupuesto
- Estilo culinario preferido
- Restricciones dietéticas

### 2. REUSE/ADAPT (Reutilizar/Adaptar)
Adapta los casos recuperados a los requisitos específicos:
- Sustitución de platos incompatibles
- Ajuste de precios
- Adaptación a restricciones dietéticas
- Cambio de ingredientes por temporada

### 3. REVISE (Revisar)
Valida que las adaptaciones sean coherentes:
- Verificación de restricciones dietéticas
- Control de presupuesto
- Rango calórico adecuado
- Compatibilidad de categorías
- Balance de temperaturas

### 4. RETAIN (Retener)
Aprende de la experiencia:
- Almacena casos exitosos
- Actualiza feedback de clientes
- Mantiene la base de conocimiento

## Uso Básico

```python
from CBR import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle,
    get_initial_cases
)

# Crear sistema CBR
config = CBRConfig(verbose=True, max_proposals=3)
cbr = ChefDigitalCBR(config)

# Cargar casos iniciales
for case in get_initial_cases():
    cbr.case_base.add_case(case)

# Crear solicitud
request = Request(
    event_type=EventType.WEDDING,
    num_guests=100,
    budget=75.0,
    season=Season.SPRING,
    preferred_style=CulinaryStyle.GOURMET,
    dietary_restrictions=["vegetariano"],
    preferences=["elegante", "mediterráneo"]
)

# Procesar solicitud
result = cbr.process_request(request)

# Mostrar explicaciones
print(result.explanations)

# Acceder a menús propuestos
for menu in result.proposed_menus:
    print(f"Menú {menu.rank}: Similitud {menu.similarity_score:.1%}")
```

## Tipos de Eventos Soportados

| Evento | Descripción | Estilos Típicos |
|--------|-------------|-----------------|
| `WEDDING` | Bodas | Gourmet, Sibarita |
| `CORPORATE` | Eventos corporativos | Moderno, Clásico |
| `CONGRESS` | Congresos/Conferencias | Fusion, Moderno |
| `FAMILIAR` | Celebraciones familiares | Regional, Clásico |
| `CHRISTENING` | Bautizos | Regional, Clásico |
| `COMMUNION` | Comuniones | Regional, Gourmet |

## Estilos Culinarios

| Estilo | Chef de Referencia | Características |
|--------|-------------------|-----------------|
| `SIBARITA` | Ferran Adrià | Creatividad, texturas, técnicas moleculares |
| `GOURMET` | Paul Bocuse | Calidad suprema, elegancia |
| `CLASSIC` | Escoffier | Tradición, recetas clásicas |
| `FUSION` | Nobu Matsuhisa | Mezcla de culturas, contrastes |
| `MODERN` | Grant Achatz | Vanguardia, multisensorial |
| `REGIONAL` | Juan Mari Arzak | Productos locales, autenticidad |

## Configuración

```python
config = CBRConfig(
    max_proposals=3,        # Máximo de menús a proponer
    min_similarity=0.3,     # Similitud mínima (0-1)
    enable_learning=True,   # Habilitar aprendizaje
    case_base_path="cases.json",  # Ruta base de casos
    verbose=False           # Modo verbose
)
```

## Explicaciones

El sistema genera explicaciones detalladas:

1. **Por qué se seleccionó** cada menú
2. **Por qué se descartaron** ciertos menús
3. **Qué adaptaciones** se realizaron
4. **Influencia del estilo** culinario elegido
5. **Maridaje** de bebidas

## Ejecutar Demo

```bash
cd /path/to/Final
python -m CBR.example_usage
```

## Dependencias

- Python 3.8+
- Dependencias opcionales:
  - `sentence-transformers` (para similitud semántica avanzada)

## Estructura de un Caso

```python
Case(
    id="case-001",
    request=Request(...),     # Solicitud original
    menu=Menu(...),           # Menú propuesto
    success=True,             # Éxito del caso
    feedback_score=4.5,       # Puntuación (1-5)
    feedback_comments="...",  # Comentarios
    source="expert"           # Fuente del caso
)
```

## Autores

Práctica de Sistemas Basados en Conocimiento (SBC)

## Licencia

Uso académico
