"""
Test para verificar que el AdaptiveWeightLearner aprende correctamente
con las dimensiones separadas de feedback.
"""

from develop.main import ChefDigitalCBR, CBRConfig
from develop.cycle.retain import FeedbackData
from develop.core.models import Request, EventType, Season, CulturalTradition, Feedback

def test_weight_learning_with_separate_dimensions():
    """
    Verifica que el weight learner ajusta pesos correctamente
    según las dimensiones específicas de satisfacción.
    """
    print("="*80)
    print("TEST: WEIGHT LEARNER CON DIMENSIONES SEPARADAS")
    print("="*80)
    
    # Crear sistema CBR con aprendizaje activado
    config = CBRConfig(
        case_base_path="cases.json",
        verbose=True,
        enable_learning=True
    )
    cbr = ChefDigitalCBR(config)
    
    # Obtener pesos iniciales
    initial_weights = cbr.weight_learner.get_current_weights()
    print("\n📊 PESOS INICIALES:")
    print(f"   price_range: {initial_weights.price_range:.4f}")
    print(f"   cultural:    {initial_weights.cultural:.4f}")
    print(f"   dietary:     {initial_weights.dietary:.4f}")
    print(f"   season:      {initial_weights.season:.4f}")
    
    # ============================================================================
    # ESCENARIO 1: Problema de PRECIO (precio malo, resto bien)
    # ============================================================================
    print("\n" + "="*80)
    print("ESCENARIO 1: PROBLEMA DE PRECIO")
    print("="*80)
    
    request1 = Request(
        event_type=EventType.FORMAL_DINNER,
        num_guests=6,
        season=Season.SPRING,
        required_diets=[],
        preferred_style=None,
        price_min=30.0,
        price_max=50.0,
        cultural_preference=CulturalTradition.ITALIAN
    )
    
    feedback1 = FeedbackData(
        menu_id="test_price_001",
        success=False,
        score=2.5,  # Score general bajo
        comments="El menú está demasiado caro para nuestro presupuesto",
        would_recommend=False,
        price_satisfaction=1.5,      # ⚠️ PROBLEMA PRECIO
        cultural_satisfaction=4.5,   # ✅ Cultura OK
        flavor_satisfaction=4.0      # ✅ Sabor OK
    )
    
    print(f"\n📝 Feedback recibido:")
    print(f"   General:  {feedback1.score:.1f}/5.0")
    print(f"   Precio:   {feedback1.price_satisfaction:.1f}/5.0  ⚠️ PROBLEMA")
    print(f"   Cultura:  {feedback1.cultural_satisfaction:.1f}/5.0  ✅")
    print(f"   Sabor:    {feedback1.flavor_satisfaction:.1f}/5.0  ✅")
    
    print("\n🧠 Aplicando aprendizaje...")
    cbr.learn_from_feedback(feedback1, request1)
    
    weights_after_1 = cbr.weight_learner.get_current_weights()
    price_change = weights_after_1.price_range - initial_weights.price_range
    
    print(f"\n📈 Cambio en peso 'price_range': {price_change:+.6f}")
    if price_change > 0:
        print(f"   ✅ CORRECTO: El peso de precio AUMENTÓ")
        print(f"   → El sistema priorizará mejor matching de precio en futuras búsquedas")
    else:
        print(f"   ⚠️ ADVERTENCIA: El peso de precio no aumentó como se esperaba")
    
    # ============================================================================
    # ESCENARIO 2: Problema de CULTURA (cultura mala, resto bien)
    # ============================================================================
    print("\n" + "="*80)
    print("ESCENARIO 2: PROBLEMA DE CULTURA")
    print("="*80)
    
    request2 = Request(
        event_type=EventType.CASUAL_GATHERING,
        num_guests=8,
        season=Season.SUMMER,
        required_diets=[],
        preferred_style=None,
        price_min=25.0,
        price_max=45.0,
        cultural_preference=CulturalTradition.FRENCH
    )
    
    feedback2 = FeedbackData(
        menu_id="test_culture_001",
        success=False,
        score=2.2,
        comments="El menú no respeta la tradición francesa solicitada",
        would_recommend=False,
        price_satisfaction=4.0,       # ✅ Precio OK
        cultural_satisfaction=1.0,    # ⚠️ PROBLEMA CULTURA
        flavor_satisfaction=3.5       # ✅ Sabor OK
    )
    
    print(f"\n📝 Feedback recibido:")
    print(f"   General:  {feedback2.score:.1f}/5.0")
    print(f"   Precio:   {feedback2.price_satisfaction:.1f}/5.0  ✅")
    print(f"   Cultura:  {feedback2.cultural_satisfaction:.1f}/5.0  ⚠️ PROBLEMA")
    print(f"   Sabor:    {feedback2.flavor_satisfaction:.1f}/5.0  ✅")
    
    print("\n🧠 Aplicando aprendizaje...")
    weights_before_2 = cbr.weight_learner.get_current_weights()
    cbr.learn_from_feedback(feedback2, request2)
    
    weights_after_2 = cbr.weight_learner.get_current_weights()
    cultural_change = weights_after_2.cultural - weights_before_2.cultural
    
    print(f"\n📈 Cambio en peso 'cultural': {cultural_change:+.6f}")
    if cultural_change > 0:
        print(f"   ✅ CORRECTO: El peso cultural AUMENTÓ")
        print(f"   → El sistema priorizará matching cultural en futuras búsquedas")
    else:
        print(f"   ⚠️ ADVERTENCIA: El peso cultural no aumentó como se esperaba")
    
    # ============================================================================
    # ESCENARIO 3: Problema de SABOR (sabor malo, resto bien)
    # ============================================================================
    print("\n" + "="*80)
    print("ESCENARIO 3: PROBLEMA DE SABOR")
    print("="*80)
    
    request3 = Request(
        event_type=EventType.BIRTHDAY,
        num_guests=10,
        season=Season.AUTUMN,
        required_diets=[],
        preferred_style=None,
        price_min=35.0,
        price_max=55.0,
        cultural_preference=None
    )
    
    feedback3 = FeedbackData(
        menu_id="test_flavor_001",
        success=False,
        score=2.3,
        comments="Los sabores no combinan bien, muy desbalanceado",
        would_recommend=False,
        price_satisfaction=4.5,       # ✅ Precio OK
        cultural_satisfaction=4.0,    # ✅ Cultura OK
        flavor_satisfaction=1.0       # ⚠️ PROBLEMA SABOR
    )
    
    print(f"\n📝 Feedback recibido:")
    print(f"   General:  {feedback3.score:.1f}/5.0")
    print(f"   Precio:   {feedback3.price_satisfaction:.1f}/5.0  ✅")
    print(f"   Cultura:  {feedback3.cultural_satisfaction:.1f}/5.0  ✅")
    print(f"   Sabor:    {feedback3.flavor_satisfaction:.1f}/5.0  ⚠️ PROBLEMA")
    
    print("\n🧠 Aplicando aprendizaje...")
    cbr.learn_from_feedback(feedback3, request3)
    
    print("\n💡 NOTA: El feedback de sabor se maneja principalmente")
    print("   en DishWeightLearner (nivel de platos individuales)")
    print("   A nivel de casos completos no hay peso directo para sabores")
    print("   Este feedback se gestiona durante la adaptación de platos")
    
    # ============================================================================
    # RESUMEN FINAL
    # ============================================================================
    print("\n" + "="*80)
    print("RESUMEN: EVOLUCIÓN DE PESOS")
    print("="*80)
    
    final_weights = cbr.weight_learner.get_current_weights()
    
    print(f"\n{'Peso':<20} {'Inicial':<12} {'Final':<12} {'Cambio':<12}")
    print("-" * 80)
    
    weights_to_check = {
        'price_range': (initial_weights.price_range, final_weights.price_range),
        'cultural': (initial_weights.cultural, final_weights.cultural),
        'dietary': (initial_weights.dietary, final_weights.dietary),
        'season': (initial_weights.season, final_weights.season),
        'guests': (initial_weights.guests, final_weights.guests),
        'event_type': (initial_weights.event_type, final_weights.event_type),
    }
    
    for weight_name, (initial, final) in weights_to_check.items():
        change = final - initial
        symbol = "↑" if change > 0 else "↓" if change < 0 else "="
        print(f"{weight_name:<20} {initial:<12.6f} {final:<12.6f} {change:+.6f} {symbol}")
    
    print("\n" + "="*80)
    print("VERIFICACIÓN DE APRENDIZAJE:")
    print("="*80)
    
    tests_passed = 0
    tests_total = 2
    
    # Test 1: Peso de precio debería haber aumentado
    if price_change > 0:
        print("✅ Test 1: Peso 'price_range' aumentó tras feedback de precio bajo")
        tests_passed += 1
    else:
        print("❌ Test 1: Peso 'price_range' NO aumentó (esperado)")
    
    # Test 2: Peso cultural debería haber aumentado
    if cultural_change > 0:
        print("✅ Test 2: Peso 'cultural' aumentó tras feedback cultural bajo")
        tests_passed += 1
    else:
        print("❌ Test 2: Peso 'cultural' NO aumentó (esperado)")
    
    print("\n" + "="*80)
    print(f"RESULTADO: {tests_passed}/{tests_total} tests pasados")
    print("="*80)
    
    if tests_passed == tests_total:
        print("\n✅ EL WEIGHT LEARNER APRENDE CORRECTAMENTE CON DIMENSIONES SEPARADAS")
        print("   - Detecta correctamente qué dimensión falló")
        print("   - Ajusta los pesos específicos apropiadamente")
        print("   - El aprendizaje es más preciso que con score único")
    else:
        print("\n⚠️ ALGUNOS TESTS FALLARON - Revisar implementación")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = test_weight_learning_with_separate_dimensions()
    exit(0 if success else 1)
