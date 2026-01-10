"""
Demo que muestra como se manejan ingredientes desconocidos en get_cultural_score.

Demuestra el efecto de ingredientes que no estan en ingredients.json
(fueron filtrados por ser menos comunes) en el calculo del score cultural.
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


def demo_unknown_ingredients():
    """
    Demuestra el manejo de ingredientes desconocidos.
    """
    print_separator("DEMO: Manejo de Ingredientes Desconocidos")
    
    calc = SimilarityCalculator()
    
    print("\n   Problema:")
    print("      - dishes.json contiene mas ingredientes que ingredients.json")
    print("      - Ingredientes menos comunes fueron filtrados")
    print("      - Como afecta esto al score cultural?")
    
    # Test 1: Plato con todos los ingredientes conocidos
    print_separator("TEST 1: Plato con ingredientes CONOCIDOS", "-")
    
    ingredients_known = ["pasta", "tomato", "basil", "garlic", "olive oil"]
    
    print(f"\n   Ingredientes: {', '.join(ingredients_known)}")
    print(f"   Verificando si estan en ingredients.json:")
    
    for ing in ingredients_known:
        exists = calc.ingredient_to_cultures.get(ing) is not None
        print(f"      {ing}: {'SI' if exists else 'NO'}")
    
    score = calc.get_cultural_score(ingredients_known, CulturalTradition.ITALIAN)
    print(f"\n   Score cultural (ITALIAN): {score:.2%}")
    
    # Test 2: Plato con mezcla de ingredientes conocidos y desconocidos
    print_separator("TEST 2: Plato con ingredientes MIXTOS (conocidos + desconocidos)", "-")
    
    ingredients_mixed = [
        "pasta",           # Conocido - italiano
        "truffle",         # Potencialmente desconocido
        "basil",           # Conocido - italiano
        "pecorino",        # Potencialmente desconocido
        "black pepper"     # Conocido - universal
    ]
    
    print(f"\n   Ingredientes: {', '.join(ingredients_mixed)}")
    print(f"   Verificando existencia en ingredients.json:")
    
    known_count = 0
    unknown_count = 0
    
    for ing in ingredients_mixed:
        exists = calc.ingredient_to_cultures.get(ing) is not None
        status = "CONOCIDO" if exists else "DESCONOCIDO"
        print(f"      {ing}: {status}")
        if exists:
            known_count += 1
        else:
            unknown_count += 1
    
    print(f"\n   Total: {known_count} conocidos, {unknown_count} desconocidos")
    
    score_mixed = calc.get_cultural_score(ingredients_mixed, CulturalTradition.ITALIAN)
    print(f"   Score cultural (ITALIAN): {score_mixed:.2%}")
    
    # Test 3: Comparar scores con politicas diferentes
    print_separator("TEST 3: Comparacion de politicas para ingredientes desconocidos", "-")
    
    test_ingredients = ["pasta", "unknown_ingredient_1", "basil", "unknown_ingredient_2"]
    
    print(f"\n   Ingredientes de prueba: {', '.join(test_ingredients)}")
    print(f"   2 conocidos (pasta, basil) + 2 desconocidos")
    
    # Calcular score actual (con neutro = 0.5)
    score_actual = calc.get_cultural_score(test_ingredients, CulturalTradition.ITALIAN)
    
    # Simular score si trataramos desconocidos como 0.0
    # Asumiendo que pasta y basil son italianos (1.0 cada uno)
    score_if_zero = 2.0 / 4  # Solo los 2 conocidos suman
    
    # Simular score si trataramos desconocidos como universales (0.7)
    score_if_universal = (2.0 + 0.7 + 0.7) / 4
    
    print(f"\n   Politica ACTUAL (desconocido = 0.5 neutro):")
    print(f"      Score: {score_actual:.2%}")
    print(f"      Razon: No penaliza ni favorece ingredientes filtrados")
    
    print(f"\n   Si trataramos desconocidos como 0.0 (penalizacion total):")
    print(f"      Score: {score_if_zero:.2%}")
    print(f"      Problema: Penaliza injustamente platos validos")
    
    print(f"\n   Si trataramos desconocidos como 0.7 (universal):")
    print(f"      Score: {score_if_universal:.2%}")
    print(f"      Problema: Da ventaja injusta a ingredientes sin verificar")
    
    # Test 4: Caso real de dishes.json
    print_separator("TEST 4: Ejemplo real - ingredientes de dishes.json", "-")
    
    # Simular algunos ingredientes que podrian estar en dishes.json
    real_dish_ingredients = [
        "all-purpose flour",  # Probablemente conocido
        "baking powder",      # Probablemente conocido  
        "vanilla extract",    # Probablemente conocido
        "buttermilk",         # Posiblemente desconocido
        "confectioners sugar" # Posiblemente desconocido
    ]
    
    print(f"\n   Ingredientes tipicos de un plato en dishes.json:")
    
    known = []
    unknown = []
    
    for ing in real_dish_ingredients:
        exists = calc.ingredient_to_cultures.get(ing) is not None
        if exists:
            known.append(ing)
            ing_data = calc.ingredient_to_cultures[ing]
            if isinstance(ing_data, dict):
                cultures = ing_data.get('cultures', [])
            else:
                cultures = ing_data
            print(f"      [OK] {ing}: {cultures}")
        else:
            unknown.append(ing)
            print(f"      [??] {ing}: NO EN BASE -> score neutro (0.5)")
    
    score_real = calc.get_cultural_score(real_dish_ingredients, CulturalTradition.AMERICAN)
    
    print(f"\n   Resumen:")
    print(f"      Conocidos: {len(known)}/{len(real_dish_ingredients)}")
    print(f"      Desconocidos: {len(unknown)}/{len(real_dish_ingredients)}")
    print(f"      Score cultural (AMERICAN): {score_real:.2%}")
    
    # Test 5: Impacto en ADAPT
    print_separator("TEST 5: Impacto en fase ADAPT", "-")
    
    print("\n   En la fase ADAPT, get_cultural_score se usa para:")
    print("      1. Evaluar platos candidatos para reemplazo cultural")
    print("      2. Medir mejora tras sustitucion de ingredientes")
    print("      3. Comparar opciones de adaptacion")
    
    print("\n   Con ingredientes desconocidos:")
    
    ingredients_before = ["pasta", "bacon", "unknown_cheese", "eggs"]
    ingredients_after = ["pasta", "guanciale", "pecorino", "eggs"]
    
    print(f"\n   Antes de sustitucion: {', '.join(ingredients_before)}")
    score_before = calc.get_cultural_score(ingredients_before, CulturalTradition.ITALIAN)
    print(f"      Score: {score_before:.2%}")
    
    print(f"\n   Despues de sustitucion: {', '.join(ingredients_after)}")
    score_after = calc.get_cultural_score(ingredients_after, CulturalTradition.ITALIAN)
    print(f"      Score: {score_after:.2%}")
    
    improvement = score_after - score_before
    print(f"\n   Mejora: {'+' if improvement >= 0 else ''}{improvement:.2%}")
    
    if improvement > 0:
        print(f"   -> Sistema detecta mejora y puede preferir esta sustitucion")
    
    print_separator()
    print("\n*** Conclusiones:")
    print("   - Ingredientes desconocidos reciben score NEUTRO (0.5)")
    print("   - No penaliza platos con ingredientes validos pero filtrados")
    print("   - No da ventaja injusta a ingredientes sin verificar")
    print("   - Permite que ADAPT funcione correctamente con datos parciales")
    print("   - El score sigue siendo util y representativo")
    print("\n   Recomendacion:")
    print("   - Si hay muchos ingredientes desconocidos, considerar ampliar")
    print("     la base ingredients.json con mas ingredientes comunes")
    print("\n")


if __name__ == "__main__":
    demo_unknown_ingredients()
