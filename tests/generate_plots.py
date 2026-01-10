#!/usr/bin/env python3
"""
Generador de plots adicionales para visualización de resultados CBR.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_json(filepath):
    """Carga un archivo JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def setup_plot_style():
    """Configura el estilo de los plots."""
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rcParams['figure.facecolor'] = '#faf7f1'
    plt.rcParams['axes.facecolor'] = '#ffffff'
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 10


def plot_cultural_similarity_heatmap():
    """Genera heatmap de similaridad por cultura."""
    try:
        data = load_json('data/results/test_semantic_retrieve.json')
        cultures = []
        top_similarities = []
        avg_similarities = []
        match_counts = []
        
        for test in data.get('cultural_preferences', []):
            cultures.append(test.get('target_culture', 'unknown'))
            metrics = test.get('metrics', {})
            top_similarities.append(metrics.get('top_similarity', 0))
            avg_similarities.append(metrics.get('avg_similarity', 0))
            match_counts.append(metrics.get('exact_cultural_matches', 0))
        
        if not cultures:
            print("⏭️  No hay datos de cultural retrieve")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Similarity scores
        x = np.arange(len(cultures))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, top_similarities, width, label='Top Match', color='#0f766e')
        bars2 = ax1.bar(x + width/2, avg_similarities, width, label='Average Top 5', color='#e07a5f')
        
        ax1.set_xlabel('Cultura')
        ax1.set_ylabel('Similaridad')
        ax1.set_title('Calidad de Recuperación por Cultura', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(cultures, rotation=45, ha='right')
        ax1.legend()
        ax1.set_ylim(0, 1.1)
        ax1.grid(axis='y', alpha=0.3)
        
        # Plot 2: Match counts
        colors = ['#059669' if c == 5 else '#f59e0b' if c >= 3 else '#dc2626' for c in match_counts]
        bars3 = ax2.bar(cultures, match_counts, color=colors)
        
        ax2.set_xlabel('Cultura')
        ax2.set_ylabel('Matches Culturales Exactos (de 5)')
        ax2.set_title('Precisión Cultural en Recuperación', fontsize=12, fontweight='bold')
        ax2.set_xticklabels(cultures, rotation=45, ha='right')
        ax2.set_ylim(0, 6)
        ax2.axhline(y=5, color='#059669', linestyle='--', alpha=0.5, label='Máximo')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('data/plots/cultural_retrieval_quality.png', dpi=150, bbox_inches='tight')
        print("✅ Generado: cultural_retrieval_quality.png")
        plt.close()
        
    except Exception as e:
        print(f"❌ Error en cultural_similarity_heatmap: {e}")


def plot_cbr_cycle_phases():
    """Genera plot de rendimiento por fase del ciclo CBR."""
    try:
        data = load_json('data/results/test_complete_cbr_cycle.json')
        scenarios = data.get('scenarios', [])
        
        if not scenarios:
            print("⏭️  No hay datos de CBR cycle")
            return
        
        scenario_names = [f"Sc. {i+1}" for i in range(len(scenarios))]
        retrieve_quality = []
        adapt_intensity = []
        feedback_scores = []
        
        for scenario in scenarios:
            phases = scenario.get('phases', {})
            retrieve_quality.append(phases.get('retrieve', {}).get('top_similarity', 0))
            adapt_intensity.append(phases.get('adapt', {}).get('cultural_adaptations', 0) / 5)  # Normalizado
            feedback_scores.append(phases.get('retain', {}).get('feedback_score', 0) / 5)  # Normalizado
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(scenario_names))
        width = 0.25
        
        bars1 = ax.bar(x - width, retrieve_quality, width, label='Retrieve (Similarity)', color='#0f766e')
        bars2 = ax.bar(x, adapt_intensity, width, label='Adapt (Intensity)', color='#f59e0b')
        bars3 = ax.bar(x + width, feedback_scores, width, label='Retain (Feedback/5)', color='#e07a5f')
        
        ax.set_xlabel('Escenario')
        ax.set_ylabel('Score Normalizado (0-1)')
        ax.set_title('Rendimiento del Ciclo CBR 4R por Escenario', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_names)
        ax.legend()
        ax.set_ylim(0, 1.1)
        ax.grid(axis='y', alpha=0.3)
        
        # Añadir línea de referencia
        ax.axhline(y=0.7, color='gray', linestyle='--', alpha=0.5, label='Umbral éxito')
        
        plt.tight_layout()
        plt.savefig('data/plots/cbr_cycle_performance.png', dpi=150, bbox_inches='tight')
        print("✅ Generado: cbr_cycle_performance.png")
        plt.close()
        
    except Exception as e:
        print(f"❌ Error en cbr_cycle_phases: {e}")


