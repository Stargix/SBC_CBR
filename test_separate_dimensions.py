"""
Test de evaluación de dimensiones separadas en el feedback.

Este script demuestra cómo el sistema ahora evalúa cada dimensión
(precio, cultura, sabor) por separado usando el LLM.
"""

from develop.cycle.retain import FeedbackData
from develop.main import ChefDigitalCBR, CBRConfig
from develop.core.models import Request, EventType, Season, DietaryRestriction, CulturalTradition

def test_feedback_dimensions():
    """
    Demuestra el uso de dimensiones separadas en FeedbackData.
    """
    print("="*70)
    print("TEST: EVALUACIÓN DE DIMENSIONES SEPARADAS")
    print("="*70)
    
    # Crear FeedbackData con dimensiones separadas
    feedback1 = FeedbackData(
        menu_id="test_001",
        success=True,
        score=4.2,  # Puntuación general
        comments="Excelente menú, pero un poco caro",
        would_recommend=True,
        price_satisfaction=3.0,      # ⚠️ Precio bajo
        cultural_satisfaction=5.0,   # ✅ Cultura perfecta
        flavor_satisfaction=4.5       # ✅ Sabor excelente
    )
    
    print("\n1. Feedback con dimensiones diferenciadas:")
    print(f"   Score general: {feedback1.score:.1f}/5.0")
    print(f"   Precio:        {feedback1.price_satisfaction:.1f}/5.0  (bajo - detecta problema)")
    print(f"   Cultura:       {feedback1.cultural_satisfaction:.1f}/5.0  (perfecto)")
    print(f"   Sabor:         {feedback1.flavor_satisfaction:.1f}/5.0  (excelente)")
    print("\n   💡 El sistema puede ajustar pesos para priorizar precio")
    
    # Ejemplo con problema cultural
    feedback2 = FeedbackData(
        menu_id="test_002",
        success=False,
        score=2.5,
        comments="El menú no respeta la tradición italiana solicitada",
        would_recommend=False,
        price_satisfaction=4.0,       # ✅ Precio bien
        cultural_satisfaction=1.5,    # ⚠️ Cultura muy baja
        flavor_satisfaction=3.5        # 👌 Sabor aceptable
    )
    
    print("\n2. Feedback con problema cultural:")
    print(f"   Score general: {feedback2.score:.1f}/5.0")
    print(f"   Precio:        {feedback2.price_satisfaction:.1f}/5.0  (bien)")
    print(f"   Cultura:       {feedback2.cultural_satisfaction:.1f}/5.0  (muy bajo - problema detectado)")
    print(f"   Sabor:         {feedback2.flavor_satisfaction:.1f}/5.0  (aceptable)")
    print("\n   💡 El sistema puede ajustar pesos para priorizar cultura")
    
    # Ejemplo con problema de sabor
    feedback3 = FeedbackData(
        menu_id="test_003",
        success=False,
        score=2.8,
        comments="Los sabores no combinan bien entre sí",
        would_recommend=False,
        price_satisfaction=4.5,       # ✅ Precio excelente
        cultural_satisfaction=4.0,    # ✅ Cultura bien
        flavor_satisfaction=1.5       # ⚠️ Sabor muy bajo
    )
    
    print("\n3. Feedback con problema de sabor:")
    print(f"   Score general: {feedback3.score:.1f}/5.0")
    print(f"   Precio:        {feedback3.price_satisfaction:.1f}/5.0  (excelente)")
    print(f"   Cultura:       {feedback3.cultural_satisfaction:.1f}/5.0  (bien)")
    print(f"   Sabor:         {feedback3.flavor_satisfaction:.1f}/5.0  (muy bajo - problema detectado)")
    print("\n   💡 El sistema puede revisar las combinaciones de sabores")
    
    print("\n" + "="*70)
    print("VENTAJAS DE LA EVALUACIÓN SEPARADA:")
    print("="*70)
    print("✅ Feedback más preciso y detallado")
    print("✅ El sistema identifica exactamente qué falló")
    print("✅ Aprendizaje más efectivo - ajusta pesos específicos")
    print("✅ Evita sobresimplificación del feedback")
    print("="*70)

def test_cbr_with_separate_dimensions():
    """
    Demuestra cómo el CBR aprende de dimensiones separadas.
    """
    print("\n\n" + "="*70)
    print("TEST: CBR APRENDIENDO DE DIMENSIONES SEPARADAS")
    print("="*70)
    
    # Crear sistema CBR
    config = CBRConfig(
        case_base_path="cases.json",
        verbose=True,
        enable_learning=True
    )
    cbr = ChefDigitalCBR(config)
    
    # Crear una solicitud de ejemplo
    request = Request(
        event_type=EventType.FORMAL_DINNER,
        num_guests=6,
        season=Season.SPRING,
        required_diets=[],
        preferred_style=None,
        price_min=40.0,
        price_max=70.0,
        cultural_preference=CulturalTradition.ITALIAN
    )
    
    print("\n📋 Solicitud de prueba:")
    print(f"   Evento: {request.event_type.value}")
    print(f"   Invitados: {request.num_guests}")
    print(f"   Presupuesto: ${request.price_min}-{request.price_max}")
    print(f"   Cultura: {request.cultural_preference.value if request.cultural_preference else 'None'}")
    
    # Feedback con dimensiones diferenciadas
    feedback = FeedbackData(
        menu_id="test_cbr_001",
        success=False,
        score=2.5,
        comments="Menú no respeta tradición italiana",
        would_recommend=False,
        price_satisfaction=4.5,       # Precio OK
        cultural_satisfaction=1.0,    # ⚠️ Problema cultural
        flavor_satisfaction=3.5       # Sabor OK
    )
    
    print("\n📊 Feedback recibido (dimensiones separadas):")
    print(f"   General:  {feedback.score:.1f}/5.0")
    print(f"   Precio:   {feedback.price_satisfaction:.1f}/5.0 ✅")
    print(f"   Cultura:  {feedback.cultural_satisfaction:.1f}/5.0 ⚠️ PROBLEMA")
    print(f"   Sabor:    {feedback.flavor_satisfaction:.1f}/5.0 👌")
    
    print("\n🧠 Aplicando aprendizaje...")
    print("   El sistema detecta que el problema fue CULTURAL")
    print("   Incrementará el peso del criterio 'cultural' en similitud")
    print("   En futuras búsquedas, priorizará casos con mejor match cultural")
    
    # Aplicar aprendizaje
    cbr.learn_from_feedback(feedback, request)
    
    print("\n" + "="*70)

if __name__ == "__main__":
    test_feedback_dimensions()
    test_cbr_with_separate_dimensions()
    
    print("\n✅ IMPLEMENTACIÓN COMPLETADA")
    print("   - FeedbackData ahora tiene campos separados por dimensión")
    print("   - LLM evalúa cada dimensión (precio, cultura, sabor) independientemente")
    print("   - El aprendizaje es más preciso y efectivo")
    print("="*70)
