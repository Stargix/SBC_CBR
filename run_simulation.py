#!/usr/bin/env python3
"""
Script simple para ejecutar simulaciones CBR con LLM (Groq API).
Permite especificar el número de iteraciones de forma directa.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env en raíz del proyecto
load_dotenv(Path(__file__).parent / '.env')

# Verificar API key
if not os.environ.get("GROQ_API_KEY"):
    print("⚠ ERROR: GROQ_API_KEY no encontrada.")
    print("\nConfigura la variable de entorno:")
    print("  export GROQ_API_KEY='tu_api_key_aqui'")
    print("\nO crea un archivo .env con:")
    print("  GROQ_API_KEY=tu_api_key_aqui")
    exit(1)

from simulation.llm_simulator import LLMCBRSimulator, LLMSimulationConfig


def run_simulation(num_iterations: int = 5, 
                   enable_learning: bool = True,
                   verbose: bool = True,
                   output_file: str = "data/llm_simulation_results.json"):
    """
    Ejecuta una simulación CBR con el LLM (Groq API).
    
    Args:
        num_iterations: Número de solicitudes a simular
        enable_learning: Activar aprendizaje adaptativo de pesos
        verbose: Mostrar información detallada
        output_file: Ruta donde guardar resultados JSON
    """
    
    print(f"🚀 Iniciando simulación CBR con {num_iterations} iteraciones...")
    print(f"📊 Aprendizaje adaptativo: {'✅' if enable_learning else '❌'}")
    print()
    
    # Configurar simulación
    config = LLMSimulationConfig(
        num_interactions=num_iterations,
        enable_adaptive_weights=enable_learning,
        verbose=verbose,
        temperature=0.9,
        results_path=output_file
    )
    
    # Ejecutar
    simulator = LLMCBRSimulator(config)
    result = simulator.run_simulation()
    
    # Resumen final
    print("\n" + "="*70)
    print("✅ SIMULACIÓN COMPLETADA")
    print("="*70)
    print(f"Total solicitudes: {result.total_requests}")
    print(f"Propuestas exitosas: {result.successful_proposals}")
    print(f"Puntuación promedio LLM: {result.llm_score:.2f}/5.0")
    print(f"Duración: {result.duration_seconds:.1f} segundos")
    print(f"Resultados guardados: {output_file}")
    print("="*70)
    
    return result


if __name__ == "__main__":
    # ===================================================================
    # CONFIGURACIÓN: Modifica estos valores según tus necesidades
    # ===================================================================

    NUM_ITERACIONES = 5  # Valor por defecto
    while True:
        num_iter = input("Número de iteraciones a simular (default 5): ")
        if not num_iter:  # Si presiona Enter sin ingresar nada
            break
        try:
            NUM_ITERACIONES = int(num_iter)
            break
        except ValueError:
            print("Número no válido")
    
    APRENDIZAJE_ACTIVO = True      # ¿Activar aprendizaje adaptativo?
    VERBOSE = True                 # ¿Mostrar detalles durante ejecución?
    
    # ===================================================================
    
    result = run_simulation(
        num_iterations=NUM_ITERACIONES,
        enable_learning=APRENDIZAJE_ACTIVO,
        verbose=VERBOSE
    )
