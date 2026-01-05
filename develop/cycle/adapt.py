"""
Fase REUSE/ADAPT del ciclo CBR.

Este módulo implementa la adaptación de casos recuperados
al nuevo contexto del cliente. Es la segunda fase del ciclo CBR.

La adaptación considera:
1. Ajuste de precios al presupuesto solicitado
2. Sustitución de ingredientes por restricciones dietéticas
3. Adaptación al número de comensales
4. Ajuste de estilo culinario
5. Adaptación a la temporada

Genera uno o más menús candidatos basados en los casos recuperados.
"""

from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass, field
import random
from copy import deepcopy

from ..core.models import (
    Case, Menu, Dish, Beverage, Request,
    EventType, Season, DishType, DishCategory,
    CulturalTradition, CulinaryStyle, Flavor, Temperature, Complexity
)
from ..core.case_base import CaseBase
from .retrieve import RetrievalResult
from .ingredient_adapter import get_ingredient_adapter, IngredientSubstitution
from ..core.similarity import calculate_dish_similarity, SimilarityCalculator
from ..core.knowledge import (
    are_categories_compatible, are_flavors_compatible,
    is_starter_temperature_appropriate, is_calorie_count_appropriate,
    is_dessert_appropriate_after_fatty, get_preferred_styles_for_event,
    is_complexity_appropriate, FLAVOR_COMPATIBILITY
)


@dataclass
class AdaptationResult:
    """
    Resultado de la adaptación de un caso.
    """
    original_case: Case
    adapted_menu: Menu
    adaptations_made: List[str]
    adaptation_score: float  # Qué tan bien se adaptó (0-1)
    price_category: str  # economico, medio, premium
    original_similarity: float = 0.0  # Similitud del caso ANTES de adaptar (de RETRIEVE)
    final_similarity: float = 0.0  # Similitud del menú DESPUÉS de adaptar (RECALCULADA)
    
    def get_adaptation_explanation(self) -> str:
        """Genera explicación de las adaptaciones realizadas"""
        if not self.adaptations_made:
            return "Menú usado sin modificaciones"
        return "Adaptaciones: " + "; ".join(self.adaptations_made)
    
    def get_similarity_change(self) -> str:
        """Muestra cómo cambió la similitud con la adaptación"""
        change = self.final_similarity - self.original_similarity
        if abs(change) < 0.01:
            return f"Similitud mantenida: {self.final_similarity:.2f}"
        elif change > 0:
            return f"Similitud mejorada: {self.original_similarity:.2f} → {self.final_similarity:.2f} (+{change:.2f})"
        else:
            return f"Similitud reducida: {self.original_similarity:.2f} → {self.final_similarity:.2f} ({change:.2f})"


