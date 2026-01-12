#!/usr/bin/env python3
"""
Test específico para forzar sustitución de ingredientes (Nivel 1).

Estrategia: Recuperar casos genéricos y aplicar UNA restricción
dietética moderada para ver si el sistema sustituye ingredientes
en lugar de reemplazar platos completos.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from develop.core.case_base import CaseBase
from develop.core.models import Request, EventType, Season
from develop.cycle.retrieve import CaseRetriever
from develop.cycle.adapt import CaseAdapter


def test_ingredient_substitution_scenarios():
    """
    Test diseñado para FORZAR sustitución de ingredientes.
    
    Metodología:
    1. Recuperar un caso genérico (sin restricciones)
    2. Aplicar UNA sola restricción moderada
    3. Verificar si sustituye ingredientes vs reemplaza platos
    """
    case_base = CaseBase()
    retriever = CaseRetriever(case_base)
    adapter = CaseAdapter(case_base)
    
    print("="*80)
    print("TEST: SUSTITUCIÓN FORZADA DE INGREDIENTES")
    print("="*80)
    print(f"Base de casos: {len(case_base.get_all_cases())} casos iniciales\n")
    
    results = []
    
    # ESCENARIO 1: Pedir casos Italian/Wedding/SUMMER sin restricciones
    print("[FASE 1] Recuperar casos base (Italian/Wedding/Summer, SIN restricciones)")
    print("-" * 80)
    
    base_request = Request(
        event_type=EventType.WEDDING,
        num_guests=80,
        price_min=50.0,
        price_max=70.0,
        season=Season.SUMMER,
        required_diets=[],
        cultural_preference="Italian"
    )
    
    base_candidates = retriever.retrieve(base_request, k=10)
    print(f"✓ Recuperados: {len(base_candidates)} casos base\n")
    
    if not base_candidates:
        print("❌ ERROR: No hay casos base compatibles")
        return
    
    # Mostrar un ejemplo
    example = base_candidates[0].case
    print(f"Ejemplo de caso base (ID: {example.id}):")
    print(f"  Starter: {example.menu.starter.name}")
    print(f"    - Diets: {example.menu.starter.diets}")
    print(f"    - Ingredients: {example.menu.starter.ingredients[:5]}...")
    print(f"  Main: {example.menu.main_course.name}")
    print(f"    - Diets: {example.menu.main_course.diets}")
    print(f"    - Ingredients: {example.menu.main_course.ingredients[:5]}...")
    print(f"  Dessert: {example.menu.dessert.name}")
    print(f"    - Diets: {example.menu.dessert.diets}")
    print(f"    - Ingredients: {example.menu.dessert.ingredients[:5]}...")
    print()
    
    # ESCENARIO 2: Aplicar restricciones MODERADAS una por una
    print("[FASE 2] Aplicar restricciones dietéticas INDIVIDUALES")
    print("-" * 80)
    print("Objetivo: Ver si sustituye ingredientes en lugar de reemplazar platos\n")
    
    test_diets = [
        ("dairy-free", "eliminar lácteos"),
        ("egg-free", "eliminar huevos"),
        ("gluten-free", "eliminar gluten"),
        ("vegetarian", "eliminar carnes"),
        ("vegan", "eliminar productos animales"),
        ("soy-free", "eliminar soya"),
        ("tree-nut-free", "eliminar nueces"),
        ("peanut-free", "eliminar maní"),
        ("shellfish-free", "eliminar mariscos"),
        ("pescatarian", "eliminar carnes rojas")
    ]
    
    for idx, (diet, description) in enumerate(test_diets, 1):
        print(f"[{idx}/{len(test_diets)}] Restricción: {diet} ({description})")
        
        # Crear request con la restricción
        diet_request = Request(
            event_type=EventType.WEDDING,
            num_guests=80,
            price_min=50.0,
            price_max=70.0,
            season=Season.SUMMER,
            required_diets=[diet],
            cultural_preference="Italian"
        )
        
        # ⚠️ CLAVE: Buscar un caso que NO cumpla la dieta
        selected_case = None
        for candidate in base_candidates:
            menu = candidate.case.menu
            # Verificar si ALGÚN plato NO cumple la dieta
            violates = False
            for dish in [menu.starter, menu.main_course, menu.dessert]:
                if diet not in dish.diets:
                    violates = True
                    break
            
            if violates:
                selected_case = candidate
                print(f"  ✓ Caso seleccionado: {candidate.case.id}")
                print(f"    Starter cumple {diet}: {diet in menu.starter.diets}")
                print(f"    Main cumple {diet}: {diet in menu.main_course.diets}")
                print(f"    Dessert cumple {diet}: {diet in menu.dessert.diets}")
                break
        
        if not selected_case:
            print(f"  ⚠️ SKIP: Todos los casos ya cumplen {diet}")
            continue
        
        # Adaptar
        adapted_menus = adapter.adapt([selected_case], diet_request)
        
        if not adapted_menus:
            print(f"  ❌ FALLÓ: No se pudo adaptar")
            results.append({
                'diet': diet,
                'success': False,
                'level': 3,
                'adaptations': []
            })
            continue
        
        adaptation = adapted_menus[0]
        adaptations_text = adaptation.adaptations_made
        
        # Analizar tipo de adaptación
        ingredient_substitutions = [a for a in adaptations_text if '→' in a and 'Plato cambiado' not in a]
        dish_replacements = [a for a in adaptations_text if 'Plato cambiado' in a or 'cambiado:' in a]
        new_menu = any('Menú generado' in a or 'generado desde cero' in a for a in adaptations_text)
        
        # Clasificar nivel
        if new_menu:
            level = 2
            level_name = "Nivel 2 (Generación nueva)"
        elif dish_replacements:
            level = 2
            level_name = "Nivel 2 (Reemplazo platos)"
        elif ingredient_substitutions:
            level = 1
            level_name = "✅ Nivel 1 (Sustitución ingredientes)"
        else:
            level = 0
            level_name = "Nivel 0 (Sin cambios)"
        
        print(f"  {level_name}")
        print(f"    - Sustituciones ingredientes: {len(ingredient_substitutions)}")
        print(f"    - Reemplazos platos: {len(dish_replacements)}")
        
        if ingredient_substitutions:
            for sub in ingredient_substitutions[:3]:  # Mostrar primeras 3
                print(f"      • {sub}")
        
        if dish_replacements:
            for repl in dish_replacements[:2]:  # Mostrar primeras 2
                print(f"      • {repl}")
        
        print()
        
        results.append({
            'diet': diet,
            'success': True,
            'level': level,
            'level_name': level_name,
            'ingredient_substitutions': len(ingredient_substitutions),
            'dish_replacements': len(dish_replacements),
            'adaptations': adaptations_text
        })
    
    # RESUMEN
    print("="*80)
    print("RESUMEN FINAL")
    print("="*80)
    
    successful = [r for r in results if r['success']]
    level_0 = len([r for r in successful if r['level'] == 0])
    level_1 = len([r for r in successful if r['level'] == 1])
    level_2 = len([r for r in successful if r['level'] == 2])
    level_3 = len([r for r in successful if r['level'] == 3])
    
    total = len(successful)
    
    print(f"\nCasos exitosos: {total}/{len(test_diets)}")
    print(f"\nDistribución:")
    print(f"  Nivel 0 (sin cambios):          {level_0} ({level_0/total*100:.1f}%)")
    print(f"  Nivel 1 (sust. ingredientes):   {level_1} ({level_1/total*100:.1f}%) ← OBJETIVO")
    print(f"  Nivel 2 (reemplazo platos):     {level_2} ({level_2/total*100:.1f}%)")
    print(f"  Nivel 3 (rechazo):              {level_3} ({level_3/total*100:.1f}%)")
    
    total_ingr_subs = sum(r['ingredient_substitutions'] for r in successful)
    total_dish_repls = sum(r['dish_replacements'] for r in successful)
    
    print(f"\nGranularidad:")
    print(f"  Total sustituciones ingredientes: {total_ingr_subs}")
    print(f"  Total reemplazos platos:          {total_dish_repls}")
    print(f"  Ratio ingredientes/platos:        {total_ingr_subs}/{total_dish_repls}")
    
    if level_1 == 0:
        print("\n⚠️ DIAGNÓSTICO: 0% usa sustitución de ingredientes")
        print("Posibles causas:")
        print("  1. El adapter de ingredientes no tiene sustituciones para estas dietas")
        print("  2. Los platos recuperados ya tienen las dietas marcadas")
        print("  3. La lógica del adapt prioriza reemplazo sobre sustitución")
        print("  4. Los ingredientes problemáticos no tienen alternativas")
    
    # Guardar resultados
    output = {
        'experiment': 'test_ingredient_substitution',
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': len(test_diets),
            'successful': total,
            'level_0': level_0,
            'level_1': level_1,
            'level_2': level_2,
            'level_3': level_3,
            'total_ingredient_substitutions': total_ingr_subs,
            'total_dish_replacements': total_dish_repls
        },
        'results': results
    }
    
    output_path = Path('data/results/test_ingredient_substitution.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Resultados guardados en: {output_path.absolute()}")
    print("="*80)


if __name__ == '__main__':
    test_ingredient_substitution_scenarios()
