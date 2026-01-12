#!/usr/bin/env python3
"""
Genera plots de progresión de feedback y pesos adaptativos desde simulación LLM.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def plot_learning_progression(learning_file='data/llm_simulation_results_learning.json',
                              results_file='data/llm_simulation_results.json',
                              output_dir='data/plots'):
    """Genera plots de progresión de feedback y pesos."""
    
    # Cargar datos
    with open(learning_file) as f:
        learning_data = json.load(f)
    
    with open(results_file) as f:
        results_data = json.load(f)
    
    history = learning_data['history']
    interactions = results_data['interactions']
    
    # Preparar datos
    iterations = [h['iteration'] for h in history]
    feedback_scores = [h['feedback_score'] for h in history]
    
    # Pesos por dimensión
    weight_keys = ['event_type', 'dietary', 'price_range', 'cultural', 'season']
    weights_over_time = {key: [h['weights'][key] for h in history] for key in weight_keys}
    
    # Crear figura con 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # =====================================================================
    # SUBPLOT 1: Progresión de Feedback del LLM
    # =====================================================================
    ax1.plot(iterations, feedback_scores, 'o-', linewidth=2, markersize=6, color='#0f766e', label='Puntuación LLM')
    
    # Línea de tendencia
    z = np.polyfit(iterations, feedback_scores, 2)
    p = np.poly1d(z)
    ax1.plot(iterations, p(iterations), "--", alpha=0.5, color='#e07a5f', linewidth=2, label='Tendencia')
    
    # Promedio móvil (ventana de 3)
    if len(feedback_scores) >= 3:
        moving_avg = np.convolve(feedback_scores, np.ones(3)/3, mode='valid')
        moving_avg_iter = iterations[1:-1]  # Ajustar índices
        ax1.plot(moving_avg_iter, moving_avg, '-.', alpha=0.7, color='#f4a261', linewidth=2, label='Media móvil (3)')
    
    ax1.set_xlabel('Iteración', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Puntuación LLM (0-5)', fontsize=12, fontweight='bold')
    ax1.set_title('Progresión de Feedback del LLM', fontsize=14, fontweight='bold', pad=20)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='best', fontsize=10)
    ax1.set_ylim([0, 5])
    
    # Agregar anotaciones para puntos clave
    max_idx = feedback_scores.index(max(feedback_scores))
    ax1.annotate(f'Máximo: {max(feedback_scores):.1f}', 
                xy=(iterations[max_idx], feedback_scores[max_idx]),
                xytext=(10, 10), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    # =====================================================================
    # SUBPLOT 2: Evolución de Pesos Adaptativos
    # =====================================================================
    colors = ['#0f766e', '#e07a5f', '#f4a261', '#2a9d8f', '#264653']
    labels = {
        'event_type': 'Tipo de Evento',
        'dietary': 'Restricciones Dietéticas',
        'price_range': 'Rango de Precio',
        'cultural': 'Preferencia Cultural',
        'season': 'Temporada'
    }
    
    for idx, (key, color) in enumerate(zip(weight_keys, colors)):
        ax2.plot(iterations, weights_over_time[key], 'o-', 
                linewidth=2, markersize=5, color=color, label=labels[key], alpha=0.8)
    
    ax2.set_xlabel('Iteración', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Peso de Similitud', fontsize=12, fontweight='bold')
    ax2.set_title('Evolución de Pesos Adaptativos del Sistema CBR', fontsize=14, fontweight='bold', pad=20)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(loc='best', fontsize=10, ncol=2)
    
    # Agregar línea horizontal en el valor inicial para referencia
    for key in weight_keys:
        initial_weight = weights_over_time[key][0]
        ax2.axhline(y=initial_weight, color='gray', linestyle=':', alpha=0.3, linewidth=1)
    
    plt.tight_layout()
    
    # Guardar
    output_path = Path(output_dir) / 'learning_progression.png'
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f'✅ Plot guardado: {output_path}')
    
    plt.close()
    
    # =====================================================================
    # PLOT ADICIONAL: Cambios de pesos entre iteraciones
    # =====================================================================
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Calcular deltas
    for idx, (key, color) in enumerate(zip(weight_keys, colors)):
        weights = weights_over_time[key]
        deltas = [weights[i] - weights[i-1] if i > 0 else 0 for i in range(len(weights))]
        ax.bar([i + idx*0.15 - 0.3 for i in iterations], deltas, 
               width=0.15, color=color, label=labels[key], alpha=0.8)
    
    ax.set_xlabel('Iteración', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cambio de Peso (Δ)', fontsize=12, fontweight='bold')
    ax.set_title('Ajustes de Pesos por Iteración', fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.legend(loc='best', fontsize=10, ncol=3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    
    plt.tight_layout()
    
    output_path2 = Path(output_dir) / 'weight_adjustments.png'
    plt.savefig(output_path2, dpi=300, bbox_inches='tight')
    print(f'✅ Plot guardado: {output_path2}')
    
    plt.close()
    
    # =====================================================================
    # ESTADÍSTICAS FINALES
    # =====================================================================
    print("\n" + "="*70)
    print("ESTADÍSTICAS DE APRENDIZAJE")
    print("="*70)
    print(f"Iteraciones: {len(iterations) - 1}")  # -1 porque incluye inicialización
    print(f"Puntuación inicial: {feedback_scores[1]:.2f}/5.0" if len(feedback_scores) > 1 else "N/A")
    print(f"Puntuación final: {feedback_scores[-1]:.2f}/5.0")
    print(f"Puntuación promedio: {np.mean(feedback_scores[1:]):.2f}/5.0")
    print(f"Mejora total: {feedback_scores[-1] - feedback_scores[1]:.2f}" if len(feedback_scores) > 1 else "N/A")
    
    print("\nCambios de pesos (inicial → final):")
    for key in weight_keys:
        initial = weights_over_time[key][0]
        final = weights_over_time[key][-1]
        change = final - initial
        change_pct = (change / initial) * 100 if initial > 0 else 0
        print(f"  {labels[key]:25s}: {initial:.3f} → {final:.3f} ({change:+.3f}, {change_pct:+.1f}%)")
    print("="*70)


if __name__ == '__main__':
    plot_learning_progression()
