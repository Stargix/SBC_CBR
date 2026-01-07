#!/usr/bin/env python3
"""
Script para enriquecer casos con análisis detallado de culturas basado en ingredientes reales.

Este script carga final_50_cases.json y para cada caso:
1. Busca los platos (starter, main, dessert, beverage) en dishes.json
2. Extrae los ingredientes de cada plato
3. Mapea ingredientes a culturas usando ingredients.json
4. Calcula la cultura DOMINANTE sin forzar la asignación
5. Genera análisis detallado con proporción de culturas

Resultado: final_50_cases_enriched_detailed.json con análisis cultural real
"""

import json
from collections import defaultdict
from pathlib import Path


def load_databases():
    """Carga las bases de datos necesarias."""
    print("📂 Cargando bases de datos...")
    
    # Cargar platos
    with open("develop/config/dishes.json", 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    
    # Crear índice de platos por nombre (normalizado)
    dishes_by_name = {}
    for dish in dishes:
        name_key = dish['name'].lower().replace(" ", "-").replace("&", "")
        dishes_by_name[name_key] = dish
    
    # Cargar ingredientes
    with open("develop/config/ingredients.json", 'r', encoding='utf-8') as f:
        ingredients_data = json.load(f)
    ing_to_cultures = ingredients_data['ingredient_to_cultures']
    
    # Cargar casos
    with open("develop/config/final_50_cases.json", 'r', encoding='utf-8') as f:
        cases_data = json.load(f)
    cases = cases_data['cases']
    
    print(f"   ✓ {len(dishes)} platos cargados")
    print(f"   ✓ {len(ing_to_cultures)} ingredientes mapeados")
    print(f"   ✓ {len(cases)} casos cargados")
    
    return dishes_by_name, ing_to_cultures, cases


def analyze_ingredients_cultures(ingredients, ing_to_cultures):
    """Mapea una lista de ingredientes a culturas."""
    culture_counts = defaultdict(int)
    
    for ingredient in ingredients:
        ing_lower = ingredient.lower()
        if ing_lower in ing_to_cultures:
            cultures = ing_to_cultures[ing_lower].get('cultures', [])
            for culture in cultures:
                culture_counts[culture] += 1
    
    return dict(culture_counts)


def find_top_cultures(culture_counts, n=2):
    """Encuentra las n culturas dominantes excluyendo 'Universal'."""
    # Filtrar Universal
    filtered = {k: v for k, v in culture_counts.items() if k != "Universal"}
    
    if not filtered:
        # Si solo hay Universal, retornar lo que haya
        if culture_counts:
            sorted_cultures = sorted(culture_counts.items(), key=lambda x: x[1], reverse=True)
            return [c[0] for c in sorted_cultures[:n]]
        return ["Universal"]
    
    # Retornar los n máximos
    sorted_cultures = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
    result = [c[0] for c in sorted_cultures[:n]]
    
    # Si hay menos de n, rellenar con Universal si es necesario
    while len(result) < n and "Universal" not in result:
        result.append("Universal")
    
    return result


def analyze_case_cultures(case, dishes_by_name, ing_to_cultures):
    """Analiza culturas para un caso específico."""
    
    # Extraer nombres de platos
    dish_names = [
        case.get('starter', ''),
        case.get('main', ''),
        case.get('dessert', ''),
        case.get('beverage', '')
    ]
    
    dish_names = [n for n in dish_names if n]  # Filtrar vacíos
    
    all_culture_counts = defaultdict(int)
    dish_details = {}
    total_ingredients = 0
    
    # Analizar cada plato
    for dish_name in dish_names:
        dish_key = dish_name.lower().replace(" ", "-").replace("&", "")
        
        if dish_key in dishes_by_name:
            dish = dishes_by_name[dish_key]
            ingredients = dish.get('ingredients', [])
            
            # Mapear ingredientes a culturas
            culture_counts = analyze_ingredients_cultures(ingredients, ing_to_cultures)
            
            # Acumular en totales
            for culture, count in culture_counts.items():
                all_culture_counts[culture] += count
            
            total_ingredients += len(ingredients)
            
            dish_details[dish_name] = {
                'ingredients_count': len(ingredients),
                'culture_counts': culture_counts,
                'top_culture': find_top_cultures(culture_counts, n=1)[0] if culture_counts else "Unknown"
            }
    
    # Encontrar culturas dominantes
    if all_culture_counts:
        top_cultures = find_top_cultures(all_culture_counts, n=2)
        dominant_culture = top_cultures[0]
        secondary_culture = top_cultures[1] if len(top_cultures) > 1 else None
        
        dominant_count = all_culture_counts.get(dominant_culture, 0)
        secondary_count = all_culture_counts.get(secondary_culture, 0) if secondary_culture else 0
        total_count = sum(all_culture_counts.values())
        
        dominant_proportion = dominant_count / total_count if total_count > 0 else 0
        secondary_proportion = secondary_count / total_count if total_count > 0 else 0
    else:
        dominant_culture = "Universal"
        secondary_culture = None
        dominant_proportion = 0
        secondary_proportion = 0
        total_count = 0
    
    return {
        'culture_analysis': {
            'dominant_culture': dominant_culture,
            'dominant_proportion': round(dominant_proportion, 3),
            'secondary_culture': secondary_culture,
            'secondary_proportion': round(secondary_proportion, 3),
            'all_culture_counts': dict(all_culture_counts)
        },
        'dish_details': dish_details,
        'total_ingredients': total_ingredients,
        'platos_analizados': len(dish_details)
    }


def main():
    """Función principal."""
    print("=" * 90)
    print("🌍 ENRIQUECIMIENTO DETALLADO DE CULTURAS (Análisis de Ingredientes)")
    print("=" * 90)
    
    # Cargar bases de datos
    dishes_by_name, ing_to_cultures, cases = load_databases()
    
    # Analizar casos
    print(f"\n📊 Procesando {len(cases)} casos...")
    
    enriched_cases = []
    culture_distribution = defaultdict(int)
    
    for i, case in enumerate(cases, 1):
        # Analizar culturas del caso
        analysis = analyze_case_cultures(case, dishes_by_name, ing_to_cultures)
        
        # Enriquecer caso
        enriched_case = {**case, **analysis}
        enriched_cases.append(enriched_case)
        
        dominant = analysis['culture_analysis']['dominant_culture']
        secondary = analysis['culture_analysis']['secondary_culture']
        dom_prop = analysis['culture_analysis']['dominant_proportion']
        sec_prop = analysis['culture_analysis']['secondary_proportion']
        platos = analysis['platos_analizados']
        ing_count = analysis['total_ingredients']
        
        # Formatear segunda cultura
        secondary_str = f"+ {secondary}" if secondary else ""
        
        culture_distribution[dominant] += 1
        
        # Mostrar progreso
        print(f"   {i:2d}. {case['event']:<12} {case['season']:<8} | {dominant:<12} ({dom_prop*100:5.1f}%) {secondary_str:<15} ({sec_prop*100:5.1f}%) | platos: {platos} | ing: {ing_count}")
    
    # Guardar resultado
    output_file = "develop/config/final_50_cases_enriched_detailed.json"
    output_data = {
        "cases": enriched_cases,
        "metadata": {
            "total_cases": len(enriched_cases),
            "culture_distribution": dict(culture_distribution)
        }
    }
    
    print(f"\n💾 Guardando en {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print("   ✓ Archivo guardado")
    
    # Mostrar estadísticas
    print("\n" + "=" * 90)
    print("📈 ESTADÍSTICAS DE ENRIQUECIMIENTO")
    print("=" * 90)
    
    total_platos = sum(c.get('platos_analizados', 0) for c in enriched_cases)
    total_ingredientes = sum(c.get('total_ingredients', 0) for c in enriched_cases)
    avg_ing = total_ingredientes / len(enriched_cases) if enriched_cases else 0
    
    print(f"\nCasos totales: {len(enriched_cases)}")
    print(f"Casos procesados: {len([c for c in enriched_cases if c.get('platos_analizados', 0) > 0])}")
    print(f"Platos analizados: {total_platos}")
    print(f"Ingredientes totales: {total_ingredientes}")
    print(f"Ingredientes promedio por caso: {avg_ing:.1f}")
    
    print(f"\nDistribución por cultura dominante:")
    print(f"{'Cultura':<20} | {'Casos':>6} | {'Porcentaje':>10}")
    print("-" * 45)
    
    for culture in sorted(culture_distribution.keys()):
        count = culture_distribution[culture]
        percentage = (count / len(enriched_cases)) * 100
        print(f"{culture:<20} | {count:6d} | {percentage:9.1f}%")
    
    print("\n✅ Enriquecimiento completado exitosamente")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
