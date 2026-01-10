"""
Script para ejecutar simulación CBR con LLM (Groq API).

Uso:
    python simulation/run_llm_simulation.py
    python simulation/run_llm_simulation.py -n 10
    python simulation/run_llm_simulation.py --adaptive
    python simulation/run_llm_simulation.py --static
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Cargar variables de entorno desde .env en raíz del proyecto
load_dotenv(Path(__file__).parent.parent / '.env')

sys.path.append(str(Path(__file__).parent.parent))

from simulation.llm_simulator import LLMCBRSimulator, LLMSimulationConfig


def main():
    parser = argparse.ArgumentParser(
        description="Simulador CBR con LLM (Groq API) para evaluación automatizada"
    )
    
    parser.add_argument(
        '-n', '--num-interactions',
        type=int,
        default=5,
        help='Número de interacciones a simular (default: 5)'
    )
    
    parser.add_argument(
        '--adaptive',
        action='store_true',
        help='Habilitar adaptive weights (default: True)'
    )
    
    parser.add_argument(
        '--static',
        action='store_true',
        help='Deshabilitar adaptive weights'
    )
    
    parser.add_argument(
        '-t', '--temperature',
        type=float,
        default=0.9,
        help='Temperatura para generación de LLM (default: 0.9)'
    )
    
    parser.add_argument(
        '-m', '--model',
        type=str,
        default='llama-3.3-70b-versatile',
        help='Modelo de Groq a usar (default: llama-3.3-70b-versatile)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/llm_simulation_results.json',
        help='Ruta para guardar resultados (default: data/llm_simulation_results.json)'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Modo silencioso (sin verbose)'
    )
    
    args = parser.parse_args()
    
    # Verificar API key
    if not os.environ.get("GROQ_API_KEY"):
        print("⚠ ERROR: GROQ_API_KEY no encontrada.")
        print("\nConfigura la variable de entorno:")
        print("  export GROQ_API_KEY='tu_api_key_aqui'")
        print("\nO crea archivo .env con:")
        print("  GROQ_API_KEY=tu_api_key_aqui")
        sys.exit(1)
    
    # Determinar si usar adaptive weights
    enable_adaptive = not args.static if args.static else True
    
    # Configurar simulación
    config = LLMSimulationConfig(
        model_name=args.model,
        num_interactions=args.num_interactions,
        enable_adaptive_weights=enable_adaptive,
        temperature=args.temperature,
        verbose=not args.quiet,
        results_path=args.output
    )
    
    print(f"\n{'='*70}")
    print("LLM CBR SIMULATOR (Groq API)")
    print('='*70)
    print(f"Modelo: {config.model_name}")
    print(f"Interacciones: {config.num_interactions}")
    print(f"Adaptive Weights: {'✅' if config.enable_adaptive_weights else '❌'}")
    print(f"Temperature: {config.temperature}")
    print(f"Output: {config.results_path}")
    print('='*70)
    
    try:
        # Crear y ejecutar simulador
        simulator = LLMCBRSimulator(config)
        result = simulator.run_simulation()
        
        print("\n✅ Simulación completada exitosamente!")
        print(f"\n📊 Resultados guardados en: {config.results_path}")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Simulación interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error durante la simulación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
