"""
Test para verificar el score cultural de Raspberry Bars específicamente
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from develop.core.similarity import SimilarityCalculator
from develop.core.models import CulturalTradition

def main():
    print("="*70)
    print("🔍 ANÁLISIS: Raspberry Bars Cultural Score")
    print("="*70)
    
    calc = SimilarityCalculator()
    
    # Ingredientes de Raspberry Bars según dishes.json
    ingredients = ["sugar", "sugar", "all-purpose flour", "butter", "eggs", "walnuts"]
    
    print(f"\n📋 INGREDIENTES DE RASPBERRY BARS:")
    print(f"   {ingredients}")
    
    # Analizar cada ingrediente
    print(f"\n🔬 ANÁLISIS POR INGREDIENTE:")
    
    total_score = 0.0
    for ing in set(ingredients):  # Sin duplicados para análisis
        ing_data = calc.ingredient_to_cultures.get(ing)
        
        if ing_data is None:
            print(f"\n   ❌ {ing}: NO ENCONTRADO en base")
            print(f"      → Score: 0.5 (neutro)")
            # Contar cuántas veces aparece
            count = ingredients.count(ing)
            total_score += 0.5 * count
            continue
        
        cultures = ing_data.get('cultures', []) if isinstance(ing_data, dict) else ing_data
        cultures_lower = [c.lower() for c in cultures]
        
        # Verificar cada caso
        count = ingredients.count(ing)
        
        if 'italian' in cultures_lower:
            print(f"\n   ✅ {ing} (x{count}): ITALIANO")
            print(f"      Culturas: {cultures}")
            print(f"      → Score: 1.0")
            total_score += 1.0 * count
        elif 'universal' in cultures_lower:
            print(f"\n   🌍 {ing} (x{count}): UNIVERSAL")
            print(f"      Culturas: {cultures}")
            print(f"      → Score: 0.7")
            total_score += 0.7 * count
        else:
            print(f"\n   ⚠️  {ing} (x{count}): OTRAS CULTURAS")
            print(f"      Culturas: {cultures}")
            
            # Verificar si es semánticamente similar
            if calc.semantic_calculator:
                max_sim = 0.0
                for c in cultures:
                    try:
                        cult = CulturalTradition(c.lower())
                        sim = calc.semantic_calculator.calculate_cultural_similarity(
                            CulturalTradition.ITALIAN, cult
                        )
                        max_sim = max(max_sim, sim)
                    except:
                        pass
                
                if max_sim > 0.7:
                    print(f"      Similaridad semántica: {max_sim:.2f}")
                    print(f"      → Score: {max_sim:.2f}")
                    total_score += max_sim * count
                else:
                    print(f"      Similaridad semántica: {max_sim:.2f} (muy baja)")
                    print(f"      → Score: 0.0")
    
    final_score = total_score / len(ingredients)
    
    print(f"\n" + "="*70)
    print(f"📊 RESULTADO FINAL")
    print(f"="*70)
    print(f"   Total ingredientes: {len(ingredients)} (incluyendo duplicados)")
    print(f"   Score total acumulado: {total_score:.2f}")
    print(f"   Score final (promedio): {final_score:.2%}")
    
    # Verificar con get_cultural_score
    actual_score = calc.get_cultural_score(ingredients, CulturalTradition.ITALIAN)
    print(f"\n   Score calculado por get_cultural_score: {actual_score:.2%}")
    
    if abs(actual_score - final_score) < 0.01:
        print(f"   ✅ Coincide con el análisis manual")
    else:
        print(f"   ⚠️  Diferencia detectada: {abs(actual_score - final_score):.2%}")

if __name__ == "__main__":
    main()
