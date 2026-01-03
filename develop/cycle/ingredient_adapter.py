"""
Módulo de adaptación de ingredientes para transformación cultural.

Este módulo permite sustituir ingredientes de un plato para adaptarlo
a una tradición cultural diferente, manteniendo la esencia del plato
pero usando ingredientes más apropiados para la cultura objetivo.

Utiliza la información de ingredients.json para determinar qué
ingredientes son característicos de cada cultura y proponer sustituciones.
"""

import json
import os
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

from ..core.models import Dish, CulturalTradition


@dataclass
class IngredientSubstitution:
    """Representa una sustitución de ingrediente"""
    original: str
    replacement: str
    reason: str
    confidence: float  # 0.0-1.0, qué tan confiados estamos en la sustitución


class IngredientAdapter:
    """
    Adaptador de ingredientes para transformaciones culturales.
    
    Carga la base de conocimiento de ingredientes y proporciona
    funciones para adaptar listas de ingredientes de una cultura a otra.
    """
    
    def __init__(self):
        """Inicializa el adaptador cargando ingredients.json"""
        self._load_ingredients_knowledge()
    
    def _load_ingredients_knowledge(self):
        """Carga el conocimiento de ingredientes desde JSON"""
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'ingredients.json'
        )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.groups = data['groups']
        self.ingredient_to_cultures = data['ingredient_to_cultures']
        self.cultures = data['cultures']
        
        # Invertir para tener culture -> ingredients
        self.culture_to_ingredients = self._build_culture_to_ingredients()
        
        # Crear índice de grupos invertido (ingredient -> group)
        self.ingredient_to_group = self._build_ingredient_to_group()
    
    def _build_culture_to_ingredients(self) -> Dict[str, Set[str]]:
        """Construye un índice de cultura -> conjunto de ingredientes"""
        culture_map = {}
        
        # También extraer non_compliant_labels para cada ingrediente
        self.ingredient_non_compliant = {}
        
        for ingredient, data in self.ingredient_to_cultures.items():
            # Extraer non_compliant_labels si existe
            if 'non_compliant_labels' in data:
                self.ingredient_non_compliant[ingredient] = set(data['non_compliant_labels'])
            
            # Extraer cultures
            cultures = data.get('cultures', [])
            for culture in cultures:
                if culture not in culture_map:
                    culture_map[culture] = set()
                culture_map[culture].add(ingredient)
        
        return culture_map
    
    def _build_ingredient_to_group(self) -> Dict[str, str]:
        """Construye un índice de ingrediente -> nombre de grupo"""
        ing_to_group = {}
        
        for group_name, ingredients in self.groups.items():
            for ingredient in ingredients:
                ing_to_group[ingredient] = group_name
        
        return ing_to_group
    
    def get_cultural_ingredients(self, culture: CulturalTradition) -> Set[str]:
        """
        Obtiene los ingredientes característicos de una cultura.
        
        Args:
            culture: Tradición cultural
            
        Returns:
            Conjunto de ingredientes de esa cultura
        """
        culture_name = culture.value.capitalize()
        return self.culture_to_ingredients.get(culture_name, set())
    
    def is_ingredient_cultural(self, ingredient: str, culture) -> bool:
        """
        Verifica si un ingrediente es apropiado para una cultura.
        
        Args:
            ingredient: Nombre del ingrediente
            culture: Tradición cultural (enum o string)
            
        Returns:
            True si es apropiado, False si no
        """
        cultures = self.ingredient_to_cultures.get(ingredient, {})
        if isinstance(cultures, dict):
            cultures = cultures.get('cultures', [])
        
        # Universal siempre es apropiado
        if 'Universal' in cultures:
            return True
        
        # Manejar cultura como string o enum
        if isinstance(culture, str):
            culture_name = culture.capitalize()
        else:
            culture_name = culture.value.capitalize()
        
        return culture_name in cultures
    
    def violates_dietary_restriction(self, ingredient: str, dietary_label: str) -> bool:
        """
        Verifica si un ingrediente viola una restricción dietética.
        
        Args:
            ingredient: Nombre del ingrediente
            dietary_label: Etiqueta dietética (ej: 'vegan', 'gluten-free')
            
        Returns:
            True si el ingrediente NO cumple la restricción (la viola)
        """
        non_compliant = self.ingredient_non_compliant.get(ingredient, set())
        return dietary_label in non_compliant
    
    def get_compliant_ingredients(self, dietary_label: str) -> Set[str]:
        """
        Obtiene ingredientes que cumplen una restricción dietética.
        
        Args:
            dietary_label: Etiqueta dietética (ej: 'vegan', 'gluten-free')
            
        Returns:
            Conjunto de ingredientes que NO violan la restricción
        """
        compliant = set()
        for ingredient in self.ingredient_to_cultures.keys():
            if not self.violates_dietary_restriction(ingredient, dietary_label):
                compliant.add(ingredient)
        return compliant
    
    def is_ingredient_cultural(self, ingredient: str, 
                              culture: CulturalTradition) -> bool:
        """
        Verifica si un ingrediente es apropiado para una cultura.
        
        Args:
            ingredient: Ingrediente a verificar
            culture: Tradición cultural
            
        Returns:
            True si el ingrediente es apropiado para esa cultura
        """
        cultures = self.ingredient_to_cultures.get(ingredient, [])
        
        # Universal siempre es apropiado
        if 'Universal' in cultures:
            return True
        
        # Manejar cultura como string o enum
        if isinstance(culture, str):
            culture_name = culture.capitalize()
        else:
            culture_name = culture.value.capitalize()
        
        return culture_name in cultures
    
    def find_substitution(self, ingredient: str, 
                         target_culture: CulturalTradition) -> Optional[IngredientSubstitution]:
        """
        Encuentra una sustitución apropiada para un ingrediente en una cultura objetivo.
        
        Estrategia MEJORADA (prioriza sabor sobre universalidad):
        1. Buscar ingrediente del MISMO GRUPO que sea de la cultura objetivo (90% confianza)
        2. Si no hay, buscar ingrediente del MISMO GRUPO que sea universal (70% confianza)
        3. Como último recurso, mantener original si ya es universal (60% confianza)
        
        Args:
            ingredient: Ingrediente a sustituir
            target_culture: Cultura objetivo
            
        Returns:
            Sustitución o None si no es necesaria
        """
        # Si ya es apropiado para la cultura, no sustituir
        if self.is_ingredient_cultural(ingredient, target_culture):
            return None
        
        # Manejar culture como string o enum
        if isinstance(target_culture, str):
            culture_name = target_culture.capitalize()
        else:
            culture_name = target_culture.value.capitalize()
        
        # Estrategia 1: Buscar en el mismo grupo un ingrediente ESPECÍFICO de la cultura
        if ingredient in self.ingredient_to_group:
            group_name = self.ingredient_to_group[ingredient]
            group_ingredients = self.groups[group_name]
            
            # Primero buscar ingredientes ESPECÍFICOS de la cultura objetivo
            cultural_matches = [
                ing for ing in group_ingredients
                if ing != ingredient and culture_name in self.ingredient_to_cultures.get(ing, [])
            ]
            
            if cultural_matches:
                # Preferir el primero (suele ser más común)
                replacement = cultural_matches[0]
                return IngredientSubstitution(
                    original=ingredient,
                    replacement=replacement,
                    reason=f"Same group ({group_name}), specific to {culture_name} cuisine",
                    confidence=0.9
                )
            
            # Estrategia 2: Si no hay específico, buscar universal en el grupo
            universal_matches = [
                ing for ing in group_ingredients
                if ing != ingredient and 'Universal' in self.ingredient_to_cultures.get(ing, [])
            ]
            
            if universal_matches:
                replacement = universal_matches[0]
                return IngredientSubstitution(
                    original=ingredient,
                    replacement=replacement,
                    reason=f"Same group ({group_name}), universal ingredient",
                    confidence=0.7
                )
        
        # Estrategia 3: Si el ingrediente ya es universal, mantenerlo
        if 'Universal' in self.ingredient_to_cultures.get(ingredient, []):
            return None
        
        # No se encontró sustitución adecuada
        return None
    
    def adapt_ingredients(self, ingredients: List[str], 
                         target_culture: CulturalTradition,
                         min_confidence: float = 0.6) -> Tuple[List[str], List[IngredientSubstitution]]:
        """
        Adapta una lista de ingredientes a una cultura objetivo.
        
        Args:
            ingredients: Lista de ingredientes originales
            target_culture: Cultura objetivo
            min_confidence: Confianza mínima para aplicar sustitución
            
        Returns:
            Tupla de (ingredientes_adaptados, lista_de_sustituciones)
        """
        adapted_ingredients = []
        substitutions = []
        
        for ingredient in ingredients:
            substitution = self.find_substitution(ingredient, target_culture)
            
            if substitution and substitution.confidence >= min_confidence:
                adapted_ingredients.append(substitution.replacement)
                substitutions.append(substitution)
            else:
                # Mantener original
                adapted_ingredients.append(ingredient)
        
        return adapted_ingredients, substitutions
    
    def get_cultural_score(self, ingredients: List[str], 
                          culture: CulturalTradition) -> float:
        """
        Calcula qué tan culturalmente apropiados son los ingredientes.
        
        Args:
            ingredients: Lista de ingredientes
            culture: Cultura a evaluar
            
        Returns:
            Score 0.0-1.0, donde 1.0 es perfectamente cultural
        """
        if not ingredients:
            return 0.5
        
        appropriate_count = sum(
            1 for ing in ingredients 
            if self.is_ingredient_cultural(ing, culture)
        )
        
        return appropriate_count / len(ingredients)
    
    def find_dietary_substitution(self, ingredient: str, dietary_labels: List[str]) -> Optional[IngredientSubstitution]:
        """
        Busca una sustitución de ingrediente que cumpla restricciones dietéticas.
        
        IMPORTANTE: Solo sustituye ingredientes del MISMO GRUPO para mantener
        la coherencia gastronómica del plato. Si no hay sustituto en el mismo
        grupo, devuelve None (el plato no se puede adaptar).
        
        Args:
            ingredient: Ingrediente a sustituir
            dietary_labels: Lista de restricciones dietéticas a cumplir (ej: ['vegan', 'gluten-free'])
            
        Returns:
            Sustitución del mismo grupo o None si no hay alternativa adecuada
        """
        # Verificar si el ingrediente actual viola alguna restricción
        violates = [label for label in dietary_labels if self.violates_dietary_restriction(ingredient, label)]
        
        if not violates:
            # Ya cumple todas las restricciones
            return None
        
        # SOLO buscar en el mismo grupo (mantener coherencia gastronómica)
        if ingredient in self.ingredient_to_group:
            group_name = self.ingredient_to_group[ingredient]
            group_ingredients = self.groups[group_name]
            
            # Filtrar ingredientes del grupo que cumplan TODAS las restricciones
            compliant_matches = [
                ing for ing in group_ingredients
                if ing != ingredient and 
                all(not self.violates_dietary_restriction(ing, label) for label in dietary_labels)
            ]
            
            if compliant_matches:
                replacement = compliant_matches[0]
                violated_str = ', '.join(violates)
                return IngredientSubstitution(
                    original=ingredient,
                    replacement=replacement,
                    reason=f"Dietary: violates {violated_str}, same group ({group_name})",
                    confidence=0.9
                )
        
        # No hay sustituto adecuado en el mismo grupo
        return None


# Instancia global para reutilización
_adapter_instance = None

def get_ingredient_adapter() -> IngredientAdapter:
    """Obtiene la instancia singleton del adaptador de ingredientes"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = IngredientAdapter()
    return _adapter_instance
