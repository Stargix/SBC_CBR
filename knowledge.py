"""
Conocimiento del dominio gastronómico.

Este módulo contiene el conocimiento declarativo del dominio:
- Compatibilidades entre sabores
- Categorías incompatibles de platos
- Maridajes de vinos
- Estilos recomendados por tipo de evento
- Reglas de validación gastronómica
- Rangos de calorías por temporada

Este conocimiento se utilizó previamente en el sistema CLIPS
y ahora se adapta al paradigma CBR para enriquecer la adaptación
y validación de casos.
"""

from typing import Dict, List, Set, Tuple
from .models import (
    Flavor, Season, EventType, CulinaryStyle, DishCategory, 
    Temperature, Complexity, CulturalTradition
)


# ============================================================
# COMPATIBILIDAD DE SABORES
# ============================================================

# Diccionario de sabores compatibles
# Un sabor A es compatible con B si se complementan bien
FLAVOR_COMPATIBILITY: Dict[Flavor, List[Flavor]] = {
    Flavor.SWEET: [Flavor.SALTY, Flavor.SOUR],
    Flavor.SALTY: [Flavor.SWEET, Flavor.UMAMI, Flavor.FATTY],
    Flavor.SOUR: [Flavor.FATTY, Flavor.SWEET, Flavor.UMAMI],
    Flavor.BITTER: [Flavor.SWEET, Flavor.UMAMI, Flavor.FATTY],
    Flavor.UMAMI: [Flavor.SOUR, Flavor.BITTER],
    Flavor.FATTY: [Flavor.SOUR, Flavor.BITTER],
    Flavor.SPICY: [Flavor.SWEET, Flavor.FATTY, Flavor.SOUR]
}


def are_flavors_compatible(flavor1: Flavor, flavor2: Flavor) -> bool:
    """
    Verifica si dos sabores son compatibles.
    
    Args:
        flavor1: Primer sabor
        flavor2: Segundo sabor
        
    Returns:
        True si son compatibles
    """
    if flavor1 == flavor2:
        return True
    return flavor2 in FLAVOR_COMPATIBILITY.get(flavor1, [])


def get_compatible_flavors(flavor: Flavor) -> List[Flavor]:
    """
    Obtiene los sabores compatibles con uno dado.
    
    Args:
        flavor: Sabor de referencia
        
    Returns:
        Lista de sabores compatibles
    """
    return FLAVOR_COMPATIBILITY.get(flavor, [])


# ============================================================
# CATEGORÍAS INCOMPATIBLES DE PLATOS
# ============================================================

# Pares de categorías que no deben aparecer juntas en un menú
INCOMPATIBLE_CATEGORIES: List[Tuple[DishCategory, DishCategory]] = [
    # Sopas y cremas no se combinan entre sí
    (DishCategory.SOUP, DishCategory.CREAM),
    (DishCategory.SOUP, DishCategory.BROTH),
    (DishCategory.CREAM, DishCategory.BROTH),
    
    # Legumbres no con carbohidratos pesados
    (DishCategory.LEGUME, DishCategory.PASTA),
    (DishCategory.LEGUME, DishCategory.RICE),
    
    # Carbohidratos no se repiten
    (DishCategory.PASTA, DishCategory.RICE),
    (DishCategory.PASTA, DishCategory.PASTA),
    (DishCategory.RICE, DishCategory.RICE),
    
    # Proteínas no se mezclan
    (DishCategory.MEAT, DishCategory.FISH),
    (DishCategory.MEAT, DishCategory.POULTRY),
    (DishCategory.MEAT, DishCategory.EGG),
    (DishCategory.POULTRY, DishCategory.FISH),
    (DishCategory.FISH, DishCategory.POULTRY),
    (DishCategory.EGG, DishCategory.EGG),
    
    # Tapas y snacks
    (DishCategory.TAPAS, DishCategory.SNACK),
    (DishCategory.TAPAS, DishCategory.SOUP),
    (DishCategory.SNACK, DishCategory.SOUP),
    
    # Verduras y ensaladas
    (DishCategory.SALAD, DishCategory.VEGETABLE),
    
    # Frutas no se repiten
    (DishCategory.FRUIT, DishCategory.FRUIT),
]


