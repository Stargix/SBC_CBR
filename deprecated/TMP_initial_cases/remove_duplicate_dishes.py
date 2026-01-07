#!/usr/bin/env python3
"""
Script para eliminar casos con platos repetidos de final_50_cases.json
"""

import json


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
    print("🗑️  ELIMINANDO CASOS CON PLATOS REPETIDOS")
    print("=" * 80)
    
    # Cargar casos
    print("\n📂 Cargando final_50_cases.json...")
    with open("develop/config/final_50_cases.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    cases = data['cases']
    
    print(f"   ✓ {len(cases)} casos cargados")
    
    # Filtrar casos sin repetidos
    print("\n🔍 Buscando casos con platos repetidos...")
    
    valid_cases = []
    removed_cases = []
    
    for i, case in enumerate(cases, 1):
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
        print(f"\n❌ Casos eliminados ({len(removed_cases)}):")
        for removed in removed_cases:
            print(f"\n   Caso #{removed['index']}: {removed['event']} - {removed['season']}")
            print(f"      starter:  {removed['dishes']['starter']}")
            print(f"      main:     {removed['dishes']['main']}")
            print(f"      dessert:  {removed['dishes']['dessert']}")
            print(f"      beverage: {removed['dishes']['beverage']}")
    
    # Guardar casos válidos
    output_data = {'cases': valid_cases}
    
    print(f"\n💾 Guardando casos válidos...")
    with open("develop/config/final_50_cases.json", 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print(f"   ✓ Archivo guardado")
    
    print("\n" + "=" * 80)
    print(f"✅ LIMPIEZA COMPLETADA")
    print(f"   Casos originales: {len(cases)}")
    print(f"   Casos eliminados: {len(removed_cases)}")
    print(f"   Casos restantes:  {len(valid_cases)}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
