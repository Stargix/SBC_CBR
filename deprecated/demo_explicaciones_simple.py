"""
Demo simple de explicaciones CBR - Muestra cómo se generan las explicaciones.

Este script demuestra:
1. Qué genera las explicaciones (ExplanationGenerator)
2. Qué información incluyen (RETRIEVE, ADAPT, REVISE)
3. Cómo varían según el contexto de la solicitud
"""

import sys
from pathlib import Path

# Añadir develop al path
develop_path = Path(__file__).parent / "develop"
sys.path.insert(0, str(develop_path))

from develop import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle, CulturalTradition
)


def print_separator(char="=", length=90):
    print("\n" + char * length)


def demo_caso_basico():
    """Caso 1: Boda básica - mostrar estructura de explicación básica"""
    print_separator()
    print("CASO 1: BODA BÁSICA - Sin restricciones complejas")
    print_separator()
    
    print("\n📝 QUÉ VAMOS A VER:")
    print("   • Desglose de similitud por criterios (RETRIEVE)")
    print("   • Adaptaciones mínimas (ADAPT)")
    print("   • Validación del menú (REVISE)")
    
    system = ChefDigitalCBR(CBRConfig(verbose=False, max_proposals=2))
    
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=150,
        season=Season.SUMMER,
        preferred_style=CulinaryStyle.CLASSIC
    )
    
    print("\n📋 SOLICITUD:")
    print(f"   • Evento: Boda (100 comensales)")
    print(f"   • Presupuesto: 80-150€/persona")
    print(f"   • Temporada: Verano")
    print(f"   • Estilo: Clásico")
    
    result = system.process_request(request)
    
    if result.success and result.proposed_menus:
        menu = result.proposed_menus[0]
        
        print(f"\n✅ RESULTADO:")
        print(f"   • Menús generados: {len(result.proposed_menus)}")
        print(f"   • Mejor similitud: {menu.similarity_score:.1%}")
        print(f"   • Adaptaciones: {len(menu.adaptations)}")
        
        print_separator("-")
        print("EXPLICACIONES GENERADAS POR EL SISTEMA:")
        print_separator("-")
        print(result.explanations)
    else:
        print("\n❌ No se generaron menús")


def demo_caso_adaptaciones():
    """Caso 2: Vegetariano italiano - mostrar adaptaciones culturales y dietéticas"""
    print_separator()
    print("CASO 2: CORPORATIVO VEGETARIANO ITALIANO")
    print_separator()
    
    print("\n📝 QUÉ VAMOS A VER:")
    print("   • Adaptaciones dietéticas (vegetarian)")
    print("   • Adaptaciones culturales (italiana)")
    print("   • Sustituciones de ingredientes")
    
    system = ChefDigitalCBR(CBRConfig(verbose=False, max_proposals=2))
    
    request = Request(
        event_type=EventType.CORPORATE,
        num_guests=50,
        price_min=40,
        price_max=70,
        season=Season.SPRING,
        preferred_style=CulinaryStyle.REGIONAL,
        required_diets=["vegetarian"],
        cultural_preference=CulturalTradition.ITALIAN
    )
    
    print("\n📋 SOLICITUD:")
    print(f"   • Evento: Corporativo (50 comensales)")
    print(f"   • Presupuesto: 40-70€/persona")
    print(f"   • Restricción: VEGETARIANO ⚠️")
    print(f"   • Cultura: ITALIANA 🇮🇹")
    
    result = system.process_request(request)
    
    if result.success and result.proposed_menus:
        menu = result.proposed_menus[0]
        
        print(f"\n✅ RESULTADO:")
        print(f"   • Menú: {menu.menu.starter.name} / {menu.menu.main_course.name} / {menu.menu.dessert.name}")
        print(f"   • Precio: {menu.menu.total_price:.2f}€")
        print(f"   • Adaptaciones realizadas: {len(menu.adaptations)}")
        
        if menu.adaptations:
            print("\n   📝 ADAPTACIONES:")
            for i, adapt in enumerate(menu.adaptations[:5], 1):
                print(f"      {i}. {adapt}")
        
        print_separator("-")
        print("EXPLICACIONES GENERADAS:")
        print_separator("-")
        # Mostrar solo primeras 3000 caracteres para no saturar
        explanations = result.explanations
        if len(explanations) > 3000:
            print(explanations[:3000])
            print("\n... [Explicación truncada para mejor visualización] ...")
        else:
            print(explanations)
    else:
        print("\n❌ No se generaron menús")


