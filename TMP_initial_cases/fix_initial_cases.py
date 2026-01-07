#!/usr/bin/env python3
"""
Script to fix format issues in initial_cases.json
- Normalize dish names to match dishes.json
- Remove cases with duplicate dishes
- Ensure proper field formatting
"""

import json
import re


def normalize_dish_name(name):
    """Normaliza un nombre de plato al formato slug."""
    # Convertir a minúsculas
    name = name.lower()
    # Eliminar prefijos como "recipe:"
    name = re.sub(r'^recipe:[-\s]*', '', name)
    # Reemplazar espacios y caracteres especiales por guiones
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    # Limpiar guiones al inicio y final
    name = name.strip('-')
    return name


def load_dishes_mapping():
    """Carga el mapeo de nombres de platos desde dishes.json."""
    print("📂 Cargando dishes.json...")
    with open("develop/config/dishes.json", 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    
    # Crear mapeo: normalized_name -> id
    dish_mapping = {}
    for dish in dishes:
        dish_id = dish['id']
        dish_name = dish['name']
        # El ID ya está normalizado
        dish_mapping[dish_id] = dish_id
        # También mapear variaciones del nombre
        normalized = normalize_dish_name(dish_name)
        dish_mapping[normalized] = dish_id
    
    print(f"   ✓ {len(dishes)} platos cargados")
    return dish_mapping


def find_best_match(dish_name, dish_mapping):
    """Encuentra el mejor match para un nombre de plato."""
    # Primero intentar match exacto
    normalized = normalize_dish_name(dish_name)
    if normalized in dish_mapping:
        return dish_mapping[normalized]
    
    # Si no hay match, buscar coincidencias parciales
    for key in dish_mapping:
        if normalized in key or key in normalized:
            return dish_mapping[key]
    
    # Si no se encuentra, retornar el nombre normalizado
    return normalized


def has_duplicate_dishes(case):
    """Verifica si un caso tiene platos repetidos."""
    dishes = [
        case.get('starter', ''),
        case.get('main', ''),
        case.get('dessert', ''),
        case.get('beverage', '')
    ]
    
    # Filtrar vacíos
    dishes = [d for d in dishes if d]
    
    # Verificar si hay duplicados
    return len(dishes) != len(set(dishes))


def main():
    print("=" * 80)
    print("🔧 FIXING INITIAL_CASES.JSON FORMAT")
    print("=" * 80)
    
    # Cargar mapeo de platos
    dish_mapping = load_dishes_mapping()
    
    # Cargar casos
    print("\n📂 Cargando initial_cases.json...")
    with open("develop/config/initial_cases.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    cases = data['cases']
    
    print(f"   ✓ {len(cases)} casos cargados")
    
    # Paso 1: Normalizar nombres de platos
    print("\n🔄 Paso 1: Normalizando nombres de platos...")
    normalized_cases = []
    fixed_names_count = 0
    
    for i, case in enumerate(cases, 1):
        normalized_case = {}
        
        # Normalizar campos simples (lowercase)
        normalized_case['event'] = case.get('event', '').lower()
        normalized_case['season'] = case.get('season', '').lower()
        normalized_case['price_min'] = case.get('price_min', 0.0)
        normalized_case['price_max'] = case.get('price_max', 0.0)
        
        # Normalizar nombres de platos
        original_starter = case.get('starter', '')
        original_main = case.get('main', '')
        original_dessert = case.get('dessert', '')
        original_beverage = case.get('beverage', '')
        
        normalized_case['starter'] = find_best_match(original_starter, dish_mapping)
        normalized_case['main'] = find_best_match(original_main, dish_mapping)
        normalized_case['dessert'] = find_best_match(original_dessert, dish_mapping)
        normalized_case['beverage'] = find_best_match(original_beverage, dish_mapping)
        
        # Normalizar style y culture (lowercase)
        normalized_case['style'] = case.get('style', 'classic').lower()
        normalized_case['culture'] = case.get('culture', 'universal').lower()
        
        # Añadir success y feedback si existen
        if 'success' in case:
            normalized_case['success'] = case['success']
        if 'feedback' in case:
            normalized_case['feedback'] = case['feedback']
        
        # Contar cambios
        if (original_starter != normalized_case['starter'] or
            original_main != normalized_case['main'] or
            original_dessert != normalized_case['dessert'] or
            original_beverage != normalized_case['beverage']):
            fixed_names_count += 1
        
        normalized_cases.append(normalized_case)
    
    print(f"   ✓ {fixed_names_count} casos con nombres corregidos")
    
    # Paso 2: Eliminar casos con platos duplicados
    print("\n🔍 Paso 2: Eliminando casos con platos repetidos...")
    
    valid_cases = []
    removed_cases = []
    
    for i, case in enumerate(normalized_cases, 1):
        if has_duplicate_dishes(case):
            removed_cases.append({
                'index': i,
                'event': case.get('event'),
                'season': case.get('season'),
                'dishes': {
                    'starter': case.get('starter'),
                    'main': case.get('main'),
                    'dessert': case.get('dessert'),
                    'beverage': case.get('beverage')
                }
            })
        else:
            valid_cases.append(case)
    
    # Mostrar casos eliminados
    if removed_cases:
        print(f"   ❌ Casos eliminados ({len(removed_cases)}):")
        for removed in removed_cases[:5]:  # Mostrar solo los primeros 5
            print(f"      Caso #{removed['index']}: {removed['event']} - {removed['season']}")
            print(f"         Platos: {list(removed['dishes'].values())}")
        if len(removed_cases) > 5:
            print(f"      ... y {len(removed_cases) - 5} más")
    else:
        print(f"   ✓ No se encontraron casos con platos duplicados")
    
    # Guardar casos válidos
    output_data = {'cases': valid_cases}
    
    print(f"\n💾 Guardando archivo corregido...")
    with open("develop/config/initial_cases.json", 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print(f"   ✓ Archivo guardado")
    
    print("\n" + "=" * 80)
    print(f"✅ CORRECCIÓN COMPLETADA")
    print(f"   Casos originales:           {len(cases)}")
    print(f"   Nombres normalizados:       {fixed_names_count}")
    print(f"   Casos con duplicados:       {len(removed_cases)}")
    print(f"   Casos finales:              {len(valid_cases)}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