def are_categories_compatible(cat1: DishCategory, cat2: DishCategory) -> bool:
    """
    Verifica si dos categorías de platos son compatibles.
    
    Args:
        cat1: Primera categoría
        cat2: Segunda categoría
        
    Returns:
        True si son compatibles (pueden aparecer juntas)
    """
    return (cat1, cat2) not in INCOMPATIBLE_CATEGORIES and \
           (cat2, cat1) not in INCOMPATIBLE_CATEGORIES


# ============================================================
# MARIDAJE DE VINOS
# ============================================================

# Compatibilidad de subtipos de vino con sabores
WINE_FLAVOR_COMPATIBILITY: Dict[str, List[Flavor]] = {
    "dry": [Flavor.SALTY, Flavor.SOUR, Flavor.FATTY],
    "fruity": [Flavor.SWEET, Flavor.UMAMI],
    "young": [Flavor.BITTER, Flavor.UMAMI],
    "full-bodied": [Flavor.FATTY, Flavor.UMAMI],
    "rose": [Flavor.SALTY, Flavor.SWEET, Flavor.UMAMI],
    "sparkling": [Flavor.SALTY, Flavor.FATTY, Flavor.SWEET],
    "sweet": [Flavor.SWEET, Flavor.UMAMI, Flavor.FATTY],  # Para postres
    "aged": [Flavor.UMAMI, Flavor.FATTY]
}


def is_wine_compatible_with_flavors(wine_subtype: str, flavors: List[Flavor], 
                                    is_dessert: bool = False) -> bool:
    """
    Verifica si un tipo de vino es compatible con los sabores del plato.
    
    Args:
        wine_subtype: Subtipo de vino
        flavors: Sabores del plato
        is_dessert: Si es para un postre (usa reglas diferentes)
        
    Returns:
        True si hay al menos un sabor compatible
    """
    compatible_flavors = WINE_FLAVOR_COMPATIBILITY.get(wine_subtype, [])
    
    # Para postres, priorizar vinos dulces y espumosos
    if is_dessert:
        if wine_subtype not in ["sweet", "sparkling"]:
            return False
    
    return any(f in compatible_flavors for f in flavors)


def get_wine_priority(wine_subtype: str, is_dessert: bool = False) -> int:
    """
    Obtiene la prioridad de un tipo de vino para selección.
    
    Args:
        wine_subtype: Subtipo de vino
        is_dessert: Si es para un postre
        
    Returns:
        Prioridad (mayor = mejor)
    """
    if is_dessert:
        dessert_priority = {
            "sweet": 50,
            "sparkling": 40,
        }
        return dessert_priority.get(wine_subtype, 5)
    else:
        main_priority = {
            "full-bodied": 25,
            "fruity": 20,
            "rose": 18,
            "dry": 15,
            "young": 12,
            "sparkling": 10,
            "aged": 10,
        }
        return main_priority.get(wine_subtype, 5)


# ============================================================
# ESTILOS POR TIPO DE EVENTO
# ============================================================

