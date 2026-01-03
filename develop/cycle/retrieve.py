"""
Fase RETRIEVE del ciclo CBR.

Este módulo implementa la recuperación de casos similares
de la base de conocimiento. Es la primera fase del ciclo CBR.

La recuperación utiliza:
1. Pre-filtrado por índices (evento, precio, temporada)
2. Cálculo de similitud detallado
3. Ranking de los casos más similares

El resultado es una lista ordenada de casos candidatos
para la siguiente fase de adaptación.
"""

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

from ..core.models import Case, Request, EventType, Season
from ..core.case_base import CaseBase
from ..core.similarity import SimilarityCalculator, SimilarityWeights


@dataclass
class RetrievalResult:
    """
    Resultado de la recuperación de un caso.
    
    Contiene el caso recuperado junto con información
    sobre por qué fue seleccionado.
    """
    case: Case
    similarity: float
    similarity_details: Dict[str, float]
    rank: int
    
    def get_explanation(self) -> str:
        """Genera una explicación de por qué se recuperó este caso"""
        explanations = []
        
        if self.similarity_details.get('event_type', 0) > 0.8:
            explanations.append("Tipo de evento muy similar")
        
        if self.similarity_details.get('price_range', 0) > 0.9:
            explanations.append("Precio dentro del rango solicitado")
        elif self.similarity_details.get('price_range', 0) > 0.7:
            explanations.append("Precio cercano al rango solicitado")
        
        if self.similarity_details.get('season', 0) > 0.9:
            explanations.append("Temporada coincidente")
        
        if self.similarity_details.get('style', 0) > 0.8:
            explanations.append("Estilo culinario apropiado")
        
        if self.similarity_details.get('dietary', 0) == 1.0:
            explanations.append("Cumple todas las restricciones dietéticas")
        
        if self.similarity_details.get('success_bonus', 0) > 0.8:
            explanations.append("Caso con alta valoración de clientes anteriores")
        
        return "; ".join(explanations) if explanations else "Caso compatible"


