#!/usr/bin/env python3
"""
Test de Estrategias de Adaptación usando el sistema real.
Hace peticiones reales y analiza las respuestas.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from develop.core.case_base import CaseBase
from develop.cycle.retrieve import CaseRetriever
from develop.cycle.adapt import CaseAdapter
from develop.core.models import Request, EventType, Season


def analyze_menu_response(request, retrieval_results, adaptation_result, case_id):
    """Analiza la respuesta del sistema para clasificar la estrategia."""
    
    result = {
        'case_id': case_id,
        'request_summary': {
            'event': request.event_type.value,
            'num_guests': request.num_guests,
            'required_diets': request.required_diets
        },
        'adaptation_level': 0,
        'ingredients_substituted': 0,
        'dishes_replaced': 0,
        'similarity_before': 0.0,
        'similarity_after': 0.0,
        'adaptations_applied': []
    }
    
    if not retrieval_results:
        result['adaptation_level'] = 3  # Rejection
        result['adaptations_applied'].append('No se encontraron casos compatibles')
        return result
    
    # Get best retrieval result
    best_result = retrieval_results[0]
    result['similarity_before'] = best_result.similarity
    
    if not adaptation_result:
        result['adaptation_level'] = 3  # Rejection
        result['adaptations_applied'].append('Adaptación falló')
        return result
    
    adapted_menu = adaptation_result[0].adapted_menu
    original_menu = best_result.case.menu
    adaptations_made = adaptation_result[0].adaptations_made
    result['similarity_after'] = adaptation_result[0].final_similarity
    
    # Analyze adaptations
    if not adaptations_made or len(adaptations_made) == 0:
        result['adaptation_level'] = 0  # No adaptation needed
        result['adaptations_applied'].append('Sin adaptaciones necesarias')
        return result
    
    # Count ingredient substitutions and dish replacements
    ingredient_subs = 0
    dish_replacements = 0
    
    for adaptation in adaptations_made:
        if isinstance(adaptation, dict):
            if adaptation.get('type') == 'ingredient_substitution':
                ingredient_subs += 1
            elif adaptation.get('type') == 'dish_replacement':
                dish_replacements += 1
        elif isinstance(adaptation, str):
            if 'ingredient' in adaptation.lower() or 'sustit' in adaptation.lower():
                ingredient_subs += 1
            elif 'plato' in adaptation.lower() or 'dish' in adaptation.lower() or 'reemplaz' in adaptation.lower():
                dish_replacements += 1
    
    result['ingredients_substituted'] = ingredient_subs
    result['dishes_replaced'] = dish_replacements
    result['adaptations_applied'] = adaptations_made
    
    # Determine level
    if ingredient_subs > 0 and dish_replacements == 0:
        result['adaptation_level'] = 1  # Ingredient substitution
    elif dish_replacements > 0:
        result['adaptation_level'] = 2  # Dish replacement
    else:
        # If we have adaptations but can't classify, check if menu changed
        if (adapted_menu.starter != original_menu.starter or
            adapted_menu.main != original_menu.main or
            adapted_menu.dessert != original_menu.dessert):
            result['adaptation_level'] = 2
            result['dishes_replaced'] = sum([
                adapted_menu.starter != original_menu.starter,
                adapted_menu.main != original_menu.main,
                adapted_menu.dessert != original_menu.dessert
            ])
        else:
            result['adaptation_level'] = 0
    
    return result


def test_adaptation_strategies_real():
    """Ejecuta el test con el sistema real."""
    
    print("\n" + "="*80)
    print("EXPERIMENTO 10: ANÁLISIS DE ESTRATEGIAS DE ADAPTACIÓN (SISTEMA REAL)")
    print("="*80 + "\n")
    
    # Initialize system
    case_base = CaseBase()
    case_base.load_from_file('develop/config/initial_cases.json')
    retriever = CaseRetriever(case_base)
    adapter = CaseAdapter(case_base)
    
    # Define test requests (30 varied requests)
    test_requests = []
    
    # Cultural conflicts (10 requests)
    cultural_tests = [
        {'event': EventType.FAMILIAR, 'num_guests': 8, 'excluded_cultures': ['Italian'], 'required_diets': []},
        {'event': EventType.WEDDING, 'num_guests': 50, 'excluded_cultures': ['French'], 'required_diets': []},
        {'event': EventType.CORPORATE, 'num_guests': 20, 'excluded_cultures': ['Spanish'], 'required_diets': []},
        {'event': EventType.COMMUNION, 'num_guests': 15, 'excluded_cultures': ['Chinese'], 'required_diets': []},
        {'event': EventType.FAMILIAR, 'num_guests': 6, 'excluded_cultures': ['Japanese'], 'required_diets': []},
        {'event': EventType.CHRISTENING, 'num_guests': 12, 'excluded_cultures': ['Mexican'], 'required_diets': []},
        {'event': EventType.CONGRESS, 'num_guests': 25, 'excluded_cultures': ['Indian'], 'required_diets': []},
        {'event': EventType.CORPORATE, 'num_guests': 30, 'excluded_cultures': ['Thai'], 'required_diets': []},
        {'event': EventType.WEDDING, 'num_guests': 60, 'excluded_cultures': ['Lebanese'], 'required_diets': []},
        {'event': EventType.COMMUNION, 'num_guests': 10, 'excluded_cultures': ['Korean'], 'required_diets': []},
    ]
    
    # Dietary restrictions (10 requests)
    dietary_tests = [
        {'event': EventType.FAMILIAR, 'num_guests': 8, 'excluded_cultures': [], 'required_diets': ['vegan']},
        {'event': EventType.WEDDING, 'num_guests': 40, 'excluded_cultures': [], 'required_diets': ['vegetarian']},
        {'event': EventType.CORPORATE, 'num_guests': 20, 'excluded_cultures': [], 'required_diets': ['gluten-free']},
        {'event': EventType.FAMILIAR, 'num_guests': 6, 'excluded_cultures': [], 'required_diets': ['dairy-free']},
        {'event': EventType.COMMUNION, 'num_guests': 12, 'excluded_cultures': [], 'required_diets': ['pescatarian']},
        {'event': EventType.CHRISTENING, 'num_guests': 10, 'excluded_cultures': [], 'required_diets': ['kosher']},
        {'event': EventType.CONGRESS, 'num_guests': 30, 'excluded_cultures': [], 'required_diets': ['vegan', 'gluten-free']},
        {'event': EventType.CORPORATE, 'num_guests': 25, 'excluded_cultures': [], 'required_diets': ['vegetarian', 'dairy-free']},
        {'event': EventType.WEDDING, 'num_guests': 50, 'excluded_cultures': [], 'required_diets': ['keto-friendly']},
        {'event': EventType.FAMILIAR, 'num_guests': 8, 'excluded_cultures': [], 'required_diets': ['paleo']},
    ]
    
    # Mixed conflicts (10 requests)
    mixed_tests = [
        {'event': EventType.FAMILIAR, 'num_guests': 10, 'excluded_cultures': ['Italian'], 'required_diets': ['vegan']},
        {'event': EventType.WEDDING, 'num_guests': 45, 'excluded_cultures': ['French'], 'required_diets': ['gluten-free']},
        {'event': EventType.CORPORATE, 'num_guests': 22, 'excluded_cultures': ['Spanish'], 'required_diets': ['vegetarian']},
        {'event': EventType.COMMUNION, 'num_guests': 14, 'excluded_cultures': ['Chinese'], 'required_diets': ['dairy-free']},
        {'event': EventType.FAMILIAR, 'num_guests': 7, 'excluded_cultures': ['Japanese'], 'required_diets': ['pescatarian']},
        {'event': EventType.CHRISTENING, 'num_guests': 11, 'excluded_cultures': ['Mexican'], 'required_diets': ['kosher']},
        {'event': EventType.CONGRESS, 'num_guests': 28, 'excluded_cultures': ['Indian'], 'required_diets': ['vegan', 'gluten-free']},
        {'event': EventType.CORPORATE, 'num_guests': 32, 'excluded_cultures': ['Thai'], 'required_diets': ['vegetarian', 'dairy-free']},
        {'event': EventType.WEDDING, 'num_guests': 55, 'excluded_cultures': ['Lebanese'], 'required_diets': ['pescatarian', 'dairy-free']},
        {'event': EventType.COMMUNION, 'num_guests': 13, 'excluded_cultures': ['Korean'], 'required_diets': ['keto-friendly']},
    ]
    
    all_results = []
    
    # Process cultural tests
    print(f"[1/3] CONFLICTOS CULTURALES ({len(cultural_tests)} casos)")
    print("-" * 80)
    for i, test_data in enumerate(cultural_tests, 1):
        request = Request(
            event_type=test_data['event'],
            season=Season.SPRING,
            num_guests=test_data['num_guests'],
            price_min=20.0,
            price_max=50.0,
            required_diets=test_data['required_diets']
        )
        
        retrieval_results = retriever.retrieve(request, k=3)
        adaptation_result = adapter.adapt(retrieval_results, request) if retrieval_results else None
        
        result = analyze_menu_response(request, retrieval_results, adaptation_result, f'cultural_{i}')
        all_results.append(result)
        
        print(f"  [{i}/{len(cultural_tests)}] Excluded {test_data['excluded_cultures']}: "
              f"Nivel {result['adaptation_level']}, "
              f"{result['ingredients_substituted']} ingr. sust., "
              f"{result['dishes_replaced']} platos cambiados")
    
    print(f"\n✓ Conflictos culturales procesados: {len(cultural_tests)}\n")
    
    # Process dietary tests
    print(f"[2/3] RESTRICCIONES DIETÉTICAS ({len(dietary_tests)} casos)")
    print("-" * 80)
    for i, test_data in enumerate(dietary_tests, 1):
        request = Request(
            event_type=test_data['event'],
            season=Season.SPRING,
            num_guests=test_data['num_guests'],
            price_min=20.0,
            price_max=50.0,
            required_diets=test_data['required_diets']
        )
        
        retrieval_results = retriever.retrieve(request, k=3)
        adaptation_result = adapter.adapt(retrieval_results, request) if retrieval_results else None
        
        result = analyze_menu_response(request, retrieval_results, adaptation_result, f'dietary_{i}')
        all_results.append(result)
        
        diets_str = ', '.join(test_data['required_diets'])
        print(f"  [{i}/{len(dietary_tests)}] {diets_str}: "
              f"Nivel {result['adaptation_level']}, "
              f"{result['ingredients_substituted']} ingr. sust., "
              f"{result['dishes_replaced']} platos cambiados")
    
    print(f"\n✓ Restricciones dietéticas procesadas: {len(dietary_tests)}\n")
    
    # Process mixed tests
    print(f"[3/3] CASOS MIXTOS ({len(mixed_tests)} casos)")
    print("-" * 80)
    for i, test_data in enumerate(mixed_tests, 1):
        request = Request(
            event_type=test_data['event'],
            season=Season.SPRING,
            num_guests=test_data['num_guests'],
            price_min=20.0,
            price_max=50.0,
            required_diets=test_data['required_diets']
        )
        
        retrieval_results = retriever.retrieve(request, k=3)
        adaptation_result = adapter.adapt(retrieval_results, request) if retrieval_results else None
        
        result = analyze_menu_response(request, retrieval_results, adaptation_result, f'mixed_{i}')
        all_results.append(result)
        
        excluded_str = ', '.join(test_data['excluded_cultures'])
        diets_str = ', '.join(test_data['required_diets'])
        print(f"  [{i}/{len(mixed_tests)}] {excluded_str} + {diets_str}: "
              f"Nivel {result['adaptation_level']}, "
              f"{result['ingredients_substituted']} ingr. sust., "
              f"{result['dishes_replaced']} platos cambiados")
    
    print(f"\n✓ Casos mixtos procesados: {len(mixed_tests)}\n")
    
    # Calculate aggregate statistics
    print("="*80)
    print("ANÁLISIS AGREGADO")
    print("="*80 + "\n")
    
    total_cases = len(all_results)
    level_0 = sum(1 for r in all_results if r['adaptation_level'] == 0)
    level_1 = sum(1 for r in all_results if r['adaptation_level'] == 1)
    level_2 = sum(1 for r in all_results if r['adaptation_level'] == 2)
    level_3 = sum(1 for r in all_results if r['adaptation_level'] == 3)
    
    total_ingredients = sum(r['ingredients_substituted'] for r in all_results)
    total_dishes = sum(r['dishes_replaced'] for r in all_results)
    
    avg_sim_before = sum(r['similarity_before'] for r in all_results) / total_cases
    avg_sim_after = sum(r['similarity_after'] for r in all_results) / total_cases
    sim_improvement = avg_sim_after - avg_sim_before
    
    success_rate = sum(1 for r in all_results if r['adaptation_level'] != 3) / total_cases
    
    print(f"Distribución de Estrategias:")
    print(f"  Nivel 0 (Sin adaptación):         {level_0} casos ({level_0/total_cases*100:.1f}%)")
    print(f"  Nivel 1 (Sust. ingredientes):     {level_1} casos ({level_1/total_cases*100:.1f}%)")
    print(f"  Nivel 2 (Cambio de plato):       {level_2} casos ({level_2/total_cases*100:.1f}%)")
    print(f"  Nivel 3 (Rechazo):                 {level_3} casos ({level_3/total_cases*100:.1f}%)")
    
    print(f"\nGranularidad:")
    print(f"  Ingredientes sustituidos (total): {total_ingredients}")
    print(f"  Ingredientes por caso (promedio): {total_ingredients/total_cases:.2f}")
    print(f"  Platos reemplazados (total):      {total_dishes}")
    print(f"  Platos por caso (promedio):       {total_dishes/total_cases:.2f}")
    
    print(f"\nEfectividad:")
    print(f"  Similitud antes de adaptación:    {avg_sim_before:.3f}")
    print(f"  Similitud después de adaptación:  {avg_sim_after:.3f}")
    print(f"  Mejora de similitud:              +{sim_improvement:.3f}")
    print(f"  Tasa de éxito:                    {success_rate*100:.1f}%")
    
    # Save results
    output_data = {
        'experiment': 'test_adaptation_strategies',
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_cases': total_cases,
            'level_0_no_adaptation': level_0,
            'level_1_ingredient_substitution': level_1,
            'level_2_dish_replacement': level_2,
            'level_3_case_rejection': level_3,
            'level_0_pct': level_0/total_cases*100,
            'level_1_pct': level_1/total_cases*100,
            'level_2_pct': level_2/total_cases*100,
            'level_3_pct': level_3/total_cases*100,
            'total_ingredients_substituted': total_ingredients,
            'total_dishes_replaced': total_dishes,
            'avg_ingredients_per_case': total_ingredients/total_cases,
            'avg_dishes_per_case': total_dishes/total_cases,
            'avg_similarity_before': avg_sim_before,
            'avg_similarity_after': avg_sim_after,
            'similarity_improvement': sim_improvement,
            'similarity_improvement_pct': (sim_improvement / avg_sim_before * 100) if avg_sim_before > 0 else 0,
            'success_rate': success_rate
        },
        'all_results': all_results
    }
    
    output_path = Path('data/results/test_adaptation_strategies.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Resultados guardados en: {output_path.absolute()}")
    print("="*80 + "\n")


if __name__ == '__main__':
    test_adaptation_strategies_real()
