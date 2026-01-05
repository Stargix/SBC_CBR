"""
Test: Semantic Similarity in RETRIEVE Phase
============================================

Evaluates how semantic cultural similarity affects case retrieval
and ranking using embedding-based similarity.

Metrics:
- Retrieval ranking quality
- Cultural similarity impact
- Embedding effectiveness
"""

import sys
import json
from pathlib import Path
from typing import Dict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop.core.case_base import CaseBase
from develop.core.models import Request, EventType, Season, CulturalTradition
from develop.cycle.retrieve import CaseRetriever


def run_test() -> Dict:
    """Execute semantic retrieve test."""
    
    results = {
        "test_name": "Semantic Similarity in RETRIEVE",
        "timestamp": datetime.now().isoformat(),
        "cultural_preferences": [],
        "summary": {}
    }
    
    case_base = CaseBase()
    retriever = CaseRetriever(case_base)
    
    # Count existing cases by culture
    culture_distribution = {}
    for case in case_base.cases:
        if case.menu.cultural_theme:
            culture_name = case.menu.cultural_theme.value
            culture_distribution[culture_name] = culture_distribution.get(culture_name, 0) + 1
    
    results["case_base_distribution"] = culture_distribution
    
    # Test different cultural preferences
    cultural_tests = [
        CulturalTradition.ITALIAN,
        CulturalTradition.SPANISH,
        CulturalTradition.FRENCH,
        CulturalTradition.JAPANESE,
        CulturalTradition.MEXICAN
    ]
    
    for culture in cultural_tests:
        request = Request(
            event_type=EventType.WEDDING,
            num_guests=100,
            price_max=60.0,
            season=Season.SUMMER,
            cultural_preference=culture
        )
        
        retrieval_results = retriever.retrieve(request, k=5)
        
        culture_result = {
            "target_culture": culture.value,
            "cases_retrieved": len(retrieval_results),
            "retrieved_cases": []
        }
        
        for i, result in enumerate(retrieval_results):
            case_culture = result.case.menu.cultural_theme.value if result.case.menu.cultural_theme else "NONE"
            
            culture_result["retrieved_cases"].append({
                "rank": i + 1,
                "case_id": result.case.id,
                "similarity_score": result.similarity,
                "case_culture": case_culture,
                "cultural_match": case_culture == culture.value
            })
        
        # Calculate metrics
        if retrieval_results:
            culture_result["metrics"] = {
                "top_similarity": retrieval_results[0].similarity,
                "avg_similarity": sum(r.similarity for r in retrieval_results) / len(retrieval_results),
                "exact_cultural_matches": sum(1 for r in culture_result["retrieved_cases"] if r["cultural_match"]),
                "top_result_is_match": culture_result["retrieved_cases"][0]["cultural_match"] if culture_result["retrieved_cases"] else False
            }
        
        results["cultural_preferences"].append(culture_result)
    
    # Summary statistics
    total_retrievals = sum(cp["cases_retrieved"] for cp in results["cultural_preferences"])
    total_exact_matches = sum(cp["metrics"]["exact_cultural_matches"] for cp in results["cultural_preferences"])
    top_match_count = sum(1 for cp in results["cultural_preferences"] if cp["metrics"]["top_result_is_match"])
    
    results["summary"] = {
        "cultures_tested": len(cultural_tests),
        "total_cases_retrieved": total_retrievals,
        "exact_cultural_matches": total_exact_matches,
        "exact_match_rate": total_exact_matches / total_retrievals if total_retrievals > 0 else 0.0,
        "top_result_match_rate": top_match_count / len(cultural_tests) if cultural_tests else 0.0,
        "avg_retrieval_similarity": sum(cp["metrics"]["top_similarity"] for cp in results["cultural_preferences"]) / len(results["cultural_preferences"])
    }
    
    return results


def main():
    print("Starting Semantic RETRIEVE Test...")
    results = run_test()
    
    output_file = Path(__file__).parent.parent / "data" / "test_semantic_retrieve.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest completed. Results saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Cultures tested: {results['summary']['cultures_tested']}")
    print(f"  Exact match rate: {results['summary']['exact_match_rate']:.1%}")
    print(f"  Top result match rate: {results['summary']['top_result_match_rate']:.1%}")
    print(f"  Avg retrieval similarity: {results['summary']['avg_retrieval_similarity']:.3f}")


if __name__ == "__main__":
    main()