# Estilos recomendados por tipo de evento con prioridad
EVENT_STYLES: Dict[EventType, List[Tuple[CulinaryStyle, int]]] = {
    EventType.WEDDING: [
        (CulinaryStyle.SIBARITA, 1),
        (CulinaryStyle.GOURMET, 1),
        (CulinaryStyle.CLASSIC, 2),
        (CulinaryStyle.FUSION, 2),
        (CulinaryStyle.MODERN, 3),
    ],
    EventType.CHRISTENING: [
        (CulinaryStyle.CLASSIC, 1),
        (CulinaryStyle.REGIONAL, 1),
        (CulinaryStyle.MODERN, 2),
    ],
    EventType.COMMUNION: [
        (CulinaryStyle.CLASSIC, 1),
        (CulinaryStyle.REGIONAL, 1),
        (CulinaryStyle.FUSION, 2),
        (CulinaryStyle.SUAVE, 2),
    ],
    EventType.FAMILIAR: [
        (CulinaryStyle.REGIONAL, 1),
        (CulinaryStyle.CLASSIC, 1),
        (CulinaryStyle.FUSION, 2),
    ],
    EventType.CONGRESS: [
        (CulinaryStyle.CLASSIC, 1),
        (CulinaryStyle.MODERN, 1),
        (CulinaryStyle.FUSION, 2),
        (CulinaryStyle.GOURMET, 2),
    ],
    EventType.CORPORATE: [
        (CulinaryStyle.CLASSIC, 1),
        (CulinaryStyle.MODERN, 1),
        (CulinaryStyle.FUSION, 2),
        (CulinaryStyle.GOURMET, 2),
    ],
}


def get_preferred_styles_for_event(event_type: EventType) -> List[CulinaryStyle]:
    """
    Obtiene los estilos preferidos para un tipo de evento, ordenados por prioridad.
    
    Args:
        event_type: Tipo de evento
        
    Returns:
        Lista de estilos ordenados por preferencia
    """
    styles_with_priority = EVENT_STYLES.get(event_type, [])
    # Ordenar por prioridad (menor número = mayor prioridad)
    sorted_styles = sorted(styles_with_priority, key=lambda x: x[1])
    return [style for style, _ in sorted_styles]


def is_style_appropriate_for_event(style: CulinaryStyle, event_type: EventType) -> bool:
    """
    Verifica si un estilo es apropiado para un evento.
    
    Args:
        style: Estilo culinario
        event_type: Tipo de evento
        
    Returns:
        True si el estilo es apropiado
    """
    preferred = get_preferred_styles_for_event(event_type)
    return style in preferred


# ============================================================
# COMPLEJIDAD POR TIPO DE EVENTO
# ============================================================

EVENT_COMPLEXITY: Dict[EventType, List[Complexity]] = {
    EventType.WEDDING: [Complexity.MEDIUM, Complexity.HIGH],
    EventType.CHRISTENING: [Complexity.LOW, Complexity.MEDIUM],
    EventType.COMMUNION: [Complexity.LOW, Complexity.MEDIUM],
    EventType.FAMILIAR: [Complexity.LOW, Complexity.MEDIUM],
    EventType.CONGRESS: [Complexity.MEDIUM],
    EventType.CORPORATE: [Complexity.MEDIUM],
}


def is_complexity_appropriate(complexity: Complexity, event_type: EventType, 
                              budget: float) -> bool:
    """
    Verifica si la complejidad es apropiada para el evento y presupuesto.
    
    Args:
        complexity: Complejidad del plato
        event_type: Tipo de evento
        budget: Presupuesto máximo
        
    Returns:
        True si la complejidad es apropiada
    """
    allowed = EVENT_COMPLEXITY.get(event_type, [Complexity.MEDIUM])
    
    # Regla especial: bodas con presupuesto bajo evitan alta complejidad
    if event_type == EventType.WEDDING and budget < 50 and complexity == Complexity.HIGH:
        return False
    
    return complexity in allowed


# ============================================================
# CALORÍAS POR TEMPORADA
# ============================================================

CALORIE_RANGES: Dict[Season, Tuple[int, int]] = {
    Season.SUMMER: (550, 950),   # Menús más ligeros
    Season.WINTER: (850, 1450),  # Menús más contundentes
    Season.SPRING: (650, 1250),  # Intermedio
    Season.AUTUMN: (650, 1250),  # Intermedio
    Season.ALL: (550, 1450),     # Rango completo
}


def get_calorie_range(season: Season) -> Tuple[int, int]:
    """
    Obtiene el rango de calorías recomendado para una temporada.
    
    Args:
        season: Temporada
        
    Returns:
        Tupla (min, max) de calorías
    """
    return CALORIE_RANGES.get(season, (650, 1250))


