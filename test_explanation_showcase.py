"""
Test de Explicabilidad - Showcasing de Explicaciones CBR

Este test demuestra cómo el sistema genera explicaciones
detalladas para diferentes tipos de solicitudes y escenarios.

Muestra las 4 fases del CBR con explicaciones completas:
1. RETRIEVE: Desglose de similitud por criterios
2. ADAPT: Adaptaciones culturales, dietéticas, de precio
3. REVISE: Validaciones y warnings
4. RETAIN: (no mostrado aquí, ver demo_retain.py)

Cada solicitud está diseñada para activar diferentes partes
del sistema de explicabilidad.
"""

import sys
from pathlib import Path

# Añadir develop al path
develop_path = Path(__file__).parent / "develop"
sys.path.insert(0, str(develop_path))

from develop import (
    ChefDigitalCBR, create_cbr_system, CBRConfig,
    Request, EventType, Season, CulinaryStyle, CulturalTradition
)


def print_separator(title: str):
    """Imprime un separador visual."""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def print_subseparator(title: str):
    """Imprime un sub-separador."""
    print("\n" + "-" * 100)
    print(f"  {title}")
    print("-" * 100)


def test_case_1_simple_wedding():
    """
    Caso 1: Boda simple sin restricciones
    
    Objetivo: Mostrar explicación básica con desglose de similitud
    Adaptaciones esperadas: Mínimas o ninguna
    """
    print_separator("CASO 1: BODA SIMPLE - Sin Restricciones")
    
    system = create_cbr_system(verbose=False)
    
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=150,
        season=Season.SUMMER,
        preferred_style=CulinaryStyle.CLASSIC
    )
    
    result = system.process_request(request)
    
    if result.success and result.proposed_menus:
        print("\n📋 SOLICITUD:")
        print(f"   Tipo: {request.event_type.value}")
        print(f"   Comensales: {request.num_guests}")
        print(f"   Presupuesto: {request.price_min}-{request.price_max}€")
        print(f"   Temporada: {request.season.value}")
        print(f"   Estilo: {request.preferred_style.value if request.preferred_style else 'No especificado'}")
        
        print(f"\n✅ Menús propuestos: {len(result.proposed_menus)}")
        
        # Mostrar solo el primero en detalle
        menu = result.proposed_menus[0]
        print(f"\n🍽️ MENÚ #1:")
        print(f"   Similitud: {menu.similarity_score:.1%}")
        print(f"   Precio: {menu.menu.total_price:.2f}€")
        print(f"   Adaptaciones: {len(menu.adaptations)}")
        
        if menu.adaptations:
            print("\n   📝 Adaptaciones realizadas:")
            for adapt in menu.adaptations[:5]:
                print(f"      • {adapt}")
        
        # Mostrar explicaciones completas
        print("\n" + "=" * 100)
        print(result.explanations)
        
    else:
        print("❌ No se pudieron generar menús")


def test_case_2_vegetarian_cultural():
    """
    Caso 2: Evento corporativo vegetariano con cultura italiana
    
    Objetivo: Mostrar adaptaciones dietéticas + culturales
    Adaptaciones esperadas: Sustituciones de ingredientes, ajustes culturales
    """
    print_separator("CASO 2: CORPORATIVO VEGETARIANO - Cultura Italiana")
    
    system = create_cbr_system(verbose=False)
    
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
    
    result = system.process_request(request)
    
    if result.success and result.proposed_menus:
        print("\n📋 SOLICITUD:")
        print(f"   Tipo: {request.event_type.value}")
        print(f"   Comensales: {request.num_guests}")
        print(f"   Presupuesto: {request.price_min}-{request.price_max}€")
        print(f"   Restricciones: {', '.join(request.required_diets)}")
        print(f"   Cultura: {request.cultural_preference.value if request.cultural_preference else 'N/A'}")
        
        print(f"\n✅ Menús propuestos: {len(result.proposed_menus)}")
        
        menu = result.proposed_menus[0]
        print(f"\n🍽️ MENÚ #1:")
        print(f"   Entrante: {menu.menu.starter.name if menu.menu.starter else 'N/A'}")
        print(f"   Principal: {menu.menu.main_course.name if menu.menu.main_course else 'N/A'}")
        print(f"   Postre: {menu.menu.dessert.name if menu.menu.dessert else 'N/A'}")
        print(f"   Precio: {menu.menu.total_price:.2f}€")
        
        print(f"\n📊 MÉTRICAS:")
        print(f"   Similitud inicial: {menu.similarity_score:.1%}")
        print(f"   Adaptaciones realizadas: {len(menu.adaptations)}")
        
        if menu.adaptations:
            print("\n   🔧 ADAPTACIONES APLICADAS:")
            for i, adapt in enumerate(menu.adaptations, 1):
                print(f"      {i}. {adapt}")
        
        print("\n" + "=" * 100)
        print(result.explanations)
        
    else:
        print("❌ No se pudieron generar menús")


