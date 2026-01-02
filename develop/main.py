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

from core.models import (
    Request, Menu, Case, Dish, Beverage, ProposedMenu,
    EventType, Season, CulinaryStyle, DishType
)
from core.case_base import CaseBase
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
        self.retriever = CaseRetriever(self.case_base)
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
        retrieved_cases = self._retrieve_phase(request)
        stats["cases_retrieved"] = len(retrieved_cases)
        
        if not retrieved_cases:
            # Sin casos similares, intentar generación desde conocimiento
            retrieved_cases = self._generate_from_knowledge(request)
        
        # FASE 2-3: REUSE/ADAPT + REVISE para cada caso
        for case, similarity in retrieved_cases:
            if len(proposed_menus) >= self.config.max_proposals * 2:  # Recuperar más para diversificar
                break
            
            # REUSE/ADAPT
            adapted_menu, adaptations = self._adapt_phase(case, request)
            stats["cases_adapted"] += 1
            
            # REVISE
            validation = self._revise_phase(adapted_menu, request)
            
            if validation.is_valid:
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
        
        # Generar explicaciones
        explanations = self.explainer.generate_full_report(
            proposed_menus, rejected_cases, request
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
    
    def _retrieve_phase(self, request: Request) -> List[Tuple[Case, float]]:
        """
        Ejecuta la fase RETRIEVE del ciclo CBR.
        
        Args:
            request: Solicitud del cliente
            
        Returns:
            Lista de (caso, similitud) ordenada por similitud
        """
        # Recuperar casos candidatos
        candidates = self.retriever.retrieve(
            request,
            k=self.config.max_proposals * 3  # Recuperar más para tener opciones
        )
        
        # Filtrar por similitud mínima y convertir a tuplas (case, similarity)
        filtered = [
            (result.case, result.similarity) for result in candidates
            if result.similarity >= self.config.min_similarity
        ]
        
        return filtered
    
    def _adapt_phase(self, case: Case, request: Request) -> Tuple[Menu, List[str]]:
        """
        Ejecuta la fase REUSE/ADAPT del ciclo CBR.
        
        Args:
            case: Caso a adaptar
            request: Solicitud del cliente
            
        Returns:
            Tupla (menú adaptado, lista de adaptaciones)
        """
        # Usar el CaseAdapter para adaptar el caso
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
            # Fallback: retornar menú original
            return case.menu, [f"Caso base sin adaptar: {case.id}"]
    
    def _revise_phase(self, menu: Menu, request: Request) -> ValidationResult:
        """
        Ejecuta la fase REVISE del ciclo CBR.
        
        Args:
            menu: Menú a validar
            request: Solicitud del cliente
            
        Returns:
            Resultado de la validación
        """
        # Validación simple - por ahora aceptar todos los menús
        # TODO: Implementar validación real
        from cycle.revise import ValidationStatus
        return ValidationResult(
            menu=menu,
            status=ValidationStatus.VALID,
            issues=[],
            score=0.8
        )
    
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
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema CBR.
        
        Returns:
            Diccionario con estadísticas
        """
        retention_stats = self.retainer.get_retention_statistics()
        
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
