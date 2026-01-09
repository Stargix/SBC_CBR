"""
Módulo principal del sistema CBR de Chef Digital.

Este módulo orquesta todas las fases del ciclo CBR:
1. RETRIEVE: Recuperar casos similares
2. REUSE/ADAPT: Reutilizar y adaptar el caso
3. REVISE: Revisar y validar la solución
4. RETAIN: Retener el nuevo conocimiento

El sistema se inspira en grandes chefs y tradiciones culinarias:
- Ferran Adrià (creatividad molecular)
- Juan Mari Arzak (innovación vasca)
- Paul Bocuse (nouvelle cuisine)
- René Redzepi (Noma, localismo)

Tradiciones culturales soportadas:
- Mediterráneas: Griega, Italiana, Catalana, Vasca, Gallega
- Medio Oriente: Marroquí, Turca, Libanesa
- África: Somalí, Etíope
- Este de Europa: Rusa
"""

import json
import os
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

try:
    # Cuando se importa como módulo
    from .core.models import (
        Request, Menu, Case, Dish, Beverage, ProposedMenu,
        EventType, Season, CulinaryStyle, DishType
    )
    from .core.case_base import CaseBase
    from .core.adaptive_weights import AdaptiveWeightLearner
    from .cycle.retrieve import CaseRetriever
    from .cycle.adapt import CaseAdapter
    from .cycle.revise import MenuReviser, ValidationResult
    from .cycle.retain import CaseRetainer, FeedbackData
    from .cycle.explanation import ExplanationGenerator
    from .cycle.diversity import ensure_diversity, get_diversity_explanation
    from .core.knowledge import (
        EVENT_STYLE_PREFERENCES, STYLE_DESCRIPTIONS,
        CULTURAL_TRADITIONS, CHEF_SIGNATURES
    )
except ImportError:
    # Cuando se ejecuta como script o desde demo sin ser módulo
    from core.models import (
        Request, Menu, Case, Dish, Beverage, ProposedMenu,
        EventType, Season, CulinaryStyle, DishType
    )
    from core.case_base import CaseBase
    from core.adaptive_weights import AdaptiveWeightLearner
    from cycle.retrieve import CaseRetriever
    from cycle.adapt import CaseAdapter
    from cycle.revise import MenuReviser, ValidationResult
    from cycle.retain import CaseRetainer, FeedbackData
    from cycle.explanation import ExplanationGenerator
    from cycle.diversity import ensure_diversity, get_diversity_explanation
    from core.knowledge import (
        EVENT_STYLE_PREFERENCES, STYLE_DESCRIPTIONS,
        CULTURAL_TRADITIONS, CHEF_SIGNATURES
    )


@dataclass
class CBRConfig:
    """
    Configuración del sistema CBR.
    """
    max_proposals: int = 3              # Máximo menús a proponer
    min_similarity: float = 0.3         # Similitud mínima para considerar
    enable_learning: bool = True        # Habilitar aprendizaje
    case_base_path: str = "cases.json"  # Ruta a la base de casos
    verbose: bool = False               # Modo verbose


@dataclass
class CBRResult:
    """
    Resultado del proceso CBR.
    """
    success: bool
    proposed_menus: List[ProposedMenu]
    rejected_cases: List[Dict[str, Any]]
    explanations: str
    processing_time: float
    stats: Dict[str, Any] = field(default_factory=dict)


