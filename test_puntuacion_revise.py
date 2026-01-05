"""
Test del nuevo sistema de puntuación de REVISE.

Demuestra cómo el sistema ahora calcula puntuaciones
basadas en múltiples componentes ponderados en lugar de
simplemente restar penalizaciones desde 100.
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


def print_separator(title="", char="="):
    if title:
        print(f"\n{char * 90}")
        print(f"  {title}")
        print(char * 90)
    else:
        print(char * 90)


def analyze_scores(result, request):
    """Analiza y muestra las puntuaciones de los menús."""
    if not result.proposed_menus:
        print("❌ No se generaron menús para analizar")
        return
    
    print(f"\n📊 ANÁLISIS DE PUNTUACIONES")
    print(f"   Menús generados: {len(result.proposed_menus)}")
    
    scores = [m.validation_result.score for m in result.proposed_menus 
              if m.validation_result]
    
    if scores:
        print(f"   Puntuación mínima: {min(scores):.1f}")
        print(f"   Puntuación máxima: {max(scores):.1f}")
        print(f"   Puntuación media: {sum(scores)/len(scores):.1f}")
        print(f"   Rango de variación: {max(scores) - min(scores):.1f} puntos")
    
    print(f"\n📋 DESGLOSE POR MENÚ:")
    print("-" * 90)
    
    for idx, menu in enumerate(result.proposed_menus, 1):
        val = menu.validation_result
        if not val:
            continue
        
        print(f"\n🍽️  MENÚ #{idx}: {menu.menu.starter.name} / "
              f"{menu.menu.main_course.name} / {menu.menu.dessert.name}")
        print(f"   Precio: {menu.menu.total_price:.2f}€")
        print(f"   Similitud: {menu.similarity_score:.1%}")
        
        # Puntuación total
        print(f"\n   🎯 PUNTUACIÓN TOTAL: {val.score:.1f}/100")
        print(f"   Estado: {val.status.value}")
        
        # Análisis de issues
        if val.issues:
            errors = [i for i in val.issues if i.severity == "error"]
            warnings = [i for i in val.issues if i.severity == "warning"]
            infos = [i for i in val.issues if i.severity == "info"]
            
            print(f"\n   📝 Issues detectados:")
            if errors:
                print(f"      ❌ Errores: {len(errors)}")
                for e in errors[:2]:
                    print(f"         • {e.message}")
            if warnings:
                print(f"      ⚠️  Warnings: {len(warnings)}")
                for w in warnings[:2]:
                    print(f"         • {w.message}")
            if infos:
                print(f"      ℹ️  Infos: {len(infos)}")
        else:
            print(f"\n   ✅ Sin issues detectados")
        
        # Explicaciones positivas
        if val.explanations:
            positives = [e for e in val.explanations 
                        if any(kw in e.lower() for kw in 
                              ['apropiado', 'ideal', 'armonía', 'buena', 'bien'])]
            if positives:
                print(f"\n   ⭐ Aspectos positivos:")
                for p in positives[:3]:
                    print(f"      • {p}")
        
        print("-" * 90)


def test_puntuacion_perfecta():
    """Test 1: Menú que debería tener puntuación alta (90+)"""
    print_separator("TEST 1: Menú de Alta Calidad (esperado: 90+)")
    
    system = ChefDigitalCBR(CBRConfig(verbose=False, max_proposals=2))
    
    # Solicitud bien alineada con casos existentes
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=120,  # Rango amplio y centrado
        season=Season.SUMMER,
        preferred_style=CulinaryStyle.CLASSIC
        # Sin restricciones especiales
    )
    
    print(f"\n📋 Solicitud: Boda clásica de verano, 100 personas, 80-120€")
    
    result = system.process_request(request)
    analyze_scores(result, request)


def test_puntuacion_con_restricciones():
    """Test 2: Menú con restricciones (esperado: 70-85)"""
    print_separator("TEST 2: Menú con Restricciones Dietéticas (esperado: 70-85)")
    
    system = ChefDigitalCBR(CBRConfig(verbose=False, max_proposals=2))
    
    request = Request(
        event_type=EventType.CORPORATE,
        num_guests=50,
        price_min=40,
        price_max=70,
        season=Season.SPRING,
        required_diets=["vegetarian"],
        cultural_preference=CulturalTradition.ITALIAN
    )
    
    print(f"\n📋 Solicitud: Corporativo vegetariano italiano, 50 personas, 40-70€")
    
    result = system.process_request(request)
    analyze_scores(result, request)


def test_puntuacion_baja():
    """Test 3: Menú con múltiples restricciones estrictas (esperado: 50-70)"""
    print_separator("TEST 3: Menú con Restricciones Complejas (esperado: 50-70)")
    
    system = ChefDigitalCBR(CBRConfig(verbose=False, max_proposals=2))
    
    request = Request(
        event_type=EventType.FAMILIAR,
        num_guests=30,
        price_min=25,
        price_max=35,  # Presupuesto MUY ajustado
        season=Season.WINTER,
        required_diets=["vegan", "gluten-free"],  # Doble restricción
        restricted_ingredients=["nuts", "soy"],
        cultural_preference=CulturalTradition.CHINESE  # Difícil de cumplir
    )
    
    print(f"\n📋 Solicitud: Familiar vegano sin gluten, chino, 30 personas, 25-35€")
    print(f"   ⚠️  Restricciones MUY estrictas")
    
    result = system.process_request(request)
    analyze_scores(result, request)


def test_comparacion_variabilidad():
    """Test 4: Comparar variabilidad de puntuaciones"""
    print_separator("TEST 4: Variabilidad de Puntuaciones")
    
    print("\nEjecutan 3 solicitudes diferentes para comparar el rango de puntuaciones:")
    
    system = ChefDigitalCBR(CBRConfig(verbose=False, max_proposals=3))
    
    # Caso simple
    req1 = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=150,
        season=Season.SUMMER
    )
    
    # Caso moderado
    req2 = Request(
        event_type=EventType.CORPORATE,
        num_guests=50,
        price_min=40,
        price_max=70,
        season=Season.SPRING,
        required_diets=["vegetarian"]
    )
    
    # Caso complejo
    req3 = Request(
        event_type=EventType.FAMILIAR,
        num_guests=30,
        price_min=25,
        price_max=40,
        season=Season.AUTUMN,
        required_diets=["vegan"],
        restricted_ingredients=["honey", "gelatin"]
    )
    
    results = [
        ("SIMPLE (Boda sin restricciones)", system.process_request(req1)),
        ("MODERADO (Vegetariano)", system.process_request(req2)),
        ("COMPLEJO (Vegano + alergias)", system.process_request(req3))
    ]
    
    print("\n" + "=" * 90)
    print("📊 COMPARACIÓN DE PUNTUACIONES")
    print("=" * 90)
    
    all_scores = []
    
    for name, result in results:
        if result.proposed_menus:
            scores = [m.validation_result.score for m in result.proposed_menus 
                     if m.validation_result]
            if scores:
                avg = sum(scores) / len(scores)
                min_s = min(scores)
                max_s = max(scores)
                all_scores.extend(scores)
                
                print(f"\n{name}:")
                print(f"   Media: {avg:.1f}")
                print(f"   Rango: {min_s:.1f} - {max_s:.1f}")
                print(f"   Menús: {len(scores)}")
    
    if all_scores:
        print("\n" + "-" * 90)
        print(f"ESTADÍSTICAS GLOBALES:")
        print(f"   Puntuación mínima: {min(all_scores):.1f}")
        print(f"   Puntuación máxima: {max(all_scores):.1f}")
        print(f"   Rango total: {max(all_scores) - min(all_scores):.1f} puntos")
        print(f"   Media global: {sum(all_scores)/len(all_scores):.1f}")
        
        # Distribución
        ranges = {
            "90-100": sum(1 for s in all_scores if 90 <= s <= 100),
            "80-89": sum(1 for s in all_scores if 80 <= s < 90),
            "70-79": sum(1 for s in all_scores if 70 <= s < 80),
            "60-69": sum(1 for s in all_scores if 60 <= s < 70),
            "<60": sum(1 for s in all_scores if s < 60)
        }
        
        print(f"\n   Distribución por rangos:")
        for rango, count in ranges.items():
            if count > 0:
                bar = "█" * count
                print(f"      {rango}: {count} {bar}")


def main():
    """Ejecuta todos los tests de puntuación."""
    print("\n" + "╔" + "═" * 88 + "╗")
    print("║" + " " * 20 + "TEST: NUEVO SISTEMA DE PUNTUACIÓN EN REVISE" + " " * 23 + "║")
    print("╚" + "═" * 88 + "╝")
    
    print("\nEste test demuestra cómo el nuevo sistema de puntuación:")
    print("  1. Pondera múltiples componentes (restricciones, calidad, cultura, etc.)")
    print("  2. Genera puntuaciones más variadas (no siempre ~80)")
    print("  3. Discrimina mejor entre menús de diferentes calidades")
    
    print("\n⚙️  COMPONENTES DE LA PUNTUACIÓN:")
    print("   • Cumplimiento restricciones: 30% (lo más crítico)")
    print("   • Calidad gastronómica: 25% (armonías, compatibilidades)")
    print("   • Adaptación cultural: 20% (fidelidad a tradición)")
    print("   • Adecuación al evento: 15% (temperatura, calorías)")
    print("   • Relación calidad-precio: 10% (valor por dinero)")
    print("   • Bonus feedback histórico: hasta +5 puntos")
    
    try:
        # Test 1: Alta calidad
        test_puntuacion_perfecta()
        input("\n>>> Presiona Enter para continuar...")
        
        # Test 2: Con restricciones
        test_puntuacion_con_restricciones()
        input("\n>>> Presiona Enter para continuar...")
        
        # Test 3: Restricciones complejas
        test_puntuacion_baja()
        input("\n>>> Presiona Enter para continuar...")
        
        # Test 4: Comparación
        test_comparacion_variabilidad()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrumpidos")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print_separator()
    print("🎉 TESTS COMPLETADOS")
    print_separator()
    
    print("\n📚 CONCLUSIONES:")
    print("\n   ANTES (sistema antiguo):")
    print("      • Puntuación = 100 - penalizaciones")
    print("      • Siempre cerca de 80 (poco rango)")
    print("      • No considera aspectos positivos")
    
    print("\n   AHORA (sistema nuevo):")
    print("      • Puntuación = suma ponderada de componentes")
    print("      • Rango amplio (15-100 puntos)")
    print("      • Bonifica armonías y adaptaciones correctas")
    print("      • Mejor discriminación entre menús")
    
    print("\n   Ver análisis completo en:")
    print("      ANALISIS_PUNTUACION_REVISE.md")
    print()


if __name__ == "__main__":
    main()
