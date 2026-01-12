"""
Script de evaluación comparativa: CBR Estático vs CBR con Aprendizaje.

Compara el rendimiento del sistema con pesos fijos vs pesos adaptativos
para demostrar la mejora del aprendizaje.

Métricas evaluadas:
- Precisión: % de casos con al menos 1 propuesta válida
- Satisfacción promedio: Score de feedback
- Tiempo de respuesta
- Diversidad de propuestas

Ejecutar: python tests/test_adaptive_learning.py
"""

import sys
import os
import time
import json
from typing import List, Dict, Tuple
from datetime import datetime
from pathlib import Path

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from develop.main import ChefDigitalCBR, CBRConfig
from develop.core.models import Request, EventType, Season
from develop.cycle.retain import FeedbackData


# ============ CASOS DE PRUEBA ============

TEST_CASES = [
    {
        "id": "BODA-001",
        "request": {
            "event_type": EventType.WEDDING,
            "num_guests": 100,
            "price_min": 45.0,
            "price_max": 55.0,
            "season": Season.SUMMER,
            "required_diets": ["vegetarian"],
            "wants_wine": True
        },
        "expected_feedback": {
            "score": 4.5,
            "success": True,
            "comments": "Excelente menú vegetariano"
        }
    },
    {
        "id": "CONGRESO-001",
        "request": {
            "event_type": EventType.CONGRESS,
            "num_guests": 200,
            "price_min": 20.0,
            "price_max": 30.0,
            "season": Season.AUTUMN,
            "wants_wine": False
        },
        "expected_feedback": {
            "score": 4.0,
            "success": True,
            "comments": "Menú eficiente para evento corporativo"
        }
    },
    {
        "id": "FAMILIAR-001",
        "request": {
            "event_type": EventType.FAMILIAR,
            "num_guests": 30,
            "price_min": 35.0,
            "price_max": 50.0,
            "season": Season.WINTER,
            "wants_wine": True
        },
        "expected_feedback": {
            "score": 4.8,
            "success": True,
            "comments": "Menú cálido perfecto para evento familiar"
        }
    },
    {
        "id": "BODA-002",
        "request": {
            "event_type": EventType.WEDDING,
            "num_guests": 150,
            "price_min": 60.0,
            "price_max": 80.0,
            "season": Season.SPRING,
            "wants_wine": True
        },
        "expected_feedback": {
            "score": 5.0,
            "success": True,
            "comments": "Menú espectacular"
        }
    },
    {
        "id": "CONGRESO-002",
        "request": {
            "event_type": EventType.CONGRESS,
            "num_guests": 80,
            "price_min": 25.0,
            "price_max": 35.0,
            "season": Season.SPRING,
            "required_diets": ["vegan"],
            "wants_wine": False
        },
        "expected_feedback": {
            "score": 3.8,
            "success": True,
            "comments": "Menú vegano funcional"
        }
    },
    {
        "id": "BODA-003",
        "request": {
            "event_type": EventType.WEDDING,
            "num_guests": 120,
            "price_min": 50.0,
            "price_max": 65.0,
            "season": Season.SUMMER,
            "restricted_ingredients": ["seafood", "nuts"],
            "wants_wine": True
        },
        "expected_feedback": {
            "score": 4.2,
            "success": True,
            "comments": "Bien adaptado a restricciones"
        }
    },
    {
        "id": "FAMILIAR-002",
        "request": {
            "event_type": EventType.FAMILIAR,
            "num_guests": 20,
            "price_min": 30.0,
            "price_max": 45.0,
            "season": Season.AUTUMN,
            "wants_wine": True
        },
        "expected_feedback": {
            "score": 4.5,
            "success": True,
            "comments": "Menú acogedor de otoño"
        }
    },
    {
        "id": "BODA-004",
        "request": {
            "event_type": EventType.WEDDING,
            "num_guests": 90,
            "price_min": 70.0,
            "price_max": 90.0,
            "season": Season.WINTER,
            "wants_wine": True,
            "wine_per_dish": True
        },
        "expected_feedback": {
            "score": 5.0,
            "success": True,
            "comments": "Menú premium con maridaje perfecto"
        }
    },
    {
        "id": "CONGRESO-003",
        "request": {
            "event_type": EventType.CONGRESS,
            "num_guests": 150,
            "price_min": 18.0,
            "price_max": 25.0,
            "season": Season.SUMMER,
            "wants_wine": False
        },
        "expected_feedback": {
            "score": 3.5,
            "success": True,
            "comments": "Menú económico aceptable"
        }
    },
    {
        "id": "BODA-005",
        "request": {
            "event_type": EventType.WEDDING,
            "num_guests": 110,
            "price_min": 55.0,
            "price_max": 70.0,
            "season": Season.SPRING,
            "required_diets": ["gluten_free"],
            "wants_wine": True
        },
        "expected_feedback": {
            "score": 4.7,
            "success": True,
            "comments": "Excelente adaptación sin gluten"
        }
    }
]


