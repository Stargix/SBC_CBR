"""
Test simplificado para verificar extracción de dimensiones del LLM de Groq.
Este test muestra exactamente qué responde el LLM y qué dimensiones se extraen.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.append(str(Path(__file__).parent))

from simulation.groq_simulator import GroqCBRSimulator, GroqSimulationConfig

def test_llm_response_format():
    """Verifica el formato de respuesta del LLM."""
    
    print("="*80)
    print("TEST: FORMATO DE RESPUESTA DEL LLM DE GROQ")
    print("="*80)
    
    config = GroqSimulationConfig(
        verbose=True,
        temperature=0.3
    )
    
    simulator = GroqCBRSimulator(config)
    
    # Crear datos de prueba
    request_data = {
        'event_type': 'FORMAL_DINNER',
        'num_guests': 6,
        'season': 'SPRING',
        'price_min': 30,
        'price_max': 50,
        'required_diets': [],
        'preferred_style': None,
        'cultural_preference': 'ITALIAN'
    }
    
    menu_details = [{
        'starter': {
            'name': 'Bruschetta',
            'ingredients': ['tomate', 'albahaca', 'ajo', 'pan'],
            'price': 8
        },
        'main_course': {
            'name': 'Pasta Carbonara',
            'ingredients': ['pasta', 'huevo', 'bacon', 'queso'],
            'price': 18
        },
        'dessert': {
            'name': 'Tiramisu',
            'ingredients': ['mascarpone', 'café', 'cacao'],
            'price': 7
        },
        'beverage': {
            'name': 'Vino Chianti',
            'price': 12
        },
        'total_price': 45
    }]
    
    print("\n📋 Solicitud de prueba:")
    print(f"   Evento: {request_data['event_type']}")
    print(f"   Presupuesto: {request_data['price_min']}-{request_data['price_max']}€")
    print(f"   Cultura: {request_data['cultural_preference']}")
    print(f"   Precio del menú: {menu_details[0]['total_price']}€")
    
    print("\n🤖 Llamando a Groq LLM...")
    print("="*80)
    
    # Llamar al método de evaluación
    result = simulator._evaluate_single_request(request_data, menu_details)
    
    print("\n📄 RESPUESTA COMPLETA DEL LLM:")
    print("="*80)
    print(result['evaluation_text'])
    print("="*80)
    
    print("\n📊 SCORES EXTRAÍDOS:")
    print(f"   General:  {result.get('score', 'N/A')}")
    print(f"   Precio:   {result.get('price_score', 'N/A')}")
    print(f"   Cultura:  {result.get('cultural_score', 'N/A')}")
    print(f"   Sabor:    {result.get('flavor_score', 'N/A')}")
    
    # Verificar si las dimensiones son diferentes del overall
    price_score = result.get('price_score', result['score'])
    cultural_score = result.get('cultural_score', result['score'])
    flavor_score = result.get('flavor_score', result['score'])
    overall_score = result['score']
    
    print("\n🔍 ANÁLISIS:")
    
    if price_score != overall_score or cultural_score != overall_score or flavor_score != overall_score:
        print("✅ Las dimensiones son DIFERENTES del score general")
        print("   → El LLM SÍ está evaluando dimensiones por separado")
    else:
        print("⚠️  Todas las dimensiones son IGUALES al score general")
        print("   → Posible problema:")
        print("      1. El LLM no está siguiendo el formato solicitado")
        print("      2. La extracción por regex no encuentra los valores")
        print("      3. Se está usando el fallback (mismo valor para todo)")
    
    # Buscar los patrones en el texto
    print("\n🔎 BÚSQUEDA DE PATRONES EN LA RESPUESTA:")
    text = result['evaluation_text'].upper()
    
    patterns = {
        'PRECIO': 'PRECIO:' in text or 'PRICE:' in text,
        'CULTURA': 'CULTURA:' in text or 'CULTURAL:' in text,
        'SABOR': 'SABOR:' in text or 'FLAVOR:' in text,
        'GENERAL': 'GENERAL:' in text or 'OVERALL:' in text
    }
    
    for pattern, found in patterns.items():
        symbol = "✅" if found else "❌"
        print(f"   {symbol} Patrón '{pattern}:' {'encontrado' if found else 'NO encontrado'}")
    
    if not any(patterns.values()):
        print("\n💡 SUGERENCIA:")
        print("   El LLM no está usando el formato solicitado.")
        print("   Puede que necesitemos:")
        print("   - Ajustar el prompt para ser más específico")
        print("   - Mejorar los patrones de extracción")
        print("   - Usar un ejemplo en el prompt")

if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY no configurada")
        print("Crea archivo .env con: GROQ_API_KEY=tu_key")
        exit(1)
    
    test_llm_response_format()