def is_calorie_count_appropriate(calories: int, season: Season) -> bool:
    """
    Verifica si el conteo de calorías es apropiado para la temporada.
    
    Args:
        calories: Calorías totales del menú
        season: Temporada
        
    Returns:
        True si está dentro del rango apropiado
    """
    min_cal, max_cal = get_calorie_range(season)
    return min_cal <= calories <= max_cal


# ============================================================
# TEMPERATURA DEL ENTRANTE POR TEMPORADA
# ============================================================

APPROPRIATE_STARTER_TEMPS: Dict[Season, List[Temperature]] = {
    Season.SUMMER: [Temperature.COLD, Temperature.WARM],
    Season.WINTER: [Temperature.HOT],
    Season.SPRING: [Temperature.WARM, Temperature.COLD, Temperature.HOT],
    Season.AUTUMN: [Temperature.WARM, Temperature.HOT],
    Season.ALL: [Temperature.HOT, Temperature.WARM, Temperature.COLD],
}


def is_starter_temperature_appropriate(temp: Temperature, season: Season) -> bool:
    """
    Verifica si la temperatura del entrante es apropiada para la temporada.
    
    Args:
        temp: Temperatura del plato
        season: Temporada
        
    Returns:
        True si es apropiada
    """
    allowed = APPROPRIATE_STARTER_TEMPS.get(season, [Temperature.WARM])
    return temp in allowed


# ============================================================
# PROGRESIÓN GASTRONÓMICA
# ============================================================

# Categorías de entrantes que funcionan bien antes de diferentes principales
GOOD_PROGRESSIONS: Dict[DishCategory, List[DishCategory]] = {
    DishCategory.SALAD: [DishCategory.MEAT, DishCategory.FISH, DishCategory.POULTRY],
    DishCategory.VEGETABLE: [DishCategory.MEAT, DishCategory.FISH, DishCategory.POULTRY],
    DishCategory.SOUP: [DishCategory.MEAT, DishCategory.PASTA, DishCategory.RICE],
    DishCategory.CREAM: [DishCategory.FISH, DishCategory.POULTRY],
    DishCategory.TAPAS: [DishCategory.MEAT, DishCategory.FISH],
}


def is_good_progression(starter_cat: DishCategory, main_cat: DishCategory) -> bool:
    """
    Verifica si hay una buena progresión entre entrante y principal.
    
    Args:
        starter_cat: Categoría del entrante
        main_cat: Categoría del principal
        
    Returns:
        True si es una buena progresión
    """
    good_mains = GOOD_PROGRESSIONS.get(starter_cat, [])
    return main_cat in good_mains


# ============================================================
# POSTRES RECOMENDADOS TRAS PLATOS GRASOS
# ============================================================

def is_dessert_appropriate_after_fatty(main_has_fatty: bool, 
                                       dessert_category: DishCategory,
                                       dessert_flavors: List[Flavor]) -> bool:
    """
    Verifica si el postre es apropiado después de un plato graso.
    
    Los postres ácidos o de frutas son mejores para limpiar el paladar.
    
    Args:
        main_has_fatty: Si el principal tiene sabor graso
        dessert_category: Categoría del postre
        dessert_flavors: Sabores del postre
        
    Returns:
        True si es apropiado
    """
    if not main_has_fatty:
        return True
    
    # Frutas refrescan el paladar
    if dessert_category == DishCategory.FRUIT:
        return True
    
    # Sabores ácidos limpian el paladar
    if Flavor.SOUR in dessert_flavors:
        return True
    
    # Los postres muy dulces y grasos no son ideales
    if Flavor.FATTY in dessert_flavors and Flavor.SWEET in dessert_flavors:
        return False
    
    return True


# ============================================================
# TRADICIONES CULTURALES Y SUS CARACTERÍSTICAS
# ============================================================

