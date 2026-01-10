"""
HTML Generator Module
=====================

Genera reportes HTML interactivos para cada test individual con gráficos y plots.
"""

import json
import base64
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


def embed_image_as_base64(image_path: Path) -> Optional[str]:
    """Convierte imagen PNG a base64 para incrustar en HTML."""
    if not image_path.exists():
        return None
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"Error embedding image {image_path}: {e}")
        return None


def generate_individual_test_htmls(results_dir: Path, htmls_dir: Path, verbose: bool = True) -> List[Path]:
    """
    Genera HTMLs individuales para cada test desde sus JSONs.
    
    Args:
        results_dir: Directorio con los JSONs de resultados
        htmls_dir: Directorio donde guardar los HTMLs
        verbose: Si True, imprime progreso
        
    Returns:
        Lista de Paths de HTMLs generados
    """
    htmls_dir.mkdir(exist_ok=True)
    generated_files = []
    
    # Mapeo de tests a generadores específicos
    test_generators = {
        "test_complete_cbr_cycle": generate_cbr_cycle_html,
        "test_user_simulation": generate_user_simulation_html,
        "test_adaptive_weights": generate_adaptive_weights_html,
        "test_semantic_cultural_adaptation": generate_cultural_adaptation_html,
        "test_semantic_retrieve": generate_retrieve_html,
        "test_negative_cases": generate_negative_cases_html,
        "test_semantic_retain": generate_retain_html,
        "test_adaptive_learning": generate_adaptive_learning_html
    }
    
    for test_name, generator_func in test_generators.items():
        json_file = results_dir / f"{test_name}.json"
        
        if not json_file.exists():
            if verbose:
                print(f"  ⚠️  Skipping {test_name} (JSON not found)")
            continue
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            html_content = generator_func(data, test_name)
            html_file = htmls_dir / f"report_{test_name}.html"
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            generated_files.append(html_file)
            
            if verbose:
                print(f"  ✓ Generated: {html_file.name}")
                
        except Exception as e:
            if verbose:
                print(f"  ✗ Error generating {test_name}: {e}")
    
    return generated_files


def generate_test_html(master_report: Dict = None, verbose: bool = True) -> Dict[str, List[Path]]:
    """
    Genera HTMLs: uno consolidado + HTMLs individuales para cada test.
    
    Args:
        master_report: Dict con resultados. Si None, lee de data/results/master_test_report.json
        verbose: Si True, imprime mensajes de progreso
        
    Returns:
        Dict con 'consolidated' y 'individual' paths
    """
    # Setup paths
    base_dir = Path(__file__).parent.parent
    results_dir = base_dir / "data" / "results"
    htmls_dir = base_dir / "data" / "htmls"
    
    # Cargar master report si no se proporciona
    if master_report is None:
        master_file = results_dir / "master_test_report.json"
        if not master_file.exists():
            if verbose:
                print(f"Master report not found: {master_file}")
            return {}
        
        with open(master_file, 'r') as f:
            master_report = json.load(f)
    
    htmls_dir.mkdir(exist_ok=True)
    
    generated = {
        'consolidated': None,
        'individual': []
    }
    
    # 1. Generar HTML consolidado
    html_content = generate_simple_html(master_report)
    html_file = htmls_dir / "test_results.html"
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    generated['consolidated'] = html_file
    
    if verbose:
        print(f"  ✓ Consolidated HTML: {html_file.name}")
    
    # 2. Generar HTMLs individuales para cada test
    if verbose:
        print(f"\n  Generating individual test HTMLs...")
    
    individual_htmls = generate_individual_test_htmls(results_dir, htmls_dir, verbose=verbose)
    generated['individual'] = individual_htmls
    
    return generated


