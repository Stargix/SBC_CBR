"""
Demo: Recalculo de similitud global después de ADAPT.

Muestra cómo la similitud cambia después de las adaptaciones,
permitiendo comparar casos adaptados con su similitud REAL.
"""

from develop.core.models import Request, EventType, Season
from develop.core.case_base import CaseBase
from develop.cycle.retrieve import CaseRetriever
from develop.cycle.adapt import CaseAdapter

def main():
    print("="*80)
    print("📊 DEMO: RECALCULO DE SIMILITUD GLOBAL DESPUÉS DE ADAPT")
    print("="*80)
    
    # Cargar base de casos
    case_base = CaseBase()
    case_base.load_from_file("config/initial_cases.json")
    
    retriever = CaseRetriever(case_base)
    adapter = CaseAdapter(case_base)
    
    print(f"\n📖 Base de casos: {len(case_base.get_all_cases())} casos cargados")
    
    # ========================================================================
    # TEST: Solicitud con cultura específica
    # ========================================================================
    print("\n" + "="*80)
    print("TEST: Adaptación cultural (Italian)")
    print("="*80)
    
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=120,
        season=Season.SPRING,
        wants_wine=True,
        required_diets=[],
        restricted_ingredients=[],
        cultural_preference="italian"
    )
    
    print(f"\n📋 SOLICITUD:")
    print(f"   Evento: {request.event_type.value}")
    print(f"   Presupuesto: {request.price_min}-{request.price_max}€")
    print(f"   Preferencia cultural: {request.cultural_preference}")
    
    # RETRIEVE: buscar casos similares
    print(f"\n🔍 FASE RETRIEVE:")
    results = retriever.retrieve(request, k=3)
    
    print(f"   Candidatos recuperados: {len(results)}")
    for r in results:
        print(f"   {r.rank}. Caso {r.case.id}")
        print(f"      Cultura original: {r.case.menu.cultural_theme or 'ninguna'}")
        print(f"      Similitud ORIGINAL: {r.similarity:.3f}")
    
    # ADAPT: adaptar casos al nuevo contexto
    print(f"\n🔧 FASE ADAPT:")
    adapted_menus = adapter.adapt(results, request, num_proposals=3)
    
    print(f"   Menús adaptados: {len(adapted_menus)}")
    
    for i, result in enumerate(adapted_menus, 1):
        print(f"\n   {'='*70}")
        print(f"   MENÚ ADAPTADO #{i}")
        print(f"   {'='*70}")
        
        if result.original_case:
            print(f"   📌 Caso base: {result.original_case.id}")
            print(f"      Cultura original: {result.original_case.menu.cultural_theme or 'ninguna'}")
        else:
            print(f"   📌 Menú generado desde cero")
        
        print(f"\n   📊 SIMILITUD:")
        print(f"      Original (RETRIEVE): {result.original_similarity:.3f}")
        print(f"      Final (ADAPT):       {result.final_similarity:.3f}")
        print(f"      {result.get_similarity_change()}")
        
        print(f"\n   🍽️  MENÚ FINAL:")
        print(f"      Starter:  {result.adapted_menu.starter.name}")
        print(f"      Main:     {result.adapted_menu.main_course.name}")
        print(f"      Dessert:  {result.adapted_menu.dessert.name}")
        print(f"      Cultura:  {result.adapted_menu.cultural_theme or 'ninguna'}")
        print(f"      Precio:   {result.adapted_menu.total_price:.2f}€")
        
        if result.adaptations_made:
            print(f"\n   🔄 ADAPTACIONES REALIZADAS ({len(result.adaptations_made)}):")
            for adaptation in result.adaptations_made[:5]:  # Máximo 5
                print(f"      • {adaptation}")
            if len(result.adaptations_made) > 5:
                print(f"      ... y {len(result.adaptations_made) - 5} más")
    
    # ========================================================================
    # ANÁLISIS: Comparación de similitudes
    # ========================================================================
    print("\n" + "="*80)
    print("📈 ANÁLISIS: ¿Cómo cambia la similitud con las adaptaciones?")
    print("="*80)
    
    for i, result in enumerate(adapted_menus, 1):
        if result.original_case:
            change = result.final_similarity - result.original_similarity
            change_pct = (change / result.original_similarity * 100) if result.original_similarity > 0 else 0
            
            print(f"\nMenú #{i} (caso {result.original_case.id}):")
            print(f"   Antes de ADAPT: {result.original_similarity:.3f}")
            print(f"   Después de ADAPT: {result.final_similarity:.3f}")
            print(f"   Cambio: {change:+.3f} ({change_pct:+.1f}%)")
            
            if abs(change) < 0.01:
                print(f"   → Adaptación mínima, similitud mantenida")
            elif change > 0:
                print(f"   → ✅ Adaptación MEJORÓ la similitud")
            else:
                print(f"   → ⚠️  Adaptación REDUJO similitud (trade-off necesario)")
    
    # ========================================================================
    # CONCLUSIÓN
    # ========================================================================
    print("\n" + "="*80)
    print("💡 CONCLUSIONES")
    print("="*80)
    
    print("\n✅ BENEFICIOS del recalculo de similitud:")
    print("   1. Sabemos la similitud REAL del menú final")
    print("   2. Podemos comparar casos adaptados objetivamente")
    print("   3. REVISE tiene datos precisos para validar")
    print("   4. Detectamos si adaptaciones empeoraron el caso")
    
    print("\n📊 COMPORTAMIENTO ESPERADO:")
    print("   • Adaptaciones culturales: pueden REDUCIR similitud inicial")
    print("     (cambiar platos afecta sabores, temperatura, etc.)")
    print("   • Adaptaciones de precio: generalmente MANTIENEN similitud")
    print("     (solo cambian platos por variantes similares)")
    print("   • Adaptaciones dietéticas: pueden REDUCIR mucho similitud")
    print("     (restricciones fuerzan cambios grandes)")
    
    print("\n🎯 ESTRATEGIA:")
    print("   • RETRIEVE busca casos con alta similitud inicial")
    print("   • ADAPT modifica lo necesario (puede reducir similitud)")
    print("   • Ordenamos por final_similarity (similitud REAL)")
    print("   • Resultado: MEJOR menú adaptado, no el menos modificado")

if __name__ == "__main__":
    main()
