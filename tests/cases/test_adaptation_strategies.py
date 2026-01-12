"""
Test de Análisis Cuantitativo de Estrategias de Adaptación
Experimento 10: Analiza las adaptaciones REALES del sistema
"""

import sys
import json
from pathlib import Path
from datetime import datetime

base_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(base_path))

from develop.core.case_base import CaseBase
from develop.cycle.retrieve import CaseRetriever
from develop.cycle.adapt import CaseAdapter
from develop.core.models import Request, EventType, Season


def analyze_adaptations(adaptations_made):
    """Analiza las adaptaciones y cuenta ingredientes vs platos."""
    ingredient_subs = 0
    dish_replacements = 0
    
    for adaptation in adaptations_made:
        adaptation_str = str(adaptation)
        
        # Las sustituciones de ingredientes tienen el símbolo →
        if '→' in adaptation_str:
            # Contar cuántas flechas (cada una es una sustitución)
            ingredient_subs += adaptation_str.count('→')
        
        # Reemplazos de platos completos
        if any(keyword in adaptation_str.lower() for keyword in [
            'plato reemplazado', 'sustituido', 'cambiado', 
            'replaced', 'substituted'
        ]):
            # Excluir si también tiene →, que indica que es solo cambio de ingredientes
            if '→' not in adaptation_str:
                dish_replacements += 1
    
    return ingredient_subs, dish_replacements


