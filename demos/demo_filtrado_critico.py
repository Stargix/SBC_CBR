"""
Demo: Filtrado de restricciones críticas en RETRIEVE.

Muestra cómo RETRIEVE filtra por dietas y alergias ANTES del scoring,
evitando desperdiciar intentos de adaptación en casos incompatibles.
"""

from develop.core.models import Request, EventType, Season
from develop.core.case_base import CaseBase
from develop.cycle.retrieve import CaseRetriever

def main():
    print("="*70)
    print("🔍 DEMO: FILTRADO DE RESTRICCIONES CRÍTICAS EN RETRIEVE")
    print("="*70)
    
    # Cargar base de casos
    case_base = CaseBase()
    case_base.load_from_file("config/initial_cases.json")
    retriever = CaseRetriever(case_base)
    
    print(f"\n📊 Base de casos: {len(case_base.get_all_cases())} casos totales")
    
    # ========================================================================
    # TEST 1: Solicitud SIN restricciones críticas
    # ========================================================================
    print("\n" + "="*70)
    print("TEST 1: Sin restricciones críticas")
    print("="*70)
    
    request_simple = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=120,
        season=Season.SPRING,
        wants_wine=True,
        required_diets=[],
        restricted_ingredients=[]
    )
    
    print(f"\n📋 SOLICITUD:")
    print(f"   Evento: {request_simple.event_type.value}")
    print(f"   Dietas: {request_simple.required_diets or 'ninguna'}")
    print(f"   Alergias: {request_simple.restricted_ingredients or 'ninguna'}")
    
    results = retriever.retrieve(request_simple, k=5)
    
    print(f"\n✅ CANDIDATOS RECUPERADOS: {len(results)}")
    for r in results[:3]:
        menu_diets = r.case.menu.get_all_diets()
        print(f"   {r.rank}. Caso {r.case.id} (sim: {r.similarity:.2f})")
        print(f"      Dietas: {menu_diets}")
    
    # ========================================================================
    # TEST 2: Solicitud CON restricciones dietéticas (vegan)
    # ========================================================================
    print("\n" + "="*70)
    print("TEST 2: Restricción dietética CRÍTICA (vegan)")
    print("="*70)
    
    request_vegan = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=120,
        season=Season.SPRING,
        wants_wine=True,
        required_diets=['vegan'],
        restricted_ingredients=[]
    )
    
    print(f"\n📋 SOLICITUD:")
    print(f"   Evento: {request_vegan.event_type.value}")
    print(f"   Dietas: {request_vegan.required_diets}")
    print(f"   Alergias: {request_vegan.restricted_ingredients or 'ninguna'}")
    
    # Contar casos veganos en la base
    all_cases = case_base.get_all_cases()
    vegan_cases = [c for c in all_cases if not c.is_negative and 
                   'vegan' in c.menu.get_all_diets()]
    
    print(f"\n📊 Casos veganos en base: {len(vegan_cases)}/{len(all_cases)}")
    
    results_vegan = retriever.retrieve(request_vegan, k=5)
    
    print(f"\n✅ CANDIDATOS RECUPERADOS: {len(results_vegan)}")
    print("   (RETRIEVE filtró casos NO veganos ANTES del scoring)")
    
    for r in results_vegan[:3]:
        menu_diets = r.case.menu.get_all_diets()
        is_vegan = 'vegan' in menu_diets
        print(f"\n   {r.rank}. Caso {r.case.id} (sim: {r.similarity:.2f})")
        print(f"      Starter: {r.case.menu.starter.name}")
        print(f"         Dietas: {r.case.menu.starter.diets}")
        print(f"      Main: {r.case.menu.main_course.name}")
        print(f"         Dietas: {r.case.menu.main_course.diets}")
        print(f"      Dessert: {r.case.menu.dessert.name}")
        print(f"         Dietas: {r.case.menu.dessert.diets}")
        print(f"      ✅ Vegano: {'SÍ' if is_vegan else '❌ NO'}")
    
    # ========================================================================
    # TEST 3: Solicitud CON alergias (nuts)
    # ========================================================================
    print("\n" + "="*70)
    print("TEST 3: Restricción de alergias CRÍTICA (nuts)")
    print("="*70)
    
    request_allergy = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=120,
        season=Season.SPRING,
        wants_wine=True,
        required_diets=[],
        restricted_ingredients=['peanuts', 'walnuts', 'almonds']
    )
    
    print(f"\n📋 SOLICITUD:")
    print(f"   Evento: {request_allergy.event_type.value}")
    print(f"   Dietas: {request_allergy.required_diets or 'ninguna'}")
    print(f"   Alergias: {request_allergy.restricted_ingredients}")
    
    results_allergy = retriever.retrieve(request_allergy, k=5)
    
    print(f"\n✅ CANDIDATOS RECUPERADOS: {len(results_allergy)}")
    print("   (RETRIEVE filtró casos con nuts ANTES del scoring)")
    
    for r in results_allergy[:3]:
        print(f"\n   {r.rank}. Caso {r.case.id} (sim: {r.similarity:.2f})")
        
        # Verificar ingredientes
        all_ingredients = (
            r.case.menu.starter.ingredients +
            r.case.menu.main_course.ingredients +
            r.case.menu.dessert.ingredients
        )
        
        has_nuts = any(ing in all_ingredients for ing in request_allergy.restricted_ingredients)
        
        print(f"      Ingredientes totales: {len(all_ingredients)}")
        print(f"      Contiene nuts: {'❌ SÍ' if has_nuts else '✅ NO'}")
    
    # ========================================================================
    # TEST 4: FALLBACK - Si quedan <3 candidatos, no filtrar
    # ========================================================================
    print("\n" + "="*70)
    print("TEST 4: FALLBACK cuando quedan pocos candidatos")
    print("="*70)
    
    request_extreme = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=120,
        season=Season.SPRING,
        wants_wine=True,
        required_diets=['vegan', 'gluten-free'],  # Combinación restrictiva
        restricted_ingredients=['onion', 'garlic', 'tomato']  # Muchos ingredientes comunes
    )
    
    print(f"\n📋 SOLICITUD (muy restrictiva):")
    print(f"   Evento: {request_extreme.event_type.value}")
    print(f"   Dietas: {request_extreme.required_diets}")
    print(f"   Alergias: {request_extreme.restricted_ingredients}")
    
    # Contar candidatos reales
    extreme_candidates = [
        c for c in all_cases if not c.is_negative and
        all(diet in c.menu.get_all_diets() for diet in request_extreme.required_diets)
    ]
    
    print(f"\n📊 Casos que cumplen dietas: {len(extreme_candidates)}")
    
    results_extreme = retriever.retrieve(request_extreme, k=5)
    
    print(f"\n✅ CANDIDATOS RECUPERADOS: {len(results_extreme)}")
    
    if len(extreme_candidates) < 3:
        print("   ⚠️  FALLBACK ACTIVADO:")
        print("      Quedan <3 candidatos tras filtrar por dietas")
        print("      → Sistema mantiene más candidatos para ADAPT")
        print("      → ADAPT intentará adaptar casos menos compatibles")
    
    # ========================================================================
    # RESUMEN
    # ========================================================================
    print("\n" + "="*70)
    print("📋 RESUMEN DEL ENFOQUE HÍBRIDO")
    print("="*70)
    
    print("\n✅ RETRIEVE filtra restricciones CRÍTICAS:")
    print("   • Dietas obligatorias (vegan, vegetarian, gluten-free...)")
    print("   • Alergias alimentarias (nuts, dairy, shellfish...)")
    print("   • Fallback: Si quedan <3 candidatos, no filtrar")
    
    print("\n🔧 ADAPT maneja restricciones ADAPTABLES:")
    print("   • Cultura culinaria (puede cambiar platos/ingredientes)")
    print("   • Precio (puede cambiar platos más baratos/caros)")
    print("   • Temporada (puede ajustar temperatura)")
    print("   • Estilo (puede cambiar presentación)")
    
    print("\n🎯 BENEFICIOS:")
    print("   ✓ No desperdicia intentos de adaptación")
    print("   ✓ Cada restricción validada UNA sola vez")
    print("   ✓ Scoring maximiza similitud entre candidatos VIABLES")
    print("   ✓ ADAPT solo valida (no busca alternativas)")

if __name__ == "__main__":
    main()
