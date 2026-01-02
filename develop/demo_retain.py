#!/usr/bin/env python3
"""
Demo del ciclo completo CBR incluyendo RETAIN (aprendizaje).

Este script demuestra cómo el sistema aprende de nuevos casos.
"""

from main import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle
)
from cycle.retain import FeedbackData


def demo_ciclo_completo():
    """Demuestra el ciclo CBR completo con aprendizaje."""
    
    print("=" * 70)
    print("🔄 DEMO COMPLETA DEL CICLO CBR")
    print("=" * 70)
    
    # Inicializar sistema
    config = CBRConfig(verbose=False, enable_learning=True)
    cbr = ChefDigitalCBR(config)
    
    # Mostrar estado inicial
    stats_inicial = cbr.get_statistics()
    cb_stats = cbr.case_base.get_statistics()
    print(f"\n📊 ESTADO INICIAL:")
    print(f"   Casos en la base: {stats_inicial['case_base']['total_cases']}")
    if cb_stats['total_cases'] > 0:
        print(f"   Feedback promedio: {cb_stats['average_feedback']:.2f}/5")
    
    # ========================================
    # FASE 1-3: RETRIEVE, ADAPT, REVISE
    # ========================================
    print("\n" + "=" * 70)
    print("FASE 1️⃣-3️⃣: RETRIEVE → ADAPT → REVISE")
    print("=" * 70)
    
    request = Request(
        event_type=EventType.FAMILIAR,
        num_guests=30,
        price_max=35.0,
        season=Season.WINTER,
        preferred_style=CulinaryStyle.REGIONAL,
    )
    
    print(f"\n📝 Nueva solicitud:")
    print(f"   Evento: Comida familiar")
    print(f"   Comensales: 30")
    print(f"   Presupuesto: 35€/persona")
    print(f"   Temporada: Invierno")
    print(f"   Estilo: Regional")
    
    # Procesar
    result = cbr.process_request(request)
    
    if result.proposed_menus:
        mejor_menu = result.proposed_menus[0]
        print(f"\n✅ Menú propuesto (similitud: {mejor_menu.similarity_score:.1%}):")
        print(f"   Entrada: {mejor_menu.menu.starter.name}")
        print(f"   Principal: {mejor_menu.menu.main_course.name}")
        print(f"   Postre: {mejor_menu.menu.dessert.name}")
        print(f"   Precio: {mejor_menu.menu.total_price:.2f}€")
        
        # ========================================
        # FASE 4: RETAIN (APRENDIZAJE)
        # ========================================
        print("\n" + "=" * 70)
        print("FASE 4️⃣: RETAIN (Aprendizaje)")
        print("=" * 70)
        
        # Simular feedback del cliente
        print("\n🎭 SIMULACIÓN: Cliente usa el menú y da feedback...\n")
        
        # Caso 1: Feedback excelente
        print("📊 Escenario 1: Feedback excelente (4.9/5)")
        feedback_bueno = FeedbackData(
            menu_id=mejor_menu.menu.id,
            success=True,
            score=4.9,
            comments="¡Excelente! A todos les encantó",
            would_recommend=True
        )
        
        decision = cbr.retainer.evaluate_retention(request, mejor_menu.menu, feedback_bueno)
        print(f"   Decisión: {decision.action}")
        print(f"   Razón: {decision.reason}")
        print(f"   ¿Retener?: {'✅ SÍ' if decision.should_retain else '❌ NO'}")
        
        if decision.should_retain:
            success, msg = cbr.retainer.retain(request, mejor_menu.menu, feedback_bueno)
            print(f"   Resultado: {msg}")
        
        # Caso 2: Feedback malo
        print("\n📊 Escenario 2: Feedback malo (2.5/5)")
        feedback_malo = FeedbackData(
            menu_id=mejor_menu.menu.id,
            success=False,
            score=2.5,
            comments="No estaba bueno",
            would_recommend=False
        )
        
        decision = cbr.retainer.evaluate_retention(request, mejor_menu.menu, feedback_malo)
        print(f"   Decisión: {decision.action}")
        print(f"   Razón: {decision.reason}")
        print(f"   ¿Retener?: {'✅ SÍ' if decision.should_retain else '❌ NO'}")
        
        # Caso 3: Feedback medio con caso similar existente
        print("\n📊 Escenario 3: Feedback medio (3.8/5)")
        feedback_medio = FeedbackData(
            menu_id=mejor_menu.menu.id,
            success=True,
            score=3.8,
            comments="Aceptable",
            would_recommend=True
        )
        
        decision = cbr.retainer.evaluate_retention(request, mejor_menu.menu, feedback_medio)
        print(f"   Decisión: {decision.action}")
        print(f"   Razón: {decision.reason}")
        print(f"   Similitud con existente: {decision.similarity_to_existing:.1%}")
        print(f"   ¿Retener?: {'✅ SÍ' if decision.should_retain else '❌ NO'}")
        
        # Mostrar estado final
        print("\n" + "=" * 70)
        print("📊 ESTADO FINAL DEL SISTEMA")
        print("=" * 70)
        
        stats_final = cbr.get_statistics()
        cb_stats_final = cbr.case_base.get_statistics()
        print(f"\n   Casos en la base: {stats_final['case_base']['total_cases']}")
        if cb_stats_final['total_cases'] > 0:
            print(f"   Casos exitosos: {cb_stats_final['successful_cases']}")
            print(f"   Feedback promedio: {cb_stats_final['average_feedback']:.2f}/5")
        
        if stats_final['case_base']['total_cases'] > stats_inicial['case_base']['total_cases']:
            nuevos = stats_final['case_base']['total_cases'] - stats_inicial['case_base']['total_cases']
            print(f"\n   🧠 ¡Sistema aprendió {nuevos} nuevo(s) caso(s)!")
        
        print("\n" + "=" * 70)
        print("💡 EXPLICACIÓN DEL APRENDIZAJE")
        print("=" * 70)
        print("""
El sistema RETIENE casos basándose en:

1. CALIDAD (score ≥ 3.5/5)
   ✅ Score 4.9 → Se retiene
   ❌ Score 2.5 → Se descarta (mala experiencia)
   ⚠️  Score 3.8 → Depende de otros factores

2. NOVEDAD (similitud < 85% con existentes)
   ✅ Caso nuevo → Se añade a la base
   ❌ Caso muy similar → Se compara score
   
3. MEJORA (si existe similar, ¿es mejor?)
   ✅ Score nuevo > score existente → Actualiza
   ❌ Score nuevo ≤ score existente → Descarta

4. LÍMITE DE CASOS (max 50 por tipo de evento)
   Si se excede → Elimina los peores

De esta forma, la base de conocimiento mejora continuamente
manteniendo solo los casos más útiles y exitosos.
        """)


def demo_estadisticas_retencion():
    """Muestra estadísticas de retención."""
    config = CBRConfig(verbose=False, enable_learning=True)
    cbr = ChefDigitalCBR(config)
    
    stats = cbr.retainer.get_retention_statistics()
    
    print("\n" + "=" * 70)
    print("📈 ESTADÍSTICAS DE RETENCIÓN")
    print("=" * 70)
    
    stats = cbr.case_base.get_statistics()
    print(f"\nCasos totales: {stats['total_cases']}")
    if stats['total_cases'] > 0:
        print(f"Casos exitosos: {stats['successful_cases']}")
        print(f"Feedback promedio: {stats['average_feedback']:.2f}/5")
    
    if 'cases_by_event' in stats:
        print("\nDistribución por tipo de evento:")
        for event_type, count in stats['cases_by_event'].items():
            print(f"  {event_type}: {count} casos")
    
    if 'cases_by_source' in stats:
        print("\nCasos por fuente:")
        for source, count in stats['cases_by_source'].items():
            print(f"  {source}: {count} casos")


if __name__ == "__main__":
    demo_ciclo_completo()
    print("\n")
    demo_estadisticas_retencion()