def test_adaptation_strategies():
    """
    Experimento 10: Análisis de estrategias de adaptación del sistema real.
    """
    
    print("\n" + "="*80)
    print("EXPERIMENTO 10: ANÁLISIS DE ESTRATEGIAS DE ADAPTACIÓN")
    print("="*80 + "\n")
    
    # Inicializar sistema
    case_base = CaseBase()
    retriever = CaseRetriever(case_base)
    adapter = CaseAdapter(case_base)
    
    # 30 peticiones variadas para provocar diferentes adaptaciones
    test_requests = []
    
    # Peticiones variando dietas (10)
    for diet in ['vegan', 'vegetarian', 'gluten-free', 'dairy-free', 'pescatarian',
                 'kosher', 'paleo', 'keto-friendly', 'egg-free', 'peanut-free']:
        test_requests.append({
            'type': 'dietary',
            'event': EventType.WEDDING,
            'guests': 50,
            'price_min': 40.0,
            'price_max': 60.0,
            'season': Season.SUMMER,
            'diets': [diet],
            'label': diet
        })
    
    # Peticiones variando eventos (10)
    for event in [EventType.WEDDING, EventType.CORPORATE, EventType.FAMILIAR,
                  EventType.COMMUNION, EventType.CHRISTENING, EventType.CONGRESS] * 2:
        test_requests.append({
            'type': 'event',
            'event': event,
            'guests': 30,
            'price_min': 50.0,
            'price_max': 70.0,
            'season': Season.AUTUMN,
            'diets': [],
            'label': event.value
        })
        if len([r for r in test_requests if r['type'] == 'event']) >= 10:
            break
    
    # Peticiones mixtas (10)
    mixed_configs = [
        (EventType.WEDDING, ['vegan', 'gluten-free'], Season.SPRING),
        (EventType.CORPORATE, ['vegetarian'], Season.SUMMER),
        (EventType.FAMILIAR, ['dairy-free'], Season.AUTUMN),
        (EventType.COMMUNION, ['pescatarian', 'dairy-free'], Season.WINTER),
        (EventType.CHRISTENING, ['kosher'], Season.SPRING),
        (EventType.CONGRESS, ['vegan'], Season.SUMMER),
        (EventType.WEDDING, ['paleo'], Season.AUTUMN),
        (EventType.CORPORATE, ['keto-friendly'], Season.WINTER),
        (EventType.FAMILIAR, ['egg-free'], Season.SPRING),
        (EventType.COMMUNION, ['peanut-free', 'dairy-free'], Season.SUMMER),
    ]
    
    for event, diets, season in mixed_configs:
        test_requests.append({
            'type': 'mixed',
            'event': event,
            'guests': 40,
            'price_min': 45.0,
            'price_max': 65.0,
            'season': season,
            'diets': diets,
            'label': f"{event.value}+{','.join(diets)}"
        })
    
    # Ejecutar tests
    all_results = []
    total_ingredient_subs = 0
    total_dish_replacements = 0
    total_similarity_before = 0
    total_similarity_after = 0
    
    for category in ['dietary', 'event', 'mixed']:
        category_requests = [r for r in test_requests if r['type'] == category]
        print(f"[{category.upper()}] Procesando {len(category_requests)} casos")
        print("-" * 80)
        
        for idx, req_data in enumerate(category_requests, 1):
            request = Request(
                event_type=req_data['event'],
                num_guests=req_data['guests'],
                price_min=req_data['price_min'],
                price_max=req_data['price_max'],
                season=req_data['season'],
                required_diets=req_data['diets']
            )
            
            # RETRIEVE
            retrieval_results = retriever.retrieve(request, k=3)
            
            if not retrieval_results:
                print(f"  [{idx}/{len(category_requests)}] {req_data['label']}: No cases retrieved")
                continue
            
            # ADAPT
            adaptation_results = adapter.adapt(retrieval_results, request, num_proposals=1)
            
            if not adaptation_results:
                print(f"  [{idx}/{len(category_requests)}] {req_data['label']}: Adaptation failed")
                continue
            
            adaptation = adaptation_results[0]
            
            # Analizar adaptaciones
            ingredient_subs, dish_replacements = analyze_adaptations(adaptation.adaptations_made)
            
            total_ingredient_subs += ingredient_subs
            total_dish_replacements += dish_replacements
            total_similarity_before += retrieval_results[0].similarity
            total_similarity_after += adaptation.final_similarity
            
            # Clasificar nivel
            if ingredient_subs > 0 and dish_replacements == 0:
                level = 1  # Solo ingredientes
            elif dish_replacements > 0:
                level = 2  # Incluye reemplazo de platos
            else:
                level = 0  # Sin adaptación clara
            
            result = {
                'category': category,
                'label': req_data['label'],
                'level': level,
                'ingredient_subs': ingredient_subs,
                'dish_replacements': dish_replacements,
                'similarity_before': retrieval_results[0].similarity,
                'similarity_after': adaptation.final_similarity,
                'adaptations': adaptation.adaptations_made
            }
            all_results.append(result)
            
            print(f"  [{idx}/{len(category_requests)}] {req_data['label']}: "
                  f"Nivel {level}, {ingredient_subs} ingr., {dish_replacements} platos")
        
        print()
    
    # Estadísticas agregadas
    total_cases = len(all_results)
    level_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for r in all_results:
        level_counts[r['level']] += 1
    
    print("="*80)
    print("ANÁLISIS AGREGADO")
    print("="*80 + "\n")
    
    print(f"Distribución de Estrategias:")
    print(f"  Nivel 0 (Sin adaptación):         {level_counts[0]} casos ({level_counts[0]/total_cases*100:.1f}%)")
    print(f"  Nivel 1 (Sust. ingredientes):     {level_counts[1]} casos ({level_counts[1]/total_cases*100:.1f}%)")
    print(f"  Nivel 2 (Cambio de plato):       {level_counts[2]} casos ({level_counts[2]/total_cases*100:.1f}%)")
    print(f"  Nivel 3 (Rechazo):                 {level_counts[3]} casos ({level_counts[3]/total_cases*100:.1f}%)")
    
    avg_sim_before = total_similarity_before / total_cases if total_cases > 0 else 0
    avg_sim_after = total_similarity_after / total_cases if total_cases > 0 else 0
    
    print(f"\nGranularidad:")
    print(f"  Ingredientes sustituidos (total): {total_ingredient_subs}")
    print(f"  Ingredientes por caso (promedio): {total_ingredient_subs/total_cases:.2f}")
    print(f"  Platos reemplazados (total):      {total_dish_replacements}")
    print(f"  Platos por caso (promedio):       {total_dish_replacements/total_cases:.2f}")
    
    print(f"\nEfectividad:")
    print(f"  Similitud antes de adaptación:    {avg_sim_before:.3f}")
    print(f"  Similitud después de adaptación:  {avg_sim_after:.3f}")
    print(f"  Mejora de similitud:              +{avg_sim_after - avg_sim_before:.3f}")
    print(f"  Tasa de éxito:                    {(total_cases / 30)*100:.1f}%")
    
    # Guardar resultados
    output_data = {
        'experiment': 'test_adaptation_strategies',
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_cases': total_cases,
            'level_0_no_adaptation': level_counts[0],
            'level_1_ingredient_substitution': level_counts[1],
            'level_2_dish_replacement': level_counts[2],
            'level_3_case_rejection': level_counts[3],
            'level_0_pct': level_counts[0]/total_cases*100,
            'level_1_pct': level_counts[1]/total_cases*100,
            'level_2_pct': level_counts[2]/total_cases*100,
            'level_3_pct': level_counts[3]/total_cases*100,
            'total_ingredients_substituted': total_ingredient_subs,
            'total_dishes_replaced': total_dish_replacements,
            'avg_ingredients_per_case': total_ingredient_subs/total_cases,
            'avg_dishes_per_case': total_dish_replacements/total_cases,
            'avg_similarity_before': avg_sim_before,
            'avg_similarity_after': avg_sim_after,
            'similarity_improvement': avg_sim_after - avg_sim_before,
            'similarity_improvement_pct': ((avg_sim_after - avg_sim_before) / avg_sim_before * 100) if avg_sim_before > 0 else 0,
            'success_rate': total_cases / 30
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
    test_adaptation_strategies()
