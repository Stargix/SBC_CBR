"""
Test: Adaptive Weight Learning Evaluation
==========================================

Compares static weights vs adaptive weight learning to demonstrate
the system's ability to optimize retrieval based on user feedback.

Metrics:
- Weight evolution over time
- Retrieval accuracy improvement
- Adaptation to user preferences
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle,
    FeedbackData
)


def run_test() -> Dict:
    """Execute adaptive weights test."""
    
    results = {
        "test_name": "Adaptive Weight Learning",
        "timestamp": datetime.now().isoformat(),
        "systems": {
            "static": {"name": "Static Weights", "results": []},
            "adaptive": {"name": "Adaptive Weights", "results": []}
        },
        "summary": {}
    }
    
    test_cases = [
        {
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=100,
                price_max=55.0,
                season=Season.SUMMER,
                required_diets=["vegetarian"],
                wants_wine=True
            ),
            "feedback": {"score": 4.5, "success": True}
        },
        {
            "request": Request(
                event_type=EventType.CONGRESS,
                num_guests=200,
                price_max=30.0,
                season=Season.AUTUMN,
                wants_wine=False
            ),
            "feedback": {"score": 4.0, "success": True}
        },
        {
            "request": Request(
                event_type=EventType.FAMILIAR,
                num_guests=30,
                price_max=45.0,
                season=Season.WINTER,
                wants_wine=True
            ),
            "feedback": {"score": 4.8, "success": True}
        },
        {
            "request": Request(
                event_type=EventType.WEDDING,
                num_guests=150,
                price_max=75.0,
                season=Season.SPRING,
                preferred_style=CulinaryStyle.GOURMET,
                wants_wine=True
            ),
            "feedback": {"score": 5.0, "success": True}
        },
        {
            "request": Request(
                event_type=EventType.CORPORATE,
                num_guests=80,
                price_max=35.0,
                season=Season.SUMMER,
                wants_wine=False
            ),
            "feedback": {"score": 3.8, "success": True}
        }
    ]
    
    # Test static system
    static_cbr = ChefDigitalCBR(CBRConfig(enable_learning=False, verbose=False))
    
    for i, test_case in enumerate(test_cases):
        result = static_cbr.process_request(test_case["request"])
        
        results["systems"]["static"]["results"].append({
            "iteration": i + 1,
            "proposals_count": len(result.proposed_menus),
            "top_similarity": result.proposed_menus[0].similarity_score if result.proposed_menus else 0.0,
            "avg_similarity": (
                sum(m.similarity_score for m in result.proposed_menus) / len(result.proposed_menus)
                if result.proposed_menus else 0.0
            )
        })
    
    # Test adaptive system
    adaptive_cbr = ChefDigitalCBR(CBRConfig(enable_learning=True, verbose=False))
    initial_weights = asdict(adaptive_cbr.retriever.similarity_calc.weights)
    
    for i, test_case in enumerate(test_cases):
        result = adaptive_cbr.process_request(test_case["request"])
        
        current_weights = asdict(adaptive_cbr.retriever.similarity_calc.weights)
        
        iteration_result = {
            "iteration": i + 1,
            "proposals_count": len(result.proposed_menus),
            "top_similarity": result.proposed_menus[0].similarity_score if result.proposed_menus else 0.0,
            "avg_similarity": (
                sum(m.similarity_score for m in result.proposed_menus) / len(result.proposed_menus)
                if result.proposed_menus else 0.0
            ),
            "weights": current_weights
        }
        
        # Apply feedback
        if result.proposed_menus:
            feedback = FeedbackData(
                menu_id=result.proposed_menus[0].menu.id,
                success=test_case["feedback"]["success"],
                score=test_case["feedback"]["score"],
                comments="Test feedback",
                would_recommend=test_case["feedback"]["score"] >= 4.0
            )
            adaptive_cbr.learn_from_feedback(feedback, test_case["request"])
        
        results["systems"]["adaptive"]["results"].append(iteration_result)
    
    final_weights = asdict(adaptive_cbr.retriever.similarity_calc.weights)
    
    # Calculate weight changes
    weight_changes = {
        key: {
            "initial": initial_weights[key],
            "final": final_weights[key],
            "change": final_weights[key] - initial_weights[key],
            "change_pct": ((final_weights[key] - initial_weights[key]) / initial_weights[key] * 100)
        }
        for key in initial_weights.keys()
    }
    
    # Summary statistics
    static_avg_similarity = sum(r["top_similarity"] for r in results["systems"]["static"]["results"]) / len(test_cases)
    adaptive_avg_similarity = sum(r["top_similarity"] for r in results["systems"]["adaptive"]["results"]) / len(test_cases)
    
    results["summary"] = {
        "test_cases": len(test_cases),
        "static_avg_similarity": static_avg_similarity,
        "adaptive_avg_similarity": adaptive_avg_similarity,
        "improvement": adaptive_avg_similarity - static_avg_similarity,
        "improvement_pct": ((adaptive_avg_similarity - static_avg_similarity) / static_avg_similarity * 100),
        "weight_changes": weight_changes,
        "most_changed_weights": sorted(
            [{"name": k, **v} for k, v in weight_changes.items()],
            key=lambda x: abs(x["change"]),
            reverse=True
        )[:3]
    }
    
    return results


def main():
    print("Starting Adaptive Weight Learning Test...")
    results = run_test()
    
    output_file = Path(__file__).parent.parent / "data" / "test_adaptive_weights.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest completed. Results saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Test cases: {results['summary']['test_cases']}")
    print(f"  Static avg similarity: {results['summary']['static_avg_similarity']:.3f}")
    print(f"  Adaptive avg similarity: {results['summary']['adaptive_avg_similarity']:.3f}")
    print(f"  Improvement: {results['summary']['improvement']:+.3f} ({results['summary']['improvement_pct']:+.1f}%)")
    print(f"\n  Top weight changes:")
    for w in results['summary']['most_changed_weights']:
        print(f"    {w['name']}: {w['change']:+.3f} ({w['change_pct']:+.1f}%)")


if __name__ == "__main__":
    main()