CULTURAL_CHARACTERISTICS: Dict[CulturalTradition, Dict] = {
    CulturalTradition.MEDITERRANEAN: {
        "key_ingredients": ["olive_oil", "tomato", "garlic", "herbs"],
        "typical_categories": [DishCategory.FISH, DishCategory.SALAD, DishCategory.VEGETABLE],
        "styles": [CulinaryStyle.CLASSIC, CulinaryStyle.REGIONAL],
    },
    CulturalTradition.CATALAN: {
        "key_ingredients": ["olive_oil", "tomato", "garlic", "almond", "romesco"],
        "typical_categories": [DishCategory.FISH, DishCategory.MEAT, DishCategory.VEGETABLE],
        "styles": [CulinaryStyle.REGIONAL, CulinaryStyle.SIBARITA],
    },
    CulturalTradition.BASQUE: {
        "key_ingredients": ["bacalao", "pintxos", "txakoli", "idiazabal"],
        "typical_categories": [DishCategory.FISH, DishCategory.TAPAS, DishCategory.MEAT],
        "styles": [CulinaryStyle.GOURMET, CulinaryStyle.REGIONAL],
    },
    CulturalTradition.ITALIAN: {
        "key_ingredients": ["pasta", "olive_oil", "tomato", "parmesan", "basil"],
        "typical_categories": [DishCategory.PASTA, DishCategory.MEAT, DishCategory.VEGETABLE],
        "styles": [CulinaryStyle.CLASSIC, CulinaryStyle.REGIONAL],
    },
    CulturalTradition.FRENCH: {
        "key_ingredients": ["butter", "cream", "wine", "herbs"],
        "typical_categories": [DishCategory.CREAM, DishCategory.MEAT, DishCategory.PASTRY],
        "styles": [CulinaryStyle.CLASSIC, CulinaryStyle.GOURMET],
    },
    CulturalTradition.MOROCCAN: {
        "key_ingredients": ["spices", "lamb", "couscous", "dates", "almonds"],
        "typical_categories": [DishCategory.MEAT, DishCategory.LEGUME],
        "styles": [CulinaryStyle.FUSION, CulinaryStyle.REGIONAL],
    },
    CulturalTradition.JAPANESE: {
        "key_ingredients": ["soy", "rice", "fish", "seaweed", "miso"],
        "typical_categories": [DishCategory.FISH, DishCategory.RICE],
        "styles": [CulinaryStyle.MODERN, CulinaryStyle.SIBARITA],
    },
    CulturalTradition.NORDIC: {
        "key_ingredients": ["fish", "berries", "root_vegetables", "rye"],
        "typical_categories": [DishCategory.FISH, DishCategory.VEGETABLE],
        "styles": [CulinaryStyle.MODERN, CulinaryStyle.REGIONAL],
    },
}


def get_cultural_characteristics(tradition: CulturalTradition) -> Dict:
    """
    Obtiene las características de una tradición cultural.
    
    Args:
        tradition: Tradición cultural
        
    Returns:
        Diccionario con características
    """
    return CULTURAL_CHARACTERISTICS.get(tradition, {})


# ============================================================
# PROPORCIONES DE PRECIO EN EL MENÚ
# ============================================================

# Proporciones objetivo de precio por componente según categoría
# (starter_min, starter_max, main_min, main_max, dessert_min, dessert_max)
PRICE_PROPORTIONS = {
    "economico": (0.10, 0.30, 0.30, 0.50, 0.08, 0.25),
    "medio": (0.15, 0.30, 0.35, 0.50, 0.12, 0.25),
    "premium": (0.12, 0.25, 0.35, 0.50, 0.12, 0.25),
}


def classify_price_category(price: float, min_price: float, max_price: float) -> str:
    """
    Clasifica un precio en categoría económico/medio/premium.
    
    Args:
        price: Precio del menú
        min_price: Precio mínimo del rango
        max_price: Precio máximo del rango
        
    Returns:
        Categoría de precio
    """
    if max_price == min_price:
        return "medio"
    
    position = (price - min_price) / (max_price - min_price)
    
    if position < 0.33:
        return "economico"
    elif position < 0.67:
        return "medio"
    else:
        return "premium"


