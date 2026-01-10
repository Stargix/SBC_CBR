#!/usr/bin/env python3
"""
Run All Tests
=============

Script principal para ejecutar tests y generar reportes.

Uso:
    python run_tests.py              # Ejecuta tests + genera reportes + HTML
    python run_tests.py --no-report  # Solo tests
    python run_tests.py --no-html    # Tests + reportes (sin HTML)
"""

import argparse
from pathlib import Path

# Añadir tests/ al path
import sys
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from test_executor import execute_all_tests, print_test_summary
from report_generator import generate_reports
from html_generator import generate_test_html


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta tests formales y genera reportes"
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
        print("\n STEP 1/3: Executing tests...")
    master_report = execute_all_tests(verbose=verbose)
    
    if verbose:
        print_test_summary(master_report)
    
    # 2. Generar reportes
    if not args.no_report:
        if verbose:
            print("\n STEP 2/3: Generating reports...")
        generate_reports(master_report, verbose=verbose)
    elif verbose:
        print("\n⏭  STEP 2/3: Skipping report generation (--no-report)")
    
    # 3. Generar HTML
    if not args.no_html:
        if verbose:
            print("\n STEP 3/3: Generating HTML...")
        generate_test_html(master_report, verbose=verbose)
    elif verbose:
        print("\n⏭  STEP 3/3: Skipping HTML generation (--no-html)")
    
    if verbose:
        print("\n All done!\n")


if __name__ == "__main__":
    main()
