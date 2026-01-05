"""
Test: Complete CBR Cycle Evaluation
=====================================

Demonstrates and evaluates the complete CBR cycle:
RETRIEVE -> ADAPT -> REVISE -> RETAIN

Metrics:
- Retrieval accuracy (similarity scores)
- Adaptation success rate
- Validation pass rate
- Retention decision quality
"""

import sys
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle, CulturalTradition,
    FeedbackData
)


def run_test() -> Dict:
    """Execute complete CBR cycle test."""
    
    results = {
        "test_name": "Complete CBR Cycle",
        "timestamp": datetime.now().isoformat(),
        "scenarios": [],
        "summary": {}
    }
    
    config = CBRConfig(verbose=False, enable_learning=True, max_proposals=3)
    cbr = ChefDigitalCBR(config)
    
    initial_cases = cbr.case_base.get_statistics()['total_cases']
    
    # Test scenarios
    scenarios = [
        {
            "id": "scenario_1",
            "description": "Italian cultural preference, summer wedding",
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=100,
                price_max=60.0,
                season=Season.SUMMER,
                cultural_preference=CulturalTradition.ITALIAN,
                wants_wine=True
            ),
            "expected_feedback": {"score": 4.7, "success": True}
        },
        {
            "id": "scenario_2",
            "description": "Chinese cultural preference, congress event",
            "request": Request(
                event_type=EventType.CONGRESS,
                num_guests=150,
                price_max=40.0,
                season=Season.AUTUMN,
                cultural_preference=CulturalTradition.CHINESE,
                wants_wine=False
            ),
            "expected_feedback": {"score": 4.5, "success": True}
        },
        {
            "id": "scenario_3",
            "description": "Spanish regional style, family event",
            "request": Request(
                event_type=EventType.FAMILIAR,
                num_guests=50,
                price_max=45.0,
                season=Season.SPRING,
                preferred_style=CulinaryStyle.REGIONAL,
                cultural_preference=CulturalTradition.SPANISH,
                wants_wine=True
            ),
            "expected_feedback": {"score": 4.8, "success": True}
        }
    ]
    
    for scenario in scenarios:
        scenario_result = {
            "scenario_id": scenario["id"],
            "description": scenario["description"],
            "phases": {}
        }
        
        request = scenario["request"]
        
        # Phase 1: RETRIEVE
        retrieval_results = cbr.retriever.retrieve(request, k=5)
        scenario_result["phases"]["retrieve"] = {
            "cases_found": len(retrieval_results),
            "top_similarity": retrieval_results[0].similarity if retrieval_results else 0.0,
            "avg_similarity": sum(r.similarity for r in retrieval_results) / len(retrieval_results) if retrieval_results else 0.0
        }
        
        # Phase 2: ADAPT
        adapted_menus = cbr.adapter.adapt(retrieval_results, request)
        scenario_result["phases"]["adapt"] = {
            "menus_adapted": len(adapted_menus),
            "cultural_adaptations": sum(1 for m in adapted_menus if m.adapted_menu.cultural_adaptations)
        }
        
        # Phase 3: REVISE (implicit in process_request)
        result = cbr.process_request(request)
        scenario_result["phases"]["revise"] = {
            "valid_proposals": len(result.proposed_menus),
            "validation_passed": len(result.proposed_menus) > 0
        }
        
        # Phase 4: RETAIN
        if result.proposed_menus:
            best_menu = result.proposed_menus[0]
            feedback = FeedbackData(
                menu_id=best_menu.menu.id,
                success=scenario["expected_feedback"]["success"],
                score=scenario["expected_feedback"]["score"],
                comments=f"Test feedback for {scenario['id']}",
                would_recommend=True
            )
            
            decision = cbr.retainer.evaluate_retention(request, best_menu.menu, feedback)
            retained, msg = cbr.retainer.retain(request, best_menu.menu, feedback)
            
            scenario_result["phases"]["retain"] = {
                "should_retain": decision.should_retain,
                "retention_action": decision.action,
                "retained": retained,
                "feedback_score": feedback.score
            }
        
        results["scenarios"].append(scenario_result)
    
    # Summary statistics
    final_cases = cbr.case_base.get_statistics()['total_cases']
    
    results["summary"] = {
        "initial_cases": initial_cases,
        "final_cases": final_cases,
        "cases_learned": final_cases - initial_cases,
        "scenarios_executed": len(scenarios),
        "avg_retrieval_similarity": sum(s["phases"]["retrieve"]["top_similarity"] for s in results["scenarios"]) / len(scenarios),
        "avg_valid_proposals": sum(s["phases"]["revise"]["valid_proposals"] for s in results["scenarios"]) / len(scenarios),
        "retention_rate": sum(1 for s in results["scenarios"] if s["phases"].get("retain", {}).get("retained", False)) / len(scenarios)
    }
    
    return results


def main():
    print("Starting Complete CBR Cycle Test...")
    results = run_test()
    
    output_file = Path(__file__).parent.parent / "data" / "test_complete_cbr_cycle.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest completed. Results saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Scenarios: {results['summary']['scenarios_executed']}")
    print(f"  Cases learned: {results['summary']['cases_learned']}")
    print(f"  Avg retrieval similarity: {results['summary']['avg_retrieval_similarity']:.3f}")
    print(f"  Avg valid proposals: {results['summary']['avg_valid_proposals']:.1f}")
    print(f"  Retention rate: {results['summary']['retention_rate']:.1%}")


if __name__ == "__main__":
    main()
