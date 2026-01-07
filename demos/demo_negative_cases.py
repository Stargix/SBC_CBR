"""
Demo: Casos negativos y mantenimiento mejorado
==============================================

Este demo muestra las 3 mejoras implementadas:
1. Almacenar casos de failure (negative cases)
2. Mantenimiento periódico (cada 10 casos, no cada inserción)
3. Eliminación por redundancia (no por calidad)
"""

import sys
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    Request, EventType, Season, CulinaryStyle, CulturalTradition,
    CaseBase, CaseRetriever, CaseAdapter, CaseRetainer, FeedbackData
)


def demo_negative_cases():
    """Demuestra el aprendizaje de casos negativos"""
    
    print("=" * 70)
    print("🧪 DEMO: Casos Negativos (Failure Learning)")
    print("=" * 70)
    
    # Inicializar sistema
    case_base = CaseBase()
    retriever = CaseRetriever(case_base)
    adapter = CaseAdapter(case_base)
    retainer = CaseRetainer(case_base)
    
    # Estadísticas iniciales
    stats = retainer.get_retention_statistics()
    print(f"\n📊 Estado inicial:")
    print(f"   - Total casos: {stats['total_cases']}")
    print(f"   - Casos positivos: {stats.get('positive_cases', stats['total_cases'])}")
    print(f"   - Casos negativos: {stats.get('negative_cases', 0)}")
    
    # Simular un request
    request = Request(
        id="req-test-negative",
        event_type=EventType.WEDDING,
        season=Season.SUMMER,
        num_guests=80,
        price_min=40,
        price_max=60,
        wants_wine=True,
        preferred_style=CulinaryStyle.MODERN
    )
    
    print(f"\n🔍 Request: Boda en verano, 80 personas, 40-60€/persona")
    
    # Verificar si hay warnings de casos negativos
    warnings = retriever.check_negative_cases(request, threshold=0.75)
    
    if warnings:
        print(f"\n⚠️  ADVERTENCIAS: {len(warnings)} casos negativos similares encontrados:")
        for case, similarity in warnings[:3]:
            print(f"   - {case.id}: {similarity:.2%} similitud")
            print(f"     Feedback: {case.feedback_score}/5 - {case.feedback_comments}")
    else:
        print(f"\n✅ No hay casos negativos similares (safe to proceed)")
    
    # Recuperar y adaptar
    results = retriever.retrieve(request, k=3)
    print(f"\n📋 Recuperados {len(results)} casos positivos")
    
    if results:
        adapted_menus = adapter.adapt(results, request)
        adapted_menu = adapted_menus[0] if adapted_menus else None
        
        if not adapted_menu:
            print("\n❌ No se pudo adaptar el menú")
            return
        
        print(f"\n🍽️  Menú propuesto:")
        print(f"   - Entrante: {adapted_menu.adapted_menu.starter.name}")
        print(f"   - Principal: {adapted_menu.adapted_menu.main_course.name}")
        print(f"   - Postre: {adapted_menu.adapted_menu.dessert.name}")
        print(f"   - Bebida: {adapted_menu.adapted_menu.beverage.name}")
        
        # Simular feedback NEGATIVO (caso de failure)
        print(f"\n❌ Simulando feedback NEGATIVO (cliente insatisfecho)...")
        
        feedback_negative = FeedbackData(
            menu_id=adapted_menu.adapted_menu.id,
            success=False,
            score=2.1,  # Muy bajo
            comments="El menú no gustó. Platos demasiado modernos para una boda tradicional",
            would_recommend=False
        )
        
        # Intentar retener el caso negativo
        retained, message = retainer.retain(request, adapted_menu.adapted_menu, feedback_negative)
        
        print(f"   Resultado: {message}")
        
        # Estadísticas después
        stats = retainer.get_retention_statistics()
        print(f"\n📊 Estado después de aprender del failure:")
        print(f"   - Total casos: {stats['total_cases']}")
        print(f"   - Casos positivos: {stats.get('positive_cases', 0)}")
        print(f"   - Casos negativos: {stats.get('negative_cases', 0)}")
        
        # Ahora verificar de nuevo
        print(f"\n🔄 Verificando de nuevo el mismo request...")
        warnings = retriever.check_negative_cases(request, threshold=0.75)
        
        if warnings:
            print(f"   ⚠️  ADVERTENCIA: Ahora detectamos {len(warnings)} caso(s) negativo(s)")
            for case, similarity in warnings[:1]:
                print(f"      → {case.id}: {similarity:.2%} similitud")
                print(f"        '{case.feedback_comments}'")
        
    print()