class ChefDigitalCBR:
    """
    Sistema CBR de Chef Digital para propuesta de menús.
    
    Implementa el ciclo completo CBR (Retrieve-Reuse-Revise-Retain)
    para proponer menús personalizados basados en experiencias previas.
    
    El sistema puede generar hasta 3 propuestas de menú ordenadas
    por relevancia, explicando por qué se seleccionaron y por qué
    otros fueron descartados.
    """
    
    def __init__(self, config: Optional[CBRConfig] = None):
        """
        Inicializa el sistema CBR.
        
        Args:
            config: Configuración opcional del sistema
        """
        self.config = config or CBRConfig()
        
        # Inicializar componentes
        self.case_base = CaseBase()
        
        # Aprendizaje adaptativo de pesos
        self.weight_learner = AdaptiveWeightLearner(learning_rate=0.05)
        
        # Componentes del ciclo CBR (con pesos adaptativos)
        self.retriever = CaseRetriever(
            self.case_base, 
            weights=self.weight_learner.get_current_weights()
        )
        self.adapter = CaseAdapter(self.case_base)
        self.reviser = MenuReviser()
        self.retainer = CaseRetainer(self.case_base)
        self.explainer = ExplanationGenerator()
        
        # Cargar base de casos si existe
        if os.path.exists(self.config.case_base_path):
            self.load_case_base(self.config.case_base_path)
    
    def process_request(self, request: Request) -> CBRResult:
        """
        Procesa una solicitud de menú completa.
        
        Este es el método principal que ejecuta el ciclo CBR completo.
        
        Args:
            request: Solicitud del cliente
            
        Returns:
            Resultado con menús propuestos y explicaciones
        """
        start_time = datetime.now()
        
        proposed_menus = []
        rejected_cases = []
        stats = {
            "cases_retrieved": 0,
            "cases_adapted": 0,
            "cases_validated": 0,
            "cases_rejected": 0
        }
        
        # FASE 1: RETRIEVE - Recuperar casos similares
        retrieval_results = self._retrieve_phase_detailed(request)
        stats["cases_retrieved"] = len(retrieval_results)
        
        if not retrieval_results:
            # Sin casos similares, intentar generación desde conocimiento
            retrieval_results = self._generate_from_knowledge_detailed(request)
        
        # FASE 2-3: REUSE/ADAPT + REVISE para cada caso
        for result in retrieval_results:
            if len(proposed_menus) >= self.config.max_proposals * 2:  # Recuperar más para diversificar
                break
            
            case = result.case
            similarity = result.similarity
            
            # REUSE/ADAPT
            adapt_result = self._adapt_phase(case, request)
            
            if adapt_result is None:
                # ADAPT rechazó el caso (no se pudo adaptar a las restricciones)
                stats["cases_rejected"] += 1
                rejected_cases.append({
                    "case": case,
                    "menu_name": f"Menú basado en caso {case.id}",
                    "reasons": ["No se pudo adaptar a las restricciones dietéticas"],
                    "similarity": similarity
                })
                continue
            
            adapted_menu, adaptations = adapt_result
            stats["cases_adapted"] += 1
            
            # REVISE
            validation = self._revise_phase(adapted_menu, request)
            
            if validation.is_valid():  # Llamar al método para verificar validación
                stats["cases_validated"] += 1
                
                # Crear propuesta
                proposal = ProposedMenu(
                    menu=adapted_menu,
                    source_case=case,
                    similarity_score=similarity,
                    adaptations=adaptations,
                    validation_result=validation,
                    rank=len(proposed_menus) + 1
                )
                proposed_menus.append(proposal)
            else:
                stats["cases_rejected"] += 1
                rejected_cases.append({
                    "case": case,
                    "menu_name": f"Menú basado en caso {case.id}",
                    "reasons": validation.issues,
                    "similarity": similarity
                })
        
        # DIVERSIFICACIÓN: Asegurar que las propuestas sean suficientemente diferentes
        if len(proposed_menus) > self.config.max_proposals:
            menus_to_diversify = [p.menu for p in proposed_menus]
            diverse_menus = ensure_diversity(
                menus_to_diversify, 
                min_distance=0.3,
                max_proposals=self.config.max_proposals
            )
            # Mantener solo las propuestas diversas
            proposed_menus = [p for p in proposed_menus if p.menu in diverse_menus]
            # Re-rankear
            for i, proposal in enumerate(proposed_menus, 1):
                proposal.rank = i
        
        # Generar explicaciones CON DATOS DETALLADOS DE RETRIEVE
        explanations = self.explainer.generate_full_report(
            proposed_menus, rejected_cases, request, 
            retrieval_results=retrieval_results,  # Pasar resultados detallados
            stats=stats  # Pasar estadísticas precisas
        )
        
        # Calcular tiempo de procesamiento
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return CBRResult(
            success=len(proposed_menus) > 0,
            proposed_menus=proposed_menus,
            rejected_cases=rejected_cases,
            explanations=explanations,
            processing_time=processing_time,
            stats=stats
        )
    
    def _retrieve_phase_detailed(self, request: Request) -> List:
        """
        Ejecuta la fase RETRIEVE del ciclo CBR con detalles completos.
        
        Args:
            request: Solicitud del cliente
            
        Returns:
            Lista de RetrievalResult con similarity_details
        """
        # Recuperar casos candidatos con detalles completos
        candidates = self.retriever.retrieve(
            request,
            k=self.config.max_proposals * 3  # Recuperar más para tener opciones
        )
        
        # Filtrar por similitud mínima
        filtered = [
            result for result in candidates
            if result.similarity >= self.config.min_similarity
        ]
        
        return filtered
    
    def _retrieve_phase(self, request: Request) -> List[Tuple[Case, float]]:
        """
        Ejecuta la fase RETRIEVE del ciclo CBR.
        
        Args:
            request: Solicitud del cliente
            
        Returns:
            Lista de (caso, similitud) ordenada por similitud
        """
        # Usar versión detallada y convertir a formato antiguo
        detailed_results = self._retrieve_phase_detailed(request)
        
        return [(result.case, result.similarity) for result in detailed_results]
    
    def _adapt_phase(self, case: Case, request: Request) -> Optional[Tuple[Menu, List[str]]]:
        """
        Ejecuta la fase REUSE/ADAPT del ciclo CBR.
        
        Args:
            case: Caso a adaptar
            request: Solicitud del cliente
            
        Returns:
            Tupla (menú adaptado, lista de adaptaciones) o None si no se pudo adaptar
        """
        # Usar el CaseAdapter para adaptar el caso
        try:
            from .cycle.retrieve import RetrievalResult
        except ImportError:
            from cycle.retrieve import RetrievalResult
        
        # Crear resultado de recuperación temporal
        retrieval_result = RetrievalResult(
            case=case, 
            similarity=1.0,
            similarity_details={},
            rank=1
        )
        
        # Adaptar usando el CaseAdapter
        adapted_results = self.adapter.adapt([retrieval_result], request, num_proposals=1)
        
        if adapted_results:
            result = adapted_results[0]
            return result.adapted_menu, result.adaptations_made
        else:
            # ADAPT rechazó el caso (no se pudo adaptar)
            return None
    
    def _revise_phase(self, menu: Menu, request: Request) -> ValidationResult:
        """
        Ejecuta la fase REVISE del ciclo CBR.
        
        Args:
            menu: Menú a validar
            request: Solicitud del cliente
            
        Returns:
            Resultado de la validación
        """
        # Usar el MenuReviser para validación completa
        validation_result = self.reviser._validate_menu(menu, request)
        return validation_result
    
    def _generate_from_knowledge_detailed(self, request: Request) -> List:
        """
        Genera casos desde el conocimiento cuando no hay casos similares.
        
        Retorna resultados detallados para explicabilidad.
        
        Args:
            request: Solicitud del cliente
            
        Returns:
            Lista de RetrievalResult generados
        """
        # Usar versión antigua y convertir
        old_format = self._generate_from_knowledge(request)
        
        # Convertir a formato detallado
        try:
            from .cycle.retrieve import RetrievalResult
        except ImportError:
            from cycle.retrieve import RetrievalResult
        
        detailed_results = []
        for case, similarity in old_format:
            result = RetrievalResult(
                case=case,
                similarity=similarity,
                similarity_details={
                    'event_type': 0.5,
                    'style': 0.5,
                    'generated': True
                },
                rank=len(detailed_results) + 1
            )
            detailed_results.append(result)
        
        return detailed_results
    
    def _generate_from_knowledge(self, request: Request) -> List[Tuple[Case, float]]:
        """
        Genera casos desde el conocimiento cuando no hay casos similares.
        
        Usa las preferencias de estilo y tradiciones culturales
        para construir un menú desde cero.
        
        Args:
            request: Solicitud del cliente
            
        Returns:
            Lista de casos generados con similitud estimada
        """
        generated_cases = []
        
        # Obtener estilos preferidos para el evento
        preferred_styles = EVENT_STYLE_PREFERENCES.get(
            request.event_type,
            [CulinaryStyle.CLASSIC]
        )
        
        # Intentar generar un caso basado en el estilo preferido del cliente
        if request.preferred_style in preferred_styles:
            case = self._create_template_case(request, request.preferred_style)
            if case:
                generated_cases.append((case, 0.5))  # Similitud base 50%
        
        # Generar variantes con otros estilos compatibles
        for style in preferred_styles[:2]:
            if style != request.preferred_style:
                case = self._create_template_case(request, style)
                if case:
                    generated_cases.append((case, 0.4))
        
        return generated_cases
    
    def _create_template_case(self, request: Request, 
                               style: CulinaryStyle) -> Optional[Case]:
        """
        Crea un caso plantilla basado en el conocimiento del dominio.
        
        Args:
            request: Solicitud del cliente
            style: Estilo culinario a aplicar
            
        Returns:
            Caso plantilla o None si no es posible
        """
        # Este método usaría el conocimiento del dominio para
        # construir un menú coherente. En una implementación completa,
        # consultaría la base de platos disponibles.
        
        # Por ahora, retornar None para indicar que no hay plantilla
        # La implementación real usaría las instancias de platos
        return None
    
    def learn_from_feedback(self, request: Request, menu: Menu,
                            feedback: FeedbackData) -> Tuple[bool, str]:
        """
        Aprende de la experiencia reteniendo casos exitosos.
        
        Esta es la fase RETAIN del ciclo CBR.
        
        Args:
            request: Solicitud original
            menu: Menú que se utilizó
            feedback: Feedback del cliente
            
        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.config.enable_learning:
            return False, "Aprendizaje deshabilitado en configuración"
        
        return self.retainer.retain(request, menu, feedback)
    
    def load_case_base(self, path: str) -> bool:
        """
        Carga la base de casos desde archivo.
        
        Args:
            path: Ruta al archivo JSON
            
        Returns:
            True si se cargó correctamente
        """
        try:
            self.case_base.load_from_file(path)
            
            # Actualizar referencias en componentes
            self.retriever = CaseRetriever(self.case_base)
            self.retainer = CaseRetainer(self.case_base)
            
            return True
        except Exception as e:
            return False
    
    def save_case_base(self, path: Optional[str] = None) -> bool:
        """
        Guarda la base de casos en archivo.
        
        Args:
            path: Ruta al archivo (usa config si no se especifica)
            
        Returns:
            True si se guardó correctamente
        """
        save_path = path or self.config.case_base_path
        
        try:
            self.case_base.save_to_file(save_path)
            
            return True
        except Exception as e:
            return False
    
    def learn_from_feedback(self, feedback_data: FeedbackData, request: Request):
        """
        Aprende de feedback del usuario y actualiza pesos de similitud.
        
        Implementa aprendizaje adaptativo: ajusta la importancia relativa
        de cada criterio según la satisfacción del cliente.
        
        Args:
            feedback_data: Datos de feedback del cliente (con dimensiones separadas)
            request: Request original del caso
        """
        # Convertir FeedbackData a objeto Feedback compatible
        try:
            from .core.models import Feedback
        except ImportError:
            from core.models import Feedback
        
        # Usar las dimensiones específicas de FeedbackData si están disponibles
        # Si no, usar el score general como fallback
        price_sat = feedback_data.price_satisfaction if feedback_data.price_satisfaction is not None else feedback_data.score
        cultural_sat = feedback_data.cultural_satisfaction if feedback_data.cultural_satisfaction is not None else (feedback_data.score if request.cultural_preference else 3.0)
        flavor_sat = feedback_data.flavor_satisfaction if feedback_data.flavor_satisfaction is not None else feedback_data.score
        
        feedback = Feedback(
            overall_satisfaction=feedback_data.score,
            price_satisfaction=price_sat,
            cultural_satisfaction=cultural_sat,
            flavor_satisfaction=flavor_sat,
            dietary_satisfaction=5.0 if feedback_data.success else 2.0,
            comments=feedback_data.comments
        )
        
        # Actualizar pesos mediante aprendizaje
        adjustments = self.weight_learner.update_from_feedback(feedback, request)
        
        # Actualizar pesos en el retriever
        self.retriever.similarity_calc.weights = self.weight_learner.get_current_weights()
        
        if self.config.verbose and adjustments:
            print(f"\n📊 Pesos ajustados mediante aprendizaje:")
            for weight_name, delta in adjustments.items():
                print(f"   {weight_name}: {delta:+.4f}")
            
            # Mostrar resumen de aprendizaje
            summary = self.weight_learner.get_learning_summary()
            if summary.get('most_changed'):
                print(f"\n📈 Pesos más cambiados desde inicio:")
                for item in summary['most_changed']:
                    print(f"   {item['weight']}: {item['change_pct']}")
    
    def save_learning_data(self, filepath: str = 'data/learning_history.json'):
        """
        Guarda historial de aprendizaje a archivo.
        
        Args:
            filepath: Ruta donde guardar los datos
        """
        self.weight_learner.save_learning_history(filepath)
        print(f"✅ Historial de aprendizaje guardado en: {filepath}")
    
    def plot_learning_evolution(self, output_dir: str = 'docs'):
        """
        Genera gráficas de evolución del aprendizaje.
        
        Args:
            output_dir: Directorio donde guardar las gráficas
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        self.weight_learner.plot_evolution(f"{output_dir}/weight_evolution.png")
        self.weight_learner.plot_feedback_correlation(f"{output_dir}/feedback_correlation.png")
        
        print(f"✅ Gráficas generadas en: {output_dir}/")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema CBR.
        
        Returns:
            Diccionario con estadísticas
        """
        retention_stats = self.retainer.get_retention_statistics()
        learning_summary = self.weight_learner.get_learning_summary()
        
        return {
            "system": {
                "version": "1.0.0",
                "config": {
                    "max_proposals": self.config.max_proposals,
                    "min_similarity": self.config.min_similarity,
                    "learning_enabled": self.config.enable_learning
                }
            },
            "case_base": retention_stats,
            "learning": learning_summary,
            "supported_events": [e.value for e in EventType],
            "supported_styles": [s.value for s in CulinaryStyle],
            "supported_seasons": [s.value for s in Season],
            "cultural_traditions": list(CULTURAL_TRADITIONS.keys())
        }
    
    def explain_style(self, style: CulinaryStyle) -> str:
        """
        Obtiene explicación detallada de un estilo culinario.
        
        Args:
            style: Estilo a explicar
            
        Returns:
            Descripción del estilo
        """
        description = STYLE_DESCRIPTIONS.get(style, "")
        signature = CHEF_SIGNATURES.get(style, {})
        
        lines = [f"Estilo: {style.value.upper()}"]
        lines.append("=" * 40)
        lines.append(description)
        
        if signature:
            lines.append("")
            lines.append(f"Chef de referencia: {signature.get('chef', 'N/A')}")
            lines.append(f"Restaurante: {signature.get('restaurant', 'N/A')}")
            lines.append(f"Características: {', '.join(signature.get('characteristics', []))}")
        
        return "\n".join(lines)


def create_cbr_system(case_base_path: Optional[str] = None,
                      verbose: bool = False) -> ChefDigitalCBR:
    """
    Factory function para crear el sistema CBR.
    
    Args:
        case_base_path: Ruta a la base de casos
        verbose: Modo verbose
        
    Returns:
        Instancia configurada del sistema CBR
    """
    config = CBRConfig(
        case_base_path=case_base_path or "cases.json",
        verbose=verbose
    )
    
    return ChefDigitalCBR(config)


# Ejemplo de uso
if __name__ == "__main__":
    # Crear sistema
    cbr = create_cbr_system(verbose=True)
    
    # Crear solicitud de ejemplo
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_max=75.0,
        season=Season.SPRING,
        preferred_style=CulinaryStyle.GOURMET,
        required_diets=["vegetariano"]
    )
    
    # Procesar solicitud
    result = cbr.process_request(request)
    
    # Mostrar resultado
    print(result.explanations)
    
    if result.success:
        print(f"\n✅ Se generaron {len(result.proposed_menus)} propuestas")
    else:
        print("\n❌ No se pudieron generar propuestas")
    
    print(f"\n⏱️ Tiempo de procesamiento: {result.processing_time:.2f}s")
