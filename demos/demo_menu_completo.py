"""
Demo: Adaptación completa de menú con restricciones dietéticas.
Muestra el flujo completo RETRIEVE → ADAPT con sustitución de ingredientes.
"""

from develop.core.models import Request, EventType, Season, Dish
from develop.core.case_base import CaseBase
from develop.cycle.retrieve import CaseRetriever
from develop.cycle.adapt import CaseAdapter
from develop.cycle.ingredient_adapter import get_ingredient_adapter

def main():
    print("="*80)
    print("🍽️  DEMO: ADAPTACIÓN COMPLETA DE MENÚ")
    print("="*80)
    
    # Cargar base de casos
    case_base = CaseBase()
    case_base.load_from_file("config/initial_cases.json")
    
    retriever = CaseRetriever(case_base)
    adapter = CaseAdapter(case_base)
    ing_adapter = get_ingredient_adapter()
    
    print(f"\n📖 Base de casos: {len(case_base.get_all_cases())} casos")
    
    # Crear request con restricción gluten-free
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
    print(f"   Invitados: {request.num_guests}")
    print(f"   Temporada: {request.season.value}")
    print(f"   ⚠️  RESTRICCIÓN DIETÉTICA: {request.required_diets}")
    
    # FASE 1: RETRIEVE
    print(f"\n{'='*80}")
    print("🔍 FASE 1: RETRIEVE")
    print(f"{'='*80}")
    
    results = retriever.retrieve(request, k=1)
    
    if not results:
        print("❌ No se encontraron candidatos")
        return
    
    best_match = results[0]
    print(f"\n📌 MEJOR CANDIDATO:")
    print(f"   Caso: {best_match.case.id}")
    print(f"   Similitud: {best_match.similarity:.3f}")
    
    print(f"\n🍽️  MENÚ ORIGINAL:")
    for dish_type in ['starter', 'main_course', 'dessert']:
        dish = getattr(best_match.case.menu, dish_type)
        
        # Analizar ingredientes con gluten
        gluten_ingredients = [
            ing for ing in dish.ingredients
            if ing_adapter.violates_dietary_restriction(ing, 'gluten-free')
        ]
        
        is_gf = 'gluten-free' in dish.diets
        status = "✅ GF" if is_gf else f"❌ {len(gluten_ingredients)} gluten ing"
        
        print(f"\n   {dish_type.upper()}: {dish.name} {status}")
        print(f"      Ingredientes: {', '.join(dish.ingredients[:5])}")
        if len(dish.ingredients) > 5:
            print(f"                    ... y {len(dish.ingredients)-5} más")
        
        if gluten_ingredients:
            print(f"      ⚠️  CON GLUTEN: {', '.join(gluten_ingredients)}")
    
    # FASE 2: ADAPT (manual para ver proceso)
    print(f"\n{'='*80}")
    print("🔧 FASE 2: ADAPT - Adaptar ingredientes")
    print(f"{'='*80}")
    
    print(f"\n🔍 BUSCANDO SUSTITUCIONES:")
    
    adapted_dishes = {}
    all_substitutions = []
    
    for dish_type in ['starter', 'main_course', 'dessert']:
        dish = getattr(best_match.case.menu, dish_type)
        
        print(f"\n   {dish_type.upper()}: {dish.name}")
        
        # Buscar ingredientes con gluten
        gluten_ingredients = [
            ing for ing in dish.ingredients
            if ing_adapter.violates_dietary_restriction(ing, 'gluten-free')
        ]
        
        if not gluten_ingredients:
            print(f"      ✅ Ya es gluten-free")
            adapted_dishes[dish_type] = dish
            continue
        
        # Intentar adaptar cada ingrediente
        new_ingredients = dish.ingredients.copy()
        substitutions_made = []
        failed = []
        
        for gluten_ing in gluten_ingredients:
            sub = ing_adapter.find_dietary_substitution(gluten_ing, ['gluten-free'])
            
            if sub:
                # Reemplazar
                idx = new_ingredients.index(gluten_ing)
                new_ingredients[idx] = sub.replacement
                substitutions_made.append(sub)
                all_substitutions.append(sub)
                
                print(f"      ✅ {sub.original} → {sub.replacement} (conf: {sub.confidence:.0%})")
            else:
                failed.append(gluten_ing)
                print(f"      ❌ {gluten_ing}: sin sustituto")
        
        if failed:
            print(f"      ⚠️  No se pudo adaptar completamente")
            adapted_dishes[dish_type] = dish
        else:
            # Crear plato adaptado
            adapted_dish = Dish(
                id=dish.id,
                name=dish.name,
                dish_type=dish.dish_type,
                price=dish.price,
                category=dish.category,
                styles=dish.styles,
                ingredients=new_ingredients,
                diets=dish.diets + ['gluten-free'] if 'gluten-free' not in dish.diets else dish.diets,
                seasons=dish.seasons,
                temperature=dish.temperature,
                complexity=dish.complexity,
                calories=dish.calories,
                max_guests=dish.max_guests,
                flavors=dish.flavors,
                compatible_beverages=dish.compatible_beverages,
                cultural_traditions=dish.cultural_traditions,
                chef_style=dish.chef_style,
                presentation_notes=dish.presentation_notes
            )
            adapted_dishes[dish_type] = adapted_dish
            print(f"      ✅ PLATO ADAPTADO ({len(substitutions_made)} cambios)")
    
    # RESULTADO
    print(f"\n{'='*80}")
    print("✨ RESULTADO FINAL")
    print(f"{'='*80}")
    
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   Sustituciones totales: {len(all_substitutions)}")
    
    if all_substitutions:
        avg_confidence = sum(s.confidence for s in all_substitutions) / len(all_substitutions)
        print(f"   Confianza promedio: {avg_confidence:.0%}")
    
    print(f"\n🍽️  MENÚ ADAPTADO:")
    
    for dish_type in ['starter', 'main_course', 'dessert']:
        dish = adapted_dishes[dish_type]
        is_gf = 'gluten-free' in dish.diets
        status = "✅ GF" if is_gf else "❌ NO GF"
        
        print(f"\n   {dish_type.upper()}: {dish.name} {status}")
        print(f"      Dietas: {', '.join(dish.diets)}")
        print(f"      Ingredientes: {', '.join(dish.ingredients[:5])}")
        if len(dish.ingredients) > 5:
            print(f"                    ... y {len(dish.ingredients)-5} más")
    
    # COMPARACIÓN
    if all_substitutions:
        print(f"\n🔄 CAMBIOS REALIZADOS:")
        for sub in all_substitutions:
            print(f"   • {sub.original} → {sub.replacement}")
            print(f"     Razón: {sub.reason}")
    
    # RESUMEN
    print(f"\n{'='*80}")
    print("📋 CONCLUSIONES")
    print(f"{'='*80}")
    
    original_gf_count = sum(
        1 for dt in ['starter', 'main_course', 'dessert']
        if 'gluten-free' in getattr(best_match.case.menu, dt).diets
    )
    
    adapted_gf_count = sum(
        1 for dt in ['starter', 'main_course', 'dessert']
        if 'gluten-free' in adapted_dishes[dt].diets
    )
    
    print(f"\n✅ ANTES: {original_gf_count}/3 platos gluten-free")
    print(f"✅ DESPUÉS: {adapted_gf_count}/3 platos gluten-free")
    
    if adapted_gf_count == 3:
        print(f"\n🎉 ¡MENÚ COMPLETAMENTE ADAPTADO!")
        print(f"   El cliente recibirá un menú 100% gluten-free")
        print(f"   Manteniendo la esencia del menú original")
    elif adapted_gf_count > original_gf_count:
        print(f"\n✅ Mejora: +{adapted_gf_count - original_gf_count} platos adaptados")
    else:
        print(f"\n⚠️  No se pudo adaptar completamente")
    
    print(f"\n💡 VENTAJAS DEL SISTEMA:")
    print(f"   ✓ Adaptación granular (ingrediente por ingrediente)")
    print(f"   ✓ Mantiene estructura del menú original")
    print(f"   ✓ Alta confianza en sustituciones (mismo grupo)")
    print(f"   ✓ Flexibilidad: no rechaza menú completo")

if __name__ == "__main__":
    main()
