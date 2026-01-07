# Formal Testing Suite - Quick Start Guide

## Overview

This testing suite provides formal, academic-quality experimental evaluation of the CBR system's capabilities. All tests are designed to produce quantitative, reproducible results suitable for research reports and presentations.

## Quick Start

### 1. Run All Tests

```bash
python run_all_tests.py
```

This will execute all 8 formal tests sequentially and generate a master report.

### 2. Generate Formal Report

```bash
python generate_formal_report.py
```

This creates:
- `data/FORMAL_REPORT.md` - Formatted markdown report
- `data/test_summary.csv` - Metrics summary for spreadsheets

### 3. View Results

```bash
cat data/FORMAL_REPORT.md
```

## Individual Tests

Each test can be run independently:

```bash
# Complete CBR Cycle
python tests/test_complete_cbr_cycle.py

# Multi-User Simulation  
python tests/test_user_simulation.py

# Adaptive Weight Learning
python tests/test_adaptive_weights.py

# Semantic Cultural Adaptation
python tests/test_semantic_cultural_adaptation.py

# Semantic RETRIEVE
python tests/test_semantic_retrieve.py

# Negative Cases Learning
python tests/test_negative_cases.py

# Semantic RETAIN
python tests/test_semantic_retain.py

# Comparative Evaluation
python tests/test_adaptive_learning.py
```

## Output Structure

```
data/
├── test_complete_cbr_cycle.json
├── test_user_simulation.json
├── test_adaptive_weights.json
├── test_semantic_cultural_adaptation.json
├── test_semantic_retrieve.json
├── test_negative_cases.json
├── test_semantic_retain.json
├── test_adaptive_learning.json
├── master_test_report.json
├── FORMAL_REPORT.md
└── test_summary.csv
```

## Test Coverage

### CBR Core Phases
- **RETRIEVE**: Tests 1, 4, 5
- **ADAPT**: Tests 1, 3, 4
- **REVISE**: Tests 1
- **RETAIN**: Tests 1, 2, 6, 7

### Advanced Techniques
- **Adaptive Weight Learning**: Tests 2, 3, 8
- **Semantic Similarity (Embeddings)**: Tests 4, 5, 7
- **Negative Case Learning**: Test 6
- **Multi-User Simulation**: Test 2

## Expected Runtime

- Individual test: 10-60 seconds
- Full suite: 5-8 minutes
- Report generation: <5 seconds

## Output Format

All tests produce:
- **JSON**: Structured, machine-readable results
- **Console**: Minimal, formal output
- **Metrics**: Quantitative measurements for analysis

## Notes

- Tests are deterministic where possible
- No decorative output (emojis removed)
- Focus on measurable, objective metrics
- Suitable for academic presentation
