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
from pathlib import Path
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
        self._load_dishes_from_json()
        self._load_beverages_from_json()
        self._generate_initial_cases()
    
    def _load_dishes_from_json(self):
        """Carga platos desde archivo JSON"""
        import json
        import os
        
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'dishes.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for dish_data in data:
            # Mapear dish_type a valores del enum
            dish_type_mapping = {
                'main': 'MAIN_COURSE',
                'main_course': 'MAIN_COURSE',
                'starter': 'STARTER',
                'dessert': 'DESSERT'
            }
            dish_type_str = dish_data['dish_type'].lower()
            dish_type_enum = dish_type_mapping.get(dish_type_str, 'MAIN_COURSE')
            
            # Mapear complexity (puede ser número o string)
            complexity_val = dish_data['complexity']
            if isinstance(complexity_val, int):
                complexity_mapping = {1: 'LOW', 2: 'MEDIUM', 3: 'HIGH'}
                complexity_enum = complexity_mapping.get(complexity_val, 'MEDIUM')
            else:
                complexity_enum = complexity_val.upper()
            
            # Filtrar flavors válidos
            valid_flavors = []
            for f in dish_data['flavors']:
                try:
                    valid_flavors.append(Flavor[f.upper()])
                except KeyError:
                    pass  # Ignorar flavors no reconocidos
            
            # Si no hay flavors válidos, usar UMAMI por defecto
            if not valid_flavors:
                valid_flavors = [Flavor.UMAMI]
            
            # Mapear categoría (con fallback a categorías válidas)
            try:
                category = DishCategory[dish_data['category'].upper()]
            except KeyError:
                # Si la categoría no existe, intentar mapearla o usar PASTA por defecto
                category_fallback = {
                    'BREAD': DishCategory.PASTRY,
                    'SANDWICH': DishCategory.SNACK,
                    'CASSEROLE': DishCategory.MEAT,
                    'UNKNOWN': DishCategory.PASTA
                }
                category = category_fallback.get(dish_data['category'].upper(), DishCategory.PASTA)
            
            dish = Dish(
                id=dish_data['id'],
                name=dish_data['name'],
                dish_type=DishType[dish_type_enum],
                price=dish_data['price'],
                category=category,
                styles=[CulinaryStyle[s.upper()] for s in dish_data['styles']],
                seasons=[Season[s.upper()] for s in dish_data['seasons']],
                temperature=Temperature[dish_data['temperature'].upper()],
                complexity=Complexity[complexity_enum],
                calories=dish_data['calories'],
                max_guests=dish_data.get('max_guests', 100),
                flavors=valid_flavors,
                diets=dish_data.get('diets', []),
                ingredients=dish_data.get('ingredients', []),
                compatible_beverages=dish_data.get('compatible_beverages', []),
                cultural_traditions=[CulturalTradition[ct.upper()] for ct in dish_data.get('cultural_traditions', [])]
            )
            self.dishes[dish.id] = dish
    
    def _load_sample_dishes(self):
        """DEPRECATED: Carga platos desde JSON usando _load_dishes_from_json()"""
        # Este método se mantiene por compatibilidad pero ya no se usa
        pass
    
    def _load_beverages_from_json(self):
        """Carga bebidas desde archivo JSON"""
        import json
        import os
        
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'beverages.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for bev_data in data:
            bev = Beverage(
                id=bev_data['id'],
                name=bev_data['name'],
                alcoholic=bev_data['alcoholic'],
                price=bev_data['price'],
                type=bev_data['type'],
                subtype=bev_data.get('subtype')
            )
            
            self.beverages[bev.id] = bev
    
    def _load_sample_beverages(self):
        """DEPRECATED: Carga bebidas desde JSON usando _load_beverages_from_json()"""
        # Este método se mantiene por compatibilidad pero ya no se usa
        pass
    
    def _load_initial_cases_from_json(self) -> List[Dict]:
        """Cargar casos iniciales desde el archivo JSON."""
        config_path = Path(__file__).parent.parent / "config" / "initial_cases.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data["cases"]

    def _generate_initial_cases(self):
        """Genera casos iniciales para poblar la base de conocimiento"""
        menu_templates = self._load_initial_cases_from_json()
        
        for i, template in enumerate(menu_templates):
            starter = self.dishes.get(template["starter"])
            main = self.dishes.get(template["main"])
            dessert = self.dishes.get(template["dessert"])
            beverage = self.beverages.get(template["beverage"])
            
            if not all([starter, main, dessert, beverage]):
                continue
            
            # Convertir strings a enums
            event = EventType(template["event"])
            season = Season(template["season"])
            style = CulinaryStyle(template["style"])
            culture = CulturalTradition(template["culture"]) if "culture" in template else None
            
            # Crear el menú
            menu = Menu(
                id=f"menu-init-{i+1}",
                starter=starter,
                main_course=main,
                dessert=dessert,
                beverage=beverage,
                dominant_style=style,
                cultural_theme=culture,
                explanation=[
                    f"Menú {style.value} para {event.value}",
                    f"Temporada: {season.value}",
                    f"Rango de precio: {template['price_min']}-{template['price_max']}€"
                ]
            )
            
            # Crear la solicitud
            request = Request(
                id=f"req-init-{i+1}",
                event_type=event,
                season=season,
                num_guests=template.get("num_guests", 50),
                price_min=template["price_min"],
                price_max=template["price_max"],
                wants_wine=beverage.alcoholic,
                preferred_style=style,
                cultural_preference=culture,
                required_diets=template.get("required_diets", []),
                restricted_ingredients=template.get("restricted_ingredients", [])
            )
            
            # Crear el caso
            case = Case(
                id=f"case-init-{i+1}",
                request=request,
                menu=menu,
                success=template["success"],
                feedback_score=template["feedback"],
                source="initial",
                is_negative=template.get("is_negative", False)  # Soporte para casos negativos
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
        if case.request.event_type not in self.index_by_event:
            self.index_by_event[case.request.event_type] = []
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
        if case.request.season not in self.index_by_season:
            self.index_by_season[case.request.season] = []
        self.index_by_season[case.request.season].append(case)
        
        # Por estilo
        if case.menu.dominant_style:
            if case.menu.dominant_style not in self.index_by_style:
                self.index_by_style[case.menu.dominant_style] = []
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
