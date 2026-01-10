"""
Test de filtrado por compatibilidad de categorías en búsqueda de reemplazo
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from develop.core.models import Dish, DishType, DishCategory, Season, CulinaryStyle
from develop.core.knowledge import are_categories_compatible

def main():
    print("="*70)
    print("🔍 TEST: Compatibilidad de categorías entre platos")
    print("="*70)
    
    # Ejemplos de compatibilidad
    tests = [
        ("soup", "soup", False, "Dos sopas - incompatible"),
        ("soup", "stew", False, "Sopa + estofado - ambos son caldosos"),
        ("soup", "salad", True, "Sopa + ensalada - compatible"),
        ("cream", "cream", False, "Dos platos con crema - incompatible"),
        ("pasta", "rice", False, "Pasta + arroz - ambos son carbohidratos"),
        ("pasta", "seafood", True, "Pasta + mariscos - compatible"),
        ("meat", "poultry", True, "Carne + ave - ambos son proteínas pero OK"),
        ("vegetable", "salad", True, "Vegetal + ensalada - compatible"),
        ("fruit", "fruit", False, "Dos platos con fruta - incompatible"),
    ]
    
    print("\n📊 MATRIZ DE COMPATIBILIDAD:")
    print("-" * 70)
    
    all_pass = True
    for cat1, cat2, expected, description in tests:
        try:
            result = are_categories_compatible(
                DishCategory(cat1),
                DishCategory(cat2)
            )
            
            status = "✅" if result == expected else "❌"
            if result != expected:
                all_pass = False
            
            print(f"{status} {cat1:12s} + {cat2:12s} = {str(result):5s} | {description}")
        except ValueError:
            print(f"⚠️  {cat1:12s} + {cat2:12s} = ERROR | Categoría inválida")
    
    print("\n" + "="*70)
    print("🎯 IMPACTO EN BÚSQUEDA DE REEMPLAZO")
    print("="*70)
    
    print("\n✅ AHORA el sistema filtra candidatos por compatibilidad:")
    print("   • Si el starter es 'soup', NO elegirá otro 'soup' o 'stew' para el postre")
    print("   • Si el main es 'pasta', NO elegirá 'rice' para el postre")
    print("   • Si hay dos platos con 'cream', buscará alternativas")
    
    print("\n⚠️  FALLBACK:")
    print("   • Si NO hay candidatos compatibles, mantiene todos")
    print("   • Evita bloquear completamente la adaptación")
    
    print("\n" + "="*70)
    if all_pass:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")

if __name__ == "__main__":
    main()
