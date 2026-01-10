"""
Test del Learning Rate Scheduler.

Demuestra cómo el learning rate se reduce gradualmente con diferentes estrategias.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).parent))

from develop.core.adaptive_weights import AdaptiveWeightLearner
from develop.core.models import Feedback, Request, EventType, Season

def test_lr_scheduler(scheduler_type: str, iterations: int = 50):
    """
    Test de un tipo específico de scheduler.
    
    Args:
        scheduler_type: 'exponential', 'linear', 'step', o None
        iterations: Número de iteraciones a simular
    """
    print(f"\n{'='*80}")
    print(f"TEST: SCHEDULER '{scheduler_type or 'CONSTANT'}'")
    print(f"{'='*80}")
    
    # Crear learner con scheduler
    learner = AdaptiveWeightLearner(
        learning_rate=0.05,
        lr_scheduler=scheduler_type,
        lr_decay_rate=0.95,  # Para exponential y step
        lr_min=0.001
    )
    
    print(f"\n📊 Configuración:")
    print(f"   Learning rate inicial: {learner.initial_learning_rate:.4f}")
    print(f"   Scheduler: {scheduler_type or 'constant'}")
    print(f"   Decay rate: {learner.lr_decay_rate:.4f}")
    print(f"   LR mínimo: {learner.lr_min:.4f}")
    
    # Simular feedback a lo largo de las iteraciones
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=8,
        season=Season.SPRING,
        required_diets=[],
        price_min=40.0,
        price_max=60.0
    )
    
    learning_rates = []
    
    print(f"\n📈 Evolución del learning rate:")
    print(f"{'Iteración':<15} {'Learning Rate':<20} {'Cambio':<15}")
    print("-" * 80)
    
    for i in range(iterations):
        # Simular feedback variable
        score = 3.0 + (i % 3) * 0.5  # Varía entre 3.0 y 4.0
        
        feedback = Feedback(
            overall_satisfaction=score,
            price_satisfaction=score,
            cultural_satisfaction=score,
            flavor_satisfaction=score
        )
        
        old_lr = learner.learning_rate
        learner.update_from_feedback(feedback, request)
        new_lr = learner.learning_rate
        change = new_lr - old_lr
        
        learning_rates.append(new_lr)
        
        # Mostrar cada 5 iteraciones o al final
        if i % 5 == 0 or i == iterations - 1:
            symbol = "↓" if change < 0 else "=" if change == 0 else "↑"
            print(f"{i+1:<15} {new_lr:<20.6f} {change:+.6f} {symbol}")
    
    print(f"\n📉 Resumen:")
    print(f"   LR inicial:  {learning_rates[0]:.6f}")
    print(f"   LR final:    {learning_rates[-1]:.6f}")
    print(f"   Reducción:   {learning_rates[0] - learning_rates[-1]:.6f} ({(1 - learning_rates[-1]/learning_rates[0])*100:.1f}%)")
    
    return learning_rates


def compare_schedulers():
    """Compara visualmente diferentes schedulers."""
    print("\n" + "="*80)
    print("COMPARACIÓN DE SCHEDULERS")
    print("="*80)
    
    iterations = 50
    schedulers = {
        'None (Constant)': None,
        'Exponential': 'exponential',
        'Linear': 'linear',
        'Step': 'step'
    }
    
    all_rates = {}
    
    for name, scheduler_type in schedulers.items():
        rates = test_lr_scheduler(scheduler_type, iterations)
        all_rates[name] = rates
    
    # Crear gráfico de comparación
    print("\n" + "="*80)
    print("GRÁFICO COMPARATIVO")
    print("="*80)
    
    plt.figure(figsize=(12, 6))
    
    for name, rates in all_rates.items():
        plt.plot(range(1, len(rates) + 1), rates, marker='o', markersize=3, label=name, linewidth=2)
    
    plt.xlabel('Iteración', fontsize=12)
    plt.ylabel('Learning Rate', fontsize=12)
    plt.title('Comparación de Learning Rate Schedulers', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_path = 'data/lr_scheduler_comparison.png'
    plt.savefig(output_path, dpi=150)
    print(f"\n✅ Gráfico guardado en: {output_path}")
    
    plt.show()


def test_with_real_scenario():
    """Test con escenario real de aprendizaje."""
    print("\n" + "="*80)
    print("TEST: ESCENARIO REAL CON SCHEDULER EXPONENTIAL")
    print("="*80)
    
    learner = AdaptiveWeightLearner(
        learning_rate=0.05,
        lr_scheduler='exponential',
        lr_decay_rate=0.98,  # Decay más suave
        lr_min=0.005
    )
    
    print(f"\n📊 Configuración:")
    print(f"   Learning rate inicial: {learner.initial_learning_rate:.4f}")
    print(f"   Scheduler: exponential")
    print(f"   Decay rate: {learner.lr_decay_rate:.4f}")
    
    # Simular problemas de precio y cultura
    request_price = Request(
        event_type=EventType.WEDDING,
        num_guests=8,
        season=Season.SPRING,
        required_diets=[],
        price_min=20.0,
        price_max=35.0
    )
    
    request_culture = Request(
        event_type=EventType.WEDDING,
        num_guests=8,
        season=Season.SPRING,
        required_diets=[],
        price_min=40.0,
        price_max=60.0,
        cultural_preference=None
    )
    
    print("\n📝 Simulando 20 iteraciones de aprendizaje...")
    print(f"{'Iter':<8} {'LR':<12} {'Ajuste Precio':<15} {'Ajuste Cultural':<15}")
    print("-" * 80)
    
    for i in range(20):
        # Alternar entre problemas de precio y cultura
        if i % 2 == 0:
            # Problema de precio
            feedback = Feedback(
                overall_satisfaction=2.5,
                price_satisfaction=1.5,
                cultural_satisfaction=4.0,
                flavor_satisfaction=4.0
            )
            request = request_price
        else:
            # Problema de cultura
            feedback = Feedback(
                overall_satisfaction=2.3,
                price_satisfaction=4.0,
                cultural_satisfaction=1.0,
                flavor_satisfaction=3.5
            )
            request = request_culture
        
        old_price = learner.weights.price_range
        old_cultural = learner.weights.cultural
        
        adjustments = learner.update_from_feedback(feedback, request)
        
        new_price = learner.weights.price_range
        new_cultural = learner.weights.cultural
        
        if i % 2 == 0 or i >= 18:  # Mostrar cada 2 o las últimas
            price_change = new_price - old_price
            cultural_change = new_cultural - old_cultural
            print(f"{i+1:<8} {learner.learning_rate:<12.6f} {price_change:+.6f}      {cultural_change:+.6f}")
    
    # Mostrar resumen
    summary = learner.get_learning_summary()
    
    print(f"\n📈 Resumen del aprendizaje:")
    print(f"   Iteraciones totales: {summary['total_iterations']}")
    print(f"   Learning rate final: {summary['learning_rate']['current']:.6f}")
    print(f"   Reducción de LR: {(1 - summary['learning_rate']['current']/summary['learning_rate']['initial'])*100:.1f}%")
    
    print(f"\n📊 Pesos más cambiados:")
    for item in summary['most_changed']:
        print(f"   {item['weight']:<20} {item['change_pct']}")
    
    print("\n✅ BENEFICIO DEL SCHEDULER:")
    print("   - Al inicio: LR alto → ajustes más agresivos")
    print("   - Con tiempo: LR bajo → ajustes más conservadores")
    print("   - Resultado: Convergencia más estable y precisa")


if __name__ == "__main__":
    import os
    os.makedirs('data', exist_ok=True)
    
    # Test con escenario real
    test_with_real_scenario()
    
    print("\n\n")
    input("Presiona ENTER para ver la comparación gráfica de schedulers...")
    
    # Comparación visual
    compare_schedulers()
    
    print("\n" + "="*80)
    print("✅ TESTS COMPLETADOS")
    print("="*80)
    print("\n💡 Para usar el scheduler en tu código:")
    print("   learner = AdaptiveWeightLearner(")
    print("       learning_rate=0.05,")
    print("       lr_scheduler='exponential',  # o 'linear', 'step'")
    print("       lr_decay_rate=0.95,")
    print("       lr_min=0.001")
    print("   )")
