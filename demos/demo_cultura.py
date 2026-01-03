#!/usr/bin/env python3
"""
Demo del sistema CBR con preferencias culturales.

Muestra cómo el sistema recupera casos similares basándose en
la preferencia cultural del cliente.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle, CulturalTradition
)


def demo_cultural_preference():
    """Demo de solicitudes con diferentes preferencias culturales."""
    
    print("=" * 70)
    print("🌍 SISTEMA CBR - DEMO DE PREFERENCIAS CULTURALES")
    print("=" * 70)
    
    # Configurar sistema
    config = CBRConfig(verbose=False, max_proposals=3)
    cbr = ChefDigitalCBR(config)
    
    # Lista de culturas a probar
    culturas = [
        (CulturalTradition.ITALIAN, "Italiana", "🇮🇹"),
        (CulturalTradition.MEXICAN, "Mexicana", "🇲🇽"),
        (CulturalTradition.JAPANESE, "Japonesa", "🇯🇵"),
        (CulturalTradition.FRENCH, "Francesa", "🇫🇷"),
        (CulturalTradition.CHINESE, "China", "🇨🇳"),
        (CulturalTradition.INDIAN, "India", "🇮🇳"),
    ]
    
    evento_base = EventType.WEDDING
    temporada = Season.SPRING
    presupuesto = 80.0
    
    print(f"\n📋 Configuración Base:")
    print(f"   Evento: {evento_base.value}")
    print(f"   Temporada: {temporada.value}")
    print(f"   Presupuesto: {presupuesto}€/persona")
    print(f"   Comensales: 100")
    print("\n" + "=" * 70)
    
    for cultura, nombre, bandera in culturas:
        print(f"\n{bandera} PREFERENCIA CULTURAL: {nombre.upper()}")
        print("-" * 70)
        
        # Crear solicitud con preferencia cultural
        request = Request(
            event_type=evento_base,
            num_guests=100,
            price_max=presupuesto,
            season=temporada,
            preferred_style=CulinaryStyle.GOURMET,
            cultural_preference=cultura,
            wants_wine=True
        )
        
        # Procesar
        result = cbr.process_request(request)
        
        # Mostrar resultado resumido
        if result.proposed_menus:
            menu_top = result.proposed_menus[0]
            print(f"\n✅ MEJOR PROPUESTA:")
            print(f"   Starter: {menu_top.menu.starter.name}")
            print(f"   Main: {menu_top.menu.main_course.name}")
            print(f"   Dessert: {menu_top.menu.dessert.name}")
            print(f"   Precio: {menu_top.menu.total_price:.2f}€/persona")
            print(f"   Similitud: {menu_top.similarity_score * 100:.1f}%")
            
            # Mostrar cultura del caso base si está disponible
            if menu_top.source_case and menu_top.source_case.menu.cultural_theme:
                cultura_caso = menu_top.source_case.menu.cultural_theme.value
                print(f"   Cultura base del caso: {cultura_caso}")
        else:
            print("   ❌ No se encontraron menús adecuados")
    
    print("\n" + "=" * 70)
    print("📊 ESTADÍSTICAS FINALES")
    print("=" * 70)
    stats = cbr.get_statistics()
    print(f"\n📚 Base de Casos:")
    print(f"   Total casos: {stats['case_base']['total_cases']}")
    
    cb_stats = cbr.case_base.get_statistics()
    print(f"   Platos: {cb_stats['total_dishes']}")
    print(f"   Bebidas: {cb_stats['total_beverages']}")
    print(f"   Feedback promedio: {cb_stats['average_feedback']:.1f}/5")
    
    # Mostrar distribución cultural
    culturas_en_base = {}
    for caso in cbr.case_base.get_all_cases():
        if caso.menu.cultural_theme:
            cultura = caso.menu.cultural_theme.value
            culturas_en_base[cultura] = culturas_en_base.get(cultura, 0) + 1
    
    print(f"\n🌍 Distribución Cultural en Base de Casos:")
    for cultura, count in sorted(culturas_en_base.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cultura}: {count} casos")
    
    print()


if __name__ == "__main__":
    demo_cultural_preference()