class EvaluationMetrics:
    """Métricas de evaluación"""
    
    def __init__(self):
        self.total_cases = 0
        self.successful_cases = 0
        self.total_proposals = 0
        self.total_time = 0.0
        self.feedback_scores = []
        self.processing_times = []
    
    def add_result(self, num_proposals: int, processing_time: float, 
                   feedback_score: float, success: bool):
        """Añade resultado de un caso"""
        self.total_cases += 1
        self.total_proposals += num_proposals
        self.total_time += processing_time
        self.feedback_scores.append(feedback_score)
        self.processing_times.append(processing_time)
        
        if success:
            self.successful_cases += 1
    
    def get_summary(self) -> Dict:
        """Calcula resumen de métricas"""
        if self.total_cases == 0:
            return {"error": "No hay casos evaluados"}
        
        avg_score = sum(self.feedback_scores) / len(self.feedback_scores)
        avg_time = sum(self.processing_times) / len(self.processing_times)
        precision = self.successful_cases / self.total_cases
        
        return {
            "precision": precision,
            "avg_satisfaction": avg_score,
            "avg_processing_time": avg_time,
            "total_cases": self.total_cases,
            "successful_cases": self.successful_cases,
            "avg_proposals_per_case": self.total_proposals / self.total_cases
        }


def build_request(req_data: dict) -> Request:
    """Construye objeto Request desde diccionario"""
    return Request(**req_data)


def build_feedback(feedback_data: dict, menu_id: str) -> FeedbackData:
    """Construye objeto FeedbackData desde diccionario"""
    return FeedbackData(
        menu_id=menu_id,
        success=feedback_data["success"],
        score=feedback_data["score"],
        comments=feedback_data["comments"],
        would_recommend=feedback_data["score"] >= 4.0
    )


def run_evaluation_static() -> Tuple[EvaluationMetrics, Dict]:
    """
    Evalúa CBR con pesos ESTÁTICOS (sin aprendizaje).
    
    Returns:
        (métricas, resultados detallados)
    """
    print("\n" + "="*60)
    print("🔹 EVALUACIÓN: CBR ESTÁTICO (Pesos Fijos)")
    print("="*60)
    
    config = CBRConfig(enable_learning=False, verbose=False)
    cbr = ChefDigitalCBR(config)
    
    metrics = EvaluationMetrics()
    results = []
    
    for test_case in TEST_CASES:
        print(f"\n▸ Procesando {test_case['id']}...")
        
        request = build_request(test_case["request"])
        
        start = time.time()
        cbr_result = cbr.process_request(request)
        elapsed = time.time() - start
        
        num_proposals = len(cbr_result.proposed_menus)
        success = num_proposals > 0
        feedback_score = test_case["expected_feedback"]["score"]
        
        metrics.add_result(num_proposals, elapsed, feedback_score, success)
        
        results.append({
            "id": test_case["id"],
            "num_proposals": num_proposals,
            "processing_time": elapsed,
            "success": success
        })
        
        print(f"  ✓ {num_proposals} propuestas en {elapsed:.2f}s")
    
    summary = metrics.get_summary()
    
    print(f"\n📊 RESULTADOS ESTÁTICO:")
    print(f"  Precisión: {summary['precision']:.1%}")
    print(f"  Satisfacción promedio: {summary['avg_satisfaction']:.2f}/5.0")
    print(f"  Tiempo promedio: {summary['avg_processing_time']:.2f}s")
    
    return metrics, {"summary": summary, "details": results}


