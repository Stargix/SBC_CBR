"""
Demo completa de adaptación cultural con similaridad semántica de ingredientes.

Este script demuestra cómo el sistema CBR:
1. Recupera casos similares
2. Adapta ingredientes usando similaridad semántica de culturas
3. Muestra las decisiones de adaptación tomadas
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from develop.core.case_base import CaseBase
from develop.core.models import Request, EventType, Season, CulturalTradition
from develop.cycle.retrieve import CaseRetriever
from develop.cycle.adapt import CaseAdapter


def print_separator(title: str = "", char: str = "="):
    """Imprime un separador visual"""
    if title:
        print(f"\n{char * 80}")
        print(f"  {title}")
        print(f"{char * 80}")
    else:
        print(f"{char * 80}")


def print_dish_details(dish, indent: str = "   "):
    """Imprime detalles de un plato"""
    print(f"{indent}* {dish.name}")
    print(f"{indent}   Precio: €{dish.price:.2f}")
    if dish.ingredients:
        print(f"{indent}   Ingredientes: {', '.join(dish.ingredients)}")
    else:
        print(f"{indent}   Ingredientes: No especificados")


def demo_cultural_adaptation():
    """
    Demuestra la adaptación cultural de menús con similaridad semántica.
    """
    print_separator("DEMO: Adaptacion Cultural con Similaridad Semantica")
    
    # 1. Crear case base
    print("\nCargando base de casos...")
    case_base = CaseBase()
    # Los casos se generan automáticamente en __init__
    print(f"   OK - {len(case_base.cases)} casos cargados")
    
    # 2. Crear una solicitud con cultura específica
    print_separator("Creando solicitud del cliente", "-")
    
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=40.0,
        price_max=60.0,
        season=Season.SUMMER,
        cultural_preference=CulturalTradition.JAPANESE,  # Cliente quiere comida japonesa
        required_diets=[],
        restricted_ingredients=[]
    )
    
    print(f"   Tipo evento: {request.event_type.value}")
    print(f"   Comensales: {request.num_guests}")
    print(f"   Presupuesto: EUR {request.price_min:.2f} - {request.price_max:.2f} por persona")
    print(f"   Temporada: {request.season.value}")
    print(f"   >> Cultura preferida: {request.cultural_preference.value.upper()}")
    
    # 3. Recuperar casos similares
    print_separator("FASE RETRIEVE: Recuperando casos similares", "-")
    
    retriever = CaseRetriever(case_base)
    retrieval_results = retriever.retrieve(request, k=3)
    
    print(f"\n   Top 3 casos mas similares:\n")
    for i, result in enumerate(retrieval_results, 1):
        menu = result.case.menu
        print(f"   {i}. Caso #{result.case.id}")
        print(f"      Similitud: {result.similarity:.2%}")
        print(f"      Cultura original: {menu.cultural_theme.value if menu.cultural_theme else 'Sin especificar'}")
        print(f"      Precio total: EUR {menu.total_price:.2f}")
        print(f"      Platos:")
        print_dish_details(menu.starter, "      ")
        print_dish_details(menu.main_course, "      ")
        print_dish_details(menu.dessert, "      ")
        print()
    
    # 4. Adaptar casos
    print_separator("FASE ADAPT: Adaptando casos a cultura japonesa", "-")
    
    adapter = CaseAdapter(case_base)
    adaptations = adapter.adapt(retrieval_results, request, num_proposals=2)
    
    print(f"\n   OK - {len(adaptations)} propuestas generadas\n")
    
    # 5. Mostrar detalles de adaptaciones
    for i, adaptation in enumerate(adaptations, 1):
        print_separator(f"Propuesta #{i}", "─")
        
        menu = adaptation.adapted_menu
        original_case = adaptation.original_case
        
        print(f"\n   >> Metricas:")
        print(f"      Caso original: #{original_case.id}")
        print(f"      Similitud original: {adaptation.original_similarity:.2%}")
        print(f"      Similitud final: {adaptation.final_similarity:.2%}")
        print(f"      Cambio: {adaptation.get_similarity_change()}")
        print(f"      Score adaptación: {adaptation.adaptation_score:.2%}")
        print(f"      Categoría precio: {adaptation.price_category}")
        
        print(f"\n   >> Menu adaptado:")
        print(f"      Cultura: {menu.cultural_theme.value if menu.cultural_theme else 'Sin especificar'}")
        print(f"      Precio total: €{menu.total_price:.2f}")
        
        print(f"\n      Entrante:")
        print_dish_details(menu.starter, "      ")
        
        print(f"\n      Plato principal:")
        print_dish_details(menu.main_course, "      ")
        
        print(f"\n      Postre:")
        print_dish_details(menu.dessert, "      ")
        
        if menu.beverage:
            print(f"\n      Bebida:")
            print(f"         * {menu.beverage.name} (EUR {menu.beverage.price:.2f})")
        
        # Mostrar adaptaciones realizadas
        if adaptation.adaptations_made:
            print(f"\n   >> Adaptaciones realizadas:")
            for j, adapt_desc in enumerate(adaptation.adaptations_made, 1):
                print(f"      {j}. {adapt_desc}")
        else:
            print(f"\n   INFO: No se realizaron adaptaciones (menu ya era apropiado)")
        
        # Mostrar adaptaciones culturales detalladas si existen
        if menu.cultural_adaptations:
            print(f"\n   >> Detalles de adaptacion cultural:")
            for j, cult_adapt in enumerate(menu.cultural_adaptations, 1):
                print(f"\n      Adaptación #{j}:")
                print(f"         Plato: {cult_adapt.get('dish_name', 'N/A')}")
                print(f"         Tipo: {cult_adapt.get('adaptation_type', 'N/A')}")
                
                if 'substitutions' in cult_adapt:
                    print(f"         Sustituciones de ingredientes:")
                    for sub in cult_adapt['substitutions']:
                        print(f"            • {sub['original']} → {sub['replacement']}")
                        print(f"              Razón: {sub['reason']}")
                        print(f"              Confianza: {sub['confidence']:.0%}")
                        if 'score_improvement' in sub:
                            print(f"              Mejora: +{sub['score_improvement']:.1%}")
                
                if 'original_dish' in cult_adapt:
                    print(f"         Plato original: {cult_adapt['original_dish']}")
                
                if 'reason' in cult_adapt:
                    print(f"         Razón: {cult_adapt['reason']}")
        
        print()
    
    # 6. Resumen y recomendación
    print_separator("*** Recomendacion Final")
    
    if adaptations:
        best = adaptations[0]
        print(f"\n   >> Propuesta recomendada: Propuesta #1")
        print(f"   >> Similitud final: {best.final_similarity:.2%}")
        print(f"   >> Precio: EUR {best.adapted_menu.total_price:.2f}")
        print(f"   >> Score adaptacion: {best.adaptation_score:.2%}")
        
        if best.adaptations_made:
            print(f"\n   OK - Adaptaciones clave:")
            for adapt in best.adaptations_made[:3]:  # Top 3
                print(f"      • {adapt}")
    
    print_separator()
    print("\n*** Demo completada ***\n")


def demo_comparison_with_without_semantic():
    """
    Demo que compara adaptación con y sin similaridad semántica.
    """
    print_separator("COMPARACION: Con vs Sin Similaridad Semantica")
    
    # Request: Cliente italiano quiere adaptar un menu frances
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=80,
        price_min=35.0,
        price_max=55.0,
        season=Season.AUTUMN,
        cultural_preference=CulturalTradition.ITALIAN,
        required_diets=[],
        restricted_ingredients=[]
    )
    
    print(f"\n   Solicitud: Adaptar menu a cocina ITALIANA")
    print(f"   Esperado: Deberia encontrar ingredientes de culturas similares (espanol, frances, etc.)")
    
    # Mostrar que culturas son similares a italiana
    print("\n   >> Analizando culturas similares a ITALIANA...")
    
    from develop.cycle.ingredient_adapter import get_ingredient_adapter
    adapter = get_ingredient_adapter()
    
    if adapter.semantic_calc:
        similar = adapter._find_similar_cultures(CulturalTradition.ITALIAN, threshold=0.6)
        print(f"\n   Culturas semanticamente similares:")
        for culture, sim in similar[:5]:
            print(f"      * {culture}: {sim:.2%}")
    else:
        print("\n   WARNING: Semantic calculator no disponible")
    
    print("\n   OK - Con esta informacion, el sistema puede buscar ingredientes de")
    print("     culturas similares cuando no encuentra match exacto.")
    
    print_separator()


if __name__ == "__main__":
    # Demo principal
    demo_cultural_adaptation()
    
    # Demo comparativa (opcional)
    print("\n" * 2)
    demo_comparison_with_without_semantic()
