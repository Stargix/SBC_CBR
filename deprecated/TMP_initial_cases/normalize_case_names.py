#!/usr/bin/env python3
"""
Script para normalizar nombres de platos y campos en final_50_cases.json
para que coincidan con el formato de dishes.json.
"""

import json
import re


def normalize_dish_name(name):
    """Normaliza un nombre de plato al formato slug."""
    # Convertir a minúsculas
    name = name.lower()
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


def normalize_cases():
    """Normaliza los nombres de platos y campos en final_50_cases.json."""
    print("=" * 80)
    print("🔧 NORMALIZANDO NOMBRES DE PLATOS Y CAMPOS")
    print("=" * 80)
    
    # Cargar mapeo de platos
    dish_mapping = load_dishes_mapping()
    
    # Cargar casos
    print("\n📂 Cargando final_50_cases.json...")
    with open("develop/config/final_50_cases.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    cases = data['cases']
    
    print(f"   ✓ {len(cases)} casos cargados")
    
    # Normalizar casos
    print("\n🔄 Normalizando casos...")
    normalized_cases = []
    fixed_count = 0
    
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
        
        # Contar cambios
        if (original_starter != normalized_case['starter'] or
            original_main != normalized_case['main'] or
            original_dessert != normalized_case['dessert'] or
            original_beverage != normalized_case['beverage']):
            fixed_count += 1
        
        normalized_cases.append(normalized_case)
        
        if i % 10 == 0:
            print(f"   ✓ {i} casos procesados")
    
    # Guardar
    output_data = {'cases': normalized_cases}
    
    print(f"\n💾 Guardando casos normalizados...")
    with open("develop/config/final_50_cases.json", 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print(f"   ✓ Archivo guardado")
    
    print("\n" + "=" * 80)
    print(f"✅ NORMALIZACIÓN COMPLETADA")
    print(f"   Casos totales: {len(normalized_cases)}")
    print(f"   Casos con nombres corregidos: {fixed_count}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    normalize_cases()