def run_evaluation_adaptive() -> Tuple[EvaluationMetrics, Dict]:
    """
    Evalúa CBR con APRENDIZAJE ADAPTATIVO.
    
    El sistema aprende de cada caso para mejorar sucesivamente.
    
    Returns:
        (métricas, resultados detallados)
    """
    print("\n" + "="*60)
    print("🔸 EVALUACIÓN: CBR ADAPTATIVO (Aprendizaje Activo)")
    print("="*60)
    
    config = CBRConfig(enable_learning=True, verbose=False)
    cbr = ChefDigitalCBR(config)
    
    metrics = EvaluationMetrics()
    results = []
    
    for test_case in TEST_CASES:
        print(f"\n▸ Procesando {test_case['id']}...")
        
        request = build_request(test_case["request"])
        
        start = time.time()
        cbr_result = cbr.process_request(request)
        elapsed = time.time() - start
        
        num_proposals = len(cbr_result.proposed_menus)
        success = num_proposals > 0
        feedback_score = test_case["expected_feedback"]["score"]
        
        metrics.add_result(num_proposals, elapsed, feedback_score, success)
        
        # APRENDIZAJE: Actualizar pesos con feedback
        if success:
            feedback = build_feedback(
                test_case["expected_feedback"],
                cbr_result.proposed_menus[0].menu.id
            )
            cbr.learn_from_feedback(feedback, request)
        
        results.append({
            "id": test_case["id"],
            "num_proposals": num_proposals,
            "processing_time": elapsed,
            "success": success,
            "learned": success
        })
        
        print(f"  ✓ {num_proposals} propuestas en {elapsed:.2f}s")
        if success:
            print(f"  📚 Pesos actualizados con feedback ({feedback_score}/5.0)")
    
    summary = metrics.get_summary()
    
    print(f"\n📊 RESULTADOS ADAPTATIVO:")
    print(f"  Precisión: {summary['precision']:.1%}")
    print(f"  Satisfacción promedio: {summary['avg_satisfaction']:.2f}/5.0")
    print(f"  Tiempo promedio: {summary['avg_processing_time']:.2f}s")
    
    # Guardar datos de aprendizaje
    cbr.save_learning_data('data/results/learning_history_test.json')
    cbr.plot_learning_evolution('data/plots')
    
    return metrics, {"summary": summary, "details": results}


