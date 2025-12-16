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
    CulinaryStyle, Flavor, Temperature, Complexity
)
from ..core.case_base import CaseBase
from .retrieve import RetrievalResult
from ..core.similarity import calculate_dish_similarity
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
    
    def get_adaptation_explanation(self) -> str:
        """Genera explicación de las adaptaciones realizadas"""
        if not self.adaptations_made:
            return "Menú usado sin modificaciones"
        return "Adaptaciones: " + "; ".join(self.adaptations_made)


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
        
        for result in retrieval_results:
            # Intentar adaptar este caso
            adapted = self._adapt_case(result.case, request)
            
            if adapted:
                adapted_menus.append(adapted)
            
            if len(adapted_menus) >= num_proposals:
                break
        
        # Si no hay suficientes, generar menús nuevos
        while len(adapted_menus) < num_proposals:
            new_menu = self._generate_new_menu(request)
            if new_menu:
                adapted_menus.append(new_menu)
            else:
                break  # No se pueden generar más
        
        # Clasificar por categoría de precio
        self._classify_by_price(adapted_menus, request)
        
        # Ordenar por puntuación de adaptación
        adapted_menus.sort(key=lambda x: x.adaptation_score, reverse=True)
        
        return adapted_menus[:num_proposals]
    
    def _adapt_case(self, case: Case, request: Request) -> Optional[AdaptationResult]:
        """
        Adapta un caso específico al nuevo contexto.
        
        Args:
            case: Caso a adaptar
            request: Nueva solicitud
            
        Returns:
            Resultado de la adaptación o None si no es posible
        """
        adaptations = []
        adapted_menu = deepcopy(case.menu)
        adapted_menu.id = f"adapted-{case.id}-{random.randint(1000, 9999)}"
        
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
        
        # 6. Adaptar estilo si es necesario
        style_adaptations = self._adapt_style(adapted_menu, request)
        adaptations.extend(style_adaptations)
        
        # Recalcular totales
        adapted_menu.calculate_totals()
        
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
            price_category=""  # Se asigna después
        )
    
    def _adapt_for_diets(self, menu: Menu, 
                         required_diets: List[str]) -> Tuple[bool, List[str]]:
        """
        Adapta el menú para cumplir restricciones dietéticas.
        
        Returns:
            (éxito, lista de adaptaciones)
        """
        if not required_diets:
            return True, []
        
        adaptations = []
        
        # Verificar cada plato
        for dish_attr in ['starter', 'main_course', 'dessert']:
            dish = getattr(menu, dish_attr)
            
            # Ver qué dietas no cumple
            missing_diets = [d for d in required_diets if d not in dish.diets]
            
            if missing_diets:
                # Buscar alternativa
                alternative = self._find_diet_alternative(
                    dish, missing_diets, required_diets
                )
                
                if alternative:
                    setattr(menu, dish_attr, alternative)
                    adaptations.append(
                        f"Sustituido {dish.name} por {alternative.name} "
                        f"(cumple {', '.join(missing_diets)})"
                    )
                else:
                    # No se encuentra alternativa
                    return False, adaptations
        
        return True, adaptations
    
    def _find_diet_alternative(self, original: Dish, 
                                missing_diets: List[str],
                                all_required: List[str]) -> Optional[Dish]:
        """
        Busca un plato alternativo que cumpla las dietas requeridas.
        """
        candidates = self.case_base.get_dishes_by_type(original.dish_type)
        
        # Filtrar por dietas
        valid_candidates = [
            d for d in candidates
            if all(diet in d.diets for diet in all_required)
        ]
        
        if not valid_candidates:
            return None
        
        # Buscar el más similar al original
        best_match = max(
            valid_candidates,
            key=lambda d: calculate_dish_similarity(original, d)
        )
        
        return best_match
    
    def _adapt_for_ingredients(self, menu: Menu,
                                restricted: List[str]) -> Tuple[bool, List[str]]:
        """
        Adapta el menú para evitar ingredientes restringidos.
        """
        if not restricted:
            return True, []
        
        adaptations = []
        
        for dish_attr in ['starter', 'main_course', 'dessert']:
            dish = getattr(menu, dish_attr)
            
            # Ver si tiene ingredientes prohibidos
            forbidden = [i for i in restricted if i in dish.ingredients]
            
            if forbidden:
                # Buscar alternativa sin esos ingredientes
                alternative = self._find_ingredient_alternative(
                    dish, restricted
                )
                
                if alternative:
                    setattr(menu, dish_attr, alternative)
                    adaptations.append(
                        f"Sustituido {dish.name} por {alternative.name} "
                        f"(evita {', '.join(forbidden)})"
                    )
                else:
                    return False, adaptations
        
        return True, adaptations
    
    def _find_ingredient_alternative(self, original: Dish,
                                      restricted: List[str]) -> Optional[Dish]:
        """
        Busca alternativa sin ingredientes restringidos.
        """
        candidates = self.case_base.get_dishes_by_type(original.dish_type)
        
        # Filtrar por ingredientes
        valid_candidates = [
            d for d in candidates
            if not any(ing in d.ingredients for ing in restricted)
        ]
        
        if not valid_candidates:
            return None
        
        best_match = max(
            valid_candidates,
            key=lambda d: calculate_dish_similarity(original, d)
        )
        
        return best_match
    
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
        """Selecciona el mejor vino para el menú basado en sabores"""
        main_flavors = menu.main_course.flavors
        
        # Buscar vino con sabores compatibles
        scored_wines = []
        for wine in wines:
            score = 0
            for flavor in wine.compatible_flavors:
                if flavor in main_flavors:
                    score += 2
                # También dar puntos por compatibilidad general
                for menu_flavor in main_flavors:
                    if are_flavors_compatible(flavor, menu_flavor):
                        score += 1
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
            
            return AdaptationResult(
                original_case=None,
                adapted_menu=menu,
                adaptations_made=["Menú generado desde cero"],
                adaptation_score=0.7,  # Score base para menús generados
                price_category=""
            )
        
        return None
    
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
            if 'red-wine' in menu.beverage.styles:
                explanations.append("Vino tinto ideal para carnes y sabores intensos")
            elif 'white-wine' in menu.beverage.styles:
                explanations.append("Vino blanco perfecto para pescados y platos ligeros")
        
        # Adaptaciones realizadas
        if adaptations:
            explanations.append(f"Adaptaciones: {', '.join(adaptations)}")
        
        return explanations
