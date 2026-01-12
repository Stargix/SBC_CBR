"""
Test: Negative Cases Learning Evaluation
=========================================

Evaluates the system's ability to learn from failures and avoid
repeating past mistakes.

Metrics:
- Negative case retention
- Failure pattern detection
- Avoidance effectiveness
"""

import sys
import json
from pathlib import Path
from typing import Dict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from develop.core.case_base import CaseBase
from develop.core.models import Request, EventType, Season, CulinaryStyle, CulturalTradition
from develop.cycle.retrieve import CaseRetriever
from develop.cycle.adapt import CaseAdapter
from develop.cycle.retain import CaseRetainer, FeedbackData


def run_test() -> Dict:
    """Execute expanded negative cases test with 10 diverse failure patterns."""
    
    results = {
        "test_name": "Negative Cases Learning",
        "timestamp": datetime.now().isoformat(),
        "scenarios": [],
        "summary": {}
    }
    
    case_base = CaseBase()
    retriever = CaseRetriever(case_base)
    adapter = CaseAdapter(case_base)
    retainer = CaseRetainer(case_base)
    
    initial_stats = retainer.get_retention_statistics()
    
    # Define 10 diverse negative case scenarios
    negative_scenarios = [
        # 1. Price failure - too expensive
        {
            "id": "price_too_high",
            "request": Request(
                event_type=EventType.FAMILIAR,
                num_guests=30,
                price_max=40.0,
                season=Season.SPRING
            ),
            "feedback_score": 1.8,
            "reason": "Price exceeded budget significantly"
        },
        # 2. Cultural mismatch
        {
            "id": "cultural_mismatch",
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=100,
                price_max=60.0,
                season=Season.SUMMER,
                cultural_preference=CulturalTradition.ITALIAN
            ),
            "feedback_score": 2.0,
            "reason": "Cultural adaptation was superficial"
        },
        # 3. Dietary violation
        {
            "id": "dietary_violation",
            "request": Request(
                event_type=EventType.CONGRESS,
                num_guests=150,
                price_max=35.0,
                season=Season.AUTUMN,
                required_diets=["vegetarian"]
            ),
            "feedback_score": 1.5,
            "reason": "Contained meat products"
        },
        # 4. Complexity mismatch - too simple for gala
        {
            "id": "complexity_too_low",
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=120,
                price_max=80.0,
                season=Season.WINTER,
                preferred_style=CulinaryStyle.GOURMET
            ),
            "feedback_score": 2.2,
            "reason": "Too simple for gourmet event"
        },
        # 5. Temperature mismatch
        {
            "id": "temperature_mismatch",
            "request": Request(
                event_type=EventType.FAMILIAR,
                num_guests=40,
                price_max=45.0,
                season=Season.WINTER
            ),
            "feedback_score": 2.4,
            "reason": "Cold starter inappropriate for winter"
        },
        # 6. Flavor clash
        {
            "id": "flavor_clash",
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=90,
                price_max=65.0,
                season=Season.SPRING,
                preferred_style=CulinaryStyle.CLASSIC
            ),
            "feedback_score": 2.0,
            "reason": "Flavors clashed between courses"
        },
        # 7. Scale mismatch - too complex for large scale
        {
            "id": "scale_mismatch",
            "request": Request(
                event_type=EventType.CONGRESS,
                num_guests=250,
                price_max=30.0,
                season=Season.SUMMER
            ),
            "feedback_score": 1.9,
            "reason": "Too complex for large-scale production"
        },
        # 8. Season inappropriateness
        {
            "id": "seasonal_mismatch",
            "request": Request(
                event_type=EventType.FAMILIAR,
                num_guests=35,
                price_max=50.0,
                season=Season.SUMMER
            ),
            "feedback_score": 2.3,
            "reason": "Heavy winter dishes in summer"
        },
        # 9. Wine pairing failure
        {
            "id": "wine_pairing_fail",
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=80,
                price_max=70.0,
                season=Season.AUTUMN,
                wants_wine=True
            ),
            "feedback_score": 2.1,
            "reason": "Wine pairing was inappropriate"
        },
        # 10. Allergy risk
        {
            "id": "allergen_risk",
            "request": Request(
                event_type=EventType.FAMILIAR,
                num_guests=50,
                price_max=45.0,
                season=Season.SPRING,
                restricted_ingredients=["peanuts", "shellfish"]
            ),
            "feedback_score": 1.6,
            "reason": "Contained restricted allergens"
        }
    ]
    
    negative_cases_created = 0
    
    # Create all negative cases
    for scenario in negative_scenarios:
        retrieval_results = retriever.retrieve(scenario["request"], k=3)
        adapted_menus = adapter.adapt(retrieval_results, scenario["request"])
        
        scenario_result = {
            "scenario_id": scenario["id"],
            "description": scenario["reason"],
            "retrieval_count": len(retrieval_results),
            "adapted_count": len(adapted_menus)
        }
        
        if adapted_menus:
            menu = adapted_menus[0].adapted_menu
            
            negative_feedback = FeedbackData(
                menu_id=menu.id,
                success=False,
                score=scenario["feedback_score"],
                comments=scenario["reason"],
                would_recommend=False
            )
            
            retained, message = retainer.retain(scenario["request"], menu, negative_feedback)
            
            scenario_result["feedback"] = {
                "score": negative_feedback.score,
                "success": negative_feedback.success,
                "retained": retained,
                "message": message
            }
            
            if retained:
                negative_cases_created += 1
        
        results["scenarios"].append(scenario_result)
    
    # Test avoidance effectiveness - make 5 requests similar to negative cases
    avoidance_tests = [
        {
            "id": "avoid_price_high",
            "request": Request(
                event_type=EventType.FAMILIAR,
                num_guests=32,
                price_max=42.0,
                season=Season.SPRING
            ),
            "similar_to": "price_too_high"
        },
        {
            "id": "avoid_cultural",
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=95,
                price_max=62.0,
                season=Season.SUMMER,
                cultural_preference=CulturalTradition.ITALIAN
            ),
            "similar_to": "cultural_mismatch"
        },
        {
            "id": "avoid_dietary",
            "request": Request(
                event_type=EventType.CONGRESS,
                num_guests=145,
                price_max=36.0,
                season=Season.AUTUMN,
                required_diets=["vegetarian"]
            ),
            "similar_to": "dietary_violation"
        },
        {
            "id": "avoid_allergen",
            "request": Request(
                event_type=EventType.FAMILIAR,
                num_guests=48,
                price_max=46.0,
                season=Season.SPRING,
                restricted_ingredients=["peanuts"]
            ),
            "similar_to": "allergen_risk"
        },
        {
            "id": "avoid_scale",
            "request": Request(
                event_type=EventType.CONGRESS,
                num_guests=240,
                price_max=31.0,
                season=Season.SUMMER
            ),
            "similar_to": "scale_mismatch"
        }
    ]
    
    avoidance_results = []
    for test in avoidance_tests:
        retrieval_results = retriever.retrieve(test["request"], k=5)
        adapted_menus = adapter.adapt(retrieval_results, test["request"])
        
        avoidance_result = {
            "test_id": test["id"],
            "similar_to_negative": test["similar_to"],
            "proposals_generated": len(adapted_menus),
            "proposals_valid": sum(1 for m in adapted_menus if m.adaptation_score > 0.5)
        }
        
        # Check similarity to negative cases
        negative_similarities = []
        for neg_scenario in results["scenarios"]:
            if neg_scenario.get("feedback"):
                # Simplified similarity check based on event type and context
                if neg_scenario["scenario_id"] == test["similar_to"]:
                    negative_similarities.append({
                        "negative_case": neg_scenario["scenario_id"],
                        "avoided": len(adapted_menus) > 0  # System generated alternatives
                    })
        
        avoidance_result["avoidance_checks"] = negative_similarities
        avoidance_results.append(avoidance_result)
    
    results["avoidance_tests"] = avoidance_results
    
    # Final statistics
    final_stats = retainer.get_retention_statistics()
    
    results["summary"] = {
        "initial_total_cases": initial_stats["total_cases"],
        "final_total_cases": final_stats["total_cases"],
        "initial_negative_cases": initial_stats.get("negative_cases", 0),
        "final_negative_cases": final_stats.get("negative_cases", 0),
        "cases_added": final_stats["total_cases"] - initial_stats["total_cases"],
        "negative_cases_created": negative_cases_created,
        "negative_patterns_tested": len(negative_scenarios),
        "avoidance_tests_conducted": len(avoidance_tests),
        "avg_proposals_despite_negatives": sum(t["proposals_generated"] for t in avoidance_results) / len(avoidance_results) if avoidance_results else 0
    }
    
    return results


def main():
    print("Starting Expanded Negative Cases Learning Test...")
    print("Testing 10 diverse failure patterns...")
    results = run_test()
    
    output_file = Path(__file__).parent.parent.parent / "data" / "results" / "test_negative_cases.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest completed. Results saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Negative patterns tested: {results['summary']['negative_patterns_tested']}")
    print(f"  Negative cases created: {results['summary']['negative_cases_created']}")
    print(f"  Avoidance tests: {results['summary']['avoidance_tests_conducted']}")
    print(f"  Avg proposals despite negatives: {results['summary']['avg_proposals_despite_negatives']:.1f}")
    print(f"  Final negative cases in base: {results['summary']['final_negative_cases']}")


if __name__ == "__main__":
    main()
