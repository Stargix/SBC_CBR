#!/usr/bin/env python3
"""
Script para añadir el campo 'culture' a final_50_cases.json.

Usa la cultura secundaria cuando American o Indian dominen para dar más variedad.
"""

import json
from collections import Counter


def main():
    print("=" * 80)
    print("🌍 AÑADIENDO CAMPO 'CULTURE' A CASOS")
    print("=" * 80)
    
    # Cargar casos originales
    with open("develop/config/final_50_cases.json", 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    original_cases = original_data['cases']
    
    # Cargar análisis enriquecido
    with open("develop/config/final_50_cases_enriched_detailed.json", 'r', encoding='utf-8') as f:
        enriched_data = json.load(f)
    enriched_cases = enriched_data['cases']
    
    print(f"\n📂 {len(original_cases)} casos cargados")
    
    # Contar culturas dominantes
    dominant_counts = Counter()
    for case in enriched_cases:
        dominant = case['culture_analysis']['dominant_culture']
        dominant_counts[dominant] += 1
    
    print(f"\n📊 Distribución inicial (antes de balancear):")
    for culture, count in dominant_counts.most_common():
        print(f"   {culture:<15}: {count:2d} casos")
    
    # Añadir campo culture con balanceo dinámico
    updated_cases = []
    culture_assigned = Counter()
    MAX_PER_CULTURE = 8  # Máximo de casos por cultura
    
    for orig, enriched in zip(original_cases, enriched_cases):
        analysis = enriched['culture_analysis']
        dominant = analysis['dominant_culture']
        secondary = analysis.get('secondary_culture')
        
        # Estrategia: Si la cultura dominante ya tiene muchos casos, usar la secundaria
        if culture_assigned[dominant] >= MAX_PER_CULTURE and secondary and secondary not in ['Universal']:
            # Usar secundaria si tiene buena proporción (>10%)
            if analysis.get('secondary_proportion', 0) >= 0.10:
                assigned_culture = secondary
            else:
                assigned_culture = dominant
        else:
            assigned_culture = dominant
        
        # Añadir campo culture (lowercase)
        updated_case = {**orig, 'culture': assigned_culture.lower()}
        updated_cases.append(updated_case)
        culture_assigned[assigned_culture] += 1
    
    # Guardar
    output_data = {'cases': updated_cases}
    
    with open("develop/config/final_50_cases.json", 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ Campo 'culture' añadido")
    
    print(f"\n📊 Distribución final (después de balancear):")
    for culture, count in culture_assigned.most_common():
        print(f"   {culture:<15}: {count:2d} casos")
    
    print("\n" + "=" * 80)
    print("✅ Actualización completada")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
