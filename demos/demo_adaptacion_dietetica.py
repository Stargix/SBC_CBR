"""
Demo: Adaptación de ingredientes por restricciones dietéticas.

Muestra cómo el sistema puede adaptar platos que casi cumplen una restricción
dietética, cambiando solo los ingredientes problemáticos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    Request, EventType, Season,
    CaseBase, CaseRetriever, CaseAdapter
)
from develop.cycle.ingredient_adapter import get_ingredient_adapter

def main():
    print("="*80)
    print("🥗 DEMO: ADAPTACIÓN DE INGREDIENTES DIETÉTICOS")
    print("="*80)
    
    # Cargar base de casos
    case_base = CaseBase()
    case_base.load_from_file("config/initial_cases.json")
    
    retriever = CaseRetriever(case_base)
    adapter_main = CaseAdapter(case_base)
    ing_adapter = get_ingredient_adapter()
    
    print(f"\n📖 Base de casos: {len(case_base.get_all_cases())} casos cargados")
    
    # ========================================================================
    # TEST 1: Plato casi vegano (solo algunos ingredientes no lo son)
    # ========================================================================
    print("\n" + "="*80)
    print("TEST 1: Adaptación de ingredientes a VEGAN")
    print("="*80)
    
    # Obtener un plato vegetariano (más fácil de adaptar a vegano)
    all_starters = case_base.get_dishes_by_type("starter")
    vegetarian_starter = None
    for dish in all_starters:
        if 'vegetarian' in dish.diets and 'vegan' not in dish.diets:
            # Verificar que tiene pocos ingredientes no veganos
            non_vegan_count = sum(
                1 for ing in dish.ingredients
                if ing_adapter.violates_dietary_restriction(ing, 'vegan')
            )
            if non_vegan_count > 0 and non_vegan_count <= 2:
                vegetarian_starter = dish
                break
    
    if vegetarian_starter:
        print(f"\n📋 PLATO ORIGINAL: {vegetarian_starter.name}")
        print(f"   Dietas: {vegetarian_starter.diets}")
        print(f"   Ingredientes: {vegetarian_starter.ingredients}")
        
        # Identificar ingredientes no veganos
        print(f"\n🔍 ANÁLISIS DE INGREDIENTES:")
        non_vegan_ingredients = []
        for ing in vegetarian_starter.ingredients:
            is_vegan_compliant = not ing_adapter.violates_dietary_restriction(ing, 'vegan')
            status = "✅ Vegan" if is_vegan_compliant else "❌ NO vegan"
            print(f"   {ing}: {status}")
            if not is_vegan_compliant:
                non_vegan_ingredients.append(ing)
        
        print(f"\n🔧 ADAPTANDO INGREDIENTES NO VEGANOS:")
        substitutions = []
        for ing in non_vegan_ingredients:
            sub = ing_adapter.find_dietary_substitution(ing, ['vegan'])
            if sub:
                print(f"   {sub.original} → {sub.replacement}")
                print(f"      Razón: {sub.reason}")
                print(f"      Confianza: {sub.confidence:.0%}")
                substitutions.append(sub)
            else:
                print(f"   {ing}: ⚠️  No se encontró sustitución")
        
        if len(substitutions) == len(non_vegan_ingredients):
            print(f"\n✅ PLATO ADAPTADO EXITOSAMENTE")
            print(f"   Sustituciones: {len(substitutions)}")
        else:
            print(f"\n⚠️  Adaptación parcial: {len(substitutions)}/{len(non_vegan_ingredients)}")
    else:
        print("\n⚠️  No se encontró plato vegetariano adecuado para demo")
    
    # ========================================================================
    # TEST 2: Solicitud con restricción dietética
    # ========================================================================
    print("\n" + "="*80)
    print("TEST 2: Request con dieta GLUTEN-FREE")
    print("="*80)
    
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=120,
        season=Season.SPRING,
        wants_wine=True,
        required_diets=['gluten-free'],
        restricted_ingredients=[],
        cultural_preference=None
    )
    
    print(f"\n📋 SOLICITUD:")
    print(f"   Evento: {request.event_type.value}")
    print(f"   Dietas requeridas: {request.required_diets}")
    
    # RETRIEVE con fallback
    print(f"\n🔍 FASE RETRIEVE:")
    results = retriever.retrieve(request, k=3)
    
    print(f"   Candidatos recuperados: {len(results)}")
    for r in results:
        print(f"   {r.rank}. Caso {r.case.id} (sim: {r.similarity:.3f})")
        
        # Ver si platos cumplen gluten-free
        for dish_attr in ['starter', 'main_course', 'dessert']:
            dish = getattr(r.case.menu, dish_attr)
            is_gf = 'gluten-free' in dish.diets
            gluten_ings = [
                ing for ing in dish.ingredients
                if ing_adapter.violates_dietary_restriction(ing, 'gluten-free')
            ]
            
            if is_gf:
                status = "✅ GF"
            elif gluten_ings:
                status = f"❌ ({len(gluten_ings)} gluten ing)"
            else:
                status = "❓ Not labeled GF"
            
            print(f"      {dish_attr}: {dish.name} {status}")
            
            if gluten_ings:
                print(f"         → {', '.join(gluten_ings)}")
    
    # ADAPT
    print(f"\n🔧 FASE ADAPT:")
    adapted_menus = adapter_main.adapt(results, request, num_proposals=2)
    
    print(f"   Menús adaptados: {len(adapted_menus)}")
    
    for i, result in enumerate(adapted_menus, 1):
        print(f"\n   {'='*70}")
        print(f"   MENÚ ADAPTADO #{i}")
        print(f"   {'='*70}")
        
        if result.original_case:
            print(f"   📌 Caso base: {result.original_case.id}")
        
        print(f"\n   📊 SIMILITUD:")
        print(f"      Original: {result.original_similarity:.3f}")
        print(f"      Final:    {result.final_similarity:.3f}")
        
        print(f"\n   🍽️  MENÚ FINAL:")
        for dish_attr in ['starter', 'main_course', 'dessert']:
            dish = getattr(result.adapted_menu, dish_attr)
            is_gf = 'gluten-free' in dish.diets
            status = "✅ GF" if is_gf else "❌ NO GF"
            print(f"      {dish_attr}: {dish.name} {status}")
        
        if result.adaptations_made:
            dietary_adaptations = [a for a in result.adaptations_made if 'Dietary' in a or 'violates' in a.lower()]
            if dietary_adaptations:
                print(f"\n   🔄 ADAPTACIONES DIETÉTICAS ({len(dietary_adaptations)}):")
                for adaptation in dietary_adaptations[:5]:
                    print(f"      • {adaptation}")
    
    # ========================================================================
    # RESUMEN
    # ========================================================================
    print("\n" + "="*80)
    print("📋 RESUMEN DE LA FUNCIONALIDAD")
    print("="*80)
    
    print("\n✅ CAPACIDADES IMPLEMENTADAS:")
    print("   1. non_compliant_labels en ingredients.json")
    print("      • Cada ingrediente declara qué dietas NO cumple")
    print("      • Ej: butter no cumple 'vegan', 'dairy-free'")
    
    print("\n   2. violates_dietary_restriction(ingredient, label)")
    print("      • Verifica si un ingrediente viola una restricción")
    
    print("\n   3. find_dietary_substitution(ingredient, labels)")
    print("      • Busca sustituto en mismo grupo que cumpla restricciones")
    print("      • Fallback: busca en todos los ingredientes")
    
    print("\n   4. _adapt_for_diets() mejorado")
    print("      • ANTES: solo validaba si plato cumple dieta")
    print("      • AHORA: adapta ingredientes específicos que violan")
    print("      • Permite platos 'casi veganos' → veganos")
    
    print("\n🎯 BENEFICIOS:")
    print("   ✓ No rechaza platos por 1-2 ingredientes problemáticos")
    print("   ✓ Adaptación granular (nivel ingrediente, no plato)")
    print("   ✓ Mantiene esencia del plato original")
    print("   ✓ Mayor flexibilidad en RETRIEVE (más candidatos)")
    
    print("\n📊 CASOS DE USO:")
    print("   • Plato vegetariano → vegano (quitar lácteos/huevos)")
    print("   • Plato normal → gluten-free (sustituir harina/pasta)")
    print("   • Plato → dairy-free (sustituir lácteos)")
    print("   • Combinar múltiples restricciones (vegan + gluten-free)")

if __name__ == "__main__":
    main()
