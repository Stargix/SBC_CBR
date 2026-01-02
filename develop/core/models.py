"""
Modelos de datos para el sistema CBR de elaboración de menús.

Este módulo define las estructuras de datos fundamentales:
- Dish: Representa un plato con sus atributos gastronómicos
- Beverage: Representa una bebida 
- Menu: Un menú completo (starter, main, dessert, beverage)
- Request: Solicitud del cliente con restricciones y preferencias
- Case: Un caso CBR que asocia un contexto (Request) con una solución (Menu)

La estructura de casos sigue el paradigma CBR donde cada caso representa
una experiencia previa de elaboración de menú satisfactoria.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from enum import Enum
import uuid


class EventType(Enum):
    """Tipos de eventos soportados"""
    WEDDING = "wedding"
    FAMILIAR = "familiar"
    CONGRESS = "congress"
    CORPORATE = "corporate"
    CHRISTENING = "christening"
    COMMUNION = "communion"


class Season(Enum):
    """Estaciones del año"""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    ALL = "all"


class DishType(Enum):
    """Tipo de plato en el menú"""
    STARTER = "starter"
    MAIN_COURSE = "main_course"
    DESSERT = "dessert"


class DishCategory(Enum):
    """Categorías gastronómicas de platos"""
    SOUP = "soup"
    CREAM = "cream"
    BROTH = "broth"
    SALAD = "salad"
    VEGETABLE = "vegetable"
    LEGUME = "legume"
    PASTA = "pasta"
    RICE = "rice"
    MEAT = "meat"
    POULTRY = "poultry"
    FISH = "fish"
    SEAFOOD = "seafood"
    EGG = "egg"
    TAPAS = "tapas"
    SNACK = "snack"
    FRUIT = "fruit"
    PASTRY = "pastry"
    ICE_CREAM = "ice_cream"


class CulinaryStyle(Enum):
    """Estilos culinarios"""
    CLASSIC = "classic"
    MODERN = "modern"
    FUSION = "fusion"
    REGIONAL = "regional"
    SIBARITA = "sibarita"        # Alta cocina, molecular
    GOURMET = "gourmet"          # Gourmet refinado
    CLASSICAL = "classical"
    SUAVE = "suave"              # Suave, familiar


class CulturalTradition(Enum):
    """Tradiciones culturales gastronómicas"""
    MEDITERRANEAN = "mediterranean"
    CATALAN = "catalan"
    BASQUE = "basque"
    GALICIAN = "galician"
    ITALIAN = "italian"
    FRENCH = "french"
    GREEK = "greek"
    MOROCCAN = "moroccan"
    TURKISH = "turkish"
    LEBANESE = "lebanese"
    NORDIC = "nordic"
    RUSSIAN = "russian"
    JAPANESE = "japanese"
    MEXICAN = "mexican"
    SPANISH = "spanish"


class Temperature(Enum):
    """Temperatura de servicio del plato"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class Complexity(Enum):
    """Complejidad de elaboración"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Flavor(Enum):
    """Sabores principales"""
    SWEET = "sweet"
    SALTY = "salty"
    SOUR = "sour"
    BITTER = "bitter"
    UMAMI = "umami"
    FATTY = "fatty"
    SPICY = "spicy"


@dataclass
class Dish:
    """
    Representa un plato gastronómico.
    
    Atributos:
        id: Identificador único del plato
        name: Nombre del plato
        dish_type: Tipo (starter, main_course, dessert)
        price: Precio por persona
        category: Categoría gastronómica
        styles: Estilos culinarios asociados
        seasons: Temporadas en que está disponible
        temperature: Temperatura de servicio
        complexity: Complejidad de elaboración
        calories: Calorías aproximadas
        max_guests: Máximo de comensales que puede servir
        flavors: Sabores principales
        diets: Dietas compatibles
        ingredients: Lista de ingredientes principales
        compatible_beverages: IDs de bebidas compatibles
        cultural_traditions: Tradiciones culturales asociadas
        chef_style: Estilo de chef inspirador (ej: "Ferran Adrià", "Arzak")
        presentation_notes: Notas sobre presentación
    """
    id: str
    name: str
    dish_type: DishType
    price: float
    category: DishCategory
    styles: List[CulinaryStyle] = field(default_factory=list)
    seasons: List[Season] = field(default_factory=lambda: [Season.ALL])
    temperature: Temperature = Temperature.WARM
    complexity: Complexity = Complexity.MEDIUM
    calories: int = 300
    max_guests: int = 400
    flavors: List[Flavor] = field(default_factory=list)
    diets: List[str] = field(default_factory=list)
    ingredients: List[str] = field(default_factory=list)
    compatible_beverages: List[str] = field(default_factory=list)
    cultural_traditions: List[CulturalTradition] = field(default_factory=list)
    chef_style: Optional[str] = None
    presentation_notes: str = ""
    
    def is_available_in_season(self, season: Season) -> bool:
        """Verifica si el plato está disponible en una temporada"""
        return Season.ALL in self.seasons or season in self.seasons
    
    def meets_dietary_restrictions(self, required_diets: List[str]) -> bool:
        """Verifica si el plato cumple con las restricciones dietéticas"""
        return all(diet in self.diets for diet in required_diets)
    
    def has_restricted_ingredient(self, restricted: List[str]) -> bool:
        """Verifica si contiene ingredientes restringidos"""
        return any(ing in self.ingredients for ing in restricted)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el plato a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'dish_type': self.dish_type.value,
            'price': self.price,
            'category': self.category.value,
            'styles': [s.value for s in self.styles],
            'seasons': [s.value for s in self.seasons],
            'temperature': self.temperature.value,
            'complexity': self.complexity.value,
            'calories': self.calories,
            'max_guests': self.max_guests,
            'flavors': [f.value for f in self.flavors],
            'diets': self.diets,
            'ingredients': self.ingredients,
            'compatible_beverages': self.compatible_beverages,
            'cultural_traditions': [t.value for t in self.cultural_traditions],
            'chef_style': self.chef_style,
            'presentation_notes': self.presentation_notes
        }


@dataclass
class Beverage:
    """
    Representa una bebida.
    
    Atributos:
        id: Identificador único
        name: Nombre de la bebida
        alcoholic: Si contiene alcohol
        price: Precio por persona
        type: Tipo de bebida (red-wine, white-wine, herbal-tea, soft-drink, etc.)
        subtype: Subtipo opcional (dry, fruity, sweet, sparkling, etc.)
    """
    id: str
    name: str
    alcoholic: bool
    price: float
    type: str
    subtype: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la bebida a diccionario"""
        result = {
            'id': self.id,
            'name': self.name,
            'alcoholic': self.alcoholic,
            'price': self.price,
            'type': self.type
        }
        if self.subtype:
            result['subtype'] = self.subtype
        return result


