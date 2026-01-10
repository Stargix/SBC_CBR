"""
Demo que verifica que la similaridad semantica cultural funciona en RETAIN.

Muestra como RETAIN usa embeddings para evaluar si un nuevo caso es novedoso
o redundante, considerando la distancia semantica entre culturas.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from develop.core.case_base import CaseBase
from develop.core.models import (
    Request, Menu, Dish, Case, EventType, Season, 
    CulturalTradition, DishType, DishCategory, 
    CulinaryStyle, Flavor, Temperature, Complexity
)
from develop.cycle.retain import CaseRetainer, FeedbackData


def print_separator(title: str = "", char: str = "="):
    if title:
        print(f"\n{char * 80}")
        print(f"  {title}")
        print(f"{char * 80}")
    else:
        print(f"{char * 80}")


def demo_retain_semantic_similarity():
    """
    Demuestra como RETAIN usa similaridad semantica cultural.
    """
    print_separator("DEMO: Similaridad Semantica Cultural en RETAIN")
    
    # 1. Crear case base
    print("\nCreando base de casos...")
    case_base = CaseBase()
    print(f"   OK - {len(case_base.cases)} casos iniciales")
    
    # 2. Crear retainer
    retainer = CaseRetainer(case_base)
    
    # Verificar que usa embeddings
    print(f"\n   Configuracion del SimilarityCalculator:")
    print(f"      use_embeddings_for_culture: {retainer.similarity_calc.use_embeddings_for_culture}")
    print(f"      semantic_calculator disponible: {retainer.similarity_calc.semantic_calculator is not None}")
    
    # 3. Test: Nuevo caso con cultura ITALIANA
    print_separator("TEST 1: Evaluar caso ITALIANO similar a ESPAÑOL existente", "-")
    
    # Request con cultura italiana
    request_italian = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=40.0,
        price_max=60.0,
        season=Season.SUMMER,
        cultural_preference=CulturalTradition.ITALIAN
    )
    
    # Menu italiano (simplificado)
    menu_italian = Menu(
        starter=Dish(
            id="test-starter",
            name="Bruschetta",
            dish_type=DishType.STARTER,
            category=DishCategory.SALAD,
            price=15.0,
            ingredients=["tomato", "basil", "olive oil", "bread"],
            styles=[CulinaryStyle.CLASSIC],
            flavors=[Flavor.SALTY],
            temperature=Temperature.WARM,
            complexity=Complexity.LOW
        ),
        main_course=Dish(
            id="test-main",
            name="Pasta Carbonara",
            dish_type=DishType.MAIN_COURSE,
            category=DishCategory.PASTA,
            price=25.0,
            ingredients=["pasta", "eggs", "bacon", "cheese"],
            styles=[CulinaryStyle.CLASSICAL],
            flavors=[Flavor.SALTY, Flavor.UMAMI],
            temperature=Temperature.HOT,
            complexity=Complexity.MEDIUM
        ),
        dessert=Dish(
            id="test-dessert",
            name="Tiramisu",
            dish_type=DishType.DESSERT,
            category=DishCategory.PASTRY,
            price=12.0,
            ingredients=["mascarpone", "coffee", "cocoa"],
            styles=[CulinaryStyle.GOURMET],
            flavors=[Flavor.SWEET],
            temperature=Temperature.COLD,
            complexity=Complexity.MEDIUM
        ),
        cultural_theme=CulturalTradition.ITALIAN
    )
    menu_italian.calculate_totals()
    
    # Feedback positivo
    feedback_good = FeedbackData(
        menu_id="test-menu-1",
        success=True,
        score=4.5,
        comments="Excelente",
        would_recommend=True
    )
    
    # Evaluar retención
    decision = retainer.evaluate_retention(request_italian, menu_italian, feedback_good)
    
    print(f"\n   Request: Cultura {request_italian.cultural_preference.value.upper()}")
    print(f"   Menu: Cultura {menu_italian.cultural_theme.value}")
    print(f"\n   >> Decision: {decision.action}")
    print(f"   >> Debe retener: {decision.should_retain}")
    print(f"   >> Razon: {decision.reason}")
    print(f"   >> Similaridad con existente: {decision.similarity_to_existing:.2%}")
    
    if decision.most_similar_case:
        most_similar_culture = decision.most_similar_case.menu.cultural_theme
        print(f"   >> Caso mas similar: #{decision.most_similar_case.id}")
        print(f"      Cultura del caso similar: {most_similar_culture.value if most_similar_culture else 'sin cultura'}")
        
        # Calcular similaridad cultural específica
        if most_similar_culture:
            cultural_sim = retainer.similarity_calc._cultural_similarity(
                CulturalTradition.ITALIAN,
                most_similar_culture
            )
            print(f"      Similaridad cultural semantica: {cultural_sim:.2%}")
    
    # 4. Test 2: Nuevo caso con cultura COREANA (diferente)
    print_separator("TEST 2: Evaluar caso COREANO (cultura diferente)", "-")
    
    request_korean = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=40.0,
        price_max=60.0,
        season=Season.SUMMER,
        cultural_preference=CulturalTradition.KOREAN
    )
    
    menu_korean = Menu(
        starter=Dish(
            id="test-starter-k",
            name="Kimchi",
            dish_type=DishType.STARTER,
            category=DishCategory.SALAD,
            price=15.0,
            ingredients=["cabbage", "chili", "garlic"],
            styles=[CulinaryStyle.REGIONAL],
            flavors=[Flavor.SPICY],
            temperature=Temperature.COLD,
            complexity=Complexity.LOW
        ),
        main_course=Dish(
            id="test-main-k",
            name="Bibimbap",
            dish_type=DishType.MAIN_COURSE,
            category=DishCategory.RICE,
            price=25.0,
            ingredients=["rice", "beef", "vegetables", "egg"],
            styles=[CulinaryStyle.REGIONAL],
            flavors=[Flavor.SALTY, Flavor.SPICY],
            temperature=Temperature.HOT,
            complexity=Complexity.MEDIUM
        ),
        dessert=Dish(
            id="test-dessert-k",
            name="Hotteok",
            dish_type=DishType.DESSERT,
            category=DishCategory.PASTRY,
            price=12.0,
            ingredients=["flour", "cinnamon", "brown sugar"],
            styles=[CulinaryStyle.TRADITIONAL],
            flavors=[Flavor.SWEET],
            temperature=Temperature.WARM,
            complexity=Complexity.LOW
        ),
        cultural_theme=CulturalTradition.KOREAN
    )
    menu_korean.calculate_totals()
    
    decision2 = retainer.evaluate_retention(request_korean, menu_korean, feedback_good)
    
    print(f"\n   Request: Cultura {request_korean.cultural_preference.value.upper()}")
    print(f"   Menu: Cultura {menu_korean.cultural_theme.value}")
    print(f"\n   >> Decision: {decision2.action}")
    print(f"   >> Debe retener: {decision2.should_retain}")
    print(f"   >> Razon: {decision2.reason}")
    print(f"   >> Similaridad con existente: {decision2.similarity_to_existing:.2%}")
    
    if decision2.most_similar_case:
        most_similar_culture2 = decision2.most_similar_case.menu.cultural_theme
        print(f"   >> Caso mas similar: #{decision2.most_similar_case.id}")
        print(f"      Cultura del caso similar: {most_similar_culture2.value if most_similar_culture2 else 'sin cultura'}")
        
        if most_similar_culture2:
            cultural_sim2 = retainer.similarity_calc._cultural_similarity(
                CulturalTradition.KOREAN,
                most_similar_culture2
            )
            print(f"      Similaridad cultural semantica: {cultural_sim2:.2%}")
    
    # 5. Comparar similaridades
    print_separator("COMPARACION DE SIMILARIDADES CULTURALES", "-")
    
    print("\n   Similaridades semanticas relevantes:")
    
    cultures_to_compare = [
        (CulturalTradition.ITALIAN, CulturalTradition.SPANISH),
        (CulturalTradition.ITALIAN, CulturalTradition.FRENCH),
        (CulturalTradition.KOREAN, CulturalTradition.JAPANESE),
        (CulturalTradition.KOREAN, CulturalTradition.CHINESE),
        (CulturalTradition.ITALIAN, CulturalTradition.KOREAN),
    ]
    
    for cult1, cult2 in cultures_to_compare:
        sim = retainer.similarity_calc._cultural_similarity(cult1, cult2)
        print(f"      {cult1.value} <-> {cult2.value}: {sim:.2%}")
    
    print_separator()
    print("\n*** Observaciones:")
    print("   - RETAIN usa embeddings para calcular similaridad entre casos")
    print("   - Culturas semanticamente cercanas (italiana-espanola) tienen")
    print("     mayor probabilidad de ser consideradas redundantes")
    print("   - Culturas lejanas (italiana-coreana) tienen mas probabilidad")
    print("     de ser retenidas como casos novedosos")
    print("   - Esto mejora la diversidad y calidad de la base de casos")
    print("\n")


if __name__ == "__main__":
    demo_retain_semantic_similarity()