def demo_redundancy_removal():
    """Demuestra la eliminación por redundancia"""
    
    print("=" * 70)
    print("🧹 DEMO: Eliminación por Redundancia (no por calidad)")
    print("=" * 70)
    
    case_base = CaseBase()
    retainer = CaseRetainer(case_base)
    
    # Configurar límite bajo para forzar limpieza
    retainer.max_cases_per_event = 8
    retainer.maintenance_frequency = 5
    
    print(f"\n⚙️  Configuración:")
    print(f"   - Máximo casos por evento: {retainer.max_cases_per_event}")
    print(f"   - Frecuencia mantenimiento: cada {retainer.maintenance_frequency} casos")
    print(f"   - Umbral redundancia: {retainer.redundancy_threshold:.0%}")
    
    # Simular añadir muchos casos SIMILARES (redundantes)
    print(f"\n🔄 Simulando adición de casos redundantes...")
    
    base_request = Request(
        id="req-base",
        event_type=EventType.FAMILIAR,
        season=Season.AUTUMN,
        num_guests=50,
        price_min=30,
        price_max=45,
        wants_wine=False,
        preferred_style=CulinaryStyle.CLASSIC
    )
    
    # Recuperar un caso base
    retriever = CaseRetriever(case_base)
    adapter = CaseAdapter(case_base)
    
    results = retriever.retrieve(base_request, k=1)
    
    if results:
        base_menu = results[0].case.menu
        
        # Añadir 12 casos casi idénticos con feedback variado
        for i in range(12):
            # Variación mínima en el request
            similar_request = Request(
                id=f"req-similar-{i}",
                event_type=EventType.FAMILIAR,
                season=Season.AUTUMN,
                num_guests=50 + random.randint(-5, 5),  # Pequeña variación
                price_min=30,
                price_max=45,
                wants_wine=False,
                preferred_style=CulinaryStyle.CLASSIC
            )
            
            # Feedback aleatorio (algunos buenos, algunos regulares)
            score = random.uniform(3.5, 4.8)
            
            feedback = FeedbackData(
                menu_id=f"menu-similar-{i}",
                success=True,
                score=score,
                comments=f"Caso similar {i+1}",
                would_recommend=True
            )
            
            retained, msg = retainer.retain(similar_request, base_menu, feedback)
            
            if "Mantenimiento" in msg or "redundantes" in msg:
                print(f"   🧹 {msg}")
    
    # Estadísticas finales
    stats = retainer.get_retention_statistics()
    familiar_cases = [c for c in case_base.cases if c.request.event_type == EventType.FAMILIAR]
    
    print(f"\n📊 Resultado final:")
    print(f"   - Total casos: {stats['total_cases']}")
    print(f"   - Casos FAMILIAR: {len(familiar_cases)}")
    print(f"   - Máximo permitido: {retainer.max_cases_per_event}")
    print(f"\n✅ Sistema eliminó casos redundantes, manteniendo diversidad")
    
    print()


def demo_periodic_maintenance():
    """Demuestra el mantenimiento periódico"""
    
    print("=" * 70)
    print("⏱️  DEMO: Mantenimiento Periódico (no en cada inserción)")
    print("=" * 70)
    
    case_base = CaseBase()
    retainer = CaseRetainer(case_base)
    
    print(f"\n⚙️  Frecuencia de mantenimiento: cada {retainer.maintenance_frequency} casos")
    print(f"   (Antes: se ejecutaba en CADA inserción)")
    
    print(f"\n🔄 Añadiendo casos...")
    print(f"   Contador actual: {retainer.cases_since_maintenance}")
    
    # Añadir casos uno por uno
    for i in range(15):
        # Variar el request para que no sean todos iguales
        request = Request(
            id=f"req-periodic-{i}",
            event_type=EventType.COMMUNION,
            season=Season.SPRING if i % 2 == 0 else Season.AUTUMN,  # Variar temporada
            num_guests=40 + (i * 10),  # Variar cantidad de invitados
            price_min=25 + (i * 2),
            price_max=35 + (i * 3),
            preferred_style=CulinaryStyle.SUAVE if i % 3 == 0 else CulinaryStyle.CLASSIC
        )
        
        retriever = CaseRetriever(case_base)
        results = retriever.retrieve(request, k=1)
        
        if results:
            feedback = FeedbackData(
                menu_id=f"menu-{i}",
                success=True,
                score=random.uniform(3.8, 4.5),
                comments="Ok",
                would_recommend=True
            )
            
            retained, msg = retainer.retain(request, results[0].case.menu, feedback)
            
            print(f"   [{i+1:2d}] Contador: {retainer.cases_since_maintenance}", end="")
            
            if retainer.cases_since_maintenance == 0:
                print(" → 🧹 ¡Mantenimiento ejecutado!")
            else:
                print()
    
    print(f"\n✅ Mantenimiento solo se ejecuta periódicamente (eficiencia mejorada)")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 DEMOS: Mejoras en Retención de Casos")
    print("=" * 70)
    print()
    
    demo_negative_cases()
    demo_redundancy_removal()
    demo_periodic_maintenance()
    
    print("=" * 70)
    print("✅ Todos los demos completados")
    print("=" * 70)
    print()
    
    print("📝 Resumen de mejoras:")
    print("   1. ✅ Casos negativos (failures) se almacenan para evitar repetir errores")
    print("   2. ✅ Mantenimiento periódico (cada 10 casos) en vez de continuo")
    print("   3. ✅ Eliminación por redundancia (similitud >90%) en vez de por calidad")
    print()