@dataclass
class Menu:
    """
    Representa un menú completo.
    
    Un menú se compone de:
    - Un entrante (starter)
    - Un plato principal (main_course)  
    - Un postre (dessert)
    - Una bebida (puede ser un maridaje de vinos)
    
    Atributos:
        id: Identificador único del menú
        starter: Plato entrante
        main_course: Plato principal
        dessert: Postre
        beverage: Bebida o maridaje
        total_price: Precio total por persona
        total_calories: Calorías totales
        dominant_style: Estilo culinario dominante
        cultural_theme: Tema cultural si existe
        explanation: Explicación de por qué funciona este menú
        score: Puntuación de calidad (0-100)
    """
    id: str
    starter: Dish
    main_course: Dish
    dessert: Dish
    beverage: Beverage
    total_price: float = 0.0
    total_calories: int = 0
    dominant_style: Optional[CulinaryStyle] = None
    cultural_theme: Optional[CulturalTradition] = None
    explanation: List[str] = field(default_factory=list)
    score: float = 0.0
    
    def __post_init__(self):
        """Calcula valores derivados después de la inicialización"""
        self.calculate_totals()
    
    def calculate_totals(self):
        """Calcula precio y calorías totales"""
        self.total_price = (self.starter.price + self.main_course.price + 
                          self.dessert.price + self.beverage.price)
        self.total_calories = (self.starter.calories + self.main_course.calories + 
                              self.dessert.calories)
    
    def get_all_ingredients(self) -> Set[str]:
        """Obtiene todos los ingredientes del menú"""
        ingredients = set()
        ingredients.update(self.starter.ingredients)
        ingredients.update(self.main_course.ingredients)
        ingredients.update(self.dessert.ingredients)
        return ingredients
    
    def get_all_diets(self) -> Set[str]:
        """Obtiene las dietas que satisface todo el menú (intersección)"""
        starter_diets = set(self.starter.diets)
        main_diets = set(self.main_course.diets)
        dessert_diets = set(self.dessert.diets)
        return starter_diets & main_diets & dessert_diets
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el menú a diccionario"""
        return {
            'id': self.id,
            'starter': self.starter.to_dict(),
            'main_course': self.main_course.to_dict(),
            'dessert': self.dessert.to_dict(),
            'beverage': self.beverage.to_dict(),
            'total_price': self.total_price,
            'total_calories': self.total_calories,
            'dominant_style': self.dominant_style.value if self.dominant_style else None,
            'cultural_theme': self.cultural_theme.value if self.cultural_theme else None,
            'explanation': self.explanation,
            'score': self.score
        }


@dataclass
class Request:
    """
    Representa una solicitud del cliente.
    
    Contiene el contexto del evento y todas las restricciones/preferencias.
    
    Atributos:
        id: Identificador único de la solicitud
        event_type: Tipo de evento
        season: Temporada del evento
        num_guests: Número de comensales
        price_min: Presupuesto mínimo por persona
        price_max: Presupuesto máximo por persona
        wants_wine: Si desea vino
        wine_per_dish: Si desea maridaje de vinos por plato
        preferred_style: Estilo culinario preferido (opcional)
        cultural_preference: Preferencia cultural (opcional)
        required_diets: Dietas obligatorias
        soft_diets: Dietas preferidas (no obligatorias)
        restricted_ingredients: Ingredientes prohibidos (alergias)
        soft_restricted_ingredients: Ingredientes a evitar si es posible
        chef_style_preference: Preferencia de estilo de chef
        show_explanations: Si mostrar explicaciones detalladas
        options_per_category: Cuántas opciones mostrar por categoría
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    event_type: EventType = EventType.FAMILIAR
    season: Season = Season.ALL
    num_guests: int = 50
    price_min: float = 20.0
    price_max: float = 80.0
    wants_wine: bool = False
    wine_per_dish: bool = False
    preferred_style: Optional[CulinaryStyle] = None
    cultural_preference: Optional[CulturalTradition] = None
    required_diets: List[str] = field(default_factory=list)
    soft_diets: List[str] = field(default_factory=list)
    restricted_ingredients: List[str] = field(default_factory=list)
    soft_restricted_ingredients: List[str] = field(default_factory=list)
    chef_style_preference: Optional[str] = None
    show_explanations: bool = True
    options_per_category: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la solicitud a diccionario"""
        return {
            'id': self.id,
            'event_type': self.event_type.value,
            'season': self.season.value,
            'num_guests': self.num_guests,
            'price_min': self.price_min,
            'price_max': self.price_max,
            'wants_wine': self.wants_wine,
            'wine_per_dish': self.wine_per_dish,
            'preferred_style': self.preferred_style.value if self.preferred_style else None,
            'cultural_preference': self.cultural_preference.value if self.cultural_preference else None,
            'required_diets': self.required_diets,
            'soft_diets': self.soft_diets,
            'restricted_ingredients': self.restricted_ingredients,
            'soft_restricted_ingredients': self.soft_restricted_ingredients,
            'chef_style_preference': self.chef_style_preference,
            'show_explanations': self.show_explanations,
            'options_per_category': self.options_per_category
        }


@dataclass
class Case:
    """
    Representa un caso CBR.
    
    Un caso es la unidad fundamental del sistema CBR, que asocia:
    - Un problema/contexto (Request): La situación del cliente
    - Una solución (Menu): El menú propuesto y aceptado
    - Resultado/feedback: Información sobre éxito del caso
    
    Atributos:
        id: Identificador único del caso
        request: Contexto/problema - la solicitud original
        menu: Solución - el menú propuesto
        success: Si el caso fue exitoso (cliente satisfecho)
        feedback_score: Puntuación de feedback (1-5)
        feedback_comments: Comentarios del feedback
        usage_count: Veces que se ha reutilizado este caso
        created_at: Fecha de creación (timestamp)
        last_used: Última vez que se usó
        adaptation_notes: Notas sobre adaptaciones realizadas
        source: Origen del caso (manual, generated, adapted)
        is_negative: Si es un caso de failure (para evitar repetir errores)
    """
    id: str
    request: Request
    menu: Menu
    success: bool = True
    feedback_score: float = 4.0
    feedback_comments: str = ""
    usage_count: int = 0
    created_at: str = ""
    last_used: str = ""
    adaptation_notes: List[str] = field(default_factory=list)
    source: str = "manual"
    is_negative: bool = False  # True si es un caso de failure (score < 3.0)
    
    def __post_init__(self):
        """Inicializa timestamps si no existen"""
        if not self.created_at:
            from datetime import datetime
            self.created_at = datetime.now().isoformat()
    
    def increment_usage(self):
        """Incrementa el contador de uso"""
        self.usage_count += 1
        from datetime import datetime
        self.last_used = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el caso a diccionario para serialización"""
        return {
            'id': self.id,
            'request': self.request.to_dict(),
            'menu': self.menu.to_dict(),
            'success': self.success,
            'feedback_score': self.feedback_score,
            'feedback_comments': self.feedback_comments,
            'usage_count': self.usage_count,
            'created_at': self.created_at,
            'last_used': self.last_used,
            'adaptation_notes': self.adaptation_notes,
            'source': self.source,
            'is_negative': self.is_negative
        }


