# CBR/develop - Sistema de Catering CBR

Implementación modular del sistema CBR para catering.

## 📁 Estructura

```
develop/
├── config/                   # Configuración JSON
│   ├── knowledge_base.json   # Reglas de compatibilidad
│   ├── dishes.json           # 25 platos
│   ├── beverages.json        # 17 bebidas
│   └── initial_cases.json    # 10 casos iniciales
├── core/                     # Componentes fundamentales
│   ├── models.py             # Dataclasses y enums
│   ├── knowledge.py          # Base de conocimiento
│   ├── case_base.py          # Gestión de casos
│   └── similarity.py         # Cálculo de similitudes
├── cycle/                    # Ciclo CBR
│   ├── retrieve.py           # Fase 1: Recuperación
│   ├── adapt.py              # Fase 2: Adaptación
│   ├── revise.py             # Fase 3: Revisión
│   ├── retain.py             # Fase 4: Retención
│   └── explanation.py        # Generación de explicaciones
├── main.py                   # Orquestador principal
├── example.py                # Ejemplo de uso
└── __init__.py               # Exportaciones del módulo
```

## 🚀 Uso

### Desde dentro de develop/

```bash
cd CBR/develop
python example.py
```

### Como módulo Python

```python
from CBR.develop import ChefDigitalCBR, CBRConfig, Request, EventType, Season

# Configurar sistema
config = CBRConfig(verbose=False, max_proposals=3)
cbr = ChefDigitalCBR(config)

# Crear solicitud
request = Request(
    event_type=EventType.WEDDING,
    num_guests=100,
    price_max=80.0,
    season=Season.SPRING
)

# Procesar
result = cbr.process_request(request)
print(result.explanations)
```

## 📝 Configuración

Todos los datos están en archivos JSON en `config/`:

- **knowledge_base.json**: Compatibilidades, maridajes, estilos
- **dishes.json**: Catálogo de platos con atributos
- **beverages.json**: Catálogo de bebidas
- **initial_cases.json**: Casos de ejemplo

## 🔄 Ciclo CBR

1. **RETRIEVE** (`cycle/retrieve.py`): Busca casos similares
2. **ADAPT** (`cycle/adapt.py`): Adapta el caso al nuevo problema
3. **REVISE** (`cycle/revise.py`): Valida la solución
4. **RETAIN** (`cycle/retain.py`): Aprende de la experiencia

## ✨ Características

- ✅ 10 casos iniciales pre-cargados
- ✅ 25 platos y 17 bebidas
- ✅ 6 tipos de eventos
- ✅ 8 estilos culinarios
- ✅ Sin dependencias externas
