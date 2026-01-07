"""
Demo rápida de filtrado por compatibilidad de categorías
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from develop.core.knowledge import are_categories_compatible
from develop.core.models import DishCategory

def main():
    print("="*70)
    print("✅ Reglas de compatibilidad activadas en búsqueda de reemplazo")
    print("="*70)
    
    # Casos principales
    casos_incompatibles = [
        ("pasta", "rice", "Ambos son carbohidratos principales"),
        ("pasta", "legume", "Carbohidrato + legumbre"),
        ("meat", "poultry", "Dos tipos de proteína principal"),
        ("meat", "fish", "Carne + pescado"),
        ("soup", "cream", "Dos platos caldosos/cremosos"),
        ("salad", "vegetable", "Duplicación de vegetales"),
        ("fruit", "fruit", "Duplicación de fruta"),
    ]
    
    print("\n🚫 CATEGORÍAS INCOMPATIBLES (se filtrarán):")
    print("-" * 70)
    for cat1, cat2, razon in casos_incompatibles:
        result = are_categories_compatible(DishCategory(cat1), DishCategory(cat2))
        symbol = "❌" if not result else "⚠️ "
        print(f"{symbol} {cat1:12s} + {cat2:12s} → {razon}")
    
    casos_compatibles = [
        ("pasta", "seafood", "Pasta con mariscos es común"),
        ("meat", "vegetable", "Carne con vegetales es típico"),
        ("soup", "salad", "Entrada ligera + sopa"),
        ("seafood", "salad", "Marisco con ensalada"),
    ]
    
    print("\n✅ CATEGORÍAS COMPATIBLES (permitidas):")
    print("-" * 70)
    for cat1, cat2, razon in casos_compatibles:
        result = are_categories_compatible(DishCategory(cat1), DishCategory(cat2))
        symbol = "✅" if result else "⚠️ "
        print(f"{symbol} {cat1:12s} + {cat2:12s} → {razon}")
    
    print("\n" + "="*70)
    print("📋 EJEMPLO DE IMPACTO:")
    print("="*70)
    print("\nMenú actual:")
    print("   Starter: Caesar Salad (category: salad)")
    print("   Main: Spaghetti Carbonara (category: pasta)")
    print("   Dessert: Tiramisu (category: cream)")
    
    print("\n🔍 Al buscar reemplazo para el DESSERT:")
    print("   ✅ Permitirá: fruit, chocolate, pastry")
    print("   ❌ Filtrará: cream (incompatible con soup si hubiera)")
    print("   ⚠️  Fallback: Si no hay opciones, mantiene todos los candidatos")

if __name__ == "__main__":
    main()
