#!/usr/bin/env python3
"""
Script para generar un nuevo final_50_cases.json con representación de TODAS las culturas.

Genera 50 casos con distribución balanceada incluyendo:
- American (5 casos)
- Chinese (4 casos)
- French (4 casos)
- Indian (5 casos)
- Italian (5 casos)
- Japanese (4 casos)
- Korean (4 casos)
- Lebanese (4 casos)
- Mexican (4 casos)
- Spanish (4 casos)
- Thai (4 casos)
- Vietnamese (2 casos)

Total: 50 casos
"""

import json
import random
from pathlib import Path
from collections import defaultdict

# Configuración de distribución equilibrada
CULTURE_DISTRIBUTION = {
    "American": 5,
    "Indian": 5,
    "Italian": 5,
    "Chinese": 4,
    "French": 4,
    "Japanese": 4,
    "Korean": 4,
    "Lebanese": 4,
    "Mexican": 4,
    "Spanish": 4,
    "Thai": 4,
    "Vietnamese": 2,
}

# Tipos de eventos
EVENTS = ["corporate", "wedding", "christening", "congress", "communion", "birthday", "familiar", "anniversary"]

# Estaciones
SEASONS = ["spring", "summer", "autumn", "winter"]

# Estilos
STYLES = ["classic", "modern", "fusion"]


