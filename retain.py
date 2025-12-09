"""
Fase RETAIN del ciclo CBR.

Este módulo implementa el aprendizaje y retención de nuevos casos.
Es la cuarta y última fase del ciclo CBR.

La retención incluye:
1. Evaluación de si un nuevo caso merece ser almacenado
2. Actualización de casos existentes con nuevo feedback
3. Mantenimiento de la base de casos (limpieza, consolidación)
4. Métricas de utilidad de casos

El objetivo es mejorar continuamente la base de conocimiento
basándose en la experiencia acumulada.
"""

from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import random

from .models import Case, Menu, Request
from .case_base import CaseBase
from .similarity import SimilarityCalculator, calculate_menu_similarity


@dataclass
class RetentionDecision:
    """
    Decisión sobre si retener un nuevo caso.
    """
    should_retain: bool
    reason: str
    similarity_to_existing: float
    most_similar_case: Optional[Case]
    action: str  # "add_new", "update_existing", "discard"


@dataclass
class FeedbackData:
    """
    Datos de feedback del cliente.
    """
    menu_id: str
    success: bool
    score: float  # 1-5
    comments: str
    would_recommend: bool


class CaseRetainer:
    """
    Gestor de retención de casos del sistema CBR.
    
    Implementa la fase RETAIN del ciclo CBR,
    decidiendo qué casos almacenar y cómo
    mantener la base de conocimiento.
    """
    
    def __init__(self, case_base: CaseBase):
        """
        Inicializa el gestor de retención.
        
        Args:
            case_base: Base de casos a gestionar
        """
        self.case_base = case_base
        self.similarity_calc = SimilarityCalculator()
        
        # Umbrales de retención
        self.novelty_threshold = 0.85  # Si similitud < este, es novedoso
        self.quality_threshold = 3.5   # Mínimo feedback para retener
        self.max_cases_per_event = 50  # Límite de casos por tipo de evento
    
    def evaluate_retention(self, request: Request, menu: Menu,
                           feedback: FeedbackData) -> RetentionDecision:
        """
        Evalúa si un nuevo caso debe ser retenido.
        
        Args:
            request: Solicitud original
            menu: Menú propuesto
            feedback: Feedback del cliente
            
        Returns:
            Decisión de retención
        """
        # 1. Verificar calidad mínima
        if feedback.score < self.quality_threshold:
            return RetentionDecision(
                should_retain=False,
                reason=f"Feedback insuficiente ({feedback.score}/5)",
                similarity_to_existing=0.0,
                most_similar_case=None,
                action="discard"
            )
        
        # 2. Buscar casos similares existentes
        existing_cases = self.case_base.get_all_cases()
        
        if not existing_cases:
            return RetentionDecision(
                should_retain=True,
                reason="Primer caso para esta configuración",
                similarity_to_existing=0.0,
                most_similar_case=None,
                action="add_new"
            )
        
        # Calcular similitud con casos existentes
        max_similarity = 0.0
        most_similar = None
        
        for case in existing_cases:
            # Similitud del request
            req_sim = self.similarity_calc.calculate_similarity(request, case)
            # Similitud del menú
            menu_sim = calculate_menu_similarity(menu, case.menu)
            
            # Similitud combinada
            combined_sim = 0.6 * req_sim + 0.4 * menu_sim
            
            if combined_sim > max_similarity:
                max_similarity = combined_sim
                most_similar = case
        
        # 3. Decidir acción
        if max_similarity >= self.novelty_threshold:
            # Muy similar a uno existente
            if most_similar and feedback.score > most_similar.feedback_score:
                # El nuevo es mejor, actualizar el existente
                return RetentionDecision(
                    should_retain=True,
                    reason="Mejora un caso existente",
                    similarity_to_existing=max_similarity,
                    most_similar_case=most_similar,
                    action="update_existing"
                )
            else:
                # El existente es igual o mejor
                return RetentionDecision(
                    should_retain=False,
                    reason="Ya existe un caso similar con igual o mejor feedback",
                    similarity_to_existing=max_similarity,
                    most_similar_case=most_similar,
                    action="discard"
                )
        else:
            # Suficientemente novedoso
            return RetentionDecision(
                should_retain=True,
                reason="Caso novedoso para la base de conocimiento",
                similarity_to_existing=max_similarity,
                most_similar_case=most_similar,
                action="add_new"
            )
    
    def retain(self, request: Request, menu: Menu, 
               feedback: FeedbackData) -> Tuple[bool, str]:
        """
        Retiene un nuevo caso si es apropiado.
        
        Args:
            request: Solicitud original
            menu: Menú aceptado
            feedback: Feedback del cliente
            
        Returns:
            Tupla (éxito, mensaje)
        """
        decision = self.evaluate_retention(request, menu, feedback)
        
        if not decision.should_retain:
            return False, decision.reason
        
        if decision.action == "add_new":
            # Crear y añadir nuevo caso
            new_case = Case(
                id=f"case-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(100, 999)}",
                request=request,
                menu=menu,
                success=feedback.success,
                feedback_score=feedback.score,
                feedback_comments=feedback.comments,
                source="learned"
            )
            
            self.case_base.add_case(new_case)
            
            # Verificar si hay que hacer limpieza
            self._maintenance_if_needed(request.event_type)
            
            return True, f"Nuevo caso añadido: {new_case.id}"
        
        elif decision.action == "update_existing":
            # Actualizar caso existente
            if decision.most_similar_case:
                old_case = decision.most_similar_case
                old_case.menu = menu
                old_case.feedback_score = feedback.score
                old_case.feedback_comments = feedback.comments
                old_case.increment_usage()
                old_case.adaptation_notes.append(
                    f"Actualizado con mejor feedback ({feedback.score}/5)"
                )
                
                return True, f"Caso actualizado: {old_case.id}"
        
        return False, "No se pudo retener el caso"
    
    def update_case_feedback(self, case_id: str, 
                             feedback: FeedbackData) -> Tuple[bool, str]:
        """
        Actualiza el feedback de un caso existente.
        
        Args:
            case_id: ID del caso a actualizar
            feedback: Nuevo feedback
            
        Returns:
            Tupla (éxito, mensaje)
        """
        for case in self.case_base.cases:
            if case.id == case_id:
                # Actualizar con promedio ponderado del feedback
                old_weight = case.usage_count
                new_weight = 1
                total_weight = old_weight + new_weight
                
                case.feedback_score = (
                    (case.feedback_score * old_weight + feedback.score * new_weight)
                    / total_weight
                )
                
                case.success = case.success and feedback.success
                case.increment_usage()
                
                if feedback.comments:
                    case.feedback_comments = feedback.comments
                
                return True, f"Feedback actualizado para caso {case_id}"
        
        return False, f"Caso {case_id} no encontrado"
    
    def _maintenance_if_needed(self, event_type):
        """
        Realiza mantenimiento de la base si es necesario.
        
        Elimina casos de baja calidad cuando se excede el límite.
        """
        event_cases = self.case_base.get_cases_by_event(event_type)
        
        if len(event_cases) > self.max_cases_per_event:
            # Ordenar por calidad y uso
            scored_cases = []
            for case in event_cases:
                utility = self._calculate_case_utility(case)
                scored_cases.append((case, utility))
            
            scored_cases.sort(key=lambda x: x[1], reverse=True)
            
            # Mantener solo los mejores
            to_keep = {c.id for c, _ in scored_cases[:self.max_cases_per_event]}
            
            # Eliminar los demás
            self.case_base.cases = [
                c for c in self.case_base.cases
                if c.id in to_keep or c.request.event_type != event_type
            ]
            
            # Reconstruir índices
            self._rebuild_indexes()
    
    def _calculate_case_utility(self, case: Case) -> float:
        """
        Calcula la utilidad de un caso para decidir si mantenerlo.
        
        Factores:
        - Feedback del cliente
        - Frecuencia de uso
        - Recencia
        - Éxito
        """
        utility = 0.0
        
        # Feedback (0-5 -> 0-50 puntos)
        utility += case.feedback_score * 10
        
        # Uso (cada uso añade puntos, con rendimientos decrecientes)
        utility += min(20, case.usage_count * 2)
        
        # Éxito
        if case.success:
            utility += 10
        
        # Recencia (casos más recientes son más valiosos)
        if case.last_used:
            try:
                last_used = datetime.fromisoformat(case.last_used)
                days_ago = (datetime.now() - last_used).days
                utility += max(0, 20 - days_ago)  # Hasta 20 puntos si es reciente
            except:
                pass
        
        return utility
    
    def _rebuild_indexes(self):
        """Reconstruye los índices de la base de casos"""
        from .models import EventType, Season, CulinaryStyle
        
        # Reiniciar índices
        self.case_base.index_by_event = {e: [] for e in EventType}
        self.case_base.index_by_season = {s: [] for s in Season}
        self.case_base.index_by_style = {s: [] for s in CulinaryStyle}
        self.case_base.index_by_price_range = {
            "low": [], "medium": [], "high": [], "premium": []
        }
        
        # Reindexar todos los casos
        for case in self.case_base.cases:
            self.case_base._index_case(case)
    
    def get_retention_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de retención y calidad de la base.
        
        Returns:
            Diccionario con estadísticas
        """
        cases = self.case_base.cases
        
        if not cases:
            return {"total_cases": 0}
        
        # Calcular estadísticas
        feedbacks = [c.feedback_score for c in cases]
        usages = [c.usage_count for c in cases]
        successes = sum(1 for c in cases if c.success)
        
        # Casos por fuente
        sources = {}
        for case in cases:
            sources[case.source] = sources.get(case.source, 0) + 1
        
        return {
            "total_cases": len(cases),
            "successful_cases": successes,
            "success_rate": successes / len(cases),
            "avg_feedback": sum(feedbacks) / len(feedbacks),
            "min_feedback": min(feedbacks),
            "max_feedback": max(feedbacks),
            "avg_usage": sum(usages) / len(usages),
            "total_usages": sum(usages),
            "cases_by_source": sources,
            "cases_by_event": {
                e.value: len(self.case_base.index_by_event.get(e, []))
                for e in self.case_base.index_by_event
            }
        }
    
    def suggest_case_improvements(self) -> List[Dict[str, Any]]:
        """
        Sugiere mejoras para casos de baja calidad.
        
        Returns:
            Lista de sugerencias
        """
        suggestions = []
        
        for case in self.case_base.cases:
            if case.feedback_score < 3.5:
                suggestions.append({
                    "case_id": case.id,
                    "current_score": case.feedback_score,
                    "event_type": case.request.event_type.value,
                    "suggestion": "Considerar revisar o eliminar este caso",
                    "issues": case.feedback_comments or "Sin comentarios"
                })
            
            elif case.usage_count == 0:
                suggestions.append({
                    "case_id": case.id,
                    "current_score": case.feedback_score,
                    "event_type": case.request.event_type.value,
                    "suggestion": "Caso nunca utilizado, verificar relevancia",
                    "issues": "Sin usos registrados"
                })
        
        return suggestions
    
    def export_learned_cases(self) -> List[Dict[str, Any]]:
        """
        Exporta los casos aprendidos (no iniciales) para respaldo.
        
        Returns:
            Lista de casos en formato diccionario
        """
        learned = [c for c in self.case_base.cases if c.source == "learned"]
        return [c.to_dict() for c in learned]