def test_case_3_vegan_lowbudget():
    """
    Caso 3: Cumpleaños vegano con presupuesto bajo
    
    Objetivo: Mostrar adaptaciones de precio + restricciones estrictas
    Adaptaciones esperadas: Muchas sustituciones, ajustes de precio
    """
    print_separator("CASO 3: CUMPLEAÑOS VEGANO - Presupuesto Ajustado")
    
    system = create_cbr_system(verbose=False)
    
    request = Request(
        event_type=EventType.FAMILIAR,  # Cumpleaños familiar
        num_guests=30,
        price_min=25,
        price_max=40,
        season=Season.AUTUMN,
        required_diets=["vegan"],
        restricted_ingredients=["honey", "gelatin"]  # Vegano estricto
    )
    
    result = system.process_request(request)
    
    if result.success and result.proposed_menus:
        print("\n📋 SOLICITUD:")
        print(f"   Tipo: {request.event_type.value}")
        print(f"   Comensales: {request.num_guests}")
        print(f"   Presupuesto: {request.price_min}-{request.price_max}€ 💰 (BAJO)")
        print(f"   Restricciones: {', '.join(request.required_diets)}")
        print(f"   Ingredientes prohibidos: {', '.join(request.restricted_ingredients)}")
        
        print(f"\n✅ Menús propuestos: {len(result.proposed_menus)}")
        
        for idx, menu in enumerate(result.proposed_menus[:2], 1):
            print(f"\n🍽️ PROPUESTA #{idx}:")
            print(f"   Precio: {menu.menu.total_price:.2f}€")
            print(f"   Similitud: {menu.similarity_score:.1%}")
            print(f"   Adaptaciones: {len(menu.adaptations)}")
            
            if menu.validation_result:
                print(f"   Estado validación: {menu.validation_result.status.value}")
                if menu.validation_result.issues:
                    warnings = [i for i in menu.validation_result.issues if i.severity == "warning"]
                    errors = [i for i in menu.validation_result.issues if i.severity == "error"]
                    if warnings:
                        print(f"   ⚠ Warnings: {len(warnings)}")
                    if errors:
                        print(f"   ❌ Errors: {len(errors)}")
        
        print("\n" + "=" * 100)
        print(result.explanations)
        
    else:
        print("❌ No se pudieron generar menús")


