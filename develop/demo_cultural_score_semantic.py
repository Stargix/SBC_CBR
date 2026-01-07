"""
Demo que muestra como get_cultural_score usa distancia semantica entre culturas.

Compara scores de ingredientes de diferentes culturas para ver como
ingredientes de culturas similares obtienen puntuacion proporcional.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from develop.core.models import CulturalTradition
from develop.core.similarity import SimilarityCalculator


def print_separator(title: str = "", char: str = "="):
    if title:
        print(f"\n{char * 80}")
        print(f"  {title}")
        print(f"{char * 80}")
    else:
        print(f"{char * 80}")


def demo_cultural_score_with_semantics():
    """
    Demuestra como get_cultural_score usa distancia semantica.
    """
    print_separator("DEMO: get_cultural_score con Distancia Semantica")
    
    calc = SimilarityCalculator()
    
    print("\n   Configuracion:")
    print(f"      use_embeddings_for_culture: {calc.use_embeddings_for_culture}")
    print(f"      semantic_calculator disponible: {calc.semantic_calculator is not None}")
    
    # Test 1: Ingredientes italianos evaluados para cultura ITALIANA
    print_separator("TEST 1: Ingredientes italianos -> Cultura ITALIANA", "-")
    
    ingredients_italian = ["pasta", "tomato", "basil", "olive oil", "parmesan"]
    score = calc.get_cultural_score(ingredients_italian, CulturalTradition.ITALIAN)
    
    print(f"\n   Ingredientes: {', '.join(ingredients_italian)}")
    print(f"   Cultura objetivo: ITALIAN")
    print(f"   Score cultural: {score:.2%}")
    print(f"\n   Desglose por ingrediente:")
    
    for ing in ingredients_italian:
        is_cultural = calc.is_ingredient_cultural(ing, CulturalTradition.ITALIAN)
        print(f"      {ing}: {'SI (1.0)' if is_cultural else 'Evaluando similaridad...'}")
    
    # Test 2: Ingredientes italianos evaluados para cultura ESPAÑOLA (similar)
    print_separator("TEST 2: Ingredientes italianos -> Cultura ESPANOLA", "-")
    
    score_spanish = calc.get_cultural_score(ingredients_italian, CulturalTradition.SPANISH)
    
    print(f"\n   Ingredientes: {', '.join(ingredients_italian)}")
    print(f"   Cultura objetivo: SPANISH")
    print(f"   Score cultural: {score_spanish:.2%}")
    
    # Calcular similaridad entre culturas
    cult_sim = calc._cultural_similarity(CulturalTradition.SPANISH, CulturalTradition.ITALIAN)
    print(f"\n   Similaridad SPANISH <-> ITALIAN: {cult_sim:.2%}")
    print(f"   Ingredientes de cultura similar obtienen score proporcional")
    
    # Test 3: Ingredientes italianos evaluados para cultura JAPONESA (diferente)
    print_separator("TEST 3: Ingredientes italianos -> Cultura JAPONESA", "-")
    
    score_japanese = calc.get_cultural_score(ingredients_italian, CulturalTradition.JAPANESE)
    
    print(f"\n   Ingredientes: {', '.join(ingredients_italian)}")
    print(f"   Cultura objetivo: JAPANESE")
    print(f"   Score cultural: {score_japanese:.2%}")
    
    cult_sim_jap = calc._cultural_similarity(CulturalTradition.JAPANESE, CulturalTradition.ITALIAN)
    print(f"\n   Similaridad JAPANESE <-> ITALIAN: {cult_sim_jap:.2%}")
    print(f"   Culturas mas distantes obtienen menor score")
    
    # Test 4: Mix de ingredientes de diferentes culturas
    print_separator("TEST 4: Mix de ingredientes (italiano + espanol + asiatico)", "-")
    
    ingredients_mix = [
        "pasta",        # Italiano
        "chorizo",      # Espanol
        "soy sauce",    # Asiatico
        "olive oil",    # Mediterraneo/universal
        "onion"         # Universal
    ]
    
    print(f"\n   Ingredientes: {', '.join(ingredients_mix)}")
    print(f"\n   Evaluando para diferentes culturas:\n")
    
    test_cultures = [
        CulturalTradition.ITALIAN,
        CulturalTradition.SPANISH,
        CulturalTradition.JAPANESE,
        CulturalTradition.CHINESE
    ]
    
    for culture in test_cultures:
        score = calc.get_cultural_score(ingredients_mix, culture)
        print(f"      {culture.value.upper():12} -> Score: {score:.2%}")
    
    # Test 5: Ingredientes asiáticos entre culturas asiáticas
    print_separator("TEST 5: Ingredientes asiaticos entre culturas asiaticas", "-")
    
    ingredients_asian = ["soy sauce", "ginger", "garlic", "rice", "sesame oil"]
    
    print(f"\n   Ingredientes: {', '.join(ingredients_asian)}")
    print(f"\n   Evaluando entre culturas asiaticas:\n")
    
    asian_cultures = [
        CulturalTradition.JAPANESE,
        CulturalTradition.CHINESE,
        CulturalTradition.KOREAN,
        CulturalTradition.THAI
    ]
    
    for culture in asian_cultures:
        score = calc.get_cultural_score(ingredients_asian, culture)
        print(f"      {culture.value.upper():12} -> Score: {score:.2%}")
    
    # Mostrar matriz de similaridades asiaticas
    print(f"\n   Similaridades entre culturas asiaticas:")
    print(f"      JAPANESE <-> CHINESE: {calc._cultural_similarity(CulturalTradition.JAPANESE, CulturalTradition.CHINESE):.2%}")
    print(f"      JAPANESE <-> KOREAN:  {calc._cultural_similarity(CulturalTradition.JAPANESE, CulturalTradition.KOREAN):.2%}")
    print(f"      CHINESE  <-> KOREAN:  {calc._cultural_similarity(CulturalTradition.CHINESE, CulturalTradition.KOREAN):.2%}")
    
    # Test 6: Comparacion antes/despues conceptual
    print_separator("COMPARACION: Antes vs Despues", "-")
    
    print("\n   ANTES (sin distancia semantica):")
    print("      Solo contaba ingredientes exactos de la cultura")
    print("      Ingredientes de culturas similares: 0 puntos")
    print("      Score mas bajo y menos flexible")
    
    print("\n   DESPUES (con distancia semantica):")
    print("      Ingredientes exactos: 1.0 punto")
    print("      Ingredientes de culturas similares: score proporcional")
    print("      Ingredientes universales: 0.7 puntos")
    print("      Score mas realista y flexible")
    
    print("\n   EJEMPLO:")
    ingredients_example = ["chorizo", "olive oil", "garlic"]
    
    # Simular score "antiguo" (solo match exacto)
    old_score = sum(1 for ing in ingredients_example if calc.is_ingredient_cultural(ing, CulturalTradition.ITALIAN)) / len(ingredients_example)
    
    # Score nuevo (con semantica)
    new_score = calc.get_cultural_score(ingredients_example, CulturalTradition.ITALIAN)
    
    print(f"      Ingredientes: {', '.join(ingredients_example)}")
    print(f"      Cultura: ITALIAN")
    print(f"      Score antiguo (solo match exacto): {old_score:.2%}")
    print(f"      Score nuevo (con semantica): {new_score:.2%}")
    print(f"      Mejora: +{(new_score - old_score):.2%}")
    
    print_separator()
    print("\n*** Observaciones:")
    print("   - Ingredientes de culturas similares ahora contribuyen al score")
    print("   - El score es mas gradual y realista")
    print("   - Mejora la evaluacion de platos fusion o adaptados")
    print("   - Util en ADAPT para evaluar calidad de sustituciones")
    print("\n")


if __name__ == "__main__":
    demo_cultural_score_with_semantics()
