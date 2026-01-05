"""
Módulo de generación de explicaciones para el sistema CBR.

Este módulo es crucial para la transparencia del sistema,
permitiendo explicar:
1. Por qué se seleccionó un menú particular
2. Por qué ciertos menús fueron descartados
3. Qué adaptaciones se realizaron y por qué
4. La influencia del estilo culinario elegido

Sigue las tradiciones culinarias de chefs como:
- Ferran Adrià (creatividad, texturas, técnicas moleculares)
- Juan Mari Arzak (cocina vasca innovadora)
- Paul Bocuse (nouvelle cuisine, tradición francesa)
- René Redzepi/Noma (ingredientes locales, temporada)
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from ..core.models import (
    Case, Menu, Request, Dish, ProposedMenu,
    CulinaryStyle, EventType, Season, DishType, Flavor
)
from ..core.knowledge import (
    STYLE_DESCRIPTIONS, EVENT_STYLE_PREFERENCES,
    FLAVOR_COMPATIBILITY, CATEGORY_INCOMPATIBILITIES,
    CALORIE_RANGES, CULTURAL_TRADITIONS, WINE_COMPATIBILITY,
    CHEF_SIGNATURES
)


def _get_menu_dishes(menu: Menu) -> List[Dish]:
    """Helper para obtener todos los platos de un menú como lista."""
    dishes = []
    if menu.starter:
        dishes.append(menu.starter)
    if menu.main_course:
        dishes.append(menu.main_course)
    if menu.dessert:
        dishes.append(menu.dessert)
    return dishes


class ExplanationType(Enum):
    """Tipos de explicación"""
    SELECTION = "selection"          # Por qué se seleccionó
    REJECTION = "rejection"          # Por qué se rechazó
    ADAPTATION = "adaptation"        # Qué adaptaciones se hicieron
    SIMILARITY = "similarity"        # Por qué es similar
    STYLE = "style"                  # Influencia del estilo culinario
    PAIRING = "pairing"              # Maridaje de bebidas
    CULTURAL = "cultural"            # Tradición cultural


@dataclass
class Explanation:
    """
    Una explicación generada por el sistema.
    """
    type: ExplanationType
    title: str
    content: str
    details: List[str]
    confidence: float = 1.0


class ExplanationGenerator:
    """
    Generador de explicaciones para el sistema CBR.
    
    Proporciona explicaciones claras y útiles sobre
    las decisiones del sistema, siguiendo la filosofía
    de los grandes chefs que inspiran el sistema.
    """
    
    def __init__(self):
        """Inicializa el generador de explicaciones"""
        pass
    
    def generate_selection_explanation(self, menu: ProposedMenu, 
                                        request: Request,
                                        retrieval_result=None) -> Explanation:
        """
        Genera explicación de por qué se seleccionó un menú.
        
        Args:
            menu: Menú propuesto seleccionado
            request: Solicitud original
            retrieval_result: Resultado detallado de RETRIEVE (opcional)
            
        Returns:
            Explicación de la selección
        """
        details = []
        
        # RETRIEVE: Desglose de similitud si está disponible
        if retrieval_result and hasattr(retrieval_result, 'similarity_details'):
            details.append("=== FASE RETRIEVE: Selección del caso base ===")
            details.append(f"Similitud global: {menu.similarity_score:.1%}")
            details.append("\nDesglose de similitud por criterio:")
            
            sim_details = retrieval_result.similarity_details
            criteria_names = {
                'event_type': 'Tipo de evento',
                'price_range': 'Rango de precio',
                'season': 'Temporada',
                'style': 'Estilo culinario',
                'cultural': 'Tradición cultural',
                'dietary': 'Requisitos dietéticos',
                'guests': 'Número de comensales',
                'wine_preference': 'Preferencia de vino',
                'success_bonus': 'Bonus por éxito previo'
            }
            
            for key, score in sorted(sim_details.items(), key=lambda x: x[1], reverse=True):
                name = criteria_names.get(key, key)
                bar = '█' * int(score * 10)
                details.append(f"  • {name}: {score:.1%} {bar}")
        else:
            # Fallback si no hay detalles de RETRIEVE
            details.append(f"Similitud con caso exitoso previo: {menu.similarity_score:.1%}")
        
        # ADAPT: Adaptaciones realizadas
        if menu.adaptations:
            details.append("\n=== FASE ADAPT: Adaptaciones aplicadas ===")
            details.append(f"Total de adaptaciones: {len(menu.adaptations)}")
            for adaptation in menu.adaptations:
                details.append(f"  • {adaptation}")
        
        # REVISE: Validación
        if menu.validation_result:
            details.append("\n=== FASE REVISE: Validación ===")
            details.append(f"Estado: {menu.validation_result.status.value}")
            if menu.validation_result.score:
                details.append(f"Puntuación de validación: {menu.validation_result.score:.1f}")
            
            # Warnings si existen
            warnings = [i for i in menu.validation_result.issues if i.severity == "warning"]
            if warnings:
                details.append(f"Advertencias: {len(warnings)}")
                for w in warnings[:3]:  # Mostrar máximo 3
                    details.append(f"  ⚠ {w.message}")
        
        # Adecuación al evento
        event_desc = self._get_event_description(request.event_type)
        details.append(f"\nDiseñado específicamente para {event_desc}")
        
        # Temporada
        season_desc = self._get_season_description(request.season)
        details.append(f"Adaptado a la temporada de {season_desc}")
        
        # Presupuesto
        details.append(
            f"Ajustado al presupuesto de {request.price_max:.2f}€ por persona"
        )
        
        # Requisitos dietéticos
        if request.required_diets:
            diets = ", ".join(request.required_diets)
            details.append(f"Respeta las restricciones dietéticas: {diets}")
        
        return Explanation(
            type=ExplanationType.SELECTION,
            title="Por qué se seleccionó este menú",
            content="",
            details=details,
            confidence=menu.similarity_score
        )
    
    def generate_rejection_explanation(self, case: Case, 
                                        request: Request,
                                        reasons: List[str]) -> Explanation:
        """
        Genera explicación de por qué se descartó un menú.
        
        Args:
            case: Caso descartado
            request: Solicitud original
            reasons: Razones del rechazo
            
        Returns:
            Explicación del rechazo
        """
        details = []
        
        for reason in reasons:
            # Traducir razones técnicas a explicaciones amigables
            if "budget" in reason.lower() or "presupuesto" in reason.lower():
                details.append(
                    "El precio del menú excede el presupuesto establecido"
                )
            elif "diet" in reason.lower() or "dieta" in reason.lower():
                details.append(
                    "Contiene ingredientes no compatibles con las restricciones dietéticas"
                )
            elif "season" in reason.lower() or "temporada" in reason.lower():
                details.append(
                    "Los ingredientes no son óptimos para la temporada actual"
                )
            elif "event" in reason.lower() or "evento" in reason.lower():
                details.append(
                    "El estilo no es el más adecuado para este tipo de evento"
                )
            elif "similarity" in reason.lower() or "similitud" in reason.lower():
                details.append(
                    "Otro menú se ajusta mejor a los requisitos especificados"
                )
            elif "calor" in reason.lower() or "temperature" in reason.lower():
                details.append(
                    "La combinación de temperaturas no es la óptima"
                )
            else:
                details.append(reason)
        
        content = (
            f"Este menú fue considerado pero finalmente descartado. "
            f"Aunque tiene cualidades positivas, otros menús se ajustan "
            f"mejor a los requisitos específicos del evento."
        )
        
        return Explanation(
            type=ExplanationType.REJECTION,
            title="Por qué se descartó este menú",
            content=content,
            details=details
        )
    
    def generate_adaptation_explanation(self, original_menu: Menu,
                                         adapted_menu: Menu,
                                         adaptations: List[str]) -> Explanation:
        """
        Genera explicación de las adaptaciones realizadas.
        
        Args:
            original_menu: Menú original del caso base
            adapted_menu: Menú adaptado
            adaptations: Lista de adaptaciones realizadas
            
        Returns:
            Explicación de las adaptaciones
        """
        details = []
        
        for adaptation in adaptations:
            details.append(f"  - {adaptation}")
        
        content = (
            f"El menú ha sido personalizado partiendo de un caso exitoso "
            f"previo. Se han realizado {len(adaptations)} adaptaciones para "
            f"ajustarlo perfectamente a sus necesidades específicas."
        )
        
        return Explanation(
            type=ExplanationType.ADAPTATION,
            title="Adaptaciones realizadas",
            content=content,
            details=details
        )
    
    def generate_style_explanation(self, style: CulinaryStyle,
                                    menu: Menu) -> Explanation:
        """
        Genera explicación sobre la influencia del estilo culinario.
        
        Args:
            style: Estilo culinario aplicado
            menu: Menú con el estilo aplicado
            
        Returns:
            Explicación del estilo
        """
        style_desc = STYLE_DESCRIPTIONS.get(style, "")
        
        details = []
        
        # Explicar cómo se refleja en el menú
        details.append("")
        details.append("Reflejo en el menú:")
        
        for dish in _get_menu_dishes(menu):
            if style in dish.styles:
                details.append(
                    f"  • {dish.name}: representa la esencia del estilo {style.value}"
                )
        
        content = style_desc or f"Menú diseñado siguiendo el estilo {style.value}"
        
        return Explanation(
            type=ExplanationType.STYLE,
            title=f"Estilo Culinario: {style.value.title()}",
            content=content,
            details=details
        )
    
    def generate_pairing_explanation(self, menu: Menu) -> Explanation:
        """
        Genera explicación del maridaje de bebidas.
        
        Args:
            menu: Menú con bebidas asignadas
            
        Returns:
            Explicación del maridaje
        """
        details = []
        
        for dish in _get_menu_dishes(menu):
            if dish.beverages:
                for beverage in dish.beverages:
                    compatibility = self._get_wine_compatibility_reason(dish, beverage)
                    details.append(
                        f"  {dish.name} con {beverage.name}: {compatibility}"
                    )
        
        content = (
            "El maridaje ha sido seleccionado siguiendo los principios clásicos "
            "de armonía entre platos y bebidas, considerando intensidades de "
            "sabor, texturas y tradiciones regionales."
        )
        
        return Explanation(
            type=ExplanationType.PAIRING,
            title="Maridaje de bebidas",
            content=content,
            details=details
        )
    
    def generate_cultural_explanation(self, culture: str,
                                       dishes: List[Dish]) -> Explanation:
        """
        Genera explicación sobre la tradición cultural.
        
        Args:
            culture: Cultura/tradición aplicada
            dishes: Platos de esa tradición
            
        Returns:
            Explicación cultural
        """
        tradition_info = CULTURAL_TRADITIONS.get(culture, {})
        
        details = []
        
        if tradition_info:
            details.append(f"Región: {tradition_info.get('region', 'N/A')}")
            
            ingredients = tradition_info.get('typical_ingredients', [])
            if ingredients:
                details.append(f"Ingredientes típicos: {', '.join(ingredients[:5])}")
            
            techniques = tradition_info.get('techniques', [])
            if techniques:
                details.append(f"Técnicas características: {', '.join(techniques[:3])}")
        
        details.append("")
        details.append("Platos representativos:")
        for dish in dishes:
            details.append(f"  • {dish.name}")
        
        content = (
            f"Este menú incorpora elementos de la tradición culinaria {culture}, "
            f"una de las más ricas del Mediterráneo y Oriente Medio. "
            f"Los platos seleccionados representan la esencia de esta cultura."
        )
        
        return Explanation(
            type=ExplanationType.CULTURAL,
            title=f"Tradición Culinaria: {culture.title()}",
            content=content,
            details=details
        )
    
    def generate_full_report(self, proposed_menus: List[ProposedMenu],
                             rejected_cases: List[Dict],
                             request: Request,
                             retrieval_results: Optional[List] = None) -> str:
        """
        Genera un informe completo de explicaciones del proceso CBR.
        
        Args:
            proposed_menus: Menús propuestos (hasta 3)
            rejected_cases: Casos rechazados con razones
            request: Solicitud original
            retrieval_results: Resultados detallados de RETRIEVE (opcional)
            
        Returns:
            Informe en formato texto con explicabilidad completa
        """
        lines = []
        lines.append("=" * 80)
        lines.append("INFORME COMPLETO DE RAZONAMIENTO CBR - Chef Digital")
        lines.append("=" * 80)
        lines.append("")
        
        # Resumen de la solicitud
        lines.append("SOLICITUD RECIBIDA")
        lines.append("-" * 80)
        lines.append(f"Tipo de evento: {request.event_type.value}")
        lines.append(f"Número de comensales: {request.num_guests}")
        lines.append(f"Presupuesto por persona: {request.price_max:.2f}€")
        lines.append(f"Temporada: {request.season.value}")
        if request.preferred_style:
            lines.append(f"Estilo preferido: {request.preferred_style.value}")
        if request.cultural_preference:
            lines.append(f"Preferencia cultural: {request.cultural_preference.value}")
        if request.required_diets:
            lines.append(f"Restricciones dietéticas: {', '.join(request.required_diets)}")
        if request.restricted_ingredients:
            lines.append(f"Ingredientes prohibidos: {', '.join(request.restricted_ingredients)}")
        lines.append("")
        
        # FASE RETRIEVE: Mostrar resultados detallados
        if retrieval_results:
            lines.append("FASE 1: RETRIEVE - Recuperación de casos similares")
            lines.append("-" * 80)
            lines.append(f"Casos analizados: {len(retrieval_results)}")
            lines.append("")
            
            for i, result in enumerate(retrieval_results[:5], 1):  # Top 5
                case_name = result.case.id if hasattr(result.case, 'id') else f"Caso {i}"
                lines.append(f"  Caso #{i}: {case_name} (Similitud: {result.similarity:.1%})")
                
                if hasattr(result, 'similarity_details'):
                    lines.append("    Desglose de similitud:")
                    sim_details = result.similarity_details
                    
                    criteria_names = {
                        'event_type': 'Tipo de evento',
                        'price_range': 'Rango de precio',
                        'season': 'Temporada',
                        'style': 'Estilo culinario',
                        'cultural': 'Tradición cultural',
                        'dietary': 'Requisitos dietéticos',
                        'guests': 'Número de comensales',
                        'wine_preference': 'Preferencia de vino',
                        'success_bonus': 'Bonus por éxito previo'
                    }
                    
                    for key in ['event_type', 'price_range', 'season', 'cultural', 'dietary']:
                        if key in sim_details:
                            score = sim_details[key]
                            name = criteria_names.get(key, key)
                            bar = '█' * int(score * 20)
                            lines.append(f"      • {name:25s}: {score:5.1%} {bar}")
                lines.append("")
            lines.append("")
        
        # Menús propuestos
        lines.append("FASE 2-3: ADAPT + REVISE - Menús adaptados y validados")
        lines.append("-" * 80)
        
        for i, menu in enumerate(proposed_menus, 1):
            lines.append(f"\n{'='*80}")
            lines.append(f"PROPUESTA #{i}")
            lines.append(f"{'='*80}")
            
            # Composición del menú
            lines.append("\nCOMPOSICIÓN DEL MENÚ:")
            lines.append(f"  Entrante:     {menu.menu.starter.name}")
            lines.append(f"  Plato Fuerte: {menu.menu.main_course.name}")
            lines.append(f"  Postre:       {menu.menu.dessert.name}")
            if menu.menu.beverage:
                lines.append(f"  Bebida:       {menu.menu.beverage.name}")
            lines.append(f"\n  Precio total: {menu.menu.total_price:.2f}€ por persona")
            lines.append(f"  Calorías totales: {menu.menu.total_calories:.2f} kcal")
            
            # RETRIEVE: Caso base
            lines.append(f"\nRETRIEVE: Caso base seleccionado")
            lines.append(f"  - Caso origen: {menu.source_case.id}")
            lines.append(f"  - Similitud inicial: {menu.similarity_score:.1%}")
            
            # Buscar detalles de retrieve si están disponibles
            if retrieval_results:
                matching_result = next((r for r in retrieval_results if r.case.id == menu.source_case.id), None)
                if matching_result and hasattr(matching_result, 'similarity_details'):
                    lines.append("  - Desglose de similitud:")
                    sim_details = matching_result.similarity_details
                    for key, score in sorted(sim_details.items(), key=lambda x: x[1], reverse=True):
                        if score > 0:
                            lines.append(f"      {key}: {score:.1%}")
            
            # ADAPT: Adaptaciones realizadas
            lines.append(f"\nADAPT: Adaptaciones aplicadas ({len(menu.adaptations)} total)")
            if menu.adaptations:
                for j, adaptation in enumerate(menu.adaptations, 1):
                    lines.append(f"  {j}. {adaptation}")
            else:
                lines.append("  - Menú usado sin modificaciones")
            
            # REVISE: Validación
            if menu.validation_result:
                lines.append(f"\nREVISE: Validación del menú")
                lines.append(f"  - Estado: {menu.validation_result.status.value.upper()}")
                if menu.validation_result.score:
                    lines.append(f"  - Puntuación de calidad: {menu.validation_result.score:.1f}")
                
                # Advertencias
                warnings = [i for i in menu.validation_result.issues if i.severity == "warning"]
                if warnings:
                    lines.append(f"  - Advertencias ({len(warnings)}):")
                    for w in warnings[:5]:
                        lines.append(f"    ⚠ {w.message}")
                
                # Explicaciones de validación
                if menu.validation_result.explanations:
                    lines.append(f"  - Explicaciones de validación:")
                    for exp in menu.validation_result.explanations[:5]:
                        lines.append(f"      {exp}")
            
            lines.append("")
        
        # Menús descartados
        if rejected_cases:
            lines.append(f"\n{'='*80}")
            lines.append("MENÚS DESCARTADOS EN FASE REVISE")
            lines.append("-" * 80)
            lines.append(f"Total de casos rechazados: {len(rejected_cases)}")
            lines.append("")
            
            for idx, rejected in enumerate(rejected_cases[:5], 1):  # Máximo 5
                case = rejected.get('case')
                reasons = rejected.get('reasons', [])
                similarity = rejected.get('similarity', 0.0)
                menu_name = rejected.get('menu_name', f'Menú {case.id}' if case else 'Menú')
                
                lines.append(f"  {idx}. {menu_name} (Similitud: {similarity:.1%})")
                
                # Mostrar razones de rechazo
                if reasons:
                    if isinstance(reasons, list):
                        # Si son ValidationIssue objects
                        for issue in reasons[:3]:
                            if hasattr(issue, 'message'):
                                lines.append(f"     - {issue.message}")
                            else:
                                lines.append(f"     - {issue}")
                    else:
                        lines.append(f"     - {reasons}")
                lines.append("")
        
        # Resumen final
        lines.append(f"\n{'='*80}")
        lines.append("RESUMEN DEL PROCESO CBR")
        lines.append("-" * 80)
        lines.append(f"- Casos analizados en RETRIEVE: {len(retrieval_results) if retrieval_results else 'N/A'}")
        lines.append(f"- Menús adaptados en ADAPT: {len(proposed_menus) + len(rejected_cases)}")
        lines.append(f"- Menús validados en REVISE: {len(proposed_menus)}")
        lines.append(f"- Menús rechazados: {len(rejected_cases)}")
        lines.append(f"- Propuestas finales presentadas: {len(proposed_menus)}")
        
        lines.append("\n" + "=" * 80)
        lines.append("Sistema CBR de Chef Digital - Explicabilidad Completa")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    # Métodos auxiliares privados
    
    def _get_event_description(self, event_type: EventType) -> str:
        """Obtiene descripción amigable del tipo de evento"""
        descriptions = {
            EventType.WEDDING: "una boda, momento especial que requiere elegancia y sofisticación",
            EventType.CORPORATE: "un evento corporativo, donde la profesionalidad es clave",
            EventType.CONGRESS: "un congreso, con necesidades de servicio eficiente",
            EventType.FAMILIAR: "una celebración familiar, con ambiente cálido y cercano",
            EventType.CHRISTENING: "un bautizo, celebración íntima y tradicional",
            EventType.COMMUNION: "una comunión, evento religioso y festivo"
        }
        return descriptions.get(event_type, f"un evento de tipo {event_type.value}")
    
    def _get_season_description(self, season: Season) -> str:
        """Obtiene descripción amigable de la temporada"""
        descriptions = {
            Season.SPRING: "primavera, con ingredientes frescos y ligeros",
            Season.SUMMER: "verano, privilegiando platos refrescantes",
            Season.AUTUMN: "otoño, con sabores cálidos y reconfortantes",
            Season.WINTER: "invierno, con platos más contundentes"
        }
        return descriptions.get(season, season.value)
    
    def _get_wine_compatibility_reason(self, dish: Dish, beverage) -> str:
        """Obtiene razón de compatibilidad vino-plato"""
        category = dish.category
        beverage_type = getattr(beverage, 'type', 'unknown')
        
        if 'tinto' in str(beverage_type).lower():
            if category in ['carne', 'caza']:
                return "El tinto potencia los sabores intensos de la carne"
            return "Selección para equilibrar el plato"
        elif 'blanco' in str(beverage_type).lower():
            if category in ['pescado', 'marisco']:
                return "El blanco fresco complementa los sabores del mar"
            return "Armonía de frescura y delicadeza"
        elif 'rosado' in str(beverage_type).lower():
            return "Versatilidad que armoniza con el plato"
        elif 'cava' in str(beverage_type).lower() or 'champagne' in str(beverage_type).lower():
            return "Elegancia y celebración en cada copa"
        else:
            return "Maridaje seleccionado por complementariedad"