@dataclass
class AdaptedMenu:
    """Menú adaptado con información de adaptaciones"""
    menu: Menu
    adaptations: List[str]
    adapted_dishes: List[Dish] = field(default_factory=list)


@dataclass
class ProposedMenu:
    """Menú propuesto como resultado del CBR"""
    menu: Menu
    source_case: Optional[Case] = None
    similarity_score: float = 0.0
    adaptations: List[str] = field(default_factory=list)
    validation_result: Optional[Any] = None
    rank: int = 0


# Constantes útiles para el sistema

STYLES_BY_EVENT = {
    EventType.WEDDING: [CulinaryStyle.SIBARITA, CulinaryStyle.GOURMET, 
                        CulinaryStyle.CLASSIC, CulinaryStyle.FUSION, CulinaryStyle.MODERN],
    EventType.CHRISTENING: [CulinaryStyle.CLASSIC, CulinaryStyle.REGIONAL, CulinaryStyle.MODERN],
    EventType.COMMUNION: [CulinaryStyle.CLASSIC, CulinaryStyle.REGIONAL, 
                          CulinaryStyle.FUSION, CulinaryStyle.SUAVE],
    EventType.FAMILIAR: [CulinaryStyle.REGIONAL, CulinaryStyle.CLASSIC, CulinaryStyle.FUSION],
    EventType.CONGRESS: [CulinaryStyle.CLASSIC, CulinaryStyle.MODERN, 
                         CulinaryStyle.FUSION, CulinaryStyle.GOURMET],
    EventType.CORPORATE: [CulinaryStyle.CLASSIC, CulinaryStyle.MODERN, 
                          CulinaryStyle.FUSION, CulinaryStyle.GOURMET],
}

