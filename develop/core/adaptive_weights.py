"""
Módulo de aprendizaje adaptativo de pesos de similitud.

Implementa una técnica avanzada de CBR que ajusta dinámicamente
los pesos de las métricas de similitud basándose en el feedback
del usuario.

Algoritmo:
- Ajuste incremental de pesos según satisfacción del cliente
- Normalización automática (suma = 1.0)
- Registro histórico de evolución
- Visualización de aprendizaje

Referencia teórica:
- Wettschereck & Aha (1995): "Weighting Features"
- Stahl & Gabel (2003): "Using Evolution Programs to Learn Local Similarity Measures"
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
from pathlib import Path

from .similarity import SimilarityWeights, DishSimilarityWeights
from .models import Feedback, Request, CulturalTradition, Dish, Menu
from . import knowledge


@dataclass
class WeightAdjustment:
    """Representa un ajuste de peso realizado"""
    timestamp: datetime
    weight_name: str
    delta: float
    reason: str
    feedback_score: float
    

@dataclass
class LearningSnapshot:
    """Snapshot del estado de aprendizaje en un momento"""
    timestamp: datetime
    iteration: int
    weights: Dict[str, float]
    feedback_score: float
    adjustments: List[str]
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para serialización"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'iteration': self.iteration,
            'weights': self.weights,
            'feedback_score': self.feedback_score,
            'adjustments': self.adjustments
        }


class AdaptiveWeightLearner:
    """
    Aprende pesos de similitud mediante feedback del usuario.
    
    Implementa un algoritmo de ajuste incremental que:
    1. Analiza feedback de satisfacción del cliente
    2. Identifica qué criterios fueron más importantes
    3. Ajusta pesos para reflejar preferencias reales
    4. Mantiene historial de aprendizaje
    
    Ejemplo de uso:
        learner = AdaptiveWeightLearner()
        
        # Tras cada caso con feedback
        learner.update_from_feedback(feedback, request)
        
        # Obtener pesos actualizados
        weights = learner.get_current_weights()
        
        # Visualizar evolución
        learner.plot_evolution()
    """
    
    def __init__(
        self, 
        initial_weights: Optional[SimilarityWeights] = None,
        learning_rate: float = 0.05,
        min_weight: float = 0.02,
        max_weight: float = 0.50,
        lr_scheduler: Optional[str] = None,
        lr_decay_rate: float = 0.95,
        lr_min: float = 0.001
    ):
        """
        Inicializa el aprendiz adaptativo.
        
        Args:
            initial_weights: Pesos iniciales (si None, usa defaults)
            learning_rate: Tasa de aprendizaje inicial (0.01-0.1 recomendado)
            min_weight: Peso mínimo permitido
            max_weight: Peso máximo permitido
            lr_scheduler: Tipo de scheduler ('exponential', 'linear', 'step', None)
            lr_decay_rate: Factor de decay (0.9-0.99 recomendado para exponential)
            lr_min: Learning rate mínimo
        """
        # Pesos actuales
        if initial_weights:
            self.weights = initial_weights
        else:
            self.weights = SimilarityWeights()
            self.weights.normalize()
        
        # Parámetros de aprendizaje
        self.initial_learning_rate = learning_rate
        self.learning_rate = learning_rate
        self.min_weight = min_weight
        self.max_weight = max_weight
        
        # Parámetros del scheduler
        self.lr_scheduler = lr_scheduler
        self.lr_decay_rate = lr_decay_rate
        self.lr_min = lr_min
        
        # Historial de aprendizaje
        self.history: List[LearningSnapshot] = []
        self.adjustments_history: List[WeightAdjustment] = []
        
        # Contador de iteraciones
        self.iteration = 0
        
        # Registro inicial
        self._record_snapshot(
            feedback_score=0.0,
            adjustments=["Inicialización con pesos por defecto"]
        )
    
    def update_from_feedback(
        self, 
        feedback: Feedback, 
        request: Request,
        menu: Optional[Menu] = None
    ) -> Dict[str, float]:
        """
        Actualiza pesos basándose en feedback del cliente.
        
        Estrategia de ajuste:
        - Feedback bajo (< 3): Aumentar importancia de criterios no cumplidos
        - Feedback alto (>= 4): Reforzar criterios que funcionaron bien
        - Feedback medio: Ajustes menores
        
        Actualiza TODOS los pesos según reglas del dominio:
        - price_range, cultural, dietary: Basado en satisfacciones específicas
        - event_type: Siempre cuando overall >= 4
        - style: Validado con knowledge.EVENT_STYLES
        - wine_preference: Correlacionado con flavor_satisfaction
        - season: Reforzado con flavor_satisfaction alto
        - guests: Por escala y problemas de cantidad
        
        Args:
            feedback: Feedback del cliente
            request: Request original del caso
            menu: Menú propuesto (opcional, para validar estilos)
            
        Returns:
            Diccionario con los ajustes realizados (para logging)
        """
        self.iteration += 1
        adjustments_made = {}
        reasons = []
        
        overall_satisfaction = feedback.overall_satisfaction
        
        # ===== ANÁLISIS DE FEEDBACK BAJO (Insatisfacción) =====
        if overall_satisfaction < 3:
            # Cliente insatisfecho - identificar qué falló
            
            # 1. Precio fue problema
            if feedback.price_satisfaction < 3:
                delta = 0.10 * self.learning_rate
                adjustments_made['price_range'] = delta
                self._adjust_weight('price_range', delta, 
                                   "Precio fue crítico (satisfacción baja)")
                
                # Reducir criterios secundarios
                adjustments_made['season'] = -0.05 * self.learning_rate
                self._adjust_weight('season', -0.05 * self.learning_rate,
                                   "Reducir importancia de temporada")
                
                reasons.append("Priorizar precio (insatisfacción)")
            
            # 2. Cultura no cumplida
            if (feedback.cultural_satisfaction < 3 and 
                request.cultural_preference):
                delta = 0.08 * self.learning_rate
                adjustments_made['cultural'] = delta
                self._adjust_weight('cultural', delta,
                                   "Cultura fue crítica (no cumplida)")
                
                # Reducir menos críticos
                adjustments_made['guests'] = -0.04 * self.learning_rate
                self._adjust_weight('guests', -0.04 * self.learning_rate,
                                   "Reducir importancia de # invitados")
                
                reasons.append("Priorizar cultura (insatisfacción)")
            
            # 3. Sabor/Calidad problema
            if feedback.flavor_satisfaction < 3:
                # No ajustamos wine_preference aquí porque no podemos determinar
                # si el problema fue el maridaje o los platos en sí
                reasons.append("INFO: Sabor insatisfactorio - revisar en adaptación de platos")
            
            # 4. Dietas no cumplidas
            if feedback.dietary_satisfaction < 3:
                delta = 0.12 * self.learning_rate  # Muy importante
                adjustments_made['dietary'] = delta
                self._adjust_weight('dietary', delta,
                                   "Dietas no cumplidas (crítico)")
                reasons.append("CRÍTICO: Reforzar restricciones dietéticas")
            
            # 5. Estilo inadecuado para el evento
            if menu and overall_satisfaction < 3:
                # Verificar si los estilos del menú son apropiados para el evento
                menu_styles = set()
                for dish in [menu.starter, menu.main_course, menu.dessert]:
                    menu_styles.update(dish.styles)
                
                preferred_styles = knowledge.get_preferred_styles_for_event(request.event_type)
                if menu_styles and not any(style in preferred_styles for style in menu_styles):
                    # El estilo no era apropiado para el evento
                    delta = 0.08 * self.learning_rate
                    adjustments_made['style'] = delta
                    self._adjust_weight('style', delta,
                                       "Estilo inadecuado para tipo de evento")
                    reasons.append("Priorizar matching de estilo culinario")
            
            # 6. Temporada inapropiada (calorías no adecuadas para la estación)
            if menu and overall_satisfaction < 3:
                # Verificar si el problema fue un menú inapropiado para la temporada
                # (ej: menú muy pesado en verano, muy ligero en invierno)
                if not knowledge.is_calorie_count_appropriate(menu.total_calories, request.season):
                    delta = 0.06 * self.learning_rate
                    adjustments_made['season'] = delta
                    self._adjust_weight('season', delta,
                                       "Menú inapropiado para temporada (calorías)")
                    reasons.append("Priorizar matching de temporada (ligero/pesado)")
        
        # ===== ANÁLISIS DE FEEDBACK ALTO (Satisfacción) =====
        elif overall_satisfaction >= 4:
            # Cliente satisfecho - reforzar lo que funcionó
            
            # 1. Cultura bien matcheada
            if (feedback.cultural_satisfaction >= 4 and 
                request.cultural_preference):
                delta = 0.03 * self.learning_rate
                adjustments_made['cultural'] = delta
                self._adjust_weight('cultural', delta,
                                   "Cultura fue muy valorada")
                reasons.append("Reforzar matching cultural (éxito)")
            
            # 2. Precio bien ajustado
            if feedback.price_satisfaction >= 4:
                delta = 0.02 * self.learning_rate
                adjustments_made['price_range'] = delta
                self._adjust_weight('price_range', delta,
                                   "Precio bien ajustado")
                reasons.append("Mantener precisión de precio")
            
            # 3. Estilo apropiado para el evento
            if menu:
                menu_styles = set()
                for dish in [menu.starter, menu.main_course, menu.dessert]:
                    menu_styles.update(dish.styles)
                
                preferred_styles = knowledge.get_preferred_styles_for_event(request.event_type)
                if menu_styles and any(style in preferred_styles for style in menu_styles):
                    # El estilo era apropiado y funcionó bien
                    delta = 0.03 * self.learning_rate
                    adjustments_made['style'] = delta
                    self._adjust_weight('style', delta,
                                       "Estilo apropiado para evento (éxito)")
                    reasons.append("Reforzar matching de estilo culinario")
            
            # 4. Maridaje de vino exitoso
            if feedback.flavor_satisfaction >= 4 and request.wants_wine:
                delta = 0.03 * self.learning_rate
                adjustments_made['wine_preference'] = delta
                self._adjust_weight('wine_preference', delta,
                                   "Maridaje de vino exitoso")
                reasons.append("Reforzar importancia de maridaje")
            
            # 5. Temporada bien aprovechada (calorías apropiadas para la estación)
            if menu and feedback.flavor_satisfaction >= 4:
                # Verificar si el menú tenía calorías apropiadas para la temporada
                if knowledge.is_calorie_count_appropriate(menu.total_calories, request.season):
                    delta = 0.02 * self.learning_rate
                    adjustments_made['season'] = delta
                    self._adjust_weight('season', delta,
                                       "Menú apropiado para temporada (calorías)")
                    reasons.append("Reforzar matching de temporada")
            
            # 6. Restricciones dietéticas bien cumplidas
            if feedback.dietary_satisfaction >= 4 and request.required_diets:
                delta = 0.03 * self.learning_rate
                adjustments_made['dietary'] = delta
                self._adjust_weight('dietary', delta,
                                   "Restricciones dietéticas bien cumplidas")
                reasons.append("Reforzar importancia de dietas")
            
            # 7. Escala de invitados bien manejada
            if overall_satisfaction >= 4 and request.num_guests > 100:
                delta = 0.02 * self.learning_rate
                adjustments_made['guests'] = delta
                self._adjust_weight('guests', delta,
                                   "Evento grande bien manejado")
                reasons.append("Reforzar matching de escala de invitados")
        
        # ===== ANÁLISIS DE FEEDBACK MEDIO =====
        else:
            # Satisfacción moderada - ajustes pequeños
            if feedback.price_satisfaction < overall_satisfaction:
                # Precio es el eslabón débil
                delta = 0.03 * self.learning_rate
                adjustments_made['price_range'] = delta
                self._adjust_weight('price_range', delta,
                                   "Precio ligeramente por debajo de expectativas")
                reasons.append("Ajuste fino de precio")
        
        # Normalizar pesos (suma = 1.0)
        self._normalize_weights()
        
        # Actualizar learning rate según scheduler
        self._update_learning_rate()
        
        # Registrar snapshot
        self._record_snapshot(
            feedback_score=overall_satisfaction,
            adjustments=reasons if reasons else ["Sin ajustes (feedback neutral)"]
        )
        
        return adjustments_made
    
    def _update_learning_rate(self):
        """
        Actualiza el learning rate según el scheduler configurado.
        
        Estrategias disponibles:
        - 'exponential': lr = lr_initial * (decay_rate ^ iteration)
        - 'linear': lr = lr_initial - (lr_initial - lr_min) * (iteration / max_iter)
        - 'step': lr = lr_initial * (decay_rate ^ (iteration // step_size))
        - None: learning rate constante
        """
        if self.lr_scheduler is None:
            return
        
        old_lr = self.learning_rate
        
        if self.lr_scheduler == 'exponential':
            # Decay exponencial: lr disminuye exponencialmente
            self.learning_rate = self.initial_learning_rate * (self.lr_decay_rate ** self.iteration)
            self.learning_rate = max(self.learning_rate, self.lr_min)
            
        elif self.lr_scheduler == 'linear':
            # Decay lineal: lr disminuye linealmente hasta lr_min
            # Asumimos 100 iteraciones para llegar a lr_min (ajustable)
            max_iterations = 100
            progress = min(self.iteration / max_iterations, 1.0)
            self.learning_rate = self.initial_learning_rate - (self.initial_learning_rate - self.lr_min) * progress
            
        elif self.lr_scheduler == 'step':
            # Step decay: lr se reduce cada N iteraciones
            step_size = 10  # Reducir cada 10 iteraciones
            self.learning_rate = self.initial_learning_rate * (self.lr_decay_rate ** (self.iteration // step_size))
            self.learning_rate = max(self.learning_rate, self.lr_min)
        
        # Registrar cambio si es significativo
        if abs(old_lr - self.learning_rate) > 0.0001:
            self.adjustments_history.append(
                WeightAdjustment(
                    timestamp=datetime.now(),
                    weight_name='learning_rate',
                    delta=self.learning_rate - old_lr,
                    reason=f"Scheduler {self.lr_scheduler}: iteración {self.iteration}",
                    feedback_score=0.0
                )
            )
    
    def _adjust_weight(self, weight_name: str, delta: float, reason: str):
        """
        Ajusta un peso individual con límites.
        
        Args:
            weight_name: Nombre del peso a ajustar
            delta: Cantidad a añadir (puede ser negativa)
            reason: Razón del ajuste
        """
        current_value = getattr(self.weights, weight_name)
        new_value = current_value + delta
        
        # Aplicar límites
        new_value = max(self.min_weight, min(self.max_weight, new_value))
        
        # Actualizar
        setattr(self.weights, weight_name, new_value)
        
        # Registrar ajuste
        self.adjustments_history.append(
            WeightAdjustment(
                timestamp=datetime.now(),
                weight_name=weight_name,
                delta=new_value - current_value,  # Delta real (tras límites)
                reason=reason,
                feedback_score=0.0  # Se actualiza en update_from_feedback
            )
        )
    
    def _normalize_weights(self):
        """Normaliza los pesos para que sumen 1.0"""
        self.weights.normalize()
    
    def _record_snapshot(self, feedback_score: float, adjustments: List[str]):
        """Registra un snapshot del estado actual"""
        snapshot = LearningSnapshot(
            timestamp=datetime.now(),
            iteration=self.iteration,
            weights=self._weights_to_dict(),
            feedback_score=feedback_score,
            adjustments=adjustments
        )
        self.history.append(snapshot)
    
    def _weights_to_dict(self) -> Dict[str, float]:
        """Convierte pesos a diccionario"""
        return {
            'event_type': self.weights.event_type,
            'season': self.weights.season,
            'price_range': self.weights.price_range,
            'style': self.weights.style,
            'cultural': self.weights.cultural,
            'dietary': self.weights.dietary,
            'guests': self.weights.guests,
            'wine_preference': self.weights.wine_preference,
            'success_bonus': self.weights.success_bonus
        }
    
    def get_current_weights(self) -> SimilarityWeights:
        """Retorna los pesos actuales"""
        return self.weights
    
    def get_learning_summary(self) -> Dict:
        """Genera resumen del aprendizaje"""
        if not self.history:
            return {"message": "No hay historial de aprendizaje"}
        
        initial = self.history[0]
        current = self.history[-1]
        
        # Calcular cambios totales
        changes = {}
        for key in initial.weights.keys():
            delta = current.weights[key] - initial.weights[key]
            changes[key] = {
                'initial': initial.weights[key],
                'current': current.weights[key],
                'change': delta,
                'change_pct': (delta / initial.weights[key] * 100) if initial.weights[key] > 0 else 0
            }
        
        # Pesos más cambiados
        sorted_changes = sorted(
            changes.items(), 
            key=lambda x: abs(x[1]['change']), 
            reverse=True
        )
        
        return {
            'total_iterations': self.iteration,
            'total_adjustments': len(self.adjustments_history),
            'weight_changes': changes,
            'most_changed': [
                {
                    'weight': name,
                    'change': data['change'],
                    'change_pct': f"{data['change_pct']:.1f}%"
                }
                for name, data in sorted_changes[:3]
            ],
            'current_weights': current.weights,
            'learning_rate': {
                'current': self.learning_rate,
                'initial': self.initial_learning_rate,
                'scheduler': self.lr_scheduler or 'constant',
                'min': self.lr_min
            }
        }
    
    def save_learning_history(self, filepath: str):
        """Guarda historial de aprendizaje a archivo JSON"""
        data = {
            'metadata': {
                'total_iterations': self.iteration,
                'learning_rate': self.learning_rate,
                'min_weight': self.min_weight,
                'max_weight': self.max_weight
            },
            'history': [snapshot.to_dict() for snapshot in self.history],
            'summary': self.get_learning_summary()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def plot_evolution(self, output_path: str = 'docs/weight_evolution.png'):
        """
        Genera gráfica de evolución de pesos.
        
        Args:
            output_path: Ruta donde guardar la imagen
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Backend sin GUI
            
            if len(self.history) < 2:
                print("⚠️ Insuficiente historial para graficar (mínimo 2 snapshots)")
                return
            
            # Extraer datos
            iterations = [s.iteration for s in self.history]
            
            # Preparar datos por peso
            weight_names = list(self.history[0].weights.keys())
            weight_data = {name: [] for name in weight_names}
            
            for snapshot in self.history:
                for name in weight_names:
                    weight_data[name].append(snapshot.weights[name])
            
            # Crear gráfica
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Colores distintos para cada peso
            colors = plt.cm.tab10(range(len(weight_names)))
            
            for idx, name in enumerate(weight_names):
                ax.plot(
                    iterations, 
                    weight_data[name], 
                    label=name.replace('_', ' ').title(),
                    marker='o',
                    markersize=4,
                    linewidth=2,
                    color=colors[idx]
                )
            
            ax.set_xlabel('Iteración de Aprendizaje', fontsize=12, fontweight='bold')
            ax.set_ylabel('Peso de Similitud', fontsize=12, fontweight='bold')
            ax.set_title('Evolución de Pesos de Similitud (Aprendizaje Adaptativo)', 
                        fontsize=14, fontweight='bold')
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # Añadir línea horizontal en 1/9 (peso uniforme)
            uniform_weight = 1.0 / len(weight_names)
            ax.axhline(y=uniform_weight, color='red', linestyle=':', 
                      alpha=0.5, label=f'Peso Uniforme ({uniform_weight:.3f})')
            
            plt.tight_layout()
            
            # Guardar
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Gráfica guardada en: {output_path}")
            
        except ImportError:
            print("⚠️ matplotlib no disponible. Instalar con: pip install matplotlib")
        except Exception as e:
            print(f"❌ Error generando gráfica: {e}")
    
    def plot_feedback_correlation(self, output_path: str = 'docs/feedback_correlation.png'):
        """
        Genera gráfica de correlación entre ajustes y feedback.
        
        Args:
            output_path: Ruta donde guardar la imagen
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            if len(self.history) < 2:
                print("⚠️ Insuficiente historial para graficar")
                return
            
            iterations = [s.iteration for s in self.history]
            feedback_scores = [s.feedback_score for s in self.history]
            
            # Calcular varianza total de pesos en cada iteración
            weight_variances = []
            for snapshot in self.history:
                weights_list = list(snapshot.weights.values())
                mean_weight = sum(weights_list) / len(weights_list)
                variance = sum((w - mean_weight) ** 2 for w in weights_list) / len(weights_list)
                weight_variances.append(variance)
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Subplot 1: Feedback a lo largo del tiempo
            ax1.plot(iterations, feedback_scores, 
                    marker='o', linewidth=2, color='steelblue',
                    label='Satisfacción del Cliente')
            ax1.axhline(y=3, color='orange', linestyle='--', 
                       alpha=0.7, label='Umbral Satisfactorio (3)')
            ax1.axhline(y=4, color='green', linestyle='--', 
                       alpha=0.7, label='Umbral Excelente (4)')
            ax1.set_xlabel('Iteración', fontsize=11, fontweight='bold')
            ax1.set_ylabel('Satisfacción (1-5)', fontsize=11, fontweight='bold')
            ax1.set_title('Evolución de Satisfacción del Cliente', 
                         fontsize=13, fontweight='bold')
            ax1.legend(loc='best')
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, 5.5)
            
            # Subplot 2: Varianza de pesos (especialización)
            ax2.plot(iterations, weight_variances, 
                    marker='s', linewidth=2, color='coral',
                    label='Varianza de Pesos')
            ax2.set_xlabel('Iteración', fontsize=11, fontweight='bold')
            ax2.set_ylabel('Varianza', fontsize=11, fontweight='bold')
            ax2.set_title('Especialización de Pesos (Mayor varianza = Mayor especialización)', 
                         fontsize=13, fontweight='bold')
            ax2.legend(loc='best')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Gráfica de correlación guardada en: {output_path}")
            
        except ImportError:
            print("⚠️ matplotlib no disponible")
        except Exception as e:
            print(f"❌ Error generando gráfica: {e}")
    
    def reset_to_defaults(self):
        """Reinicia pesos a valores por defecto"""
        self.weights = SimilarityWeights()
        self.weights.normalize()
        self.iteration = 0
        self.history.clear()
        self.adjustments_history.clear()
        
        self._record_snapshot(
            feedback_score=0.0,
            adjustments=["Reset a pesos por defecto"]
        )


class AdaptiveDishWeightLearner:
    """
    Aprende pesos de similitud de platos mediante feedback del usuario.
    
    Similar a AdaptiveWeightLearner, pero enfocado específicamente en
    características de platos individuales durante la fase de adaptación.
    
    Este learner ayuda a mejorar la búsqueda de platos alternativos cuando
    se necesita reemplazar un plato en un menú.
    
    Ejemplo de uso:
        learner = AdaptiveDishWeightLearner()
        
        # Tras feedback sobre una adaptación de plato
        learner.update_from_feedback(
            original_dish=dish1,
            replacement_dish=dish2,
            feedback_score=4.5,
            adaptation_reason="dietary"
        )
        
        # Obtener pesos actualizados
        weights = learner.get_current_weights()
    """
    
    def __init__(
        self, 
        initial_weights: Optional[DishSimilarityWeights] = None,
        learning_rate: float = 0.05,
        min_weight: float = 0.02,
        max_weight: float = 0.50
    ):
        """
        Inicializa el aprendiz adaptativo de platos.
        
        Args:
            initial_weights: Pesos iniciales (si None, usa defaults)
            learning_rate: Tasa de aprendizaje (0.01-0.1 recomendado)
            min_weight: Peso mínimo permitido
            max_weight: Peso máximo permitido
        """
        # Pesos actuales
        if initial_weights:
            self.weights = initial_weights
        else:
            self.weights = DishSimilarityWeights()
            self.weights.normalize()
        
        # Parámetros de aprendizaje
        self.learning_rate = learning_rate
        self.min_weight = min_weight
        self.max_weight = max_weight
        
        # Historial de aprendizaje
        self.history: List[LearningSnapshot] = []
        self.adjustments_history: List[WeightAdjustment] = []
        
        # Contador de iteraciones
        self.iteration = 0
        
        # Registro inicial
        self._record_snapshot(
            feedback_score=0.0,
            adjustments=["Inicialización con pesos por defecto (platos)"]
        )
    
    def update_from_feedback(
        self,
        original_dish: Dish,
        replacement_dish: Dish,
        feedback: Feedback,
        adaptation_reason: str = "general"
    ) -> Dict[str, float]:
        """
        Actualiza pesos basándose en feedback sobre una adaptación de plato.
        
        Estrategia:
        - Si la adaptación fue exitosa (score alto), reforzar las características
          que fueron similares entre el plato original y el reemplazo
        - Si fue mal (score bajo), aumentar peso de características que diferían
        - Usa feedback específico de sabores (flavor_satisfaction) para ajustar 'flavors'
        
        Args:
            original_dish: Plato original del caso
            replacement_dish: Plato usado como reemplazo
            feedback: Objeto Feedback completo con satisfacciones específicas
            adaptation_reason: Razón de la adaptación (dietary, cultural, etc.)
            
        Returns:
            Diccionario con los ajustes realizados
        """
        self.iteration += 1
        adjustments_made = {}
        reasons = []
        
        # Extraer score general y específicos
        feedback_score = feedback.overall_satisfaction
        
        # Análisis de características
        same_category = original_dish.category == replacement_dish.category
        same_styles = bool(set(original_dish.styles) & set(replacement_dish.styles))
        same_flavors = bool(set(original_dish.flavors) & set(replacement_dish.flavors))
        
        price_diff = abs(original_dish.price - replacement_dish.price) / max(original_dish.price, 0.01)
        
        # ===== FEEDBACK ALTO (Adaptación exitosa) =====
        if feedback_score >= 4:
            # Reforzar características que se mantuvieron similares
            
            if same_category:
                delta = 0.03 * self.learning_rate
                adjustments_made['category'] = delta
                self._adjust_weight('category', delta, 
                                   "Mantener categoría fue exitoso")
                reasons.append("Reforzar importancia de categoría")
            
            if same_styles:
                delta = 0.04 * self.learning_rate
                adjustments_made['styles'] = delta
                self._adjust_weight('styles', delta,
                                   "Estilos similares fueron bien valorados")
                reasons.append("Estilos culinarios importantes")
            
            # IMPORTANTE: Usar feedback específico de sabores
            if feedback.flavor_satisfaction >= 4 and same_flavors:
                delta = 0.05 * self.learning_rate  # Aumentado porque es feedback directo
                adjustments_made['flavors'] = delta
                self._adjust_weight('flavors', delta,
                                   "Sabores similares fueron muy valorados (feedback directo)")
                reasons.append("✅ Sabores bien valorados - mantener similitud")
            
            if price_diff < 0.2:  # Precio similar
                delta = 0.02 * self.learning_rate
                adjustments_made['price'] = delta
                self._adjust_weight('price', delta,
                                   "Precio similar fue apropiado")
                reasons.append("Mantener rango de precio")
            
            # Si la razón fue cultural y fue exitoso
            if adaptation_reason == "cultural":
                delta = 0.05 * self.learning_rate
                adjustments_made['cultural'] = delta
                self._adjust_weight('cultural', delta,
                                   "Adaptación cultural exitosa")
                reasons.append("Cultural fue crítico (éxito)")
            
            # Si la razón fue dietética y fue exitoso
            if adaptation_reason == "dietary":
                delta = 0.05 * self.learning_rate
                adjustments_made['diets'] = delta
                self._adjust_weight('diets', delta,
                                   "Adaptación dietética exitosa")
                reasons.append("Restricciones dietéticas bien manejadas")
        
        # ===== FEEDBACK BAJO (Adaptación problemática) =====
        elif feedback_score < 3:
            # La adaptación no funcionó - necesitamos ser más estrictos
            
            if not same_category:
                delta = 0.06 * self.learning_rate
                adjustments_made['category'] = delta
                self._adjust_weight('category', delta,
                                   "Cambio de categoría fue problemático")
                reasons.append("Ser más estricto con categoría")
            
            if not same_styles:
                delta = 0.05 * self.learning_rate
                adjustments_made['styles'] = delta
                self._adjust_weight('styles', delta,
                                   "Cambio de estilo fue problemático")
                reasons.append("Mantener estilos más similares")
            
            if price_diff > 0.3:  # Precio muy diferente
                delta = 0.04 * self.learning_rate
                adjustments_made['price'] = delta
                self._adjust_weight('price', delta,
                                   "Diferencia de precio fue problemática")
                reasons.append("Ser más cuidadoso con precio")
            
            # IMPORTANTE: Usar feedback específico de sabores
            if feedback.flavor_satisfaction < 3:
                # El cliente reporta sabores insatisfactorios
                if not same_flavors:
                    # Cambiamos sabores Y el cliente se quejó específicamente
                    delta = 0.08 * self.learning_rate  # Aumentado por feedback directo
                    adjustments_made['flavors'] = delta
                    self._adjust_weight('flavors', delta,
                                       "❌ Sabores diferentes Y feedback negativo (crítico)")
                    reasons.append("CRÍTICO: Cliente insatisfecho con sabores - mantener más similitud")
                else:
                    # Sabores similares pero aún así se quejó (problema del plato original)
                    delta = 0.03 * self.learning_rate
                    adjustments_made['flavors'] = delta
                    self._adjust_weight('flavors', delta,
                                       "Sabores no gustaron (problema del plato base)")
                    reasons.append("Revisar perfil de sabores en general")
            elif not same_flavors and feedback_score < 3:
                # No hay feedback específico de sabor, pero cambió y score general bajo
                delta = 0.05 * self.learning_rate
                adjustments_made['flavors'] = delta
                self._adjust_weight('flavors', delta,
                                   "Cambio de sabores contribuyó a insatisfacción")
                reasons.append("Mantener perfiles de sabor más similares")
            
            # Si falló y era adaptación cultural
            if adaptation_reason == "cultural":
                delta = 0.08 * self.learning_rate
                adjustments_made['cultural'] = delta
                self._adjust_weight('cultural', delta,
                                   "Adaptación cultural falló - priorizar")
                reasons.append("CRÍTICO: Mejorar matching cultural")
        
        # ===== FEEDBACK MEDIO =====
        else:
            # Ajustes menores basados en la razón de adaptación
            if adaptation_reason == "dietary":
                delta = 0.03 * self.learning_rate
                adjustments_made['diets'] = delta
                self._adjust_weight('diets', delta,
                                   "Ajuste fino de restricciones dietéticas")
                reasons.append("Afinar matching dietético")
        
        # Normalizar pesos
        self._normalize_weights()
        
        # Registrar snapshot
        self._record_snapshot(
            feedback_score=feedback_score,
            adjustments=reasons if reasons else ["Sin ajustes (feedback neutral)"]
        )
        
        return adjustments_made
    
    def _adjust_weight(self, weight_name: str, delta: float, reason: str):
        """Ajusta un peso individual con límites"""
        current_value = getattr(self.weights, weight_name)
        new_value = current_value + delta
        
        # Aplicar límites
        new_value = max(self.min_weight, min(self.max_weight, new_value))
        
        # Actualizar
        setattr(self.weights, weight_name, new_value)
        
        # Registrar ajuste
        self.adjustments_history.append(
            WeightAdjustment(
                timestamp=datetime.now(),
                weight_name=weight_name,
                delta=new_value - current_value,
                reason=reason,
                feedback_score=0.0
            )
        )
    
    def _normalize_weights(self):
        """Normaliza los pesos para que sumen 1.0"""
        self.weights.normalize()
    
    def _record_snapshot(self, feedback_score: float, adjustments: List[str]):
        """Registra un snapshot del estado actual"""
        snapshot = LearningSnapshot(
            timestamp=datetime.now(),
            iteration=self.iteration,
            weights=self._weights_to_dict(),
            feedback_score=feedback_score,
            adjustments=adjustments
        )
        self.history.append(snapshot)
    
    def _weights_to_dict(self) -> Dict[str, float]:
        """Convierte pesos a diccionario"""
        return {
            'category': self.weights.category,
            'price': self.weights.price,
            'complexity': self.weights.complexity,
            'flavors': self.weights.flavors,
            'styles': self.weights.styles,
            'temperature': self.weights.temperature,
            'diets': self.weights.diets,
            'cultural': self.weights.cultural
        }
    
    def get_current_weights(self) -> DishSimilarityWeights:
        """Retorna los pesos actuales"""
        return self.weights
    
    def get_learning_summary(self) -> Dict:
        """Genera resumen del aprendizaje"""
        if not self.history:
            return {"message": "No hay historial de aprendizaje"}
        
        initial = self.history[0]
        current = self.history[-1]
        
        # Calcular cambios totales
        changes = {}
        for key in initial.weights.keys():
            delta = current.weights[key] - initial.weights[key]
            changes[key] = {
                'initial': initial.weights[key],
                'current': current.weights[key],
                'change': delta,
                'change_pct': (delta / initial.weights[key] * 100) if initial.weights[key] > 0 else 0
            }
        
        # Pesos más cambiados
        sorted_changes = sorted(
            changes.items(), 
            key=lambda x: abs(x[1]['change']), 
            reverse=True
        )
        
        return {
            'total_iterations': self.iteration,
            'total_adjustments': len(self.adjustments_history),
            'weight_changes': changes,
            'most_changed': [
                {
                    'weight': name,
                    'change': data['change'],
                    'change_pct': f"{data['change_pct']:.1f}%"
                }
                for name, data in sorted_changes[:3]
            ],
            'current_weights': current.weights,
            'learning_rate': {
                'current': self.learning_rate,
                'initial': self.initial_learning_rate,
                'scheduler': self.lr_scheduler or 'constant',
                'min': self.lr_min
            }
        }
    
    def save_learning_history(self, filepath: str):
        """Guarda historial de aprendizaje a archivo JSON"""
        data = {
            'metadata': {
                'learner_type': 'dish_similarity',
                'total_iterations': self.iteration,
                'learning_rate': self.learning_rate,
                'min_weight': self.min_weight,
                'max_weight': self.max_weight
            },
            'history': [snapshot.to_dict() for snapshot in self.history],
            'summary': self.get_learning_summary()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def reset_to_defaults(self):
        """Reinicia pesos a valores por defecto"""
        self.weights = DishSimilarityWeights()
        self.weights.normalize()
        self.iteration = 0
        self.history.clear()
        self.adjustments_history.clear()
        
        self._record_snapshot(
            feedback_score=0.0,
            adjustments=["Reset a pesos por defecto (platos)"]
        )