def load_databases():
    """Carga las bases de datos de platos."""
    print("📂 Cargando bases de datos...")
    
    # Cargar dishes.json (es una lista directa)
    with open("develop/config/dishes.json", 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    
    # Cargar ingredients.json para mapeo de culturas
    with open("develop/config/ingredients.json", 'r', encoding='utf-8') as f:
        ingredients_data = json.load(f)
    ing_to_cultures = ingredients_data['ingredient_to_cultures']
    
    print(f"   ✓ {len(dishes)} platos cargados")
    print(f"   ✓ {len(ing_to_cultures)} ingredientes mapeados")
    
    return dishes, ing_to_cultures


def get_culture_for_dish(dish_name, dishes, ing_to_cultures):
    """Obtiene la cultura predominante para un plato basado en sus ingredientes."""
    # Buscar el plato en la base de datos
    matching_dish = None
    for dish in dishes:
        if dish['name'].lower() == dish_name.lower():
            matching_dish = dish
            break
    
    if not matching_dish or 'ingredients' not in matching_dish:
        return "Universal"
    
    # Mapear ingredientes a culturas
    culture_counts = defaultdict(int)
    ingredient_list = matching_dish.get('ingredients', [])
    
    for ingredient in ingredient_list:
        ing_lower = ingredient.lower()
        if ing_lower in ing_to_cultures:
            cultures = ing_to_cultures[ing_lower].get('cultures', ['Universal'])
            for culture in cultures:
                if culture != "Universal":
                    culture_counts[culture] += 1
    
    if culture_counts:
        # Retornar la cultura con más ingredientes
        return max(culture_counts.items(), key=lambda x: x[1])[0]
    else:
        return "Universal"


def find_dishes_by_culture(target_culture, dishes, ing_to_cultures, num_dishes=3):
    """Encuentra platos asociados a una cultura."""
    matching_dishes = []
    
    for dish in dishes:
        if 'ingredients' not in dish:
            continue
        
        # Mapear ingredientes a culturas
        culture_counts = defaultdict(int)
        ingredient_list = dish.get('ingredients', [])
        
        for ingredient in ingredient_list:
            ing_lower = ingredient.lower()
            if ing_lower in ing_to_cultures:
                cultures = ing_to_cultures[ing_lower].get('cultures', [])
                for culture in cultures:
                    if culture != "Universal":
                        culture_counts[culture] += 1
        
        # Si tiene ingredientes de la cultura objetivo, incluir
        if culture_counts.get(target_culture, 0) > 0:
            matching_dishes.append(dish['name'])
    
    # Retornar platos aleatorios
    if len(matching_dishes) > num_dishes:
        return random.sample(matching_dishes, num_dishes)
    else:
        return matching_dishes if matching_dishes else random.sample([d['name'] for d in dishes if 'ingredients' in d], num_dishes)


def generate_case(case_id, culture, dishes, ing_to_cultures):
    """Genera un caso individual con la cultura especificada."""
    
    # Seleccionar atributos aleatorios
    event = random.choice(EVENTS)
    season = random.choice(SEASONS)
    style = random.choice(STYLES)
    
    # Generar rango de precio basado en cultura
    price_ranges = {
        "American": (45, 95),
        "Indian": (50, 100),
        "Italian": (60, 120),
        "Chinese": (40, 85),
        "French": (70, 150),
        "Japanese": (65, 130),
        "Korean": (45, 95),
        "Lebanese": (50, 100),
        "Mexican": (45, 90),
        "Spanish": (55, 110),
        "Thai": (45, 95),
        "Vietnamese": (40, 85),
    }
    
    price_min, price_max_range = price_ranges.get(culture, (50, 100))
    price_max = price_min + random.randint(20, price_max_range - price_min)
    
    # Encontrar platos de la cultura
    starter_list = find_dishes_by_culture(culture, dishes, ing_to_cultures, num_dishes=3)
    main_list = find_dishes_by_culture(culture, dishes, ing_to_cultures, num_dishes=3)
    dessert_list = find_dishes_by_culture(culture, dishes, ing_to_cultures, num_dishes=2)
    beverage_list = find_dishes_by_culture(culture, dishes, ing_to_cultures, num_dishes=2)
    
    # Si no hay suficientes platos, usar cualquiera
    if not starter_list:
        starter_list = [random.choice([d['name'] for d in dishes if 'ingredients' in d])]
    if not main_list:
        main_list = [random.choice([d['name'] for d in dishes if 'ingredients' in d])]
    if not dessert_list:
        dessert_list = [random.choice([d['name'] for d in dishes if 'ingredients' in d])]
    if not beverage_list:
        beverage_list = [random.choice([d['name'] for d in dishes if 'ingredients' in d])]
    
    # Normalizar nombres de platos a slug format
    def to_slug(name):
        return name.lower().replace(" ", "-").replace("&", "")
    
    return {
        "event": event,
        "season": season,
        "price_min": float(price_min),
        "price_max": float(price_max),
        "starter": to_slug(random.choice(starter_list)),
        "main": to_slug(random.choice(main_list)),
        "dessert": to_slug(random.choice(dessert_list)),
        "beverage": to_slug(random.choice(beverage_list)),
        "style": style,
        "culture_target": culture
    }


def main():
    """Función principal."""
    print("=" * 90)
    print("🌍 GENERACIÓN DE 50 CASOS CON TODAS LAS CULTURAS")
    print("=" * 90)
    
    # Cargar bases de datos
    dishes, ing_to_cultures = load_databases()
    
    # Generar casos
    print("\n📝 Generando 50 casos...")
    cases = []
    case_count = 0
    
    # Crear lista de culturas con su distribución deseada
    culture_list = []
    for culture, count in CULTURE_DISTRIBUTION.items():
        culture_list.extend([culture] * count)
    
    # Barajar para distribución aleatoria
    random.shuffle(culture_list)
    
    for i, culture in enumerate(culture_list, 1):
        case = generate_case(i, culture, dishes, ing_to_cultures)
        cases.append(case)
        
        # Mostrar progreso cada 5 casos
        if i % 5 == 0:
            print(f"   ✓ {i:2d} casos generados")
    
    # Crear estructura final (sin incluir culture_target en el JSON final)
    final_cases = []
    for case in cases:
        final_case = {k: v for k, v in case.items() if k != "culture_target"}
        final_cases.append(final_case)
    
    # Guardar
    output_file = "develop/config/final_50_cases_all_cultures.json"
    output_data = {"cases": final_cases}
    
    print(f"\n💾 Guardando en {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print("   ✓ Archivo guardado")
    
    # Mostrar estadísticas
    print("\n📊 DISTRIBUCIÓN DE CULTURAS EN CASOS GENERADOS:")
    print("-" * 50)
    
    culture_count = defaultdict(int)
    for case in cases:
        culture_count[case["culture_target"]] += 1
    
    print(f"{'Cultura':<15} | {'Esperados':>10} | {'Generados':>10}")
    print("-" * 50)
    
    for culture in sorted(culture_count.keys()):
        expected = CULTURE_DISTRIBUTION[culture]
        actual = culture_count[culture]
        match = "✓" if expected == actual else "✗"
        print(f"{culture:<15} | {expected:10d} | {actual:10d} {match}")
    
    print("\n✅ GENERACIÓN COMPLETADA")
    print("=" * 90)
    print(f"\n📝 Próximos pasos:")
    print(f"   1. Revisar: {output_file}")
    print(f"   2. Reemplazar: cp {output_file} develop/config/final_50_cases.json")
    print(f"   3. Re-ejecutar: python enrich_cases_culture_detailed.py")


if __name__ == "__main__":
    main()