def plot_adaptation_intensity():
    """Genera plot de intensidad de adaptaciones culturales."""
    try:
        data = load_json('data/results/test_semantic_cultural_adaptation.json')
        test_cases = data.get('test_cases', [])
        
        if not test_cases:
            print("⏭️  No hay datos de cultural adaptation")
            return
        
        cultures = []
        adaptations = []
        substitutions = []
        replacements = []
        similarities = []
        
        for test in test_cases:
            cultures.append(test.get('target_culture', 'unknown'))
            adapt_data = test.get('adaptation', {})
            adaptations.append(adapt_data.get('cultural_adaptations_applied', 0))
            substitutions.append(adapt_data.get('ingredient_substitutions', 0))
            replacements.append(adapt_data.get('dish_replacements', 0))
            
            retrieval = test.get('retrieval', {})
            similarities.append(retrieval.get('top_similarity', 0))
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Stacked adaptations
        x = np.arange(len(cultures))
        
        p1 = ax1.bar(x, adaptations, label='Adaptaciones Culturales', color='#0f766e')
        p2 = ax1.bar(x, substitutions, bottom=adaptations, label='Sustituciones', color='#f59e0b')
        p3 = ax1.bar(x, replacements, bottom=np.array(adaptations)+np.array(substitutions), 
                     label='Reemplazos', color='#e07a5f')
        
        ax1.set_xlabel('Cultura Objetivo')
        ax1.set_ylabel('Número de Operaciones')
        ax1.set_title('Intensidad de Adaptación por Cultura', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(cultures, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Plot 2: Similarity vs Adaptations
        total_adaptations = np.array(adaptations) + np.array(substitutions) + np.array(replacements)
        
        scatter = ax2.scatter(similarities, total_adaptations, s=200, alpha=0.6, c=range(len(cultures)), 
                             cmap='viridis', edgecolors='black', linewidth=1.5)
        
        for i, culture in enumerate(cultures):
            ax2.annotate(culture, (similarities[i], total_adaptations[i]), 
                        fontsize=9, ha='center', va='bottom')
        
        ax2.set_xlabel('Similaridad de Recuperación')
        ax2.set_ylabel('Total de Adaptaciones Necesarias')
        ax2.set_title('Similaridad vs Esfuerzo de Adaptación', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Línea de tendencia
        if len(similarities) > 1:
            z = np.polyfit(similarities, total_adaptations, 1)
            p = np.poly1d(z)
            ax2.plot(similarities, p(similarities), "r--", alpha=0.5, label='Tendencia')
            ax2.legend()
        
        plt.tight_layout()
        plt.savefig('data/plots/adaptation_intensity.png', dpi=150, bbox_inches='tight')
        print("✅ Generado: adaptation_intensity.png")
        plt.close()
        
    except Exception as e:
        print(f"❌ Error en adaptation_intensity: {e}")


def plot_negative_learning():
    """Genera plot de aprendizaje de casos negativos."""
    try:
        data = load_json('data/results/test_negative_cases.json')
        summary = data.get('summary', {})
        scenarios = data.get('scenarios', [])
        
        if not summary:
            print("⏭️  No hay datos de negative cases")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Case base evolution
        categories = ['Casos\nPositivos', 'Casos\nNegativos']
        initial = [
            summary.get('initial_total_cases', 0) - summary.get('initial_negative_cases', 0),
            summary.get('initial_negative_cases', 0)
        ]
        final = [
            summary.get('final_total_cases', 0) - summary.get('final_negative_cases', 0),
            summary.get('final_negative_cases', 0)
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, initial, width, label='Inicial', color='#5b6474')
        bars2 = ax1.bar(x + width/2, final, width, label='Final', color='#e07a5f')
        
        ax1.set_ylabel('Número de Casos')
        ax1.set_title('Evolución de la Base de Casos', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Añadir valores en las barras
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(f'{int(height)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=9)
        
        # Plot 2: Feedback scores
        feedback_data = []
        labels = []
        
        for scenario in scenarios:
            if 'feedback' in scenario:
                score = scenario['feedback'].get('score', 0)
                feedback_data.append(score)
                labels.append(scenario.get('scenario_id', '').replace('_', ' ').title()[:20])
        
        if feedback_data:
            colors = ['#059669' if s > 3.5 else '#f59e0b' if s > 2.5 else '#dc2626' for s in feedback_data]
            bars3 = ax2.bar(range(len(feedback_data)), feedback_data, color=colors)
            
            ax2.set_xlabel('Escenario')
            ax2.set_ylabel('Puntuación de Feedback')
            ax2.set_title('Distribución de Feedback por Escenario', fontsize=12, fontweight='bold')
            ax2.set_xticks(range(len(labels)))
            ax2.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
            ax2.axhline(y=3.5, color='#059669', linestyle='--', alpha=0.5, label='Umbral éxito')
            ax2.legend()
            ax2.set_ylim(0, 5.5)
            ax2.grid(axis='y', alpha=0.3)
            
            # Añadir valores
            for bar in bars3:
                height = bar.get_height()
                ax2.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig('data/plots/negative_learning.png', dpi=150, bbox_inches='tight')
        print("✅ Generado: negative_learning.png")
        plt.close()
        
    except Exception as e:
        print(f"❌ Error en negative_learning: {e}")


def plot_retention_strategies():
    """Genera plot de estrategias de retención."""
    try:
        data = load_json('data/results/test_semantic_retain.json')
        test_cases = data.get('test_cases', [])
        summary = data.get('summary', {})
        
        if not test_cases:
            print("⏭️  No hay datos de retain")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Pie chart de acciones
        actions = {}
        for test in test_cases:
            action = test.get('decision', {}).get('action', 'unknown')
            actions[action] = actions.get(action, 0) + 1
        
        colors_map = {
            'add_new': '#059669',
            'update_existing': '#f59e0b',
            'reject': '#dc2626'
        }
        
        labels = [a.replace('_', ' ').title() for a in actions.keys()]
        sizes = list(actions.values())
        colors = [colors_map.get(a, '#5b6474') for a in actions.keys()]
        
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
               startangle=90, textprops={'fontsize': 10})
        ax1.set_title('Distribución de Estrategias de Retención', fontsize=12, fontweight='bold')
        
        # Plot 2: Bar chart de crecimiento
        initial = summary.get('initial_cases', 0)
        final = summary.get('final_cases', 0)
        
        bars = ax2.bar(['Inicial', 'Final'], [initial, final], color=['#5b6474', '#0f766e'])
        
        ax2.set_ylabel('Número de Casos')
        ax2.set_title('Crecimiento de la Base de Casos', fontsize=12, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        # Añadir valores y delta
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'{int(height)}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Añadir flecha de crecimiento
        delta = final - initial
        ax2.annotate('', xy=(1, final), xytext=(0, initial),
                    arrowprops=dict(arrowstyle='->', color='#e07a5f', lw=2))
        ax2.text(0.5, (initial + final) / 2, f'+{delta}', 
                ha='center', va='center', fontsize=11, color='#e07a5f', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('data/plots/retention_strategies.png', dpi=150, bbox_inches='tight')
        print("✅ Generado: retention_strategies.png")
        plt.close()
        
    except Exception as e:
        print(f"❌ Error en retention_strategies: {e}")


def main():
    """Genera todos los plots adicionales."""
    print("\n🎨 Generando plots adicionales...\n")
    
    # Crear directorio si no existe
    Path('data/plots').mkdir(parents=True, exist_ok=True)
    
    setup_plot_style()
    
    # Generar cada plot
    plot_cultural_similarity_heatmap()
    plot_cbr_cycle_phases()
    plot_adaptation_intensity()
    plot_negative_learning()
    plot_retention_strategies()
    
    print("\n✅ Todos los plots adicionales generados en data/plots/")
    print("\nPlots disponibles:")
    print("  - feedback_evolution.png (existente)")
    print("  - feedback_correlation.png (existente)")
    print("  - weight_evolution.png (existente)")
    print("  - cultural_retrieval_quality.png (nuevo)")
    print("  - cbr_cycle_performance.png (nuevo)")
    print("  - adaptation_intensity.png (nuevo)")
    print("  - negative_learning.png (nuevo)")
    print("  - retention_strategies.png (nuevo)")


if __name__ == '__main__':
    main()