COMPLEXITY_BY_EVENT = {
    EventType.WEDDING: [Complexity.MEDIUM, Complexity.HIGH],
    EventType.CHRISTENING: [Complexity.LOW, Complexity.MEDIUM],
    EventType.COMMUNION: [Complexity.LOW, Complexity.MEDIUM],
    EventType.FAMILIAR: [Complexity.LOW, Complexity.MEDIUM],
    EventType.CONGRESS: [Complexity.MEDIUM],
    EventType.CORPORATE: [Complexity.MEDIUM],
}

# Estilos de chef reconocibles
CHEF_STYLES = {
    "ferran_adria": {
        "name": "Ferran Adrià",
        "description": "Innovación molecular, texturas sorprendentes",
        "techniques": ["esferificación", "gelificación", "espumas"],
        "styles": [CulinaryStyle.SIBARITA, CulinaryStyle.MODERN]
    },
    "arzak": {
        "name": "Juan Mari Arzak",
        "description": "Cocina de autor vasca, tradición e innovación",
        "techniques": ["pintxos elaborados", "salsas complejas"],
        "styles": [CulinaryStyle.GOURMET, CulinaryStyle.REGIONAL]
    },
    "bocuse": {
        "name": "Paul Bocuse",
        "description": "Elegancia clásica francesa",
        "techniques": ["nouvelle cuisine", "presentación clásica"],
        "styles": [CulinaryStyle.CLASSIC, CulinaryStyle.GOURMET]
    },
    "noma": {
        "name": "René Redzepi (Noma)",
        "description": "Sensibilidad nórdica, productos locales",
        "techniques": ["fermentación", "forrajeo", "minimalismo"],
        "styles": [CulinaryStyle.MODERN, CulinaryStyle.REGIONAL]
    },
    "roca": {
        "name": "Hermanos Roca",
        "description": "Creatividad catalana, postres innovadores",
        "techniques": ["postres de autor", "paisajes comestibles"],
        "styles": [CulinaryStyle.SIBARITA, CulinaryStyle.MODERN]
    }
}
