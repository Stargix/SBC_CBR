"""
Test directo importando similarity.py
"""

import sys
from pathlib import Path

# Forzar recarga de módulos
if 'develop.core.similarity' in sys.modules:
    del sys.modules['develop.core.similarity']
if 'develop.core.models' in sys.modules:
    del sys.modules['develop.core.models']

sys.path.insert(0, str(Path(__file__).parent))

from develop.core.similarity import SimilarityCalculator
from develop.core.models import CulturalTradition

print("="*70)
print("🔬 TEST DIRECTO: Import fresco de similarity.py")
print("="*70)

calc = SimilarityCalculator()

# Test Raspberry Cobbler
ingredients_cobbler = ["raspberries", "sugar"]
score_cobbler = calc.get_cultural_score(ingredients_cobbler, CulturalTradition.ITALIAN)

print(f"\n📋 Raspberry Cobbler (raspberries, sugar):")
print(f"   Score cultural para ITALIAN: {score_cobbler:.0%}")
print(f"   {'✅ CORRECTO (70%)' if abs(score_cobbler - 0.7) < 0.01 else '❌ ERROR: Esperado 70%'}")

# Test Raspberry Bars
ingredients_bars = ["sugar", "sugar", "all-purpose flour", "butter", "eggs", "walnuts"]
score_bars = calc.get_cultural_score(ingredients_bars, CulturalTradition.ITALIAN)

print(f"\n📋 Raspberry Bars (sugar x2, flour, butter, eggs, walnuts):")
print(f"   Score cultural para ITALIAN: {score_bars:.0%}")
print(f"   {'✅ CORRECTO (75%)' if abs(score_bars - 0.75) < 0.01 else '❌ ERROR: Esperado 75%'}")

# Verificar el método is_ingredient_cultural
print(f"\n🔬 VERIFICACIÓN: is_ingredient_cultural")
is_sugar_with = calc.is_ingredient_cultural("sugar", CulturalTradition.ITALIAN, include_universal=True)
is_sugar_without = calc.is_ingredient_cultural("sugar", CulturalTradition.ITALIAN, include_universal=False)

print(f"   sugar + include_universal=True: {is_sugar_with}")
print(f"   sugar + include_universal=False: {is_sugar_without}")
print(f"   {'✅ CORRECTO' if is_sugar_with and not is_sugar_without else '❌ ERROR'}")

print("\n" + "="*70)
if abs(score_cobbler - 0.7) < 0.01 and abs(score_bars - 0.75) < 0.01:
    print("✅ TODOS LOS TESTS PASARON - Código está correcto")
else:
    print("❌ TESTS FALLARON - Puede haber cache persistente")
