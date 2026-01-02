"""
Fase REVISE del ciclo CBR.

Este módulo implementa la validación y revisión de las propuestas
generadas. Es la tercera fase del ciclo CBR.

La revisión incluye:
1. Validación de restricciones gastronómicas
2. Validación de proporciones de precio
3. Verificación de compatibilidades
4. Generación de explicaciones detalladas
5. Identificación de propuestas a descartar y por qué

Los menús que pasan la validación se presentan al usuario
con explicaciones comprensibles.
"""

from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from core.models import (
    Menu, Request, Dish,
    Season, EventType, DishCategory, Flavor, Temperature, Complexity
)
from cycle.adapt import AdaptationResult
from core.knowledge import (
    are_categories_compatible, are_flavors_compatible,
    is_starter_temperature_appropriate, is_calorie_count_appropriate,
    is_dessert_appropriate_after_fatty, is_complexity_appropriate,
    get_calorie_range, validate_price_proportions, classify_price_category
)


class ValidationStatus(Enum):
    """Estado de validación de un menú"""
    VALID = "valid"
    VALID_WITH_WARNINGS = "valid_with_warnings"
    INVALID = "invalid"


@dataclass
class ValidationIssue:
    """
    Representa un problema encontrado durante la validación.
    """
    severity: str  # "error", "warning", "info"
    category: str  # tipo de validación que falló
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """
    Resultado de la validación de un menú.
    """
    menu: Menu
    status: ValidationStatus
    issues: List[ValidationIssue] = field(default_factory=list)
    score: float = 0.0
    explanations: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Retorna True si el menú es válido (puede presentarse)"""
        return self.status in [ValidationStatus.VALID, ValidationStatus.VALID_WITH_WARNINGS]
    
    def get_rejection_reason(self) -> str:
        """Obtiene la razón principal de rechazo"""
        errors = [i for i in self.issues if i.severity == "error"]
        if errors:
            return errors[0].message
        return "Menú rechazado por múltiples advertencias"


class MenuReviser:
    """
    Revisor de menús del sistema CBR.
    
    Implementa la fase REVISE del ciclo CBR,
    validando y refinando las propuestas generadas.
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Inicializa el revisor.
        
        Args:
            strict_mode: Si True, las advertencias también invalidan
        """
        self.strict_mode = strict_mode
        
        # Umbrales de validación
        self.max_warnings = 3  # Máximo de advertencias antes de invalidar
    
    def revise(self, adaptation_results: List[AdaptationResult],
               request: Request) -> List[ValidationResult]:
        """
        Revisa y valida las propuestas de adaptación.
        
        Args:
            adaptation_results: Resultados de la fase de adaptación
            request: Solicitud original del cliente
            
        Returns:
            Lista de resultados de validación
        """
        validation_results = []
        
        for result in adaptation_results:
            validation = self._validate_menu(result.adapted_menu, request)
            
            # Incorporar información de adaptación
            if result.adaptations_made:
                validation.explanations.extend([
                    f"Adaptación: {a}" for a in result.adaptations_made
                ])
            
            validation_results.append(validation)
        
        # Ordenar por puntuación
        validation_results.sort(key=lambda v: v.score, reverse=True)
        
        # Filtrar solo válidos
        valid_results = [v for v in validation_results if v.is_valid()]
        
        return valid_results
    
    def _validate_menu(self, menu: Menu, request: Request) -> ValidationResult:
        """
        Valida un menú completo.
        
        Args:
            menu: Menú a validar
            request: Solicitud del cliente
            
        Returns:
            Resultado de validación
        """
        issues = []
        explanations = []
        
        # 1. Validar precio en rango
        price_issues, price_exp = self._validate_price(menu, request)
        issues.extend(price_issues)
        explanations.extend(price_exp)
        
        # 2. Validar cultura si fue solicitada
        cultural_issues, cultural_exp = self._validate_culture(menu, request)
        issues.extend(cultural_issues)
        explanations.extend(cultural_exp)
        
        # 3. Validar temperatura del starter para temporada
        temp_issues, temp_exp = self._validate_temperature(menu, request)
        issues.extend(temp_issues)
        explanations.extend(temp_exp)
        
        # 3. Validar compatibilidad de sabores
        flavor_issues, flavor_exp = self._validate_flavors(menu)
        issues.extend(flavor_issues)
        explanations.extend(flavor_exp)
        
        # 4. Validar categorías incompatibles
        cat_issues, cat_exp = self._validate_categories(menu)
        issues.extend(cat_issues)
        explanations.extend(cat_exp)
        
        # 5. Validar calorías según temporada
        cal_issues, cal_exp = self._validate_calories(menu, request)
        issues.extend(cal_issues)
        explanations.extend(cal_exp)
        
        # 6. Validar postre tras plato graso
        dessert_issues, dessert_exp = self._validate_dessert_after_fatty(menu)
        issues.extend(dessert_issues)
        explanations.extend(dessert_exp)
        
        # 7. Validar complejidad para evento
        complex_issues, complex_exp = self._validate_complexity(menu, request)
        issues.extend(complex_issues)
        explanations.extend(complex_exp)
        
        # 8. Validar proporciones de precio
        prop_issues, prop_exp = self._validate_proportions(menu, request)
        issues.extend(prop_issues)
        explanations.extend(prop_exp)
        
        # 9. Validar restricciones dietéticas (crítico)
        diet_issues, diet_exp = self._validate_diets(menu, request)
        issues.extend(diet_issues)
        explanations.extend(diet_exp)
        
        # 10. Validar ingredientes restringidos (crítico)
        ing_issues, ing_exp = self._validate_ingredients(menu, request)
        issues.extend(ing_issues)
        explanations.extend(ing_exp)
        
        # Determinar estado
        errors = sum(1 for i in issues if i.severity == "error")
        warnings = sum(1 for i in issues if i.severity == "warning")
        
        if errors > 0:
            status = ValidationStatus.INVALID
        elif warnings > self.max_warnings or (self.strict_mode and warnings > 0):
            status = ValidationStatus.INVALID
        elif warnings > 0:
            status = ValidationStatus.VALID_WITH_WARNINGS
        else:
            status = ValidationStatus.VALID
        
        # Calcular puntuación
        score = self._calculate_score(menu, request, issues)
        
        # Agregar explicaciones del menú original
        explanations.extend(menu.explanation)
        
        return ValidationResult(
            menu=menu,
            status=status,
            issues=issues,
            score=score,
            explanations=list(set(explanations))  # Eliminar duplicados
        )
    
    def _validate_price(self, menu: Menu, 
                        request: Request) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida que el precio esté en el rango solicitado"""
        issues = []
        explanations = []
        
        if menu.total_price < request.price_min:
            diff = request.price_min - menu.total_price
            issues.append(ValidationIssue(
                severity="warning",
                category="price",
                message=f"Precio ({menu.total_price:.2f}€) por debajo del mínimo ({request.price_min:.2f}€)",
                suggestion="Considere opciones premium para alcanzar el presupuesto"
            ))
        elif menu.total_price > request.price_max:
            diff = menu.total_price - request.price_max
            issues.append(ValidationIssue(
                severity="error",
                category="price",
                message=f"Precio ({menu.total_price:.2f}€) excede el máximo ({request.price_max:.2f}€)",
                suggestion="Buscar alternativas más económicas"
            ))
        else:
            explanations.append(
                f"Precio {menu.total_price:.2f}€ dentro del presupuesto"
            )
        
        return issues, explanations
    
    def _validate_culture(self, menu: Menu,
                          request: Request) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida la adaptación cultural del menú"""
        issues = []
        explanations = []
        
        # Solo validar si el usuario pidió una cultura específica
        if not request.cultural_preference:
            return issues, explanations
        
        # Verificar si el menú tiene tema cultural
        if menu.cultural_theme:
            if menu.cultural_theme == request.cultural_preference:
                explanations.append(
                    f"Menú adaptado a cultura {request.cultural_preference.value}"
                )
            else:
                # Diferente cultura - calcular qué tan bien se adaptó
                from cycle.ingredient_adapter import get_ingredient_adapter
                adapter = get_ingredient_adapter()
                
                cultural_scores = []
                for dish_attr in ['starter', 'main_course', 'dessert']:
                    dish = getattr(menu, dish_attr)
                    if dish.ingredients:
                        score = adapter.get_cultural_score(
                            dish.ingredients, 
                            request.cultural_preference
                        )
                        cultural_scores.append(score)
                
                if cultural_scores:
                    avg_score = sum(cultural_scores) / len(cultural_scores)
                    
                    if avg_score >= 0.6:
                        explanations.append(
                            f"Menú bien adaptado a {request.cultural_preference.value} "
                            f"(score cultural: {avg_score:.0%})"
                        )
                    elif avg_score >= 0.4:
                        issues.append(ValidationIssue(
                            severity="info",
                            category="culture",
                            message=f"Adaptación cultural moderada ({avg_score:.0%})",
                            suggestion=None
                        ))
                    else:
                        issues.append(ValidationIssue(
                            severity="warning",
                            category="culture",
                            message=f"Adaptación cultural limitada ({avg_score:.0%})",
                            suggestion="Considerar platos más representativos de la cultura"
                        ))
        
        # Informar sobre adaptaciones realizadas
        if menu.cultural_adaptations:
            num_adaptations = len(menu.cultural_adaptations)
            explanations.append(
                f"Se realizaron {num_adaptations} adaptaciones culturales"
            )
        
        return issues, explanations
    
    def _validate_temperature(self, menu: Menu,
                              request: Request) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida la temperatura del starter para la temporada"""
        issues = []
        explanations = []
        
        if request.season == Season.ALL:
            return issues, explanations
        
        if is_starter_temperature_appropriate(menu.starter.temperature, request.season):
            temp_name = {
                Temperature.HOT: "caliente",
                Temperature.WARM: "templado",
                Temperature.COLD: "frío"
            }.get(menu.starter.temperature, "")
            
            season_name = {
                Season.SUMMER: "verano",
                Season.WINTER: "invierno",
                Season.SPRING: "primavera",
                Season.AUTUMN: "otoño"
            }.get(request.season, "")
            
            explanations.append(
                f"Entrante {temp_name} apropiado para {season_name}"
            )
        else:
            issues.append(ValidationIssue(
                severity="warning",
                category="temperature",
                message=f"Temperatura del entrante ({menu.starter.temperature.value}) "
                        f"no ideal para {request.season.value}",
                suggestion="Considerar entrante con temperatura más apropiada"
            ))
        
        return issues, explanations
    
    def _validate_flavors(self, menu: Menu) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida compatibilidad de sabores entre platos"""
        issues = []
        explanations = []
        
        # Verificar starter-main
        starter_flavors = set(menu.starter.flavors)
        main_flavors = set(menu.main_course.flavors)
        
        if starter_flavors and main_flavors:
            compatible = False
            compatible_pairs = []
            
            for sf in starter_flavors:
                for mf in main_flavors:
                    if are_flavors_compatible(sf, mf):
                        compatible = True
                        compatible_pairs.append((sf.value, mf.value))
            
            if compatible:
                if compatible_pairs:
                    pair = compatible_pairs[0]
                    explanations.append(
                        f"Armonía de sabores: {pair[0]} complementa {pair[1]}"
                    )
            else:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="flavors",
                    message="Los sabores del entrante y principal podrían no armonizar bien",
                    suggestion="Buscar platos con sabores más complementarios"
                ))
        
        return issues, explanations
    
    def _validate_categories(self, menu: Menu) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida que las categorías de platos sean compatibles"""
        issues = []
        explanations = []
        
        # Starter-Main
        if not are_categories_compatible(menu.starter.category, menu.main_course.category):
            issues.append(ValidationIssue(
                severity="error",
                category="categories",
                message=f"Categorías incompatibles: {menu.starter.category.value} "
                        f"y {menu.main_course.category.value}",
                suggestion="Elegir platos de categorías complementarias"
            ))
        else:
            explanations.append(
                f"Buena progresión: {menu.starter.category.value} → "
                f"{menu.main_course.category.value}"
            )
        
        # Main-Dessert (menos restrictivo)
        if not are_categories_compatible(menu.main_course.category, menu.dessert.category):
            issues.append(ValidationIssue(
                severity="warning",
                category="categories",
                message=f"Categorías posiblemente repetitivas entre principal y postre"
            ))
        
        return issues, explanations
    
    def _validate_calories(self, menu: Menu,
                           request: Request) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida las calorías totales según la temporada"""
        issues = []
        explanations = []
        
        if request.season == Season.ALL:
            return issues, explanations
        
        total_cal = menu.total_calories
        min_cal, max_cal = get_calorie_range(request.season)
        
        if is_calorie_count_appropriate(total_cal, request.season):
            if request.season == Season.SUMMER:
                explanations.append(f"Menú ligero ({total_cal} kcal) ideal para verano")
            elif request.season == Season.WINTER:
                explanations.append(f"Menú contundente ({total_cal} kcal) perfecto para invierno")
            else:
                explanations.append(f"Menú equilibrado ({total_cal} kcal)")
        else:
            if total_cal < min_cal:
                issues.append(ValidationIssue(
                    severity="info",
                    category="calories",
                    message=f"Menú ligero ({total_cal} kcal) para {request.season.value}",
                    suggestion="Podría añadir un plato más sustancioso"
                ))
            else:
                issues.append(ValidationIssue(
                    severity="info",
                    category="calories",
                    message=f"Menú contundente ({total_cal} kcal) para {request.season.value}",
                    suggestion="Considerar opciones más ligeras"
                ))
        
        return issues, explanations
    
    def _validate_dessert_after_fatty(self, menu: Menu) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida que el postre sea apropiado tras un plato graso"""
        issues = []
        explanations = []
        
        main_has_fatty = Flavor.FATTY in menu.main_course.flavors
        
        if main_has_fatty:
            appropriate = is_dessert_appropriate_after_fatty(
                True, menu.dessert.category, menu.dessert.flavors
            )
            
            if appropriate:
                if menu.dessert.category == DishCategory.FRUIT:
                    explanations.append(
                        "Postre de frutas refresca el paladar tras plato contundente"
                    )
                elif Flavor.SOUR in menu.dessert.flavors:
                    explanations.append(
                        "Postre con toques ácidos limpia el paladar"
                    )
            else:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="dessert",
                    message="El postre podría resultar pesado tras un plato graso",
                    suggestion="Considerar un postre más ligero o ácido"
                ))
        
        return issues, explanations
    
    def _validate_complexity(self, menu: Menu,
                             request: Request) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida la complejidad de los platos para el evento"""
        issues = []
        explanations = []
        
        # Validar complejidad del plato principal
        if is_complexity_appropriate(
            menu.main_course.complexity, request.event_type, request.price_max
        ):
            if menu.main_course.complexity == Complexity.HIGH:
                explanations.append("Plato principal de alta cocina")
            elif menu.main_course.complexity == Complexity.LOW:
                explanations.append("Plato principal accesible y familiar")
        else:
            issues.append(ValidationIssue(
                severity="warning",
                category="complexity",
                message=f"Complejidad {menu.main_course.complexity.value} "
                        f"podría no ser ideal para {request.event_type.value}",
                suggestion="Ajustar complejidad según tipo de evento"
            ))
        
        return issues, explanations
    
    def _validate_proportions(self, menu: Menu,
                              request: Request) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida las proporciones de precio entre componentes"""
        issues = []
        explanations = []
        
        category = classify_price_category(
            menu.total_price, request.price_min, request.price_max
        )
        
        food_total = menu.starter.price + menu.main_course.price + menu.dessert.price
        
        if validate_price_proportions(
            menu.starter.price, menu.main_course.price, 
            menu.dessert.price, category
        ):
            # Verificar que el main sea el más caro
            if menu.main_course.price > menu.starter.price and \
               menu.main_course.price > menu.dessert.price:
                explanations.append("Proporciones de precio bien equilibradas")
        else:
            # Verificar sanidad básica
            if menu.starter.price > menu.main_course.price:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="proportions",
                    message="El entrante es más caro que el plato principal",
                    suggestion="El plato principal debería ser el más destacado"
                ))
        
        return issues, explanations
    
    def _validate_diets(self, menu: Menu,
                        request: Request) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida que se cumplan las restricciones dietéticas"""
        issues = []
        explanations = []
        
        if not request.required_diets:
            return issues, explanations
        
        menu_diets = menu.get_all_diets()
        
        fulfilled = [d for d in request.required_diets if d in menu_diets]
        missing = [d for d in request.required_diets if d not in menu_diets]
        
        if missing:
            issues.append(ValidationIssue(
                severity="error",
                category="dietary",
                message=f"No cumple restricciones dietéticas: {', '.join(missing)}",
                suggestion="Buscar alternativas que cumplan estas dietas"
            ))
        else:
            explanations.append(
                f"Cumple dietas requeridas: {', '.join(fulfilled)}"
            )
        
        return issues, explanations
    
    def _validate_ingredients(self, menu: Menu,
                              request: Request) -> Tuple[List[ValidationIssue], List[str]]:
        """Valida que no haya ingredientes restringidos"""
        issues = []
        explanations = []
        
        if not request.restricted_ingredients:
            return issues, explanations
        
        menu_ingredients = menu.get_all_ingredients()
        
        found_restricted = [
            ing for ing in request.restricted_ingredients 
            if ing in menu_ingredients
        ]
        
        if found_restricted:
            issues.append(ValidationIssue(
                severity="error",
                category="ingredients",
                message=f"Contiene ingredientes restringidos: {', '.join(found_restricted)}",
                suggestion="Buscar platos sin estos ingredientes"
            ))
        else:
            explanations.append("No contiene ingredientes prohibidos")
        
        return issues, explanations
    
    def _calculate_score(self, menu: Menu, request: Request,
                         issues: List[ValidationIssue]) -> float:
        """
        Calcula una puntuación de calidad para el menú.
        
        Returns:
            Puntuación entre 0 y 100
        """
        score = 100.0
        
        # Penalizar por issues
        for issue in issues:
            if issue.severity == "error":
                score -= 25
            elif issue.severity == "warning":
                score -= 10
            elif issue.severity == "info":
                score -= 2
        
        # Bonus por estar en centro del rango de precio
        if request.price_max > request.price_min:
            center = (request.price_min + request.price_max) / 2
            deviation = abs(menu.total_price - center) / (request.price_max - request.price_min)
            # Bonus si está cerca del centro
            if deviation < 0.2:
                score += 5
        
        # Bonus por feedback alto si viene de un caso
        if hasattr(menu, 'source_case_feedback'):
            score += menu.source_case_feedback * 2
        
        return max(0, min(100, score))
    
    def generate_report(self, validation_results: List[ValidationResult],
                        request: Request) -> str:
        """
        Genera un informe de validación completo.
        
        Args:
            validation_results: Resultados de validación
            request: Solicitud original
            
        Returns:
            Informe en formato texto
        """
        lines = []
        lines.append("=" * 60)
        lines.append("INFORME DE VALIDACIÓN DE MENÚS")
        lines.append("=" * 60)
        lines.append("")
        
        # Resumen de la solicitud
        lines.append(f"Evento: {request.event_type.value}")
        lines.append(f"Temporada: {request.season.value}")
        lines.append(f"Presupuesto: {request.price_min:.2f}€ - {request.price_max:.2f}€")
        lines.append(f"Comensales: {request.num_guests}")
        
        if request.required_diets:
            lines.append(f"Dietas requeridas: {', '.join(request.required_diets)}")
        if request.restricted_ingredients:
            lines.append(f"Ingredientes prohibidos: {', '.join(request.restricted_ingredients)}")
        
        lines.append("")
        lines.append("-" * 60)
        
        # Resultados por menú
        valid_count = sum(1 for v in validation_results if v.is_valid())
        lines.append(f"Menús válidos: {valid_count}/{len(validation_results)}")
        lines.append("")
        
        for i, result in enumerate(validation_results, 1):
            lines.append(f"MENÚ #{i} - {result.status.value.upper()}")
            lines.append(f"  Puntuación: {result.score:.1f}/100")
            lines.append(f"  Precio: {result.menu.total_price:.2f}€")
            lines.append("")
            lines.append(f"  Entrante: {result.menu.starter.name}")
            lines.append(f"  Principal: {result.menu.main_course.name}")
            lines.append(f"  Postre: {result.menu.dessert.name}")
            lines.append(f"  Bebida: {result.menu.beverage.name}")
            lines.append("")
            
            if result.issues:
                lines.append("  Observaciones:")
                for issue in result.issues:
                    icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue.severity, "•")
                    lines.append(f"    {icon} {issue.message}")
                lines.append("")
            
            if result.explanations:
                lines.append("  Explicaciones:")
                for exp in result.explanations[:5]:  # Limitar
                    lines.append(f"    • {exp}")
                lines.append("")
            
            lines.append("-" * 60)
        
        return "\n".join(lines)
