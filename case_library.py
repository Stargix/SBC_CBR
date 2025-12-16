"""
Biblioteca de casos iniciales para el sistema CBR.

Este módulo proporciona casos base para inicializar el sistema
antes de que aprenda de la experiencia.

Los casos se basan en menús típicos para diferentes tipos de eventos,
siguiendo tradiciones culinarias y estilos de chefs reconocidos.
"""

from datetime import datetime
from typing import List
import json

from .models import (
    Case, Request, Menu, Dish, Beverage,
    EventType, Season, CulinaryStyle, DishType,
    DishCategory, Temperature, Complexity, Flavor
)


def create_sample_dish(
    id: str,
    name: str,
    dish_type: DishType,
    price: float,
    category: DishCategory,
    styles: List[CulinaryStyle],
    seasons: List[Season],
    temperature: Temperature,
    complexity: Complexity,
    calories: int,
    flavors: List[Flavor],
    diets: List[str],
    ingredients: List[str]
) -> Dish:
    """Helper para crear platos de ejemplo"""
    return Dish(
        id=id,
        name=name,
        dish_type=dish_type,
        price=price,
        category=category,
        styles=styles,
        seasons=seasons,
        temperature=temperature,
        complexity=complexity,
        calories=calories,
        max_guests=400,
        flavors=flavors,
        diets=diets,
        ingredients=ingredients,
        compatible_beverages=[]
    )


def create_sample_beverage(
    id: str,
    name: str,
    bev_type: str,
    price: float,
    alcoholic: bool = True
) -> Beverage:
    """Helper para crear bebidas de ejemplo"""
    return Beverage(
        id=id,
        name=name,
        styles=[bev_type],
        price=price,
        alcoholic=alcoholic
    )


