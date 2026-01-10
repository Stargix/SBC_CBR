"""
Test: Semantic Similarity in RETAIN Phase
==========================================

Evaluates how semantic cultural similarity affects retention decisions,
preventing redundant cases while allowing culturally diverse ones.

Metrics:
- Retention decision accuracy
- Semantic redundancy detection
- Cultural diversity maintenance
"""

import sys
import json
from pathlib import Path
from typing import Dict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop.core.case_base import CaseBase
from develop.core.models import (
    Request, Menu, Dish, EventType, Season, CulturalTradition,
    DishType, DishCategory, CulinaryStyle, Flavor, Temperature, Complexity
)
from develop.cycle.retain import CaseRetainer, FeedbackData


def create_test_menu(culture: CulturalTradition, menu_id: str) -> Menu:
    """Create a test menu with specific cultural theme."""
    
    from develop.core.models import Beverage
    
    return Menu(
        id=menu_id,
        starter=Dish(
            id=f"{menu_id}-starter",
            name=f"{culture.value} Starter",
            dish_type=DishType.STARTER,
            category=DishCategory.SALAD,
            price=15.0,
            ingredients=["test_ingredient_1", "test_ingredient_2"],
            styles=[CulinaryStyle.CLASSIC],
            flavors=[Flavor.SALTY],
            temperature=Temperature.WARM,
            complexity=Complexity.LOW
        ),
        main_course=Dish(
            id=f"{menu_id}-main",
            name=f"{culture.value} Main",
            dish_type=DishType.MAIN_COURSE,
            category=DishCategory.MEAT,
            price=30.0,
            ingredients=["test_ingredient_3", "test_ingredient_4"],
            styles=[CulinaryStyle.CLASSICAL],
            flavors=[Flavor.SALTY, Flavor.UMAMI],
            temperature=Temperature.HOT,
            complexity=Complexity.MEDIUM
        ),
        dessert=Dish(
            id=f"{menu_id}-dessert",
            name=f"{culture.value} Dessert",
            dish_type=DishType.DESSERT,
            category=DishCategory.PASTRY,
            price=12.0,
            ingredients=["test_ingredient_5"],
            styles=[CulinaryStyle.GOURMET],
            flavors=[Flavor.SWEET],
            temperature=Temperature.COLD,
            complexity=Complexity.MEDIUM
        ),
        beverage=Beverage(
            id=f"{menu_id}-beverage",
            name="Test Beverage",
            alcoholic=False,
            price=5.0,
            type="soft-drink"
        ),
        cultural_theme=culture
    )


def run_test() -> Dict:
    """Execute semantic retain test."""
    
    results = {
        "test_name": "Semantic Similarity in RETAIN",
        "timestamp": datetime.now().isoformat(),
        "test_cases": [],
        "summary": {}
    }
    
    case_base = CaseBase()
    retainer = CaseRetainer(case_base)
    
    initial_cases = len(case_base.cases)
    
    # Test 1: Italian menu (similar to existing Spanish cases)
    test_1_request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=40.0,
        price_max=60.0,
        season=Season.SUMMER,
        cultural_preference=CulturalTradition.ITALIAN
    )
    
    test_1_menu = create_test_menu(CulturalTradition.ITALIAN, "test-italian")
    
    test_1_feedback = FeedbackData(
        menu_id=test_1_menu.id,
        success=True,
        score=4.5,
        comments="Test Italian menu",
        would_recommend=True
    )
    
    decision_1 = retainer.evaluate_retention(test_1_request, test_1_menu, test_1_feedback)
    retained_1, message_1 = retainer.retain(test_1_request, test_1_menu, test_1_feedback)
    
    results["test_cases"].append({
        "test_id": "italian_vs_spanish",
        "description": "Italian menu vs existing Spanish cases (semantically similar)",
        "menu_culture": "ITALIAN",
        "decision": {
            "should_retain": decision_1.should_retain,
            "action": decision_1.action,
            "reason": decision_1.reason,
            "retained": retained_1
        }
    })
    
    # Test 2: Japanese menu (different from Mediterranean cultures)
    test_2_request = Request(
        event_type=EventType.CONGRESS,
        num_guests=150,
        price_min=30.0,
        price_max=50.0,
        season=Season.AUTUMN,
        cultural_preference=CulturalTradition.JAPANESE
    )
    
    test_2_menu = create_test_menu(CulturalTradition.JAPANESE, "test-japanese")
    
    test_2_feedback = FeedbackData(
        menu_id=test_2_menu.id,
        success=True,
        score=4.6,
        comments="Test Japanese menu",
        would_recommend=True
    )
    
    decision_2 = retainer.evaluate_retention(test_2_request, test_2_menu, test_2_feedback)
    retained_2, message_2 = retainer.retain(test_2_request, test_2_menu, test_2_feedback)
    
    results["test_cases"].append({
        "test_id": "japanese_vs_european",
        "description": "Japanese menu vs European cases (semantically different)",
        "menu_culture": "JAPANESE",
        "decision": {
            "should_retain": decision_2.should_retain,
            "action": decision_2.action,
            "reason": decision_2.reason,
            "retained": retained_2
        }
    })
    
    # Test 3: French menu (similar to Italian/Spanish)
    test_3_request = Request(
        event_type=EventType.WEDDING,
        num_guests=120,
        price_min=50.0,
        price_max=70.0,
        season=Season.SPRING,
        cultural_preference=CulturalTradition.FRENCH
    )
    
    test_3_menu = create_test_menu(CulturalTradition.FRENCH, "test-french")
    
    test_3_feedback = FeedbackData(
        menu_id=test_3_menu.id,
        success=True,
        score=4.8,
        comments="Test French menu",
        would_recommend=True
    )
    
    decision_3 = retainer.evaluate_retention(test_3_request, test_3_menu, test_3_feedback)
    retained_3, message_3 = retainer.retain(test_3_request, test_3_menu, test_3_feedback)
    
    results["test_cases"].append({
        "test_id": "french_vs_european",
        "description": "French menu vs European cases (semantically similar)",
        "menu_culture": "FRENCH",
        "decision": {
            "should_retain": decision_3.should_retain,
            "action": decision_3.action,
            "reason": decision_3.reason,
            "retained": retained_3
        }
    })
    
    # Summary statistics
    final_cases = len(case_base.cases)
    retained_count = sum(1 for tc in results["test_cases"] if tc["decision"]["retained"])
    
    results["summary"] = {
        "initial_cases": initial_cases,
        "final_cases": final_cases,
        "test_menus_submitted": len(results["test_cases"]),
        "menus_retained": retained_count,
        "retention_rate": retained_count / len(results["test_cases"]) if results["test_cases"] else 0.0,
        "semantic_similarity_used": retainer.similarity_calc.use_embeddings_for_culture
    }
    
    return results


def main():
    print("Starting Semantic RETAIN Test...")
    results = run_test()
    
    output_file = Path(__file__).parent.parent / "data" / "results" / "test_semantic_retain.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest completed. Results saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Test menus submitted: {results['summary']['test_menus_submitted']}")
    print(f"  Menus retained: {results['summary']['menus_retained']}")
    print(f"  Retention rate: {results['summary']['retention_rate']:.1%}")
    print(f"  Semantic similarity enabled: {results['summary']['semantic_similarity_used']}")


if __name__ == "__main__":
    main()
