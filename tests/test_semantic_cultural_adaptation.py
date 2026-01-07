"""
Test: Semantic Cultural Adaptation Evaluation
==============================================

Evaluates the system's ability to adapt menus using semantic similarity
between cultural traditions (via embeddings).

Metrics:
- Cultural adaptation accuracy
- Ingredient substitution quality
- Semantic similarity scores
- Adaptation coverage
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop.core.case_base import CaseBase
from develop.core.models import Request, EventType, Season, CulturalTradition
from develop.cycle.retrieve import CaseRetriever
from develop.cycle.adapt import CaseAdapter


def run_test() -> Dict:
    """Execute semantic cultural adaptation test."""
    
    results = {
        "test_name": "Semantic Cultural Adaptation",
        "timestamp": datetime.now().isoformat(),
        "test_cases": [],
        "summary": {}
    }
    
    case_base = CaseBase()
    retriever = CaseRetriever(case_base)
    adapter = CaseAdapter(case_base)
    
    # Test cases: different cultural preferences
    test_scenarios = [
        {
            "id": "italian_adaptation",
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=100,
                price_max=60.0,
                season=Season.SUMMER,
                cultural_preference=CulturalTradition.ITALIAN
            ),
            "target_culture": "ITALIAN"
        },
        {
            "id": "spanish_adaptation",
            "request": Request(
                event_type=EventType.FAMILIAR,
                num_guests=50,
                price_max=50.0,
                season=Season.SPRING,
                cultural_preference=CulturalTradition.SPANISH
            ),
            "target_culture": "SPANISH"
        },
        {
            "id": "japanese_adaptation",
            "request": Request(
                event_type=EventType.CONGRESS,
                num_guests=150,
                price_max=40.0,
                season=Season.AUTUMN,
                cultural_preference=CulturalTradition.JAPANESE
            ),
            "target_culture": "JAPANESE"
        },
        {
            "id": "french_adaptation",
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=120,
                price_max=70.0,
                season=Season.WINTER,
                cultural_preference=CulturalTradition.FRENCH
            ),
            "target_culture": "FRENCH"
        }
    ]
    
    for scenario in test_scenarios:
        request = scenario["request"]
        
        # Retrieve cases
        retrieval_results = retriever.retrieve(request, k=5)
        
        if not retrieval_results:
            continue
        
        # Adapt cases
        adapted_menus = adapter.adapt(retrieval_results, request)
        
        test_result = {
            "scenario_id": scenario["id"],
            "target_culture": scenario["target_culture"],
            "retrieval": {
                "cases_found": len(retrieval_results),
                "top_similarity": float(retrieval_results[0].similarity),
                "avg_similarity": float(sum(r.similarity for r in retrieval_results) / len(retrieval_results))
            },
            "adaptation": {
                "menus_generated": len(adapted_menus),
                "cultural_adaptations_applied": 0,
                "ingredient_substitutions": 0,
                "dish_replacements": 0
            }
        }
        
        # Analyze adaptations
        for adapted in adapted_menus:
            if adapted.adapted_menu.cultural_adaptations:
                test_result["adaptation"]["cultural_adaptations_applied"] += 1
                
                for adaptation in adapted.adapted_menu.cultural_adaptations:
                    if adaptation.get("type") == "ingredient":
                        test_result["adaptation"]["ingredient_substitutions"] += 1
                    elif adaptation.get("adaptation_type") == "dish_replacement":
                        test_result["adaptation"]["dish_replacements"] += 1
        
        # Cultural score for best adapted menu
        if adapted_menus:
            best_menu = adapted_menus[0].adapted_menu
            test_result["adaptation"]["cultural_theme"] = (
                best_menu.cultural_theme.value if best_menu.cultural_theme else None
            )
            test_result["adaptation"]["total_price"] = float(best_menu.total_price)
        
        results["test_cases"].append(test_result)
    
    # Summary statistics
    total_adaptations = sum(tc["adaptation"]["cultural_adaptations_applied"] for tc in results["test_cases"])
    total_substitutions = sum(tc["adaptation"]["ingredient_substitutions"] for tc in results["test_cases"])
    total_replacements = sum(tc["adaptation"]["dish_replacements"] for tc in results["test_cases"])
    
    results["summary"] = {
        "scenarios_tested": len(test_scenarios),
        "avg_retrieval_similarity": float(sum(tc["retrieval"]["top_similarity"] for tc in results["test_cases"]) / len(results["test_cases"])),
        "total_cultural_adaptations": total_adaptations,
        "total_ingredient_substitutions": total_substitutions,
        "total_dish_replacements": total_replacements,
        "adaptation_rate": float(total_adaptations / len(results["test_cases"]) if results["test_cases"] else 0.0)
    }
    
    return results


def main():
    print("Starting Semantic Cultural Adaptation Test...")
    results = run_test()
    
    output_file = Path(__file__).parent.parent / "data" / "test_semantic_cultural_adaptation.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest completed. Results saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Scenarios tested: {results['summary']['scenarios_tested']}")
    print(f"  Avg retrieval similarity: {results['summary']['avg_retrieval_similarity']:.3f}")
    print(f"  Total adaptations: {results['summary']['total_cultural_adaptations']}")
    print(f"  Ingredient substitutions: {results['summary']['total_ingredient_substitutions']}")
    print(f"  Dish replacements: {results['summary']['total_dish_replacements']}")


if __name__ == "__main__":
    main()
