#!/usr/bin/env python3
"""
Demo de adaptación cultural completa con sustitución de ingredientes.

Muestra cómo el sistema CBR adapta menús de una cultura a otra,
sustituyendo ingredientes para hacer el plato más apropiado culturalmente.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle, CulturalTradition
)


def print_menu_details(menu, title="MENÚ"):
    """Imprime detalles de un menú incluyendo ingredientes"""
    print(f"\n{title}")
    print("=" * 70)
    
    for dish_type, dish_attr in [
        ("Starter", "starter"),
        ("Main", "main_course"),
        ("Dessert", "dessert")
    ]:
        dish = getattr(menu, dish_attr)
        print(f"\n{dish_type}: {dish.name}")
        print(f"  Precio: {dish.price}€")
        
        if dish.ingredients:
            print(f"  Ingredientes: {', '.join(dish.ingredients[:8])}")
            if len(dish.ingredients) > 8:
                print(f"               ... y {len(dish.ingredients) - 8} más")
    
    print(f"\nBebida: {menu.beverage.name}")
    print(f"TOTAL: {menu.total_price:.2f}€/persona")
    
    if menu.cultural_theme:
        print(f"Cultura: {menu.cultural_theme.value}")
    
    # Mostrar adaptaciones culturales si existen
    if menu.cultural_adaptations:
        print(f"\n🔄 ADAPTACIONES CULTURALES:")
        for adaptation in menu.cultural_adaptations:
            # Hay dos tipos: dish_replacement y adaptación de ingredientes
            if 'adaptation_type' in adaptation and adaptation['adaptation_type'] == 'dish_replacement':
                print(f"   • 🔄 PLATO REEMPLAZADO: {adaptation['original_dish']} → {adaptation['dish_name']}")
                print(f"     Razón: {adaptation['reason']}")
            else:
                # Adaptación de ingrediente
                print(f"   • {adaptation['dish_name']}:")
                print(f"     {adaptation['original_ingredient']} → {adaptation['adapted_ingredient']}")
                print(f"     Razón: {adaptation['reason']}")
                print(f"     Confianza: {adaptation['confidence']*100:.0f}%")


def demo_cultural_adaptation():
    """Demo de adaptación cultural completa"""
    
    print("=" * 70)
    print("🌍 DEMO: ADAPTACIÓN CULTURAL CON INGREDIENTES")
    print("=" * 70)
    
    # Configurar sistema
    config = CBRConfig(verbose=True, max_proposals=1)
    cbr = ChefDigitalCBR(config)
    
    print("\n📖 ESCENARIO:")
    print("-" * 70)
    print("Un cliente solicita un menú ITALIANO para una boda,")
    print("pero el sistema tiene casos exitosos de otras culturas.")
    print("Veremos cómo adapta un caso MEXICANO a preferencias ITALIANAS.")
    
    # Solicitud con preferencia ITALIANA
    request_italian = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_max=100.0,
        season=Season.SPRING,
        preferred_style=CulinaryStyle.GOURMET,
        cultural_preference=CulturalTradition.ITALIAN,
        wants_wine=True
    )
    
    print("\n📋 SOLICITUD:")
    print("-" * 70)
    print(f"   Evento: {request_italian.event_type.value}")
    print(f"   Temporada: {request_italian.season.value}")
    print(f"   Presupuesto: {request_italian.price_max}€/persona")
    print(f"   Preferencia cultural: {request_italian.cultural_preference.value.upper()}")
    print(f"   Estilo: {request_italian.preferred_style.value}")
    
    # Procesar solicitud
    result = cbr.process_request(request_italian)
    
    if result.proposed_menus:
        menu_propuesto = result.proposed_menus[0]
        
        print_menu_details(menu_propuesto.menu, "✅ MENÚ PROPUESTO")
        
        # Mostrar el caso fuente
        if menu_propuesto.source_case:
            source_menu = menu_propuesto.source_case.menu
            print(f"\n📚 CASO FUENTE:")
            print(f"   ID: {menu_propuesto.source_case.id}")
            if source_menu.cultural_theme:
                print(f"   Cultura original: {source_menu.cultural_theme.value}")
            print(f"   Feedback: {menu_propuesto.source_case.feedback_score}/5")
        
        # Mostrar similitud
        print(f"\n📊 MÉTRICAS:")
        print(f"   Similitud con caso: {menu_propuesto.similarity_score * 100:.1f}%")
    else:
        print("\n❌ No se pudieron generar propuestas")
    
    print("\n" + "=" * 70)
    print("🔁 PROBANDO ADAPTACIÓN INVERSA...")
    print("=" * 70)
    print("Ahora solicitaremos cultura MEXICANA para ver la diferencia")
    
    # Solicitud MEXICANA
    request_mexican = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_max=100.0,
        season=Season.SPRING,
        preferred_style=CulinaryStyle.GOURMET,
        cultural_preference=CulturalTradition.MEXICAN,
        wants_wine=True
    )
    
    print(f"\n📋 Nueva preferencia cultural: {request_mexican.cultural_preference.value.upper()}")
    
    result2 = cbr.process_request(request_mexican)
    
    if result2.proposed_menus:
        menu_mexican = result2.proposed_menus[0]
        print_menu_details(menu_mexican.menu, "✅ MENÚ MEXICANO")
        
        if menu_mexican.source_case:
            source = menu_mexican.source_case.menu
            if source.cultural_theme:
                print(f"\n   (Adaptado de cultura: {source.cultural_theme.value})")
    
    print("\n" + "=" * 70)
    print("📊 ESTADÍSTICAS FINALES")
    print("=" * 70)
    
    stats = cbr.get_statistics()
    cb_stats = cbr.case_base.get_statistics()
    
    print(f"\n📚 Base de Casos:")
    print(f"   Total casos: {stats['case_base']['total_cases']}")
    print(f"   Platos: {cb_stats['total_dishes']}")
    print(f"   Bebidas: {cb_stats['total_beverages']}")
    
    # Distribución cultural
    culturas = {}
    for caso in cbr.case_base.get_all_cases():
        if caso.menu.cultural_theme:
            c = caso.menu.cultural_theme.value
            culturas[c] = culturas.get(c, 0) + 1
    
    print(f"\n🌍 Culturas en base de casos:")
    for cultura, count in sorted(culturas.items()):
        print(f"   • {cultura}: {count}")
    
    print()


if __name__ == "__main__":
    demo_cultural_adaptation()
