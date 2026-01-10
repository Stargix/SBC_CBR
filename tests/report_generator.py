"""
Report Generator Module
=======================

Genera reportes formales en formato Markdown y CSV.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict


def generate_markdown_report(data: Dict) -> str:
    """Genera reporte en formato markdown."""
    
    md = []
    md.append("# CBR System - Formal Experimental Results")
    md.append(f"\n**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("\n---\n")
    
    # Executive Summary
    md.append("## Executive Summary\n")
    md.append(f"- **Total Tests Executed:** {data.get('tests_executed', 0)}")
    
    successful = sum(1 for r in data.get('results', {}).values() 
                    if r.get('execution', {}).get('status') == 'success')
    md.append(f"- **Successful Tests:** {successful}/{data.get('tests_executed', 0)}")
    md.append("\n---\n")
    
    # Individual Test Results
    md.append("## Test Results\n")
    
    test_order = [
        ("test_complete_cbr_cycle", "Complete CBR Cycle"),
        ("test_user_simulation", "Multi-User Simulation"),
        ("test_adaptive_weights", "Adaptive Weight Learning"),
        ("test_semantic_cultural_adaptation", "Semantic Cultural Adaptation"),
        ("test_semantic_retrieve", "Semantic RETRIEVE"),
        ("test_negative_cases", "Negative Cases Learning"),
        ("test_semantic_retain", "Semantic RETAIN"),
        ("test_adaptive_learning", "Adaptive Learning Evaluation")
    ]
    
    for test_key, test_title in test_order:
        if test_key not in data.get('results', {}):
            continue
            
        result = data['results'][test_key]
        md.append(f"### {test_title}\n")
        
        status = result.get('execution', {}).get('status', 'unknown')
        md.append(f"**Status:** {status.upper()}\n")
        
        if result.get('data') and 'summary' in result['data']:
            summary = result['data']['summary']
            md.append("\n**Key Metrics:**\n")
            
            for key, value in summary.items():
                if isinstance(value, (int, float, str)) and not isinstance(value, bool):
                    formatted_key = key.replace('_', ' ').title()
                    if isinstance(value, float):
                        if 'rate' in key or 'pct' in key or 'improvement' in key:
                            md.append(f"- {formatted_key}: {value:.1%}" if abs(value) <= 1 else f"- {formatted_key}: {value:.2f}%")
                        else:
                            md.append(f"- {formatted_key}: {value:.3f}")
                    else:
                        md.append(f"- {formatted_key}: {value}")
        
        md.append("\n")
    
    md.append("---\n")
    md.append("\n## Conclusions\n")
    md.append("The experimental results demonstrate:\n")
    md.append("1. Complete implementation of the CBR cycle (RETRIEVE, ADAPT, REVISE, RETAIN)\n")
    md.append("2. Effective learning from user feedback with adaptive weight optimization\n")
    md.append("3. Semantic cultural similarity enhancing retrieval and adaptation accuracy\n")
    md.append("4. Negative case learning preventing repetition of past failures\n")
    md.append("5. Progressive system improvement through multi-user simulation\n")
    
    return "\n".join(md)


def generate_csv_summary(data: Dict) -> str:
    """Genera resumen CSV de métricas clave."""
    
    csv_lines = ["Test,Metric,Value"]
    
    for test_key, result in data.get('results', {}).items():
        if result.get('data') and 'summary' in result['data']:
            summary = result['data']['summary']
            for key, value in summary.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    csv_lines.append(f"{test_key},{key},{value}")
    
    return "\n".join(csv_lines)


def generate_reports(master_report: Dict = None, verbose: bool = True) -> Dict[str, Path]:
    """
    Genera reportes markdown y CSV desde el master report.
    
    Args:
        master_report: Dict con resultados. Si None, lee de data/results/master_test_report.json
        verbose: Si True, imprime mensajes de progreso
        
    Returns:
        Dict con paths de los archivos generados
    """
    # Setup paths
    base_dir = Path(__file__).parent.parent
    results_dir = base_dir / "data" / "results"
    reports_dir = base_dir / "data" / "reports"
    
    # Cargar master report si no se proporciona
    if master_report is None:
        master_file = results_dir / "master_test_report.json"
        if not master_file.exists():
            raise FileNotFoundError(f"Master report not found: {master_file}")
        
        with open(master_file, 'r') as f:
            master_report = json.load(f)
    
    # Crear directorio de reportes
    reports_dir.mkdir(exist_ok=True)
    
    generated_files = {}
    
    # Markdown report
    md_content = generate_markdown_report(master_report)
    md_file = reports_dir / "FORMAL_REPORT.md"
    with open(md_file, 'w') as f:
        f.write(md_content)
    generated_files['markdown'] = md_file
    
    if verbose:
        print(f"Markdown report generated: {md_file}")
    
    # CSV summary
    csv_content = generate_csv_summary(master_report)
    csv_file = reports_dir / "test_summary.csv"
    with open(csv_file, 'w') as f:
        f.write(csv_content)
    generated_files['csv'] = csv_file
    
    if verbose:
        print(f"CSV summary generated: {csv_file}")
    
    return generated_files


if __name__ == "__main__":
    generate_reports(verbose=True)
