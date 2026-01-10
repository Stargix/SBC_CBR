"""
Silent Test Runner - Executes all tests with minimal console output
====================================================================

Runs all formal tests suppressing verbose output, showing only final summaries.
"""

import sys
import subprocess
from pathlib import Path
import json


def run_test_silent(test_name: str) -> dict:
    """Execute a test with suppressed output."""
    
    test_path = Path(__file__).parent / "tests" / f"{test_name}.py"
    
    try:
        # Run with output suppression
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Load results from JSON
        data_file = Path(__file__).parent / "data" / f"{test_name}.json"
        
        if data_file.exists():
            with open(data_file, 'r') as f:
                test_data = json.load(f)
            
            return {
                "name": test_name,
                "status": "success" if result.returncode == 0 else "failed",
                "summary": test_data.get("summary", {})
            }
        else:
            return {
                "name": test_name,
                "status": "no_output",
                "summary": {}
            }
            
    except subprocess.TimeoutExpired:
        return {
            "name": test_name,
            "status": "timeout",
            "summary": {}
        }
    except Exception as e:
        return {
            "name": test_name,
            "status": "error",
            "error": str(e),
            "summary": {}
        }


def main():
    """Run all tests silently and show clean summary."""
    
    tests = [
        "test_complete_cbr_cycle",
        "test_user_simulation",
        "test_adaptive_weights",
        "test_semantic_cultural_adaptation",
        "test_semantic_retrieve",
        "test_negative_cases",
        "test_semantic_retain"
    ]
    
    print("="*80)
    print("RUNNING FORMAL TESTS (Silent Mode)")
    print("="*80)
    
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] {test}...", end=" ", flush=True)
        
        result = run_test_silent(test)
        results.append(result)
        
        print(f"{result['status'].upper()}")
    
    # Print summary table
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r["status"] == "success")
    
    print(f"\nTotal: {len(tests)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(tests) - successful}")
    
    print("\n" + "-"*80)
    print(f"{'Test Name':<45} {'Status':<15} {'Key Metric'}")
    print("-"*80)
    
    for result in results:
        name = result["name"].replace("test_", "")
        status = result["status"]
        
        # Extract one key metric
        summary = result.get("summary", {})
        key_metric = ""
        
        if "retention_rate" in summary:
            key_metric = f"Retention: {summary['retention_rate']:.1%}"
        elif "avg_retrieval_similarity" in summary:
            key_metric = f"Similarity: {summary['avg_retrieval_similarity']:.3f}"
        elif "improvement" in summary:
            key_metric = f"Improvement: {summary['improvement']:+.3f}"
        elif "scenarios_executed" in summary:
            key_metric = f"Scenarios: {summary['scenarios_executed']}"
        elif "total_requests" in summary:
            key_metric = f"Requests: {summary['total_requests']}"
        
        print(f"{name:<45} {status:<15} {key_metric}")
    
    print("-"*80)
    print(f"\nAll results saved to: data/test_*.json")
    print("Generate formal report: python generate_formal_report.py")


if __name__ == "__main__":
    main()
