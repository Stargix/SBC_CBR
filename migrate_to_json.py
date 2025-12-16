#!/usr/bin/env python3
"""
Script de migración de datos hardcodeados a JSON.

Este script extrae los datos hardcodeados de case_base.py
(platos, bebidas, casos) y los convierte a formato JSON
para facilitar su mantenimiento.

Uso:
    python migrate_to_json.py

Genera:
    - config/dishes.json
    - config/beverages.json
    - config/initial_cases.json (opcional)
"""

import json
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from CBR.case_base import CaseBase
from CBR.models import Flavor


def extract_dishes_to_json(case_base):
    """Extrae todos los platos a formato JSON"""
    dishes = []
    
    for dish_id, dish in case_base.dishes.items():
        dish_dict = {
            "id": dish.id,
            "name": dish.name,
            "dish_type": dish.dish_type.value,
            "price": dish.price,
            "category": dish.category.value,
            "styles": [s.value for s in dish.styles],
            "seasons": [s.value for s in dish.seasons],
            "temperature": dish.temperature.value,
            "complexity": dish.complexity.value,
            "calories": dish.calories,
            "max_guests": dish.max_guests,
            "flavors": [f.value for f in dish.flavors],
            "diets": dish.diets,
            "ingredients": dish.ingredients,
            "compatible_beverages": dish.compatible_beverages,
            "cultural_traditions": [ct.value for ct in dish.cultural_traditions]
        }
        dishes.append(dish_dict)
    
    return dishes


def extract_beverages_to_json(case_base):
    """Extrae todas las bebidas a formato JSON"""
    beverages = []
    
    for bev_id, bev in case_base.beverages.items():
        bev_dict = {
            "id": bev.id,
            "name": bev.name,
            "alcoholic": bev.alcoholic,
            "price": bev.price,
            "styles": bev.styles,
            "subtype": bev.subtype,
        }
        
        if hasattr(bev, 'compatible_flavors') and bev.compatible_flavors:
            bev_dict["compatible_flavors"] = [f.value for f in bev.compatible_flavors]
        
        beverages.append(bev_dict)
    
    return beverages


def main():
    """Función principal"""
    print("Iniciando migración de datos hardcodeados a JSON...")
    
    # Crear instancia de CaseBase para acceder a los datos
    print("Cargando datos de case_base...")
    case_base = CaseBase()
    
    # Crear directorio config si no existe
    config_dir = Path(__file__).parent / 'config'
    config_dir.mkdir(exist_ok=True)
    
    # Extraer platos
    print(f"Extrayendo {len(case_base.dishes)} platos...")
    dishes = extract_dishes_to_json(case_base)
    dishes_file = config_dir / 'dishes.json'
    with open(dishes_file, 'w', encoding='utf-8') as f:
        json.dump({"dishes": dishes}, f, indent=2, ensure_ascii=False)
    print(f"✓ Platos guardados en {dishes_file}")
    
    # Extraer bebidas
    print(f"Extrayendo {len(case_base.beverages)} bebidas...")
    beverages = extract_beverages_to_json(case_base)
    beverages_file = config_dir / 'beverages.json'
    with open(beverages_file, 'w', encoding='utf-8') as f:
        json.dump({"beverages": beverages}, f, indent=2, ensure_ascii=False)
    print(f"✓ Bebidas guardadas en {beverages_file}")
    
    print("\n¡Migración completada!")
    print("\nPróximos pasos:")
    print("1. Revisar los archivos JSON generados")
    print("2. Modificar case_base.py para cargar desde JSON")
    print("3. Probar que el sistema sigue funcionando")
    

if __name__ == "__main__":
    main()
