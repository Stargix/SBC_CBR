# CBR - Sistema de Razonamiento Basado en Casos para Elaboración de Menús
# Práctica SBC - Universidad

"""
Paquete CBR (Case-Based Reasoning) para el sistema de Chef Digital.

Este paquete implementa un sistema de razonamiento basado en casos
para la propuesta de menús de catering personalizados.

Módulos:
- models: Clases de datos (Plato, Bebida, Menu, Caso, Solicitud)
- knowledge: Conocimiento del dominio gastronómico
- case_base: Gestión de la base de casos
- similarity: Funciones de similitud
- retrieve: Fase de recuperación
- adapt: Fase de adaptación/reutilización
- revise: Fase de revisión
- retain: Fase de retención
- explanation: Generación de explicaciones
- case_library: Biblioteca de casos iniciales
- main: Orquestador principal del ciclo CBR

El sistema se inspira en:
- Ferran Adrià (elBulli)
- Juan Mari Arzak (Arzak)
- Paul Bocuse
- René Redzepi (Noma)

Tradiciones culturales soportadas:
- Mediterráneas: Griega, Italiana, Catalana, Vasca, Gallega
- Medio Oriente: Marroquí, Turca, Libanesa
- África: Somalí, Etíope
- Este de Europa: Rusa
"""

__version__ = "1.0.0"

# Modelos de datos
from .models import (
    Dish, Beverage, Menu, Case, Request, ProposedMenu,
    EventType, Season, CulinaryStyle, DishType, DishCategory,
    Temperature, Complexity, Flavor
)

# Conocimiento del dominio
from .knowledge import (
    FLAVOR_COMPATIBILITY,
    INCOMPATIBLE_CATEGORIES,
    WINE_FLAVOR_COMPATIBILITY,
    EVENT_STYLES,
    CULTURAL_CHARACTERISTICS,
    CALORIE_RANGES,
    STYLE_DESCRIPTIONS,
    CHEF_SIGNATURES
)

# Componentes del ciclo CBR
from .case_base import CaseBase
from .similarity import SimilarityCalculator, calculate_menu_similarity
from .retrieve import CaseRetriever
from .adapt import CaseAdapter
from .revise import MenuReviser, ValidationResult
from .retain import CaseRetainer, FeedbackData, RetentionDecision
from .explanation import ExplanationGenerator, ExplanationType, Explanation

# Biblioteca de casos
from .case_library import get_initial_cases

# Sistema principal
from .main import ChefDigitalCBR, CBRConfig, CBRResult, create_cbr_system

__all__ = [
    # Modelos
    'Dish', 'Beverage', 'Menu', 'Case', 'Request', 'ProposedMenu',
    'EventType', 'Season', 'CulinaryStyle', 'DishType', 'DishCategory',
    'Temperature', 'Complexity', 'Flavor',
    # Conocimiento
    'FLAVOR_COMPATIBILITY', 'INCOMPATIBLE_CATEGORIES',
    'WINE_FLAVOR_COMPATIBILITY', 'EVENT_STYLES', 'CULTURAL_CHARACTERISTICS',
    'CALORIE_RANGES', 'STYLE_DESCRIPTIONS', 'CHEF_SIGNATURES',
    # Ciclo CBR
    'CaseBase', 'SimilarityCalculator', 'calculate_menu_similarity',
    'CaseRetriever', 'CaseAdapter', 'MenuReviser', 'ValidationResult',
    'CaseRetainer', 'FeedbackData', 'RetentionDecision',
    'ExplanationGenerator', 'ExplanationType', 'Explanation',
    # Biblioteca
    'get_initial_cases',
    # Sistema principal
    'ChefDigitalCBR', 'CBRConfig', 'CBRResult', 'create_cbr_system',
]
