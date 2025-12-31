#!/usr/bin/env python3
"""
Script para convertir los CSV a JSON para el sistema CBR.
Mantén los CSV como fuente de datos, ejecuta este script cuando los actualices.
"""
import csv
import json
import ast
from pathlib import Path


def parse_list_field(value):
    """Convierte strings como "['item1', 'item2']" a listas Python."""
    if not value or value.strip() == '':
        return []
    try:
        # Intentar evaluar como literal Python
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except:
        # Si falla, separar por comas
        return [item.strip() for item in value.strip('[]').split(',') if item.strip()]


def create_slug(name):
    """Crea un ID tipo slug a partir del nombre."""
    # Convertir a minúsculas, reemplazar espacios y caracteres especiales
    slug = name.lower()
    slug = slug.replace(' ', '-')
    slug = slug.replace('&', 'and')
    # Remover caracteres especiales excepto guiones
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    # Eliminar guiones múltiples
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-')


def convert_beverages():
    """Convierte begudes.csv y wines.csv a un único beverages.json."""
    config_dir = Path(__file__).parent
    begudes_path = config_dir / "begudes.csv"
    wines_path = config_dir / "wines.csv"
    json_path = config_dir / "beverages.json"
    
    beverages = []
    
    # Cargar begudes.csv
    with open(begudes_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            category = row['Category']
            is_alcoholic = category.lower() not in ['herbal tea', 'tea', 'coffee', 'juice', 'water', 'soft drink']
            
            # Determinar type
            beverage_type = category.lower().replace(' ', '-')
            
            # Determinar subtype (solo para bebidas que no sean herbal tea o soft drink)
            subtype = None
            if category.lower() not in ['herbal tea', 'soft drink']:
                subtype = beverage_type
            
            beverage = {
                "id": create_slug(row['Name']),
                "name": row['Name'],
                "alcoholic": is_alcoholic,
                "price": float(row['Price_Per_Serving_EUR']),
                "type": beverage_type
            }
            
            if subtype:
                beverage["subtype"] = subtype
            
            beverages.append(beverage)
    
    begudes_count = len(beverages)
    
    # Cargar wines.csv
    with open(wines_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            wine_type = row['Type'].lower()  # white, red, rose, sparkling
            subcategory = row['Subcategory'].lower()  # dry, sweet, etc.
            
            beverage = {
                "id": create_slug(row['Name']),
                "name": row['Name'],
                "alcoholic": True,
                "price": float(row['Price per Cup']),
                "type": f"{wine_type}-wine",
                "subtype": subcategory
            }
            beverages.append(beverage)
    
    wines_count = len(beverages) - begudes_count
    
    # Guardar todo en beverages.json
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(beverages, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Convertido begudes.csv + wines.csv → beverages.json ({begudes_count} bebidas + {wines_count} vinos = {len(beverages)} total)")


def convert_dishes_to_json():
    """Convierte dishes_data.csv a dishes.json."""
    config_dir = Path(__file__).parent
    csv_path = config_dir / "dishes_data.csv"
    json_path = config_dir / "dishes.json"
    
    dishes = []
    
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        dish_id = 1
        
        for row in reader:
            # Parsear campos de lista
            compatible_drinks = parse_list_field(row.get('compatible_drinks', ''))
            ingredients = parse_list_field(row.get('ingredients', ''))
            taste = parse_list_field(row.get('taste', ''))
            health_labels = parse_list_field(row.get('healthLabels', ''))
            diet_labels = parse_list_field(row.get('dietLabels', ''))
            seasons = parse_list_field(row.get('season', ''))
            cutlery = parse_list_field(row.get('cutlery', ''))
            
            # Mapear complexity a string para el enum
            complexity_num = row.get('complexity', 'medium')
            if complexity_num == '1' or complexity_num == 'low':
                complexity = 'low'
            elif complexity_num == '3' or complexity_num == 'high':
                complexity = 'high'
            else:
                complexity = 'medium'
            
            # Mapear course_type al enum usado
            course_mapping = {
                'main_course': 'main_course',
                'starter': 'starter',
                'dessert': 'dessert',
                'side': 'starter',
                'appetizer': 'starter'
            }
            course_type = row.get('course_type', 'main_course')
            dish_type = course_mapping.get(course_type, 'main_course')
            
            # Crear el plato con todos los campos requeridos
            dish = {
                "id": create_slug(row['name']),
                "name": row['name'],
                "dish_type": dish_type,
                "price": float(row.get('total_price', 0)),
                "category": row.get('type', 'unknown'),
                "styles": [row.get('style', 'casual')],
                "seasons": seasons if seasons else ['all'],
                "flavors": taste if taste else ['umami'],
                "ingredients": ingredients,
                "complexity": complexity,
                "temperature": row.get('temperature', 'hot'),
                "calories": float(row.get('kcal', 0)),
                "max_guests": 100,  # Por defecto
                "diets": diet_labels,
                "compatible_beverages": compatible_drinks,
                "cultural_traditions": []  # Por defecto vacío
            }
            dishes.append(dish)
            dish_id += 1
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dishes, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Convertido {csv_path.name} → {json_path.name} ({len(dishes)} platos)")


def main():
    """Ejecuta todas las conversiones."""
    print("🔄 Convirtiendo CSV → JSON...\n")
    
    try:
        convert_beverages()
        convert_dishes_to_json()
        
        print("\n✅ Conversión completada!")
        print("\n📝 Próximos pasos:")
        print("   1. Revisa los JSON generados")
        print("   2. Los CSV son tu fuente de datos (edita ahí)")
        print("   3. Ejecuta este script cada vez que actualices los CSV")
        print("   4. El sistema CBR seguirá cargando desde JSON (más rápido)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
