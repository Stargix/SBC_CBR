#!/usr/bin/env python3
"""
Ejemplo de uso del sistema CBR de Chef Digital.

Este script demuestra cómo utilizar el sistema CBR para
obtener propuestas de menús personalizados.
"""

import sys
import os

# Añadir directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CBR import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle
)


def demo_wedding_menu():
    """Demostración: Menú para boda"""
    print("\n" + "=" * 60)
    print("DEMO 1: Propuesta de Menú para Boda")
    print("=" * 60)
    
    # Crear sistema CBR con casos iniciales
    config = CBRConfig(verbose=True, max_proposals=3)
    cbr = ChefDigitalCBR(config)
    
    # Crear solicitud
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_max=80.0,
        season=Season.SPRING,
        preferred_style=CulinaryStyle.GOURMET,
        required_diets=[],
    )
    
    print(f"\n📋 Solicitud:")
    print(f"   Evento: Boda")
    print(f"   Comensales: {request.num_guests}")
    print(f"   Presupuesto: {request.price_max}€/persona")
    print(f"   Temporada: Primavera")
    print(f"   Estilo: Gourmet")
    
    # Procesar solicitud
    result = cbr.process_request(request)
    
    # Mostrar resultados
    print(result.explanations)
    
    return result


def demo_corporate_vegetarian():
    """Demostración: Menú corporativo vegetariano"""
    print("\n" + "=" * 60)
    print("DEMO 2: Propuesta de Menú Corporativo Vegetariano")
    print("=" * 60)
    
    config = CBRConfig(verbose=True)
    cbr = ChefDigitalCBR(config)
    
    request = Request(
        event_type=EventType.CORPORATE,
        num_guests=60,
        price_max=45.0,
        season=Season.AUTUMN,
        preferred_style=CulinaryStyle.MODERN,
        required_diets=["vegetariano"],
    )
    
    print(f"\n📋 Solicitud:")
    print(f"   Evento: Corporativo")
    print(f"   Comensales: {request.num_guests}")
    print(f"   Presupuesto: {request.price_max}€/persona")
    print(f"   Temporada: Otoño")
    print(f"   Estilo: Moderno")
    print(f"   Restricciones: Vegetariano")
    
    result = cbr.process_request(request)
    print(result.explanations)
    
    return result


def demo_christening_catalan():
    """Demostración: Bautizo con cocina catalana"""
    print("\n" + "=" * 60)
    print("DEMO 3: Propuesta de Menú para Bautizo - Cocina Catalana")
    print("=" * 60)
    
    config = CBRConfig(verbose=True)
    cbr = ChefDigitalCBR(config)
    
    request = Request(
        event_type=EventType.CHRISTENING,
        num_guests=45,
        price_max=55.0,
        season=Season.SPRING,
        preferred_style=CulinaryStyle.REGIONAL,
        required_diets=[],
    )
    
    print(f"\n📋 Solicitud:")
    print(f"   Evento: Bautizo")
    print(f"   Comensales: {request.num_guests}")
    print(f"   Presupuesto: {request.price_max}€/persona")
    print(f"   Temporada: Primavera")
    print(f"   Estilo: Regional (Catalán)")
    
    result = cbr.process_request(request)
    print(result.explanations)
    
    return result


def demo_system_stats():
    """Muestra estadísticas del sistema"""
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS DEL SISTEMA")
    print("=" * 60)
    
    config = CBRConfig(verbose=False)
    cbr = ChefDigitalCBR(config)
    
    stats = cbr.get_statistics()
    
    print(f"\n📊 Información del Sistema:")
    print(f"   Versión: {stats['system']['version']}")
    print(f"   Max. propuestas: {stats['system']['config']['max_proposals']}")
    print(f"   Similitud mínima: {stats['system']['config']['min_similarity']:.0%}")
    
    print(f"\n📚 Base de Casos:")
    print(f"   Total casos: {stats['case_base']['total_cases']}")
    print(f"   Casos exitosos: {stats['case_base']['successful_cases']}")
    print(f"   Tasa de éxito: {stats['case_base']['success_rate']:.0%}")
    print(f"   Feedback promedio: {stats['case_base']['avg_feedback']:.1f}/5")
    
    print(f"\n🎉 Eventos soportados:")
    for event in stats['supported_events']:
        print(f"   - {event}")
    
    print(f"\n🍽️ Estilos culinarios:")
    for style in stats['supported_styles']:
        print(f"   - {style}")
    
    print(f"\n🌍 Tradiciones culturales:")
    for tradition in stats['cultural_traditions']:
        print(f"   - {tradition}")


def explain_culinary_style(style: CulinaryStyle):
    """Explica un estilo culinario"""
    config = CBRConfig()
    cbr = ChefDigitalCBR(config)
    
    explanation = cbr.explain_style(style)
    print(explanation)


def main():
    """Función principal"""
    print("=" * 60)
    print("🍽️  CHEF DIGITAL - Sistema CBR de Menús")
    print("=" * 60)
    print("\nBienvenido al sistema de propuesta de menús basado en")
    print("Razonamiento Basado en Casos (CBR).")
    
    # Ejecutar demos
    demo_system_stats()
    
    print("\n" + "-" * 60)
    print("Seleccione una demo:")
    print("  1. Boda elegante (Gourmet)")
    print("  2. Evento corporativo vegetariano (Moderno)")
    print("  3. Bautizo catalán (Regional)")
    print("  4. Ver todos los estilos culinarios")
    print("  5. Ejecutar todas las demos")
    print("  0. Salir")
    print("-" * 60)
    
    try:
        choice = input("\nOpción [1-5, 0]: ").strip()
        
        if choice == "1":
            demo_wedding_menu()
        elif choice == "2":
            demo_corporate_vegetarian()
        elif choice == "3":
            demo_christening_catalan()
        elif choice == "4":
            print("\n📖 ESTILOS CULINARIOS DISPONIBLES:")
            for style in CulinaryStyle:
                print("\n" + "-" * 40)
                explain_culinary_style(style)
        elif choice == "5":
            demo_wedding_menu()
            demo_corporate_vegetarian()
            demo_christening_catalan()
        elif choice == "0":
            print("\n¡Hasta pronto! 🍽️")
        else:
            print("Opción no válida")
    except KeyboardInterrupt:
        print("\n\n¡Hasta pronto! 🍽️")
    except EOFError:
        # Si no hay entrada interactiva, ejecutar demo por defecto
        print("\n[Ejecutando demo por defecto]")
        demo_wedding_menu()


if __name__ == "__main__":
    main()