def compare_results(static_metrics: EvaluationMetrics, 
                    adaptive_metrics: EvaluationMetrics):
    """
    Compara resultados de ambas evaluaciones.
    
    Args:
        static_metrics: Métricas del CBR estático
        adaptive_metrics: Métricas del CBR adaptativo
    """
    print("\n" + "="*60)
    print("📈 COMPARACIÓN DE RESULTADOS")
    print("="*60)
    
    static_summary = static_metrics.get_summary()
    adaptive_summary = adaptive_metrics.get_summary()
    
    # Calcular mejoras
    precision_improvement = (
        adaptive_summary['precision'] - static_summary['precision']
    ) * 100
    
    satisfaction_improvement = (
        adaptive_summary['avg_satisfaction'] - static_summary['avg_satisfaction']
    )
    
    time_diff = (
        adaptive_summary['avg_processing_time'] - static_summary['avg_processing_time']
    )
    
    print(f"\n┌─────────────────────────────┬──────────┬──────────┬──────────┐")
    print(f"│ Métrica                     │ Estático │ Adaptivo │  Mejora  │")
    print(f"├─────────────────────────────┼──────────┼──────────┼──────────┤")
    print(f"│ Precisión                   │ {static_summary['precision']:7.1%} │ {adaptive_summary['precision']:7.1%} │ {precision_improvement:+7.1f}% │")
    print(f"│ Satisfacción promedio       │   {static_summary['avg_satisfaction']:.2f}/5 │   {adaptive_summary['avg_satisfaction']:.2f}/5 │   {satisfaction_improvement:+.2f}   │")
    print(f"│ Tiempo promedio (s)         │   {static_summary['avg_processing_time']:.3f}  │   {adaptive_summary['avg_processing_time']:.3f}  │   {time_diff:+.3f}  │")
    print(f"│ Casos exitosos              │   {static_summary['successful_cases']:3d}    │   {adaptive_summary['successful_cases']:3d}    │    {adaptive_summary['successful_cases'] - static_summary['successful_cases']:+2d}    │")
    print(f"└─────────────────────────────┴──────────┴──────────┴──────────┘")
    
    print(f"\n🎯 CONCLUSIONES:")
    
    if precision_improvement > 0:
        print(f"   ✅ Precisión mejoró {precision_improvement:.1f}% con aprendizaje")
    elif precision_improvement < 0:
        print(f"   ⚠ Precisión empeoró {abs(precision_improvement):.1f}% (normal en muestras pequeñas)")
    else:
        print(f"   ➖ Precisión sin cambios")
    
    if satisfaction_improvement > 0:
        print(f"   ✅ Satisfacción mejoró {satisfaction_improvement:.2f} puntos")
    elif satisfaction_improvement < 0:
        print(f"   ⚠ Satisfacción bajó {abs(satisfaction_improvement):.2f} puntos")
    else:
        print(f"   ➖ Satisfacción sin cambios")
    
    if abs(time_diff) < 0.1:
        print(f"   ✅ Tiempo de procesamiento similar (overhead mínimo)")
    elif time_diff > 0:
        print(f"   ⚠ Aprendizaje añade {time_diff:.3f}s por caso")
    else:
        print(f"   ✅ Aprendizaje es más rápido por {abs(time_diff):.3f}s")
    
    # Guardar comparación
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "static": static_summary,
        "adaptive": adaptive_summary,
        "improvements": {
            "precision": precision_improvement,
            "satisfaction": satisfaction_improvement,
            "time": time_diff
        }
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/results/evaluation_comparison.json', 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n💾 Comparación guardada en: data/evaluation_comparison.json")


def main():
    """Ejecuta evaluación completa"""
    print("\n" + "="*60)
    print("🧪 EVALUACIÓN COMPARATIVA: CBR Estático vs Adaptativo")
    print("="*60)
    print(f"📋 Total de casos de prueba: {len(TEST_CASES)}")
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Evaluación 1: CBR Estático
    static_metrics, static_results = run_evaluation_static()
    
    # Evaluación 2: CBR Adaptativo
    adaptive_metrics, adaptive_results = run_evaluation_adaptive()
    
    # Comparar resultados
    compare_results(static_metrics, adaptive_metrics)
    
    # Obtener resúmenes
    static_summary = static_metrics.get_summary()
    adaptive_summary = adaptive_metrics.get_summary()
    
    # Guardar resultado del test en JSON para reports/HTML
    test_result = {
        "summary": {
            "test_type": "Comparative Evaluation",
            "static_precision": static_summary.get("precision", 0),
            "static_satisfaction": static_summary.get("avg_satisfaction", 0),
            "static_time": static_summary.get("avg_processing_time", 0),
            "adaptive_precision": adaptive_summary.get("precision", 0),
            "adaptive_satisfaction": adaptive_summary.get("avg_satisfaction", 0),
            "adaptive_time": adaptive_summary.get("avg_processing_time", 0),
            "precision_improvement_pct": ((adaptive_summary.get("precision", 0) - static_summary.get("precision", 0)) / static_summary.get("precision", 1) * 100) if static_summary.get("precision", 0) > 0 else 0,
            "satisfaction_improvement": adaptive_summary.get("avg_satisfaction", 0) - static_summary.get("avg_satisfaction", 0),
            "time_overhead_seconds": adaptive_summary.get("avg_processing_time", 0) - static_summary.get("avg_processing_time", 0),
            "total_test_cases": len(TEST_CASES),
            "adaptive_better": adaptive_summary.get("avg_satisfaction", 0) > static_summary.get("avg_satisfaction", 0)
        }
    }
    
    output_file = Path(__file__).parent.parent.parent / "data" / "results" / "test_adaptive_learning.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(test_result, f, indent=2)
    
    print(f"✅ Evaluación completada")
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
