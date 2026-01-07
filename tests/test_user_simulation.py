"""
Test: Multi-User Simulation with Progressive Learning
======================================================

Simulates multiple synthetic users making requests and providing feedback
to evaluate the system's learning capabilities over time.

Metrics:
- System accuracy evolution
- User satisfaction trends
- Case base growth
- Learning efficiency
"""

import sys
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle, CulturalTradition,
    FeedbackData
)


class SyntheticUser:
    """Synthetic user with consistent preferences."""
    
    def __init__(self, user_id: str, base_case: dict):
        self.user_id = user_id
        self.base_case = base_case
        self.strictness = random.uniform(0.3, 0.9)
    
    def generate_request(self) -> Request:
        """Generate request based on user preferences."""
        budget_base = (self.base_case["price_min"] + self.base_case["price_max"]) / 2
        budget_variation = budget_base * random.uniform(-0.05, 0.05)
        
        guests_base = self.base_case["num_guests"]
        guests_variation = int(guests_base * random.uniform(-0.1, 0.1))
        
        return Request(
            event_type=EventType(self.base_case["event"]),
            season=Season(self.base_case["season"]),
            num_guests=max(5, guests_base + guests_variation),
            price_max=budget_base + budget_variation,
            wants_wine=self.base_case.get("wants_wine", True),
            preferred_style=CulinaryStyle(self.base_case["style"]) if "style" in self.base_case else None
        )
    
    def evaluate_proposal(self, menu, request) -> FeedbackData:
        """Generate feedback based on menu quality."""
        base_score = 4.0
        
        # Adjust score based on price match
        price_diff = abs(menu.total_price - request.price_max) / request.price_max
        if price_diff < 0.05:
            base_score += 0.5
        elif price_diff > 0.15:
            base_score -= 1.0
        
        # Random variation based on strictness
        score = base_score + random.uniform(-self.strictness, 1.0 - self.strictness)
        score = max(1.0, min(5.0, score))
        
        return FeedbackData(
            menu_id=menu.id,
            success=score >= 3.5,
            score=score,
            comments=f"User {self.user_id} feedback",
            would_recommend=score >= 4.0
        )


def run_test(num_users: int = 5, iterations: int = 10) -> Dict:
    """Execute multi-user simulation."""
    
    results = {
        "test_name": "Multi-User Simulation",
        "timestamp": datetime.now().isoformat(),
        "parameters": {
            "num_users": num_users,
            "iterations": iterations
        },
        "iterations": [],
        "summary": {}
    }
    
    config = CBRConfig(verbose=False, enable_learning=True, max_proposals=3)
    cbr = ChefDigitalCBR(config)
    
    # Load initial cases to create synthetic users
    initial_cases = cbr.case_base.get_all_cases()[:num_users]
    users = [
        SyntheticUser(f"user_{i+1}", {
            "event": case.request.event_type.value,
            "season": case.request.season.value,
            "num_guests": case.request.num_guests,
            "price_min": case.request.price_min,
            "price_max": case.request.price_max,
            "wants_wine": case.request.wants_wine,
            "style": case.menu.dominant_style.value if case.menu.dominant_style else "classical"
        })
        for i, case in enumerate(initial_cases)
    ]
    
    initial_case_count = len(cbr.case_base.get_all_cases())
    
    for iteration in range(iterations):
        iteration_result = {
            "iteration": iteration + 1,
            "requests_processed": 0,
            "successful_proposals": 0,
            "total_feedback_score": 0.0,
            "cases_retained": 0
        }
        
        for user in users:
            request = user.generate_request()
            result = cbr.process_request(request)
            
            iteration_result["requests_processed"] += 1
            
            if result.proposed_menus:
                iteration_result["successful_proposals"] += 1
                best_menu = result.proposed_menus[0]
                
                feedback = user.evaluate_proposal(best_menu.menu, request)
                iteration_result["total_feedback_score"] += feedback.score
                
                retained, _ = cbr.retainer.retain(request, best_menu.menu, feedback)
                if retained:
                    iteration_result["cases_retained"] += 1
        
        iteration_result["avg_feedback_score"] = (
            iteration_result["total_feedback_score"] / iteration_result["requests_processed"]
            if iteration_result["requests_processed"] > 0 else 0.0
        )
        iteration_result["success_rate"] = (
            iteration_result["successful_proposals"] / iteration_result["requests_processed"]
            if iteration_result["requests_processed"] > 0 else 0.0
        )
        iteration_result["current_case_count"] = len(cbr.case_base.get_all_cases())
        
        results["iterations"].append(iteration_result)
    
    # Calculate summary statistics
    final_case_count = len(cbr.case_base.get_all_cases())
    
    results["summary"] = {
        "initial_cases": initial_case_count,
        "final_cases": final_case_count,
        "total_cases_learned": final_case_count - initial_case_count,
        "total_requests": num_users * iterations,
        "avg_final_feedback": sum(it["avg_feedback_score"] for it in results["iterations"][-3:]) / 3,
        "avg_initial_feedback": sum(it["avg_feedback_score"] for it in results["iterations"][:3]) / 3,
        "improvement": 0.0,
        "avg_success_rate": sum(it["success_rate"] for it in results["iterations"]) / iterations
    }
    
    results["summary"]["improvement"] = (
        results["summary"]["avg_final_feedback"] - results["summary"]["avg_initial_feedback"]
    )
    
    return results


def main():
    print("Starting Multi-User Simulation Test...")
    results = run_test(num_users=5, iterations=15)
    
    output_file = Path(__file__).parent.parent / "data" / "test_user_simulation.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest completed. Results saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Total requests: {results['summary']['total_requests']}")
    print(f"  Cases learned: {results['summary']['total_cases_learned']}")
    print(f"  Initial avg feedback: {results['summary']['avg_initial_feedback']:.3f}")
    print(f"  Final avg feedback: {results['summary']['avg_final_feedback']:.3f}")
    print(f"  Improvement: {results['summary']['improvement']:+.3f}")
    print(f"  Success rate: {results['summary']['avg_success_rate']:.1%}")


if __name__ == "__main__":
    main()
