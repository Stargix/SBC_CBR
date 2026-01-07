"""
Demo simple: Mostrar sustitución de ingredientes dietéticos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop.cycle.ingredient_adapter import get_ingredient_adapter

def main():
    print("="*80)
    print("🔬 DEMO: SUSTITUCIÓN DE INGREDIENTES DIETÉTICOS")
    print("="*80)
    
    adapter = get_ingredient_adapter()
    
    # TEST 1: Ingrediente con gluten → gluten-free
    print("\n" + "-"*80)
    print("TEST 1: all-purpose flour → gluten-free")
    print("-"*80)
    
    ingredient = "all-purpose flour"
    dietary_labels = ['gluten-free']
    
    print(f"\n📋 INGREDIENTE ORIGINAL: {ingredient}")
    print(f"   Restricción: {dietary_labels}")
    
    # Verificar si viola
    violates = adapter.violates_dietary_restriction(ingredient, 'gluten-free')
    print(f"   ¿Viola gluten-free?: {violates}")
    
    if violates:
        # Buscar sustitución
        substitution = adapter.find_dietary_substitution(ingredient, dietary_labels)
        
        if substitution:
            print(f"\n✅ SUSTITUCIÓN ENCONTRADA:")
            print(f"   {substitution.original} → {substitution.replacement}")
            print(f"   Razón: {substitution.reason}")
            print(f"   Confianza: {substitution.confidence:.0%}")
        else:
            print(f"\n❌ No se encontró sustitución")
    
    # TEST 2: Ingrediente lácteo → vegan + dairy-free
    print("\n" + "-"*80)
    print("TEST 2: butter → vegan + dairy-free")
    print("-"*80)
    
    ingredient = "butter"
    dietary_labels = ['vegan', 'dairy-free']
    
    print(f"\n📋 INGREDIENTE ORIGINAL: {ingredient}")
    print(f"   Restricciones: {dietary_labels}")
    
    # Verificar qué restricciones viola
    violations = []
    for label in dietary_labels:
        if adapter.violates_dietary_restriction(ingredient, label):
            violations.append(label)
    
    print(f"   Viola: {violations}")
    
    if violations:
        substitution = adapter.find_dietary_substitution(ingredient, dietary_labels)
        
        if substitution:
            print(f"\n✅ SUSTITUCIÓN ENCONTRADA:")
            print(f"   {substitution.original} → {substitution.replacement}")
            print(f"   Razón: {substitution.reason}")
            print(f"   Confianza: {substitution.confidence:.0%}")
            
            # Verificar que el sustituto cumple TODAS las restricciones
            print(f"\n🔍 VERIFICACIÓN DEL SUSTITUTO:")
            for label in dietary_labels:
                complies = not adapter.violates_dietary_restriction(substitution.replacement, label)
                status = "✅" if complies else "❌"
                print(f"   {label}: {status}")
        else:
            print(f"\n❌ No se encontró sustitución")
    
    # TEST 3: Ingrediente ya cumple → no necesita sustitución
    print("\n" + "-"*80)
    print("TEST 3: olive oil → vegan (ya cumple)")
    print("-"*80)
    
    ingredient = "olive oil"
    dietary_labels = ['vegan']
    
    print(f"\n📋 INGREDIENTE ORIGINAL: {ingredient}")
    print(f"   Restricción: {dietary_labels}")
    
    violates = adapter.violates_dietary_restriction(ingredient, 'vegan')
    print(f"   ¿Viola vegan?: {violates}")
    
    substitution = adapter.find_dietary_substitution(ingredient, dietary_labels)
    
    if substitution:
        print(f"\n   Sustitución: {substitution.replacement}")
    else:
        print(f"\n   ✅ No necesita sustitución (ya cumple)")
    
    # TEST 4: Múltiples restricciones (vegan + gluten-free + nut-free)
    print("\n" + "-"*80)
    print("TEST 4: Restricciones múltiples")
    print("-"*80)
    
    test_ingredients = ['chicken', 'butter', 'all-purpose flour', 'almonds']
    dietary_labels = ['vegan', 'gluten-free', 'nut-free']
    
    print(f"\n📋 INGREDIENTES: {test_ingredients}")
    print(f"   Restricciones: {dietary_labels}")
    print(f"\n   ANÁLISIS:")
    
    for ing in test_ingredients:
        violations = [label for label in dietary_labels 
                     if adapter.violates_dietary_restriction(ing, label)]
        
        if violations:
            print(f"\n   {ing}:")
            print(f"      Viola: {violations}")
            
            substitution = adapter.find_dietary_substitution(ing, dietary_labels)
            
            if substitution:
                print(f"      → {substitution.replacement}")
                print(f"      Confianza: {substitution.confidence:.0%}")
                
                # Verificar que cumple TODAS
                still_violates = [label for label in dietary_labels
                                if adapter.violates_dietary_restriction(substitution.replacement, label)]
                
                if still_violates:
                    print(f"      ⚠️  Aún viola: {still_violates}")
                else:
                    print(f"      ✅ Cumple todas las restricciones")
            else:
                print(f"      ❌ No se encontró sustitución adecuada")
        else:
            print(f"\n   {ing}: ✅ Cumple todas")
    
    # RESUMEN
    print("\n" + "="*80)
    print("📊 RESUMEN DEL SISTEMA")
    print("="*80)
    
    print("\n✅ MÉTODOS IMPLEMENTADOS:")
    print("   • violates_dietary_restriction(ingredient, label)")
    print("   • get_compliant_ingredients(label)")
    print("   • find_dietary_substitution(ingredient, labels)")
    
    print("\n🎯 ESTRATEGIA DE BÚSQUEDA:")
    print("   1. Mismo grupo + cumple restricciones (conf: 90%)")
    print("   2. Si no hay en grupo: NO SUSTITUIR (mantiene coherencia)")
    
    print("\n📝 CARACTERÍSTICAS:")
    print("   ✓ Soporta múltiples restricciones simultáneas")
    print("   ✓ Garantiza que sustituto cumple TODAS las restricciones")
    print("   ✓ SOLO sustituye dentro del mismo grupo (coherencia gastronómica)")
    print("   ✓ Prioriza calidad del plato sobre forzar adaptaciones")

if __name__ == "__main__":
    main()