def test_case_4_cultural_premium():
    """
    Caso 4: Evento de gala con cultura marroquí y presupuesto alto
    
    Objetivo: Mostrar adaptaciones culturales complejas en premium
    Adaptaciones esperadas: Cambios culturales sofisticados, calidad premium
    """
    print_separator("CASO 4: GALA MARROQUÍ - Premium")
    
    system = create_cbr_system(verbose=False)
    
    request = Request(
        event_type=EventType.WEDDING,  # Usamos wedding para evento elegante
        num_guests=150,
        price_min=120,
        price_max=200,
        season=Season.WINTER,
        preferred_style=CulinaryStyle.FUSION,
        cultural_preference=CulturalTradition.LEBANESE  # Aproximación a marroquí
    )
    
    result = system.process_request(request)
    
    if result.success and result.proposed_menus:
        print("\n📋 SOLICITUD:")
        print(f"   Tipo: {request.event_type.value} 🎩")
        print(f"   Comensales: {request.num_guests}")
        print(f"   Presupuesto: {request.price_min}-{request.price_max}€ 💎 (PREMIUM)")
        print(f"   Estilo: {request.preferred_style.value if request.preferred_style else 'N/A'}")
        print(f"   Cultura: {request.cultural_preference.value if request.cultural_preference else 'N/A'}")
        
        print(f"\n✅ Menús propuestos: {len(result.proposed_menus)}")
        
        menu = result.proposed_menus[0]
        
        print(f"\n🍽️ MENÚ PREMIUM:")
        dishes = []
        if menu.menu.starter:
            dishes.append(f"Entrante: {menu.menu.starter.name}")
        if menu.menu.main_course:
            dishes.append(f"Principal: {menu.menu.main_course.name}")
        if menu.menu.dessert:
            dishes.append(f"Postre: {menu.menu.dessert.name}")
        
        for dish_desc in dishes:
            print(f"   {dish_desc}")
        
        print(f"\n   💰 Precio: {menu.menu.total_price:.2f}€/persona")
        print(f"   📊 Similitud: {menu.similarity_score:.1%}")
        
        if menu.adaptations:
            print(f"\n   🔧 Adaptaciones culturales: {len(menu.adaptations)}")
            for adapt in menu.adaptations[:7]:
                print(f"      • {adapt}")
        
        print("\n" + "=" * 100)
        print(result.explanations)
        
    else:
        print("❌ No se pudieron generar menús")


def test_case_5_allergies_complex():
    """
    Caso 5: Aniversario con múltiples alergias y preferencias
    
    Objetivo: Mostrar validación con warnings/errors
    Adaptaciones esperadas: Múltiples sustituciones, validación estricta
    """
    print_separator("CASO 5: ANIVERSARIO - Alergias Múltiples")
    
    system = create_cbr_system(verbose=False)
    
    request = Request(
        event_type=EventType.FAMILIAR,  # Aniversario familiar
        num_guests=40,
        price_min=60,
        price_max=90,
        season=Season.SPRING,
        required_diets=["gluten-free"],
        soft_diets=["dairy-free"],
        restricted_ingredients=["nuts", "shellfish", "wheat"]
        # preferred_ingredients no existe en Request
    )
    
    result = system.process_request(request)
    
    if result.success and result.proposed_menus:
        print("\n📋 SOLICITUD:")
        print(f"   Tipo: {request.event_type.value}")
        print(f"   Comensales: {request.num_guests}")
        print(f"   Presupuesto: {request.price_min}-{request.price_max}€")
        all_diets = request.required_diets + request.soft_diets
        print(f"   Restricciones: {', '.join(all_diets)}")
        print(f"   ⚠ Alergias: {', '.join(request.restricted_ingredients)}")
        # Removed preferred_ingredients line
        
        print(f"\n✅ Menús propuestos: {len(result.proposed_menus)}")
        
        for idx, menu in enumerate(result.proposed_menus[:2], 1):
            print(f"\n🍽️ PROPUESTA #{idx}:")
            print(f"   Similitud: {menu.similarity_score:.1%}")
            
            # Mostrar validación detallada
            if menu.validation_result:
                print(f"\n   🔍 VALIDACIÓN:")
                print(f"      Estado: {menu.validation_result.status.value}")
                print(f"      Score: {menu.validation_result.score:.1%}")
                
                if menu.validation_result.issues:
                    print(f"      Issues detectados: {len(menu.validation_result.issues)}")
                    
                    for issue in menu.validation_result.issues[:5]:
                        icon = "⚠" if issue.severity == "warning" else "❌"
                        print(f"         {icon} {issue.message}")
        
        print("\n" + "=" * 100)
        print(result.explanations)
        
    else:
        print("❌ No se pudieron generar menús")


