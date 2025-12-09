"""
Base de casos para el sistema CBR de menús.

Este módulo implementa la base de conocimiento del sistema CBR:
- Almacenamiento y gestión de casos
- Indexación para recuperación eficiente
- Persistencia de la base de casos
- Carga de datos iniciales basados en el sistema CLIPS

La base de casos se estructura por tipo de evento y rango de precios
para facilitar la recuperación de casos similares.
"""

import json
import os
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import random

from .models import (
    Case, Menu, Dish, Beverage, Request,
    EventType, Season, DishType, DishCategory,
    CulinaryStyle, Temperature, Complexity, Flavor,
    CulturalTradition, CHEF_STYLES
)


class CaseBase:
    """
    Base de casos del sistema CBR.
    
    Gestiona el almacenamiento, recuperación y persistencia de casos.
    Los casos se indexan por tipo de evento y rango de precios para
    facilitar la recuperación eficiente.
    
    Atributos:
        cases: Lista de todos los casos
        dishes: Diccionario de platos disponibles
        beverages: Diccionario de bebidas disponibles
        index_by_event: Índice de casos por tipo de evento
        index_by_price_range: Índice por rango de precios
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Inicializa la base de casos.
        
        Args:
            data_path: Ruta al archivo de persistencia
        """
        self.cases: List[Case] = []
        self.dishes: Dict[str, Dish] = {}
        self.beverages: Dict[str, Beverage] = {}
        
        # Índices para recuperación eficiente
        self.index_by_event: Dict[EventType, List[Case]] = {e: [] for e in EventType}
        self.index_by_price_range: Dict[str, List[Case]] = {
            "low": [],      # 0-30€
            "medium": [],   # 30-60€
            "high": [],     # 60-100€
            "premium": []   # 100€+
        }
        self.index_by_season: Dict[Season, List[Case]] = {s: [] for s in Season}
        self.index_by_style: Dict[CulinaryStyle, List[Case]] = {s: [] for s in CulinaryStyle}
        
        self.data_path = data_path
        
        # Cargar datos iniciales
        self._initialize_base_data()
        
        # Cargar casos persistidos si existen
        if data_path and os.path.exists(data_path):
            self.load_from_file(data_path)
    
    def _initialize_base_data(self):
        """Inicializa los datos base del sistema (platos y bebidas)"""
        self._load_sample_dishes()
        self._load_sample_beverages()
        self._generate_initial_cases()
    
    def _load_sample_dishes(self):
        """Carga platos de ejemplo basados en los datos de CLIPS"""
        
        # ENTRANTES (Starters)
        starters = [
            Dish(
                id="skinny-tangy-smoked-salmon-salad",
                name="Skinny Tangy Smoked Salmon Layered Salad",
                dish_type=DishType.STARTER,
                price=21.0,
                category=DishCategory.SALAD,
                styles=[CulinaryStyle.CLASSIC],
                seasons=[Season.ALL],
                temperature=Temperature.COLD,
                complexity=Complexity.MEDIUM,
                calories=109,
                max_guests=400,
                flavors=[Flavor.SOUR, Flavor.SALTY],
                diets=["pescatarian", "gluten-free", "wheat-free", "egg-free"],
                ingredients=["garlic", "honey", "lemon", "oil", "pepper", "salt", "salmon"],
                compatible_beverages=["white-wine", "herbal-tea"],
                cultural_traditions=[CulturalTradition.NORDIC]
            ),
            Dish(
                id="carrot-ginger-soup",
                name="Carrot-Ginger Zinger Soup",
                dish_type=DishType.STARTER,
                price=21.0,
                category=DishCategory.SOUP,
                styles=[CulinaryStyle.CLASSICAL],
                seasons=[Season.WINTER],
                temperature=Temperature.HOT,
                complexity=Complexity.MEDIUM,
                calories=76,
                max_guests=400,
                flavors=[Flavor.SALTY],
                diets=["vegan", "vegetarian", "pescatarian", "dairy-free", "gluten-free"],
                ingredients=["carrots", "garlic", "oil", "pepper", "salt", "ginger"],
                compatible_beverages=["soft-drink", "white-wine"],
                cultural_traditions=[CulturalTradition.FRENCH]
            ),
            Dish(
                id="black-bean-corn-salsa",
                name="Black Bean and Corn Salsa",
                dish_type=DishType.STARTER,
                price=14.0,
                category=DishCategory.LEGUME,
                styles=[CulinaryStyle.FUSION],
                seasons=[Season.ALL],
                temperature=Temperature.COLD,
                complexity=Complexity.LOW,
                calories=83,
                max_guests=400,
                flavors=[Flavor.SALTY],
                diets=["vegan", "vegetarian", "pescatarian", "dairy-free", "gluten-free"],
                ingredients=["cilantro", "garlic", "onion", "salt", "black_beans", "corn"],
                compatible_beverages=["soft-drink", "white-wine"],
                cultural_traditions=[CulturalTradition.MEXICAN]
            ),
            Dish(
                id="red-bean-sausage-soup",
                name="Red Bean 'N' Sausage Soup",
                dish_type=DishType.STARTER,
                price=28.0,
                category=DishCategory.SOUP,
                styles=[CulinaryStyle.CLASSICAL],
                seasons=[Season.AUTUMN],
                temperature=Temperature.HOT,
                complexity=Complexity.HIGH,
                calories=251,
                max_guests=400,
                flavors=[Flavor.SWEET, Flavor.SALTY, Flavor.FATTY],
                diets=["dairy-free", "gluten-free", "wheat-free", "egg-free"],
                ingredients=["onion", "pepper", "salt", "sugar", "beans", "sausage"],
                compatible_beverages=["red-wine", "herbal-tea"]
            ),
            Dish(
                id="mediterranean-bruschetta",
                name="Mediterranean Bruschetta",
                dish_type=DishType.STARTER,
                price=16.0,
                category=DishCategory.TAPAS,
                styles=[CulinaryStyle.REGIONAL, CulinaryStyle.CLASSIC],
                seasons=[Season.ALL],
                temperature=Temperature.WARM,
                complexity=Complexity.LOW,
                calories=150,
                max_guests=400,
                flavors=[Flavor.SALTY, Flavor.UMAMI],
                diets=["vegetarian", "vegan"],
                ingredients=["tomato", "basil", "garlic", "olive_oil", "bread"],
                compatible_beverages=["white-wine", "soft-drink"],
                cultural_traditions=[CulturalTradition.ITALIAN, CulturalTradition.MEDITERRANEAN]
            ),
            Dish(
                id="gazpacho-andaluz",
                name="Gazpacho Andaluz",
                dish_type=DishType.STARTER,
                price=15.0,
                category=DishCategory.SOUP,
                styles=[CulinaryStyle.REGIONAL],
                seasons=[Season.SUMMER],
                temperature=Temperature.COLD,
                complexity=Complexity.LOW,
                calories=95,
                max_guests=400,
                flavors=[Flavor.SOUR, Flavor.SALTY],
                diets=["vegan", "vegetarian", "gluten-free"],
                ingredients=["tomato", "cucumber", "pepper", "garlic", "olive_oil", "vinegar"],
                compatible_beverages=["white-wine", "soft-drink"],
                cultural_traditions=[CulturalTradition.SPANISH, CulturalTradition.MEDITERRANEAN]
            ),
            Dish(
                id="foie-gras-terrine",
                name="Foie Gras Terrine with Fig Compote",
                dish_type=DishType.STARTER,
                price=45.0,
                category=DishCategory.MEAT,
                styles=[CulinaryStyle.GOURMET, CulinaryStyle.SIBARITA],
                seasons=[Season.AUTUMN, Season.WINTER],
                temperature=Temperature.COLD,
                complexity=Complexity.HIGH,
                calories=320,
                max_guests=200,
                flavors=[Flavor.FATTY, Flavor.SWEET, Flavor.UMAMI],
                diets=["gluten-free"],
                ingredients=["foie", "fig", "cognac", "spices"],
                compatible_beverages=["sweet-wine", "sparkling-wine"],
                cultural_traditions=[CulturalTradition.FRENCH],
                chef_style="bocuse"
            ),
            Dish(
                id="ceviche-peruano",
                name="Ceviche Peruano",
                dish_type=DishType.STARTER,
                price=24.0,
                category=DishCategory.FISH,
                styles=[CulinaryStyle.FUSION, CulinaryStyle.MODERN],
                seasons=[Season.SUMMER, Season.SPRING],
                temperature=Temperature.COLD,
                complexity=Complexity.MEDIUM,
                calories=120,
                max_guests=300,
                flavors=[Flavor.SOUR, Flavor.SPICY, Flavor.SALTY],
                diets=["pescatarian", "gluten-free", "dairy-free"],
                ingredients=["white_fish", "lime", "onion", "cilantro", "chili"],
                compatible_beverages=["white-wine", "sparkling-wine"],
                cultural_traditions=[CulturalTradition.MEDITERRANEAN]
            ),
        ]
        
        # PLATOS PRINCIPALES (Main Courses)
        mains = [
            Dish(
                id="schinkennudeln-ham-cheese-pasta",
                name="Schinkennudeln (Ham & Cheese Pasta)",
                dish_type=DishType.MAIN_COURSE,
                price=14.0,
                category=DishCategory.PASTA,
                styles=[CulinaryStyle.SIBARITA],
                seasons=[Season.SPRING, Season.SUMMER],
                temperature=Temperature.HOT,
                complexity=Complexity.LOW,
                calories=306,
                max_guests=400,
                flavors=[Flavor.SALTY, Flavor.UMAMI, Flavor.FATTY],
                diets=["egg-free", "peanut-free", "tree-nut-free"],
                ingredients=["cheese", "garlic", "oil", "pepper", "salt", "water", "ham", "pasta"],
                compatible_beverages=["red-wine", "white-wine"]
            ),
            Dish(
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
                max_guests=400,
                flavors=[Flavor.SALTY, Flavor.UMAMI],
                diets=["dairy-free", "egg-free", "peanut-free"],
                ingredients=["cinnamon", "cumin", "flour", "garlic", "honey", "oil", "onion", "pepper", "salt", "chicken"],
                compatible_beverages=["red-wine", "white-wine"],
                cultural_traditions=[CulturalTradition.MOROCCAN]
            ),
            Dish(
                id="pork-stew-green-salsa",
                name="Pork Stew in Green Salsa",
                dish_type=DishType.MAIN_COURSE,
                price=21.0,
                category=DishCategory.MEAT,
                styles=[CulinaryStyle.REGIONAL],
                seasons=[Season.WINTER],
                temperature=Temperature.HOT,
                complexity=Complexity.HIGH,
                calories=267,
                max_guests=400,
                flavors=[Flavor.SALTY, Flavor.UMAMI, Flavor.FATTY],
                diets=["egg-free", "peanut-free", "tree-nut-free"],
                ingredients=["cilantro", "cream", "cumin", "flour", "garlic", "oil", "onion", "pepper", "salt", "pork"],
                compatible_beverages=["red-wine", "white-wine"],
                cultural_traditions=[CulturalTradition.MEXICAN]
            ),
            Dish(
                id="whole-chicken-cabbage",
                name="Whole Chicken And Cabbage Braised",
                dish_type=DishType.MAIN_COURSE,
                price=28.0,
                category=DishCategory.POULTRY,
                styles=[CulinaryStyle.CLASSIC],
                seasons=[Season.WINTER],
                temperature=Temperature.HOT,
                complexity=Complexity.LOW,
                calories=322,
                max_guests=400,
                flavors=[Flavor.SALTY, Flavor.UMAMI],
                diets=["gluten-free", "dairy-free"],
                ingredients=["chicken", "cabbage", "onion", "butter", "herbs"],
                compatible_beverages=["red-wine", "white-wine"]
            ),
            Dish(
                id="grilled-sea-bass",
                name="Grilled Sea Bass with Herbs",
                dish_type=DishType.MAIN_COURSE,
                price=32.0,
                category=DishCategory.FISH,
                styles=[CulinaryStyle.CLASSIC, CulinaryStyle.GOURMET],
                seasons=[Season.ALL],
                temperature=Temperature.HOT,
                complexity=Complexity.MEDIUM,
                calories=280,
                max_guests=300,
                flavors=[Flavor.SALTY, Flavor.UMAMI],
                diets=["pescatarian", "gluten-free", "dairy-free"],
                ingredients=["sea_bass", "lemon", "herbs", "olive_oil", "garlic"],
                compatible_beverages=["white-wine"],
                cultural_traditions=[CulturalTradition.MEDITERRANEAN]
            ),
            Dish(
                id="beef-wellington",
                name="Beef Wellington",
                dish_type=DishType.MAIN_COURSE,
                price=55.0,
                category=DishCategory.MEAT,
                styles=[CulinaryStyle.GOURMET, CulinaryStyle.SIBARITA],
                seasons=[Season.AUTUMN, Season.WINTER],
                temperature=Temperature.HOT,
                complexity=Complexity.HIGH,
                calories=580,
                max_guests=150,
                flavors=[Flavor.UMAMI, Flavor.FATTY, Flavor.SALTY],
                diets=["egg-free"],
                ingredients=["beef", "mushrooms", "pate", "puff_pastry", "herbs"],
                compatible_beverages=["red-wine"],
                cultural_traditions=[CulturalTradition.FRENCH],
                chef_style="bocuse"
            ),
            Dish(
                id="risotto-funghi",
                name="Risotto ai Funghi Porcini",
                dish_type=DishType.MAIN_COURSE,
                price=26.0,
                category=DishCategory.RICE,
                styles=[CulinaryStyle.CLASSIC, CulinaryStyle.REGIONAL],
                seasons=[Season.AUTUMN, Season.WINTER],
                temperature=Temperature.HOT,
                complexity=Complexity.MEDIUM,
                calories=380,
                max_guests=300,
                flavors=[Flavor.UMAMI, Flavor.FATTY],
                diets=["vegetarian", "gluten-free"],
                ingredients=["arborio_rice", "porcini", "parmesan", "butter", "onion", "wine"],
                compatible_beverages=["white-wine", "red-wine"],
                cultural_traditions=[CulturalTradition.ITALIAN]
            ),
            Dish(
                id="bacalao-pil-pil",
                name="Bacalao al Pil-Pil",
                dish_type=DishType.MAIN_COURSE,
                price=38.0,
                category=DishCategory.FISH,
                styles=[CulinaryStyle.REGIONAL, CulinaryStyle.GOURMET],
                seasons=[Season.ALL],
                temperature=Temperature.HOT,
                complexity=Complexity.HIGH,
                calories=320,
                max_guests=200,
                flavors=[Flavor.SALTY, Flavor.UMAMI, Flavor.FATTY],
                diets=["pescatarian", "gluten-free", "dairy-free"],
                ingredients=["cod", "olive_oil", "garlic", "chili"],
                compatible_beverages=["white-wine"],
                cultural_traditions=[CulturalTradition.BASQUE],
                chef_style="arzak"
            ),
            Dish(
                id="cordero-asado",
                name="Cordero Asado con Hierbas",
                dish_type=DishType.MAIN_COURSE,
                price=42.0,
                category=DishCategory.MEAT,
                styles=[CulinaryStyle.REGIONAL, CulinaryStyle.CLASSIC],
                seasons=[Season.SPRING, Season.WINTER],
                temperature=Temperature.HOT,
                complexity=Complexity.MEDIUM,
                calories=450,
                max_guests=250,
                flavors=[Flavor.UMAMI, Flavor.FATTY, Flavor.SALTY],
                diets=["gluten-free", "dairy-free"],
                ingredients=["lamb", "rosemary", "thyme", "garlic", "potatoes"],
                compatible_beverages=["red-wine"],
                cultural_traditions=[CulturalTradition.SPANISH, CulturalTradition.MEDITERRANEAN]
            ),
        ]
        
        # POSTRES (Desserts)
        desserts = [
            Dish(
                id="caramel-pretzel-brownies",
                name="Caramel Pretzel Brownies",
                dish_type=DishType.DESSERT,
                price=42.0,
                category=DishCategory.PASTRY,
                styles=[CulinaryStyle.MODERN],
                seasons=[Season.AUTUMN],
                temperature=Temperature.WARM,
                complexity=Complexity.LOW,
                calories=449,
                max_guests=400,
                flavors=[Flavor.SWEET, Flavor.SALTY],
                diets=["vegetarian", "pescatarian", "egg-free"],
                ingredients=["vanilla", "caramel", "chocolate", "pretzel"],
                compatible_beverages=["red-wine", "white-wine", "sweet-wine"]
            ),
            Dish(
                id="cheesecake-ice-cream",
                name="Cheesecake Ice Cream",
                dish_type=DishType.DESSERT,
                price=17.5,
                category=DishCategory.ICE_CREAM,
                styles=[CulinaryStyle.REGIONAL],
                seasons=[Season.ALL],
                temperature=Temperature.COLD,
                complexity=Complexity.LOW,
                calories=196,
                max_guests=400,
                flavors=[Flavor.SWEET, Flavor.FATTY, Flavor.SALTY],
                diets=["vegetarian", "pescatarian", "gluten-free", "egg-free"],
                ingredients=["cream", "salt", "sugar", "vanilla", "cheese"],
                compatible_beverages=["sweet-wine", "herbal-tea"]
            ),
            Dish(
                id="ice-cream-marshmallow-bars",
                name="Ice Cream Marshmallow Cereal Bars",
                dish_type=DishType.DESSERT,
                price=31.5,
                category=DishCategory.ICE_CREAM,
                styles=[CulinaryStyle.FUSION],
                seasons=[Season.SUMMER],
                temperature=Temperature.COLD,
                complexity=Complexity.LOW,
                calories=186,
                max_guests=400,
                flavors=[Flavor.SWEET],
                diets=["vegetarian", "egg-free"],
                ingredients=["butter", "marshmallow", "cereal"],
                compatible_beverages=["red-wine", "white-wine", "soft-drink"]
            ),
            Dish(
                id="tiramisu-classic",
                name="Tiramisu Classic",
                dish_type=DishType.DESSERT,
                price=18.0,
                category=DishCategory.PASTRY,
                styles=[CulinaryStyle.CLASSIC, CulinaryStyle.REGIONAL],
                seasons=[Season.ALL],
                temperature=Temperature.COLD,
                complexity=Complexity.MEDIUM,
                calories=280,
                max_guests=400,
                flavors=[Flavor.SWEET, Flavor.BITTER],
                diets=["vegetarian"],
                ingredients=["mascarpone", "coffee", "cocoa", "savoiardi", "eggs"],
                compatible_beverages=["sweet-wine", "coffee"],
                cultural_traditions=[CulturalTradition.ITALIAN]
            ),
            Dish(
                id="crema-catalana",
                name="Crema Catalana",
                dish_type=DishType.DESSERT,
                price=14.0,
                category=DishCategory.CREAM,
                styles=[CulinaryStyle.REGIONAL, CulinaryStyle.CLASSIC],
                seasons=[Season.ALL],
                temperature=Temperature.COLD,
                complexity=Complexity.MEDIUM,
                calories=220,
                max_guests=400,
                flavors=[Flavor.SWEET, Flavor.FATTY],
                diets=["vegetarian", "gluten-free"],
                ingredients=["cream", "eggs", "sugar", "cinnamon", "lemon"],
                compatible_beverages=["sweet-wine"],
                cultural_traditions=[CulturalTradition.CATALAN]
            ),
            Dish(
                id="tarta-santiago",
                name="Tarta de Santiago",
                dish_type=DishType.DESSERT,
                price=16.0,
                category=DishCategory.PASTRY,
                styles=[CulinaryStyle.REGIONAL],
                seasons=[Season.ALL],
                temperature=Temperature.WARM,
                complexity=Complexity.LOW,
                calories=350,
                max_guests=400,
                flavors=[Flavor.SWEET],
                diets=["vegetarian", "gluten-free"],
                ingredients=["almonds", "eggs", "sugar", "lemon"],
                compatible_beverages=["sweet-wine", "herbal-tea"],
                cultural_traditions=[CulturalTradition.GALICIAN]
            ),
            Dish(
                id="chocolate-fondant",
                name="Chocolate Fondant with Vanilla Ice Cream",
                dish_type=DishType.DESSERT,
                price=22.0,
                category=DishCategory.PASTRY,
                styles=[CulinaryStyle.GOURMET, CulinaryStyle.MODERN],
                seasons=[Season.ALL],
                temperature=Temperature.HOT,
                complexity=Complexity.HIGH,
                calories=420,
                max_guests=200,
                flavors=[Flavor.SWEET, Flavor.BITTER],
                diets=["vegetarian"],
                ingredients=["chocolate", "butter", "eggs", "sugar", "vanilla"],
                compatible_beverages=["sweet-wine", "sparkling-wine"],
                cultural_traditions=[CulturalTradition.FRENCH],
                chef_style="roca"
            ),
            Dish(
                id="fresh-fruit-platter",
                name="Fresh Seasonal Fruit Platter",
                dish_type=DishType.DESSERT,
                price=12.0,
                category=DishCategory.FRUIT,
                styles=[CulinaryStyle.CLASSIC, CulinaryStyle.REGIONAL],
                seasons=[Season.SUMMER, Season.SPRING],
                temperature=Temperature.COLD,
                complexity=Complexity.LOW,
                calories=120,
                max_guests=400,
                flavors=[Flavor.SWEET, Flavor.SOUR],
                diets=["vegan", "vegetarian", "gluten-free", "dairy-free"],
                ingredients=["seasonal_fruits"],
                compatible_beverages=["sparkling-wine", "soft-drink"]
            ),
        ]
        
        # Agregar todos los platos al diccionario
        for dish in starters + mains + desserts:
            self.dishes[dish.id] = dish
    
    def _load_sample_beverages(self):
        """Carga bebidas de ejemplo basadas en los datos de CLIPS"""
        
        beverages = [
            # Infusiones y tés
            Beverage(
                id="chamomile-infusion",
                name="Chamomile Infusion",
                alcoholic=False,
                price=1.8,
                styles=["herbal-tea"],
                subtype="none"
            ),
            Beverage(
                id="green-tea-mint",
                name="Green Tea with Mint",
                alcoholic=False,
                price=2.2,
                styles=["herbal-tea"],
                subtype="none"
            ),
            Beverage(
                id="ginger-lemon-blend",
                name="Ginger Lemon Blend",
                alcoholic=False,
                price=3.0,
                styles=["herbal-tea"],
                subtype="none"
            ),
            
            # Refrescos
            Beverage(
                id="sparkling-water",
                name="Sparkling Water",
                alcoholic=False,
                price=2.0,
                styles=["soft-drink"],
                subtype="none"
            ),
            Beverage(
                id="still-water",
                name="Still Mineral Water",
                alcoholic=False,
                price=1.5,
                styles=["soft-drink"],
                subtype="none"
            ),
            Beverage(
                id="lemonade",
                name="Fresh Lemonade",
                alcoholic=False,
                price=3.0,
                styles=["soft-drink"],
                subtype="none"
            ),
            
            # Vinos blancos
            Beverage(
                id="cloudy-bay-sauvignon",
                name="Cloudy Bay Sauvignon Blanc",
                alcoholic=True,
                price=5.0,
                styles=["white-wine"],
                subtype="dry",
                compatible_flavors=[Flavor.SALTY, Flavor.SOUR, Flavor.FATTY]
            ),
            Beverage(
                id="albarino-rias-baixas",
                name="Albariño Rías Baixas",
                alcoholic=True,
                price=4.5,
                styles=["white-wine"],
                subtype="fruity",
                compatible_flavors=[Flavor.SWEET, Flavor.UMAMI]
            ),
            Beverage(
                id="verdejo-rueda",
                name="Verdejo de Rueda",
                alcoholic=True,
                price=4.0,
                styles=["white-wine"],
                subtype="dry",
                compatible_flavors=[Flavor.SALTY, Flavor.SOUR]
            ),
            
            # Vinos tintos
            Beverage(
                id="rioja-reserva",
                name="Rioja Reserva",
                alcoholic=True,
                price=6.0,
                styles=["red-wine"],
                subtype="full-bodied",
                compatible_flavors=[Flavor.FATTY, Flavor.UMAMI]
            ),
            Beverage(
                id="ribera-duero-crianza",
                name="Ribera del Duero Crianza",
                alcoholic=True,
                price=5.5,
                styles=["red-wine"],
                subtype="full-bodied",
                compatible_flavors=[Flavor.FATTY, Flavor.UMAMI]
            ),
            Beverage(
                id="priorat-reserva",
                name="Priorat Reserva",
                alcoholic=True,
                price=8.0,
                styles=["red-wine"],
                subtype="full-bodied",
                compatible_flavors=[Flavor.FATTY, Flavor.UMAMI]
            ),
            Beverage(
                id="garnacha-joven",
                name="Garnacha Joven",
                alcoholic=True,
                price=3.5,
                styles=["red-wine"],
                subtype="young",
                compatible_flavors=[Flavor.BITTER, Flavor.UMAMI]
            ),
            
            # Rosados
            Beverage(
                id="rosado-navarra",
                name="Rosado de Navarra",
                alcoholic=True,
                price=4.0,
                styles=["rose-wine"],
                subtype="rose",
                compatible_flavors=[Flavor.SALTY, Flavor.SWEET, Flavor.UMAMI]
            ),
            
            # Espumosos y dulces
            Beverage(
                id="cava-brut-nature",
                name="Cava Brut Nature",
                alcoholic=True,
                price=5.0,
                styles=["sparkling-wine"],
                subtype="sparkling",
                compatible_flavors=[Flavor.SALTY, Flavor.FATTY, Flavor.SWEET]
            ),
            Beverage(
                id="pedro-ximenez",
                name="Pedro Ximénez",
                alcoholic=True,
                price=6.0,
                styles=["sweet-wine"],
                subtype="sweet",
                compatible_flavors=[Flavor.SWEET, Flavor.UMAMI, Flavor.FATTY]
            ),
            Beverage(
                id="moscatel-valencia",
                name="Moscatel de Valencia",
                alcoholic=True,
                price=4.5,
                styles=["sweet-wine"],
                subtype="sweet",
                compatible_flavors=[Flavor.SWEET, Flavor.FATTY]
            ),
        ]
        
        for bev in beverages:
            self.beverages[bev.id] = bev
    
    def _generate_initial_cases(self):
        """Genera casos iniciales para poblar la base de conocimiento"""
        
        # Combinaciones predefinidas de menús exitosos
        menu_templates = [
            # Boda de verano - Premium
            {
                "event": EventType.WEDDING,
                "season": Season.SUMMER,
                "price_range": (80, 150),
                "starter": "ceviche-peruano",
                "main": "grilled-sea-bass",
                "dessert": "fresh-fruit-platter",
                "beverage": "cava-brut-nature",
                "style": CulinaryStyle.GOURMET,
                "success": True,
                "feedback": 4.8
            },
            {
                "event": EventType.WEDDING,
                "season": Season.AUTUMN,
                "price_range": (100, 180),
                "starter": "foie-gras-terrine",
                "main": "beef-wellington",
                "dessert": "chocolate-fondant",
                "beverage": "rioja-reserva",
                "style": CulinaryStyle.SIBARITA,
                "success": True,
                "feedback": 4.9
            },
            # Comunión - Clásico
            {
                "event": EventType.COMMUNION,
                "season": Season.SPRING,
                "price_range": (40, 70),
                "starter": "mediterranean-bruschetta",
                "main": "moroccan-chicken-tagine",
                "dessert": "tiramisu-classic",
                "beverage": "lemonade",
                "style": CulinaryStyle.CLASSIC,
                "success": True,
                "feedback": 4.5
            },
            # Bautizo - Regional
            {
                "event": EventType.CHRISTENING,
                "season": Season.SPRING,
                "price_range": (35, 60),
                "starter": "gazpacho-andaluz",
                "main": "cordero-asado",
                "dessert": "tarta-santiago",
                "beverage": "verdejo-rueda",
                "style": CulinaryStyle.REGIONAL,
                "success": True,
                "feedback": 4.6
            },
            # Comida familiar - Económico
            {
                "event": EventType.FAMILIAR,
                "season": Season.WINTER,
                "price_range": (25, 45),
                "starter": "carrot-ginger-soup",
                "main": "whole-chicken-cabbage",
                "dessert": "crema-catalana",
                "beverage": "still-water",
                "style": CulinaryStyle.REGIONAL,
                "success": True,
                "feedback": 4.3
            },
            # Congreso - Moderno
            {
                "event": EventType.CONGRESS,
                "season": Season.ALL,
                "price_range": (50, 80),
                "starter": "skinny-tangy-smoked-salmon-salad",
                "main": "risotto-funghi",
                "dessert": "tiramisu-classic",
                "beverage": "albarino-rias-baixas",
                "style": CulinaryStyle.MODERN,
                "success": True,
                "feedback": 4.4
            },
            # Corporativo - Clásico
            {
                "event": EventType.CORPORATE,
                "season": Season.ALL,
                "price_range": (45, 75),
                "starter": "mediterranean-bruschetta",
                "main": "grilled-sea-bass",
                "dessert": "cheesecake-ice-cream",
                "beverage": "cloudy-bay-sauvignon",
                "style": CulinaryStyle.CLASSIC,
                "success": True,
                "feedback": 4.5
            },
            # Boda vasca
            {
                "event": EventType.WEDDING,
                "season": Season.ALL,
                "price_range": (90, 160),
                "starter": "skinny-tangy-smoked-salmon-salad",
                "main": "bacalao-pil-pil",
                "dessert": "chocolate-fondant",
                "beverage": "priorat-reserva",
                "style": CulinaryStyle.GOURMET,
                "success": True,
                "feedback": 4.7,
                "culture": CulturalTradition.BASQUE
            },
            # Familiar italiano
            {
                "event": EventType.FAMILIAR,
                "season": Season.AUTUMN,
                "price_range": (30, 50),
                "starter": "mediterranean-bruschetta",
                "main": "risotto-funghi",
                "dessert": "tiramisu-classic",
                "beverage": "garnacha-joven",
                "style": CulinaryStyle.REGIONAL,
                "success": True,
                "feedback": 4.6,
                "culture": CulturalTradition.ITALIAN
            },
            # Verano económico
            {
                "event": EventType.FAMILIAR,
                "season": Season.SUMMER,
                "price_range": (20, 40),
                "starter": "gazpacho-andaluz",
                "main": "schinkennudeln-ham-cheese-pasta",
                "dessert": "fresh-fruit-platter",
                "beverage": "sparkling-water",
                "style": CulinaryStyle.REGIONAL,
                "success": True,
                "feedback": 4.2
            },
        ]
        
        for i, template in enumerate(menu_templates):
            starter = self.dishes.get(template["starter"])
            main = self.dishes.get(template["main"])
            dessert = self.dishes.get(template["dessert"])
            beverage = self.beverages.get(template["beverage"])
            
            if not all([starter, main, dessert, beverage]):
                continue
            
            # Crear el menú
            menu = Menu(
                id=f"menu-init-{i+1}",
                starter=starter,
                main_course=main,
                dessert=dessert,
                beverage=beverage,
                dominant_style=template.get("style"),
                cultural_theme=template.get("culture"),
                explanation=[
                    f"Menú {template['style'].value} para {template['event'].value}",
                    f"Temporada: {template['season'].value}",
                    f"Rango de precio: {template['price_range'][0]}-{template['price_range'][1]}€"
                ]
            )
            
            # Crear la solicitud
            request = Request(
                id=f"req-init-{i+1}",
                event_type=template["event"],
                season=template["season"],
                num_guests=random.randint(30, 150),
                price_min=template["price_range"][0],
                price_max=template["price_range"][1],
                wants_wine=beverage.alcoholic,
                preferred_style=template.get("style"),
                cultural_preference=template.get("culture")
            )
            
            # Crear el caso
            case = Case(
                id=f"case-init-{i+1}",
                request=request,
                menu=menu,
                success=template["success"],
                feedback_score=template["feedback"],
                source="initial"
            )
            
            self.add_case(case)
    
    def add_case(self, case: Case):
        """
        Añade un caso a la base y actualiza los índices.
        
        Args:
            case: Caso a añadir
        """
        self.cases.append(case)
        self._index_case(case)
    
    def _index_case(self, case: Case):
        """
        Indexa un caso en las estructuras de búsqueda.
        
        Args:
            case: Caso a indexar
        """
        # Por tipo de evento
        self.index_by_event[case.request.event_type].append(case)
        
        # Por rango de precio
        price = case.menu.total_price
        if price < 30:
            self.index_by_price_range["low"].append(case)
        elif price < 60:
            self.index_by_price_range["medium"].append(case)
        elif price < 100:
            self.index_by_price_range["high"].append(case)
        else:
            self.index_by_price_range["premium"].append(case)
        
        # Por temporada
        self.index_by_season[case.request.season].append(case)
        
        # Por estilo
        if case.menu.dominant_style:
            self.index_by_style[case.menu.dominant_style].append(case)
    
    def get_cases_by_event(self, event_type: EventType) -> List[Case]:
        """Obtiene casos por tipo de evento"""
        return self.index_by_event.get(event_type, [])
    
    def get_cases_by_price_range(self, min_price: float, max_price: float) -> List[Case]:
        """Obtiene casos dentro de un rango de precios"""
        result = []
        for case in self.cases:
            if min_price <= case.menu.total_price <= max_price:
                result.append(case)
        return result
    
    def get_cases_by_season(self, season: Season) -> List[Case]:
        """Obtiene casos por temporada"""
        cases = self.index_by_season.get(season, [])
        # También incluir casos con temporada ALL
        cases.extend(self.index_by_season.get(Season.ALL, []))
        # Eliminar duplicados manteniendo el orden
        seen = set()
        result = []
        for case in cases:
            if case.id not in seen:
                result.append(case)
                seen.add(case.id)
        return result
    
    def get_all_cases(self) -> List[Case]:
        """Obtiene todos los casos"""
        return self.cases.copy()
    
    def get_dish_by_id(self, dish_id: str) -> Optional[Dish]:
        """Obtiene un plato por ID"""
        return self.dishes.get(dish_id)
    
    def get_beverage_by_id(self, bev_id: str) -> Optional[Beverage]:
        """Obtiene una bebida por ID"""
        return self.beverages.get(bev_id)
    
    def get_dishes_by_type(self, dish_type: DishType) -> List[Dish]:
        """Obtiene todos los platos de un tipo"""
        return [d for d in self.dishes.values() if d.dish_type == dish_type]
    
    def get_compatible_beverages(self, wants_wine: bool) -> List[Beverage]:
        """Obtiene bebidas según preferencia de alcohol"""
        if wants_wine:
            return [b for b in self.beverages.values() if b.alcoholic]
        else:
            return [b for b in self.beverages.values() if not b.alcoholic]
    
    def save_to_file(self, filepath: str):
        """
        Guarda la base de casos en un archivo JSON.
        
        Args:
            filepath: Ruta del archivo
        """
        data = {
            "cases": [case.to_dict() for case in self.cases],
            "metadata": {
                "version": "1.0",
                "total_cases": len(self.cases),
                "saved_at": datetime.now().isoformat()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filepath: str):
        """
        Carga casos desde un archivo JSON.
        
        Args:
            filepath: Ruta del archivo
        """
        # Implementación de carga - se haría reconstruyendo objetos desde JSON
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la base de casos"""
        return {
            "total_cases": len(self.cases),
            "total_dishes": len(self.dishes),
            "total_beverages": len(self.beverages),
            "cases_by_event": {e.value: len(cases) for e, cases in self.index_by_event.items()},
            "cases_by_price": {r: len(cases) for r, cases in self.index_by_price_range.items()},
            "successful_cases": sum(1 for c in self.cases if c.success),
            "average_feedback": sum(c.feedback_score for c in self.cases) / len(self.cases) if self.cases else 0
        }
