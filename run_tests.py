#!/usr/bin/env python3
"""
Run All Tests
=============

Script principal para ejecutar tests y generar reportes.

Ejecución:
- Tests formales (8 tests)
- Reportes markdown y CSV
- HTMLs interactivos con plots Plotly
- Plots PNG adicionales (matplotlib)

Uso:
    python run_tests.py              # Todo (tests + reportes + HTML + plots)
    python run_tests.py --no-report  # Solo tests
    python run_tests.py --no-html    # Tests + reportes (sin HTML ni plots)
    python run_tests.py -q           # Modo silencioso
"""

import argparse
from pathlib import Path

# Añadir tests/ al path
import sys
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from test_executor import execute_all_tests, print_test_summary
from report_generator import generate_reports
from html_generator import generate_test_html
from generate_plots import (
    plot_cultural_similarity_heatmap,
    plot_cbr_cycle_phases,
    plot_adaptation_intensity,
    plot_negative_learning,
    plot_retention_strategies
)


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta tests formales, genera reportes, HTMLs y plots"
    )
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='No generar reportes markdown/CSV'
    )
    parser.add_argument(
        '--no-html',
        action='store_true',
        help='No generar HTML interactivo'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Modo silencioso (menos output)'
    )
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    # 1. Ejecutar tests
    if verbose:
        print("\n🧪 STEP 1/4: Executing tests...")
    master_report = execute_all_tests(verbose=verbose)
    
    if verbose:
        print_test_summary(master_report)
    
    # 2. Generar reportes
    if not args.no_report:
        if verbose:
            print("\n📊 STEP 2/4: Generating reports...")
        generate_reports(master_report, verbose=verbose)
    elif verbose:
        print("\n⏭  STEP 2/4: Skipping report generation (--no-report)")
    
    # 3. Generar HTML
    if not args.no_html:
        if verbose:
            print("\n🌐 STEP 3/4: Generating HTML...")
        generate_test_html(master_report, verbose=verbose)
    elif verbose:
        print("\n⏭  STEP 3/4: Skipping HTML generation (--no-html)")
    
    # 4. Generar plots adicionales (PNG)
    if not args.no_html:  # Solo si no saltamos HTML
        if verbose:
            print("\n📈 STEP 4/4: Generating additional plots...")
        try:
            plot_cultural_similarity_heatmap()
            plot_cbr_cycle_phases()
            plot_adaptation_intensity()
            plot_negative_learning()
            plot_retention_strategies()
            if verbose:
                print("✅ Plots generados exitosamente en data/plots/")
        except Exception as e:
            if verbose:
                print(f"⚠ Error generando plots: {e}")
    
    if verbose:
        print("\n✅ All done!\n")


if __name__ == "__main__":
    main()
