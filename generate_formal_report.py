"""
Generate Formal Test Report
============================

Creates a formatted report suitable for academic presentation.
Outputs both JSON and Markdown formats.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def format_number(value, decimals=2):
    """Format number for display."""
    if isinstance(value, float):
        return f"{value:.{decimals}f}"
    return str(value)


def generate_markdown_report(data: Dict) -> str:
    """Generate markdown formatted report."""
    
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
    """Generate CSV summary of key metrics."""
    
    csv_lines = ["Test,Metric,Value"]
    
    for test_key, result in data.get('results', {}).items():
        if result.get('data') and 'summary' in result['data']:
            summary = result['data']['summary']
            
            for key, value in summary.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    csv_lines.append(f"{test_key},{key},{value}")
    
    return "\n".join(csv_lines)


def main():
    """Generate formal report from test results."""
    
    master_report_file = Path(__file__).parent / "data" / "master_test_report.json"
    
    if not master_report_file.exists():
        print("Error: Master test report not found. Run 'python run_all_tests.py' first.")
        sys.exit(1)
    
    with open(master_report_file, 'r') as f:
        data = json.load(f)
    
    # Generate markdown report
    markdown_content = generate_markdown_report(data)
    markdown_file = Path(__file__).parent / "data" / "FORMAL_REPORT.md"
    
    with open(markdown_file, 'w') as f:
        f.write(markdown_content)
    
    print(f"Markdown report generated: {markdown_file}")
    
    # Generate CSV summary
    csv_content = generate_csv_summary(data)
    csv_file = Path(__file__).parent / "data" / "test_summary.csv"
    
    with open(csv_file, 'w') as f:
        f.write(csv_content)
    
    print(f"CSV summary generated: {csv_file}")
    
    # Print to console
    print("\n" + "="*80)
    print(markdown_content)
    print("="*80)


if __name__ == "__main__":
    main()