def generate_simple_html(data: Dict) -> str:
    """Genera HTML simple con resultados de tests."""
    
    successful = sum(1 for r in data.get('results', {}).values() 
                    if r.get('execution', {}).get('status') == 'success')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CBR Test Results</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2563eb;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .test-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .test-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .status-success {{
            color: #059669;
        }}
        .status-failed {{
            color: #dc2626;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        .metric-item {{
            padding: 8px;
            background: #f9fafb;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CBR System - Test Results</h1>
        <p>Generated: {data.get('execution_timestamp', 'N/A')}</p>
    </div>
    
    <div class="summary">
        <div class="metric-card">
            <div class="metric-value">{data.get('tests_executed', 0)}</div>
            <div class="metric-label">Total Tests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #059669">{successful}</div>
            <div class="metric-label">Successful</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #dc2626">{data.get('tests_executed', 0) - successful}</div>
            <div class="metric-label">Failed</div>
        </div>
    </div>
    
    <h2>Test Details</h2>
"""
    
    test_names = {
        "test_complete_cbr_cycle": "Complete CBR Cycle",
        "test_user_simulation": "Multi-User Simulation",
        "test_adaptive_weights": "Adaptive Weight Learning",
        "test_semantic_cultural_adaptation": "Semantic Cultural Adaptation",
        "test_semantic_retrieve": "Semantic RETRIEVE",
        "test_negative_cases": "Negative Cases Learning",
        "test_semantic_retain": "Semantic RETAIN",
        "test_adaptive_learning": "Adaptive Learning Evaluation"
    }
    
    for test_key, result in data.get('results', {}).items():
        status = result.get('execution', {}).get('status', 'unknown')
        status_class = 'status-success' if status == 'success' else 'status-failed'
        test_name = test_names.get(test_key, test_key)
        
        html += f"""
    <div class="test-card">
        <div class="test-title">{test_name} <span class="{status_class}">({status.upper()})</span></div>
"""
        
        if result.get('data', {}).get('summary'):
            html += '        <div class="metrics">\n'
            summary = result['data']['summary']
            for key, value in list(summary.items())[:8]:
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    formatted_key = key.replace('_', ' ').title()
                    if isinstance(value, float):
                        formatted_value = f"{value:.3f}"
                    else:
                        formatted_value = str(value)
                    html += f'            <div class="metric-item"><strong>{formatted_key}:</strong> {formatted_value}</div>\n'
            html += '        </div>\n'
        
        html += '    </div>\n'
    
    html += """
    <div style="text-align: center; margin-top: 40px; color: #666;">
        <p>For detailed analysis, see FORMAL_REPORT.md</p>
    </div>
</body>
</html>
"""
    
    return html


# ============================================================================
# INDIVIDUAL TEST HTML GENERATORS
# ============================================================================

def get_html_template(title: str, test_name: str, embedded_images: Dict[str, str] = None) -> str:
    """Template base para HTMLs individuales con estilos mejorados."""
    
    if embedded_images is None:
        embedded_images = {}
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Chef Digital CBR</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}
        
        .card-title {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .card-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            position: relative;
            height: 400px;
        }}
        
        .plot-container {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .plot-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
        }}
        
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }}
        
        .metric-label {{
            font-size: 0.85em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        
        .metric-unit {{
            font-size: 0.8em;
            color: #999;
            margin-top: 5px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Test: {test_name}</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
"""
    
    return html


def generate_cbr_cycle_html(data: Dict, test_name: str) -> str:
    """Genera HTML para test_complete_cbr_cycle."""
    return generate_generic_html(data, "Complete CBR Cycle Test", test_name)


def generate_user_simulation_html(data: Dict, test_name: str) -> str:
    """Genera HTML para test_user_simulation con plots embebidos."""
    base_dir = Path(__file__).parent.parent
    plots_dir = base_dir / "data" / "plots"
    
    plot_images = {}
    
    # Intentar incrustar feedback_evolution.png
    feedback_plot = plots_dir / "feedback_evolution.png"
    if feedback_plot.exists():
        plot_images['feedback_evolution'] = embed_image_as_base64(feedback_plot)
    
    return generate_generic_html(data, "Multi-User Simulation", test_name, plot_images)


def generate_adaptive_weights_html(data: Dict, test_name: str) -> str:
    """Genera HTML para test_adaptive_weights con plots embebidos."""
    base_dir = Path(__file__).parent.parent
    plots_dir = base_dir / "data" / "plots"
    
    plot_images = {}
    
    # Intentar incrustar weight_evolution.png
    weight_plot = plots_dir / "weight_evolution.png"
    if weight_plot.exists():
        plot_images['weight_evolution'] = embed_image_as_base64(weight_plot)
    
    return generate_generic_html(data, "Adaptive Weight Learning", test_name, plot_images)


def generate_cultural_adaptation_html(data: Dict, test_name: str) -> str:
    """Genera HTML para test_semantic_cultural_adaptation."""
    return generate_generic_html(data, "Semantic Cultural Adaptation", test_name)


def generate_retrieve_html(data: Dict, test_name: str) -> str:
    """Genera HTML para test_semantic_retrieve."""
    return generate_generic_html(data, "Semantic RETRIEVE Test", test_name)


def generate_negative_cases_html(data: Dict, test_name: str) -> str:
    """Genera HTML para test_negative_cases."""
    return generate_generic_html(data, "Negative Cases Learning", test_name)


def generate_retain_html(data: Dict, test_name: str) -> str:
    """Genera HTML para test_semantic_retain."""
    return generate_generic_html(data, "Semantic RETAIN Test", test_name)


def generate_adaptive_learning_html(data: Dict, test_name: str) -> str:
    """Genera HTML para test_adaptive_learning."""
    base_dir = Path(__file__).parent.parent
    plots_dir = base_dir / "data" / "plots"
    
    plot_images = {}
    
    # Intentar incrustar feedback_correlation.png y otros plots
    correlation_plot = plots_dir / "feedback_correlation.png"
    if correlation_plot.exists():
        plot_images['feedback_correlation'] = embed_image_as_base64(correlation_plot)
    
    return generate_generic_html(data, "Adaptive Learning Evaluation", test_name, plot_images)


def generate_generic_html(data: Dict, title: str, test_name: str, plot_images: Dict[str, str] = None) -> str:
    """Generador genérico de HTML para cualquier test."""
    
    if plot_images is None:
        plot_images = {}
    
    html = get_html_template(title, test_name)
    summary = data.get('summary', {})
    
    # Tarjetas de resumen (primeras 4 métricas)
    html += '        <div class="summary-cards">\n'
    metric_items = list(summary.items())
    for key, value in metric_items[:4]:
        if isinstance(value, (int, float)):
            formatted_key = key.replace('_', ' ').title()
            formatted_value = f"{value:.3f}" if isinstance(value, float) else str(value)
            html += f"""
            <div class="card">
                <div class="card-title">{formatted_key}</div>
                <div class="card-value">{formatted_value}</div>
            </div>
"""
    html += '        </div>\n'
    
    # Sección de plots embebidos
    if plot_images:
        html += '        <div class="content">\n'
        html += '            <div class="section">\n'
        html += '                <h2 class="section-title">📊 Visualizaciones</h2>\n'
        
        for plot_name, plot_base64 in plot_images.items():
            if plot_base64:
                html += f"""
                <div class="plot-container">
                    <h3>{plot_name.replace('_', ' ').title()}</h3>
                    <img src="data:image/png;base64,{plot_base64}" alt="{plot_name}">
                </div>
"""
        html += '            </div>\n'
    
    # Sección de métricas detalladas
    html += """
            <div class="section">
                <h2 class="section-title">📈 Métricas Detalladas</h2>
                <div class="metric-grid">
"""
    
    for key, value in summary.items():
        if isinstance(value, (int, float)):
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, float):
                formatted_value = f"{value:.4f}" if value < 1 else f"{value:.2f}"
            else:
                formatted_value = str(value)
            
            html += f"""
                    <div class="metric-card">
                        <div class="metric-label">{formatted_key}</div>
                        <div class="metric-value">{formatted_value}</div>
                    </div>
"""
    
    html += """
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>For detailed analysis, see FORMAL_REPORT.md in data/reports/</p>
        </div>
    </div>
</body>
</html>
"""
    return html


if __name__ == "__main__":
    generate_test_html(verbose=True)
