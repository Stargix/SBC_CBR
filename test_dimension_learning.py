"""
Test que fuerza escenarios problemáticos para ver el aprendizaje del weight learner.
Simula feedback negativo directamente sin necesidad de Groq.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from develop.main import ChefDigitalCBR, CBRConfig
from develop.cycle.retain import FeedbackData
from develop.core.models import Request, EventType, Season, CulturalTradition

def test_weight_learning_with_problems():
    """
    Test que muestra el aprendizaje con problemas específicos en cada dimensión.
    """
    print("="*80)
    print("TEST: APRENDIZAJE CON PROBLEMAS EN DIMENSIONES ESPECÍFICAS")
    print("="*80)
    
    # Crear sistema CBR
    config = CBRConfig(
        case_base_path="cases.json",
        verbose=True,
        enable_learning=True
    )
    cbr = ChefDigitalCBR(config)
    
    # Obtener pesos iniciales VERDADEROS (antes de cualquier aprendizaje)
    # Guardamos una copia profunda
    initial_weights_dict = {
        'price_range': cbr.weight_learner.weights.price_range,
        'cultural': cbr.weight_learner.weights.cultural,
        'dietary': cbr.weight_learner.weights.dietary,
        'season': cbr.weight_learner.weights.season,
        'event_type': cbr.weight_learner.weights.event_type,
        'guests': cbr.weight_learner.weights.guests,
    }
    
    print("\n📊 PESOS INICIALES (snapshot antes de aprendizaje):")
    print(f"   price_range: {initial_weights_dict['price_range']:.6f}")
    print(f"   cultural:    {initial_weights_dict['cultural']:.6f}")
    print(f"   dietary:     {initial_weights_dict['dietary']:.6f}")
    print(f"   season:      {initial_weights_dict['season']:.6f}")
    
    # ============================================================================
    # ESCENARIO 1: Problema de PRECIO (demasiado caro)
    # ============================================================================
    print("\n" + "="*80)
    print("ESCENARIO 1: PROBLEMA DE PRECIO")
    print("Cliente insatisfecho porque el menú está muy caro")
    print("="*80)
    
    request1 = Request(
        event_type=EventType.FAMILIAR,
        num_guests=6,
        season=Season.SPRING,
        required_diets=[],
        preferred_style=None,
        price_min=20.0,
        price_max=35.0,
        cultural_preference=None
    )
    
    # Simular feedback con PRECIO bajo pero resto OK
    feedback1 = FeedbackData(
        menu_id="test_price_problem",
        success=False,
        score=2.3,  # Score general bajo
        comments="El menú está demasiado caro para nuestro presupuesto. Los platos están bien pero el precio es excesivo.",
        would_recommend=False,
        price_satisfaction=1.5,      # ⚠️ PRECIO MUY BAJO
        cultural_satisfaction=4.0,   # ✅ Cultura OK
        flavor_satisfaction=4.2      # ✅ Sabor OK
    )
    
    print(f"\n📝 Feedback recibido:")
    print(f"   General:  {feedback1.score:.1f}/5.0  (insatisfecho)")
    print(f"   Precio:   {feedback1.price_satisfaction:.1f}/5.0  ⚠️ PROBLEMA IDENTIFICADO")
    print(f"   Cultura:  {feedback1.cultural_satisfaction:.1f}/5.0  ✅ OK")
    print(f"   Sabor:    {feedback1.flavor_satisfaction:.1f}/5.0  ✅ OK")
    
    print("\n🧠 Aplicando aprendizaje...")
    cbr.learn_from_feedback(feedback1, request1)
    
    weights_after_1 = cbr.weight_learner.get_current_weights()
    price_change = weights_after_1.price_range - initial_weights_dict['price_range']
    
    print(f"\n📈 Cambio en peso 'price_range': {price_change:+.6f}")
    print(f"   Inicial: {initial_weights_dict['price_range']:.6f}")
    print(f"   Final:   {weights_after_1.price_range:.6f}")
    if price_change > 0.001:
        print(f"   ✅ ÉXITO: El peso de precio AUMENTÓ significativamente")
    else:
        print(f"   ⚠️ El peso de precio cambió poco: {price_change:+.8f}")
    
    # ============================================================================
    # ESCENARIO 2: Problema de CULTURA
    # ============================================================================
    print("\n" + "="*80)
    print("ESCENARIO 2: PROBLEMA DE CULTURA")
    print("Cliente insatisfecho porque no respeta la tradición italiana solicitada")
    print("="*80)
    
    request2 = Request(
        event_type=EventType.WEDDING,
        num_guests=8,
        season=Season.SUMMER,
        required_diets=[],
        preferred_style=None,
        price_min=40.0,
        price_max=60.0,
        cultural_preference=CulturalTradition.ITALIAN
    )
    
    feedback2 = FeedbackData(
        menu_id="test_culture_problem",
        success=False,
        score=2.1,
        comments="El menú no respeta la tradición italiana que solicitamos. Los ingredientes no son apropiados.",
        would_recommend=False,
        price_satisfaction=4.0,       # ✅ Precio OK
        cultural_satisfaction=1.0,    # ⚠️ CULTURA MUY BAJA
        flavor_satisfaction=3.5       # 👌 Sabor aceptable
    )
    
    print(f"\n📝 Feedback recibido:")
    print(f"   General:  {feedback2.score:.1f}/5.0  (muy insatisfecho)")
    print(f"   Precio:   {feedback2.price_satisfaction:.1f}/5.0  ✅ OK")
    print(f"   Cultura:  {feedback2.cultural_satisfaction:.1f}/5.0  ⚠️ PROBLEMA GRAVE")
    print(f"   Sabor:    {feedback2.flavor_satisfaction:.1f}/5.0  👌 Aceptable")
    
    print("\n🧠 Aplicando aprendizaje...")
    weights_before_2 = cbr.weight_learner.get_current_weights()
    cbr.learn_from_feedback(feedback2, request2)
    
    weights_after_2 = cbr.weight_learner.get_current_weights()
    cultural_change = weights_after_2.cultural - weights_before_2.cultural
    
    print(f"\n📈 Cambio en peso 'cultural': {cultural_change:+.6f}")
    print(f"   Antes:   {weights_before_2.cultural:.6f}")
    print(f"   Después: {weights_after_2.cultural:.6f}")
    if cultural_change > 0.001:
        print(f"   ✅ ÉXITO: El peso cultural AUMENTÓ significativamente")
    else:
        print(f"   ⚠️ El peso cultural cambió poco: {cultural_change:+.8f}")
    
    # ============================================================================
    # ESCENARIO 3: Problema de SABOR
    # ============================================================================
    print("\n" + "="*80)
    print("ESCENARIO 3: PROBLEMA DE SABOR")
    print("Cliente insatisfecho porque los sabores no combinan bien")
    print("="*80)
    
    request3 = Request(
        event_type=EventType.CHRISTENING,
        num_guests=10,
        season=Season.AUTUMN,
        required_diets=[],
        preferred_style=None,
        price_min=35.0,
        price_max=55.0,
        cultural_preference=None
    )
    
    feedback3 = FeedbackData(
        menu_id="test_flavor_problem",
        success=False,
        score=2.4,
        comments="Los sabores no combinan bien entre sí. Demasiado desbalanceado.",
        would_recommend=False,
        price_satisfaction=4.5,       # ✅ Precio excelente
        cultural_satisfaction=4.0,    # ✅ Cultura OK
        flavor_satisfaction=1.2       # ⚠️ SABOR MUY BAJO
    )
    
    print(f"\n📝 Feedback recibido:")
    print(f"   General:  {feedback3.score:.1f}/5.0  (insatisfecho)")
    print(f"   Precio:   {feedback3.price_satisfaction:.1f}/5.0  ✅ Excelente")
    print(f"   Cultura:  {feedback3.cultural_satisfaction:.1f}/5.0  ✅ OK")
    print(f"   Sabor:    {feedback3.flavor_satisfaction:.1f}/5.0  ⚠️ PROBLEMA GRAVE")
    
    print("\n🧠 Aplicando aprendizaje...")
    cbr.learn_from_feedback(feedback3, request3)
    
    print("\n💡 NOTA sobre sabor:")
    print("   El feedback de sabor se maneja principalmente a nivel de platos")
    print("   (DishWeightLearner) y durante la adaptación, no tanto en los")
    print("   pesos de similitud de casos completos.")
    
    # ============================================================================
    # RESUMEN FINAL
    # ============================================================================
    print("\n" + "="*80)
    print("RESUMEN: EVOLUCIÓN DE PESOS TRAS APRENDIZAJE")
    print("="*80)
    
    final_weights = cbr.weight_learner.get_current_weights()
    
    print(f"\n{'Peso':<20} {'Inicial':<15} {'Final':<15} {'Cambio':<15} {'%':<10}")
    print("-" * 80)
    
    weights_to_compare = {
        'price_range': (initial_weights_dict['price_range'], final_weights.price_range),
        'cultural': (initial_weights_dict['cultural'], final_weights.cultural),
        'dietary': (initial_weights_dict['dietary'], final_weights.dietary),
        'season': (initial_weights_dict['season'], final_weights.season),
        'event_type': (initial_weights_dict['event_type'], final_weights.event_type),
    }
    
    for weight_name, (initial, final) in weights_to_compare.items():
        change = final - initial
        pct_change = (change / initial * 100) if initial > 0 else 0
        symbol = "↑" if change > 0.001 else "↓" if change < -0.001 else "="
        print(f"{weight_name:<20} {initial:<15.6f} {final:<15.6f} {change:+.6f} {symbol}    {pct_change:+.1f}%")
    
    # ============================================================================
    # VERIFICACIÓN
    # ============================================================================
    print("\n" + "="*80)
    print("VERIFICACIÓN DE APRENDIZAJE:")
    print("="*80)
    
    tests_passed = 0
    tests_total = 2
    
    # Test 1: Peso de precio debería haber aumentado
    if price_change > 0.001:
        print("✅ Test 1: Peso 'price_range' aumentó tras problema de precio")
        print(f"   Cambio: {price_change:+.6f} ({price_change/initial_weights_dict['price_range']*100:+.1f}%)")
        tests_passed += 1
    else:
        print("❌ Test 1: Peso 'price_range' NO aumentó suficientemente")
        print(f"   Cambio: {price_change:+.8f}")
        print(f"   (El cambio es muy pequeño debido a la normalización)")
    
    # Test 2: Peso cultural debería haber aumentado
    if cultural_change > 0.001:
        print("✅ Test 2: Peso 'cultural' aumentó tras problema cultural")
        print(f"   Cambio: {cultural_change:+.6f} ({cultural_change/weights_before_2.cultural*100:+.1f}%)")
        tests_passed += 1
    else:
        print("❌ Test 2: Peso 'cultural' NO aumentó suficientemente")
        print(f"   Cambio: {cultural_change:+.8f}")
        print(f"   (El cambio es muy pequeño debido a la normalización)")
    
    print("\n" + "="*80)
    print(f"RESULTADO: {tests_passed}/{tests_total} tests pasados")
    print("="*80)
    
    if tests_passed == tests_total:
        print("\n🎉 ¡ÉXITO! EL APRENDIZAJE CON DIMENSIONES SEPARADAS FUNCIONA")
        print("\n✅ Demostración exitosa:")
        print("   - Problema de PRECIO → Peso 'price_range' aumentó")
        print("   - Problema de CULTURA → Peso 'cultural' aumentó")
        print("   - El sistema aprende de dimensiones específicas")
        print("   - El aprendizaje es más preciso que con score único")
        
        print("\n📊 BENEFICIO DE DIMENSIONES SEPARADAS:")
        print("   Sin dimensiones: Todos los pesos se ajustarían igual")
        print("   Con dimensiones: Solo el peso problemático se ajusta")
        print("   → Aprendizaje más eficiente y preciso")
    else:
        print("\n⚠️ ALGUNOS TESTS FALLARON")
        print("   Posibles razones:")
        print("   - Learning rate muy bajo")
        print("   - Umbrales de ajuste muy conservadores")
        print("   - Normalización compensando los cambios")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = test_weight_learning_with_problems()
    exit(0 if success else 1)
