#!/usr/bin/env python3
"""
Generador de HTML mejorado para reportes de tests del sistema CBR.
Utiliza la estética de la web y aprovecha toda la información de los JSON.
"""

import json
import base64
from pathlib import Path
from datetime import datetime


def load_json(filepath):
    """Carga un archivo JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def encode_image_base64(image_path):
    """Codifica una imagen en base64 para incrustarla en HTML."""
    if not Path(image_path).exists():
        return None
    with open(image_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"


def get_html_template(title, has_plots=False):
    """Genera la plantilla HTML base con la estética de la web."""
    plots_html = ""
    if has_plots:
        plots_html = """
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        """
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - CBR System Report</title>
    <style>
        :root {{
            --surface: #ffffff;
            --ink: #0f172a;
            --muted: #5b6474;
            --accent: #0f766e;
            --accent-2: #e07a5f;
            --line: #e1dacf;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #faf7f1 0%, #f4f1eb 100%);
            color: var(--ink);
            padding: 28px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            margin-bottom: 32px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 42px;
            letter-spacing: -0.02em;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .header .subtitle {{
            color: var(--muted);
            font-size: 16px;
        }}
        
        .panel {{
            background: var(--surface);
            border-radius: 18px;
            border: 1px solid var(--line);
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
        }}
        
        .panel h2 {{
            font-size: 26px;
            margin-bottom: 20px;
            color: var(--accent);
        }}
        
        .panel h3 {{
            font-size: 20px;
            margin: 24px 0 12px 0;
            color: var(--ink);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        .stat-card {{
            background: #faf7f1;
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 16px;
            text-align: center;
        }}
        
        .stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 8px;
        }}
        
        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: var(--accent);
        }}
        
        .stat-value.positive {{
            color: #059669;
        }}
        
        .stat-value.negative {{
            color: #dc2626;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        .comparison-table th {{
            background: var(--accent);
            color: white;
            padding: 12px;
            text-align: left;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .comparison-table td {{
            padding: 12px;
            border-bottom: 1px solid var(--line);
        }}
        
        .comparison-table tr:hover {{
            background: #faf7f1;
        }}
        
        .plot-container {{
            margin: 24px 0;
            padding: 20px;
            background: white;
            border-radius: 12px;
            border: 1px solid var(--line);
        }}
        
        .plot-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--accent);
        }}
        
        .alert {{
            padding: 14px 18px;
            border-radius: 12px;
            margin: 16px 0;
            font-size: 14px;
        }}
        
        .alert.info {{
            background: rgba(15, 118, 110, 0.08);
            color: var(--accent);
            border: 1px solid rgba(15, 118, 110, 0.2);
        }}
        
        .alert.success {{
            background: rgba(5, 150, 105, 0.08);
            color: #059669;
            border: 1px solid rgba(5, 150, 105, 0.2);
        }}
        
        .alert.warning {{
            background: rgba(224, 122, 95, 0.08);
            color: var(--accent-2);
            border: 1px solid rgba(224, 122, 95, 0.2);
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .badge.success {{
            background: rgba(5, 150, 105, 0.15);
            color: #059669;
        }}
        
        .badge.neutral {{
            background: rgba(91, 100, 116, 0.15);
            color: var(--muted);
        }}
        
        .badge.warning {{
            background: rgba(224, 122, 95, 0.15);
            color: var(--accent-2);
        }}
        
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: var(--muted);
            font-size: 14px;
            padding: 20px;
            border-top: 1px solid var(--line);
        }}
        
        code {{
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            color: var(--accent-2);
        }}
    </style>
    {plots_html}
</head>
<body>
    <div class="container">
"""


