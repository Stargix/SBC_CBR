"""
Master Test Runner
==================

Executes all formal tests and generates a comprehensive report.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def run_test(test_name: str) -> Dict:
    """Execute a single test and return results."""
    
    test_path = Path(__file__).parent / "tests" / f"{test_name}.py"
    
    if not test_path.exists():
        return {"error": f"Test file not found: {test_path}"}
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "error": "Test exceeded 5 minute timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def load_test_results(test_name: str) -> Dict:
    """Load test results from JSON file."""
    
    data_file = Path(__file__).parent / "data" / f"{test_name}.json"
    
    if not data_file.exists():
        return {}
    
    try:
        with open(data_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to load results: {str(e)}"}


def main():
    """Run all tests and generate master report."""
    
    tests = [
        "test_complete_cbr_cycle",
        "test_user_simulation",
        "test_adaptive_weights",
        "test_semantic_cultural_adaptation",
        "test_semantic_retrieve",
        "test_negative_cases",
        "test_semantic_retain",
        "test_adaptive_learning"
    ]
    
    master_report = {
        "execution_timestamp": datetime.now().isoformat(),
        "tests_executed": len(tests),
        "results": {}
    }
    
    print("="*80)
    print("EXECUTING FORMAL TEST SUITE")
    print("="*80)
    
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] Running: {test}")
        print("-" * 80)
        
        execution = run_test(test)
        test_data = load_test_results(test)
        
        master_report["results"][test] = {
            "execution": execution,
            "data": test_data
        }
        
        if execution.get("status") == "success":
            print(f"Status: SUCCESS")
        else:
            print(f"Status: {execution.get('status', 'UNKNOWN').upper()}")
            if execution.get("stderr"):
                print(f"Error: {execution['stderr'][:200]}")
    
    # Save master report
    output_file = Path(__file__).parent / "data" / "master_test_report.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(master_report, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUITE SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in master_report["results"].values() if r["execution"].get("status") == "success")
    print(f"\nTests executed: {len(tests)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(tests) - successful}")
    print(f"\nMaster report saved to: {output_file}")
    
    # Print key metrics from each test
    print("\n" + "="*80)
    print("KEY METRICS")
    print("="*80)
    
    for test_name, result in master_report["results"].items():
        if result["execution"].get("status") == "success" and result.get("data"):
            print(f"\n{test_name}:")
            data = result["data"]
            
            if "summary" in data:
                summary = data["summary"]
                for key, value in list(summary.items())[:5]:
                    if isinstance(value, (int, float)):
                        if isinstance(value, float):
                            print(f"  {key}: {value:.3f}")
                        else:
                            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