class CaseRetriever:
    """
    Recuperador de casos del sistema CBR.
    
    Implementa la fase RETRIEVE del ciclo CBR, buscando
    los casos más similares a una nueva solicitud.
    """
    
    def __init__(self, case_base: CaseBase, 
                 weights: Optional[SimilarityWeights] = None):
        """
        Inicializa el recuperador.
        
        Args:
            case_base: Base de casos a consultar
            weights: Pesos para el cálculo de similitud
        """
        self.case_base = case_base
        self.similarity_calc = SimilarityCalculator(weights)
        
        # Parámetros de recuperación
        self.min_similarity_threshold = 0.3  # Mínima similitud para considerar
        self.max_candidates = 50  # Máximo de candidatos a evaluar en detalle
    
    def retrieve(self, request: Request, k: int = 5) -> List[RetrievalResult]:
        """
        Recupera los k casos más similares a la solicitud.
        
        Proceso:
        1. Pre-filtrado rápido por índices
        2. Cálculo de similitud detallado
        3. Ranking y selección de top-k
        4. Filtrado de casos negativos (solo se usan para evitarlos)
        
        Args:
            request: Solicitud del cliente
            k: Número de casos a recuperar
            
        Returns:
            Lista de resultados de recuperación ordenados por similitud
        """
        # Fase 1: Pre-filtrado
        candidates = self._prefilter_candidates(request)
        
        if not candidates:
            # Si no hay candidatos con pre-filtrado, usar todos
            candidates = self.case_base.get_all_cases()
        
        # Filtrar casos negativos (solo queremos casos exitosos para adaptar)
        candidates = [c for c in candidates if not c.is_negative]
        
        # FILTRADO CRÍTICO: Dietas y alergias (con fallback si quedan pocos)
        candidates = self._filter_by_critical_constraints(candidates, request)
        
        # Limitar candidatos para eficiencia
        candidates = candidates[:self.max_candidates]
        
        # Fase 2: Cálculo de similitud detallado
        scored_cases = []
        for case in candidates:
            details = self.similarity_calc.calculate_detailed_similarity(request, case)
            similarity = details['total']
            
            # BOOST: Si el usuario pide cultura específica, aumentar similitud de casos compatibles
            if request.cultural_preference and case.menu.cultural_theme:
                if request.cultural_preference == case.menu.cultural_theme:
                    # Caso de la misma cultura solicitada - boost significativo
                    similarity = min(1.0, similarity + 0.2)
                    details['cultural_match'] = 1.0
                else:
                    # Cultura diferente - calcular qué tan adaptable es
                    from cycle.ingredient_adapter import get_ingredient_adapter
                    adapter = get_ingredient_adapter()
                    
                    # Calcular score cultural promedio del menú
                    cultural_scores = []
                    for dish_attr in ['starter', 'main_course', 'dessert']:
                        dish = getattr(case.menu, dish_attr)
                        if dish.ingredients:
                            score = adapter.get_cultural_score(dish.ingredients, request.cultural_preference)
                            cultural_scores.append(score)
                    
                    if cultural_scores:
                        avg_cultural_score = sum(cultural_scores) / len(cultural_scores)
                        details['cultural_adaptability'] = avg_cultural_score
                        # No penalizar, solo informar - ADAPT se encargará
            
            # SIEMPRE incluir candidatos - no usar umbral mínimo arbitrario
            scored_cases.append((case, similarity, details))
        
        # Fase 3: Ranking
        scored_cases.sort(key=lambda x: x[1], reverse=True)
        
        # Construir resultados
        results = []
        for rank, (case, similarity, details) in enumerate(scored_cases[:k], 1):
            result = RetrievalResult(
                case=case,
                similarity=similarity,
                similarity_details=details,
                rank=rank
            )
            results.append(result)
        
        return results
    
    def _filter_by_critical_constraints(self, candidates: List[Case], 
                                         request: Request) -> List[Case]:
        """
        Filtra candidatos por restricciones CRÍTICAS (dietas, alergias).
        
        Estas restricciones no son adaptables fácilmente, por lo que
        es mejor filtrarlas aquí en RETRIEVE.
        
        Si el filtrado deja muy pocos candidatos (<3), usa fallback
        para no quedarnos sin opciones.
        
        Args:
            candidates: Lista de candidatos a filtrar
            request: Solicitud con restricciones
            
        Returns:
            Lista filtrada (o original si fallback)
        """
        filtered = candidates
        
        # Filtrar por dietas obligatorias
        if request.required_diets:
            diets_filtered = []
            for case in filtered:
                # Obtener todas las dietas que cumple el menú
                menu_diets = case.menu.get_all_diets()
                # Ver si cumple TODAS las dietas requeridas
                if all(diet in menu_diets for diet in request.required_diets):
                    diets_filtered.append(case)
            
            # FALLBACK: Solo si hay AL MENOS 1 candidato, usar filtrado
            # Si no hay ninguno, ADAPT intentará adaptar los casos
            if len(diets_filtered) > 0:
                filtered = diets_filtered
            # Si quedan 0, mantener todos y dejar que ADAPT intente adaptarlos
        
        # Filtrar por alergias (ingredientes restringidos)
        # CRÍTICO: Alergias NO son adaptables, SIEMPRE filtrar
        if request.restricted_ingredients:
            allergy_filtered = []
            for case in filtered:
                # Ver si algún plato contiene ingredientes prohibidos
                has_allergen = False
                for dish in [case.menu.starter, case.menu.main_course, case.menu.dessert]:
                    if any(ing in dish.ingredients for ing in request.restricted_ingredients):
                        has_allergen = True
                        break
                
                if not has_allergen:
                    allergy_filtered.append(case)
            
            # Para alergias, SIEMPRE filtrar (no hay fallback seguro)
            filtered = allergy_filtered
        
        return filtered
    
    def _prefilter_candidates(self, request: Request) -> List[Case]:
        """
        Pre-filtra candidatos usando los índices de la base de casos.
        
        Esto es una optimización para bases de casos grandes.
        
        Args:
            request: Solicitud del cliente
            
        Returns:
            Lista de casos pre-filtrados
        """
        candidates = []
        seen_ids = set()
        
        # 1. Casos del mismo tipo de evento
        event_cases = self.case_base.get_cases_by_event(request.event_type)
        for case in event_cases:
            if case.id not in seen_ids:
                candidates.append(case)
                seen_ids.add(case.id)
        
        # 2. Casos en rango de precio (con margen del 20%)
        margin = (request.price_max - request.price_min) * 0.2
        price_cases = self.case_base.get_cases_by_price_range(
            request.price_min - margin,
            request.price_max + margin
        )
        for case in price_cases:
            if case.id not in seen_ids:
                candidates.append(case)
                seen_ids.add(case.id)
        
        # 3. Casos de la misma temporada
        season_cases = self.case_base.get_cases_by_season(request.season)
        for case in season_cases:
            if case.id not in seen_ids:
                candidates.append(case)
                seen_ids.add(case.id)
        
        return candidates
    
    def retrieve_with_explanations(self, request: Request, 
                                    k: int = 5) -> Tuple[List[RetrievalResult], str]:
        """
        Recupera casos y genera una explicación del proceso.
        
        Args:
            request: Solicitud del cliente
            k: Número de casos a recuperar
            
        Returns:
            Tupla con (resultados, explicación textual)
        """
        results = self.retrieve(request, k)
        
        # Generar explicación
        explanation_parts = [
            f"Se buscaron casos similares para un evento {request.event_type.value}",
            f"en temporada {request.season.value}",
            f"con presupuesto {request.price_min}-{request.price_max}€."
        ]
        
        if results:
            explanation_parts.append(f"\nSe encontraron {len(results)} casos relevantes:")
            for r in results:
                explanation_parts.append(
                    f"\n  {r.rank}. Caso '{r.case.id}' (similitud: {r.similarity:.2f})"
                )
                explanation_parts.append(f"     - {r.get_explanation()}")
        else:
            explanation_parts.append("\nNo se encontraron casos suficientemente similares.")
            explanation_parts.append("Se procederá a generar un menú nuevo.")
        
        return results, " ".join(explanation_parts)
    
    def retrieve_diverse(self, request: Request, k: int = 5, 
                         diversity_weight: float = 0.3) -> List[RetrievalResult]:
        """
        Recupera casos diversos (no solo los más similares).
        
        Útil para ofrecer variedad de opciones al cliente.
        Utiliza una estrategia de Maximal Marginal Relevance (MMR).
        
        Args:
            request: Solicitud del cliente
            k: Número de casos a recuperar
            diversity_weight: Peso de la diversidad (0-1)
            
        Returns:
            Lista de resultados diversos
        """
        # Obtener más candidatos de los necesarios
        all_results = self.retrieve(request, k * 3)
        
        if len(all_results) <= k:
            return all_results
        
        # Seleccionar diversos usando MMR
        selected = [all_results[0]]  # El más similar siempre se incluye
        remaining = all_results[1:]
        
        while len(selected) < k and remaining:
            best_candidate = None
            best_score = -1
            
            for candidate in remaining:
                # Calcular similitud con casos ya seleccionados
                max_sim_to_selected = max(
                    self._case_to_case_similarity(candidate.case, sel.case)
                    for sel in selected
                )
                
                # MMR score: balance entre similitud a query y diversidad
                mmr_score = (
                    (1 - diversity_weight) * candidate.similarity -
                    diversity_weight * max_sim_to_selected
                )
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_candidate = candidate
            
            if best_candidate:
                selected.append(best_candidate)
                remaining.remove(best_candidate)
        
        # Actualizar ranks
        for i, result in enumerate(selected, 1):
            result.rank = i
        
        return selected
    
    def _case_to_case_similarity(self, case1: Case, case2: Case) -> float:
        """
        Calcula similitud entre dos casos.
        
        Usado para diversificación.
        """
        # Similitud simplificada basada en menús
        from ..core.similarity import calculate_menu_similarity
        return calculate_menu_similarity(case1.menu, case2.menu)
    
    def get_retrieval_statistics(self, request: Request) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre la recuperación.
        
        Útil para diagnóstico y mejora del sistema.
        
        Args:
            request: Solicitud del cliente
            
        Returns:
            Diccionario con estadísticas
        """
        all_cases = self.case_base.get_all_cases()
        
        similarities = []
        for case in all_cases:
            sim = self.similarity_calc.calculate_similarity(request, case)
            similarities.append(sim)
        
        similarities.sort(reverse=True)
        
        return {
            "total_cases": len(all_cases),
            "above_threshold": sum(1 for s in similarities if s >= self.min_similarity_threshold),
            "max_similarity": max(similarities) if similarities else 0,
            "min_similarity": min(similarities) if similarities else 0,
            "avg_similarity": sum(similarities) / len(similarities) if similarities else 0,
            "median_similarity": similarities[len(similarities)//2] if similarities else 0,
            "top_5_similarities": similarities[:5]
        }
    
    def check_negative_cases(self, request: Request, threshold: float = 0.80) -> List[Tuple[Case, float]]:
        """
        Verifica si hay casos negativos (failures) similares al request.
        
        Esto permite advertir: "Este tipo de menú falló anteriormente".
        
        Args:
            request: Solicitud del cliente
            threshold: Umbral mínimo de similitud (0.80 = 80%)
            
        Returns:
            Lista de tuplas (caso_negativo, similitud) ordenadas por similitud
        """
        all_cases = self.case_base.get_all_cases()
        negative_cases = [c for c in all_cases if c.is_negative]
        
        warnings = []
        for case in negative_cases:
            similarity = self.similarity_calc.calculate_similarity(request, case)
            
            if similarity >= threshold:
                warnings.append((case, similarity))
        
        # Ordenar por similitud descendente
        warnings.sort(key=lambda x: x[1], reverse=True)
        
        return warnings
