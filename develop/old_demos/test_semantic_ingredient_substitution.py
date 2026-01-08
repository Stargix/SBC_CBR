"""
Script de prueba para la sustitución de ingredientes con similaridad semántica cultural.

Demuestra cómo el sistema ahora puede encontrar ingredientes de culturas similares
cuando no hay match exacto con la cultura objetivo.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from develop.core.models import CulturalTradition
from develop.cycle.ingredient_adapter import get_ingredient_adapter

def test_semantic_substitution():
    """
    Prueba la sustitución de ingredientes usando similaridad semántica de culturas.
    """
    adapter = get_ingredient_adapter()
    
    print("=" * 80)
    print("TEST: Sustitución de Ingredientes con Similaridad Semántica Cultural")
    print("=" * 80)
    
    # Caso 1: Ingrediente español adaptándose a cultura italiana (culturas similares)
    print("\n📋 CASO 1: Ingrediente español → Cocina italiana")
    print("-" * 80)
    ingredient = "chorizo"  # Típicamente español
    target = CulturalTradition.ITALIAN
    
    print(f"Ingrediente original: {ingredient}")
    print(f"Cultura objetivo: {target.value}")
    
    substitution = adapter.find_substitution(ingredient, target)
    
    if substitution:
        print(f"\n✅ Sustitución encontrada:")
        print(f"   Original: {substitution.original}")
        print(f"   Reemplazo: {substitution.replacement}")
        print(f"   Razón: {substitution.reason}")
        print(f"   Confianza: {substitution.confidence:.0%}")
    else:
        print(f"\n❌ No se encontró sustitución (ingrediente ya es apropiado)")
    
    # Caso 2: Ingrediente francés adaptándose a cultura española
    print("\n\n📋 CASO 2: Ingrediente francés → Cocina española")
    print("-" * 80)
    ingredient = "foie gras"
    target = CulturalTradition.SPANISH
    
    print(f"Ingrediente original: {ingredient}")
    print(f"Cultura objetivo: {target.value}")
    
    substitution = adapter.find_substitution(ingredient, target)
    
    if substitution:
        print(f"\n✅ Sustitución encontrada:")
        print(f"   Original: {substitution.original}")
        print(f"   Reemplazo: {substitution.replacement}")
        print(f"   Razón: {substitution.reason}")
        print(f"   Confianza: {substitution.confidence:.0%}")
    else:
        print(f"\n❌ No se encontró sustitución (ingrediente ya es apropiado)")
    
    # Caso 3: Ingrediente japonés adaptándose a cultura tailandesa
    print("\n\n📋 CASO 3: Ingrediente japonés → Cocina tailandesa")
    print("-" * 80)
    ingredient = "wasabi"  # Típicamente japonés
    target = CulturalTradition.THAI
    
    print(f"Ingrediente original: {ingredient}")
    print(f"Cultura objetivo: {target.value}")
    
    substitution = adapter.find_substitution(ingredient, target)
    
    if substitution:
        print(f"\n✅ Sustitución encontrada:")
        print(f"   Original: {substitution.original}")
        print(f"   Reemplazo: {substitution.replacement}")
        print(f"   Razón: {substitution.reason}")
        print(f"   Confianza: {substitution.confidence:.0%}")
    else:
        print(f"\n❌ No se encontró sustitución (ingrediente ya es apropiado)")
    
    # Caso 4: Ingrediente chino adaptándose a cultura coreana
    print("\n\n📋 CASO 4: Ingrediente chino → Cocina coreana")
    print("-" * 80)
    ingredient = "salsa de soja"  # Asiático pero más específico de ciertas culturas
    target = CulturalTradition.KOREAN
    
    print(f"Ingrediente original: {ingredient}")
    print(f"Cultura objetivo: {target.value}")
    
    substitution = adapter.find_substitution(ingredient, target)
    
    if substitution:
        print(f"\n✅ Sustitución encontrada:")
        print(f"   Original: {substitution.original}")
        print(f"   Reemplazo: {substitution.replacement}")
        print(f"   Razón: {substitution.reason}")
        print(f"   Confianza: {substitution.confidence:.0%}")
    else:
        print(f"\n❌ No se encontró sustitución (ingrediente ya es apropiado)")
    
    # Caso 5: Verificar culturas similares
    print("\n\n📋 VERIFICACIÓN: Culturas similares a Española")
    print("-" * 80)
    similar = adapter._find_similar_cultures(CulturalTradition.SPANISH, threshold=0.5)
    
    if similar:
        print(f"\nCulturas semánticamente similares a SPANISH (threshold: 0.5):")
        for culture, similarity in similar[:5]:
            print(f"   • {culture}: {similarity:.2f}")
    else:
        print("\n⚠️ No hay calculador semántico disponible o no hay culturas similares")
    
    print("\n" + "=" * 80)
    print("✓ Test completado")
    print("=" * 80)


if __name__ == "__main__":
    test_semantic_substitution()
