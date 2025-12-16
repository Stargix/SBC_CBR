"""
Cycle: Fases del ciclo CBR.

- retrieve: Recuperación de casos similares
- adapt: Adaptación de casos al nuevo problema
- revise: Validación y revisión de la solución
- retain: Retención de nuevos casos en la base
- explanation: Generación de explicaciones
"""

from .retrieve import CaseRetriever
from .adapt import CaseAdapter
from .revise import MenuReviser, ValidationResult
from .retain import CaseRetainer, FeedbackData, RetentionDecision
from .explanation import ExplanationGenerator, ExplanationType, Explanation

__all__ = [
    'CaseRetriever', 'CaseAdapter', 'MenuReviser', 'ValidationResult',
    'CaseRetainer', 'FeedbackData', 'RetentionDecision',
    'ExplanationGenerator', 'ExplanationType', 'Explanation'
]