class CaseAdapter:
    """
    Adaptador de casos del sistema CBR.
    
    Implementa la fase REUSE/ADAPT del ciclo CBR,
    modificando casos recuperados para ajustarse
    al nuevo contexto.
    """
    
    def __init__(self, case_base: CaseBase):
        """
        Inicializa el adaptador.
        
        Args:
            case_base: Base de casos para buscar alternativas
        """
        self.case_base = case_base
        self.similarity_calc = SimilarityCalculator()  # Para recalcular similitud post-adaptación
    
    def adapt(self, retrieval_results: List[RetrievalResult], 
              request: Request,
              num_proposals: int = 3) -> List[AdaptationResult]:
        """
        Adapta los casos recuperados al nuevo contexto.
        
        Args:
            retrieval_results: Casos recuperados
            request: Solicitud del cliente
            num_proposals: Número de propuestas a generar
            
        Returns:
            Lista de menús adaptados
        """
        adapted_menus = []
        rejected_by_negatives = 0
        
        for result in retrieval_results:
            # Intentar adaptar este caso
            adapted = self._adapt_case(result.case, request, result.similarity)
            
            if adapted:
                adapted_menus.append(adapted)
            else:
                # Caso rechazado (probablemente por similitud a negativo)
                rejected_by_negatives += 1
            
            if len(adapted_menus) >= num_proposals:
                break
        
        # Advertir si se rechazaron casos por similitud a failures
        if rejected_by_negatives > 0:
            pass  # Información capturada en stats, no imprimir
        
        # Si no hay suficientes, generar menús nuevos
        attempts = 0
        max_attempts = num_proposals * 3  # Límite de intentos
        
        while len(adapted_menus) < num_proposals and attempts < max_attempts:
            attempts += 1
            new_menu = self._generate_new_menu(request)
            
            if new_menu:
                # Verificar que el nuevo menú no sea similar a casos negativos
                neg_sim = self._check_against_negative_cases(request, new_menu.adapted_menu)
                
                if neg_sim > 0.75:
                    # Menú rechazado, información capturada en attempts
                    continue  # Intentar otro
                
                adapted_menus.append(new_menu)
            else:
                break  # No se pueden generar más
        
        # Clasificar por categoría de precio
        self._classify_by_price(adapted_menus, request)
        
        # Ordenar por similitud FINAL (después de adaptación)
        # Esto compara menús adaptados usando su similitud REAL, no la del caso original
        adapted_menus.sort(key=lambda x: x.final_similarity, reverse=True)
        
        return adapted_menus[:num_proposals]
    
    def _adapt_case(self, case: Case, request: Request, 
                    original_similarity: float = 0.0) -> Optional[AdaptationResult]:
        """
        Adapta un caso específico al nuevo contexto.
        
        Args:
            case: Caso a adaptar
            request: Nueva solicitud
            original_similarity: Similitud del caso ANTES de adaptar (de RETRIEVE)
            
        Returns:
            Resultado de la adaptación o None si no es posible
        """
        adaptations = []
        adapted_menu = deepcopy(case.menu)
        adapted_menu.id = f"adapted-{case.id}-{random.randint(1000, 9999)}"
        
        # CRÍTICO: Verificar que no estamos cerca de un caso negativo
        negative_similarity = self._check_against_negative_cases(request, adapted_menu)
        if negative_similarity > 0.75:  # Similar a un failure previo
            adaptations.append(
                f"⚠️ RECHAZADO: {negative_similarity:.0%} similar a un caso negativo"
            )
            return None  # No usar este caso
        
        # 1. Adaptar restricciones dietéticas
        diet_ok, diet_adaptations = self._adapt_for_diets(
            adapted_menu, request.required_diets
        )
        if not diet_ok:
            return None  # No se puede adaptar para las dietas
        adaptations.extend(diet_adaptations)
        
        # 2. Adaptar ingredientes restringidos
        ing_ok, ing_adaptations = self._adapt_for_ingredients(
            adapted_menu, request.restricted_ingredients
        )
        if not ing_ok:
            return None
        adaptations.extend(ing_adaptations)
        
        # 3. Adaptar precio al presupuesto
        price_ok, price_adaptations = self._adapt_for_price(
            adapted_menu, request.price_min, request.price_max
        )
        adaptations.extend(price_adaptations)
        
        # 4. Adaptar temporada (temperatura del starter)
        season_adaptations = self._adapt_for_season(adapted_menu, request.season)
        adaptations.extend(season_adaptations)
        
        # 5. Adaptar bebida
        bev_adaptations = self._adapt_beverage(
            adapted_menu, request.wants_wine, request.wine_per_dish
        )
        adaptations.extend(bev_adaptations)
        
        # 6. Adaptar culturalmente si es necesario
        cultural_adaptations = self._adapt_for_culture(
            adapted_menu, case.menu.cultural_theme, request.cultural_preference, request
        )
        adaptations.extend(cultural_adaptations)
        
        # 7. Adaptar estilo si es necesario
        style_adaptations = self._adapt_style(adapted_menu, request)
        adaptations.extend(style_adaptations)
        
        # Recalcular totales
        adapted_menu.calculate_totals()
        
        # VALIDACIÓN PREVENTIVA: Ajustar antes de enviar a REVISE
        preventive_adaptations = self._preventive_validation(adapted_menu, request)
        adaptations.extend(preventive_adaptations)
        
        # Recalcular totales tras validación preventiva
        adapted_menu.calculate_totals()
        
        # RECALCULAR similitud global del menú ADAPTADO
        # (la similitud original de RETRIEVE ya no es válida tras los cambios)
        # Crear Case temporal para calcular similitud
        temp_case = Case(
            id="temp",
            menu=adapted_menu,
            request=request,  # Usar request actual
            is_negative=False
        )
        final_similarity = self.similarity_calc.calculate_similarity(request, temp_case)
        
        # Calcular score de adaptación
        adaptation_score = self._calculate_adaptation_score(
            case.menu, adapted_menu, request
        )
        
        # Generar explicaciones
        adapted_menu.explanation = self._generate_menu_explanation(
            adapted_menu, request, adaptations
        )
        
        return AdaptationResult(
            original_case=case,
            adapted_menu=adapted_menu,
            adaptations_made=adaptations,
            adaptation_score=adaptation_score,
            price_category="",  # Se asigna después
            original_similarity=original_similarity,  # Similitud ANTES de adaptar
            final_similarity=final_similarity  # Similitud DESPUÉS de adaptar
        )
    
    def _adapt_for_diets(self, menu: Menu, 
                         required_diets: List[str]) -> Tuple[bool, List[str]]:
        """
        Adapta el menú para cumplir restricciones dietéticas.
        
        Estrategia HÍBRIDA:
        1. RETRIEVE ya filtró casos que cumplen dietas a nivel de plato
        2. Si un plato no cumple, intentamos ADAPTAR INGREDIENTES específicos
        3. Solo fallamos si no podemos adaptar
        
        Returns:
            (éxito, lista de adaptaciones)
        """
        if not required_diets:
            return True, []
        
        adaptations = []
        adapter = get_ingredient_adapter()
        
        # Verificar y adaptar cada plato
        for dish_attr in ['starter', 'main_course', 'dessert']:
            dish = getattr(menu, dish_attr)
            
            # Ver qué dietas no cumple el plato completo
            missing_diets = [d for d in required_diets if d not in dish.diets]
            
            if missing_diets:
                # Intentar ADAPTAR INGREDIENTES en vez de rechazar
                # Buscar ingredientes que violan las restricciones
                violating_ingredients = []
                for ingredient in dish.ingredients:
                    for diet in missing_diets:
                        if adapter.violates_dietary_restriction(ingredient, diet):
                            if ingredient not in violating_ingredients:
                                violating_ingredients.append(ingredient)
                
                if violating_ingredients:
                    # Intentar sustituir cada ingrediente problemático
                    import copy
                    adapted_dish = copy.deepcopy(dish)
                    new_ingredients = list(adapted_dish.ingredients)
                    substitutions_made = []
                    
                    for ing in violating_ingredients:
                        substitution = adapter.find_dietary_substitution(ing, missing_diets)
                        if substitution:
                            # Reemplazar TODAS las ocurrencias del ingrediente
                            new_ingredients = [
                                substitution.replacement if item == ing else item 
                                for item in new_ingredients
                            ]
                            substitutions_made.append(substitution)
                    
                    if substitutions_made:
                        # Actualizar ingredientes del plato COPIADO
                        adapted_dish.ingredients = new_ingredients
                        # Añadir las dietas que ahora cumple
                        if adapted_dish.diets is None:
                            adapted_dish.diets = list(missing_diets)
                        else:
                            adapted_dish.diets = list(set(adapted_dish.diets + missing_diets))
                        
                        # Reemplazar el plato en el menú con la versión adaptada
                        setattr(menu, dish_attr, adapted_dish)
                        
                        for sub in substitutions_made:
                            adaptations.append(
                                f"{dish.name}: {sub.original}→{sub.replacement} ({sub.reason})"
                            )
                    else:
                        # No se pudieron sustituir ingredientes
                        return False, adaptations + [f"ERROR: {dish.name} no cumple {', '.join(missing_diets)} y no se encontraron sustituciones"]
                else:
                    # El plato no cumple la dieta pero no hay ingredientes específicos que violen
                    # (caso edge: puede ser por método de preparación)
                    return False, adaptations + [f"ERROR: {dish.name} no cumple {', '.join(missing_diets)}"]
        
        return True, adaptations
    
    def _adapt_for_ingredients(self, menu: Menu,
                                restricted: List[str]) -> Tuple[bool, List[str]]:
        """
        Verifica que el menú no contiene ingredientes restringidos (alergias).
        
        NOTA: RETRIEVE ya filtra por alergias, así que esto es solo validación.
        Si falla aquí, es un error del sistema.
        """
        if not restricted:
            return True, []
        
        for dish_attr in ['starter', 'main_course', 'dessert']:
            dish = getattr(menu, dish_attr)
            
            # Ver si tiene ingredientes prohibidos
            forbidden = [i for i in restricted if i in dish.ingredients]
            
            if forbidden:
                # RETRIEVE debería haber filtrado esto - error del sistema
                return False, [f"ERROR: {dish.name} contiene {', '.join(forbidden)}"]
        
        # Todo OK - sin adaptaciones necesarias
        return True, []
    
    def _adapt_for_price(self, menu: Menu, 
                         min_price: float, max_price: float) -> Tuple[bool, List[str]]:
        """
        Adapta el menú al rango de precios solicitado.
        """
        adaptations = []
        current_total = menu.total_price
        
        # Si ya está en rango, no hacer nada
        if min_price <= current_total <= max_price:
            return True, adaptations
        
        # Si está por encima, buscar alternativas más económicas
        if current_total > max_price:
            excess = current_total - max_price
            adaptations.extend(
                self._reduce_price(menu, excess)
            )
        
        # Si está por debajo, buscar alternativas más premium
        elif current_total < min_price:
            deficit = min_price - current_total
            adaptations.extend(
                self._increase_price(menu, deficit)
            )
        
        menu.calculate_totals()
        return True, adaptations
    
    def _reduce_price(self, menu: Menu, amount: float) -> List[str]:
        """Reduce el precio del menú buscando alternativas más económicas"""
        adaptations = []
        
        # Ordenar platos por precio (mayor primero)
        dishes = [
            ('starter', menu.starter),
            ('main_course', menu.main_course),
            ('dessert', menu.dessert)
        ]
        dishes.sort(key=lambda x: x[1].price, reverse=True)
        
        remaining = amount
        
        for attr, dish in dishes:
            if remaining <= 0:
                break
            
            # Buscar alternativa más barata
            alternatives = self.case_base.get_dishes_by_type(dish.dish_type)
            cheaper = [d for d in alternatives if d.price < dish.price]
            
            if cheaper:
                # Elegir la más similar que sea más barata
                cheaper.sort(
                    key=lambda d: (calculate_dish_similarity(dish, d), -d.price),
                    reverse=True
                )
                new_dish = cheaper[0]
                saving = dish.price - new_dish.price
                
                setattr(menu, attr, new_dish)
                remaining -= saving
                adaptations.append(
                    f"Sustituido {dish.name} por {new_dish.name} "
                    f"(ahorro: {saving:.2f}€)"
                )
        
        # Advertir si no se pudo ajustar completamente
        if remaining > 0.5:  # Tolerancia de 0.5€
            adaptations.append(
                f"⚠️ No se pudo reducir completamente el precio (faltan {remaining:.2f}€)"
            )
        
        return adaptations
    
    def _increase_price(self, menu: Menu, amount: float) -> List[str]:
        """Aumenta el precio del menú buscando alternativas premium"""
        adaptations = []
        
        dishes = [
            ('main_course', menu.main_course),  # Priorizar el principal
            ('starter', menu.starter),
            ('dessert', menu.dessert)
        ]
        
        remaining = amount
        
        for attr, dish in dishes:
            if remaining <= 0:
                break
            
            alternatives = self.case_base.get_dishes_by_type(dish.dish_type)
            pricier = [d for d in alternatives if d.price > dish.price]
            
            if pricier:
                pricier.sort(
                    key=lambda d: (calculate_dish_similarity(dish, d), d.price),
                    reverse=True
                )
                new_dish = pricier[0]
                increase = new_dish.price - dish.price
                
                setattr(menu, attr, new_dish)
                remaining -= increase
                adaptations.append(
                    f"Mejorado {dish.name} a {new_dish.name} "
                    f"(+{increase:.2f}€ calidad premium)"
                )
        
        # Advertir si no se pudo ajustar completamente
        if remaining > 0.5:  # Tolerancia de 0.5€
            adaptations.append(
                f"⚠️ No se pudo aumentar completamente el precio (faltan {remaining:.2f}€)"
            )
        
        return adaptations
    
    def _adapt_for_season(self, menu: Menu, season: Season) -> List[str]:
        """
        Adapta el menú a la temporada (principalmente temperatura del starter).
        """
        adaptations = []
        
        if season == Season.ALL:
            return adaptations
        
        # Verificar temperatura del starter
        if not is_starter_temperature_appropriate(menu.starter.temperature, season):
            # Buscar starter con temperatura apropiada
            candidates = self.case_base.get_dishes_by_type(DishType.STARTER)
            
            appropriate = [
                d for d in candidates
                if is_starter_temperature_appropriate(d.temperature, season)
                and d.is_available_in_season(season)
            ]
            
            if appropriate:
                # Elegir el más similar
                best = max(
                    appropriate,
                    key=lambda d: calculate_dish_similarity(menu.starter, d)
                )
                
                old_name = menu.starter.name
                menu.starter = best
                adaptations.append(
                    f"Sustituido {old_name} por {best.name} "
                    f"(más apropiado para {season.value})"
                )
        
        return adaptations
    
    def _adapt_beverage(self, menu: Menu, wants_wine: bool,
                        wine_per_dish: bool) -> List[str]:
        """
        Adapta la bebida según preferencias.
        """
        adaptations = []
        
        # Verificar si la bebida actual cumple preferencia
        current_alcoholic = menu.beverage.alcoholic
        
        if wants_wine and not current_alcoholic:
            # Buscar vino apropiado
            wines = self.case_base.get_compatible_beverages(True)
            if wines:
                # Elegir vino compatible con el menú
                best_wine = self._select_best_wine(menu, wines)
                old_name = menu.beverage.name
                menu.beverage = best_wine
                adaptations.append(
                    f"Cambiado {old_name} por {best_wine.name} (maridaje de vino)"
                )
        
        elif not wants_wine and current_alcoholic:
            # Buscar bebida sin alcohol
            non_alcoholic = self.case_base.get_compatible_beverages(False)
            if non_alcoholic:
                best = random.choice(non_alcoholic)
                old_name = menu.beverage.name
                menu.beverage = best
                adaptations.append(
                    f"Cambiado {old_name} por {best.name} (sin alcohol)"
                )
        
        return adaptations
    
    def _select_best_wine(self, menu: Menu, wines: List[Beverage]) -> Beverage:
        """Selecciona el mejor vino para el menú basado en compatibilidad de sabores"""
        from ..core.knowledge import is_wine_compatible_with_flavors
        
        main_flavors = menu.main_course.flavors
        
        # Buscar vino compatible con los sabores del plato principal
        scored_wines = []
        for wine in wines:
            score = 0
            
            # Si el vino tiene subtype, usar la knowledge base para compatibilidad
            if wine.subtype:
                if is_wine_compatible_with_flavors(wine.subtype, main_flavors):
                    score += 3
            
            # Preferir vinos tintos para carnes, blancos para pescados
            if 'red-wine' in wine.type:
                if any(f in ['umami', 'fatty', 'smoky'] for f in main_flavors):
                    score += 2
            elif 'white-wine' in wine.type:
                if any(f in ['sour', 'fresh', 'light'] for f in main_flavors):
                    score += 2
            
            scored_wines.append((wine, score))
        
        scored_wines.sort(key=lambda x: x[1], reverse=True)
        return scored_wines[0][0] if scored_wines else wines[0]
    
    def _adapt_style(self, menu: Menu, request: Request) -> List[str]:
        """
        Adapta el estilo culinario si es necesario.
        """
        adaptations = []
        
        if request.preferred_style is None:
            return adaptations
        
        # Verificar si el menú ya tiene el estilo preferido
        if menu.dominant_style == request.preferred_style:
            return adaptations
        
        preferred_styles = get_preferred_styles_for_event(request.event_type)
        
        # Si el estilo actual no es apropiado, intentar adaptar
        if menu.dominant_style not in preferred_styles:
            # Buscar platos con el estilo preferido
            for dish_attr in ['main_course', 'starter', 'dessert']:
                dish = getattr(menu, dish_attr)
                
                if request.preferred_style not in dish.styles:
                    alternatives = self.case_base.get_dishes_by_type(dish.dish_type)
                    styled = [
                        d for d in alternatives
                        if request.preferred_style in d.styles
                    ]
                    
                    if styled:
                        best = max(
                            styled,
                            key=lambda d: calculate_dish_similarity(dish, d)
                        )
                        setattr(menu, dish_attr, best)
                        menu.dominant_style = request.preferred_style
                        adaptations.append(
                            f"Adaptado estilo a {request.preferred_style.value}"
                        )
                        break
        
        return adaptations
    
    def _calculate_adaptation_score(self, original: Menu, adapted: Menu,
                                    request: Request) -> float:
        """
        Calcula qué tan exitosa fue la adaptación.
        
        Score más alto = mejor adaptación.
        """
        score = 1.0
        
        # Penalizar si el precio está fuera del rango
        if adapted.total_price < request.price_min:
            score -= 0.2
        elif adapted.total_price > request.price_max:
            score -= 0.3
        
        # Penalizar muchos cambios
        changes = 0
        if adapted.starter.id != original.starter.id:
            changes += 1
        if adapted.main_course.id != original.main_course.id:
            changes += 1
        if adapted.dessert.id != original.dessert.id:
            changes += 1
        if adapted.beverage.id != original.beverage.id:
            changes += 0.5
        
        score -= changes * 0.1
        
        # Bonus por cumplir restricciones dietéticas
        menu_diets = adapted.get_all_diets()
        if all(d in menu_diets for d in request.required_diets):
            score += 0.1
        
        return max(0, min(1, score))
    
    def _generate_new_menu(self, request: Request) -> Optional[AdaptationResult]:
        """
        Genera un menú completamente nuevo cuando no hay casos adaptables.
        """
        # Obtener platos disponibles
        starters = self.case_base.get_dishes_by_type(DishType.STARTER)
        mains = self.case_base.get_dishes_by_type(DishType.MAIN_COURSE)
        desserts = self.case_base.get_dishes_by_type(DishType.DESSERT)
        beverages = self.case_base.get_compatible_beverages(request.wants_wine)
        
        if not all([starters, mains, desserts, beverages]):
            return None
        
        # Filtrar por restricciones dietéticas
        if request.required_diets:
            starters = [d for d in starters if all(diet in d.diets for diet in request.required_diets)]
            mains = [d for d in mains if all(diet in d.diets for diet in request.required_diets)]
            desserts = [d for d in desserts if all(diet in d.diets for diet in request.required_diets)]
        
        # Filtrar por ingredientes restringidos
        if request.restricted_ingredients:
            starters = [d for d in starters if not any(i in d.ingredients for i in request.restricted_ingredients)]
            mains = [d for d in mains if not any(i in d.ingredients for i in request.restricted_ingredients)]
            desserts = [d for d in desserts if not any(i in d.ingredients for i in request.restricted_ingredients)]
        
        # Filtrar por temporada
        if request.season != Season.ALL:
            starters = [d for d in starters if d.is_available_in_season(request.season)]
            mains = [d for d in mains if d.is_available_in_season(request.season)]
            desserts = [d for d in desserts if d.is_available_in_season(request.season)]
        
        if not all([starters, mains, desserts]):
            return None
        
        # Seleccionar platos que encajen en el presupuesto
        target_price = (request.price_min + request.price_max) / 2
        
        # Intentar encontrar combinación válida
        for _ in range(50):  # Máximo intentos
            starter = random.choice(starters)
            main = random.choice(mains)
            dessert = random.choice(desserts)
            beverage = random.choice(beverages)
            
            total = starter.price + main.price + dessert.price + beverage.price
            
            # Verificar precio
            if not (request.price_min <= total <= request.price_max):
                continue
            
            # Verificar compatibilidad de categorías
            if not are_categories_compatible(starter.category, main.category):
                continue
            
            # Verificar compatibilidad de sabores
            starter_flavors = set(starter.flavors)
            main_flavors = set(main.flavors)
            
            flavor_compatible = False
            for sf in starter_flavors:
                for mf in main_flavors:
                    if are_flavors_compatible(sf, mf):
                        flavor_compatible = True
                        break
                if flavor_compatible:
                    break
            
            if not flavor_compatible and starter_flavors and main_flavors:
                continue
            
            # Verificar postre tras plato graso
            main_has_fatty = Flavor.FATTY in main.flavors
            if not is_dessert_appropriate_after_fatty(
                main_has_fatty, dessert.category, dessert.flavors
            ):
                continue
            
            # Crear menú
            menu = Menu(
                id=f"generated-{random.randint(10000, 99999)}",
                starter=starter,
                main_course=main,
                dessert=dessert,
                beverage=beverage,
                explanation=["Menú generado especialmente para su evento"]
            )
            
            # Determinar estilo dominante
            all_styles = set(starter.styles) | set(main.styles) | set(dessert.styles)
            preferred = get_preferred_styles_for_event(request.event_type)
            for style in preferred:
                if style in all_styles:
                    menu.dominant_style = style
                    break
            
            # RECALCULAR similitud del menú generado
            temp_case = Case(
                id="temp-generated",
                menu=menu,
                request=request,
                is_negative=False
            )
            final_similarity = self.similarity_calc.calculate_similarity(request, temp_case)
            
            return AdaptationResult(
                original_case=None,
                adapted_menu=menu,
                adaptations_made=["Menú generado desde cero"],
                adaptation_score=0.7,  # Score base para menús generados
                price_category="",
                original_similarity=0.0,  # No hay caso original
                final_similarity=final_similarity  # Similitud del menú generado
            )
        
        return None
    
    def _check_against_negative_cases(self, request: Request, proposed_menu: Menu) -> float:
        """
        Verifica si el menú propuesto es similar a casos negativos (failures).
        
        Args:
            request: Solicitud del cliente
            proposed_menu: Menú que estamos considerando proponer
            
        Returns:
            Similitud máxima con casos negativos (0-1)
        """
        from ..core.similarity import SimilarityCalculator, calculate_menu_similarity
        
        # Obtener todos los casos negativos
        all_cases = self.case_base.get_all_cases()
        negative_cases = [c for c in all_cases if c.is_negative]
        
        if not negative_cases:
            return 0.0  # No hay casos negativos, safe
        
        max_similarity = 0.0
        similarity_calc = SimilarityCalculator()
        
        for neg_case in negative_cases:
            # Similitud del request
            req_sim = similarity_calc.calculate_similarity(request, neg_case)
            
            # Similitud del menú propuesto con el menú del caso negativo
            menu_sim = calculate_menu_similarity(proposed_menu, neg_case.menu)
            
            # Similitud combinada (más peso al menú)
            combined_sim = 0.4 * req_sim + 0.6 * menu_sim
            
            max_similarity = max(max_similarity, combined_sim)
        
        return max_similarity
    
    def _classify_by_price(self, results: List[AdaptationResult],
                           request: Request):
        """
        Clasifica los resultados por categoría de precio.
        """
        price_range = request.price_max - request.price_min
        
        for result in results:
            price = result.adapted_menu.total_price
            
            if price_range > 0:
                position = (price - request.price_min) / price_range
                
                if position < 0.33:
                    result.price_category = "economico"
                elif position < 0.67:
                    result.price_category = "medio"
                else:
                    result.price_category = "premium"
            else:
                result.price_category = "medio"
    
    def _generate_menu_explanation(self, menu: Menu, request: Request,
                                    adaptations: List[str]) -> List[str]:
        """
        Genera explicaciones detalladas para el menú.
        """
        explanations = []
        
        # Explicación del starter
        if is_starter_temperature_appropriate(menu.starter.temperature, request.season):
            temp_text = {
                Temperature.HOT: "caliente",
                Temperature.WARM: "templado",
                Temperature.COLD: "frío"
            }.get(menu.starter.temperature, "")
            
            season_text = {
                Season.SUMMER: "verano",
                Season.WINTER: "invierno",
                Season.SPRING: "primavera",
                Season.AUTUMN: "otoño"
            }.get(request.season, "")
            
            if temp_text and season_text:
                explanations.append(
                    f"Entrante {temp_text} ideal para {season_text}"
                )
        
        # Explicación de sabores
        starter_flavors = menu.starter.flavors
        main_flavors = menu.main_course.flavors
        
        for sf in starter_flavors:
            for mf in main_flavors:
                if are_flavors_compatible(sf, mf):
                    explanations.append(
                        f"Armonía de sabores: {sf.value} del entrante "
                        f"complementa {mf.value} del principal"
                    )
                    break
        
        # Explicación del postre
        if Flavor.FATTY in main_flavors:
            if menu.dessert.category == DishCategory.FRUIT:
                explanations.append(
                    "Postre de frutas refresca el paladar tras plato contundente"
                )
            elif Flavor.SOUR in menu.dessert.flavors:
                explanations.append(
                    "Postre con notas ácidas limpia el paladar"
                )
        
        # Explicación de calorías
        if is_calorie_count_appropriate(menu.total_calories, request.season):
            if request.season == Season.SUMMER and menu.total_calories < 800:
                explanations.append(
                    f"Menú ligero ({menu.total_calories} kcal) para verano"
                )
            elif request.season == Season.WINTER and menu.total_calories > 1000:
                explanations.append(
                    f"Menú contundente ({menu.total_calories} kcal) para invierno"
                )
        
        # Explicación de vino
        if menu.beverage.alcoholic:
            if 'red-wine' in menu.beverage.type:
                explanations.append("Vino tinto ideal para carnes y sabores intensos")
            elif 'white-wine' in menu.beverage.type:
                explanations.append("Vino blanco perfecto para pescados y platos ligeros")
        
        return explanations
    
    def _find_cultural_dish_replacement(self, original_dish: Dish, 
                                       target_culture: CulturalTradition,
                                       current_menu: Menu,
                                       request: Request) -> Optional[Dish]:
        """
        Busca un plato de reemplazo usando similitud global del sistema.
        
        REFACTORIZADO: Usa calculate_similarity() con 9 dimensiones en vez de
        scoring manual de 3 factores. Esto asegura consistencia con RETRIEVE.
        
        Args:
            original_dish: Plato a reemplazar
            target_culture: Cultura objetivo
            current_menu: Menú actual (para crear caso temporal)
            request: Solicitud del cliente
            
        Returns:
            Plato de reemplazo con mejor similitud global o None
        """
        # Buscar plato de reemplazo
        target_culture_name = target_culture if isinstance(target_culture, str) else target_culture.value
        
        # Obtener todos los platos del mismo tipo
        candidates = self.case_base.get_dishes_by_type(original_dish.dish_type)
        
        if not candidates:
            return None
        
        # FILTRO 1: Platos que ya están en el menú (evitar duplicados)
        current_dish_ids = {
            current_menu.starter.id,
            current_menu.main_course.id,
            current_menu.dessert.id
        }
        candidates = [d for d in candidates if d.id not in current_dish_ids]
        
        # FILTRO 2: Restricciones dietéticas obligatorias (CRÍTICO)
        if request.required_diets:
            candidates = [d for d in candidates 
                         if all(diet in d.diets for diet in request.required_diets)]
        
        # FILTRO 3: Ingredientes prohibidos (CRÍTICO - alergias)
        if request.restricted_ingredients:
            candidates = [d for d in candidates
                         if not any(ing in d.ingredients for ing in request.restricted_ingredients)]
        
        # FILTRO 4: Incompatibilidad de categorías con otros platos del menú
        # Evitar que dos platos del menú tengan categorías incompatibles
        other_dishes = []
        for dish_attr in ['starter', 'main_course', 'dessert']:
            other_dish = getattr(current_menu, dish_attr)
            if other_dish.id != original_dish.id:  # Excluir el plato que estamos reemplazando
                other_dishes.append(other_dish)
        
        if other_dishes:
            candidates_compatible = []
            for candidate in candidates:
                # Verificar compatibilidad con todos los otros platos
                is_compatible = True
                for other in other_dishes:
                    if not are_categories_compatible(candidate.category, other.category):
                        is_compatible = False
                        break
                
                if is_compatible:
                    candidates_compatible.append(candidate)
            
            if candidates_compatible:
                candidates = candidates_compatible
        
        if not candidates:
            return None
        
        # SCORING: Usar calculate_dish_similarity mejorado que ya incluye cultura
        # 
        # calculate_dish_similarity() ahora considera 8 dimensiones con pesos calibrados:
        # - Categoría (15%)
        # - Precio (15%)
        # - Complejidad (10%)
        # - Sabores (15%)
        # - Estilos (15%)
        # - Temperatura (5%)
        # - Dietas (10%)
        # - Cultura de ingredientes (15%) - evaluada con get_cultural_score
        #
        # Esto elimina la ponderación manual arbitraria y usa un sistema coherente.
        
        scored_candidates = []
        
        for dish in candidates:
            # Calcular similitud completa incluyendo evaluación cultural
            similarity = calculate_dish_similarity(
                original_dish, 
                dish,
                target_culture=target_culture,
                similarity_calc=self.similarity_calc
            )
            
            scored_candidates.append((dish, similarity))
        
        # Ordenar por score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar el mejor
        best_dish = scored_candidates[0][0]
        best_score = scored_candidates[0][1]
        
        return best_dish
    
    def _adapt_for_culture(self, menu: Menu, 
                          original_culture: Optional[CulturalTradition],
                          target_culture: Optional[CulturalTradition],
                          request: Request) -> List[str]:
        """
        Adapta el menú a una cultura gastronómica diferente.
        
        REFACTORIZADO: Compara similitud global entre dos opciones:
        1. Adaptar ingredientes del plato actual
        2. Reemplazar con plato diferente
        
        Elige la opción con mejor similitud global (sin threshold arbitrario).
        
        Args:
            menu: Menú a adaptar (se modifica in-place)
            original_culture: Cultura del caso original
            target_culture: Cultura solicitada por el cliente
            request: Solicitud del cliente
            
        Returns:
            Lista de adaptaciones realizadas
        """
        adaptations = []
        
        # Si no hay preferencia cultural o ya coinciden, no adaptar
        if not target_culture:
            return adaptations
        
        if original_culture == target_culture:
            return adaptations
        
        # Obtener el adaptador de ingredientes
        adapter = get_ingredient_adapter()
        
        # Adaptar cada plato del menú
        for dish_attr in ['starter', 'main_course', 'dessert']:
            dish = getattr(menu, dish_attr)
            
            if not dish.ingredients:
                continue  # Sin ingredientes listados, no podemos adaptar
            
            # OPCIÓN 1: Adaptar ingredientes del plato actual
            adapted_dish = deepcopy(dish)
            current_ingredients = adapted_dish.ingredients.copy()
            current_score = self.similarity_calc.get_cultural_score(current_ingredients, target_culture)
            dish_substitutions = []
            
            for ingredient in adapted_dish.ingredients:
                substitution = adapter.find_substitution(ingredient, target_culture)
                
                if substitution:
                    temp_ingredients = [
                        substitution.replacement if ing == ingredient else ing
                        for ing in current_ingredients
                    ]
                    
                    new_score = self.similarity_calc.get_cultural_score(temp_ingredients, target_culture)
                    
                    if new_score > current_score:
                        improvement = new_score - current_score
                        current_ingredients = temp_ingredients
                        
                        substitution_with_improvement = IngredientSubstitution(
                            original=substitution.original,
                            replacement=substitution.replacement,
                            reason=substitution.reason,
                            confidence=substitution.confidence
                        )
                        dish_substitutions.append({
                            'substitution': substitution_with_improvement,
                            'score_before': current_score,
                            'score_after': new_score,
                            'improvement': improvement
                        })
                        
                        current_score = new_score
            
            adapted_dish.ingredients = current_ingredients
            final_adapted_score = current_score
            
            # OPCIÓN 2: Buscar plato de reemplazo
            replacement_dish = self._find_cultural_dish_replacement(
                dish, target_culture, menu, request
            )
            
            # Comparar similitud global de ambas opciones
            # Crear casos temporales para cada opción
            temp_menu_adapted = deepcopy(menu)
            setattr(temp_menu_adapted, dish_attr, adapted_dish)
            temp_menu_adapted.cultural_theme = target_culture
            temp_menu_adapted.calculate_totals()
            
            temp_case_adapted = Case(
                id=f"temp-adapted-{dish.id}",
                request=deepcopy(request),
                menu=temp_menu_adapted,
                success=True,
                feedback_score=4.0
            )
            
            similarity_adapted = self.similarity_calc.calculate_similarity(request, temp_case_adapted)
            
            if replacement_dish:
                temp_menu_replaced = deepcopy(menu)
                setattr(temp_menu_replaced, dish_attr, replacement_dish)
                temp_menu_replaced.cultural_theme = target_culture
                temp_menu_replaced.calculate_totals()
                
                temp_case_replaced = Case(
                    id=f"temp-replaced-{replacement_dish.id}",
                    request=deepcopy(request),
                    menu=temp_menu_replaced,
                    success=True,
                    feedback_score=4.0
                )
                
                similarity_replaced = self.similarity_calc.calculate_similarity(request, temp_case_replaced)
                
                # DECISIÓN: Elegir la opción con MEJOR similitud global
                if similarity_replaced > similarity_adapted:
                    # Reemplazo es mejor
                    setattr(menu, dish_attr, replacement_dish)
                    adaptations.append(
                        f"Plato reemplazado: {dish.name} → {replacement_dish.name} "
                        f"(similitud: {similarity_adapted:.1%} → {similarity_replaced:.1%})"
                    )
                    
                    menu.cultural_adaptations.append({
                        "dish_id": replacement_dish.id,
                        "dish_name": replacement_dish.name,
                        "original_dish": dish.name,
                        "target_culture": target_culture if isinstance(target_culture, str) else target_culture.value,
                        "adaptation_type": "dish_replacement",
                        "reason": f"Replacement has better global similarity",
                        "similarity_adapted": f"{similarity_adapted:.2f}",
                        "similarity_replaced": f"{similarity_replaced:.2f}"
                    })
                elif dish_substitutions:
                    # Adaptación de ingredientes es mejor (o igual)
                    setattr(menu, dish_attr, adapted_dish)
                    
                    subs_desc = []
                    for item in dish_substitutions:
                        sub = item['substitution']
                        improvement_pct = item['improvement'] * 100
                        subs_desc.append(
                            f"{sub.original}→{sub.replacement} (+{improvement_pct:.0f}%)"
                        )
                    
                    original_cultural_score = self.similarity_calc.get_cultural_score(dish.ingredients, target_culture)
                    final_improvement = final_adapted_score - original_cultural_score
                    adaptations.append(
                        f"{dish.name}: {', '.join(subs_desc)} "
                        f"(cultural: {original_cultural_score:.0%}→{final_adapted_score:.0%}, global: {similarity_adapted:.1%})"
                    )
                    
                    for item in dish_substitutions:
                        sub = item['substitution']
                        menu.cultural_adaptations.append({
                            "dish_id": dish.id,
                            "dish_name": dish.name,
                            "original_ingredient": sub.original,
                            "adapted_ingredient": sub.replacement,
                            "reason": sub.reason,
                            "confidence": sub.confidence,
                            "target_culture": target_culture if isinstance(target_culture, str) else target_culture.value,
                            "score_before": f"{item['score_before']:.2f}",
                            "score_after": f"{item['score_after']:.2f}",
                            "improvement": f"+{item['improvement']*100:.0f}%"
                        })
            elif dish_substitutions:
                # Solo hay adaptación de ingredientes (no hay reemplazo disponible)
                setattr(menu, dish_attr, adapted_dish)
                
                subs_desc = []
                for item in dish_substitutions:
                    sub = item['substitution']
                    improvement_pct = item['improvement'] * 100
                    subs_desc.append(
                        f"{sub.original}→{sub.replacement} (+{improvement_pct:.0f}%)"
                    )
                
                original_cultural_score = self.similarity_calc.get_cultural_score(dish.ingredients, target_culture)
                final_improvement = final_adapted_score - original_cultural_score
                adaptations.append(
                    f"{dish.name}: {', '.join(subs_desc)} "
                    f"(similitud {original_cultural_score:.0%}→{final_adapted_score:.0%}, +{final_improvement*100:.0f}%)"
                )
                
                for item in dish_substitutions:
                    sub = item['substitution']
                    menu.cultural_adaptations.append({
                        "dish_id": dish.id,
                        "dish_name": dish.name,
                        "original_ingredient": sub.original,
                        "adapted_ingredient": sub.replacement,
                        "reason": sub.reason,
                        "confidence": sub.confidence,
                        "target_culture": target_culture if isinstance(target_culture, str) else target_culture.value,
                        "score_before": f"{item['score_before']:.2f}",
                        "score_after": f"{item['score_after']:.2f}",
                        "improvement": f"+{item['improvement']*100:.0f}%"
                    })
        
        # Actualizar el tema cultural del menú
        if adaptations:
            menu.cultural_theme = target_culture
            original_name = original_culture if isinstance(original_culture, str) else (original_culture.value if original_culture else 'neutral')
            target_name = target_culture if isinstance(target_culture, str) else target_culture.value
            adaptations.insert(0, 
                f"Menú adaptado culturalmente: {original_name} → {target_name}"
            )
        
        return adaptations
    
    def _preventive_validation(self, menu: Menu, request: Request) -> List[str]:
        """
        Validación preventiva para evitar rechazos en REVISE.
        
        Ajusta el menú antes de enviarlo a la fase REVISE para maximizar
        probabilidad de aceptación.
        
        Validaciones:
        1. Precio excede máximo → reducir proporcionalmente
        2. Dietas no cumplidas → último intento de sustitución
        3. Ingredientes prohibidos → verificar y eliminar
        
        Returns:
            Lista de adaptaciones preventivas realizadas
        """
        adaptations = []
        
        # 1. VALIDACIÓN PREVENTIVA DE PRECIO
        if menu.total_price > request.price_max:
            excess = menu.total_price - request.price_max
            
            # Reducir precios proporcionalmente
            if excess > 0.5:  # Solo si excede más de 0.5€
                reduction_ratio = request.price_max / menu.total_price
                
                # Aplicar reducción proporcional a cada plato
                menu.starter.price *= reduction_ratio
                menu.main_course.price *= reduction_ratio
                menu.dessert.price *= reduction_ratio
                menu.beverage.price *= reduction_ratio
                
                adaptations.append(
                    f"⚙️ Precios ajustados preventivamente (-{excess:.2f}€ para cumplir presupuesto)"
                )
        
        # 2. VALIDACIÓN PREVENTIVA DE DIETAS
        if request.required_diets:
            menu_diets = menu.get_all_diets()
            missing_diets = [d for d in request.required_diets if d not in menu_diets]
            
            if missing_diets:
                # Último intento: marcar advertencia
                adaptations.append(
                    f"⚠️ Advertencia: Pueden faltar dietas {', '.join(missing_diets)}"
                )
        
        # 3. VALIDACIÓN PREVENTIVA DE INGREDIENTES PROHIBIDOS
        if request.restricted_ingredients:
            menu_ingredients = menu.get_all_ingredients()
            found_restricted = [
                ing for ing in request.restricted_ingredients 
                if ing in menu_ingredients
            ]
            
            if found_restricted:
                adaptations.append(
                    f"⚠️ CRÍTICO: Ingredientes prohibidos detectados: {', '.join(found_restricted)}"
                )
        
        # 4. VALIDACIÓN PREVENTIVA DE TEMPERATURA-TEMPORADA
        if request.season != Season.ALL:
            from ..core.knowledge import is_starter_temperature_appropriate
            if not is_starter_temperature_appropriate(menu.starter.temperature, request.season):
                adaptations.append(
                    f"ℹ️ Temperatura del entrante ({menu.starter.temperature.value}) "
                    f"puede no ser ideal para {request.season.value}"
                )
        
        return adaptations
