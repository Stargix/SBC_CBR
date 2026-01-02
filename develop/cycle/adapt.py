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

from core.models import (
    Case, Menu, Dish, Beverage, Request,
    EventType, Season, DishType, DishCategory,
    CulturalTradition, CulinaryStyle, Flavor, Temperature, Complexity
)
from core.case_base import CaseBase
from cycle.retrieve import RetrievalResult
from cycle.ingredient_adapter import get_ingredient_adapter, IngredientSubstitution
from core.similarity import calculate_dish_similarity, SimilarityCalculator
from core.knowledge import (
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
            print(f"⚠️  {rejected_by_negatives} caso(s) rechazado(s) por similitud a failures previos")
        
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
                    print(f"⚠️  Menú generado rechazado: {neg_sim:.0%} similar a failure")
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
        from core.knowledge import is_wine_compatible_with_flavors
        
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
        from core.similarity import SimilarityCalculator, calculate_menu_similarity
        
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
        Busca un plato de reemplazo culturalmente apropiado.
        
        Cuando un plato es demasiado diferente culturalmente, en lugar de
        adaptar ingredientes (que puede resultar absurdo), busca un plato
        completamente diferente del mismo tipo que sea apropiado.
        
        IMPORTANTE: Filtra por TODAS las restricciones (temporada, sabores, 
        compatibilidades), no solo cultura.
        
        Args:
            original_dish: Plato a reemplazar
            target_culture: Cultura objetivo
            current_menu: Menú actual (para evitar duplicados)
            request: Solicitud del cliente (para validar restricciones)
            
        Returns:
            Plato de reemplazo o None
        """
        print(f"\n   🔍 BÚSQUEDA DE REEMPLAZO para {original_dish.name}")
        target_culture_name = target_culture if isinstance(target_culture, str) else target_culture.value
        print(f"      Cultura objetivo: {target_culture_name}")
        print(f"      Tipo de plato: {original_dish.dish_type.value}")
        
        # Obtener todos los platos del mismo tipo
        candidates = self.case_base.get_dishes_by_type(original_dish.dish_type)
        
        print(f"      Candidatos totales: {len(candidates)}")
        
        if not candidates:
            print(f"      ❌ Sin candidatos")
            return None
        
        # FILTRO 1: Platos que ya están en el menú (evitar duplicados)
        current_dish_ids = {
            current_menu.starter.id,
            current_menu.main_course.id,
            current_menu.dessert.id
        }
        candidates = [d for d in candidates if d.id not in current_dish_ids]
        
        # FILTRO 2: Temporada apropiada (opcional - si elimina muchos, relajar)
        if request.season != Season.ALL:
            season_filtered = [d for d in candidates 
                              if request.season in d.seasons or Season.ALL in d.seasons]
            # Solo aplicar filtro si no elimina TODOS los candidatos
            if len(season_filtered) >= 5:
                candidates = season_filtered
        
        # FILTRO 3: Restricciones dietéticas obligatorias (CRÍTICO)
        if request.required_diets:
            candidates = [d for d in candidates 
                         if all(diet in d.diets for diet in request.required_diets)]
        
        # FILTRO 4: Ingredientes prohibidos (CRÍTICO - alergias)
        if request.restricted_ingredients:
            candidates = [d for d in candidates
                         if not any(ing in d.ingredients for ing in request.restricted_ingredients)]
        
        print(f"      Candidatos tras filtros básicos: {len(candidates)}")
        
        # Obtener adaptador de ingredientes para scoring cultural
        adapter = get_ingredient_adapter()
        
        # Scoring multi-criterio: cultura + compatibilidades gastronómicas
        scored_candidates = []
        for dish in candidates:
            if not dish.ingredients:
                continue  # Necesitamos ingredientes para evaluar
            
            # SCORE 1: Cultural (0-1)
            cultural_score = adapter.get_cultural_score(dish.ingredients, target_culture)
            
            # SCORE 2: Compatibilidad de sabores con otros platos del menú (0-1)
            from core.knowledge import are_flavors_compatible
            flavor_score = 0.0
            flavor_checks = 0
            
            # Compatibilidad con starter
            if original_dish.dish_type != DishType.STARTER:
                for df in dish.flavors:
                    for sf in current_menu.starter.flavors:
                        if are_flavors_compatible(df, sf):
                            flavor_score += 1
                        flavor_checks += 1
            
            # Compatibilidad con main
            if original_dish.dish_type != DishType.MAIN_COURSE:
                for df in dish.flavors:
                    for mf in current_menu.main_course.flavors:
                        if are_flavors_compatible(df, mf):
                            flavor_score += 1
                        flavor_checks += 1
            
            if flavor_checks > 0:
                flavor_score = flavor_score / flavor_checks
            else:
                flavor_score = 0.5  # Neutral si no hay sabores
            
            # SCORE 3: Temperatura apropiada para temporada (0-1)
            from core.knowledge import is_starter_temperature_appropriate
            if original_dish.dish_type == DishType.STARTER:
                temp_score = 1.0 if is_starter_temperature_appropriate(
                    dish.temperature, request.season
                ) else 0.3
            else:
                temp_score = 1.0  # Main/dessert no tienen restricción de temperatura
            
            # SCORE 4: Score cultural ajustado con ponderación de ingredientes
            # Normalizar culture para comparación
            if isinstance(target_culture, str):
                culture_name = target_culture.capitalize()
            else:
                culture_name = target_culture.value.capitalize()
            
            specific_count = 0
            universal_count = 0
            
            for ing in dish.ingredients:
                cultures = adapter.ingredient_to_cultures.get(ing, [])
                if culture_name in cultures:
                    specific_count += 1
                elif 'Universal' in cultures:
                    universal_count += 1
            
            total_ingredients = len(dish.ingredients)
            if total_ingredients > 0:
                weighted_score = (specific_count * 1.0 + universal_count * 0.5) / total_ingredients
                
                # Penalización por robustez
                if specific_count == 0:
                    robustness_penalty = 0.5
                elif specific_count == 1:
                    robustness_penalty = 0.85
                else:
                    robustness_penalty = 1.0
                
                adjusted_cultural_score = weighted_score * robustness_penalty
            else:
                adjusted_cultural_score = 0.0
            
            # SCORE FINAL: Combinar todos los criterios
            # Cultura: 60%, Sabores: 25%, Temperatura: 15%
            final_score = (
                adjusted_cultural_score * 0.60 +
                flavor_score * 0.25 +
                temp_score * 0.15
            )
            
            scored_candidates.append((
                dish, 
                cultural_score,  # Score crudo cultural
                adjusted_cultural_score,  # Score cultural ajustado
                final_score,  # Score final multi-criterio
                specific_count,
                flavor_score,
                temp_score
            ))
        
        print(f"      Candidatos evaluados: {len(scored_candidates)}")
        
        if not scored_candidates:
            print(f"      ❌ Sin candidatos válidos")
            return None
        
        # Ordenar por score FINAL (multi-criterio)
        scored_candidates.sort(key=lambda x: x[3], reverse=True)
        
        # Mostrar top 5 con detalles
        print(f"      📊 TOP 5 candidatos (multi-criterio):")
        for i, (dish, raw, adj, final, spec, flav, temp) in enumerate(scored_candidates[:5], 1):
            print(f"         {i}. {dish.name}:")
            print(f"            Cultural: {adj:.0%} | Sabores: {flav:.0%} | Temp: {temp:.0%} | FINAL: {final:.0%}")
        
        # Retornar el mejor candidato
        best = scored_candidates[0]
        best_dish = best[0]
        final_score = best[3]
        
        print(f"      ✅ SELECCIONADO: {best_dish.name} (score final: {final_score:.0%})")
        return best_dish
    
    def _adapt_for_culture(self, menu: Menu, 
                          original_culture: Optional[CulturalTradition],
                          target_culture: Optional[CulturalTradition],
                          request: Request) -> List[str]:
        """
        Adapta el menú a una cultura gastronómica diferente.
        
        Si el cliente solicita una cultura específica y el caso tiene
        una cultura diferente, adaptamos los ingredientes para que sean
        más apropiados a la cultura objetivo.
        
        ESTRATEGIA: Acepta sustituciones siempre que mejoren la similitud
        cultural del plato, no basándose en umbral fijo de confianza.
        
        Args:
            menu: Menú a adaptar (se modifica in-place)
            original_culture: Cultura del caso original
            target_culture: Cultura solicitada por el cliente
            request: Solicitud del cliente (para validar restricciones)
            
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
            
            # Calcular similitud cultural ANTES de adaptar
            original_score = adapter.get_cultural_score(dish.ingredients, target_culture)
            
            # DECISIÓN: ¿Adaptar ingredientes o buscar plato diferente?
            # Buscar reemplazo si el plato tiene MUY POCOS ingredientes apropiados
            # Usar criterio relativo: si <40% de ingredientes son apropiados
            if original_score < 0.40:
                # El plato es culturalmente muy diferente - buscar reemplazo
                replacement_dish = self._find_cultural_dish_replacement(
                    dish, target_culture, menu, request
                )
                
                if replacement_dish:
                    setattr(menu, dish_attr, replacement_dish)
                    adaptations.append(
                        f"Plato reemplazado: {dish.name} → {replacement_dish.name} "
                        f"(demasiado diferente culturalmente, score: {original_score:.0%})"
                    )
                    
                    # Registrar en adaptaciones
                    menu.cultural_adaptations.append({
                        "dish_id": replacement_dish.id,
                        "dish_name": replacement_dish.name,
                        "original_dish": dish.name,
                        "target_culture": target_culture if isinstance(target_culture, str) else target_culture.value,
                        "adaptation_type": "dish_replacement",
                        "reason": f"Original dish too culturally different (score: {original_score:.0%})",
                        "score_before": f"{original_score:.2f}",
                        "score_after": "1.00"  # Plato nuevo es apropiado
                    })
                    continue  # No adaptar ingredientes del plato reemplazado
            
            # Si el plato tiene suficientes ingredientes apropiados (>=40%), adaptar
            # Adaptar ingredientes UNO POR UNO para ver mejora incremental
            current_ingredients = dish.ingredients.copy()
            current_score = original_score
            dish_substitutions = []
            
            for ingredient in dish.ingredients:
                # Intentar sustituir este ingrediente
                substitution = adapter.find_substitution(ingredient, target_culture)
                
                if substitution:
                    # Aplicar temporalmente la sustitución
                    temp_ingredients = [
                        substitution.replacement if ing == ingredient else ing
                        for ing in current_ingredients
                    ]
                    
                    # Calcular nuevo score
                    new_score = adapter.get_cultural_score(temp_ingredients, target_culture)
                    
                    # Solo aplicar si mejora
                    if new_score > current_score:
                        improvement = new_score - current_score
                        current_ingredients = temp_ingredients
                        
                        # Guardar con información de mejora incremental
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
            
            # Si hubo mejoras, aplicar todas las sustituciones
            if dish_substitutions:
                # Actualizar ingredientes del plato
                dish.ingredients = current_ingredients
                
                # Registrar adaptaciones con mejora individual
                subs_desc = []
                for item in dish_substitutions:
                    sub = item['substitution']
                    improvement_pct = item['improvement'] * 100
                    subs_desc.append(
                        f"{sub.original}→{sub.replacement} (+{improvement_pct:.0f}%)"
                    )
                
                final_improvement = current_score - original_score
                adaptations.append(
                    f"{dish.name}: {', '.join(subs_desc)} "
                    f"(similitud {original_score:.0%}→{current_score:.0%}, +{final_improvement*100:.0f}%)"
                )
                
                # Guardar en cultural_adaptations del menú
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
        
        # Adaptaciones realizadas
        if adaptations:
            explanations.append(f"Adaptaciones: {', '.join(adaptations)}")
        
        return explanations