def get_initial_cases() -> List[Case]:
    """
    Retorna la biblioteca de casos iniciales.
    
    Incluye casos para todos los tipos de eventos y estilos culinarios.
    
    Returns:
        Lista de casos iniciales
    """
    # Para ahora, retorna una lista vacía
    # La implementación completa requiere ajustar la estructura
    return []
    
    cases = []
    
    # ==========================================
    # CASO 1: Boda elegante estilo gourmet
    # ==========================================
    cases.append(Case(
        id="case-wedding-gourmet-001",
        request=Request(
            event_type=EventType.WEDDING,
            num_guests=150,
            price_max=85.0,
            season=Season.SPRING,
            preferred_style=CulinaryStyle.GOURMET,
            required_diets=[],
        ),
        menu=Menu(
            id="menu-wedding-001",
            dishes=[
                create_sample_dish(
                    id="skinny-tangy-smoked-salmon-layered-salad",
                    name="Skinny Tangy Smoked Salmon Layered Salad",
                    dish_type=DishType.STARTER,
                    price=21.0,
                    category=DishCategory.SALAD,
                    styles=[CulinaryStyle.CLASSIC],
                    seasons=[Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER],
                    temperature=Temperature.COLD,
                    complexity=Complexity.MEDIUM,
                    calories=109,
                    flavors=[Flavor.SOUR, Flavor.SALTY],
                    diets=["pescatarian", "gluten-free"],
                    ingredients=["garlic", "honey", "lemon", "oil", "pepper", "salt"]
                ),
                create_sample_dish(
                    id="moroccan-chicken-tagine",
                    name="Moroccan Chicken Tagine",
                    dish_type=DishType.MAIN_COURSE,
                    price=21.0,
                    category=DishCategory.POULTRY,
                    styles=[CulinaryStyle.CLASSIC],
                    seasons=[Season.SPRING],
                    temperature=Temperature.HOT,
                    complexity=Complexity.HIGH,
                    calories=228,
                    flavors=[Flavor.SALTY, Flavor.UMAMI],
                    diets=["dairy-free", "pork-free"],
                    ingredients=["cinnamon", "cumin", "flour", "garlic", "honey", "oil", "onion", "pepper", "salt"]
                ),
                create_sample_dish(
                    id="cheesecake-ice-cream",
                    name="Cheesecake Ice Cream",
                    dish_type=DishType.DESSERT,
                    price=17.5,
                    category=DishCategory.CREAM,
                    styles=[CulinaryStyle.REGIONAL],
                    seasons=[Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER],
                    temperature=Temperature.COLD,
                    complexity=Complexity.LOW,
                    calories=196,
                    flavors=[Flavor.SWEET, Flavor.FATTY, Flavor.SALTY],
                    diets=["vegetarian", "gluten-free"],
                    ingredients=["cream", "salt", "sugar", "vanilla"]
                )
            ],
            beverages=[
                create_sample_beverage("white-wine-001", "Albariño Rías Baixas", "white-wine", 8.0),
                create_sample_beverage("cava-001", "Cava Brut Nature", "cava", 6.0)
            ],
            total_price=73.5,
            event_type=EventType.WEDDING,
            season=Season.SPRING
        ),
        success=True,
        feedback_score=4.8,
        feedback_comments="Excelente equilibrio y presentación elegante",
        source="expert"
    ))
    
    # ==========================================
    # CASO 2: Evento corporativo moderno
    # ==========================================
    cases.append(Case(
        id="case-corporate-modern-001",
        request=Request(
            event_type=EventType.CORPORATE,
            num_guests=80,
            price_max=45.0,
            season=Season.AUTUMN,
            preferred_style=CulinaryStyle.MODERN,
            required_diets=["vegetariano"],
        ),
        menu=Menu(
            id="menu-corporate-001",
            dishes=[
                create_sample_dish(
                    id="black-bean-and-corn-salsa",
                    name="Black Bean and Corn Salsa",
                    dish_type=DishType.STARTER,
                    price=14.0,
                    category=DishCategory.LEGUME,
                    styles=[CulinaryStyle.FUSION],
                    seasons=[Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER],
                    temperature=Temperature.COLD,
                    complexity=Complexity.LOW,
                    calories=83,
                    flavors=[Flavor.SALTY],
                    diets=["vegan", "vegetarian", "gluten-free"],
                    ingredients=["cilantro", "garlic", "onion", "salt"]
                ),
                create_sample_dish(
                    id="schinkennudeln-vegetarian",
                    name="Pasta Mediterránea Vegetariana",
                    dish_type=DishType.MAIN_COURSE,
                    price=16.0,
                    category=DishCategory.PASTA,
                    styles=[CulinaryStyle.MODERN],
                    seasons=[Season.AUTUMN],
                    temperature=Temperature.HOT,
                    complexity=Complexity.LOW,
                    calories=280,
                    flavors=[Flavor.SALTY, Flavor.UMAMI],
                    diets=["vegetarian"],
                    ingredients=["cheese", "garlic", "oil", "pepper", "salt", "tomato", "basil"]
                ),
                create_sample_dish(
                    id="caramel-pretzel-brownies",
                    name="Caramel Pretzel Brownies",
                    dish_type=DishType.DESSERT,
                    price=12.0,
                    category=DishCategory.CREAM,
                    styles=[CulinaryStyle.MODERN],
                    seasons=[Season.AUTUMN],
                    temperature=Temperature.WARM,
                    complexity=Complexity.LOW,
                    calories=449,
                    flavors=[Flavor.SWEET, Flavor.SALTY],
                    diets=["vegetarian"],
                    ingredients=["vanilla", "chocolate", "sugar"]
                )
            ],
            beverages=[
                create_sample_beverage("soft-drink-001", "Agua mineral con gas", "soft-drink", 2.0, alcohol=False),
                create_sample_beverage("coffee-001", "Café espresso", "coffee", 2.5, alcohol=False)
            ],
            total_price=46.5,
            event_type=EventType.CORPORATE,
            season=Season.AUTUMN
        ),
        success=True,
        feedback_score=4.5,
        feedback_comments="Servicio eficiente y opciones vegetarianas excelentes",
        source="expert"
    ))
    
    # ==========================================
    # CASO 3: Celebración familiar clásica
    # ==========================================
    cases.append(Case(
        id="case-familiar-classic-001",
        request=Request(
            event_type=EventType.FAMILIAR,
            num_guests=40,
            price_max=35.0,
            season=Season.WINTER,
            preferred_style=CulinaryStyle.CLASSIC,
            required_diets=[],
        ),
        menu=Menu(
            id="menu-familiar-001",
            dishes=[
                create_sample_dish(
                    id="carrot-ginger-zinger-soup",
                    name="Carrot-Ginger Zinger Soup",
                    dish_type=DishType.STARTER,
                    price=8.0,
                    category=DishCategory.SOUP,
                    styles=[CulinaryStyle.CLASSIC],
                    seasons=[Season.WINTER],
                    temperature=Temperature.HOT,
                    complexity=Complexity.MEDIUM,
                    calories=76,
                    flavors=[Flavor.SALTY],
                    diets=["vegan", "vegetarian", "gluten-free"],
                    ingredients=["carrots", "garlic", "oil", "pepper", "salt", "ginger"]
                ),
                create_sample_dish(
                    id="jay-s-spicy-slow-cooker-turkey-chili",
                    name="Jay's Spicy Slow Cooker Turkey Chili",
                    dish_type=DishType.MAIN_COURSE,
                    price=18.0,
                    category=DishCategory.SOUP,
                    styles=[CulinaryStyle.REGIONAL],
                    seasons=[Season.WINTER],
                    temperature=Temperature.HOT,
                    complexity=Complexity.HIGH,
                    calories=257,
                    flavors=[Flavor.SALTY, Flavor.SOUR, Flavor.UMAMI],
                    diets=["dairy-free", "pork-free"],
                    ingredients=["pepper", "salt", "turkey", "beans", "tomato"]
                ),
                create_sample_dish(
                    id="classic-apple-pie",
                    name="Classic Apple Pie",
                    dish_type=DishType.DESSERT,
                    price=8.0,
                    category=DishCategory.FRUIT,
                    styles=[CulinaryStyle.CLASSIC],
                    seasons=[Season.WINTER, Season.AUTUMN],
                    temperature=Temperature.WARM,
                    complexity=Complexity.MEDIUM,
                    calories=320,
                    flavors=[Flavor.SWEET],
                    diets=["vegetarian"],
                    ingredients=["apple", "sugar", "cinnamon", "flour", "butter"]
                )
            ],
            beverages=[
                create_sample_beverage("red-wine-002", "Rioja Crianza", "red-wine", 5.0),
                create_sample_beverage("herbal-tea-001", "Infusión de manzanilla", "herbal-tea", 2.0, alcohol=False)
            ],
            total_price=41.0,
            event_type=EventType.FAMILIAR,
            season=Season.WINTER
        ),
        success=True,
        feedback_score=4.7,
        feedback_comments="Muy reconfortante, como cocina de casa",
        source="expert"
    ))
    
    # ==========================================
    # CASO 4: Congreso/Conferencia eficiente
    # ==========================================
    cases.append(Case(
        id="case-congress-fusion-001",
        request=Request(
            event_type=EventType.CONGRESS,
            num_guests=200,
            price_max=40.0,
            season=Season.SUMMER,
            preferred_style=CulinaryStyle.FUSION,
            required_diets=["sin gluten"],
        ),
        menu=Menu(
            id="menu-congress-001",
            dishes=[
                create_sample_dish(
                    id="asian-salad-bowl",
                    name="Asian Fusion Salad Bowl",
                    dish_type=DishType.STARTER,
                    price=12.0,
                    category=DishCategory.SALAD,
                    styles=[CulinaryStyle.FUSION],
                    seasons=[Season.SUMMER],
                    temperature=Temperature.COLD,
                    complexity=Complexity.LOW,
                    calories=150,
                    flavors=[Flavor.SALTY, Flavor.SOUR],
                    diets=["vegan", "gluten-free"],
                    ingredients=["cabbage", "carrots", "ginger", "sesame", "lime"]
                ),
                create_sample_dish(
                    id="teriyaki-chicken-rice",
                    name="Teriyaki Chicken with Jasmine Rice",
                    dish_type=DishType.MAIN_COURSE,
                    price=18.0,
                    category=DishCategory.POULTRY,
                    styles=[CulinaryStyle.FUSION],
                    seasons=[Season.SUMMER],
                    temperature=Temperature.HOT,
                    complexity=Complexity.MEDIUM,
                    calories=380,
                    flavors=[Flavor.SWEET, Flavor.SALTY, Flavor.UMAMI],
                    diets=["dairy-free", "gluten-free"],
                    ingredients=["chicken", "rice", "soy-sauce", "ginger", "garlic", "honey"]
                ),
                create_sample_dish(
                    id="mango-coconut-panna-cotta",
                    name="Mango Coconut Panna Cotta",
                    dish_type=DishType.DESSERT,
                    price=9.0,
                    category=DishCategory.CREAM,
                    styles=[CulinaryStyle.FUSION],
                    seasons=[Season.SUMMER],
                    temperature=Temperature.COLD,
                    complexity=Complexity.MEDIUM,
                    calories=220,
                    flavors=[Flavor.SWEET, Flavor.FATTY],
                    diets=["vegetarian", "gluten-free"],
                    ingredients=["mango", "coconut-milk", "sugar", "gelatin"]
                )
            ],
            beverages=[
                create_sample_beverage("green-tea-001", "Té verde frío", "green-tea", 2.5, alcohol=False),
                create_sample_beverage("white-wine-002", "Verdejo", "white-wine", 4.5)
            ],
            total_price=46.0,
            event_type=EventType.CONGRESS,
            season=Season.SUMMER
        ),
        success=True,
        feedback_score=4.3,
        feedback_comments="Excelente logística y sabores interesantes",
        source="expert"
    ))
    
    # ==========================================
    # CASO 5: Bautizo tradicional
    # ==========================================
    cases.append(Case(
        id="case-christening-regional-001",
        request=Request(
            event_type=EventType.CHRISTENING,
            num_guests=50,
            price_max=55.0,
            season=Season.SPRING,
            preferred_style=CulinaryStyle.REGIONAL,
            required_diets=[],
        ),
        menu=Menu(
            id="menu-christening-001",
            dishes=[
                create_sample_dish(
                    id="esqueixada-de-bacalla",
                    name="Esqueixada de Bacallà",
                    dish_type=DishType.STARTER,
                    price=14.0,
                    category=DishCategory.FISH,
                    styles=[CulinaryStyle.REGIONAL],
                    seasons=[Season.SPRING, Season.SUMMER],
                    temperature=Temperature.COLD,
                    complexity=Complexity.MEDIUM,
                    calories=180,
                    flavors=[Flavor.SALTY, Flavor.SOUR],
                    diets=["dairy-free"],
                    ingredients=["cod", "tomato", "onion", "olive-oil", "vinegar"]
                ),
                create_sample_dish(
                    id="pollastre-amb-samfaina",
                    name="Pollastre amb Samfaina",
                    dish_type=DishType.MAIN_COURSE,
                    price=22.0,
                    category=DishCategory.POULTRY,
                    styles=[CulinaryStyle.REGIONAL],
                    seasons=[Season.SPRING, Season.SUMMER],
                    temperature=Temperature.HOT,
                    complexity=Complexity.HIGH,
                    calories=350,
                    flavors=[Flavor.SALTY, Flavor.UMAMI],
                    diets=["dairy-free", "gluten-free"],
                    ingredients=["chicken", "eggplant", "zucchini", "pepper", "tomato", "garlic"]
                ),
                create_sample_dish(
                    id="crema-catalana",
                    name="Crema Catalana",
                    dish_type=DishType.DESSERT,
                    price=10.0,
                    category=DishCategory.CREAM,
                    styles=[CulinaryStyle.REGIONAL],
                    seasons=[Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER],
                    temperature=Temperature.COLD,
                    complexity=Complexity.MEDIUM,
                    calories=280,
                    flavors=[Flavor.SWEET],
                    diets=["vegetarian", "gluten-free"],
                    ingredients=["egg", "milk", "sugar", "cinnamon", "lemon"]
                )
            ],
            beverages=[
                create_sample_beverage("cava-002", "Cava Brut Reserva", "cava", 7.0),
                create_sample_beverage("soft-drink-002", "Zumo de naranja natural", "juice", 3.0, alcohol=False)
            ],
            total_price=56.0,
            event_type=EventType.CHRISTENING,
            season=Season.SPRING
        ),
        success=True,
        feedback_score=4.9,
        feedback_comments="Auténtica cocina catalana, los invitados quedaron encantados",
        source="expert"
    ))
    
    # ==========================================
    # CASO 6: Comunión sibarita
    # ==========================================
    cases.append(Case(
        id="case-communion-sibarita-001",
        request=Request(
            event_type=EventType.COMMUNION,
            num_guests=60,
            price_max=65.0,
            season=Season.SPRING,
            preferred_style=CulinaryStyle.SIBARITA,
            required_diets=[],
        ),
        menu=Menu(
            id="menu-communion-001",
            dishes=[
                create_sample_dish(
                    id="gazpacho-foam",
                    name="Espuma de Gazpacho con Tartar de Langostinos",
                    dish_type=DishType.STARTER,
                    price=18.0,
                    category=DishCategory.SOUP,
                    styles=[CulinaryStyle.SIBARITA],
                    seasons=[Season.SPRING, Season.SUMMER],
                    temperature=Temperature.COLD,
                    complexity=Complexity.HIGH,
                    calories=120,
                    flavors=[Flavor.SOUR, Flavor.SALTY],
                    diets=["gluten-free"],
                    ingredients=["tomato", "cucumber", "shrimp", "olive-oil", "garlic"]
                ),
                create_sample_dish(
                    id="sous-vide-beef",
                    name="Solomillo de Ternera Sous-Vide con Reducción de Pedro Ximénez",
                    dish_type=DishType.MAIN_COURSE,
                    price=32.0,
                    category=DishCategory.MEAT,
                    styles=[CulinaryStyle.SIBARITA],
                    seasons=[Season.SPRING],
                    temperature=Temperature.HOT,
                    complexity=Complexity.HIGH,
                    calories=420,
                    flavors=[Flavor.UMAMI, Flavor.SWEET, Flavor.SALTY],
                    diets=["gluten-free", "dairy-free"],
                    ingredients=["beef", "wine", "butter", "herbs", "garlic"]
                ),
                create_sample_dish(
                    id="chocolate-sphere",
                    name="Esfera de Chocolate con Corazón Líquido",
                    dish_type=DishType.DESSERT,
                    price=14.0,
                    category=DishCategory.CREAM,
                    styles=[CulinaryStyle.SIBARITA],
                    seasons=[Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER],
                    temperature=Temperature.WARM,
                    complexity=Complexity.HIGH,
                    calories=380,
                    flavors=[Flavor.SWEET, Flavor.BITTER],
                    diets=["vegetarian"],
                    ingredients=["chocolate", "cream", "sugar", "vanilla"]
                )
            ],
            beverages=[
                create_sample_beverage("red-wine-003", "Ribera del Duero Reserva", "red-wine", 9.0),
                create_sample_beverage("soft-drink-003", "Refresco artesanal de frutas", "artisan-soda", 4.0, alcohol=False)
            ],
            total_price=77.0,
            event_type=EventType.COMMUNION,
            season=Season.SPRING
        ),
        success=True,
        feedback_score=4.6,
        feedback_comments="Presentación impresionante, técnicas innovadoras",
        source="expert"
    ))
    
    # ==========================================
    # CASO 7: Boda veraniega mediterránea
    # ==========================================
    cases.append(Case(
        id="case-wedding-regional-002",
        request=Request(
            event_type=EventType.WEDDING,
            num_guests=120,
            price_max=70.0,
            season=Season.SUMMER,
            preferred_style=CulinaryStyle.REGIONAL,
            required_diets=["sin mariscos"],
        ),
        menu=Menu(
            id="menu-wedding-002",
            dishes=[
                create_sample_dish(
                    id="caprese-tower",
                    name="Torre Caprese con Burrata y Tomate del Tiempo",
                    dish_type=DishType.STARTER,
                    price=16.0,
                    category=DishCategory.SALAD,
                    styles=[CulinaryStyle.REGIONAL],
                    seasons=[Season.SUMMER],
                    temperature=Temperature.COLD,
                    complexity=Complexity.LOW,
                    calories=220,
                    flavors=[Flavor.FATTY, Flavor.SALTY],
                    diets=["vegetarian", "gluten-free"],
                    ingredients=["tomato", "burrata", "basil", "olive-oil", "balsamic"]
                ),
                create_sample_dish(
                    id="grilled-sea-bass",
                    name="Lubina a la Brasa con Verduras de Temporada",
                    dish_type=DishType.MAIN_COURSE,
                    price=28.0,
                    category=DishCategory.FISH,
                    styles=[CulinaryStyle.REGIONAL],
                    seasons=[Season.SUMMER],
                    temperature=Temperature.HOT,
                    complexity=Complexity.MEDIUM,
                    calories=280,
                    flavors=[Flavor.SALTY, Flavor.UMAMI],
                    diets=["dairy-free", "gluten-free"],
                    ingredients=["sea-bass", "zucchini", "pepper", "olive-oil", "lemon", "herbs"]
                ),
                create_sample_dish(
                    id="tarta-santiago",
                    name="Tarta de Santiago con Helado de Turrón",
                    dish_type=DishType.DESSERT,
                    price=12.0,
                    category=DishCategory.CAKE,
                    styles=[CulinaryStyle.REGIONAL],
                    seasons=[Season.SUMMER],
                    temperature=Temperature.WARM,
                    complexity=Complexity.MEDIUM,
                    calories=350,
                    flavors=[Flavor.SWEET],
                    diets=["gluten-free"],
                    ingredients=["almonds", "egg", "sugar", "lemon"]
                )
            ],
            beverages=[
                create_sample_beverage("white-wine-003", "Albariño D.O. Rías Baixas", "white-wine", 8.0),
                create_sample_beverage("rosé-001", "Rosado de Navarra", "rosé-wine", 6.0)
            ],
            total_price=70.0,
            event_type=EventType.WEDDING,
            season=Season.SUMMER
        ),
        success=True,
        feedback_score=4.8,
        feedback_comments="Perfecto para el verano, sabores frescos y auténticos",
        source="expert"
    ))
    
    # ==========================================
    # CASO 8: Evento corporativo vegano
    # ==========================================
    cases.append(Case(
        id="case-corporate-modern-002",
        request=Request(
            event_type=EventType.CORPORATE,
            num_guests=100,
            price_max=50.0,
            season=Season.AUTUMN,
            preferred_style=CulinaryStyle.MODERN,
            required_diets=["vegano"],
        ),
        menu=Menu(
            id="menu-corporate-002",
            dishes=[
                create_sample_dish(
                    id="pumpkin-soup-vegan",
                    name="Crema de Calabaza con Leche de Coco y Semillas",
                    dish_type=DishType.STARTER,
                    price=10.0,
                    category=DishCategory.SOUP,
                    styles=[CulinaryStyle.MODERN],
                    seasons=[Season.AUTUMN, Season.WINTER],
                    temperature=Temperature.HOT,
                    complexity=Complexity.LOW,
                    calories=150,
                    flavors=[Flavor.SWEET, Flavor.SALTY],
                    diets=["vegan", "gluten-free"],
                    ingredients=["pumpkin", "coconut-milk", "seeds", "spices"]
                ),
                create_sample_dish(
                    id="buddha-bowl",
                    name="Buddha Bowl con Quinoa y Verduras Asadas",
                    dish_type=DishType.MAIN_COURSE,
                    price=22.0,
                    category=DishCategory.LEGUME,
                    styles=[CulinaryStyle.MODERN],
                    seasons=[Season.AUTUMN],
                    temperature=Temperature.WARM,
                    complexity=Complexity.MEDIUM,
                    calories=380,
                    flavors=[Flavor.SALTY, Flavor.UMAMI],
                    diets=["vegan", "gluten-free"],
                    ingredients=["quinoa", "chickpeas", "sweet-potato", "kale", "tahini"]
                ),
                create_sample_dish(
                    id="avocado-chocolate-mousse",
                    name="Mousse de Chocolate y Aguacate",
                    dish_type=DishType.DESSERT,
                    price=11.0,
                    category=DishCategory.CREAM,
                    styles=[CulinaryStyle.MODERN],
                    seasons=[Season.AUTUMN],
                    temperature=Temperature.COLD,
                    complexity=Complexity.LOW,
                    calories=280,
                    flavors=[Flavor.SWEET, Flavor.BITTER],
                    diets=["vegan", "gluten-free"],
                    ingredients=["avocado", "chocolate", "coconut-cream", "maple-syrup"]
                )
            ],
            beverages=[
                create_sample_beverage("kombucha-001", "Kombucha artesanal", "kombucha", 4.0, alcohol=False),
                create_sample_beverage("natural-wine-001", "Vino natural ecológico", "natural-wine", 7.0)
            ],
            total_price=54.0,
            event_type=EventType.CORPORATE,
            season=Season.AUTUMN
        ),
        success=True,
        feedback_score=4.4,
        feedback_comments="Excelente propuesta vegana, sorprendió a todos",
        source="expert"
    ))
    
    return cases


def export_cases_to_json(cases: List[Case], filepath: str) -> None:
    """
    Exporta casos a archivo JSON.
    
    Args:
        cases: Lista de casos a exportar
        filepath: Ruta del archivo de salida
    """
    cases_data = [case.to_dict() for case in cases]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cases_data, f, ensure_ascii=False, indent=2)


def load_cases_from_json(filepath: str) -> List[Case]:
    """
    Carga casos desde archivo JSON.
    
    Args:
        filepath: Ruta del archivo JSON
        
    Returns:
        Lista de casos
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        cases_data = json.load(f)
    
    return [Case.from_dict(data) for data in cases_data]


# Ejecutar para generar archivo inicial
if __name__ == "__main__":
    cases = get_initial_cases()