def validate_price_proportions(starter_price: float, main_price: float, 
                               dessert_price: float, category: str,
                               tolerance: float = 0.25) -> bool:
    """
    Valida si las proporciones de precio son correctas.
    
    Args:
        starter_price: Precio del entrante
        main_price: Precio del principal
        dessert_price: Precio del postre
        category: Categoría de precio
        tolerance: Tolerancia adicional
        
    Returns:
        True si las proporciones son válidas
    """
    total = starter_price + main_price + dessert_price
    if total == 0:
        return False
    
    proportions = PRICE_PROPORTIONS.get(category, PRICE_PROPORTIONS["medio"])
    
    s_min, s_max = proportions[0] - tolerance, proportions[1] + tolerance
    m_min, m_max = proportions[2] - tolerance, proportions[3] + tolerance
    d_min, d_max = proportions[4] - tolerance, proportions[5] + tolerance
    
    s_prop = starter_price / total
    m_prop = main_price / total
    d_prop = dessert_price / total
    
    return (s_min <= s_prop <= s_max and 
            m_min <= m_prop <= m_max and 
            d_min <= d_prop <= d_max)


# ============================================================
# ALIAS Y COMPATIBILIDAD
# ============================================================

# Aliases para compatibilidad con módulos que esperan estos nombres
CATEGORY_INCOMPATIBILITIES = INCOMPATIBLE_CATEGORIES
WINE_COMPATIBILITY = WINE_FLAVOR_COMPATIBILITY
EVENT_STYLE_PREFERENCES = EVENT_STYLES
CULTURAL_TRADITIONS = CULTURAL_CHARACTERISTICS

# Descripciones de estilos culinarios
STYLE_DESCRIPTIONS = {
    CulinaryStyle.CLASSIC: "Cocina clásica que respeta las tradiciones culinarias establecidas, con técnicas probadas y presentación elegante.",
    CulinaryStyle.MODERN: "Cocina de vanguardia que experimenta con técnicas contemporáneas y presentaciones innovadoras.",
    CulinaryStyle.FUSION: "Combinación de influencias culinarias de diferentes culturas, creando nuevas armonías de sabores.",
    CulinaryStyle.REGIONAL: "Cocina de autor que celebra los productos locales y las tradiciones regionales específicas.",
    CulinaryStyle.SIBARITA: "Alta cocina refinada con técnicas avanzadas, presentación artística y creatividad molecular.",
    CulinaryStyle.GOURMET: "Gastronomía de lujo centrada en ingredientes de máxima calidad y elaboración meticulosa."
}

# Firma de chefs de referencia
CHEF_SIGNATURES = {
    CulinaryStyle.SIBARITA: {
        "chef": "Ferran Adrià",
        "restaurant": "elBulli",
        "characteristics": ["esferificación", "gelificación", "espumas", "técnicas moleculares"]
    },
    CulinaryStyle.GOURMET: {
        "chef": "Paul Bocuse",
        "restaurant": "L'Auberge du Pont de Collonges",
        "characteristics": ["nouvelle cuisine", "presentación elegante", "salsas finas"]
    },
    CulinaryStyle.CLASSIC: {
        "chef": "Auguste Escoffier",
        "restaurant": "Savoy Hotel",
        "characteristics": ["recetas francesas clásicas", "presentación formal"]
    },
    CulinaryStyle.FUSION: {
        "chef": "Nobu Matsuhisa",
        "restaurant": "Nobu",
        "characteristics": ["cocina japonesa-peruana", "técnicas de vanguardia"]
    },
    CulinaryStyle.MODERN: {
        "chef": "Grant Achatz",
        "restaurant": "Alinea",
        "characteristics": ["experiencia multisensorial", "presentación teatral"]
    },
    CulinaryStyle.REGIONAL: {
        "chef": "Juan Mari Arzak",
        "restaurant": "Arzak",
        "characteristics": ["cocina vasca de autor", "productos locales", "innovación"]
    }
}
