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

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop.core.case_base import CaseBase
from develop.core.models import Request, EventType, Season, CulinaryStyle
from develop.cycle.retrieve import CaseRetriever
from develop.cycle.adapt import CaseAdapter
from develop.cycle.retain import CaseRetainer, FeedbackData


def run_test() -> Dict:
    """Execute negative cases test."""
    
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
    
    # Scenario 1: Create and retain a negative case
    request_1 = Request(
        event_type=EventType.WEDDING,
        num_guests=80,
        price_max=60.0,
        season=Season.SUMMER,
        preferred_style=CulinaryStyle.MODERN
    )
    
    retrieval_results = retriever.retrieve(request_1, k=3)
    adapted_menus = adapter.adapt(retrieval_results, request_1)
    
    scenario_1 = {
        "scenario_id": "negative_case_creation",
        "description": "Create negative case from low feedback",
        "retrieval_count": len(retrieval_results),
        "adapted_count": len(adapted_menus)
    }
    
    if adapted_menus:
        menu = adapted_menus[0].adapted_menu
        
        # Simulate negative feedback
        negative_feedback = FeedbackData(
            menu_id=menu.id,
            success=False,
            score=2.1,
            comments="Menu too modern for traditional wedding",
            would_recommend=False
        )
        
        retained, message = retainer.retain(request_1, menu, negative_feedback)
        
        scenario_1["feedback"] = {
            "score": negative_feedback.score,
            "success": negative_feedback.success,
            "retained": retained,
            "message": message
        }
    
    results["scenarios"].append(scenario_1)
    
    # Scenario 2: Check if system warns about similar negative case
    request_2 = Request(
        event_type=EventType.WEDDING,
        num_guests=85,
        price_max=65.0,
        season=Season.SUMMER,
        preferred_style=CulinaryStyle.MODERN
    )
    
    warnings = retriever.check_negative_cases(request_2, threshold=0.75)
    
    scenario_2 = {
        "scenario_id": "negative_case_warning",
        "description": "Check warnings for similar request",
        "warnings_found": len(warnings),
        "warning_details": [
            {
                "case_id": case.id,
                "similarity": float(similarity),
                "feedback_score": case.feedback_score
            }
            for case, similarity in warnings[:3]
        ]
    }
    
    results["scenarios"].append(scenario_2)
    
    # Scenario 3: Positive feedback case
    request_3 = Request(
        event_type=EventType.FAMILIAR,
        num_guests=40,
        price_max=45.0,
        season=Season.AUTUMN,
        preferred_style=CulinaryStyle.REGIONAL
    )
    
    retrieval_results_3 = retriever.retrieve(request_3, k=3)
    adapted_menus_3 = adapter.adapt(retrieval_results_3, request_3)
    
    scenario_3 = {
        "scenario_id": "positive_case_creation",
        "description": "Create positive case from high feedback"
    }
    
    if adapted_menus_3:
        menu_3 = adapted_menus_3[0].adapted_menu
        
        positive_feedback = FeedbackData(
            menu_id=menu_3.id,
            success=True,
            score=4.7,
            comments="Excellent regional menu",
            would_recommend=True
        )
        
        retained_3, message_3 = retainer.retain(request_3, menu_3, positive_feedback)
        
        scenario_3["feedback"] = {
            "score": positive_feedback.score,
            "success": positive_feedback.success,
            "retained": retained_3
        }
    
    results["scenarios"].append(scenario_3)
    
    # Final statistics
    final_stats = retainer.get_retention_statistics()
    
    results["summary"] = {
        "initial_total_cases": initial_stats["total_cases"],
        "final_total_cases": final_stats["total_cases"],
        "initial_negative_cases": initial_stats.get("negative_cases", 0),
        "final_negative_cases": final_stats.get("negative_cases", 0),
        "cases_added": final_stats["total_cases"] - initial_stats["total_cases"],
        "negative_cases_added": final_stats.get("negative_cases", 0) - initial_stats.get("negative_cases", 0),
        "warning_system_functional": len(warnings) > 0
    }
    
    return results


def main():
    print("Starting Negative Cases Learning Test...")
    results = run_test()
    
    output_file = Path(__file__).parent.parent / "data" / "test_negative_cases.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest completed. Results saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Cases added: {results['summary']['cases_added']}")
    print(f"  Negative cases added: {results['summary']['negative_cases_added']}")
    print(f"  Warning system functional: {results['summary']['warning_system_functional']}")
    print(f"  Final negative cases: {results['summary']['final_negative_cases']}")


if __name__ == "__main__":
    main()
