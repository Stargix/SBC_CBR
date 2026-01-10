"""
Test para verificar que ingredientes universales NO dan score 1.0
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from develop.core.similarity import SimilarityCalculator
from develop.core.models import CulturalTradition

def main():
    print("="*70)
    print("🐛 TEST: Bug de ingredientes universales dando score 1.0")
    print("="*70)
    
    calc = SimilarityCalculator()
    
    # Test 1: Raspberry Cobbler (solo universales)
    print("\n📋 TEST 1: Raspberry Cobbler")
    print("   Ingredientes: raspberries, sugar (ambos universales)")
    
    ingredients = ["raspberries", "sugar"]
    score = calc.get_cultural_score(ingredients, CulturalTradition.ITALIAN)
    
    print(f"\n   Score para cultura ITALIANA: {score*100:.0f}%")
    print(f"   Esperado: 70% (0.7 por cada universal)")
    print(f"   {'✅ CORRECTO' if abs(score - 0.7) < 0.01 else '❌ BUG: Debería ser 70%'}")
    
    # Test 2: Plato mixto (específicos + universales)
    print("\n📋 TEST 2: Plato mixto")
    print("   Ingredientes: butter (italiano), sugar (universal)")
    
    ingredients_mixed = ["butter", "sugar"]
    score_mixed = calc.get_cultural_score(ingredients_mixed, CulturalTradition.ITALIAN)
    
    print(f"\n   Score para cultura ITALIANA: {score_mixed*100:.0f}%")
    print(f"   Esperado: 85% ((1.0 + 0.7) / 2)")
    print(f"   {'✅ CORRECTO' if abs(score_mixed - 0.85) < 0.01 else f'❌ BUG: Debería ser 85%, obtuvo {score_mixed*100:.0f}%'}")
    
    # Test 3: Verificar is_ingredient_cultural
    print("\n📋 TEST 3: is_ingredient_cultural con include_universal")
    
    is_cultural_with = calc.is_ingredient_cultural("sugar", CulturalTradition.ITALIAN, include_universal=True)
    is_cultural_without = calc.is_ingredient_cultural("sugar", CulturalTradition.ITALIAN, include_universal=False)
    
    print(f"   sugar + ITALIAN con include_universal=True: {is_cultural_with}")
    print(f"   Esperado: True (universal es apropiado)")
    print(f"   {'✅ CORRECTO' if is_cultural_with else '❌ ERROR'}")
    
    print(f"\n   sugar + ITALIAN con include_universal=False: {is_cultural_without}")
    print(f"   Esperado: False (no es específico de Italia)")
    print(f"   {'✅ CORRECTO' if not is_cultural_without else '❌ ERROR'}")
    
    # Test 4: Ingrediente específico italiano
    print("\n📋 TEST 4: Ingrediente específico italiano")
    
    is_italian = calc.is_ingredient_cultural("butter", CulturalTradition.ITALIAN, include_universal=False)
    score_butter = calc.get_cultural_score(["butter"], CulturalTradition.ITALIAN)
    
    print(f"   butter + ITALIAN con include_universal=False: {is_italian}")
    print(f"   Esperado: True (específico de Italia)")
    print(f"   {'✅ CORRECTO' if is_italian else '❌ ERROR'}")
    
    print(f"\n   Score de ['butter'] para ITALIAN: {score_butter*100:.0f}%")
    print(f"   Esperado: 100% (específico de la cultura)")
    print(f"   {'✅ CORRECTO' if abs(score_butter - 1.0) < 0.01 else '❌ ERROR'}")
    
    print("\n" + "="*70)
    print("🎯 RESUMEN")
    print("="*70)
    
    all_pass = (
        abs(score - 0.7) < 0.01 and
        abs(score_mixed - 0.85) < 0.01 and
        is_cultural_with and
        not is_cultural_without and
        is_italian and
        abs(score_butter - 1.0) < 0.01
    )
    
    if all_pass:
        print("✅ Todos los tests pasaron correctamente")
        print("   Bug corregido: Universales dan 70%, no 100%")
    else:
        print("❌ Algunos tests fallaron")

if __name__ == "__main__":
    main()
