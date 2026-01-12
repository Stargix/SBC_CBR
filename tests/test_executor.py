"""
Test Executor Module
====================

Ejecuta todos los tests formales del sistema CBR.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List


def run_test(test_name: str, cases_dir: Path) -> Dict:
    """Ejecuta un test individual y retorna resultados."""
    
    test_path = cases_dir / f"{test_name}.py"
    
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


def load_test_results(test_name: str, results_dir: Path) -> Dict:
    """Carga los resultados de un test desde JSON."""
    
    data_file = results_dir / f"{test_name}.json"
    
    if not data_file.exists():
        return {}
    
    try:
        with open(data_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to load results: {str(e)}"}


def execute_all_tests(verbose: bool = True) -> Dict:
    """
    Ejecuta todos los tests formales y retorna reporte maestro.
    
    Args:
        verbose: Si True, imprime progreso por consola
        
    Returns:
        Dict con resultados de todos los tests
    """
    from datetime import datetime
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    cases_dir = Path(__file__).parent / "cases"
    results_dir = base_dir / "data" / "results"
    
    # Crear directorio si no existe
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Lista de tests
    tests = [
        "test_complete_cbr_cycle",
        "test_user_simulation",
        "test_adaptive_weights",
        "test_semantic_cultural_adaptation",
        "test_semantic_retrieve",
        "test_negative_cases",
        "test_dietary_restrictions",
        "test_semantic_retain",
        "test_adaptive_learning",
        "test_adaptation_strategies"
    ]
    
    master_report = {
        "execution_timestamp": datetime.now().isoformat(),
        "tests_executed": len(tests),
        "results": {}
    }
    
    if verbose:
        print("="*80)
        print("EXECUTING FORMAL TEST SUITE")
        print("="*80)
    
    for i, test in enumerate(tests, 1):
        if verbose:
            print(f"\n[{i}/{len(tests)}] Running: {test}")
            print("-" * 80)
        
        execution = run_test(test, cases_dir)
        test_data = load_test_results(test, results_dir)
        
        master_report["results"][test] = {
            "execution": execution,
            "data": test_data
        }
        
        if verbose:
            if execution.get("status") == "success":
                print(f"Status: SUCCESS")
            else:
                print(f"Status: {execution.get('status', 'UNKNOWN').upper()}")
                if execution.get("stderr"):
                    print(f"Error: {execution['stderr'][:200]}")
    
    # Guardar master report
    master_file = results_dir / "master_test_report.json"
    with open(master_file, 'w') as f:
        json.dump(master_report, f, indent=2)
    
    if verbose:
        print(f"\nMaster report saved to: {master_file}")
    
    return master_report


def print_test_summary(master_report: Dict):
    """Imprime resumen de los tests ejecutados."""
    
    print("\n" + "="*80)
    print("TEST SUITE SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in master_report['results'].values() 
                    if r['execution']['status'] == 'success')
    failed = sum(1 for r in master_report['results'].values() 
                if r['execution']['status'] != 'success')
    
    print(f"\nTests executed: {master_report['tests_executed']}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    # Print key metrics from each test
    print("\n" + "="*80)
    print("KEY METRICS")
    print("="*80)
    
    for test_key, result in master_report['results'].items():
        if result['execution']['status'] == 'success' and result.get('data', {}).get('summary'):
            print(f"\n{test_key}:")
            summary = result['data']['summary']
            for key, value in list(summary.items())[:6]:  # Limitar a 6 métricas principales
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    formatted_key = key.replace('_', ' ')
                    if isinstance(value, float):
                        print(f"  {formatted_key}: {value:.3f}")
                    else:
                        print(f"  {formatted_key}: {value}")
    
    print("="*80)


if __name__ == "__main__":
    master_report = execute_all_tests(verbose=True)
    print_test_summary(master_report)
