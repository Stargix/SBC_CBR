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

from ..core.models import Case, Menu, Request
from ..core.case_base import CaseBase
from ..core.similarity import SimilarityCalculator, calculate_menu_similarity


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
        
        # Umbrales de retención (ajustados para aprendizaje más permisivo)
        self.novelty_threshold = 0.92  # Si similitud < este, es novedoso (antes 0.85)
        self.quality_threshold = 3.0   # Mínimo feedback para retener como positivo (antes 3.5)
        self.negative_threshold = 2.5  # Feedback < 2.5 se guarda como caso negativo (antes 3.0)
        self.max_cases_per_event = 50  # Límite de casos por tipo de evento
        self.max_cases_total = 200  # Límite total para evitar crecimiento infinito
        
        # Mantenimiento periódico (no en cada inserción)
        self.maintenance_frequency = 10  # Cada 10 casos añadidos
        self.cases_since_maintenance = 0
        
        # Umbral de redundancia para eliminar casos duplicados
        self.redundancy_threshold = 0.90  # Casos con sim > 0.90 son redundantes
    
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
        # 1. Verificar si es caso negativo (failure)
        is_negative = feedback.score < self.negative_threshold
        
        if is_negative:
            # Guardar como caso negativo para evitar repetir errores
            return RetentionDecision(
                should_retain=True,
                reason=f"Caso negativo - evitar repetir este error ({feedback.score}/5)",
                similarity_to_existing=0.0,
                most_similar_case=None,
                action="add_negative"
            )
        elif feedback.score < self.quality_threshold:
            # No es suficientemente malo para aprender, ni suficientemente bueno
            return RetentionDecision(
                should_retain=False,
                reason=f"Feedback medio - no aporta aprendizaje ({feedback.score}/5)",
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
            # Muy similar a uno existente (≥92%)
            if most_similar and feedback.score > most_similar.feedback_score + 0.2:
                # El nuevo es mejor, actualizar el existente
                return RetentionDecision(
                    should_retain=True,
                    reason=f"Mejora caso existente ({feedback.score:.1f} vs {most_similar.feedback_score:.1f})",
                    similarity_to_existing=max_similarity,
                    most_similar_case=most_similar,
                    action="update_existing"
                )
            else:
                # El existente es igual o mejor, redundante
                return RetentionDecision(
                    should_retain=False,
                    reason=f"Redundante con caso existente (sim={max_similarity:.2%}, score similar)",
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
               feedback: FeedbackData, 
               source_case: Optional[Case] = None) -> Tuple[bool, str]:
        """
        Retiene un nuevo caso si es apropiado.
        
        Args:
            request: Solicitud original
            menu: Menú aceptado
            feedback: Feedback del cliente
            source_case: Caso fuente si el menú fue adaptado de otro caso
            
        Returns:
            Tupla (éxito, mensaje)
        """
        decision = self.evaluate_retention(request, menu, feedback)
        
        if not decision.should_retain:
            return False, decision.reason
        
        if decision.action == "add_new" or decision.action == "add_negative":
            # Determinar si es caso negativo
            is_negative = decision.action == "add_negative"
            
            # Determinar la fuente del caso
            source_type = "learned"
            original_case_id = None
            
            if source_case and menu.cultural_adaptations:
                # Es un caso adaptado culturalmente
                source_type = "cultural_adaptation"
                original_case_id = source_case.id
            elif source_case:
                # Es un caso adaptado de otras formas
                source_type = "adapted"
                original_case_id = source_case.id
            
            # Crear y añadir nuevo caso
            new_case = Case(
                id=f"case-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(100, 999)}",
                request=request,
                menu=menu,
                success=feedback.success,
                feedback_score=feedback.score,
                feedback_comments=feedback.comments,
                source=source_type,
                is_negative=is_negative,
                original_case_id=original_case_id
            )
            
            self.case_base.add_case(new_case)
            self.cases_since_maintenance += 1
            
            # POLÍTICA DE OLVIDO: Si excedemos el límite total, hacer limpieza
            if len(self.case_base.get_all_cases()) > self.max_cases_total:
                self._enforce_case_limit()
            
            # Verificar si hay que hacer limpieza periódica
            if self.cases_since_maintenance >= self.maintenance_frequency:
                self._maintenance_if_needed(request.event_type)
                self.cases_since_maintenance = 0
            
            tipo = "negativo (failure)" if is_negative else "positivo"
            adaptacion = f" (adaptado culturalmente de {original_case_id})" if menu.cultural_adaptations else ""
            return True, f"Nuevo caso {tipo} añadido: {new_case.id}{adaptacion}"
        
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
        
        Nueva estrategia: elimina casos REDUNDANTES (muy similares)
        en vez de casos de baja calidad.
        """
        event_cases = self.case_base.get_cases_by_event(event_type)
        
        if len(event_cases) > self.max_cases_per_event:
            # Nueva estrategia: eliminar redundantes
            to_remove = self._identify_redundant_cases(event_cases)
            
            if to_remove:
                # Eliminar casos redundantes
                self.case_base.cases = [
                    c for c in self.case_base.cases if c.id not in to_remove
                ]
            else:
                # Si no hay redundantes, eliminar los de menor utilidad
                # (como último recurso)
                self._fallback_remove_by_utility(event_cases)
            
            # Reconstruir índices
            self._rebuild_indexes()
    
    def _identify_redundant_cases(self, cases: List[Case]) -> set:
        """
        Identifica casos redundantes (muy similares entre sí).
        
        Estrategia: Para cada grupo de casos muy similares,
        mantener solo el mejor (mayor feedback + uso).
        
        Returns:
            Set de IDs de casos a eliminar
        """
        to_remove = set()
        processed = set()
        
        # Separar casos positivos y negativos
        positive_cases = [c for c in cases if not c.is_negative]
        negative_cases = [c for c in cases if c.is_negative]
        
        # Eliminar redundancia en positivos
        for i, case1 in enumerate(positive_cases):
            if case1.id in processed or case1.id in to_remove:
                continue
            
            # Buscar casos muy similares
            similar_group = [case1]
            
            for case2 in positive_cases[i+1:]:
                if case2.id in to_remove:
                    continue
                
                # Calcular similitud request + menu
                req_sim = self.similarity_calc.calculate_similarity(
                    case1.request, case2.request
                )
                menu_sim = calculate_menu_similarity(case1.menu, case2.menu)
                combined_sim = 0.6 * req_sim + 0.4 * menu_sim
                
                if combined_sim >= self.redundancy_threshold:
                    similar_group.append(case2)
            
            # Si hay casos redundantes, mantener solo el mejor
            if len(similar_group) > 1:
                # Ordenar por utilidad
                similar_group.sort(
                    key=lambda c: self._calculate_case_utility(c),
                    reverse=True
                )
                
                # Mantener el primero (mejor), eliminar los demás
                for case in similar_group[1:]:
                    to_remove.add(case.id)
                    processed.add(case.id)
            
            processed.add(case1.id)
        
        # Los casos negativos también se pueden condensar
        # pero con menor agresividad (queremos recordar varios tipos de errores)
        neg_redundancy_threshold = 0.95  # Más restrictivo
        processed_neg = set()
        
        for i, case1 in enumerate(negative_cases):
            if case1.id in processed_neg or case1.id in to_remove:
                continue
            
            similar_neg = [case1]
            for case2 in negative_cases[i+1:]:
                if case2.id in to_remove:
                    continue
                
                req_sim = self.similarity_calc.calculate_similarity(
                    case1.request, case2.request
                )
                menu_sim = calculate_menu_similarity(case1.menu, case2.menu)
                combined_sim = 0.6 * req_sim + 0.4 * menu_sim
                
                if combined_sim >= neg_redundancy_threshold:
                    similar_neg.append(case2)
            
            if len(similar_neg) > 1:
                # Para negativos, mantener el de peor score (más representativo del error)
                similar_neg.sort(key=lambda c: c.feedback_score)
                for case in similar_neg[1:]:
                    to_remove.add(case.id)
                    processed_neg.add(case.id)
            
            processed_neg.add(case1.id)
        
        return to_remove
    
    def _fallback_remove_by_utility(self, event_cases: List[Case]):
        """
        Estrategia de respaldo: si no hay redundantes, eliminar por utilidad.
        """
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
            if c.id in to_keep or c.request.event_type not in [case.request.event_type for case in event_cases]
        ]
        
        removed_count = len(event_cases) - len(to_keep)
    
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
        from ..core.models import EventType, Season, CulinaryStyle
        
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
        
        # Separar casos positivos y negativos
        positive_cases = [c for c in cases if not c.is_negative]
        negative_cases = [c for c in cases if c.is_negative]
        
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
            "positive_cases": len(positive_cases),
            "negative_cases": len(negative_cases),
            "successful_cases": successes,
            "success_rate": successes / len(cases) if cases else 0,
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
    
    def _enforce_case_limit(self):
        """
        Aplica política de olvido para mantener la base en el límite.
        
        Estrategia:
        1. Eliminar casos de baja utilidad
        2. Priorizar mantener casos exitosos y recientes
        3. Mantener diversidad entre eventos
        """
        all_cases = self.case_base.get_all_cases()
        
        if len(all_cases) <= self.max_cases_total:
            return  # No hace falta
        
        # Calcular utilidad de cada caso
        case_utilities = []
        for case in all_cases:
            utility = self._calculate_case_utility(case)
            case_utilities.append((case, utility))
        
        # Ordenar por utilidad (menor a mayor)
        case_utilities.sort(key=lambda x: x[1])
        
        # Calcular cuántos eliminar
        to_remove_count = len(all_cases) - self.max_cases_total
        
        # Eliminar los de menor utilidad
        cases_to_remove = [case for case, _ in case_utilities[:to_remove_count]]
        
        for case in cases_to_remove:
            self.case_base.cases.remove(case)
    
    def export_learned_cases(self) -> List[Dict[str, Any]]:
        """
        Exporta los casos aprendidos (no iniciales) para respaldo.
        
        Returns:
            Lista de casos en formato diccionario
        """
        learned = [c for c in self.case_base.cases if c.source == "learned"]
        return [c.to_dict() for c in learned]
