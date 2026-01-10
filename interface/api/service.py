import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from develop.main import ChefDigitalCBR, CBRConfig
from develop.core.models import (
    Request,
    EventType,
    Season,
    CulinaryStyle,
    CulturalTradition,
    ProposedMenu,
)
from develop.cycle.retain import FeedbackData
from develop.cycle.diversity import ensure_diversity


def _parse_enum(enum_cls, value, default):
    if value is None:
        return default
    try:
        return enum_cls[str(value).upper()]
    except KeyError:
        return default


def _serialize_issue(issue) -> Dict[str, Any]:
    if hasattr(issue, "message"):
        return {
            "severity": getattr(issue, "severity", None),
            "category": getattr(issue, "category", None),
            "message": getattr(issue, "message", None),
            "suggestion": getattr(issue, "suggestion", None),
        }
    return {"message": str(issue)}


def _serialize_validation(validation) -> Dict[str, Any]:
    return {
        "status": getattr(validation.status, "value", str(validation.status)),
        "score": getattr(validation, "score", None),
        "issues": [_serialize_issue(issue) for issue in getattr(validation, "issues", [])],
        "explanations": getattr(validation, "explanations", []),
    }


def _serialize_menu(menu) -> Dict[str, Any]:
    if hasattr(menu, "to_dict"):
        return menu.to_dict()
    return {"menu": str(menu)}


def _serialize_case(case) -> Dict[str, Any]:
    if hasattr(case, "to_dict"):
        return case.to_dict()
    return {"case": str(case)}


def _serialize_retrieval_result(result) -> Dict[str, Any]:
    return {
        "case_id": getattr(result.case, "id", None),
        "similarity": result.similarity,
        "rank": result.rank,
        "similarity_details": result.similarity_details,
        "case": _serialize_case(result.case),
    }


def _serialize_proposal(menu, source_case, similarity, adaptations, validation, rank) -> Dict[str, Any]:
    return {
        "rank": rank,
        "similarity": similarity,
        "source_case_id": getattr(source_case, "id", None),
        "menu": _serialize_menu(menu),
        "adaptations": adaptations,
        "validation": _serialize_validation(validation) if validation else None,
    }


def _serialize_rejected(rejected: Dict[str, Any]) -> Dict[str, Any]:
    case = rejected.get("case")
    reasons = rejected.get("reasons")
    if isinstance(reasons, list):
        reasons_payload = [_serialize_issue(r) for r in reasons]
    else:
        reasons_payload = reasons
    return {
        "case_id": getattr(case, "id", None),
        "case": _serialize_case(case) if case else None,
        "menu_name": rejected.get("menu_name"),
        "similarity": rejected.get("similarity"),
        "reasons": reasons_payload,
    }


_CASE_ID_PATTERN = re.compile(r"(case-[A-Za-z0-9\\-]+)")


def _extract_case_id(message: str) -> Optional[str]:
    if not message:
        return None
    match = _CASE_ID_PATTERN.search(message)
    if match:
        return match.group(1)
    return None


def _validation_score_to_feedback(score: Optional[float]) -> float:
    if score is None:
        return 0.0
    return max(1.0, min(5.0, float(score) / 20.0))


