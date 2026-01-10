"""
Módulo de adaptación de ingredientes para transformación cultural y dietética.

Este módulo permite sustituir ingredientes de un plato para adaptarlo
a una tradición cultural diferente o a restricciones dietéticas,
manteniendo la esencia del plato pero usando ingredientes más apropiados.

RESPONSABILIDADES:
- Encontrar sustituciones de ingredientes (find_substitution)
- Adaptar listas completas de ingredientes (adapt_ingredients)
- Manejar restricciones dietéticas (find_dietary_substitution)

NOTA: El análisis de similitud cultural (get_cultural_score, is_ingredient_cultural)
se encuentra en develop.core.similarity.SimilarityCalculator
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
        
        # Import here to avoid circular dependency
        from ..core.similarity import SimilarityCalculator
        self.similarity_calc = SimilarityCalculator()
        
        # Inicializar semantic calculator si está disponible
        self.semantic_calc = None
        if self.similarity_calc.semantic_calculator:
            self.semantic_calc = self.similarity_calc.semantic_calculator
    
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
    
    def _find_similar_cultures(self, target_culture: CulturalTradition, 
                              threshold: float = 0.6) -> List[Tuple[str, float]]:
        """
        Encuentra culturas semánticamente similares a la cultura objetivo.
        
        Args:
            target_culture: Cultura objetivo
            threshold: Umbral mínimo de similaridad (0-1)
            
        Returns:
            Lista de tuplas (nombre_cultura, similaridad) ordenadas por similaridad descendente
        """
        if self.semantic_calc is None:
            return []
        
        # Importar CulturalTradition para iterar sobre todas las culturas
        from ..core.models import CulturalTradition as CT
        
        similar_cultures = []
        
        # Calcular similaridad con todas las demás culturas
        for culture in CT:
            if culture == target_culture:
                continue  # Excluir la cultura objetivo
            
            similarity = self.semantic_calc.calculate_cultural_similarity(target_culture, culture)
            
            if similarity >= threshold:
                similar_cultures.append((culture.value, similarity))
        
        # Ordenar por similaridad descendente
        similar_cultures.sort(key=lambda x: x[1], reverse=True)
        
        return similar_cultures
    
    def find_substitution(self, ingredient: str, 
                         target_culture: CulturalTradition) -> Optional[IngredientSubstitution]:
        """
        Encuentra una sustitución apropiada para un ingrediente en una cultura objetivo.
        
        Estrategia MEJORADA (prioriza sabor sobre universalidad):
        1. Buscar ingrediente del MISMO GRUPO que sea de la cultura objetivo (90% confianza)
        2. Si no hay, buscar ingrediente del MISMO GRUPO de culturas semánticamente similares (80% confianza)
        3. Si no hay, buscar ingrediente del MISMO GRUPO que sea universal (70% confianza)
        4. Como último recurso, mantener original si ya es universal (60% confianza)
        
        Args:
            ingredient: Ingrediente a sustituir
            target_culture: Cultura objetivo
            
        Returns:
            Sustitución o None si no es necesaria
        """
        # Si ya es apropiado para la cultura, no sustituir
        if self.similarity_calc.is_ingredient_cultural(ingredient, target_culture):
            return None
        
        # Manejar culture como string o enum
        if isinstance(target_culture, str):
            culture_name = target_culture.lower()
        else:
            culture_name = target_culture.value.lower()
        
        # Estrategia 1: Buscar en el mismo grupo un ingrediente ESPECÍFICO de la cultura
        if ingredient in self.ingredient_to_group:
            group_name = self.ingredient_to_group[ingredient]
            group_ingredients = self.groups[group_name]
            
            # Primero buscar ingredientes ESPECÍFICOS de la cultura objetivo
            cultural_matches = []
            for ing in group_ingredients:
                if ing != ingredient:
                    ing_data = self.ingredient_to_cultures.get(ing, {})
                    cultures = ing_data.get('cultures', []) if isinstance(ing_data, dict) else ing_data
                    cultures_lower = [c.lower() for c in cultures] if isinstance(cultures, list) else []
                    if culture_name in cultures_lower:
                        cultural_matches.append(ing)
            
            if cultural_matches:
                # Preferir el primero (suele ser más común)
                replacement = cultural_matches[0]
                return IngredientSubstitution(
                    original=ingredient,
                    replacement=replacement,
                    reason=f"Same group ({group_name}), specific to {culture_name} cuisine",
                    confidence=0.9
                )
            
            # Estrategia 2: Si no hay específico, buscar en culturas semánticamente similares
            if self.semantic_calc is not None:
                # Calcular similaridad semántica con todas las culturas disponibles
                similar_cultures = self._find_similar_cultures(target_culture, threshold=0.6)
                
                if similar_cultures:
                    # Buscar ingredientes de culturas similares en el mismo grupo
                    similar_cultural_matches = []
                    for similar_culture, similarity in similar_cultures:
                        for ing in group_ingredients:
                            if ing != ingredient:
                                ing_data = self.ingredient_to_cultures.get(ing, {})
                                cultures = ing_data.get('cultures', []) if isinstance(ing_data, dict) else ing_data
                                cultures_lower = [c.lower() for c in cultures] if isinstance(cultures, list) else []
                                if similar_culture.lower() in cultures_lower:
                                    similar_cultural_matches.append((ing, similarity, similar_culture))
                    
                    if similar_cultural_matches:
                        # Ordenar por similaridad (mayor primero)
                        similar_cultural_matches.sort(key=lambda x: x[1], reverse=True)
                        replacement, sim_score, source_culture = similar_cultural_matches[0]
                        return IngredientSubstitution(
                            original=ingredient,
                            replacement=replacement,
                            reason=f"Same group ({group_name}), from similar culture {source_culture} (similarity: {sim_score:.2f})",
                            confidence=0.8
                        )
            
            # Estrategia 3: Si no hay específico ni similar, buscar universal en el grupo
            universal_matches = []
            for ing in group_ingredients:
                if ing != ingredient:
                    ing_data = self.ingredient_to_cultures.get(ing, {})
                    cultures = ing_data.get('cultures', []) if isinstance(ing_data, dict) else ing_data
                    cultures_lower = [c.lower() for c in cultures] if isinstance(cultures, list) else []
                    if 'universal' in cultures_lower:
                        universal_matches.append(ing)
            
            if universal_matches:
                replacement = universal_matches[0]
                return IngredientSubstitution(
                    original=ingredient,
                    replacement=replacement,
                    reason=f"Same group ({group_name}), universal ingredient",
                    confidence=0.7
                )
        
        # Estrategia 4: Si el ingrediente ya es universal, mantenerlo
        ing_data = self.ingredient_to_cultures.get(ingredient, {})
        cultures = ing_data.get('cultures', []) if isinstance(ing_data, dict) else ing_data
        cultures_lower = [c.lower() for c in cultures] if isinstance(cultures, list) else []
        if 'universal' in cultures_lower:
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
