"""
Ejemplo de uso del sistema CBR con Aprendizaje Adaptativo.

Demuestra:
1. ADAPT Preventivo: Ajustes antes de REVISE
2. RETAIN con Aprendizaje: Actualización de pesos según feedback

Ejecutar: python develop/demo_adaptive_cbr.py
"""

import sys
from pathlib import Path

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from develop.main import ChefDigitalCBR, CBRConfig
from develop.core.models import Request, EventType, Season
from develop.cycle.retain import FeedbackData


def print_separator(title: str = ""):
    """Imprime separador visual"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print('='*70)
    else:
        print('-'*70)


def demo_adaptive_cbr():
    """Demostración del CBR adaptativo"""
    
    print_separator("🤖 CHEF DIGITAL CBR - Sistema Adaptativo")
    
    # Crear sistema con aprendizaje habilitado
    config = CBRConfig(
        enable_learning=True,
        verbose=True,
        max_proposals=3
    )
    cbr = ChefDigitalCBR(config)
    
    print(f"\n✅ Sistema inicializado")
    print(f"   📊 Casos en base: {len(cbr.case_base.get_all_cases())}")
    print(f"   🧠 Aprendizaje: ACTIVADO")
    print(f"   ⚙️ ADAPT Preventivo: ACTIVADO")
    
    # ========== CASO 1: Boda Vegetariana ==========
    print_separator("📋 CASO 1: Boda Vegetariana de Verano")
    
    request1 = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=45.0,
        price_max=55.0,
        season=Season.SUMMER,
        required_diets=["vegetarian"],
        wants_wine=True
    )
    
    print(f"\n🔍 Solicitud:")
    print(f"   Evento: {request1.event_type.value}")
    print(f"   Invitados: {request1.num_guests}")
    print(f"   Presupuesto: {request1.price_min}-{request1.price_max}€")
    print(f"   Temporada: {request1.season.value}")
    print(f"   Dietas: {', '.join(request1.required_diets)}")
    
    result1 = cbr.process_request(request1)
    
    print(f"\n📤 Resultado:")
    print(f"   ✓ {len(result1.proposed_menus)} propuestas generadas")
    
    if result1.proposed_menus:
        menu1 = result1.proposed_menus[0]
        print(f"\n🍽️ PROPUESTA #1:")
        print(f"   Entrante: {menu1.menu.starter.name} ({menu1.menu.starter.price:.2f}€)")
        print(f"   Principal: {menu1.menu.main_course.name} ({menu1.menu.main_course.price:.2f}€)")
        print(f"   Postre: {menu1.menu.dessert.name} ({menu1.menu.dessert.price:.2f}€)")
        print(f"   Bebida: {menu1.menu.beverage.name} ({menu1.menu.beverage.price:.2f}€)")
        print(f"   💰 Total: {menu1.menu.total_price:.2f}€")
        print(f"   ⭐ Similitud: {menu1.similarity_score:.2%}")
        
        # Mostrar adaptaciones
        if menu1.adaptations:
            print(f"\n   🔧 Adaptaciones realizadas:")
            for adapt in menu1.adaptations[:3]:  # Mostrar primeras 3
                print(f"      • {adapt}")
        
        # Simular feedback positivo
        feedback1 = FeedbackData(
            menu_id=menu1.menu.id,
            success=True,
            score=4.5,
            comments="Excelente menú vegetariano, muy fresco",
            would_recommend=True
        )
        
        print(f"\n📝 Feedback simulado:")
        print(f"   Satisfacción: {feedback1.score}/5.0 ⭐⭐⭐⭐½")
        print(f"   Comentario: '{feedback1.comments}'")
        
        # APRENDIZAJE: Actualizar pesos
        print(f"\n🧠 Aprendiendo de feedback...")
        cbr.learn_from_feedback(feedback1, request1)
        print(f"   ✅ Pesos de similitud actualizados")
    
    # ========== CASO 2: Congreso Corporativo ==========
    print_separator("📋 CASO 2: Congreso Corporativo")
    
    request2 = Request(
        event_type=EventType.CONGRESS,
        num_guests=200,
        price_min=20.0,
        price_max=30.0,
        season=Season.AUTUMN,
        wants_wine=False
    )
    
    print(f"\n🔍 Solicitud:")
    print(f"   Evento: {request2.event_type.value}")
    print(f"   Invitados: {request2.num_guests}")
    print(f"   Presupuesto: {request2.price_min}-{request2.price_max}€")
    print(f"   Temporada: {request2.season.value}")
    
    result2 = cbr.process_request(request2)
    
    print(f"\n📤 Resultado:")
    print(f"   ✓ {len(result2.proposed_menus)} propuestas generadas")
    
    if result2.proposed_menus:
        menu2 = result2.proposed_menus[0]
        print(f"\n🍽️ PROPUESTA #1:")
        print(f"   Menú: {menu2.menu.starter.name} + {menu2.menu.main_course.name} + {menu2.menu.dessert.name}")
        print(f"   💰 Total: {menu2.menu.total_price:.2f}€")
        print(f"   ⭐ Similitud: {menu2.similarity_score:.2%}")
        
        # Feedback moderado
        feedback2 = FeedbackData(
            menu_id=menu2.menu.id,
            success=True,
            score=4.0,
            comments="Funcional para evento corporativo",
            would_recommend=True
        )
        
        print(f"\n📝 Feedback simulado:")
        print(f"   Satisfacción: {feedback2.score}/5.0 ⭐⭐⭐⭐")
        
        print(f"\n🧠 Aprendiendo de feedback...")
        cbr.learn_from_feedback(feedback2, request2)
    
    # ========== CASO 3: Boda Premium Mediterránea ==========
    print_separator("📋 CASO 3: Boda Premium Mediterránea")
    
    request3 = Request(
        event_type=EventType.WEDDING,
        num_guests=120,
        price_min=70.0,
        price_max=90.0,
        season=Season.SPRING,
        cultural_preference="mediterranean",
        wants_wine=True,
        wine_per_dish=True
    )
    
    print(f"\n🔍 Solicitud:")
    print(f"   Evento: {request3.event_type.value} (Premium)")
    print(f"   Invitados: {request3.num_guests}")
    print(f"   Presupuesto: {request3.price_min}-{request3.price_max}€")
    print(f"   Cultura: {request3.cultural_preference}")
    print(f"   Maridaje: Sí")
    
    result3 = cbr.process_request(request3)
    
    print(f"\n📤 Resultado:")
    print(f"   ✓ {len(result3.proposed_menus)} propuestas generadas")
    
    if result3.proposed_menus:
        menu3 = result3.proposed_menus[0]
        print(f"\n🍽️ PROPUESTA #1:")
        print(f"   Menú: {menu3.menu.starter.name} + {menu3.menu.main_course.name} + {menu3.menu.dessert.name}")
        print(f"   💰 Total: {menu3.menu.total_price:.2f}€")
        print(f"   ⭐ Similitud: {menu3.similarity_score:.2%}")
        
        if menu3.menu.cultural_theme:
            print(f"   🌍 Tema cultural: {menu3.menu.cultural_theme}")
        
        # Feedback excelente
        feedback3 = FeedbackData(
            menu_id=menu3.menu.id,
            success=True,
            score=5.0,
            comments="¡Perfecto! Menú mediterráneo espectacular con excelente maridaje",
            would_recommend=True
        )
        
        print(f"\n📝 Feedback simulado:")
        print(f"   Satisfacción: {feedback3.score}/5.0 ⭐⭐⭐⭐⭐")
        print(f"   Comentario: '{feedback3.comments}'")
        
        print(f"\n🧠 Aprendiendo de feedback...")
        cbr.learn_from_feedback(feedback3, request3)
    
    # ========== RESUMEN DE APRENDIZAJE ==========
    print_separator("📊 RESUMEN DE APRENDIZAJE")
    
    learning_summary = cbr.weight_learner.get_learning_summary()
    
    print(f"\n🎓 Iteraciones de aprendizaje: {learning_summary['total_iterations']}")
    print(f"🔧 Ajustes totales: {learning_summary['total_adjustments']}")
    
    if learning_summary.get('most_changed'):
        print(f"\n📈 Pesos más modificados:")
        for item in learning_summary['most_changed']:
            print(f"   • {item['weight']}: {item['change_pct']}")
    
    print(f"\n💾 Pesos actuales:")
    current = learning_summary['current_weights']
    for weight_name, value in sorted(current.items(), key=lambda x: x[1], reverse=True)[:5]:
        bar = '█' * int(value * 50)
        print(f"   {weight_name:20s} [{bar:<25s}] {value:.3f}")
    
    # Guardar datos de aprendizaje
    print_separator("💾 GUARDANDO DATOS")
    
    cbr.save_learning_data('data/demo_learning_history.json')
    cbr.plot_learning_evolution('docs/demo')
    
    print(f"\n✅ Datos guardados:")
    print(f"   📄 Historial: data/demo_learning_history.json")
    print(f"   📊 Gráficas: docs/demo/")
    
    # Estadísticas del sistema
    print_separator("📊 ESTADÍSTICAS DEL SISTEMA")
    
    stats = cbr.get_statistics()
    
    print(f"\n📦 Base de casos:")
    print(f"   Total: {stats['case_base']['total_cases']}")
    print(f"   Positivos: {stats['case_base']['positive_cases']}")
    print(f"   Negativos: {stats['case_base']['negative_cases']}")
    
    print(f"\n🧠 Aprendizaje:")
    print(f"   Iteraciones: {stats['learning']['total_iterations']}")
    print(f"   Ajustes: {stats['learning']['total_adjustments']}")
    
    print_separator()
    print("✅ Demo completada exitosamente")
    print_separator()


if __name__ == "__main__":
    demo_adaptive_cbr()