class CBRService:
    def __init__(self, case_base_path: Optional[str] = None):
        config = CBRConfig(verbose=False)
        if case_base_path:
            config.case_base_path = case_base_path
        self.cbr = ChefDigitalCBR(config)
        self._trace_cache: Dict[str, Dict[str, Any]] = {}
        self._trace_order: List[str] = []
        self._max_traces = 50

    def _store_trace(self, trace_id: str, request: Request, proposals: List[Dict[str, Any]]) -> None:
        self._trace_cache[trace_id] = {
            "request": request,
            "proposals": proposals,
            "created_at": time.time(),
        }
        self._trace_order.append(trace_id)
        while len(self._trace_order) > self._max_traces:
            oldest = self._trace_order.pop(0)
            self._trace_cache.pop(oldest, None)

    def build_request(self, payload: Dict[str, Any]) -> Request:
        event_type = _parse_enum(EventType, payload.get("event_type"), EventType.FAMILIAR)
        season = _parse_enum(Season, payload.get("season"), Season.SPRING)
        preferred_style = None
        if payload.get("preferred_style"):
            preferred_style = _parse_enum(
                CulinaryStyle, payload.get("preferred_style"), None
            )
        cultural_preference = None
        if payload.get("cultural_preference"):
            cultural_preference = _parse_enum(
                CulturalTradition, payload.get("cultural_preference"), None
            )

        required_diets = payload.get("required_diets", []) or []
        if isinstance(required_diets, str):
            required_diets = [required_diets]

        restricted_ingredients = payload.get("restricted_ingredients", []) or []
        if isinstance(restricted_ingredients, str):
            restricted_ingredients = [restricted_ingredients]

        return Request(
            event_type=event_type,
            season=season,
            num_guests=int(payload.get("num_guests", 50)),
            price_min=float(payload.get("price_min", 0.0)),
            price_max=float(payload.get("price_max", 0.0)),
            wants_wine=bool(payload.get("wants_wine", False)),
            preferred_style=preferred_style,
            cultural_preference=cultural_preference,
            required_diets=required_diets,
            restricted_ingredients=restricted_ingredients,
        )

    def process_with_trace(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        request = self.build_request(payload)

        stats = {
            "cases_retrieved": 0,
            "cases_adapted": 0,
            "cases_validated": 0,
            "cases_rejected": 0,
        }

        retrieval_results = self.cbr._retrieve_phase_detailed(request)
        stats["cases_retrieved"] = len(retrieval_results)
        if not retrieval_results:
            retrieval_results = self.cbr._generate_from_knowledge_detailed(request)

        proposed = []
        rejected = []

        for result in retrieval_results:
            if len(proposed) >= self.cbr.config.max_proposals * 2:
                break

            case = result.case
            similarity = result.similarity

            adapt_result = self.cbr._adapt_phase(case, request)
            if adapt_result is None:
                stats["cases_rejected"] += 1
                rejected.append(
                    {
                        "case": case,
                        "menu_name": f"Menu based on case {case.id}",
                        "reasons": ["Could not adapt to dietary constraints"],
                        "similarity": similarity,
                    }
                )
                continue

            adapted_menu, adaptations = adapt_result
            stats["cases_adapted"] += 1

            validation = self.cbr._revise_phase(adapted_menu, request)
            if validation.is_valid():
                stats["cases_validated"] += 1
                proposed.append(
                    {
                        "menu": adapted_menu,
                        "source_case": case,
                        "similarity": similarity,
                        "adaptations": adaptations,
                        "validation": validation,
                    }
                )
            else:
                stats["cases_rejected"] += 1
                rejected.append(
                    {
                        "case": case,
                        "menu_name": f"Menu based on case {case.id}",
                        "reasons": validation.issues,
                        "similarity": similarity,
                    }
                )

        if len(proposed) > self.cbr.config.max_proposals:
            menus_to_diversify = [p["menu"] for p in proposed]
            diverse_menus = ensure_diversity(
                menus_to_diversify,
                min_distance=0.3,
                max_proposals=self.cbr.config.max_proposals,
            )
            proposed = [p for p in proposed if p["menu"] in diverse_menus]

        proposed_payload = []
        for idx, item in enumerate(proposed, 1):
            item["rank"] = idx
            proposed_payload.append(
                _serialize_proposal(
                    item["menu"],
                    item["source_case"],
                    item["similarity"],
                    item["adaptations"],
                    item["validation"],
                    idx,
                )
            )

        rejected_payload = [_serialize_rejected(item) for item in rejected]
        retrieval_payload = [_serialize_retrieval_result(r) for r in retrieval_results]

        proposals_for_report = [
            ProposedMenu(
                menu=item["menu"],
                source_case=item["source_case"],
                similarity_score=item["similarity"],
                adaptations=item["adaptations"],
                validation_result=item["validation"],
                rank=idx + 1,
            )
            for idx, item in enumerate(proposed)
        ]

        explanations = self.cbr.explainer.generate_full_report(
            proposals_for_report,
            rejected,
            request,
            retrieval_results=retrieval_results,
            stats=stats,
        )

        processing_time = time.time() - start_time
        trace_id = str(uuid4())
        stored_proposals = [
            {
                "rank": idx,
                "menu": item["menu"],
                "source_case": item["source_case"],
            }
            for idx, item in enumerate(proposed, 1)
        ]
        self._store_trace(trace_id, request, stored_proposals)

        # NO auto-retain: El feedback automático (validation_score/20) siempre da ~4.95
        # Esto NO es adecuado para CBR porque:
        # 1. No hay feedback real del usuario
        # 2. No permite aprendizaje adaptativo de pesos
        # 3. Contamina la base de casos con casos no validados por humanos
        # El usuario debe evaluar manualmente cada menú propuesto
        retention_info = None
        retained_case = None

        return {
            "trace_id": trace_id,
            "request": request.to_dict(),
            "retrieval_results": retrieval_payload,
            "proposed_menus": proposed_payload,
            "rejected_cases": rejected_payload,
            "explanations": explanations,
            "stats": stats,
            "processing_time": processing_time,
            "retention": retention_info,
            "_retained_case": retained_case,
        }

    def generate_random_request(self) -> Dict[str, Any]:
        event_types = ["WEDDING", "FAMILIAR", "CONGRESS", "CORPORATE", "CHRISTENING", "COMMUNION"]
        dietary = ["vegan", "vegetarian", "gluten-free", "lactose-free", "kosher", "pork-free"]
        seasons = ["SPRING", "SUMMER", "AUTUMN", "WINTER"]
        styles = ["CLASSIC", "MODERN", "FUSION", "REGIONAL", "SIBARITA", "GOURMET"]
        cultures = ["AMERICAN", "CHINESE", "FRENCH", "INDIAN", "ITALIAN", "JAPANESE", "MEXICAN", "SPANISH", "KOREAN", "VIETNAMESE", "LEBANESE"]
        ingredients = ["shellfish", "nuts", "dairy", "eggs", "fish"]

        price_min = random.randint(15, 40)
        price_max = price_min + random.randint(10, 40)
        return {
            "event_type": random.choice(event_types),
            "num_guests": random.randint(2, 50),
            "season": random.choice(seasons),
            "price_min": price_min,
            "price_max": price_max,
            "wants_wine": random.choice([True, False]),
            "required_diets": random.sample(dietary, k=random.randint(0, 2)),
            "restricted_ingredients": random.sample(ingredients, k=random.randint(0, 2)),
            "preferred_style": random.choice(styles) if random.random() > 0.5 else None,
            "cultural_preference": random.choice(cultures) if random.random() > 0.5 else None,
        }

    def run_synthetic(self, use_llm: bool) -> Dict[str, Any]:
        if use_llm:
            try:
                from simulation.llm_simulator import LLMCBRSimulator, LLMSimulationConfig
            except ImportError as exc:
                return {
                    "error": "LLM simulator dependencies missing",
                    "details": str(exc),
                }

            config = LLMSimulationConfig(num_interactions=1, verbose=False, save_results=False)
            simulator = LLMCBRSimulator(config)
            result = simulator.run_simulation()
            interaction = result.interactions[0] if result.interactions else None
            interaction_eval = interaction.llm_evaluation if interaction else ""
            interaction_score = interaction.llm_score if interaction else 0.0

            return {
                "request": interaction.generated_request if interaction else None,
                "llm_score": interaction_score or result.llm_score,
                "llm_evaluation": interaction_eval,
                "llm_summary": result.llm_evaluation,
                "interactions": [i.__dict__ for i in result.interactions],
            }

        request_payload = self.generate_random_request()
        trace = self.process_with_trace(request_payload)
        return {"request": request_payload, "trace": trace, "llm_score": None}

    def _auto_retain(
        self,
        request: Request,
        proposed: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Optional[Any]]:
        candidate = max(
            proposed,
            key=lambda item: (
                getattr(item.get("validation"), "score", 0.0) or 0.0,
                item.get("similarity", 0.0),
            ),
        )

        validation = candidate.get("validation")
        validation_score = getattr(validation, "score", 0.0) if validation else 0.0
        feedback_score = _validation_score_to_feedback(validation_score)
        success = bool(validation.is_valid()) if validation else False
        comments = f"Auto-retain (validation score {validation_score:.1f}/100)"

        feedback = FeedbackData(
            menu_id=candidate["menu"].id,
            success=success,
            score=feedback_score,
            comments=comments,
            would_recommend=success,
        )

        try:
            self.cbr.learn_from_feedback(feedback, request, candidate["menu"])
        except Exception:
            pass

        before_ids = {case.id for case in self.cbr.case_base.get_all_cases()}
        retained, message = self.cbr.retainer.retain(
            request,
            candidate["menu"],
            feedback,
            candidate.get("source_case"),
        )

        case = None
        case_id = None
        if retained:
            after_cases = self.cbr.case_base.get_all_cases()
            new_case = next((c for c in after_cases if c.id not in before_ids), None)
            if new_case:
                case = new_case
                case_id = new_case.id
            else:
                case_id = _extract_case_id(message)
                if case_id:
                    case = next((c for c in after_cases if c.id == case_id), None)

        retention_info = {
            "success": retained,
            "message": message,
            "case_id": case_id,
            "proposal_rank": candidate.get("rank"),
            "score": feedback_score,
        }
        return retention_info, case

    def retain_from_trace(
        self,
        trace_id: str,
        proposal_rank: int,
        score: float,
        success: bool,
        comments: Optional[str],
    ) -> Dict[str, Any]:
        trace = self._trace_cache.get(trace_id)
        if not trace:
            return {"success": False, "message": "Trace not found"}

        proposals = trace.get("proposals", [])
        proposal = next((item for item in proposals if item["rank"] == proposal_rank), None)
        if not proposal:
            return {"success": False, "message": "Proposal not found in trace"}

        request = trace["request"]
        menu = proposal["menu"]
        source_case = proposal.get("source_case")
        feedback = FeedbackData(
            menu_id=menu.id,
            success=success,
            score=score,
            comments=comments or "",
            would_recommend=success,
        )

        # Update adaptive weights using the same feedback signal
        try:
            self.cbr.learn_from_feedback(feedback, request, menu)
        except Exception:
            pass

        before_ids = {case.id for case in self.cbr.case_base.get_all_cases()}
        retained, message = self.cbr.retainer.retain(request, menu, feedback, source_case)
        case = None
        case_id = None

        if retained:
            after_cases = self.cbr.case_base.get_all_cases()
            new_case = next((c for c in after_cases if c.id not in before_ids), None)
            if new_case:
                case = new_case
                case_id = new_case.id
            else:
                case_id = _extract_case_id(message)
                if case_id:
                    case = next((c for c in after_cases if c.id == case_id), None)

        return {
            "success": retained,
            "message": message,
            "case": case,
            "case_id": case_id,
        }

    def process_manual_feedback(
        self,
        request_data: Dict[str, Any],
        menu_id: str,
        price_satisfaction: float,
        cultural_satisfaction: float,
        flavor_satisfaction: float,
        overall_satisfaction: float,
    ) -> Dict[str, Any]:
        """Process manual feedback with multi-dimensional scores and RETAIN the case"""
        try:
            request = self.build_request(request_data)
            
            # Create feedback with multi-dimensional scores
            feedback = FeedbackData(
                menu_id=menu_id,
                success=overall_satisfaction >= 3.5,
                score=overall_satisfaction,
                price_satisfaction=price_satisfaction,
                cultural_satisfaction=cultural_satisfaction,
                flavor_satisfaction=flavor_satisfaction,
                would_recommend=overall_satisfaction >= 4.0,
                comments=f"Manual evaluation - P:{price_satisfaction} C:{cultural_satisfaction} F:{flavor_satisfaction} O:{overall_satisfaction}",
            )
            
            # Apply learning to adaptive weights
            self.cbr.learn_from_feedback(feedback, request, None)
            
            # RETAIN: Guardar el caso en la base de datos
            # Necesitamos recuperar el menú desde los traces
            menu_to_retain = None
            source_case = None
            
            # Buscar en traces el menú evaluado
            for trace_id, trace_data in self._trace_cache.items():
                for proposal in trace_data.get('proposals', []):
                    if proposal['menu'].id == menu_id:
                        menu_to_retain = proposal['menu']
                        source_case = proposal.get('source_case')
                        break
                if menu_to_retain:
                    break
            
            case_retained = False
            case_id = None
            
            if menu_to_retain:
                before_ids = {case.id for case in self.cbr.case_base.get_all_cases()}
                retained, message = self.cbr.retainer.retain(
                    request, 
                    menu_to_retain, 
                    feedback, 
                    source_case
                )
                
                if retained:
                    case_retained = True
                    after_cases = self.cbr.case_base.get_all_cases()
                    new_case = next((c for c in after_cases if c.id not in before_ids), None)
                    if new_case:
                        case_id = new_case.id
            
            # Get updated weights for response
            weights_info = None
            try:
                if hasattr(self.cbr, 'weight_learner') and self.cbr.weight_learner:
                    current_weights = self.cbr.weight_learner.get_current_weights()
                    weights_info = {
                        'event_type': current_weights.event_type,
                        'season': current_weights.season,
                        'price_range': current_weights.price_range,
                        'cultural': current_weights.cultural,
                        'style': current_weights.style,
                    }
            except AttributeError:
                pass
            
            return {
                "success": True,
                "message": f"Feedback procesado. {'Caso guardado!' if case_retained else 'Pesos actualizados.'}",
                "case_retained": case_retained,
                "case_id": case_id,
                "weights_updated": weights_info,
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error procesando feedback: {str(e)}",
                "weights_updated": None,
            }
