# Formal Testing Suite

This directory contains formal experimental tests for the CBR system, designed for academic presentation and evaluation.

## Test Suite Overview

### Core Tests

1. **test_complete_cbr_cycle.py** - Complete CBR cycle evaluation
2. **test_user_simulation.py** - Multi-user simulation with learning
3. **test_adaptive_weights.py** - Adaptive weight optimization
4. **test_semantic_cultural_adaptation.py** - Semantic cultural adaptation
5. **test_semantic_retrieve.py** - Semantic similarity in RETRIEVE
6. **test_negative_cases.py** - Negative case learning
7. **test_semantic_retain.py** - Semantic similarity in RETAIN
8. **test_adaptive_learning.py** - Comparative evaluation (static vs adaptive)

## Running Tests

### Run All Tests

```bash
python run_all_tests.py
```

### Run Individual Test

```bash
python tests/test_complete_cbr_cycle.py
```

### Generate Formal Report

```bash
python run_all_tests.py
python generate_formal_report.py
```

## Output Files

All test results are saved in `data/` directory:

- `test_*.json` - Individual test results (JSON format)
- `master_test_report.json` - Consolidated results
- `FORMAL_REPORT.md` - Formatted report for presentation
- `test_summary.csv` - Metrics summary (spreadsheet compatible)

## Test Characteristics

- **Formal output**: No emojis, minimal console output
- **Structured results**: JSON format with clear metrics
- **Reproducible**: Deterministic where possible
- **Quantitative**: Focus on measurable metrics
- **Academic**: Suitable for research reports and presentations
