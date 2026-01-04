"""
Test específico de los platos que dan 100% en la demo
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from develop.core.similarity import SimilarityCalculator
from develop.core.models import CulturalTradition

def main():
    print("="*70)
    print("🔍 ANÁLISIS: Platos con 100% Cultural Score")
    print("="*70)
    
    # Cargar dishes.json
    with open('develop/config/dishes.json', 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    
    calc = SimilarityCalculator()
    
    # Platos a analizar
    platos_problema = [
        "Cherry Cream Pie",
        "CROCK POT CHERRY DUMP CAKE",
        "Chewy No-Bake Cookies & Cream Bars",
        "We Made Chex Bars from a Mix and Life Will Never Be the Same",
        "Raspberry Cobbler",
        "Raspberry Bars"
    ]
    
    for nombre_plato in platos_problema:
        # Buscar el plato
        plato = None
        for d in dishes:
            if d['name'] == nombre_plato:
                plato = d
                break
        
        if not plato:
            print(f"\n❌ {nombre_plato}: NO ENCONTRADO")
            continue
        
        ingredients = plato.get('ingredients', [])
        
        print(f"\n{'='*70}")
        print(f"📋 {nombre_plato}")
        print(f"{'='*70}")
        print(f"Ingredientes ({len(ingredients)}): {ingredients}")
        
        if not ingredients:
            print("   ⚠️  Sin ingredientes listados")
            continue
        
        # Calcular score
        score = calc.get_cultural_score(ingredients, CulturalTradition.ITALIAN)
        
        print(f"\n📊 Score Cultural (ITALIAN): {score:.2%}")
        
        # Analizar cada ingrediente
        print(f"\n🔬 Desglose por ingrediente:")
        
        for ing in set(ingredients):
            count = ingredients.count(ing)
            ing_data = calc.ingredient_to_cultures.get(ing)
            
            if ing_data is None:
                print(f"   ❌ {ing} (x{count}): NO en base → 0.5")
            else:
                cultures = ing_data.get('cultures', []) if isinstance(ing_data, dict) else ing_data
                cultures_lower = [c.lower() for c in cultures]
                
                if 'italian' in cultures_lower:
                    print(f"   🇮🇹 {ing} (x{count}): ITALIANO → 1.0")
                elif 'universal' in cultures_lower:
                    print(f"   🌍 {ing} (x{count}): UNIVERSAL → 0.7")
                else:
                    print(f"   ⚠️  {ing} (x{count}): {cultures[:3]} → semántico o 0.0")
        
        # Calcular score esperado manualmente
        total_manual = 0.0
        for ing in ingredients:
            ing_data = calc.ingredient_to_cultures.get(ing)
            if ing_data is None:
                total_manual += 0.5
            else:
                cultures = ing_data.get('cultures', []) if isinstance(ing_data, dict) else ing_data
                cultures_lower = [c.lower() for c in cultures]
                
                if 'italian' in cultures_lower:
                    total_manual += 1.0
                elif 'universal' in cultures_lower:
                    total_manual += 0.7
                else:
                    # Simplificado - asumir 0.0 sin semántico
                    total_manual += 0.0
        
        score_manual = total_manual / len(ingredients)
        print(f"\n✅ Score calculado manualmente: {score_manual:.2%}")
        print(f"✅ Score de get_cultural_score: {score:.2%}")
        
        if abs(score - score_manual) > 0.05:
            print(f"⚠️  DIFERENCIA: {abs(score - score_manual):.2%}")

if __name__ == "__main__":
    main()
