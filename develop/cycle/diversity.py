"""
Módulo de diversificación de propuestas.

Asegura que las propuestas de menús sean suficientemente distintas
entre sí para dar opciones variadas al usuario.
"""

from typing import List
from ..core.models import Menu
from ..core.similarity import calculate_menu_similarity


def ensure_diversity(menus: List[Menu], 
                     min_distance: float = 0.3,
                     max_proposals: int = 3) -> List[Menu]:
    """
    Filtra menús para asegurar diversidad entre propuestas.
    
    Estrategia:
    1. Siempre mantener el primero (mayor similitud al request)
    2. Añadir menús subsecuentes solo si son suficientemente diferentes
       de los ya seleccionados
    3. Garantizar variedad en precio, estilo, cultura
    
    Args:
        menus: Lista de menús candidatos (ordenados por relevancia)
        min_distance: Distancia mínima entre menús (0-1)
                     1 - min_distance = máxima similitud permitida
        max_proposals: Número máximo de propuestas a retornar
        
    Returns:
        Lista de menús diversos (máximo max_proposals)
    """
    if not menus:
        return []
    
    # Siempre incluir el primero (mejor match)
    diverse_menus = [menus[0]]
    
    for menu in menus[1:]:
        if len(diverse_menus) >= max_proposals:
            break
        
        # Verificar que sea suficientemente diferente de todos los seleccionados
        is_diverse = all(
            calculate_menu_similarity(menu, existing) < (1 - min_distance)
            for existing in diverse_menus
        )
        
        if is_diverse:
            diverse_menus.append(menu)
    
    return diverse_menus


def calculate_diversity_score(menus: List[Menu]) -> float:
    """
    Calcula un score de diversidad de una lista de menús.
    
    Args:
        menus: Lista de menús
        
    Returns:
        Score 0-1 donde 1 es máxima diversidad
    """
    if len(menus) <= 1:
        return 1.0
    
    # Calcular similitud promedio entre todos los pares
    similarities = []
    for i in range(len(menus)):
        for j in range(i + 1, len(menus)):
            sim = calculate_menu_similarity(menus[i], menus[j])
            similarities.append(sim)
    
    if not similarities:
        return 1.0
    
    avg_similarity = sum(similarities) / len(similarities)
    
    # Diversidad es el complemento de similitud
    diversity = 1.0 - avg_similarity
    
    return diversity


def get_diversity_explanation(menus: List[Menu]) -> str:
    """
    Genera explicación de la diversidad de las propuestas.
    
    Args:
        menus: Lista de menús propuestos
        
    Returns:
        Texto explicativo
    """
    if len(menus) <= 1:
        return "Una única propuesta."
    
    diversity_score = calculate_diversity_score(menus)
    
    # Analizar diferencias
    differences = []
    
    # Diferencias de precio
    prices = [m.total_price for m in menus]
    price_range = max(prices) - min(prices)
    if price_range > 20:
        differences.append(f"rango de precio ({min(prices):.0f}€-{max(prices):.0f}€)")
    
    # Diferencias de estilo
    styles = [m.dominant_style for m in menus if m.dominant_style]
    unique_styles = len(set(styles))
    if unique_styles > 1:
        differences.append(f"{unique_styles} estilos culinarios")
    
    # Diferencias culturales
    cultures = [m.cultural_theme for m in menus if m.cultural_theme]
    unique_cultures = len(set(cultures))
    if unique_cultures > 1:
        differences.append(f"{unique_cultures} tradiciones culturales")
    
    if differences:
        diff_text = ", ".join(differences)
        return f"Propuestas diversificadas: {diff_text} (diversidad: {diversity_score:.0%})"
    else:
        return f"Propuestas similares entre sí (diversidad: {diversity_score:.0%})"