def demo_caso_restricciones():
    """Caso 3: Vegano con presupuesto bajo - mostrar validaciones y warnings"""
    print_separator()
    print("CASO 3: FAMILIAR VEGANO - Presupuesto Ajustado")
    print_separator()
    
    print("\n📝 QUÉ VAMOS A VER:")
    print("   • Adaptaciones por restricciones estrictas (vegan)")
    print("   • Ajustes de precio (presupuesto bajo)")
    print("   • Warnings de validación (REVISE)")
    
    system = ChefDigitalCBR(CBRConfig(verbose=False, max_proposals=2))
    
    request = Request(
        event_type=EventType.FAMILIAR,
        num_guests=30,
        price_min=25,
        price_max=40,
        season=Season.AUTUMN,
        required_diets=["vegan"],
        restricted_ingredients=["honey", "gelatin"]
    )
    
    print("\n📋 SOLICITUD:")
    print(f"   • Evento: Familiar (30 comensales)")
    print(f"   • Presupuesto: 25-40€/persona 💰 (BAJO)")
    print(f"   • Restricción: VEGANO ⚠️")
    print(f"   • Prohibido: miel, gelatina")
    
    result = system.process_request(request)
    
    if result.success and result.proposed_menus:
        menu = result.proposed_menus[0]
        
        print(f"\n✅ RESULTADO:")
        print(f"   • Precio final: {menu.menu.total_price:.2f}€")
        print(f"   • Adaptaciones: {len(menu.adaptations)}")
        
        if menu.validation_result:
            print(f"\n   🔍 VALIDACIÓN:")
            print(f"      • Estado: {menu.validation_result.status.value}")
            if menu.validation_result.issues:
                print(f"      • Issues: {len(menu.validation_result.issues)}")
        
        print_separator("-")
        print("EXPLICACIONES GENERADAS:")
        print_separator("-")
        explanations = result.explanations
        if len(explanations) > 3000:
            print(explanations[:3000])
            print("\n... [Explicación truncada] ...")
        else:
            print(explanations)
    else:
        print("\n❌ No se generaron menús")


def main():
    """Ejecuta las demos de explicación."""
    print("\n" + "╔" + "═" * 88 + "╗")
    print("║" + " " * 15 + "DEMO: CÓMO SE GENERAN LAS EXPLICACIONES EN EL SISTEMA CBR" + " " * 15 + "║")
    print("╚" + "═" * 88 + "╝")
    
    print("\nEste demo muestra cómo el sistema CBR genera explicaciones detalladas.")
    print("\nLas explicaciones se generan en el módulo 'explanation.py' y cubren:")
    print("  1. RETRIEVE: Por qué se seleccionó cada caso (similitud desglosada)")
    print("  2. ADAPT: Qué adaptaciones se hicieron (culturales, dietéticas, precio)")
    print("  3. REVISE: Validación del menú (warnings, errores)")
    
    print("\nSe ejecutarán 3 casos con características diferentes:\n")
    
    try:
        # Caso 1: Básico
        demo_caso_basico()
        input("\n>>> Presiona Enter para continuar al Caso 2...")
        
        # Caso 2: Con adaptaciones
        demo_caso_adaptaciones()
        input("\n>>> Presiona Enter para continuar al Caso 3...")
        
        # Caso 3: Con restricciones
        demo_caso_restricciones()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print_separator()
    print("🎉 DEMO COMPLETADO")
    print_separator()
    
    print("\n📚 RESUMEN:")
    print("\nLas explicaciones se generan en:")
    print("   • develop/cycle/explanation.py - Módulo de explicabilidad")
    print("\nExplican:")
    print("   • Por qué se seleccionó un menú (similitud por criterios)")
    print("   • Qué adaptaciones se hicieron (culturales, dietéticas, precio)")
    print("   • Cómo se validó (warnings, errores detectados)")
    print("\nCada solicitud diferente activa diferentes partes del sistema,")
    print("generando explicaciones personalizadas al contexto.\n")


if __name__ == "__main__":
    main()