def get_html_footer():
    """Genera el pie de página HTML."""
    return """
    </div>
    <div class="footer">
        <p>Generated on {timestamp}</p>
        <p>CBR Chef System - Experimental Results Report</p>
    </div>
</body>
</html>
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def generate_adaptive_weights_html(data, output_path):
    """Genera HTML para test de adaptive weights con comparativas y gráficos."""
    html = get_html_template("Adaptive Weight Learning", has_plots=True)
    
    # Header
    html += """
        <div class="header">
            <h1>🎯 Adaptive Weight Learning</h1>
            <p class="subtitle">Comparative Analysis: Static vs Adaptive Weight Systems</p>
        </div>
    """
    
    # Summary stats
    static_data = data['systems']['static']['results']
    adaptive_data = data['systems']['adaptive']['results']
    
    static_avg_top = sum(r['top_similarity'] for r in static_data) / len(static_data)
    adaptive_avg_top = sum(r['top_similarity'] for r in adaptive_data) / len(adaptive_data)
    improvement = ((adaptive_avg_top - static_avg_top) / static_avg_top) * 100
    
    html += """
        <div class="panel">
            <h2>📊 Summary Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Static Avg Similarity</div>
                    <div class="stat-value">{:.2%}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Adaptive Avg Similarity</div>
                    <div class="stat-value positive">{:.2%}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Improvement</div>
                    <div class="stat-value {}">{:+.2f}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Iterations Tested</div>
                    <div class="stat-value">{}</div>
                </div>
            </div>
        </div>
    """.format(
        static_avg_top,
        adaptive_avg_top,
        "positive" if improvement > 0 else "negative",
        improvement,
        len(static_data)
    )
    
    # Detailed comparison - AHORA CON PLOTS
    html += """
        <div class="panel">
            <h2>📊 Performance Comparison</h2>
            <div class="plot-container">
                <div id="similarityComparisonPlot"></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📈 Similarity Trends</h2>
            <div class="plot-container">
                <div id="trendsPlot"></div>
            </div>
        </div>
        
        <script>
            // Prepare comparison data
            var iterations = [];
            var staticTop = [];
            var adaptiveTop = [];
            var staticAvg = [];
            var adaptiveAvg = [];
    """
    
    for i, (s, a) in enumerate(zip(static_data, adaptive_data), 1):
        html += f"""
            iterations.push({i});
            staticTop.push({s['top_similarity']});
            adaptiveTop.push({a['top_similarity']});
            staticAvg.push({s['avg_similarity']});
            adaptiveAvg.push({a['avg_similarity']});
        """
    
    html += """
            // Comparison plot
            var trace1 = {
                x: iterations,
                y: staticTop,
                mode: 'lines+markers',
                name: 'Static - Top Similarity',
                line: {color: '#5b6474', width: 2, dash: 'dash'},
                marker: {size: 8}
            };
            
            var trace2 = {
                x: iterations,
                y: adaptiveTop,
                mode: 'lines+markers',
                name: 'Adaptive - Top Similarity',
                line: {color: '#0f766e', width: 3},
                marker: {size: 10}
            };
            
            var trace3 = {
                x: iterations,
                y: staticAvg,
                mode: 'lines+markers',
                name: 'Static - Avg Similarity',
                line: {color: '#9ca3af', width: 2, dash: 'dot'},
                marker: {size: 8}
            };
            
            var trace4 = {
                x: iterations,
                y: adaptiveAvg,
                mode: 'lines+markers',
                name: 'Adaptive - Avg Similarity',
                line: {color: '#e07a5f', width: 3},
                marker: {size: 10}
            };
            
            var compLayout = {
                title: 'Static vs Adaptive: Similarity Performance',
                xaxis: {title: 'Iteration'},
                yaxis: {title: 'Similarity Score', range: [0, 1]},
                hovermode: 'x unified',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'},
                showlegend: true,
                legend: {x: 0.7, y: 0.1}
            };
            
            Plotly.newPlot('similarityComparisonPlot', [trace1, trace2, trace3, trace4], compLayout, {responsive: true});
            
            // Improvement trend
            var improvements = [];
            for (var i = 0; i < iterations.length; i++) {
                improvements.push((adaptiveTop[i] - staticTop[i]) * 100);
            }
            
            var improvementTrace = {
                x: iterations,
                y: improvements,
                type: 'bar',
                name: 'Improvement (%)',
                marker: {
                    color: improvements.map(v => v > 0 ? '#059669' : '#dc2626')
                }
            };
            
            var trendLayout = {
                title: 'Adaptive Improvement Over Static (%)',
                xaxis: {title: 'Iteration'},
                yaxis: {title: 'Improvement (%)', zeroline: true},
                hovermode: 'closest',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('trendsPlot', [improvementTrace], trendLayout, {responsive: true});
        </script>
    """
    
    # Weight evolution (if available in adaptive data)
    if 'weights' in adaptive_data[0]:
        html += """
        <div class="panel">
            <h2>⚖️ Weight Evolution Over Iterations</h2>
            <div class="plot-container">
                <div id="weightsPlot"></div>
            </div>
        </div>
        <script>
            var weights = [];
            var iterations = [];
        """
        
        # Extraer evolución de pesos
        weight_keys = list(adaptive_data[0]['weights'].keys())
        weight_evolution = {key: [] for key in weight_keys}
        
        for i, result in enumerate(adaptive_data, 1):
            html += f"iterations.push({i});\n"
            for key in weight_keys:
                weight_evolution[key].append(result['weights'][key])
        
        # Crear traces para plotly
        html += "var traces = [];\n"
        for key in weight_keys:
            html += f"""
            traces.push({{
                x: iterations,
                y: {weight_evolution[key]},
                mode: 'lines+markers',
                name: '{key}',
                line: {{width: 2}},
                marker: {{size: 8}}
            }});
            """
        
        html += """
            var layout = {
                title: 'Weight Adaptation Throughout Iterations',
                xaxis: {title: 'Iteration'},
                yaxis: {title: 'Weight Value'},
                hovermode: 'closest',
                showlegend: true,
                height: 500
            };
            Plotly.newPlot('weightsPlot', traces, layout);
        </script>
        """
    
    # Plot evolution image if exists
    plot_path = Path('data/plots/weight_evolution.png')
    if plot_path.exists():
        img_data = encode_image_base64(plot_path)
        if img_data:
            html += f"""
        <div class="panel">
            <h2>📈 Weight Evolution Visualization</h2>
            <div class="plot-container">
                <img src="{img_data}" style="width: 100%; height: auto;" alt="Weight Evolution">
            </div>
        </div>
            """
    
    html += get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f" Generated: {output_path}")


def generate_adaptive_learning_html(data, output_path):
    """Genera HTML para test de adaptive learning."""
    html = get_html_template("Adaptive Learning Evaluation", has_plots=True)
    
    summary = data['summary']
    
    html += """
        <div class="header">
            <h1>🧠 Adaptive Learning Evaluation</h1>
            <p class="subtitle">Comparative Performance Analysis</p>
        </div>
    """
    
    # Main metrics
    html += f"""
        <div class="panel">
            <h2>📊 Key Performance Indicators</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Static Precision</div>
                    <div class="stat-value">{summary['static_precision']:.1%}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Adaptive Precision</div>
                    <div class="stat-value">{summary['adaptive_precision']:.1%}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Precision Improvement</div>
                    <div class="stat-value {'positive' if summary['precision_improvement_pct'] > 0 else 'neutral'}">{summary['precision_improvement_pct']:+.1f}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Test Cases</div>
                    <div class="stat-value">{summary['total_test_cases']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Static Satisfaction</div>
                    <div class="stat-value">{summary['static_satisfaction']:.1f}/5</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Adaptive Satisfaction</div>
                    <div class="stat-value">{summary['adaptive_satisfaction']:.1f}/5</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Satisfaction Δ</div>
                    <div class="stat-value {'positive' if summary['satisfaction_improvement'] > 0 else 'neutral'}">{summary['satisfaction_improvement']:+.1f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Time Overhead</div>
                    <div class="stat-value">{summary['time_overhead_seconds']*1000:.1f}ms</div>
                </div>
            </div>
        </div>
    """
    
    # Performance comparison
    html += f"""
        <div class="panel">
            <h2>🔬 Detailed Comparison</h2>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Static System</th>
                        <th>Adaptive System</th>
                        <th>Difference</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Precision</strong></td>
                        <td>{summary['static_precision']:.2%}</td>
                        <td>{summary['adaptive_precision']:.2%}</td>
                        <td><span class="badge {'success' if summary['precision_improvement_pct'] > 0 else 'neutral'}">{summary['precision_improvement_pct']:+.1f}%</span></td>
                    </tr>
                    <tr>
                        <td><strong>User Satisfaction</strong></td>
                        <td>{summary['static_satisfaction']:.2f} / 5.0</td>
                        <td>{summary['adaptive_satisfaction']:.2f} / 5.0</td>
                        <td><span class="badge {'success' if summary['satisfaction_improvement'] > 0 else 'neutral'}">{summary['satisfaction_improvement']:+.2f}</span></td>
                    </tr>
                    <tr>
                        <td><strong>Processing Time</strong></td>
                        <td>{summary['static_time']*1000:.2f} ms</td>
                        <td>{summary['adaptive_time']*1000:.2f} ms</td>
                        <td><span class="badge warning">{summary['time_overhead_seconds']*1000:+.2f} ms</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    """
    
    # Conclusion
    winner = "Adaptive" if summary['adaptive_better'] else "Static"
    alert_class = "success" if summary['adaptive_better'] else "info"
    
    html += f"""
        <div class="panel">
            <h2>💡 Conclusion</h2>
            <div class="alert {alert_class}">
                <strong>Winner: {winner} System</strong><br>
                {'The adaptive system shows measurable improvements in key metrics.' if summary['adaptive_better'] else 'Both systems perform similarly with no significant difference.'}
            </div>
        </div>
    """
    
    # Plot if exists
    plot_path = Path('data/plots/feedback_correlation.png')
    if plot_path.exists():
        img_data = encode_image_base64(plot_path)
        if img_data:
            html += f"""
        <div class="panel">
            <h2>📈 Performance Correlation</h2>
            <div class="plot-container">
                <img src="{img_data}" style="width: 100%; height: auto;" alt="Feedback Correlation">
            </div>
        </div>
            """
    
    html += get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f" Generated: {output_path}")


def generate_semantic_retrieve_html(data, output_path):
    """Genera HTML para test de semantic retrieve."""
    html = get_html_template("Semantic Similarity Retrieval", has_plots=True)
    
    html += """
        <div class="header">
            <h1>🔍 Semantic Similarity Retrieval</h1>
            <p class="subtitle">Recipe Retrieval with Semantic Similarity Analysis</p>
        </div>
    """
    
    test_results = data.get('cultural_preferences', [])
    
    # Summary stats
    total_tests = len(test_results)
    total_retrieved = sum(t.get('cases_retrieved', 0) for t in test_results)
    avg_retrieved = total_retrieved / total_tests if total_tests > 0 else 0
    
    html += f"""
        <div class="panel">
            <h2>📊 Retrieval Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Cultures Tested</div>
                    <div class="stat-value">{total_tests}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Retrieved</div>
                    <div class="stat-value">{total_retrieved}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Retrieved per Culture</div>
                    <div class="stat-value">{avg_retrieved:.1f}</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📈 Similarity Scores by Culture</h2>
            <div class="plot-container">
                <div id="cultureSimilarityPlot"></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>🎯 Cultural Match Analysis</h2>
            <div class="plot-container">
                <div id="culturalMatchPlot"></div>
            </div>
        </div>
        
        <script>
            var cultures = [];
            var topScores = [];
            var avgScores = [];
            var matchCounts = [];
    """
    
    for test in test_results:
        culture = test.get('target_culture', 'unknown')
        metrics = test.get('metrics', {})
        html += f"""
            cultures.push('{culture}');
            topScores.push({metrics.get('top_similarity', 0)});
            avgScores.push({metrics.get('avg_similarity', 0)});
            matchCounts.push({metrics.get('exact_cultural_matches', 0)});
        """
    
    html += """
            // Similarity scores plot
            var topTrace = {
                x: cultures,
                y: topScores,
                name: 'Top Similarity',
                type: 'bar',
                marker: {color: '#0f766e'}
            };
            
            var avgTrace = {
                x: cultures,
                y: avgScores,
                name: 'Avg Similarity',
                type: 'bar',
                marker: {color: '#e07a5f'}
            };
            
            var similarityLayout = {
                title: 'Top vs Average Similarity by Culture',
                xaxis: {title: 'Culture'},
                yaxis: {title: 'Similarity Score', range: [0, 1]},
                barmode: 'group',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('cultureSimilarityPlot', [topTrace, avgTrace], similarityLayout, {responsive: true});
            
            // Cultural match plot
            var matchTrace = {
                x: cultures,
                y: matchCounts,
                type: 'bar',
                marker: {
                    color: matchCounts.map(v => v === 5 ? '#059669' : v >= 3 ? '#f59e0b' : '#dc2626')
                },
                text: matchCounts.map(v => v + '/5'),
                textposition: 'outside'
            };
            
            var matchLayout = {
                title: 'Exact Cultural Matches (out of 5 retrieved)',
                xaxis: {title: 'Culture'},
                yaxis: {title: 'Number of Matches', range: [0, 6]},
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('culturalMatchPlot', [matchTrace], matchLayout, {responsive: true});
        </script>
    """
    
    html += get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f" Generated: {output_path}")


def generate_user_simulation_html(data, output_path):
    """Genera HTML para test de user simulation con plots interactivos."""
    html = get_html_template("Multi-User Simulation", has_plots=True)
    
    html += """
        <div class="header">
            <h1>👥 Multi-User Simulation</h1>
            <p class="subtitle">System Performance Under Multi-User Load</p>
        </div>
    """
    
    params = data['parameters']
    iterations = data['iterations']
    
    # Calculate summary stats
    avg_feedback = sum(i['avg_feedback_score'] for i in iterations) / len(iterations)
    total_retained = sum(i['cases_retained'] for i in iterations)
    avg_success_rate = sum(i['success_rate'] for i in iterations) / len(iterations)
    
    html += f"""
        <div class="panel">
            <h2>📊 Simulation Parameters & Results</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Concurrent Users</div>
                    <div class="stat-value">{params['num_users']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Iterations</div>
                    <div class="stat-value">{params['iterations']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Feedback Score</div>
                    <div class="stat-value positive">{avg_feedback:.2f}/5</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Success Rate</div>
                    <div class="stat-value positive">{avg_success_rate:.1%}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Cases Retained</div>
                    <div class="stat-value">{total_retained}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Final Case Count</div>
                    <div class="stat-value">{iterations[-1]['current_case_count']}</div>
                </div>
            </div>
        </div>
    """
    
    # Interactive plots with Plotly
    html += """
        <div class="panel">
            <h2>📈 Feedback Score Evolution</h2>
            <div class="plot-container">
                <div id="feedbackPlot"></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📦 Case Base Growth</h2>
            <div class="plot-container">
                <div id="caseGrowthPlot"></div>
            </div>
        </div>
        
        <div class="panel">
            <h2> Success Rate & Retention</h2>
            <div class="plot-container">
                <div id="performancePlot"></div>
            </div>
        </div>
        
        <script>
            // Prepare data
            var iterations = [];
            var feedbackScores = [];
            var caseCounts = [];
            var casesRetained = [];
            var successRates = [];
    """
    
    for iter_data in iterations:
        html += f"""
            iterations.push({iter_data['iteration']});
            feedbackScores.push({iter_data['avg_feedback_score']});
            caseCounts.push({iter_data['current_case_count']});
            casesRetained.push({iter_data['cases_retained']});
            successRates.push({iter_data['success_rate'] * 100});
        """
    
    html += """
            // Feedback score plot
            var feedbackTrace = {
                x: iterations,
                y: feedbackScores,
                mode: 'lines+markers',
                name: 'Avg Feedback Score',
                line: {color: '#0f766e', width: 3},
                marker: {size: 10, color: '#0f766e'}
            };
            
            var feedbackLayout = {
                title: 'User Satisfaction Over Time',
                xaxis: {title: 'Iteration'},
                yaxis: {title: 'Feedback Score (0-5)', range: [0, 5]},
                hovermode: 'closest',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('feedbackPlot', [feedbackTrace], feedbackLayout, {responsive: true});
            
            // Case growth plot
            var caseTrace = {
                x: iterations,
                y: caseCounts,
                mode: 'lines+markers',
                name: 'Total Cases',
                fill: 'tozeroy',
                line: {color: '#e07a5f', width: 3},
                marker: {size: 10, color: '#e07a5f'}
            };
            
            var caseLayout = {
                title: 'Case Base Size Evolution',
                xaxis: {title: 'Iteration'},
                yaxis: {title: 'Number of Cases'},
                hovermode: 'closest',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('caseGrowthPlot', [caseTrace], caseLayout, {responsive: true});
            
            // Performance plot (dual axis)
            var retentionTrace = {
                x: iterations,
                y: casesRetained,
                type: 'bar',
                name: 'Cases Retained',
                marker: {color: '#0f766e'}
            };
            
            var successTrace = {
                x: iterations,
                y: successRates,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Success Rate (%)',
                yaxis: 'y2',
                line: {color: '#e07a5f', width: 3},
                marker: {size: 10, color: '#e07a5f'}
            };
            
            var performanceLayout = {
                title: 'Retention vs Success Rate',
                xaxis: {title: 'Iteration'},
                yaxis: {title: 'Cases Retained', side: 'left'},
                yaxis2: {
                    title: 'Success Rate (%)',
                    overlaying: 'y',
                    side: 'right',
                    range: [0, 100]
                },
                hovermode: 'x unified',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('performancePlot', [retentionTrace, successTrace], performanceLayout, {responsive: true});
        </script>
    """
    
    # Add static image if exists
    plot_path = Path('data/plots/feedback_evolution.png')
    if plot_path.exists():
        img_data = encode_image_base64(plot_path)
        if img_data:
            html += f"""
        <div class="panel">
            <h2>📊 Static Visualization</h2>
            <div class="plot-container">
                <img src="{img_data}" style="width: 100%; height: auto;" alt="Feedback Evolution">
            </div>
        </div>
            """
    
    html += get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f" Generated: {output_path}")


def generate_complete_cbr_cycle_html(data, output_path):
    """Genera HTML para test de complete CBR cycle."""
    html = get_html_template("Complete CBR Cycle", has_plots=True)
    
    html += """
        <div class="header">
            <h1>♻️ Complete CBR Cycle</h1>
            <p class="subtitle">Full Cycle Testing: Retrieve → Reuse → Revise → Retain</p>
        </div>
    """
    
    summary = data['summary']
    scenarios = data['scenarios']
    
    html += f"""
        <div class="panel">
            <h2>📊 Overall Results</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Scenarios Executed</div>
                    <div class="stat-value">{summary['scenarios_executed']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Initial Cases</div>
                    <div class="stat-value">{summary['initial_cases']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Cases Learned</div>
                    <div class="stat-value positive">{summary['cases_learned']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Final Cases</div>
                    <div class="stat-value">{summary['final_cases']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Similarity</div>
                    <div class="stat-value positive">{summary['avg_retrieval_similarity']:.2%}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Retention Rate</div>
                    <div class="stat-value positive">{summary['retention_rate']:.1%}</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📈 4R Cycle Performance</h2>
            <div class="plot-container">
                <div id="cyclePerformancePlot"></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>🎯 Quality Metrics by Scenario</h2>
            <div class="plot-container">
                <div id="qualityMetricsPlot"></div>
            </div>
        </div>
        
        <script>
            var scenarios = [];
            var topSimilarity = [];
            var avgSimilarity = [];
            var culturalAdapt = [];
            var feedbackScores = [];
    """
    
    for i, scenario in enumerate(scenarios, 1):
        phases = scenario['phases']
        html += f"""
            scenarios.push('Scenario {i}');
            topSimilarity.push({phases['retrieve']['top_similarity']});
            avgSimilarity.push({phases['retrieve']['avg_similarity']});
            culturalAdapt.push({phases['adapt']['cultural_adaptations']});
            feedbackScores.push({phases['retain']['feedback_score']});
        """
    
    html += """
            // Cycle performance - Radar-like stacked bars
            var retrieveTrace = {
                x: scenarios,
                y: topSimilarity,
                name: 'Retrieve Quality',
                type: 'bar',
                marker: {color: '#0f766e'}
            };
            
            var adaptTrace = {
                x: scenarios,
                y: culturalAdapt.map(v => v / 5), // Normalize to 0-1 scale
                name: 'Adapt Intensity',
                type: 'bar',
                marker: {color: '#f59e0b'}
            };
            
            var feedbackTrace = {
                x: scenarios,
                y: feedbackScores.map(v => v / 5), // Normalize to 0-1 scale
                name: 'Retain Quality',
                type: 'bar',
                marker: {color: '#e07a5f'}
            };
            
            var cycleLayout = {
                title: '4R Cycle Phase Performance (Normalized)',
                xaxis: {title: 'Scenario'},
                yaxis: {title: 'Performance Score', range: [0, 1]},
                barmode: 'group',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('cyclePerformancePlot', [retrieveTrace, adaptTrace, feedbackTrace], cycleLayout, {responsive: true});
            
            // Quality metrics - dual axis
            var simTrace = {
                x: scenarios,
                y: avgSimilarity,
                name: 'Avg Similarity',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: '#0f766e', width: 3},
                marker: {size: 10},
                yaxis: 'y1'
            };
            
            var feedbackLineTrace = {
                x: scenarios,
                y: feedbackScores,
                name: 'Feedback Score',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: '#e07a5f', width: 3},
                marker: {size: 10},
                yaxis: 'y2'
            };
            
            var qualityLayout = {
                title: 'Similarity vs Feedback Across Scenarios',
                xaxis: {title: 'Scenario'},
                yaxis: {
                    title: 'Similarity Score',
                    titlefont: {color: '#0f766e'},
                    tickfont: {color: '#0f766e'},
                    range: [0, 1]
                },
                yaxis2: {
                    title: 'Feedback Score',
                    titlefont: {color: '#e07a5f'},
                    tickfont: {color: '#e07a5f'},
                    overlaying: 'y',
                    side: 'right',
                    range: [0, 5]
                },
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('qualityMetricsPlot', [simTrace, feedbackLineTrace], qualityLayout, {responsive: true});
        </script>
    """
    
    # Individual scenarios
    for i, scenario in enumerate(scenarios, 1):
        phases = scenario['phases']
        html += f"""
        <div class="panel">
            <h2>Scenario {i}: {scenario['description']}</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">📥 Retrieved Cases</div>
                    <div class="stat-value">{phases['retrieve']['cases_found']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">🎯 Top Similarity</div>
                    <div class="stat-value positive">{phases['retrieve']['top_similarity']:.2%}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">🔄 Menus Adapted</div>
                    <div class="stat-value">{phases['adapt']['menus_adapted']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label"> Valid Proposals</div>
                    <div class="stat-value">{phases['revise']['valid_proposals']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">💾 Retained</div>
                    <div class="stat-value">{'✓' if phases['retain']['retained'] else '✗'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">⭐ Feedback</div>
                    <div class="stat-value positive">{phases['retain']['feedback_score']:.1f}/5</div>
                </div>
            </div>
            <div class="alert info">
                <strong>Retention Action:</strong> {phases['retain']['retention_action'].replace('_', ' ').title()}
            </div>
        </div>
        """
    
    html += get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f" Generated: {output_path}")


def generate_negative_cases_html(data, output_path):
    """Genera HTML para test de negative cases."""
    html = get_html_template("Negative Cases Learning", has_plots=True)
    
    html += """
        <div class="header">
            <h1>⚠ Negative Cases Learning</h1>
            <p class="subtitle">Learning from Failures: Negative Case Management</p>
        </div>
    """
    
    summary = data['summary']
    scenarios = data['scenarios']
    
    html += f"""
        <div class="panel">
            <h2>📊 Summary Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Initial Cases</div>
                    <div class="stat-value">{summary['initial_total_cases']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Final Cases</div>
                    <div class="stat-value">{summary['final_total_cases']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Negative Cases Created</div>
                    <div class="stat-value warning">{summary['negative_cases_added']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Warning System</div>
                    <div class="stat-value positive">{'✓ Functional' if summary['warning_system_functional'] else '✗ Failed'}</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📈 Case Base Evolution</h2>
            <div class="plot-container">
                <div id="caseEvolutionPlot"></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>⚠ Feedback Distribution</h2>
            <div class="plot-container">
                <div id="feedbackDistPlot"></div>
            </div>
        </div>
        
        <script>
            // Case base evolution
            var caseTypes = ['Positive/Neutral', 'Negative'];
            var initialCounts = [{summary['initial_total_cases'] - summary['initial_negative_cases']}, {summary['initial_negative_cases']}];
            var finalCounts = [{summary['final_total_cases'] - summary['final_negative_cases']}, {summary['final_negative_cases']}];
            
            var initialTrace = {{
                x: caseTypes,
                y: initialCounts,
                name: 'Initial',
                type: 'bar',
                marker: {{color: '#5b6474'}}
            }};
            
            var finalTrace = {{
                x: caseTypes,
                y: finalCounts,
                name: 'Final',
                type: 'bar',
                marker: {{color: '#e07a5f'}}
            }};
            
            var evolutionLayout = {{
                title: 'Case Base Composition: Before vs After',
                xaxis: {{title: 'Case Type'}},
                yaxis: {{title: 'Number of Cases'}},
                barmode: 'group',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {{family: '-apple-system, BlinkMacSystemFont, sans-serif'}}
            }};
            
            Plotly.newPlot('caseEvolutionPlot', [initialTrace, finalTrace], evolutionLayout, {{responsive: true}});
            
            // Feedback distribution
            var feedbackScenarios = [];
            var feedbackValues = [];
            var feedbackColors = [];
    """
    
    for scenario in scenarios:
        if 'feedback' in scenario:
            feedback = scenario['feedback']
            score = feedback['score']
            scenario_name = scenario['scenario_id'].replace('_', ' ').title()
            html += f"""
            feedbackScenarios.push('{scenario_name}');
            feedbackValues.push({score});
            feedbackColors.push({score} > 3.5 ? '#059669' : {score} > 2.5 ? '#f59e0b' : '#dc2626');
            """
    
    html += """
            var feedbackTrace = {
                x: feedbackScenarios,
                y: feedbackValues,
                type: 'bar',
                marker: {color: feedbackColors},
                text: feedbackValues.map(v => v.toFixed(1) + '/5'),
                textposition: 'outside'
            };
            
            var feedbackLayout = {
                title: 'Feedback Scores by Scenario',
                xaxis: {title: 'Scenario'},
                yaxis: {title: 'Feedback Score', range: [0, 5.5]},
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'},
                shapes: [{
                    type: 'line',
                    x0: -0.5,
                    x1: feedbackScenarios.length - 0.5,
                    y0: 3.5,
                    y1: 3.5,
                    line: {
                        color: '#059669',
                        width: 2,
                        dash: 'dash'
                    }
                }],
                annotations: [{
                    x: feedbackScenarios.length - 0.5,
                    y: 3.5,
                    text: 'Success Threshold',
                    showarrow: false,
                    xanchor: 'left',
                    yanchor: 'bottom'
                }]
            };
            
            Plotly.newPlot('feedbackDistPlot', [feedbackTrace], feedbackLayout, {responsive: true});
        </script>
    """
    
    # Scenarios
    for i, scenario in enumerate(scenarios, 1):
        html += f"""
        <div class="panel">
            <h2>{scenario['scenario_id'].replace('_', ' ').title()}</h2>
            <div class="alert info">
                {scenario['description']}
            </div>
        """
        
        if 'feedback' in scenario:
            feedback = scenario['feedback']
            html += f"""
            <h3>Feedback Results</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Score</div>
                    <div class="stat-value {'positive' if feedback['score'] > 3.5 else 'warning'}">{feedback['score']:.1f}/5</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Success</div>
                    <div class="stat-value">{'✓' if feedback['success'] else '✗'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Retained</div>
                    <div class="stat-value">{'✓' if feedback['retained'] else '✗'}</div>
                </div>
            </div>
            """
            if 'message' in feedback:
                html += f'<div class="alert warning">{feedback["message"]}</div>'
        
        if 'warnings_found' in scenario and scenario['warnings_found'] > 0:
            html += f"""
            <h3>⚠ Warnings Detected: {scenario['warnings_found']}</h3>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Case ID</th>
                        <th>Similarity</th>
                        <th>Feedback Score</th>
                    </tr>
                </thead>
                <tbody>
            """
            for warning in scenario['warning_details']:
                html += f"""
                    <tr>
                        <td><code>{warning['case_id']}</code></td>
                        <td><span class="badge warning">{warning['similarity']:.2%}</span></td>
                        <td><span class="badge warning">{warning['feedback_score']:.1f}/5</span></td>
                    </tr>
                """
            html += """
                </tbody>
            </table>
            """
        
        html += "</div>"
    
    html += get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f" Generated: {output_path}")


def generate_semantic_cultural_html(data, output_path):
    """Genera HTML para test de semantic cultural adaptation."""
    html = get_html_template("Semantic Cultural Adaptation", has_plots=True)
    
    html += """
        <div class="header">
            <h1>🌍 Semantic Cultural Adaptation</h1>
            <p class="subtitle">Cross-Cultural Recipe Adaptation Analysis</p>
        </div>
    """
    
    tests = data.get('test_cases', [])
    summary = data.get('summary', {})
    
    html += f"""
        <div class="panel">
            <h2>📊 Summary Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Cultures Tested</div>
                    <div class="stat-value">{len(tests)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Adaptations</div>
                    <div class="stat-value">{summary.get('total_adaptations', 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Similarity</div>
                    <div class="stat-value">{summary.get('avg_retrieval_similarity', 0):.3f}</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>🎯 Retrieval Quality by Culture</h2>
            <div class="plot-container">
                <div id="retrievalQualityPlot"></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>🔧 Adaptation Intensity</h2>
            <div class="plot-container">
                <div id="adaptationPlot"></div>
            </div>
        </div>
        
        <script>
            var cultures = [];
            var topSim = [];
            var avgSim = [];
            var adaptations = [];
            var substitutions = [];
            var replacements = [];
    """
    
    for test in tests:
        culture = test.get('target_culture', 'unknown')
        retrieval = test.get('retrieval', {})
        adaptation = test.get('adaptation', {})
        
        html += f"""
            cultures.push('{culture}');
            topSim.push({retrieval.get('top_similarity', 0)});
            avgSim.push({retrieval.get('avg_similarity', 0)});
            adaptations.push({adaptation.get('cultural_adaptations_applied', 0)});
            substitutions.push({adaptation.get('ingredient_substitutions', 0)});
            replacements.push({adaptation.get('dish_replacements', 0)});
        """
    
    html += """
            // Retrieval quality
            var topSimTrace = {
                x: cultures,
                y: topSim,
                name: 'Top Match',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: '#0f766e', width: 3},
                marker: {size: 10}
            };
            
            var avgSimTrace = {
                x: cultures,
                y: avgSim,
                name: 'Avg of Top 5',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: '#e07a5f', width: 3},
                marker: {size: 10}
            };
            
            var retrievalLayout = {
                title: 'Semantic Similarity in Retrieval Phase',
                xaxis: {title: 'Target Culture'},
                yaxis: {title: 'Similarity Score', range: [0, 1]},
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('retrievalQualityPlot', [topSimTrace, avgSimTrace], retrievalLayout, {responsive: true});
            
            // Adaptation intensity
            var adaptTrace = {
                x: cultures,
                y: adaptations,
                name: 'Cultural Adaptations',
                type: 'bar',
                marker: {color: '#0f766e'}
            };
            
            var substTrace = {
                x: cultures,
                y: substitutions,
                name: 'Ingredient Substitutions',
                type: 'bar',
                marker: {color: '#f59e0b'}
            };
            
            var replaceTrace = {
                x: cultures,
                y: replacements,
                name: 'Dish Replacements',
                type: 'bar',
                marker: {color: '#e07a5f'}
            };
            
            var adaptLayout = {
                title: 'Adaptation Operations Applied',
                xaxis: {title: 'Target Culture'},
                yaxis: {title: 'Number of Operations'},
                barmode: 'stack',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('adaptationPlot', [adaptTrace, substTrace, replaceTrace], adaptLayout, {responsive: true});
        </script>
    """
    
    # Details per culture
    for i, test in enumerate(tests, 1):
        culture = test.get('target_culture', 'Unknown')
        retrieval = test.get('retrieval', {})
        adaptation = test.get('adaptation', {})
        
        html += f"""
        <div class="panel">
            <h2>{culture} Adaptation Details</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Top Similarity</div>
                    <div class="stat-value">{retrieval.get('top_similarity', 0):.3f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Adaptations</div>
                    <div class="stat-value">{adaptation.get('cultural_adaptations_applied', 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Menu Price</div>
                    <div class="stat-value">€{adaptation.get('total_price', 0):.2f}</div>
                </div>
            </div>
        </div>
        """
    
    html += get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f" Generated: {output_path}")


def generate_semantic_retain_html(data, output_path):
    """Genera HTML para test de semantic retain."""
    html = get_html_template("Semantic Retain", has_plots=True)
    
    html += """
        <div class="header">
            <h1>💾 Semantic Retain</h1>
            <p class="subtitle">Case Base Retention and Update Strategies</p>
        </div>
    """
    
    tests = data.get('test_cases', [])
    summary = data.get('summary', {})
    
    html += f"""
        <div class="panel">
            <h2>📊 Retention Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Initial Cases</div>
                    <div class="stat-value">{summary.get('initial_cases', 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Final Cases</div>
                    <div class="stat-value">{summary.get('final_cases', 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Retention Rate</div>
                    <div class="stat-value">{summary.get('retention_rate', 0)*100:.0f}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Cases Added</div>
                    <div class="stat-value positive">+{summary.get('final_cases', 0) - summary.get('initial_cases', 0)}</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>🔄 Retention Actions Distribution</h2>
            <div class="plot-container">
                <div id="actionsPlot"></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📈 Case Base Growth</h2>
            <div class="plot-container">
                <div id="growthPlot"></div>
            </div>
        </div>
        
        <script>
            var testNames = [];
            var actions = [];
            var actionColors = {{
                'add_new': '#059669',
                'update_existing': '#f59e0b',
                'reject': '#dc2626'
            }};
    """
    
    for i, test in enumerate(tests, 1):
        decision = test.get('decision', {})
        action = decision.get('action', 'unknown')
        html += f"""
            testNames.push('Test {i}');
            actions.push({{action: '{action}', color: actionColors['{action}'] || '#5b6474'}});
        """
    
    html += """
            // Actions pie chart
            var actionCounts = {};
            actions.forEach(a => {
                actionCounts[a.action] = (actionCounts[a.action] || 0) + 1;
            });
            
            var pieTrace = {
                labels: Object.keys(actionCounts).map(k => k.replace('_', ' ').toUpperCase()),
                values: Object.values(actionCounts),
                type: 'pie',
                marker: {
                    colors: Object.keys(actionCounts).map(k => actionColors[k])
                },
                textinfo: 'label+percent',
                textposition: 'outside'
            };
            
            var pieLayout = {
                title: 'Retention Strategy Distribution',
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {family: '-apple-system, BlinkMacSystemFont, sans-serif'}
            };
            
            Plotly.newPlot('actionsPlot', [pieTrace], pieLayout, {responsive: true});
            
            // Growth visualization
    """
    
    initial = summary.get('initial_cases', 0)
    final = summary.get('final_cases', 0)
    
    html += f"""
            var growthTrace = {{
                x: ['Initial', 'Final'],
                y: [{initial}, {final}],
                type: 'bar',
                marker: {{
                    color: ['#5b6474', '#0f766e']
                }},
                text: [{initial}, {final}],
                textposition: 'outside'
            }};
            
            var growthLayout = {{
                title: 'Case Base Size Evolution',
                xaxis: {{title: 'State'}},
                yaxis: {{title: 'Number of Cases'}},
                plot_bgcolor: '#faf7f1',
                paper_bgcolor: '#ffffff',
                font: {{family: '-apple-system, BlinkMacSystemFont, sans-serif'}}
            }};
            
            Plotly.newPlot('growthPlot', [growthTrace], growthLayout, {{responsive: true}});
        </script>
    """
    
    # Individual test details
    for i, test in enumerate(tests, 1):
        decision = test.get('decision', {})
        action = decision.get('action', 'unknown')
        retained = decision.get('retained', False)
        
        html += f"""
        <div class="panel">
            <h2>Test {i}: {test.get('description', 'N/A')}</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Culture</div>
                    <div class="stat-value">{test.get('menu_culture', 'N/A')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Action</div>
                    <div class="stat-value {'positive' if retained else 'warning'}">{action.replace('_', ' ').title()}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Retained</div>
                    <div class="stat-value">{'✓' if retained else '✗'}</div>
                </div>
            </div>
            <div class="alert info">
                <strong>Reason:</strong> {decision.get('reason', 'N/A')}
            </div>
        </div>
        """
    
    html += get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f" Generated: {output_path}")


def generate_index_html(htmls_dir):
    """Genera un index.html con enlaces a todos los reportes."""
    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CBR Test Reports - Index</title>
    <style>
        :root {
            --surface: #ffffff;
            --ink: #0f172a;
            --muted: #5b6474;
            --accent: #0f766e;
            --accent-2: #e07a5f;
            --line: #e1dacf;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #faf7f1 0%, #f5f0e8 100%);
            color: var(--ink);
            padding: 40px 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 60px;
        }
        
        h1 {
            font-size: 3em;
            color: var(--accent);
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: var(--muted);
            font-size: 1.2em;
        }
        
        .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
        }
        
        .report-card {
            background: var(--surface);
            border-radius: 18px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            text-decoration: none;
            color: var(--ink);
            display: block;
        }
        
        .report-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        
        .report-card h2 {
            color: var(--accent);
            margin-bottom: 10px;
            font-size: 1.5em;
        }
        
        .report-card p {
            color: var(--muted);
            line-height: 1.6;
        }
        
        .icon {
            font-size: 2.5em;
            margin-bottom: 15px;
            display: block;
        }
        
        .category {
            margin-bottom: 50px;
        }
        
        .category h2 {
            color: var(--accent-2);
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 3px solid var(--line);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 CBR Test Reports</h1>
            <p class="subtitle">Interactive Visual Reports for Case-Based Reasoning System</p>
        </header>
        
        <div class="category">
            <h2>🎯 Learning & Adaptation</h2>
            <div class="reports-grid">
                <a href="report_adaptive_weights.html" class="report-card">
                    <span class="icon">⚖️</span>
                    <h2>Adaptive Weights</h2>
                    <p>Static vs Adaptive weight learning comparison with performance metrics</p>
                </a>
                
                <a href="report_adaptive_learning.html" class="report-card">
                    <span class="icon">📈</span>
                    <h2>Adaptive Learning</h2>
                    <p>Learning system performance: precision, satisfaction, and time overhead</p>
                </a>
                
                <a href="report_user_simulation.html" class="report-card">
                    <span class="icon">👥</span>
                    <h2>User Simulation</h2>
                    <p>Multi-user interactions with feedback evolution and retention analysis</p>
                </a>
            </div>
        </div>
        
        <div class="category">
            <h2>🔄 CBR Cycle</h2>
            <div class="reports-grid">
                <a href="report_complete_cbr_cycle.html" class="report-card">
                    <span class="icon">♻️</span>
                    <h2>Complete CBR Cycle</h2>
                    <p>Full 4R cycle (Retrieve, Reuse, Revise, Retain) across scenarios</p>
                </a>
                
                <a href="report_semantic_retrieve.html" class="report-card">
                    <span class="icon">🔍</span>
                    <h2>Semantic Retrieve</h2>
                    <p>Case retrieval with similarity scores and rankings</p>
                </a>
                
                <a href="report_semantic_retain.html" class="report-card">
                    <span class="icon">💾</span>
                    <h2>Semantic Retain</h2>
                    <p>Case retention strategies and learning integration</p>
                </a>
            </div>
        </div>
        
        <div class="category">
            <h2>🌍 Cultural & Edge Cases</h2>
            <div class="reports-grid">
                <a href="report_semantic_cultural_adaptation.html" class="report-card">
                    <span class="icon">🌏</span>
                    <h2>Cultural Adaptation</h2>
                    <p>Cross-cultural recipe adaptations and ingredient substitutions</p>
                </a>
                
                <a href="report_negative_cases.html" class="report-card">
                    <span class="icon">⚠</span>
                    <h2>Negative Cases</h2>
                    <p>Failure learning and negative feedback handling</p>
                </a>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    with open(htmls_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html)


def generate_test_html(master_report=None, verbose=True):
    """
    Genera todos los reportes HTML.
    Esta es la interfaz llamada desde run_tests.py.
    
    Args:
        master_report: Reporte maestro (no usado actualmente, genera desde JSONs)
        verbose: Si imprimir mensajes de progreso
    """
    results_dir = Path('data/results')
    htmls_dir = Path('data/htmls')
    htmls_dir.mkdir(exist_ok=True)
    
    if verbose:
        print("📄 Generating visual HTML reports...")
    
    generators = {
        'test_adaptive_weights.json': ('report_adaptive_weights.html', generate_adaptive_weights_html),
        'test_adaptive_learning.json': ('report_adaptive_learning.html', generate_adaptive_learning_html),
        'test_semantic_retrieve.json': ('report_semantic_retrieve.html', generate_semantic_retrieve_html),
        'test_user_simulation.json': ('report_user_simulation.html', generate_user_simulation_html),
        'test_complete_cbr_cycle.json': ('report_complete_cbr_cycle.html', generate_complete_cbr_cycle_html),
        'test_negative_cases.json': ('report_negative_cases.html', generate_negative_cases_html),
        'test_semantic_cultural_adaptation.json': ('report_semantic_cultural_adaptation.html', generate_semantic_cultural_html),
        'test_semantic_retain.json': ('report_semantic_retain.html', generate_semantic_retain_html),
    }
    
    generated = 0
    for json_file, (html_file, generator_func) in generators.items():
        json_path = results_dir / json_file
        if json_path.exists():
            data = load_json(json_path)
            generator_func(data, htmls_dir / html_file)
            generated += 1
            if verbose:
                print(f"    {html_file}")
        elif verbose:
            print(f"   ⏭️  Skipped {json_file} (not found)")
    
    # Generate index.html
    generate_index_html(htmls_dir)
    
    if verbose:
        print(f"\n   Generated {generated} HTML reports in {htmls_dir}/")


def main():
    """Genera todos los reportes HTML (modo standalone)."""
    results_dir = Path('data/results')
    htmls_dir = Path('data/htmls')
    htmls_dir.mkdir(exist_ok=True)
    
    print("🚀 Generating enhanced HTML reports...\n")
    
    generators = {
        'test_adaptive_weights.json': ('report_adaptive_weights.html', generate_adaptive_weights_html),
        'test_adaptive_learning.json': ('report_adaptive_learning.html', generate_adaptive_learning_html),
        'test_semantic_retrieve.json': ('report_semantic_retrieve.html', generate_semantic_retrieve_html),
        'test_user_simulation.json': ('report_user_simulation.html', generate_user_simulation_html),
        'test_complete_cbr_cycle.json': ('report_complete_cbr_cycle.html', generate_complete_cbr_cycle_html),
        'test_negative_cases.json': ('report_negative_cases.html', generate_negative_cases_html),
        'test_semantic_cultural_adaptation.json': ('report_semantic_cultural_adaptation.html', generate_semantic_cultural_html),
        'test_semantic_retain.json': ('report_semantic_retain.html', generate_semantic_retain_html),
    }
    
    for json_file, (html_file, generator_func) in generators.items():
        json_path = results_dir / json_file
        if json_path.exists():
            data = load_json(json_path)
            generator_func(data, htmls_dir / html_file)
        else:
            print(f"⚠  Skipped {json_file} (not found)")
    
    # Generate index
    generate_index_html(htmls_dir)
    
    print("\n All HTML reports generated successfully!")
    print(f"📁 Location: {htmls_dir.absolute()}")


if __name__ == '__main__':
    main()
