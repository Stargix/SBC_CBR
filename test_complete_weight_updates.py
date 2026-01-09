"""
Test para verificar que TODOS los pesos se actualizan correctamente
incluyendo style, wine_preference, guests, event_type y season.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'develop'))

from core.adaptive_weights import AdaptiveWeightLearner
from core.models import (
    Feedback, Request, EventType, Season,
    CulturalTradition, Menu, Dish, DishType, DishCategory, 
    CulinaryStyle, Flavor, Temperature, Complexity, Beverage
)


def create_test_menu():
    """Crea un menú de prueba con estilos específicos"""
    starter = Dish(
        id="starter1",
        name="Ensalada Caprese",
        dish_type=DishType.STARTER,
        category=DishCategory.SALAD,
        price=12.0,
        calories=200,
        complexity=Complexity.LOW,
        flavors=[Flavor.SALTY, Flavor.SOUR],
        styles=[CulinaryStyle.CLASSIC, CulinaryStyle.REGIONAL],
        temperature=Temperature.COLD,
        ingredients=["tomato", "mozzarella", "basil"],
        diets=[],
        cultural_traditions=[CulturalTradition.ITALIAN]
    )
    
    main = Dish(
        id="main1",
        name="Filete Wellington",
        dish_type=DishType.MAIN_COURSE,
        category=DishCategory.MEAT,
        price=45.0,
        calories=650,
        complexity=Complexity.HIGH,
        flavors=[Flavor.UMAMI, Flavor.FATTY],
        styles=[CulinaryStyle.GOURMET, CulinaryStyle.CLASSIC],
        temperature=Temperature.HOT,
        ingredients=["beef", "puff_pastry", "mushroom"],
        diets=[],
        cultural_traditions=[CulturalTradition.FRENCH]
    )
    
    dessert = Dish(
        id="dessert1",
        name="Tiramisu",
        dish_type=DishType.DESSERT,
        category=DishCategory.PASTRY,
        price=10.0,
        calories=350,
        complexity=Complexity.MEDIUM,
        flavors=[Flavor.SWEET, Flavor.BITTER],
        styles=[CulinaryStyle.CLASSIC],
        temperature=Temperature.COLD,
        ingredients=["mascarpone", "coffee", "ladyfingers"],
        diets=[],
        cultural_traditions=[CulturalTradition.ITALIAN]
    )
    
    beverage = Beverage(
        id="bev1",
        name="Vino Tinto Reserva",
        alcoholic=True,
        price=25.0,
        type="red-wine",
        subtype="full-bodied"
    )
    
    return Menu(
        id="menu1",
        starter=starter,
        main_course=main,
        dessert=dessert,
        beverage=beverage
    )


def test_style_weight_updates():
    """Test: style se actualiza con estilos apropiados/inapropiados"""
    print("\n" + "="*70)
    print("TEST 1: Actualización de peso 'style'")
    print("="*70)
    
    learner = AdaptiveWeightLearner(learning_rate=0.1)
    initial_style = learner.weights.style
    
    # Crear request de boda (espera GOURMET, SIBARITA, CLASSIC)
    request = Request(
        event_type=EventType.WEDDING,
        season=Season.SUMMER,
        num_guests=100,
        price_min=50,
        price_max=80
    )
    
    # Crear menú con estilos apropiados (GOURMET, CLASSIC)
    menu = create_test_menu()
    
    # Feedback positivo
    feedback = Feedback(
        overall_satisfaction=5.0,
        price_satisfaction=5.0,
        cultural_satisfaction=3.0,
        flavor_satisfaction=5.0,
        dietary_satisfaction=5.0,
        comments="Excelente!"
    )
    
    adjustments = learner.update_from_feedback(feedback, request, menu)
    
    print(f"\n📊 Request: {request.event_type.value}")
    print(f"   Estilos del menú: GOURMET, CLASSIC")
    print(f"   Feedback: {feedback.overall_satisfaction}/5")
    print(f"\n✅ Peso 'style' inicial: {initial_style:.4f}")
    print(f"✅ Peso 'style' final: {learner.weights.style:.4f}")
    print(f"✅ Delta: {learner.weights.style - initial_style:+.4f}")
    
    if 'style' in adjustments:
        print(f"✅ ✓ 'style' fue actualizado correctamente")
        return True
    else:
        print(f"❌ ✗ 'style' NO fue actualizado")
        return False


def test_wine_preference_updates():
    """Test: wine_preference se actualiza con feedback de sabor"""
    print("\n" + "="*70)
    print("TEST 2: Actualización de peso 'wine_preference'")
    print("="*70)
    
    learner = AdaptiveWeightLearner(learning_rate=0.1)
    initial_wine = learner.weights.wine_preference
    
    # Request con preferencia de vino
    request = Request(
        event_type=EventType.WEDDING,
        season=Season.SUMMER,
        num_guests=100,
        price_min=50,
        price_max=80,
        wants_wine=True
    )
    
    menu = create_test_menu()
    
    # Feedback positivo de sabor (buen maridaje)
    feedback = Feedback(
        overall_satisfaction=4.5,
        price_satisfaction=4.0,
        cultural_satisfaction=3.0,
        flavor_satisfaction=5.0,  # Maridaje excelente
        dietary_satisfaction=5.0,
        comments="El vino combinaba perfectamente"
    )
    
    adjustments = learner.update_from_feedback(feedback, request, menu)
    
    print(f"\n📊 Request wine wants_wine: {request.wants_wine}")
    print(f"   Feedback flavor_satisfaction: {feedback.flavor_satisfaction}/5")
    print(f"\n✅ Peso 'wine_preference' inicial: {initial_wine:.4f}")
    print(f"✅ Peso 'wine_preference' final: {learner.weights.wine_preference:.4f}")
    print(f"✅ Delta: {learner.weights.wine_preference - initial_wine:+.4f}")
    
    if 'wine_preference' in adjustments:
        print(f"✅ ✓ 'wine_preference' fue actualizado correctamente")
        return True
    else:
        print(f"❌ ✗ 'wine_preference' NO fue actualizado")
        return False


def test_guests_positive_update():
    """Test: guests se actualiza positivamente con eventos grandes exitosos"""
    print("\n" + "="*70)
    print("TEST 3: Actualización positiva de peso 'guests'")
    print("="*70)
    
    learner = AdaptiveWeightLearner(learning_rate=0.1)
    initial_guests = learner.weights.guests
    
    # Request con muchos invitados
    request = Request(
        event_type=EventType.CONGRESS,
        season=Season.AUTUMN,
        num_guests=200,  # Evento grande
        price_min=30,
        price_max=50
    )
    
    menu = create_test_menu()
    
    # Feedback muy positivo
    feedback = Feedback(
        overall_satisfaction=5.0,
        price_satisfaction=4.5,
        cultural_satisfaction=3.0,
        flavor_satisfaction=4.5,
        dietary_satisfaction=5.0,
        comments="Servicio eficiente para 200 personas"
    )
    
    adjustments = learner.update_from_feedback(feedback, request, menu)
    
    print(f"\n📊 Número de invitados: {request.num_guests}")
    print(f"   Feedback: {feedback.overall_satisfaction}/5")
    print(f"\n✅ Peso 'guests' inicial: {initial_guests:.4f}")
    print(f"✅ Peso 'guests' final: {learner.weights.guests:.4f}")
    print(f"✅ Delta: {learner.weights.guests - initial_guests:+.4f}")
    
    if 'guests' in adjustments and adjustments['guests'] > 0:
        print(f"✅ ✓ 'guests' fue incrementado correctamente")
        return True
    else:
        print(f"❌ ✗ 'guests' NO fue incrementado (solo decrementos anteriormente)")
        return False


def test_event_type_expanded():
    """Test: event_type se actualiza con satisfacción >=4 (no solo 5)"""
    print("\n" + "="*70)
    print("TEST 4: Actualización expandida de 'event_type'")
    print("="*70)
    
    learner = AdaptiveWeightLearner(learning_rate=0.1)
    initial_event = learner.weights.event_type
    
    request = Request(
        event_type=EventType.CORPORATE,
        season=Season.SPRING,
        num_guests=50,
        price_min=40,
        price_max=60
    )
    
    menu = create_test_menu()
    
    # Feedback 4/5 (antes no se actualizaba, solo con 5/5)
    feedback = Feedback(
        overall_satisfaction=4.0,
        price_satisfaction=4.0,
        cultural_satisfaction=3.0,
        flavor_satisfaction=4.5,
        dietary_satisfaction=5.0,
        comments="Muy bueno"
    )
    
    adjustments = learner.update_from_feedback(feedback, request, menu)
    
    print(f"\n📊 Event type: {request.event_type.value}")
    print(f"   Feedback: {feedback.overall_satisfaction}/5 (antes requería 5/5)")
    print(f"\n✅ Peso 'event_type' inicial: {initial_event:.4f}")
    print(f"✅ Peso 'event_type' final: {learner.weights.event_type:.4f}")
    print(f"✅ Delta: {learner.weights.event_type - initial_event:+.4f}")
    
    if 'event_type' in adjustments:
        print(f"✅ ✓ 'event_type' actualizado con feedback 4/5 (expandido)")
        return True
    else:
        print(f"❌ ✗ 'event_type' NO fue actualizado")
        return False


def test_season_positive_update():
    """Test: season se actualiza positivamente con buen flavor_satisfaction"""
    print("\n" + "="*70)
    print("TEST 5: Actualización positiva de 'season'")
    print("="*70)
    
    learner = AdaptiveWeightLearner(learning_rate=0.1)
    initial_season = learner.weights.season
    
    request = Request(
        event_type=EventType.WEDDING,
        season=Season.SUMMER,
        num_guests=80,
        price_min=50,
        price_max=70
    )
    
    menu = create_test_menu()
    
    # Feedback con excelente sabor (ingredientes de temporada)
    feedback = Feedback(
        overall_satisfaction=4.5,
        price_satisfaction=4.0,
        cultural_satisfaction=3.0,
        flavor_satisfaction=5.0,  # Ingredientes frescos de temporada
        dietary_satisfaction=5.0,
        comments="Ingredientes fresquísimos de temporada"
    )
    
    adjustments = learner.update_from_feedback(feedback, request, menu)
    
    print(f"\n📊 Temporada: {request.season.value}")
    print(f"   Feedback flavor: {feedback.flavor_satisfaction}/5")
    print(f"\n✅ Peso 'season' inicial: {initial_season:.4f}")
    print(f"✅ Peso 'season' final: {learner.weights.season:.4f}")
    print(f"✅ Delta: {learner.weights.season - initial_season:+.4f}")
    
    if 'season' in adjustments and adjustments['season'] > 0:
        print(f"✅ ✓ 'season' fue incrementado correctamente")
        return True
    else:
        print(f"❌ ✗ 'season' NO fue incrementado (solo decrementos anteriormente)")
        return False


def test_all_weights_summary():
    """Test resumen: verificar que todos los pesos pueden actualizarse"""
    print("\n" + "="*70)
    print("TEST 6: RESUMEN - Todos los pesos actualizables")
    print("="*70)
    
    learner = AdaptiveWeightLearner(learning_rate=0.1)
    
    # Request completo
    request = Request(
        event_type=EventType.WEDDING,
        season=Season.SUMMER,
        num_guests=150,
        price_min=60,
        price_max=85,
        wants_wine=True,
        cultural_preference=CulturalTradition.ITALIAN,
        required_diets=["vegetarian"]
    )
    
    menu = create_test_menu()
    
    # Feedback muy positivo en todas las dimensiones
    feedback = Feedback(
        overall_satisfaction=5.0,
        price_satisfaction=5.0,
        cultural_satisfaction=5.0,
        flavor_satisfaction=5.0,
        dietary_satisfaction=5.0,
        comments="Perfecto en todos los aspectos"
    )
    
    adjustments = learner.update_from_feedback(feedback, request, menu)
    
    print(f"\n📊 Pesos actualizados:")
    all_weights = [
        'event_type', 'season', 'price_range', 'style', 
        'cultural', 'dietary', 'guests', 'wine_preference'
    ]
    
    updated_count = 0
    for weight in all_weights:
        if weight in adjustments:
            print(f"   ✅ {weight}: {adjustments[weight]:+.4f}")
            updated_count += 1
        else:
            print(f"   ⚪ {weight}: no actualizado")
    
    print(f"\n📈 Total actualizado: {updated_count}/{len(all_weights)} pesos")
    
    # Verificar los que DEBEN estar presentes
    critical_weights = ['event_type', 'style', 'wine_preference', 'season', 'guests']
    critical_updated = sum(1 for w in critical_weights if w in adjustments)
    
    print(f"🎯 Pesos críticos actualizados: {critical_updated}/{len(critical_weights)}")
    
    return critical_updated >= 4  # Al menos 4 de 5 críticos


def main():
    """Ejecuta todos los tests"""
    print("\n" + "="*70)
    print("VERIFICACIÓN COMPLETA DE ACTUALIZACIÓN DE PESOS ADAPTIVOS")
    print("="*70)
    
    results = []
    
    results.append(("style", test_style_weight_updates()))
    results.append(("wine_preference", test_wine_preference_updates()))
    results.append(("guests positivo", test_guests_positive_update()))
    results.append(("event_type expandido", test_event_type_expanded()))
    results.append(("season positivo", test_season_positive_update()))
    results.append(("resumen completo", test_all_weights_summary()))
    
    print("\n" + "="*70)
    print("RESULTADOS FINALES")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*70}")
    print(f"Tests pasados: {passed}/{total} ({passed/total*100:.1f}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ¡TODOS LOS PESOS SE ACTUALIZAN CORRECTAMENTE!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) fallaron")
        return 1


if __name__ == "__main__":
    exit(main())
