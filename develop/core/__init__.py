"""
Core: Módulos fundamentales del sistema CBR.

- models: Dataclasses y enums del dominio
- knowledge: Base de conocimiento (compatibilidades, reglas)
- case_base: Almacenamiento y gestión de casos
- similarity: Cálculo de similitudes entre casos
"""

from .models import *
from .knowledge import *
from .case_base import CaseBase
from .similarity import SimilarityCalculator, calculate_menu_similarity

__all__ = [
    'Dish', 'Beverage', 'Menu', 'Case', 'Request',
    'EventType', 'Season', 'CulinaryStyle', 'DishType',
    'CaseBase', 'SimilarityCalculator', 'calculate_menu_similarity'
]