def test_case_6_comparison_showcase():
    """
    Caso 6: Comparación lado a lado de diferentes propuestas
    
    Objetivo: Mostrar cómo varían las explicaciones entre propuestas
    """
    print_separator("CASO 6: COMPARACIÓN DE PROPUESTAS")
    
    system = create_cbr_system(verbose=False)
    
    request = Request(
        event_type=EventType.CORPORATE,
        num_guests=80,
        price_min=50,
        price_max=80,
        season=Season.SUMMER,
        preferred_style=CulinaryStyle.MODERN
    )
    
    result = system.process_request(request)
    
    if result.success and result.proposed_menus:
        print("\n📋 SOLICITUD:")
        print(f"   Evento corporativo de verano para 80 personas")
        print(f"   Presupuesto: 50-80€ por persona")
        print(f"   Estilo: Moderno")
        
        print(f"\n✅ Se generaron {len(result.proposed_menus)} propuestas diferentes")
        
        print("\n📊 COMPARACIÓN DE PROPUESTAS:")
        print("-" * 100)
        
        for idx, menu in enumerate(result.proposed_menus, 1):
            print(f"\n🍽️ PROPUESTA #{idx}:")
            print(f"   Precio: {menu.menu.total_price:.2f}€")
            print(f"   Similitud: {menu.similarity_score:.1%}")
            print(f"   Adaptaciones: {len(menu.adaptations)}")
            
            # Composición
            print(f"\n   Composición:")
            if menu.menu.starter:
                print(f"      Entrante: {menu.menu.starter.name}")
            if menu.menu.main_course:
                print(f"      Principal: {menu.menu.main_course.name}")
            if menu.menu.dessert:
                print(f"      Postre: {menu.menu.dessert.name}")
            
            # Top 3 adaptaciones
            if menu.adaptations:
                print(f"\n   Top adaptaciones:")
                for adapt in menu.adaptations[:3]:
                    print(f"      • {adapt}")
        
        print("\n" + "=" * 100)
        print("EXPLICACIONES COMPLETAS:")
        print("=" * 100)
        print(result.explanations)
        
    else:
        print("❌ No se pudieron generar menús")


def main():
    """Ejecuta todos los test cases."""
    print("\n" + "╔" + "═" * 98 + "╗")
    print("║" + " " * 20 + "TEST DE EXPLICABILIDAD - SISTEMA CBR CHEF DIGITAL" + " " * 28 + "║")
    print("╚" + "═" * 98 + "╝")
    
    print("\nEste test muestra cómo el sistema genera explicaciones detalladas")
    print("para diferentes tipos de solicitudes y escenarios.\n")
    print("Cada caso activará diferentes partes del sistema de explicabilidad:")
    print("  • RETRIEVE: Desglose de similitud por múltiples criterios")
    print("  • ADAPT: Adaptaciones culturales, dietéticas, de precio")
    print("  • REVISE: Validaciones, warnings, errores detectados")
    
    tests = [
        ("1", "Boda simple sin restricciones", test_case_1_simple_wedding),
        ("2", "Corporativo vegetariano italiano", test_case_2_vegetarian_cultural),
        ("3", "Cumpleaños vegano presupuesto bajo", test_case_3_vegan_lowbudget),
        ("4", "Gala marroquí premium", test_case_4_cultural_premium),
        ("5", "Aniversario con alergias múltiples", test_case_5_allergies_complex),
        ("6", "Comparación de propuestas", test_case_6_comparison_showcase),
    ]
    
    print("\n" + "=" * 100)
    print("CASOS DE TEST DISPONIBLES:")
    print("=" * 100)
    for num, desc, _ in tests:
        print(f"   {num}. {desc}")
    
    print("\n¿Qué casos deseas ejecutar?")
    print("  • Presiona Enter para ejecutar TODOS")
    print("  • Escribe números separados por comas (ej: 1,3,5)")
    print("  • Escribe 'q' para salir")
    
    choice = input("\nTu elección: ").strip()
    
    if choice.lower() == 'q':
        print("\n👋 ¡Hasta luego!")
        return
    
    if not choice:
        # Ejecutar todos
        selected = tests
    else:
        # Ejecutar seleccionados
        numbers = [n.strip() for n in choice.split(",")]
        selected = [(num, desc, func) for num, desc, func in tests if num in numbers]
    
    print(f"\n🚀 Ejecutando {len(selected)} caso(s)...")
    
    for num, desc, test_func in selected:
        try:
            test_func()
            print("\n✅ Caso completado\n")
        except Exception as e:
            print(f"\n❌ Error en caso {num}: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 100)
    print("🎉 TEST COMPLETADO")
    print("=" * 100)
    print("\nPara ver el ciclo completo de RETAIN (aprendizaje), ejecuta:")
    print("   python develop/demo_retain.py")


if __name__ == "__main__":
    main()
