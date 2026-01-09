"""
CBR - Case-Based Reasoning para Sistema de Catering.

Organización de módulos:
- core: Modelos de datos, base de conocimiento, base de casos
- cycle: Fases del ciclo CBR (retrieve, reuse, revise, retain)
- config: Archivos JSON de configuración
"""

from .core.models import (
    Dish, Beverage, Menu, Case, Request, ProposedMenu,
    EventType, Season, CulinaryStyle, DishType, DishCategory,
    Temperature, Complexity, Flavor, CulturalTradition
)

from .core.knowledge import (
    FLAVOR_COMPATIBILITY, INCOMPATIBLE_CATEGORIES,
    WINE_FLAVOR_COMPATIBILITY, EVENT_STYLES, CULTURAL_CHARACTERISTICS,
    CALORIE_RANGES
)

from .core.case_base import CaseBase
from .core.similarity import SimilarityCalculator, calculate_menu_similarity

from .cycle.retrieve import CaseRetriever
from .cycle.adapt import CaseAdapter
from .cycle.revise import MenuReviser, ValidationResult
from .cycle.retain import CaseRetainer, FeedbackData, RetentionDecision
from .cycle.explanation import ExplanationGenerator, ExplanationType, Explanation

from .main import ChefDigitalCBR, CBRConfig, CBRResult, create_cbr_system

__all__ = [
    # Modelos
    'Dish', 'Beverage', 'Menu', 'Case', 'Request', 'ProposedMenu',
    'EventType', 'Season', 'CulinaryStyle', 'DishType', 'DishCategory',
    'Temperature', 'Complexity', 'Flavor', 'CulturalTradition',
    # Conocimiento
    'FLAVOR_COMPATIBILITY', 'INCOMPATIBLE_CATEGORIES',
    'WINE_FLAVOR_COMPATIBILITY', 'EVENT_STYLES', 'CULTURAL_CHARACTERISTICS',
    'CALORIE_RANGES',
    # Ciclo CBR
    'CaseBase', 'SimilarityCalculator', 'calculate_menu_similarity',
    'CaseRetriever', 'CaseAdapter', 'MenuReviser', 'ValidationResult',
    'CaseRetainer', 'FeedbackData', 'RetentionDecision',
    'ExplanationGenerator', 'ExplanationType', 'Explanation',
    # Sistema principal
    'ChefDigitalCBR', 'CBRConfig', 'CBRResult', 'create_cbr_system',
]
