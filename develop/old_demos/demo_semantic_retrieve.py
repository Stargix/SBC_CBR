"""
Demo que muestra como la similaridad semantica cultural afecta el RETRIEVE.

Compara los resultados de retrieve con diferentes culturas solicitadas
para demostrar que las culturas semanticamente similares obtienen mejor ranking.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from develop.core.case_base import CaseBase
from develop.core.models import Request, EventType, Season, CulturalTradition
from develop.cycle.retrieve import CaseRetriever
from develop.core.similarity import SimilarityCalculator


def print_separator(title: str = "", char: str = "="):
    if title:
        print(f"\n{char * 80}")
        print(f"  {title}")
        print(f"{char * 80}")
    else:
        print(f"{char * 80}")


def demo_cultural_semantic_retrieve():
    """
    Demuestra como los embeddings culturales afectan el ranking en retrieve.
    """
    print_separator("DEMO: Similaridad Semantica Cultural en RETRIEVE")
    
    # Cargar case base
    print("\nCargando base de casos...")
    case_base = CaseBase()
    print(f"   OK - {len(case_base.cases)} casos cargados")
    
    # Mostrar distribución de culturas en la base
    print("\n   Distribucion de culturas en la base:")
    culture_counts = {}
    for case in case_base.cases:
        culture = case.menu.cultural_theme
        if culture:
            culture_name = culture.value
            culture_counts[culture_name] = culture_counts.get(culture_name, 0) + 1
    
    for culture, count in sorted(culture_counts.items()):
        print(f"      {culture}: {count} casos")
    
    # Base request (sin cultura específica)
    base_request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=40.0,
        price_max=60.0,
        season=Season.SUMMER
    )
    
    # Test 1: Solicitar cultura ITALIANA
    print_separator("TEST 1: Solicitud con cultura ITALIANA", "-")
    
    request_italian = Request(
        event_type=base_request.event_type,
        num_guests=base_request.num_guests,
        price_min=base_request.price_min,
        price_max=base_request.price_max,
        season=base_request.season,
        cultural_preference=CulturalTradition.ITALIAN
    )
    
    retriever = CaseRetriever(case_base)
    
    # Reutilizar el mismo calculator para evitar recomputar embeddings
    similarity_calc = retriever.similarity_calc
    
    results_italian = retriever.retrieve(request_italian, k=5)
    
    print(f"\n   Top 5 casos para cultura ITALIANA:\n")
    for i, result in enumerate(results_italian, 1):
        case_culture = result.case.menu.cultural_theme
        culture_name = case_culture.value if case_culture else "sin cultura"
        print(f"   {i}. Caso #{result.case.id}")
        print(f"      Similitud total: {result.similarity:.2%}")
        print(f"      Cultura del caso: {culture_name}")
        
        # Calcular similaridad cultural específica
        if case_culture:
            cultural_sim = similarity_calc._cultural_similarity(
                CulturalTradition.ITALIAN, 
                case_culture
            )
            print(f"      Similaridad cultural: {cultural_sim:.2%}")
        print()
    
    # Test 2: Solicitar cultura ESPAÑOLA
    print_separator("TEST 2: Solicitud con cultura ESPAÑOLA", "-")
    
    request_spanish = Request(
        event_type=base_request.event_type,
        num_guests=base_request.num_guests,
        price_min=base_request.price_min,
        price_max=base_request.price_max,
        season=base_request.season,
        cultural_preference=CulturalTradition.SPANISH
    )
    
    results_spanish = retriever.retrieve(request_spanish, k=5)
    
    print(f"\n   Top 5 casos para cultura ESPAÑOLA:\n")
    for i, result in enumerate(results_spanish, 1):
        case_culture = result.case.menu.cultural_theme
        culture_name = case_culture.value if case_culture else "sin cultura"
        print(f"   {i}. Caso #{result.case.id}")
        print(f"      Similitud total: {result.similarity:.2%}")
        print(f"      Cultura del caso: {culture_name}")
        
        if case_culture:
            cultural_sim = similarity_calc._cultural_similarity(
                CulturalTradition.SPANISH, 
                case_culture
            )
            print(f"      Similaridad cultural: {cultural_sim:.2%}")
        print()
    
    # Test 3: Solicitar cultura JAPONESA
    print_separator("TEST 3: Solicitud con cultura JAPONESA", "-")
    
    request_japanese = Request(
        event_type=base_request.event_type,
        num_guests=base_request.num_guests,
        price_min=base_request.price_min,
        price_max=base_request.price_max,
        season=base_request.season,
        cultural_preference=CulturalTradition.JAPANESE
    )
    
    results_japanese = retriever.retrieve(request_japanese, k=5)
    
    print(f"\n   Top 5 casos para cultura JAPONESA:\n")
    for i, result in enumerate(results_japanese, 1):
        case_culture = result.case.menu.cultural_theme
        culture_name = case_culture.value if case_culture else "sin cultura"
        print(f"   {i}. Caso #{result.case.id}")
        print(f"      Similitud total: {result.similarity:.2%}")
        print(f"      Cultura del caso: {culture_name}")
        
        if case_culture:
            cultural_sim = similarity_calc._cultural_similarity(
                CulturalTradition.JAPANESE, 
                case_culture
            )
            print(f"      Similaridad cultural: {cultural_sim:.2%}")
        print()
    
    # Análisis: Mostrar matriz de similaridades culturales
    print_separator("MATRIZ DE SIMILARIDADES CULTURALES SEMANTICAS", "-")
    test_cultures = [
        CulturalTradition.SPANISH,
        CulturalTradition.ITALIAN, 
        CulturalTradition.FRENCH,
        CulturalTradition.MEXICAN,
        CulturalTradition.JAPANESE,
        CulturalTradition.CHINESE,
        CulturalTradition.KOREAN
    ]
    
    print("\n   Similaridades entre culturas (usando embeddings):\n")
    
    for culture1 in test_cultures:
        print(f"   {culture1.value.upper()}:")
        sims = []
        for culture2 in test_cultures:
            if culture1 != culture2:
                sim = similarity_calc._cultural_similarity(culture1, culture2)
                sims.append((culture2.value, sim))
        
        # Ordenar por similaridad descendente
        sims.sort(key=lambda x: x[1], reverse=True)
        
        # Mostrar top 3
        for cult_name, sim in sims[:3]:
            print(f"      -> {cult_name}: {sim:.2%}")
        print()
    
    print_separator()
    print("\n*** Observaciones:")
    print("   - Culturas semanticamente similares (ej: italiana-espanola) tienen")
    print("     mayor similaridad y por tanto mejor ranking en retrieve")
    print("   - Esto mejora la calidad de los casos recuperados cuando no hay")
    print("     match exacto de cultura")
    print("   - El sistema usa embeddings pre-computados para eficiencia")
    print("\n")


if __name__ == "__main__":
    demo_cultural_semantic_retrieve()
