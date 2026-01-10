"""
Sistema de simulación con LLM (Groq API) para CBR de Chef Digital.
"""

from .llm_simulator import (
    LLMCBRSimulator, 
    LLMSimulationConfig, 
    LLMSimulationResult,
    InteractionResult
)

__all__ = [
    'LLMCBRSimulator',
    'LLMSimulationConfig', 
    'LLMSimulationResult',
    'InteractionResult'
]
