#!/usr/bin/env python3
"""
Demo completo del sistema CBR con adaptación cultural de ingredientes.

Este script muestra todo el flujo:
1. Solicitud con preferencia cultural
2. Recuperación de casos similares
3. Adaptación cultural con sustitución de ingredientes
4. Retención de casos adaptados exitosos
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle, CulturalTradition,
    FeedbackData
)


def main():
    print("=" * 80)
    print("🌍 SISTEMA CBR - DEMO COMPLETO DE ADAPTACIÓN CULTURAL")
    print("=" * 80)
    
    # Configurar sistema
    config = CBRConfig(verbose=False, max_proposals=2, enable_learning=True)
    cbr = ChefDigitalCBR(config)
    
    print("\n📊 ESTADO INICIAL:")
    print("-" * 80)
    stats_inicial = cbr.case_base.get_statistics()
    print(f"   Casos en base: {stats_inicial['total_cases']}")
    
    # Distribución cultural
    culturas_init = {}
    for caso in cbr.case_base.get_all_cases():
        if caso.menu.cultural_theme:
            c = caso.menu.cultural_theme.value
            culturas_init[c] = culturas_init.get(c, 0) + 1
    
    print(f"   Distribución cultural:")
    for cultura, count in sorted(culturas_init.items()):
        print(f"      • {cultura}: {count} casos")
    
    # ==================== ESCENARIO 1: Solicitud Italiana ====================
    print("\n" + "=" * 80)
    print("📋 ESCENARIO 1: Cliente solicita menú ITALIANO")
    print("=" * 80)
    
    request_italian = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_max=90.0,
        season=Season.SPRING,
        preferred_style=CulinaryStyle.GOURMET,
        cultural_preference=CulturalTradition.ITALIAN,
        wants_wine=True
    )
    
    print(f"\n   Evento: {request_italian.event_type.value}")
    print(f"   Cultura preferida: {request_italian.cultural_preference.value.upper()}")
    print(f"   Presupuesto: {request_italian.price_max}€/persona")
    
    result1 = cbr.process_request(request_italian)
    
    # DEBUG: Mostrar casos recuperados
    print(f"\n   🔍 DEBUG - Casos recuperados:")
    if hasattr(result1, 'retrieval_results') and result1.retrieval_results:
        for i, rr in enumerate(result1.retrieval_results[:3], 1):
            print(f"      {i}. Similitud: {rr.similarity_score:.1%}")
            print(f"         Cultura original: {rr.case.menu.cultural_theme}")
            print(f"         Starter: {rr.case.menu.starter.name}")
    
    if result1.proposed_menus:
        menu1 = result1.proposed_menus[0]
        print(f"\n✅ MEJOR PROPUESTA:")
        print(f"   Starter: {menu1.menu.starter.name}")
        print(f"   Main: {menu1.menu.main_course.name}")
        print(f"   Dessert: {menu1.menu.dessert.name}")
        print(f"   Precio: {menu1.menu.total_price:.2f}€")
        print(f"   Similitud global: {menu1.similarity_score * 100:.1f}%")
        
        if menu1.menu.cultural_theme:
            print(f"   Cultura del menú: {menu1.menu.cultural_theme.value}")
        
        # Mostrar adaptaciones culturales realizadas con detalles de mejora
        if menu1.menu.cultural_adaptations:
            print(f"\n   🔄 ADAPTACIONES CULTURALES REALIZADAS ({len(menu1.menu.cultural_adaptations)} cambios):")
            
            # Agrupar por plato
            by_dish = {}
            for adapt in menu1.menu.cultural_adaptations:
                dish_name = adapt['dish_name']
                if dish_name not in by_dish:
                    by_dish[dish_name] = []
                by_dish[dish_name].append(adapt)
            
            for dish_name, adaptations in by_dish.items():
                # Verificar si es reemplazo de plato completo
                if adaptations and 'adaptation_type' in adaptations[0] and adaptations[0]['adaptation_type'] == 'dish_replacement':
                    adapt = adaptations[0]
                    print(f"\n      📍 {adapt['original_dish']} → {dish_name}:")
                    print(f"         🔄 PLATO REEMPLAZADO COMPLETAMENTE")
                    print(f"         Razón: {adapt['reason']}")
                    print(f"         Similitud cultural: {adapt['score_before']}→{adapt['score_after']}")
                else:
                    # Adaptaciones de ingredientes
                    print(f"\n      📍 {dish_name}:")
                    if adaptations and 'score_before' in adaptations[0]:
                        score_before = adaptations[0]['score_before']
                        score_after = adaptations[-1]['score_after']
                        print(f"         Similitud cultural: {score_before}→{score_after}")
                    
                    for adapt in adaptations:
                        if 'original_ingredient' in adapt:  # Adaptación de ingrediente
                            improvement = adapt.get('improvement', '')
                            print(f"         • {adapt['original_ingredient']} → {adapt['adapted_ingredient']} {improvement}")
                            print(f"           Razón: {adapt['reason']}")
                            print(f"           Confianza: {adapt['confidence']:.0%}")
        else:
            print(f"\n   ℹ️  Sin adaptaciones culturales (platos ya apropiados para la cultura solicitada)")
        
        # Simular feedback positivo
        print(f"\n   📝 Cliente muy satisfecho - Feedback: 4.8/5")
        feedback1 = FeedbackData(
            menu_id=menu1.menu.id,
            success=True,
            score=4.8,
            comments="Excelente menú italiano, muy auténtico",
            would_recommend=True
        )
        
        # Retener el caso
        retained, msg = cbr.retainer.retain(
            request_italian, 
            menu1.menu, 
            feedback1,
            source_case=menu1.source_case
        )
        
        if retained:
            print(f"   ✅ {msg}")
    
    # ==================== ESCENARIO 2: Solicitud Mexicana ====================
    print("\n" + "=" * 80)
    print("📋 ESCENARIO 2: Cliente solicita menú MEXICANO")
    print("=" * 80)
    
    request_mexican = Request(
        event_type=EventType.COMMUNION,
        num_guests=80,
        price_max=70.0,
        season=Season.SUMMER,
        preferred_style=CulinaryStyle.REGIONAL,
        cultural_preference=CulturalTradition.MEXICAN,
        wants_wine=False
    )
    
    print(f"\n   Evento: {request_mexican.event_type.value}")
    print(f"   Cultura preferida: {request_mexican.cultural_preference.value.upper()}")
    print(f"   Presupuesto: {request_mexican.price_max}€/persona")
    
    result2 = cbr.process_request(request_mexican)
    
    if result2.proposed_menus:
        menu2 = result2.proposed_menus[0]
        print(f"\n✅ MEJOR PROPUESTA:")
        print(f"   Starter: {menu2.menu.starter.name}")
        print(f"   Main: {menu2.menu.main_course.name}")
        print(f"   Dessert: {menu2.menu.dessert.name}")
        print(f"   Precio: {menu2.menu.total_price:.2f}€")
        
        if menu2.menu.cultural_adaptations:
            print(f"\n   🔄 {len(menu2.menu.cultural_adaptations)} ingredientes adaptados")
        
        # Simular feedback positivo
        print(f"\n   📝 Cliente satisfecho - Feedback: 4.5/5")
        feedback2 = FeedbackData(
            menu_id=menu2.menu.id,
            success=True,
            score=4.5,
            comments="Muy bueno, sabores auténticos",
            would_recommend=True
        )
        
        retained, msg = cbr.retainer.retain(
            request_mexican,
            menu2.menu,
            feedback2,
            source_case=menu2.source_case
        )
        
        if retained:
            print(f"   ✅ {msg}")
    
    # ==================== ESCENARIO 3: Solicitud Japonesa ====================
    print("\n" + "=" * 80)
    print("📋 ESCENARIO 3: Cliente solicita menú JAPONÉS")
    print("=" * 80)
    
    request_japanese = Request(
        event_type=EventType.CORPORATE,
        num_guests=50,
        price_max=85.0,
        season=Season.AUTUMN,
        preferred_style=CulinaryStyle.MODERN,
        cultural_preference=CulturalTradition.JAPANESE,
        wants_wine=False
    )
    
    print(f"\n   Evento: {request_japanese.event_type.value}")
    print(f"   Cultura preferida: {request_japanese.cultural_preference.value.upper()}")
    
    result3 = cbr.process_request(request_japanese)
    
    if result3.proposed_menus:
        menu3 = result3.proposed_menus[0]
        print(f"\n✅ PROPUESTA:")
        print(f"   Starter: {menu3.menu.starter.name}")
        print(f"   Main: {menu3.menu.main_course.name}")
        print(f"   Dessert: {menu3.menu.dessert.name}")
        print(f"   Precio: {menu3.menu.total_price:.2f}€")
        print(f"   Similitud global: {menu3.similarity_score * 100:.1f}%")
        
        if menu3.menu.cultural_theme:
            print(f"   Cultura del menú: {menu3.menu.cultural_theme.value}")
        
        # Mostrar adaptaciones culturales
        if menu3.menu.cultural_adaptations:
            print(f"\n   🔄 ADAPTACIONES CULTURALES REALIZADAS ({len(menu3.menu.cultural_adaptations)} cambios):")
            
            # Agrupar por plato
            by_dish = {}
            for adapt in menu3.menu.cultural_adaptations:
                dish_name = adapt['dish_name']
                if dish_name not in by_dish:
                    by_dish[dish_name] = []
                by_dish[dish_name].append(adapt)
            
            for dish_name, adaptations in by_dish.items():
                # Verificar si es reemplazo de plato completo
                if adaptations and 'adaptation_type' in adaptations[0] and adaptations[0]['adaptation_type'] == 'dish_replacement':
                    adapt = adaptations[0]
                    print(f"\n      📍 {adapt['original_dish']} → {dish_name}:")
                    print(f"         🔄 PLATO REEMPLAZADO COMPLETAMENTE")
                    print(f"         Razón: {adapt['reason']}")
                    print(f"         Similitud cultural: {adapt['score_before']}→{adapt['score_after']}")
                else:
                    # Adaptaciones de ingredientes
                    print(f"\n      📍 {dish_name}:")
                    if adaptations and 'score_before' in adaptations[0]:
                        score_before = adaptations[0]['score_before']
                        score_after = adaptations[-1]['score_after']
                        print(f"         Similitud cultural: {score_before}→{score_after}")
                    
                    for adapt in adaptations:
                        if 'original_ingredient' in adapt:  # Adaptación de ingrediente
                            improvement = adapt.get('improvement', '')
                            print(f"         • {adapt['original_ingredient']} → {adapt['adapted_ingredient']} {improvement}")
                            print(f"           Razón: {adapt['reason']}")
                            print(f"           Confianza: {adapt['confidence']:.0%}")
        else:
            print(f"\n   ℹ️  Sin adaptaciones culturales")
    
    # ==================== RESUMEN FINAL ====================
    print("\n" + "=" * 80)
    print("📊 RESUMEN FINAL DEL SISTEMA")
    print("=" * 80)
    
    stats_final = cbr.case_base.get_statistics()
    print(f"\n   Casos totales: {stats_final['total_cases']}")
    print(f"   Incremento: +{stats_final['total_cases'] - stats_inicial['total_cases']} casos")
    
    # Nueva distribución cultural
    culturas_final = {}
    casos_adaptados = 0
    
    for caso in cbr.case_base.get_all_cases():
        if caso.menu.cultural_theme:
            c = caso.menu.cultural_theme.value
            culturas_final[c] = culturas_final.get(c, 0) + 1
        
        if caso.source == "cultural_adaptation":
            casos_adaptados += 1
    
    print(f"\n   📚 Distribución cultural actualizada:")
    for cultura, count in sorted(culturas_final.items()):
        delta = count - culturas_init.get(cultura, 0)
        delta_str = f" (+{delta})" if delta > 0 else ""
        print(f"      • {cultura}: {count}{delta_str}")
    
    print(f"\n   🔄 Casos adaptados culturalmente: {casos_adaptados}")
    print(f"   ⭐ Feedback promedio: {stats_final['average_feedback']:.2f}/5")
    
    print(f"\n   🎯 CONCLUSIÓN:")
    print(f"      El sistema ha aprendido de las solicitudes culturales,")
    print(f"      adaptando menús existentes y reteniendo los exitosos.")
    print(f"      Ahora puede servir mejor a clientes con preferencias culturales.")
    
    print()


if __name__ == "__main__":
    main()
